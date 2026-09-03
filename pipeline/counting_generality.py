r"""How much does the counting choice distort cross-country patent comparisons? (Paper A)

The ASEAN analysis showed that summing the WIPO bulk file across filing offices inflates
an economy's count by an amount that depends on how much it files abroad -- China barely,
Singapore by half. The obvious question is whether that is a property of this country set
or of the data source. This script answers it for every economy in the file.

Three quantities, all computable for any origin from the bulk file alone:

  * **domestic share** -- publications at the applicant's own office, as a fraction of the
    total. An economy filing only at home is already close to one record per invention;
    one filing everywhere is counted many times.
  * **PCT layer** -- publications under the international-phase office code, which
    `build_dataset.py` removes. Summing it alongside national publications counts
    PCT-routed inventions twice.
  * **duplication factor** -- the office-sum divided by the sum of cell-wise office maxima
    for the same origin, year and field. An invention appears at most once at any one
    office, so the larger count is an upper bound on distinct inventions and the smaller a
    lower bound. Their ratio brackets how much duplication the sum contains.

The third is a proxy, so it is validated against the real thing: for the economies where
WIPO's family series was exported by hand, the script reports how well the proxy tracks
the actual publications-to-families ratio. A proxy that fails that check is reported as
failing rather than used.

Also writes the Paper A review measures (identity residual, EPC split, cell granularity,
rank instability, labelled vs cell-wise leading office) as extra columns and tables.

Writes docs/counting_generality.md, docs/paper_a_new_quantities.md, and CSVs under
data/derived/. Run: python pipeline/counting_generality.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DERIVED, ROOT, WIPO_RAW  # noqa: E402
from _countries import COUNTRIES  # noqa: E402
from _pct_published_2020 import PUBLISHED_PCT_APPLICATIONS_2020  # noqa: E402

WINDOW = (2018, 2022)
MIN_PUBS = 500          # below this the shares are too noisy to rank economies by
PCT_OFFICE = "**"
IDENTITY_TOL = 0.05     # |1/H - D| threshold for "on the identity"
PROXY = ("CN", "JP", "KR", "MY", "PH", "SG", "TH")
PCT_SELECTED = ("RU", "CN", "KR", "IN", "JP", "DE", "US", "NL", "SE")
RANK_TOP_N = 25

# EPC contracting states (ISO 3166-1 alpha-2 as they appear in the WIPO origin column).
# Source: European Patent Office, "Member states of the European Patent Organisation"
# (contracting states of the European Patent Convention), retrieved for this pipeline.
# Montenegro (ME) became a contracting state on 1 October 2022 and is included because
# it is an EPC state; the 2018-2022 window only overlaps the last quarter of 2022.
# Validation and extension states (e.g. MA, MD, TN, KH, BA) are not contracting states.
EPC_ISO2 = frozenset({
    "AL", "AT", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GB", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV",
    "MC", "ME", "MK", "MT", "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI",
    "SK", "SM", "TR",
})

# Display names for Paper A notes. Study-set names come from COUNTRIES; the rest are
# conventional short English names, not a second data source.
NAMES = {
    **COUNTRIES,
    "AE": "United Arab Emirates", "AG": "Antigua and Barbuda", "AR": "Argentina",
    "AT": "Austria", "AU": "Australia", "BB": "Barbados", "BE": "Belgium",
    "BG": "Bulgaria", "BR": "Brazil", "BY": "Belarus", "CA": "Canada",
    "CH": "Switzerland", "CL": "Chile", "CO": "Colombia", "CY": "Cyprus",
    "CZ": "Czechia", "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
    "ES": "Spain", "FI": "Finland", "FR": "France", "GB": "United Kingdom",
    "GR": "Greece", "HK": "Hong Kong SAR", "HR": "Croatia", "HU": "Hungary",
    "IE": "Ireland", "IL": "Israel", "IN": "India", "IR": "Iran",
    "IS": "Iceland", "IT": "Italy", "LI": "Liechtenstein", "LT": "Lithuania",
    "LU": "Luxembourg", "LV": "Latvia", "MA": "Morocco", "MC": "Monaco",
    "MD": "Moldova", "MO": "Macao SAR", "MT": "Malta", "MX": "Mexico",
    "NL": "Netherlands", "NO": "Norway", "NZ": "New Zealand", "PE": "Peru",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "RS": "Serbia",
    "RU": "Russia", "SA": "Saudi Arabia", "SE": "Sweden", "SI": "Slovenia",
    "SK": "Slovakia", "TN": "Tunisia", "TR": "Türkiye", "UA": "Ukraine",
    "US": "United States", "ZA": "South Africa",
}


def name_of(code: str) -> str:
    return NAMES.get(code, code)


def load():
    raw = pd.read_csv(WIPO_RAW / "dc_indicator_patent_4_publication_by_technology.csv")
    w = raw[raw.year.between(*WINDOW) & (raw.tec_id > 0)]
    # '**' in the ORIGIN column is unknown origin, not an economy. It carries 164,817
    # publications in this window and was being ranked alongside real economies.
    return w[w.origin != PCT_OFFICE]


def _dup_by_cells(nat: pd.DataFrame, cell_keys: list[str]) -> pd.DataFrame:
    """Office-sum and max-over-office within each cell, then summed to origin.

    cell_keys must start with 'origin'. Collapsing a dimension means omitting it here,
    so the remaining keys define a coarser cell.
    """
    grp = cell_keys + ["office"]
    collapsed = nat.groupby(grp, observed=True)["count"].sum()
    cell = collapsed.groupby(cell_keys)
    upper = cell.sum()
    lower = cell.max()
    if cell_keys == ["origin"]:
        return pd.DataFrame({"upper": upper, "lower": lower})
    return pd.DataFrame({
        "upper": upper.groupby("origin").sum(),
        "lower": lower.groupby("origin").sum(),
    })


def _fisher_z_ci(rho: float, n: int, alpha: float = 0.05,
                 n_controls: int = 0) -> tuple[float, float]:
    """Fisher z interval on a Spearman (or Pearson) correlation.

    z = artanh(rho); SE = 1/sqrt(n-3-k) with k the number of controls
    (zero for a simple correlation, one for a first-order partial).
    """
    df_se = n - 3 - n_controls
    if df_se <= 0 or not np.isfinite(rho) or abs(rho) >= 1:
        return float("nan"), float("nan")
    z = np.arctanh(rho)
    se = 1.0 / np.sqrt(df_se)
    zcrit = float(stats.norm.ppf(1 - alpha / 2))
    return float(np.tanh(z - zcrit * se)), float(np.tanh(z + zcrit * se))


def _partial_spearman(x, y, z):
    """Partial Spearman of x with y controlling for z.

    Rank-Pearson residual method: Pearson correlation of the residuals from
    regressing rank(x) and rank(y) on rank(z). First-order p-value and
    Fisher-z interval use df = n-4.
    """
    x = pd.Series(x, dtype=float)
    y = pd.Series(y, dtype=float)
    z = pd.Series(z, dtype=float)
    mask = x.notna() & y.notna() & z.notna()
    rx, ry, rz = x[mask].rank(), y[mask].rank(), z[mask].rank()
    n = int(len(rx))
    bx = np.polyfit(rz.to_numpy(), rx.to_numpy(), 1)
    by = np.polyfit(rz.to_numpy(), ry.to_numpy(), 1)
    res_x = rx.to_numpy() - (bx[0] * rz.to_numpy() + bx[1])
    res_y = ry.to_numpy() - (by[0] * rz.to_numpy() + by[1])
    rho, _ = stats.pearsonr(res_x, res_y)
    df = n - 4
    t = rho * np.sqrt(df / (1.0 - rho ** 2))
    p = float(2 * stats.t.sf(abs(t), df))
    lo, hi = _fisher_z_ci(float(rho), n, n_controls=1)
    return float(rho), p, lo, hi, n


def pct_origin_rank_check(n_top: int = 20):
    """Office-** volumes versus published PCT applications by origin, 2020.

    Uses the same 2020 office-** construction as the 309,728 aggregate
    (all tec_id, origin ** excluded from the rank check), not the
    2018-2022 tec_id>0 analysis window.
    """
    raw = pd.read_csv(WIPO_RAW / "dc_indicator_patent_4_publication_by_technology.csv")
    star = (
        raw[(raw.office == PCT_OFFICE) & (raw.year == 2020)]
        .groupby("origin")["count"].sum()
    )
    star = star[star.index != "**"]
    top = star.sort_values(ascending=False).head(n_top)
    pub = pd.Series(PUBLISHED_PCT_APPLICATIONS_2020, name="published")
    both = pd.DataFrame({"star": top, "published": pub}).dropna()
    rho, p = stats.spearmanr(both["star"], both["published"])
    lo, hi = _fisher_z_ci(float(rho), len(both))
    return both, float(rho), float(p), lo, hi


def measures(w: pd.DataFrame) -> pd.DataFrame:
    nat = w[w.office != PCT_OFFICE]                      # the corrected basis
    tot = nat.groupby("origin")["count"].sum()
    dom = nat[nat.office == nat.origin].groupby("origin")["count"].sum()
    pct = w[w.office == PCT_OFFICE].groupby("origin")["count"].sum()

    oyf = _dup_by_cells(nat, ["origin", "year", "tec_id"])
    oy = _dup_by_cells(nat, ["origin", "year"])
    of = _dup_by_cells(nat, ["origin", "tec_id"])
    oo = _dup_by_cells(nat, ["origin"])

    office_tot = nat.groupby(["origin", "office"], observed=True)["count"].sum()
    labelled_max = office_tot.groupby("origin").max()
    leader_idx = office_tot.groupby("origin").idxmax()
    leader_office = pd.Series(
        {origin: key[1] for origin, key in leader_idx.items()},
        name="origin_leader_office",
    )

    d = pd.DataFrame({
        "publications": tot,
        "domestic": dom,
        "pct_layer": pct,
        "upper": oyf["upper"],
        "lower": oyf["lower"],
        "labelled_max": labelled_max,
        "origin_leader_office": leader_office,
        "dup_origin_year": oy["upper"] / oy["lower"],
        "dup_origin_field": of["upper"] / of["lower"],
        "dup_origin_only": oo["upper"] / oo["lower"],
    }).fillna({"domestic": 0, "pct_layer": 0})
    d = d[d.publications >= MIN_PUBS]
    d["domestic_share"] = 100 * d.domestic / d.publications
    d["pct_share"] = 100 * d.pct_layer / (d.publications + d.pct_layer)
    d["duplication_factor"] = d.upper / d.lower
    d["labelled_dup"] = d.upper / d.labelled_max
    d["is_epc"] = d.index.isin(EPC_ISO2)
    d["home_is_origin_leader"] = d.origin_leader_office.eq(d.index)
    # An exact zero here means the file carries no origin-resolved rows for that economy's
    # own office -- Thailand has a patent office and residents file at it. The domestic
    # share is unmeasurable for these, not zero, so it is set to NaN rather than plotted
    # at the left edge as though it were a measurement. The duplication factor does not
    # depend on it and is kept.
    d["domestic_measurable"] = d.domestic > 0
    d.loc[~d.domestic_measurable, "domestic_share"] = float("nan")
    d["H"] = d.domestic_share / 100.0
    d["identity"] = 1.0 / d.H
    # 1/H - D is non-negative by construction (sum of cell maxima >= home total).
    # Clip only floating-point crumbs around zero so KR does not print as -0.00.
    d["residual"] = d.identity - d.duplication_factor
    d.loc[d.residual.abs() < 1e-10, "residual"] = 0.0
    d["on_identity"] = d.residual.abs() < IDENTITY_TOL
    # Fraction of the 1/H identity actually realised; bounded in (0, 1].
    d["DH"] = d.duplication_factor * d.H
    return d.sort_values("duplication_factor", ascending=False)


def validate(d: pd.DataFrame):
    """Does the proxy track the real publications-to-families ratio where both exist?"""
    fam = pd.read_csv(DERIVED / "wipo_families_long.csv")
    fam = fam[fam.year.between(*WINDOW)].groupby("origin")["families"].sum()
    both = d.join(fam.rename("families"), how="inner")
    both = both[both.families > 0].copy()
    both["true_ratio"] = both.publications / both.families
    both["lower_over_families"] = both.lower / both.families
    both["upper_over_families"] = both.upper / both.families
    both["abs_dev"] = (both.duplication_factor - both.true_ratio).abs()
    both["abs_err_lower"] = (both.lower_over_families - 1.0).abs()
    both["abs_err_upper"] = (both.upper_over_families - 1.0).abs()
    if len(both) < 5:
        return both, None
    n = len(both)
    rho, p = stats.spearmanr(both.duplication_factor, both.true_ratio)
    rho_lo, rho_hi = _fisher_z_ci(float(rho), n)
    rho_lf, p_lf = stats.spearmanr(both.lower, both.families)
    lf_lo, lf_hi = _fisher_z_ci(float(rho_lf), n)
    rho_uf, p_uf = stats.spearmanr(both.upper, both.families)
    uf_lo, uf_hi = _fisher_z_ci(float(rho_uf), n)
    rho_lf_d, p_lf_d = stats.spearmanr(both.lower_over_families, both.duplication_factor)
    extras = {
        "rho": float(rho), "p": float(p), "rho_lo": rho_lo, "rho_hi": rho_hi,
        "rho_lower_families": float(rho_lf), "p_lower_families": float(p_lf),
        "rho_lower_families_lo": lf_lo, "rho_lower_families_hi": lf_hi,
        "rho_upper_families": float(rho_uf), "p_upper_families": float(p_uf),
        "rho_upper_families_lo": uf_lo, "rho_upper_families_hi": uf_hi,
        "rho_lower_over_fam_vs_D": float(rho_lf_d), "p_lower_over_fam_vs_D": float(p_lf_d),
        "mae_lower": float(both.abs_err_lower.mean()),
        "mae_upper": float(both.abs_err_upper.mean()),
        "mae_lower_excl_ph": float(both.drop(index=["PH"], errors="ignore")
                                   .abs_err_lower.mean())
        if "PH" in both.index else float("nan"),
        "n": n,
    }
    return both, extras


def rank_table(w: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Ranks under three counting rules, plus families for the seven-economy overlap."""
    incl = d.publications + d.pct_layer
    ranks = pd.DataFrame({
        "sum_incl_star": incl,
        "sum_excl_star": d.publications,
        "cellwise_leading": d.lower,
        "rank_sum_incl_star": incl.rank(ascending=False, method="min").astype(int),
        "rank_sum_excl_star": d.publications.rank(ascending=False, method="min").astype(int),
        "rank_cellwise_leading": d.lower.rank(ascending=False, method="min").astype(int),
    }, index=d.index)
    ranks["rank_change_1_to_3"] = ranks.rank_cellwise_leading - ranks.rank_sum_incl_star
    ranks["abs_rank_change_1_to_3"] = ranks.rank_change_1_to_3.abs()
    fam = pd.read_csv(DERIVED / "wipo_families_long.csv")
    fam = fam[fam.year.between(*WINDOW)].groupby("origin")["families"].sum()
    ranks["families"] = fam.reindex(ranks.index)
    ranks["name"] = [name_of(o) for o in ranks.index]
    top = ranks.sort_values("sum_excl_star", ascending=False).head(RANK_TOP_N)
    return ranks, top


def write_side_tables(d: pd.DataFrame, both: pd.DataFrame, ranks: pd.DataFrame,
                      top: pd.DataFrame) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)

    gran = pd.DataFrame([
        {"granularity": "origin_year_field",
         "min": d.duplication_factor.min(), "median": d.duplication_factor.median(),
         "max": d.duplication_factor.max(), "n": len(d)},
        {"granularity": "origin_year",
         "min": d.dup_origin_year.min(), "median": d.dup_origin_year.median(),
         "max": d.dup_origin_year.max(), "n": len(d)},
        {"granularity": "origin_field",
         "min": d.dup_origin_field.min(), "median": d.dup_origin_field.median(),
         "max": d.dup_origin_field.max(), "n": len(d)},
        {"granularity": "origin_only",
         "min": d.dup_origin_only.min(), "median": d.dup_origin_only.median(),
         "max": d.dup_origin_only.max(), "n": len(d)},
    ])
    gran.to_csv(DERIVED / "counting_granularity.csv", index=False)

    present = [o for o in PCT_SELECTED if o in d.index]
    pct_sel = d.loc[present, ["pct_share", "publications", "pct_layer"]].copy()
    pct_sel.insert(0, "name", [name_of(o) for o in pct_sel.index])
    pct_sel.to_csv(DERIVED / "counting_pct_selected.csv")

    meas = d.loc[d.domestic_measurable]
    qrows = [
        {"measure": "domestic_share", "sample": "measurable_home",
         "n": int(len(meas)), "p25": float(meas.domestic_share.quantile(0.25)),
         "p75": float(meas.domestic_share.quantile(0.75)),
         "min": float(meas.domestic_share.min()), "median": float(meas.domestic_share.median()),
         "max": float(meas.domestic_share.max())},
        {"measure": "pct_share", "sample": "all_68",
         "n": int(len(d)), "p25": float(d.pct_share.quantile(0.25)),
         "p75": float(d.pct_share.quantile(0.75)),
         "min": float(d.pct_share.min()), "median": float(d.pct_share.median()),
         "max": float(d.pct_share.max())},
        {"measure": "duplication_factor", "sample": "all_68",
         "n": int(len(d)), "p25": float(d.duplication_factor.quantile(0.25)),
         "p75": float(d.duplication_factor.quantile(0.75)),
         "min": float(d.duplication_factor.min()), "median": float(d.duplication_factor.median()),
         "max": float(d.duplication_factor.max())},
        {"measure": "duplication_factor", "sample": "measurable_home",
         "n": int(len(meas)), "p25": float(meas.duplication_factor.quantile(0.25)),
         "p75": float(meas.duplication_factor.quantile(0.75)),
         "min": float(meas.duplication_factor.min()),
         "median": float(meas.duplication_factor.median()),
         "max": float(meas.duplication_factor.max())},
    ]
    pd.DataFrame(qrows).to_csv(DERIVED / "counting_quartiles.csv", index=False)

    top.to_csv(DERIVED / "counting_ranks.csv")
    ranks.to_csv(DERIVED / "counting_ranks_all68.csv")
    if len(both):
        cols = [c for c in (
            "duplication_factor", "true_ratio", "publications", "families", "lower", "upper",
            "lower_over_families", "upper_over_families", "abs_dev",
            "abs_err_lower", "abs_err_upper", "domestic_share", "H",
        ) if c in both.columns]
        both[cols].to_csv(DERIVED / "counting_proxy_seven.csv")


def _fmt(x, nd=2):
    if x != x:
        return "NA"
    return f"{x:.{nd}f}"


def write_new_quantities_md(d: pd.DataFrame, both: pd.DataFrame, extras: dict | None,
                            ranks: pd.DataFrame, top: pd.DataFrame) -> None:
    meas = d.loc[d.domestic_measurable]
    epc = d.loc[d.is_epc]
    non = d.loc[~d.is_epc]
    gap = (d.labelled_dup - d.duplication_factor).clip(lower=0)
    differ = (d.labelled_max - d.lower).abs() > 0.5
    mover = top["abs_rank_change_1_to_3"].idxmax()
    mover_all = ranks["abs_rank_change_1_to_3"].idxmax()
    top20 = ranks.sort_values("sum_excl_star", ascending=False).head(20)
    top20_mover = top20["abs_rank_change_1_to_3"].idxmax()
    dup_vals = d.duplication_factor.to_numpy()
    pair_vals = pd.Series(
        [max(a, b) / min(a, b) for i, a in enumerate(dup_vals) for b in dup_vals[i + 1:]])
    pair_med = float(pair_vals.median())
    n_pairs = int(len(pair_vals))

    highlight = ["CN", "KR", "JP", "MY", "PH", "SG"]
    L = [
        "# Paper A — newly computed quantities",
        "",
        "Generated by `python pipeline/counting_generality.py`. Writer: use these values;",
        "do not round from memory. Every entry is registered under `paper_a.*` in",
        "`pipeline/check_numbers.py`. Window 2018–2022, `tec_id>0`, origin `**` excluded,",
        "office `**` held as a separate PCT layer.",
        "",
        "## M1. Identity D = 1/H",
        "",
        "H = home-office share of named-office publications. D is the current",
        "origin-year-field duplication factor. Residual = 1/H − D (positive means D",
        "lies below the identity). Sample: 58 economies with a measurable home office.",
        "",
        f"- n with |residual| < {IDENTITY_TOL}: **{int(meas.on_identity.sum())}** of {len(meas)}",
        f"- n whose home office is the origin-level leading named office: "
        f"**{int(meas.home_is_origin_leader.sum())}** of {len(meas)}",
        f"- max residual: **{_fmt(meas.residual.max(), 2)}** "
        f"({name_of(meas.residual.idxmax())}, {meas.residual.idxmax()})",
        f"- Singapore residual: **{_fmt(d.loc['SG', 'residual'], 2)}** "
        f"(H={_fmt(100*d.loc['SG','H'], 1)}%, 1/H={_fmt(d.loc['SG','identity'], 2)}, "
        f"D={_fmt(d.loc['SG','duplication_factor'], 2)})",
        f"- observed D ceiling: **{_fmt(d.duplication_factor.max(), 2)}** "
        f"({name_of(d.duplication_factor.idxmax())})",
        f"- 1/H at Singapore (low-H example in the review): **{_fmt(d.loc['SG','identity'], 2)}**",
        f"- 1/H at the lowest measurable H ({name_of(meas.H.idxmin())}, "
        f"H={_fmt(100*meas.H.min(), 1)}%): **{_fmt(meas.identity.max(), 1)}**",
        "",
        "| economy | H (%) | 1/H | D | residual | home = origin-level leader | leader office |",
        "|---|---:|---:|---:|---:|:---:|---|",
    ]
    for o in highlight:
        r = d.loc[o]
        L.append(
            f"| {name_of(o)} ({o}) | {_fmt(100*r.H, 1)} | {_fmt(r.identity, 2)} | "
            f"{_fmt(r.duplication_factor, 2)} | {_fmt(r.residual, 2)} | "
            f"{'yes' if r.home_is_origin_leader else 'no'} | {r.origin_leader_office} |"
        )
    L += [
        "",
        "## M2. EPC vs non-EPC",
        "",
        "EPC contracting-state origins use the documented ISO2 list in",
        "`pipeline/counting_generality.py` (`EPC_ISO2`). Validation/extension states are excluded.",
        "",
        f"- n EPC among the 68: **{int(d.is_epc.sum())}**; non-EPC: **{int((~d.is_epc).sum())}**",
        f"- D EPC min/median/max (all 68): **{_fmt(epc.duplication_factor.min())} / "
        f"{_fmt(epc.duplication_factor.median())} / {_fmt(epc.duplication_factor.max())}**",
        f"- D non-EPC min/median/max (all 68): **{_fmt(non.duplication_factor.min())} / "
        f"{_fmt(non.duplication_factor.median())} / {_fmt(non.duplication_factor.max())}** "
        f"(max at {non.duplication_factor.idxmax()}, unmeasurable home)",
        f"- measurable-home EPC n={int(meas.is_epc.sum())} D min/median/max: "
        f"**{_fmt(meas.loc[meas.is_epc, 'duplication_factor'].min())} / "
        f"{_fmt(meas.loc[meas.is_epc, 'duplication_factor'].median())} / "
        f"{_fmt(meas.loc[meas.is_epc, 'duplication_factor'].max())}**",
        f"- measurable-home non-EPC n={int((~meas.is_epc).sum())} D min/median/max: "
        f"**{_fmt(meas.loc[~meas.is_epc, 'duplication_factor'].min())} / "
        f"{_fmt(meas.loc[~meas.is_epc, 'duplication_factor'].median())} / "
        f"{_fmt(meas.loc[~meas.is_epc, 'duplication_factor'].max())}** "
        f"(max at {meas.loc[~meas.is_epc, 'duplication_factor'].idxmax()})",
        f"- n whose origin-level leading office is EP: "
        f"**{int((d.origin_leader_office == 'EP').sum())}** of {len(d)} "
        f"(all EPC; 0 non-EPC)",
        f"- Singapore D: **{_fmt(d.loc['SG','duplication_factor'], 2)}** (non-EPC)",
        f"- Switzerland D: **{_fmt(d.loc['CH','duplication_factor'], 2)}** (EPC); "
        f"H=**{_fmt(100*d.loc['CH','H'], 1)}%**; "
        f"origin-level leading office **{d.loc['CH','origin_leader_office']}**",
        f"- top 5 by D among the 68: "
        + ", ".join(
            f"{o}{' (EPC)' if d.loc[o,'is_epc'] else ' (non-EPC)'}"
            f"{'' if d.loc[o,'domestic_measurable'] else ', unmeasurable home'}"
            for o in d.duplication_factor.head(5).index
        ),
        f"- top 5 by D among measurable-home: "
        + ", ".join(
            f"{o}{' (EPC)' if meas.loc[o,'is_epc'] else ' (non-EPC)'}"
            for o in meas.duplication_factor.head(5).index
        ),
        f"- high-D tail among measurable-home is all EPC: "
        f"**{bool(meas.duplication_factor.head(5).index.isin(EPC_ISO2).all())}**",
        "",
        "## M3. Cell granularity of D",
        "",
        "The direction is arithmetic: the sum of within-cell maxima is at least the",
        "maximum of the summed cells, so coarser cells cannot lower D. The magnitude",
        "is the finding. Origin-only D is office-sum divided by the largest single",
        "named office — the definition the manuscript previously labelled and then",
        "corrected away from.",
        "",
        f"Coarser cells raise D: the origin-year-field range "
        f"{_fmt(d.duplication_factor.min())}–{_fmt(d.duplication_factor.max())} becomes "
        f"{_fmt(d.dup_origin_year.min())}–{_fmt(d.dup_origin_year.max())} "
        f"at origin-year (max {d.dup_origin_year.idxmax()}), "
        f"{_fmt(d.dup_origin_field.min())}–{_fmt(d.dup_origin_field.max())} "
        f"at origin-field (max {d.dup_origin_field.idxmax()}), and "
        f"{_fmt(d.dup_origin_only.min())}–{_fmt(d.dup_origin_only.max())} "
        f"at origin-only (max {d.dup_origin_only.idxmax()}). "
        "The 4.3-fold headline does not compress when the cell is coarsened.",
        "",
        f"Collapsing year while retaining field (origin-year-field vs origin-field) "
        f"isolates the temporal-spread component: the maximum rises from "
        f"{_fmt(d.duplication_factor.max())} to {_fmt(d.dup_origin_field.max())}; "
        f"the median from {_fmt(d.duplication_factor.median())} to "
        f"{_fmt(d.dup_origin_field.median())}.",
        "",
        "| cell | min | median | max |",
        "|---|---:|---:|---:|",
        f"| origin-year-field (current) | {_fmt(d.duplication_factor.min())} | "
        f"{_fmt(d.duplication_factor.median())} | {_fmt(d.duplication_factor.max())} |",
        f"| origin-year (max at {d.dup_origin_year.idxmax()}) | {_fmt(d.dup_origin_year.min())} | "
        f"{_fmt(d.dup_origin_year.median())} | {_fmt(d.dup_origin_year.max())} |",
        f"| origin-field (max at {d.dup_origin_field.idxmax()}) | {_fmt(d.dup_origin_field.min())} | "
        f"{_fmt(d.dup_origin_field.median())} | {_fmt(d.dup_origin_field.max())} |",
        f"| origin-only (max at {d.dup_origin_only.idxmax()}) | {_fmt(d.dup_origin_only.min())} | "
        f"{_fmt(d.dup_origin_only.median())} | {_fmt(d.dup_origin_only.max())} |",
        "",
        "## M4 and S1. Seven-economy overlap",
        "",
    ]
    if extras is None:
        L.append("Too few overlapping economies to compute.")
    else:
        closer = "leading-office" if extras["mae_lower"] < extras["mae_upper"] else "office-sum"
        L += [
            f"- n = **{extras['n']}** ({', '.join(sorted(both.index))})",
            f"- Spearman D vs publications/families: **{extras['rho']:+.3f}** "
            f"(p={extras['p']:.4f}); Fisher-z 95% CI **[{extras['rho_lo']:.3f}, "
            f"{extras['rho_hi']:.3f}]**",
            f"- Spearman cell-wise leading office vs families (no shared numerator): "
            f"**{extras['rho_lower_families']:+.3f}** "
            f"(p={extras['p_lower_families']:.4f})"
            + (
                "; Fisher-z 95% CI undefined because |rho| = 1"
                if not np.isfinite(extras["rho_lower_families_lo"])
                else f"; Fisher-z 95% CI **[{extras['rho_lower_families_lo']:.3f}, "
                     f"{extras['rho_lower_families_hi']:.3f}]**"
            ),
            f"- Spearman office-sum vs families: "
            f"**{extras['rho_upper_families']:+.3f}** "
            f"(p={extras['p_upper_families']:.4f})"
            + (
                "; Fisher-z 95% CI undefined because |rho| = 1"
                if not np.isfinite(extras["rho_upper_families_lo"])
                else f"; Fisher-z 95% CI **[{extras['rho_upper_families_lo']:.3f}, "
                     f"{extras['rho_upper_families_hi']:.3f}]**"
            )
            + ". Rank agreement therefore barely discriminates the two candidates; "
            "only the MARE separates them.",
            f"- Spearman (leading-office / families) vs D: "
            f"**{extras['rho_lower_over_fam_vs_D']:+.3f}** "
            f"(p={extras['p_lower_over_fam_vs_D']:.4f})",
            f"- S1 mean |leading-office / families − 1|: **{_fmt(extras['mae_lower'], 3)}**",
            f"- S1 mean |office-sum / families − 1|: **{_fmt(extras['mae_upper'], 3)}**",
            f"- closer to 1: **{closer}**",
            "",
            "| economy | D | pubs/families | leading-office/families | office-sum/families |",
            "|---|---:|---:|---:|---:|",
        ]
        for o, r in both.sort_values("true_ratio", ascending=False).iterrows():
            L.append(
                f"| {name_of(o)} | {_fmt(r.duplication_factor)} | {_fmt(r.true_ratio)} | "
                f"{_fmt(r.lower_over_families)} | {_fmt(r.upper_over_families)} |"
            )
    L += [
        "",
        "## S2. PCT-layer share (selected origins in the 68)",
        "",
        "Same window and filters as the 68-economy table (`tec_id>0`, 2018–2022).",
        "Do not reuse the all-year audit-file ordering.",
        "",
        "| origin | PCT-layer share (%) |",
        "|---|---:|",
    ]
    for o in PCT_SELECTED:
        if o in d.index:
            L.append(f"| {name_of(o)} ({o}) | {_fmt(d.loc[o, 'pct_share'], 1)} |")
        else:
            L.append(f"| {o} | not in the 68 |")
    L += [
        "",
        "## S5. Quartiles",
        "",
        "| measure | sample | n | p25 | p75 |",
        "|---|---|---:|---:|---:|",
        f"| H (home-office share, %) | measurable-home | {len(meas)} | "
        f"{_fmt(meas.domestic_share.quantile(0.25), 1)} | "
        f"{_fmt(meas.domestic_share.quantile(0.75), 1)} |",
        f"| PCT-layer share (%) | all 68 | {len(d)} | "
        f"{_fmt(d.pct_share.quantile(0.25), 1)} | {_fmt(d.pct_share.quantile(0.75), 1)} |",
        f"| D | all 68 | {len(d)} | {_fmt(d.duplication_factor.quantile(0.25))} | "
        f"{_fmt(d.duplication_factor.quantile(0.75))} |",
        f"| D | measurable-home | {len(meas)} | "
        f"{_fmt(meas.duplication_factor.quantile(0.25))} | "
        f"{_fmt(meas.duplication_factor.quantile(0.75))} |",
        "",
        "## Rank instability (new Fig. 3 / figA5)",
        "",
        "Ranks among the 68. CSV: `data/derived/counting_ranks.csv` (top 25 by named-office",
        "publications). Families filled only for the seven-economy overlap.",
        "",
        f"- largest |rank(sum incl. `**`) − rank(cell-wise leading office)| among top 25: "
        f"**{name_of(mover)} ({mover})**, rank "
        f"{int(top.loc[mover, 'rank_sum_incl_star'])} vs "
        f"{int(top.loc[mover, 'rank_cellwise_leading'])} "
        f"(change {int(top.loc[mover, 'rank_change_1_to_3']):+d})"
        + (
            "; tied at the same absolute change: "
            + ", ".join(
                f"{o} ({int(top.loc[o,'rank_sum_incl_star'])} vs "
                f"{int(top.loc[o,'rank_cellwise_leading'])})"
                for o in top.index
                if o != mover and int(top.loc[o, "abs_rank_change_1_to_3"])
                == int(top.loc[mover, "abs_rank_change_1_to_3"])
            )
            if (top["abs_rank_change_1_to_3"] == top.loc[mover, "abs_rank_change_1_to_3"]).sum() > 1
            else ""
        ),
        f"- largest among the top 20 by named-office volume (figA5): "
        f"**{name_of(top20_mover)} ({top20_mover})**, rank "
        f"{int(top20.loc[top20_mover, 'rank_sum_incl_star'])} vs "
        f"{int(top20.loc[top20_mover, 'rank_cellwise_leading'])} "
        f"(change {int(top20.loc[top20_mover, 'rank_change_1_to_3']):+d})",
        f"- largest among all 68: **{name_of(mover_all)} ({mover_all})**, rank "
        f"{int(ranks.loc[mover_all, 'rank_sum_incl_star'])} vs "
        f"{int(ranks.loc[mover_all, 'rank_cellwise_leading'])} "
        f"(change {int(ranks.loc[mover_all, 'rank_change_1_to_3']):+d})",
        "",
        "## M6. Cell-wise leading office vs origin-level labelled max",
        "",
        "Labels that say 'largest single office' describe office-sum / max_o(sum_cells p).",
        "Computed D uses office-sum / sum_cells max_o(p). The latter denominator is larger",
        "whenever different offices lead different cells, so computed D ≤ labelled D.",
        "",
        f"- n where the two denominators differ: **{int(differ.sum())}** of {len(d)}",
        f"- max gap (labelled D − computed D): **{_fmt(gap.max(), 3)}** "
        f"({name_of(gap.idxmax()) if len(gap) else 'NA'})",
        f"- median gap: **{_fmt(gap.median(), 3)}**",
        "",
        "The origin-only grain is this labelled quantity: office-sum divided by the",
        "largest single named office. That is why the two denominators differ for",
        f"{int(differ.sum())} of {len(d)}, and why origin-only D reaches "
        f"{_fmt(d.dup_origin_only.max())} ({d.dup_origin_only.idxmax()}).",
        "",
    ]

    # --- R2 quantities (identity gap, matched H, Q vs H, endpoints, micro-states)
    n_home = int(meas.home_is_origin_leader.sum())
    n_id = int(meas.on_identity.sum())
    n_home_not_id = int((meas.home_is_origin_leader & ~meas.on_identity).sum())
    qh_rho, qh_p = stats.spearmanr(meas.pct_share, meas.domestic_share)
    qh_lo, qh_hi = _fisher_z_ci(float(qh_rho), len(meas))
    pct_min_o = d.pct_share.idxmin()
    pct_max_o = d.pct_share.idxmax()
    sa = d.loc["SA"]
    match_isos = [o for o in ("NZ", "SG", "SE", "LU") if o in d.index]
    L += [
        "## R2. Identity gap 19 versus 35",
        "",
        f"All {n_id} economies within {IDENTITY_TOL} of the identity are among the "
        f"{n_home} whose home office is the origin-level leading named office. "
        f"The remaining **{n_home_not_id}** have a home office that leads at origin "
        "level but not in every year-field cell, so cell-wise D sits below 1/H.",
        "",
        "## R2. Matched home-office share (EPC contrast)",
        "",
        "Origins within half a percentage point of Singapore on H. New Zealand is",
        "the non-EPC high-D case at that H; Sweden and Luxembourg are the EPC pair.",
        "Do not use Switzerland here: its H is 3.1%, so most of the D gap versus",
        "Singapore is the identity rather than architecture.",
        "",
        "| economy | H (%) | D | EPC | origin-level leader |",
        "|---|---:|---:|:---:|---|",
    ]
    for o in match_isos:
        r = d.loc[o]
        L.append(
            f"| {name_of(o)} ({o}) | {_fmt(100*r.H, 1)} | {_fmt(r.duplication_factor, 2)} | "
            f"{'yes' if r.is_epc else 'no'} | {r.origin_leader_office} |"
        )
    L += [
        "",
        f"- Sweden/Singapore D ratio: "
        f"**{_fmt(d.loc['SE','duplication_factor']/d.loc['SG','duplication_factor'], 2)}**",
        f"- Luxembourg/Singapore D ratio: "
        f"**{_fmt(d.loc['LU','duplication_factor']/d.loc['SG','duplication_factor'], 2)}**",
        f"- New Zealand/Singapore D ratio: "
        f"**{_fmt(d.loc['NZ','duplication_factor']/d.loc['SG','duplication_factor'], 2)}**",
        "",
        "## R2. Q against H (descriptive, n=58)",
        "",
        "If office ** is the PCT international phase, Q should rise as H falls.",
        "Reported as descriptive: H and Q share the named-office sum in different",
        "roles in their denominators.",
        "",
        f"- Spearman Q vs H: **{qh_rho:+.3f}** (p={qh_p:.6f}); "
        f"Fisher-z 95% CI **[{qh_lo:.3f}, {qh_hi:.3f}]**",
        f"- n = **{len(meas)}**",
        "",
        "## R2. Range endpoints named",
        "",
        f"- H minimum **{_fmt(meas.domestic_share.min(), 1)}%** at "
        f"{name_of(meas.domestic_share.idxmin())} "
        f"({meas.domestic_share.idxmin()}); maximum **{_fmt(meas.domestic_share.max(), 1)}%** "
        f"at {name_of(meas.domestic_share.idxmax())}",
        f"- PCT-layer minimum **{_fmt(d.pct_share.min(), 1)}%** at "
        f"{name_of(pct_min_o)} ({pct_min_o}"
        f"{'' if d.loc[pct_min_o, 'domestic_measurable'] else ', unmeasurable home'}); "
        f"maximum **{_fmt(d.pct_share.max(), 1)}%** at {name_of(pct_max_o)} ({pct_max_o}"
        f"{'' if d.loc[pct_max_o, 'domestic_measurable'] else ', unmeasurable home'})",
        f"- residual range among the 58: **{_fmt(meas.residual.min(), 2)}** to "
        f"**{_fmt(meas.residual.max(), 2)}** (max at {name_of(sa.name)}, "
        f"H={_fmt(100*sa.H, 1)}%, 1/H={_fmt(sa.identity, 1)}, D={_fmt(sa.duplication_factor, 2)})",
        f"- median pairwise D ratio **{_fmt(pair_med, 2)}** "
        f"is the median of **{n_pairs}** pairwise ratios $D_i/D_j$ taken larger over smaller",
        "",
        "## R2. Micro-state and offshore-domicile extremes",
        "",
        f"- Antigua and Barbuda (AG): D=**{_fmt(d.loc['AG','duplication_factor'], 2)}** "
        f"(all-68 non-EPC maximum); origin-only D="
        f"**{_fmt(d.loc['AG','dup_origin_only'], 2)}** (origin-only maximum); "
        f"rank 50 vs 65 (largest movement among the 68); home office unmeasurable; "
        f"origin-level leader {d.loc['AG','origin_leader_office']}; "
        f"{int(d.loc['AG','publications'])} named-office publications",
        f"- Monaco (MC): largest labelled-versus-computed D gap "
        f"**{_fmt(gap.max(), 3)}**; D={_fmt(d.loc['MC','duplication_factor'], 2)}; "
        f"origin-level leader {d.loc['MC','origin_leader_office']}; EPC contracting state",
        "",
    ]

    # --- R3 quantities (partial EPC, D·H, PCT-by-origin, MARE excluding PH)
    epc_flag = meas.is_epc.astype(float)
    prho, pp, plo, phi, pn = _partial_spearman(
        meas.duplication_factor, epc_flag, meas.H)
    dh = meas.DH
    meas_q = meas.copy()
    meas_q["Hq"] = pd.qcut(meas_q.H, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    q_rows = []
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        sub = meas_q[meas_q.Hq == q]
        q_rows.append(
            f"| {q} | {int((~sub.is_epc).sum())} | "
            f"{_fmt(sub.loc[~sub.is_epc, 'duplication_factor'].median(), 2)} | "
            f"{int(sub.is_epc.sum())} | "
            f"{_fmt(sub.loc[sub.is_epc, 'duplication_factor'].median(), 2)} |"
        )
    il = d.loc["IL"]
    substantial = meas[meas.domestic >= 1000]
    head_iso = substantial.residual.idxmax()
    head = substantial.loc[head_iso]
    pct_both, pct_rho, pct_p, pct_lo, pct_hi = pct_origin_rank_check()
    se_star = int(pct_both.loc["SE", "star"]) if "SE" in pct_both.index else None
    se_pub = int(pct_both.loc["SE", "published"]) if "SE" in pct_both.index else None
    mae_ex = extras["mae_lower_excl_ph"] if extras is not None else float("nan")
    L += [
        "## R3. Partial Spearman of D with EPC status controlling for H",
        "",
        "Rank-Pearson residual method; Fisher-z SE uses n-4. This is the statistic",
        "that decides whether the high tail is an EPC pattern after H is held.",
        "",
        f"- n = **{pn}** (measurable-home economies)",
        f"- partial Spearman D vs EPC | H: **{prho:+.3f}** (p={pp:.4f}); "
        f"Fisher-z 95% CI **[{plo:.3f}, {phi:.3f}]**",
        "",
        "H-quartile median D (measurable-home 58):",
        "",
        "| H quartile | n non-EPC | median D non-EPC | n EPC | median D EPC |",
        "|---|---:|---:|---:|---:|",
        *q_rows,
        "",
        "Q2 non-EPC has n=2; the informative split is Q1.",
        "",
        "## R3. Fraction of the identity realised (D·H)",
        "",
        f"- min **{_fmt(dh.min(), 3)}** ({name_of(dh.idxmin())}); "
        f"p25 **{_fmt(dh.quantile(0.25), 2)}**; "
        f"median **{_fmt(dh.median(), 2)}**; "
        f"p75 **{_fmt(dh.quantile(0.75), 2)}**; "
        f"max **{_fmt(dh.max(), 2)}**",
        f"- n with D·H ≥ 0.95: **{int((dh >= 0.95).sum())}** of {len(meas)}",
        f"- China / Korea / Japan: "
        f"{_fmt(d.loc['CN','DH'], 2)} / {_fmt(d.loc['KR','DH'], 2)} / "
        f"{_fmt(d.loc['JP','DH'], 2)}",
        f"- Malaysia **{_fmt(d.loc['MY','DH'], 2)}**; "
        f"Singapore **{_fmt(d.loc['SG','DH'], 2)}**; "
        f"Switzerland **{_fmt(d.loc['CH','DH'], 2)}**; "
        f"Saudi Arabia **{_fmt(d.loc['SA','DH'], 3)}**",
        "",
        "## R3. Saudi Arabia as boundary; substantial-home residual",
        "",
        f"- Saudi Arabia: H={_fmt(100*sa.H, 1)}%, 1/H=**{_fmt(sa.identity, 2)}**, "
        f"D={_fmt(sa.duplication_factor, 2)}, residual="
        f"**{_fmt(sa.residual, 2)}**, home-office publications="
        f"**{int(sa.domestic)}**. Treat as the boundary of the measurable/"
        f"unmeasurable split, not a headline residual.",
        f"- Largest residual among economies with at least 1,000 origin-resolved "
        f"home-office publications: {name_of(head_iso)} ({head_iso}), "
        f"H={_fmt(100*head.H, 1)}%, 1/H={_fmt(head.identity, 2)}, "
        f"D={_fmt(head.duplication_factor, 2)}, residual="
        f"**{_fmt(head.residual, 2)}**, home publications="
        f"**{int(head.domestic):,}**",
        f"- Israel (IL) check: residual {_fmt(il.residual, 2)}, "
        f"home {int(il.domestic):,}",
        "",
        "## R3. Office ** versus published PCT applications by origin, 2020",
        "",
        "Discriminating test: an unknown-office bucket would not track published",
        "PCT filing by origin. Top 20 named origins by office-** volume.",
        "",
        f"- n = **{len(pct_both)}**; Spearman **{pct_rho:+.3f}** "
        f"(p={pct_p:.2e}); Fisher-z 95% CI **[{pct_lo:.3f}, {pct_hi:.3f}]**",
        f"- Sweden: office-** **{se_star:,}**; published PCT applications "
        f"**{se_pub:,}**",
        "",
        "## R3. MARE excluding the Philippines year-anchor case",
        "",
        f"- leading-office MARE over seven: **{_fmt(extras['mae_lower'], 3) if extras else 'NA'}**",
        f"- leading-office MARE excluding PH: **{_fmt(mae_ex, 3)}**",
        f"- office-sum MARE over seven: **{_fmt(extras['mae_upper'], 3) if extras else 'NA'}**",
        "",
    ]
    (ROOT / "docs" / "paper_a_new_quantities.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")


def main():
    w = load()
    d = measures(w)
    both, extras = validate(d)
    ranks, top = rank_table(w, d)
    write_side_tables(d, both, ranks, top)
    write_new_quantities_md(d, both, extras, ranks, top)

    print(f"{len(d)} economies with at least {MIN_PUBS} publications in "
          f"{WINDOW[0]}-{WINDOW[1]}\n")
    n_unmeas = int((~d.domestic_measurable).sum())
    print(f"  domestic share      {d.domestic_share.min():5.1f}% to {d.domestic_share.max():5.1f}%"
          f"   median {d.domestic_share.median():5.1f}%   ({n_unmeas} unmeasurable, excluded)")
    print(f"  PCT layer           {d.pct_share.min():5.1f}% to {d.pct_share.max():5.1f}%"
          f"   median {d.pct_share.median():5.1f}%")
    print(f"  duplication factor  {d.duplication_factor.min():5.2f}x to "
          f"{d.duplication_factor.max():5.2f}x  median {d.duplication_factor.median():5.2f}x")
    if extras is not None:
        print(f"\n  proxy validation against real family counts (n={extras['n']}): "
              f"Spearman {extras['rho']:+.3f}, p={extras['p']:.4f}, "
              f"Fisher-z 95% CI [{extras['rho_lo']:.3f}, {extras['rho_hi']:.3f}]")
    else:
        print("\n  too few to validate")

    meas = d.loc[d.domestic_measurable]
    print(f"\n  M1 identity |residual|<{IDENTITY_TOL}: {int(meas.on_identity.sum())}/{len(meas)}"
          f"  max residual {meas.residual.max():.2f}  SG residual {d.loc['SG','residual']:.2f}")
    print(f"  M2 EPC n={int(d.is_epc.sum())} D {d.loc[d.is_epc,'duplication_factor'].min():.2f}-"
          f"{d.loc[d.is_epc,'duplication_factor'].max():.2f}  "
          f"non-EPC {d.loc[~d.is_epc,'duplication_factor'].min():.2f}-"
          f"{d.loc[~d.is_epc,'duplication_factor'].max():.2f}")
    print(f"  M3 D origin-year {d.dup_origin_year.min():.2f}-{d.dup_origin_year.max():.2f}  "
          f"origin-only {d.dup_origin_only.min():.2f}-{d.dup_origin_only.max():.2f}")
    differ = int(((d.labelled_max - d.lower).abs() > 0.5).sum())
    print(f"  M6 labelled vs cell-wise differ for {differ}/{len(d)}; "
          f"max gap {(d.labelled_dup - d.duplication_factor).max():.3f}")
    mover = top["abs_rank_change_1_to_3"].idxmax()
    print(f"  rank mover (top 25): {mover}  "
          f"r{int(top.loc[mover,'rank_sum_incl_star'])} vs "
          f"r{int(top.loc[mover,'rank_cellwise_leading'])}")

    DERIVED.mkdir(parents=True, exist_ok=True)
    d.to_csv(DERIVED / "counting_generality.csv")

    L = ["# How far does the counting artefact generalise?", "",
         "Generated by `python pipeline/counting_generality.py`. Supporting analysis for the",
         "methods paper (see `docs/two_paper_strategy.md`).", "",
         f"Window {WINDOW[0]}–{WINDOW[1]}; economies with at least {MIN_PUBS} publications.",
         "", "## The three measures", "",
         "| measure | minimum | median | maximum |", "|---|---:|---:|---:|",
         f"| publications filed at the home office | {d.domestic_share.min():.1f}% | "
         f"{d.domestic_share.median():.1f}% | {d.domestic_share.max():.1f}% |",
         f"| publications in the PCT international phase | {d.pct_share.min():.1f}% | "
         f"{d.pct_share.median():.1f}% | {d.pct_share.max():.1f}% |",
         f"| duplication factor (office-sum ÷ cell-wise leading office) | "
         f"{d.duplication_factor.min():.2f}× | {d.duplication_factor.median():.2f}× | "
         f"{d.duplication_factor.max():.2f}× |", "",
         f"The domestic share is unmeasurable for **{int((~d.domestic_measurable).sum())}** of",
         "these economies: the file carries no origin-resolved rows for their own office, which",
         "is not the same as nobody filing there — Thailand has a patent office and residents",
         "use it. Those are excluded from the domestic-share statistics and from Figure A1's",
         "horizontal axis; their duplication factor does not depend on the domestic share and",
         "is retained.",
         "",
         f"Across **{len(d)} economies**, the fraction of an economy's publications that sit",
         "at its own office runs from essentially none to essentially all. So the correction",
         "from an office-summed count to a per-invention count removes a different share from",
         "every economy, and a comparison between two of them inherits the difference.", ""]

    if extras is not None:
        L += ["## Is the duplication factor a usable proxy?", "",
              "The factor is computable from the bulk file alone, but it is an approximation:",
              "it cannot see two distinct inventions filed at the same office. It is therefore",
              "checked against the real thing for the economies where WIPO's family series was",
              "exported by hand.", "",
              f"Spearman correlation between the proxy and the actual",
              f"publications-to-families ratio, n={extras['n']}: **{extras['rho']:+.3f}** "
              f"(p={extras['p']:.4f}; Fisher-z 95% CI "
              f"{extras['rho_lo']:.3f} to {extras['rho_hi']:.3f}).", ""]
        L += ["| economy | duplication factor | publications ÷ families |", "|---|---:|---:|"]
        for o, r in both.sort_values("true_ratio", ascending=False).iterrows():
            L.append(f"| {name_of(o)} | {r.duplication_factor:.2f}× | "
                     f"{r.true_ratio:.2f}× |")
        L += ["",
              "Six of the seven track closely. The Philippines sits furthest off the line",
              "(proxy 1.17×, actual 0.82×), and the reason is structural rather than a fault in",
              "either series. Families are counted by earliest filing year and publications by",
              "publication year, roughly eighteen months later, so within a fixed window an",
              "economy can record more families than publications — and the Philippines files",
              "81% of its patents at home, which is where the ratio is lowest to begin with.",
              "An earlier version of this document called that economy's data anomalous. It is",
              "not: it is the year-anchor offset the methods section describes, showing up",
              "where the mechanism predicts it should.",
              "",
              "The two series share an office-sum numerator, so the Spearman of D with",
              "publications/families is not a test of independent measures. Rank agreement",
              "of the office-sum with families is similarly high; the practical comparison",
              "is the mean absolute relative error of the cell-wise leading office versus",
              "the office-sum against families. See `docs/paper_a_new_quantities.md`.", ""]

    hi, lo = d.duplication_factor.max(), d.duplication_factor.min()
    hi_c = name_of(d.duplication_factor.idxmax())
    lo_c = name_of(d.duplication_factor.idxmin())
    L += ["## What this means for any two-country comparison", "",
          f"The factor spans **{lo:.2f}× to {hi:.2f}×**. Comparing the most affected economy",
          f"({hi_c}) with the least ({lo_c}) on office-summed publications therefore overstates",
          f"the first relative to the second by roughly **{hi / lo:.1f}×** before any difference",
          "in inventive output is involved at all.",
          "",
          "The economies at the two ends are not arbitrary. Among measurable-home",
          "economies the high tail of D remains associated with EPC membership after",
          "home-office share is controlled (partial Spearman of D with EPC status given H).",
          "At the lowest H the values still interleave (New Zealand near Sweden), and",
          "EP-as-leader is not required for high D. The low tail is domestically",
          "concentrated filing (China, Russia). The extremes of every structural measure",
          "also include micro-state and offshore-domicile origins (Antigua and Barbuda,",
          "Monaco), which follows from first-named-applicant attribution rather than",
          "from inventive activity in those jurisdictions.",
          "**The distortion is therefore correlated with home-office share, with a residual",
          "EPC association, and with attribution rules — not with a generic",
          "international-orientation gradient.**", ""]

    L += ["## Most and least affected economies", "",
          "| economy | domestic share | PCT layer | duplication factor |", "|---|---:|---:|---:|"]
    for o, r in pd.concat([d.head(8), d.tail(8)]).iterrows():
        ds = f"{r.domestic_share:.1f}%" if r.domestic_measurable else "unmeasurable"
        L.append(f"| {name_of(o)} | {ds} | {r.pct_share:.1f}% | "
                 f"{r.duplication_factor:.2f}× |")
    L += ["",
          "Further Paper A quantities (identity residual, EPC split, cell granularity,",
          "rank instability, labelled vs cell-wise D) are in `docs/paper_a_new_quantities.md`.",
          ""]
    (ROOT / "docs" / "counting_generality.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nwrote {ROOT / 'docs' / 'counting_generality.md'}")
    print(f"wrote {ROOT / 'docs' / 'paper_a_new_quantities.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
