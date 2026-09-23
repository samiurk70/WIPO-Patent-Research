"""Recompute every numeric claim in Paper A/main.tex from raw/derived data,
write numbers.json, and scan the manuscript for numeric tokens that no
recomputed quantity accounts for.

  python pipeline/check_numbers.py            # gate: exit 1 on any value mismatch
  python pipeline/check_numbers.py --strict   # also fail on manuscript orphan numbers
  python pipeline/check_numbers.py --report    # verbose, never exits non-zero
"""
import sys

import pandas as pd

from _paths import DERIVED, WIPO_RAW as WIPO
from numbers_registry import Registry

REPORT = "--report" in sys.argv[1:]
STRICT = "--strict" in sys.argv[1:]

raw = pd.read_csv(WIPO / "dc_indicator_patent_4_publication_by_technology.csv")

FAM_END = 2022
_fam = pd.read_csv(DERIVED / "wipo_families_long.csv")
_fam = _fam[_fam.year <= FAM_END]
fam = _fam.pivot_table(index="year", columns="country", values="families").fillna(0)
fao = _fam.pivot_table(index="year", columns="country", values="foreign_oriented").fillna(0)

reg = Registry()
R = reg.record
N = reg.note_only

R("s3.wipo_records", len(raw), claimed=663584, tol=0,
  note="rows in the WIPO patent-publications-by-technology bulk file", printed=["663,584"])
R("s3.wipo_field_assignments", raw["count"].sum() / 1e6, claimed=50.2, tol=0.05, unit="million",
  note="publication-to-field assignments described by the file; whole counting, so this "
       "exceeds the number of publications", printed=["50.2"])
R("rq1.china.families.2000", fam.loc[2000, "China"], claimed=23079, tol=0,
  note="China patent families, 2000", printed=["23,079"])
R("rq1.china.families.2022", fam.loc[2022, "China"], claimed=1517232, tol=0,
  note="China patent families, 2022", printed=["1,517,232"])
R("rq1.singapore.families.2000", fam.loc[2000, "Singapore"], claimed=716, tol=0,
  note="Singapore families, 2000")
R("rq1.singapore.families.2022", fam.loc[2022, "Singapore"], claimed=3036, tol=0,
  note="Singapore families 2022", printed=["3,036"])
R("rq1.china.foreign_share.2022",
  100 * fao.loc[2022, "China"] / fam.loc[2022, "China"], claimed=3.6, tol=0.15, unit="%",
  note="share of Chinese families extended to a foreign office, 2022")
R("rq1.singapore.foreign_share.2022",
  100 * fao.loc[2022, "Singapore"] / fam.loc[2022, "Singapore"], claimed=91.9, tol=0.5,
  unit="%", note="share of Singaporean families extended to a foreign office, 2022")
_w = raw[raw.year.between(2018, 2022) & raw.origin.isin(["SG", "CN"])]
for _code, _key, _claim in (("SG", "singapore", 20.2), ("CN", "china", 3.9)):
    _c = _w[_w.origin == _code]
    R(f"s3.pct_layer.share_{_key}",
      100 * _c[_c.office == "**"]["count"].sum() / _c["count"].sum(),
      claimed=_claim, tol=0.1, unit="%",
      note=f"PCT international phase as a share of {_key} publications, 2018-2022")

# --- Paper A quantities. Recomputed from counting_generality.csv.
_genp = DERIVED / "counting_generality.csv"
if _genp.exists():
    import numpy as _np  # noqa: E402
    from scipy import stats as _st  # noqa: E402
    import itertools as _it  # noqa: E402

    def _fisher_z_ci(rho, n, alpha=0.05, n_controls=0):
        df_se = n - 3 - n_controls
        if df_se <= 0 or not _np.isfinite(rho) or abs(rho) >= 1:
            return float("nan"), float("nan")
        z = _np.arctanh(rho)
        se = 1.0 / _np.sqrt(df_se)
        zc = float(_st.norm.ppf(1 - alpha / 2))
        return float(_np.tanh(z - zc * se)), float(_np.tanh(z + zc * se))

    _gen = pd.read_csv(_genp, index_col=0)
    R("paper_a.n_economies", len(_gen), claimed=68, tol=0,
      note="economies with at least 500 publications, 2018-2022, unknown origin excluded")
    R("paper_a.min_pubs", 500, claimed=500, tol=0,
      note="publication threshold for inclusion in the 68-economy set")
    R("paper_a.min_pubs_low", 200, claimed=200, tol=0,
      note="lower publication threshold used in the sensitivity sentence")
    R("paper_a.min_pubs_high", 1000, claimed=1000, tol=0, printed=["1,000", "1000"],
      note="higher publication threshold used in the sensitivity sentence")
    R("paper_a.n_unmeasurable", int((~_gen.domestic_measurable).sum()), claimed=10, tol=0,
      note="economies whose own office is not origin-resolved; domestic share excluded, not zero")
    R("paper_a.n_measurable", int(_gen.domestic_measurable.sum()), claimed=58, tol=0,
      note="economies with a measurable home-office share (Figure A1 horizontal axis)")
    _dom = _gen.loc[_gen.domestic_measurable, "domestic_share"]
    R("paper_a.domestic.min", _dom.min(), claimed=0.3, tol=0.05, unit="%",
      note="lowest measurable home-office share")
    R("paper_a.domestic.median", _dom.median(), claimed=37.8, tol=0.2, unit="%",
      note="median measurable home-office share")
    R("paper_a.domestic.max", _dom.max(), claimed=95.4, tol=0.1, unit="%",
      note="highest measurable home-office share (China)")
    R("paper_a.pct.min", _gen.pct_share.min(), claimed=3.2, tol=0.1, unit="%",
      note="smallest PCT-international-phase share")
    R("paper_a.pct.median", _gen.pct_share.median(), claimed=15.1, tol=0.2, unit="%",
      note="median PCT-international-phase share")
    R("paper_a.pct.max", _gen.pct_share.max(), claimed=54.4, tol=0.2, unit="%",
      note="largest PCT-international-phase share")
    R("paper_a.dup.min", _gen.duplication_factor.min(), claimed=1.05, tol=0.01,
      note="smallest office-sum / cell-wise leading office")
    R("paper_a.dup.median", _gen.duplication_factor.median(), claimed=2.27, tol=0.02,
      note="median office-sum / cell-wise leading office")
    R("paper_a.dup.max", _gen.duplication_factor.max(), claimed=4.48, tol=0.02,
      note="largest office-sum / cell-wise leading office")
    R("paper_a.dup.ratio", _gen.duplication_factor.max() / _gen.duplication_factor.min(),
      claimed=4.3, tol=0.05,
      note="how far an office-summed comparison can overstate the high-duplication economy")
    R("paper_a.china.domestic", _gen.loc["CN", "domestic_share"], claimed=95.4, tol=0.1, unit="%",
      note="China home-office share of publications, 2018-2022")
    R("paper_a.singapore.domestic", _gen.loc["SG", "domestic_share"], claimed=5.0, tol=0.2, unit="%",
      note="Singapore home-office share of publications, 2018-2022")
    _fam_g = pd.read_csv(DERIVED / "wipo_families_long.csv")
    _fam_g = _fam_g[_fam_g.year.between(2018, 2022)].groupby("origin")["families"].sum()
    _both = _gen.join(_fam_g.rename("families"), how="inner")
    _both = _both[_both.families > 0].copy()
    _both["true_ratio"] = _both.publications / _both.families
    if len(_both) >= 5:
        _rho, _p = _st.spearmanr(_both.duplication_factor, _both.true_ratio)
        _both["abs_dev"] = (_both.duplication_factor - _both.true_ratio).abs()
        R("paper_a.proxy.n", len(_both), claimed=7, tol=0,
          note="economies where the duplication proxy can be checked against real families")
        R("paper_a.proxy.rho", float(_rho), claimed=0.964, tol=0.005,
          note="Spearman correlation of the proxy with publications/families")
        R("paper_a.proxy.p", float(_p), claimed=0.0005, tol=0.0001, printed=["0.0005"],
          note="p-value of paper_a.proxy.rho")
        R("paper_a.proxy.mae", float(_both.abs_dev.mean()), claimed=0.19, tol=0.02,
          note="mean absolute deviation of the proxy from publications/families")
        R("paper_a.proxy.max_abs_dev", float(_both.abs_dev.max()), claimed=0.56, tol=0.02,
          note="largest absolute deviation of the proxy (Singapore)")
        _lo, _hi = _fisher_z_ci(float(_rho), len(_both))
        R("paper_a.proxy.rho_ci_lo", _lo, claimed=0.771, tol=0.005,
          note="Fisher-z 95% CI lower bound on Spearman D vs publications/families")
        R("paper_a.proxy.rho_ci_hi", _hi, claimed=0.995, tol=0.005,
          note="Fisher-z 95% CI upper bound on Spearman D vs publications/families")
        _rho_lf, _p_lf = _st.spearmanr(_both.lower, _both.families)
        R("paper_a.proxy.rho_lower_families", float(_rho_lf), claimed=1.0, tol=0.001,
          note="Spearman of cell-wise leading office vs families; no shared numerator")
        R("paper_a.proxy.p_lower_families", float(_p_lf), claimed=0.0, tol=0.0001,
          note="p-value of paper_a.proxy.rho_lower_families")
        _rho_uf, _p_uf = _st.spearmanr(_both.upper, _both.families)
        R("paper_a.proxy.rho_upper_families", float(_rho_uf), claimed=0.964, tol=0.005,
          note="Spearman of office-sum vs families over the seven; rank barely discriminates")
        R("paper_a.proxy.p_upper_families", float(_p_uf), claimed=0.0005, tol=0.0001, printed=["0.0005"],
          note="p-value of paper_a.proxy.rho_upper_families")
        _both["lower_over_fam"] = _both.lower / _both.families
        _both["upper_over_fam"] = _both.upper / _both.families
        _rho_lfd, _p_lfd = _st.spearmanr(_both.lower_over_fam, _both.duplication_factor)
        R("paper_a.proxy.rho_lower_over_fam_vs_D", float(_rho_lfd), claimed=-0.214, tol=0.005,
          note="Spearman of (leading-office/families) vs D")
        R("paper_a.proxy.p_lower_over_fam_vs_D", float(_p_lfd), claimed=0.6445, tol=0.0005, printed=["0.6445"],
          note="p-value of paper_a.proxy.rho_lower_over_fam_vs_D")
        _mae_l = float((_both.lower_over_fam - 1.0).abs().mean())
        _mae_u = float((_both.upper_over_fam - 1.0).abs().mean())
        R("paper_a.s1.mae_leading_office", _mae_l, claimed=0.101, tol=0.002,
          note="mean |cell-wise leading office / families - 1| over the seven")
        _mae_l_ex = float(
            _both.drop(index=["PH"], errors="ignore")["lower_over_fam"].sub(1.0).abs().mean()
        ) if "PH" in _both.index else float("nan")
        R("paper_a.s1.mae_leading_office_excl_ph", _mae_l_ex, claimed=0.069, tol=0.002,
          note="leading-office MARE over six, Philippines year-anchor case excluded")
        R("paper_a.s1.mae_office_sum", _mae_u, claimed=0.803, tol=0.002,
          note="mean |office-sum / families - 1| over the seven")
        R("paper_a.s1.leading_office_closer", 1.0 if _mae_l < _mae_u else 0.0, claimed=1, tol=0,
          note="1 if leading-office MAE is smaller than office-sum MAE")
        if "PH" in _both.index:
            R("paper_a.s1.ph.leading_over_fam",
              float(_both.loc["PH", "lower"] / _both.loc["PH", "families"]),
              claimed=0.70, tol=0.01,
              note="Philippines leading-office/families; year-anchor case set aside")
    R("paper_a.dup.median_58",
      _gen.loc[_gen.domestic_measurable, "duplication_factor"].median(),
      claimed=2.14, tol=0.02,
      note="median duplication factor among the 58 economies with a measurable home office")
    _f = _gen.duplication_factor.to_numpy()
    _pair = pd.Series([max(a, b) / min(a, b) for a, b in _it.combinations(_f, 2)])
    R("paper_a.dup.pair_median", float(_pair.median()), claimed=1.57, tol=0.02,
      note="median pairwise ratio of duplication factors across the 68 economies")
    R("paper_a.pct.office_star_2020",
      int(raw[(raw.office == "**") & (raw.year == 2020)]["count"].sum()),
      claimed=309728, tol=0, printed=["309,728"],
      note="publications under office ** in 2020")
    reg.external("paper_a.pct.wipo_applications_2020", 275900,
                 "WIPO PCT Yearly Review 2021, key numbers for 2020",
                 printed=["275,900", "275900"],
                 note="estimated PCT applications filed in 2020")
    R("paper_a.china_singapore.ratio.2018",
      fam.loc[2018, "China"] / fam.loc[2018, "Singapore"],
      claimed=470, tol=5, printed=["470"],
      note="China-to-Singapore, all families, 2018 truncation anchor")
    R("paper_a.china_singapore.ratio_foreign.2018",
      fao.loc[2018, "China"] / fao.loc[2018, "Singapore"],
      claimed=15, tol=1, printed=["15"],
      note="China-to-Singapore, foreign-oriented families, 2018 truncation anchor")
    R("paper_a.china_singapore.ratio.2019",
      fam.loc[2019, "China"] / fam.loc[2019, "Singapore"],
      claimed=416, tol=1, printed=["416"],
      note="China-to-Singapore all-families ratio in 2019; local minimum on figA4")

    # M1 identity
    _meas = _gen.loc[_gen.domestic_measurable]
    R("paper_a.identity.n_within_0_05", int(_meas.on_identity.sum()), claimed=19, tol=0,
      printed=["0.05"],
      note="measurable-home economies with |1/H - D| < 0.05")
    R("paper_a.identity.n_home_is_origin_leader",
      int(_meas.home_is_origin_leader.sum()), claimed=35, tol=0,
      note="measurable-home economies whose home office is the origin-level leading named office")
    R("paper_a.identity.max_residual", float(_meas.residual.max()), claimed=369.68, tol=0.05,
      note="largest 1/H - D among measurable-home economies (Saudi Arabia)")
    R("paper_a.identity.low_H.one_over_H", float(_meas.identity.max()), claimed=371.41, tol=0.02,
      note="1/H at the lowest measurable home-office share")
    for _iso, _slug, _h, _inv, _d, _res, _lead in (
        ("CN", "china", 95.4, 1.05, 1.05, 0.00, 1),
        ("KR", "korea", 68.1, 1.47, 1.47, 0.00, 1),
        ("JP", "japan", 55.4, 1.80, 1.80, 0.00, 1),
        ("MY", "malaysia", 47.9, 2.09, 2.00, 0.08, 1),
        ("PH", "philippines", 81.1, 1.23, 1.17, 0.07, 1),
        ("SG", "singapore", 5.0, 20.08, 2.60, 17.48, 0),
    ):
        r = _gen.loc[_iso]
        R(f"paper_a.identity.{_slug}.H", 100 * r.H, claimed=_h, tol=0.2, unit="%",
          note=f"{_slug} home-office share (percent)")
        R(f"paper_a.identity.{_slug}.one_over_H", r.identity, claimed=_inv, tol=0.02,
          note=f"{_slug} 1/H")
        R(f"paper_a.identity.{_slug}.D", r.duplication_factor, claimed=_d, tol=0.02,
          note=f"{_slug} duplication factor")
        R(f"paper_a.identity.{_slug}.residual", r.residual, claimed=_res, tol=0.02,
          note=f"{_slug} identity residual 1/H - D")
        R(f"paper_a.identity.{_slug}.home_is_leader",
          1.0 if bool(r.home_is_origin_leader) else 0.0, claimed=_lead, tol=0,
          note=f"{_slug}: 1 if home office is origin-level leading named office")

    # M2 EPC
    _epc = _gen.loc[_gen.is_epc]
    _non = _gen.loc[~_gen.is_epc]
    R("paper_a.epc.n", int(_gen.is_epc.sum()), claimed=35, tol=0,
      note="EPC contracting-state origins among the 68")
    R("paper_a.non_epc.n", int((~_gen.is_epc).sum()), claimed=33, tol=0,
      note="non-EPC origins among the 68")
    R("paper_a.epc.dup.min", float(_epc.duplication_factor.min()), claimed=1.15, tol=0.01,
      note="EPC duplication-factor minimum")
    R("paper_a.epc.dup.median", float(_epc.duplication_factor.median()), claimed=2.75, tol=0.02,
      note="EPC duplication-factor median")
    R("paper_a.epc.dup.max", float(_epc.duplication_factor.max()), claimed=4.48, tol=0.02,
      note="EPC duplication-factor maximum")
    R("paper_a.non_epc.dup.min", float(_non.duplication_factor.min()), claimed=1.05, tol=0.01,
      note="non-EPC duplication-factor minimum")
    R("paper_a.non_epc.dup.median", float(_non.duplication_factor.median()), claimed=1.73, tol=0.02,
      note="non-EPC duplication-factor median")
    R("paper_a.non_epc.dup.max", float(_non.duplication_factor.max()), claimed=4.10, tol=0.02,
      note="non-EPC duplication-factor maximum")
    R("paper_a.switzerland.D", float(_gen.loc["CH", "duplication_factor"]), claimed=4.48, tol=0.02,
      note="Switzerland duplication factor")
    R("paper_a.epc.measurable_top5_all_epc",
      1.0 if bool(_meas.duplication_factor.head(5).index.isin(
          _gen.index[_gen.is_epc]).all()) else 0.0,
      claimed=1, tol=0,
      note="1 if the five highest-D measurable-home economies are all EPC")

    # M3 cell granularity
    R("paper_a.m3.origin_year.min", float(_gen.dup_origin_year.min()), claimed=1.05, tol=0.01,
      note="D at origin-year cells, minimum")
    R("paper_a.m3.origin_year.median", float(_gen.dup_origin_year.median()), claimed=2.51, tol=0.02,
      note="D at origin-year cells, median")
    R("paper_a.m3.origin_year.max", float(_gen.dup_origin_year.max()), claimed=5.41, tol=0.02,
      note="D at origin-year cells, maximum")
    R("paper_a.m3.origin_only.min", float(_gen.dup_origin_only.min()), claimed=1.05, tol=0.01,
      note="D at origin-only cells, minimum")
    R("paper_a.m3.origin_only.median", float(_gen.dup_origin_only.median()), claimed=2.54, tol=0.02,
      note="D at origin-only cells, median")
    R("paper_a.m3.origin_only.max", float(_gen.dup_origin_only.max()), claimed=5.77, tol=0.02,
      note="D at origin-only cells, maximum")

    # S2 PCT-layer shares for the requested origins that sit in the 68
    for _iso, _slug, _claim in (
        ("RU", "russia", 4.5), ("CN", "china", 3.9), ("KR", "korea", 8.8),
        ("IN", "india", 7.5), ("JP", "japan", 14.3), ("DE", "germany", 13.7),
        ("US", "united_states", 13.3), ("NL", "netherlands", 16.6), ("SE", "sweden", 18.8),
    ):
        if _iso in _gen.index:
            R(f"paper_a.s2.{_slug}.pct_share", float(_gen.loc[_iso, "pct_share"]),
              claimed=_claim, tol=0.1, unit="%",
              note=f"{_slug} PCT-layer share of publications, 2018-2022")

    # S5 quartiles
    R("paper_a.s5.H.p25", float(_meas.domestic_share.quantile(0.25)), claimed=9.2, tol=0.1,
      unit="%", note="p25 of measurable home-office share")
    R("paper_a.s5.H.p75", float(_meas.domestic_share.quantile(0.75)), claimed=64.8, tol=0.1,
      unit="%", printed=["75"], note="p75 of measurable home-office share")
    R("paper_a.s5.H.n", int(len(_meas)), claimed=58, tol=0,
      note="n for home-office-share quartiles")
    R("paper_a.s5.pct.p25", float(_gen.pct_share.quantile(0.25)), claimed=12.7, tol=0.1,
      unit="%", note="p25 of PCT-layer share, 68 economies")
    R("paper_a.s5.pct.p75", float(_gen.pct_share.quantile(0.75)), claimed=18.6, tol=0.1,
      unit="%", note="p75 of PCT-layer share, 68 economies")
    R("paper_a.s5.pct.n", int(len(_gen)), claimed=68, tol=0,
      note="n for PCT-share quartiles")
    R("paper_a.s5.dup.p25", float(_gen.duplication_factor.quantile(0.25)), claimed=1.55, tol=0.02,
      note="p25 of D, 68 economies")
    R("paper_a.s5.dup.p75", float(_gen.duplication_factor.quantile(0.75)), claimed=3.34, tol=0.02,
      note="p75 of D, 68 economies")
    R("paper_a.s5.dup.n", int(len(_gen)), claimed=68, tol=0,
      note="n for D quartiles among the 68")
    R("paper_a.s5.dup58.p25", float(_meas.duplication_factor.quantile(0.25)), claimed=1.48, tol=0.02,
      note="p25 of D among measurable-home economies")
    R("paper_a.s5.dup58.p75", float(_meas.duplication_factor.quantile(0.75)), claimed=3.45, tol=0.02,
      note="p75 of D among measurable-home economies")
    R("paper_a.s5.dup58.n", int(len(_meas)), claimed=58, tol=0,
      note="n for D quartiles among measurable-home economies")

    # Rank instability
    _rk = pd.read_csv(DERIVED / "counting_ranks.csv", index_col=0)
    _rk68 = pd.read_csv(DERIVED / "counting_ranks_all68.csv", index_col=0)
    _top20 = _rk68.sort_values("sum_excl_star", ascending=False).head(20)
    _mv25 = _rk["abs_rank_change_1_to_3"].idxmax()
    _mv20 = _top20["abs_rank_change_1_to_3"].idxmax()
    _mv68 = _rk68["abs_rank_change_1_to_3"].idxmax()
    R("paper_a.rank.top25.n", len(_rk), claimed=25, tol=0,
      note="economies in the rank table (top 25 by named-office publications)")
    R("paper_a.rank.top25.max_abs_change",
      float(_rk.loc[_mv25, "abs_rank_change_1_to_3"]), claimed=8, tol=0,
      note="largest |rank incl ** minus rank cell-wise| among the top 25")
    R("paper_a.rank.top25.mover_rank_incl",
      float(_rk.loc[_mv25, "rank_sum_incl_star"]), claimed=23, tol=0,
      note="top-25 largest-mover rank under office-sum including **")
    R("paper_a.rank.top25.mover_rank_cellwise",
      float(_rk.loc[_mv25, "rank_cellwise_leading"]), claimed=15, tol=0,
      note="top-25 largest-mover rank under cell-wise leading office")
    for _iso, _slug, _incl, _cell in (
        ("RU", "russia", 13, 6),
        ("TR", "turkiye", 23, 15),
        ("BR", "brazil", 24, 16),
        ("PL", "poland", 26, 18),
    ):
        R(f"paper_a.rank.{_slug}.incl",
          float(_rk.loc[_iso, "rank_sum_incl_star"]), claimed=_incl, tol=0,
          note=f"{_slug} rank under office-sum including **")
        R(f"paper_a.rank.{_slug}.cellwise",
          float(_rk.loc[_iso, "rank_cellwise_leading"]), claimed=_cell, tol=0,
          note=f"{_slug} rank under cell-wise leading office")
    R("paper_a.rank.top20.max_abs_change",
      float(_top20.loc[_mv20, "abs_rank_change_1_to_3"]), claimed=7, tol=0,
      note="largest |rank change col1 vs col3| among the top 20 by named-office volume")
    R("paper_a.rank.top20.mover_rank_incl",
      float(_top20.loc[_mv20, "rank_sum_incl_star"]), claimed=13, tol=0,
      note="top-20 largest-mover rank under office-sum including **")
    R("paper_a.rank.top20.mover_rank_cellwise",
      float(_top20.loc[_mv20, "rank_cellwise_leading"]), claimed=6, tol=0,
      note="top-20 largest-mover rank under cell-wise leading office")
    R("paper_a.rank.all68.max_abs_change",
      float(_rk68.loc[_mv68, "abs_rank_change_1_to_3"]), claimed=15, tol=0,
      note="largest |rank change col1 vs col3| among all 68")
    R("paper_a.rank.all68.mover_rank_incl",
      float(_rk68.loc[_mv68, "rank_sum_incl_star"]), claimed=50, tol=0,
      note="all-68 largest-mover rank under office-sum including **")
    R("paper_a.rank.all68.mover_rank_cellwise",
      float(_rk68.loc[_mv68, "rank_cellwise_leading"]), claimed=65, tol=0,
      note="all-68 largest-mover rank under cell-wise leading office")

    # M6 labelled vs cell-wise
    _gap = (_gen.labelled_dup - _gen.duplication_factor).clip(lower=0)
    _differ = (_gen.labelled_max - _gen.lower).abs() > 0.5
    R("paper_a.m6.n_differ", int(_differ.sum()), claimed=61, tol=0,
      note="economies where origin-level max office differs from the cell-wise leading-office sum")
    R("paper_a.m6.max_gap", float(_gap.max()), claimed=2.294, tol=0.005,
      note="max labelled D minus computed D")
    R("paper_a.m6.median_gap", float(_gap.median()), claimed=0.224, tol=0.005,
      note="median labelled D minus computed D")

    # R2: origin-field grain (temporal-spread component)
    R("paper_a.m3.origin_field.min", float(_gen.dup_origin_field.min()), claimed=1.05, tol=0.01,
      note="D at origin-field cells, minimum")
    R("paper_a.m3.origin_field.median", float(_gen.dup_origin_field.median()), claimed=2.39, tol=0.02,
      note="D at origin-field cells, median")
    R("paper_a.m3.origin_field.max", float(_gen.dup_origin_field.max()), claimed=4.90, tol=0.02,
      note="D at origin-field cells, maximum")

    # R2: measurable-home EPC split (primary base)
    _mepc = _meas.loc[_meas.is_epc]
    _mnon = _meas.loc[~_meas.is_epc]
    R("paper_a.epc.measurable.n", int(_mepc.shape[0]), claimed=32, tol=0,
      note="EPC contracting-state origins among the 58 with a measurable home office")
    R("paper_a.non_epc.measurable.n", int(_mnon.shape[0]), claimed=26, tol=0,
      note="non-EPC origins among the 58 with a measurable home office")
    R("paper_a.epc.measurable.dup.min", float(_mepc.duplication_factor.min()), claimed=1.15, tol=0.01,
      note="measurable-home EPC D minimum")
    R("paper_a.epc.measurable.dup.median", float(_mepc.duplication_factor.median()), claimed=2.82, tol=0.02,
      note="measurable-home EPC D median")
    R("paper_a.epc.measurable.dup.max", float(_mepc.duplication_factor.max()), claimed=4.48, tol=0.02,
      note="measurable-home EPC D maximum")
    R("paper_a.non_epc.measurable.dup.min", float(_mnon.duplication_factor.min()), claimed=1.05, tol=0.01,
      note="measurable-home non-EPC D minimum")
    R("paper_a.non_epc.measurable.dup.median", float(_mnon.duplication_factor.median()), claimed=1.63, tol=0.02,
      note="measurable-home non-EPC D median")
    R("paper_a.non_epc.measurable.dup.max", float(_mnon.duplication_factor.max()), claimed=3.87, tol=0.02,
      note="measurable-home non-EPC D maximum (New Zealand)")
    R("paper_a.epc.n_leader_ep", int((_gen.origin_leader_office == "EP").sum()), claimed=10, tol=0,
      note="origins whose origin-level leading named office is the EPO")
    R("paper_a.identity.n_home_leader_not_identity",
      int((_meas.home_is_origin_leader & ~_meas.on_identity).sum()), claimed=16, tol=0,
      note="home is origin-level leader but |1/H-D| >= 0.05")
    R("paper_a.dup.n_pairs", int(len(_pair)), claimed=2278, tol=0, printed=["2,278", "2278"],
      note="number of unordered pairs among the 68; median pairwise ratio is over these")
    R("paper_a.switzerland.H", 100 * float(_gen.loc["CH", "H"]), claimed=3.1, tol=0.1, unit="%",
      note="Switzerland home-office share")
    R("paper_a.sweden.H", 100 * float(_gen.loc["SE", "H"]), claimed=5.3, tol=0.1, unit="%",
      note="Sweden home-office share")
    R("paper_a.sweden.D", float(_gen.loc["SE", "duplication_factor"]), claimed=3.88, tol=0.02,
      note="Sweden duplication factor")
    R("paper_a.luxembourg.H", 100 * float(_gen.loc["LU", "H"]), claimed=5.5, tol=0.1, unit="%",
      note="Luxembourg home-office share")
    R("paper_a.luxembourg.D", float(_gen.loc["LU", "duplication_factor"]), claimed=4.44, tol=0.02,
      note="Luxembourg duplication factor")
    R("paper_a.new_zealand.H", 100 * float(_gen.loc["NZ", "H"]), claimed=4.8, tol=0.1, unit="%",
      note="New Zealand home-office share")
    R("paper_a.new_zealand.D", float(_gen.loc["NZ", "duplication_factor"]), claimed=3.87, tol=0.02,
      note="New Zealand duplication factor")
    R("paper_a.matched.se_over_sg",
      float(_gen.loc["SE", "duplication_factor"] / _gen.loc["SG", "duplication_factor"]),
      claimed=1.49, tol=0.02, note="Sweden/Singapore D ratio at matched H")
    R("paper_a.matched.lu_over_sg",
      float(_gen.loc["LU", "duplication_factor"] / _gen.loc["SG", "duplication_factor"]),
      claimed=1.71, tol=0.02, note="Luxembourg/Singapore D ratio at matched H")
    R("paper_a.saudi.H", 100 * float(_gen.loc["SA", "H"]), claimed=0.3, tol=0.05, unit="%",
      note="Saudi Arabia home-office share")
    R("paper_a.saudi.D", float(_gen.loc["SA", "duplication_factor"]), claimed=1.73, tol=0.02,
      note="Saudi Arabia duplication factor")
    R("paper_a.saudi.one_over_H", float(_gen.loc["SA", "identity"]), claimed=371.41, tol=0.02,
      note="Saudi Arabia 1/H")
    R("paper_a.saudi.home_pubs", float(_gen.loc["SA", "domestic"]), claimed=32, tol=0,
      note="Saudi Arabia origin-resolved home-office publications, 2018-2022")
    R("paper_a.antigua.D", float(_gen.loc["AG", "duplication_factor"]), claimed=4.10, tol=0.02,
      note="Antigua and Barbuda D; all-68 non-EPC maximum")
    R("paper_a.antigua.pubs", float(_gen.loc["AG", "publications"]), claimed=1592, tol=0,
      printed=["1,592", "1592"],
      note="Antigua and Barbuda named-office publications, 2018-2022")
    R("paper_a.monaco.D", float(_gen.loc["MC", "duplication_factor"]), claimed=2.56, tol=0.02,
      note="Monaco computed D")
    _qh, _qhp = _st.spearmanr(_meas.pct_share, _meas.domestic_share)
    _qh_lo, _qh_hi = _fisher_z_ci(float(_qh), len(_meas))
    R("paper_a.qh.rho", float(_qh), claimed=-0.559, tol=0.005,
      note="Spearman of PCT-layer share Q against home-office share H, n=58")
    R("paper_a.qh.p", float(_qhp), claimed=0.000005, tol=0.000001, printed=["0.000005"],
      note="p-value of paper_a.qh.rho")
    R("paper_a.qh.rho_ci_lo", _qh_lo, claimed=-0.714, tol=0.005,
      note="Fisher-z 95% CI lower bound on Spearman Q vs H")
    R("paper_a.qh.rho_ci_hi", _qh_hi, claimed=-0.352, tol=0.005,
      note="Fisher-z 95% CI upper bound on Spearman Q vs H")
    R("paper_a.s1.sg.abs_err",
      float(abs(_both.loc["SG", "lower"] / _both.loc["SG", "families"] - 1.0))
      if "SG" in _both.index else float("nan"),
      claimed=0.22, tol=0.01,
      note="Singapore |leading-office/families - 1|; largest genuine error among six")
    R("paper_a.russia.H", 100 * float(_gen.loc["RU", "H"]), claimed=91.9, tol=0.2, unit="%",
      note="Russia home-office share")

    # R3: partial Spearman D vs EPC | H, D·H, Israel residual, PCT-by-origin
    from counting_generality import _partial_spearman as _partial_spearman
    from _pct_published_2020 import PUBLISHED_PCT_APPLICATIONS_2020
    _prho, _pp, _plo, _phi, _pn = _partial_spearman(
        _meas.duplication_factor, _meas.is_epc.astype(float), _meas.H)
    R("paper_a.epc.partial_rho", _prho, claimed=0.413, tol=0.005,
      note="partial Spearman of D with EPC status controlling for H, n=58")
    R("paper_a.epc.partial_p", _pp, claimed=0.0016, tol=0.0002, printed=["0.0016"],
      note="p-value of paper_a.epc.partial_rho; t with df=n-4")
    R("paper_a.epc.partial_rho_ci_lo", _plo, claimed=0.171, tol=0.005,
      note="Fisher-z 95% CI lower bound on partial Spearman D vs EPC | H")
    R("paper_a.epc.partial_rho_ci_hi", _phi, claimed=0.608, tol=0.005,
      note="Fisher-z 95% CI upper bound on partial Spearman D vs EPC | H")
    R("paper_a.epc.partial_n", float(_pn), claimed=58, tol=0,
      note="n for the partial Spearman")
    _dh = _meas.duplication_factor * _meas.H
    R("paper_a.dh.min", float(_dh.min()), claimed=0.005, tol=0.001,
      note="minimum D·H among measurable-home economies (Saudi Arabia)")
    R("paper_a.dh.p25", float(_dh.quantile(0.25)), claimed=0.32, tol=0.01,
      note="p25 of D·H among the 58")
    R("paper_a.dh.median", float(_dh.median()), claimed=0.90, tol=0.01,
      note="median D·H among the 58")
    R("paper_a.dh.p75", float(_dh.quantile(0.75)), claimed=0.99, tol=0.01,
      note="p75 of D·H among the 58")
    R("paper_a.dh.max", float(_dh.max()), claimed=1.00, tol=0.01,
      note="maximum D·H among the 58")
    R("paper_a.dh.n_ge_095", float((_dh >= 0.95).sum()), claimed=23, tol=0,
      note="measurable-home economies with D·H at least 0.95")
    R("paper_a.dh.china", float(_gen.loc["CN", "duplication_factor"] * _gen.loc["CN", "H"]),
      claimed=1.00, tol=0.01, note="China D·H")
    R("paper_a.dh.korea", float(_gen.loc["KR", "duplication_factor"] * _gen.loc["KR", "H"]),
      claimed=1.00, tol=0.01, note="Korea D·H")
    R("paper_a.dh.japan", float(_gen.loc["JP", "duplication_factor"] * _gen.loc["JP", "H"]),
      claimed=1.00, tol=0.01, note="Japan D·H")
    R("paper_a.dh.malaysia", float(_gen.loc["MY", "duplication_factor"] * _gen.loc["MY", "H"]),
      claimed=0.96, tol=0.01, note="Malaysia D·H")
    R("paper_a.dh.singapore", float(_gen.loc["SG", "duplication_factor"] * _gen.loc["SG", "H"]),
      claimed=0.13, tol=0.01, note="Singapore D·H")
    R("paper_a.dh.switzerland", float(_gen.loc["CH", "duplication_factor"] * _gen.loc["CH", "H"]),
      claimed=0.14, tol=0.01, note="Switzerland D·H")
    R("paper_a.dh.saudi", float(_gen.loc["SA", "duplication_factor"] * _gen.loc["SA", "H"]),
      claimed=0.005, tol=0.001, note="Saudi Arabia D·H")
    R("paper_a.israel.H", 100 * float(_gen.loc["IL", "H"]), claimed=2.9, tol=0.1, unit="%",
      note="Israel home-office share")
    R("paper_a.israel.one_over_H", float(_gen.loc["IL", "identity"]), claimed=34.95, tol=0.02,
      note="Israel 1/H")
    R("paper_a.israel.D", float(_gen.loc["IL", "duplication_factor"]), claimed=2.55, tol=0.02,
      note="Israel duplication factor")
    R("paper_a.israel.residual", float(_gen.loc["IL", "residual"]), claimed=32.40, tol=0.02,
      note="Israel identity residual; largest among home-office block of at least 1,000")
    R("paper_a.israel.home_pubs", float(_gen.loc["IL", "domestic"]), claimed=1450, tol=0,
      printed=["1,450", "1450"],
      note="Israel origin-resolved home-office publications, 2018-2022")
    _mq = _meas.copy()
    _mq["Hq"] = pd.qcut(_mq.H, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    for _q, _epc_n, _epc_d, _non_n, _non_d in (
        ("q1", 9, 3.77, 6, 2.57),
        ("q2", 12, 3.67, 2, 2.84),
        ("q3", 7, 2.01, 7, 1.80),
        ("q4", 4, 1.33, 11, 1.23),
    ):
        _sub = _mq[_mq.Hq == _q.upper()]
        R(f"paper_a.epc.{_q}.n_epc", float(_sub.is_epc.sum()), claimed=_epc_n, tol=0,
          note=f"{_q.upper()} measurable-home EPC count")
        R(f"paper_a.epc.{_q}.n_non", float((~_sub.is_epc).sum()), claimed=_non_n, tol=0,
          note=f"{_q.upper()} measurable-home non-EPC count")
        R(f"paper_a.epc.{_q}.median_D_epc",
          float(_sub.loc[_sub.is_epc, "duplication_factor"].median()),
          claimed=_epc_d, tol=0.02, note=f"{_q.upper()} median D among EPC")
        R(f"paper_a.epc.{_q}.median_D_non",
          float(_sub.loc[~_sub.is_epc, "duplication_factor"].median()),
          claimed=_non_d, tol=0.02, note=f"{_q.upper()} median D among non-EPC")
    _star20 = (
        raw[(raw.office == "**") & (raw.year == 2020)]
        .groupby("origin")["count"].sum()
    )
    _star20 = _star20[_star20.index != "**"].sort_values(ascending=False).head(20)
    _both20 = pd.DataFrame({
        "star": _star20,
        "pct": pd.Series(PUBLISHED_PCT_APPLICATIONS_2020),
    }).dropna()
    _rho20, _p20 = _st.spearmanr(_both20["star"], _both20["pct"])
    _lo20, _hi20 = _fisher_z_ci(float(_rho20), len(_both20))
    R("paper_a.pct_origin.n", float(len(_both20)), claimed=20, tol=0,
      note="named origins in the 2020 office-** vs published-PCT rank check")
    R("paper_a.pct_origin.rho", float(_rho20), claimed=0.991, tol=0.002,
      note="Spearman of 2020 office-** publications vs published PCT applications by origin")
    R("paper_a.pct_origin.p", float(_p20), claimed=0.0, tol=1e-10,
      printed=["10^{-15}", "10^{-16}"],
      note="p-value of paper_a.pct_origin.rho")
    R("paper_a.pct_origin.rho_ci_lo", _lo20, claimed=0.977, tol=0.005,
      note="Fisher-z 95% CI lower bound on Spearman office-** vs published PCT")
    R("paper_a.pct_origin.rho_ci_hi", _hi20, claimed=0.997, tol=0.005,
      note="Fisher-z 95% CI upper bound on Spearman office-** vs published PCT")
    R("paper_a.pct_origin.sweden.star", float(_both20.loc["SE", "star"]), claimed=4356, tol=0,
      printed=["4,356", "4356"],
      note="Sweden 2020 publications under office **")
    reg.external("paper_a.pct_origin.sweden.published", 4356,
                 "WIPO PCT Yearly Review 2021, origin-level PCT applications for 2020",
                 printed=["4,356", "4356"],
                 note="Sweden published PCT applications, 2020")

# ------------------------------------------------------------------ output
reg.write_json()
orphans, orphan_err = reg.orphan_scan()

fail = bool(reg.failures) or (STRICT and bool(orphans))

if REPORT:
    print(f"{len(reg.entries)} quantities recorded -> numbers.json")
    print(f"\n{len(reg.failures)} blocking value mismatch(es):")
    for key, claimed, val, tol, note in reg.failures:
        print(f"  FAIL {key}: manuscript={claimed} recomputed={val:.4f} (tol {tol}) - {note}")
    print(f"\n{len(reg.waived)} waived mismatch(es):")
    for key, claimed, val, tol, note, reason in reg.waived:
        print(f"  WAIVED {key}: manuscript={claimed} recomputed={val:.4f} - {reason}")
    print(f"\norphan scan: {orphan_err or f'{len(orphans)} unresolved numeric token(s)'}"
          f" ({'blocking' if STRICT else 'report-only'})")
    for tok, ctx in orphans:
        print(f"  ? {tok:>12}   ...{ctx}...")
else:
    for key, claimed, val, tol, note in reg.failures:
        print(f"FAIL {key}: manuscript={claimed} recomputed={val:.4f} (tol {tol})")
    for key, claimed, val, tol, note, reason in reg.waived:
        print(f"waived {key}: {reason}")
    if STRICT and orphans:
        print(f"ORPHAN: {len(orphans)} manuscript number(s) absent from numbers.json")
        for tok, ctx in orphans:
            print(f"  {tok:>12}  ...{ctx}...")
    if not fail:
        tail = "" if STRICT else f"  ({len(orphans)} orphan token(s), report-only)"
        print(f"check_numbers: {len(reg.entries)} quantities OK, numbers.json written{tail}")

sys.exit(1 if fail else 0)
