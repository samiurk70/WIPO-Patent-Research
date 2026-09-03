r"""Load the hand-exported WIPO patent-family series (plan task 1.1, Option A).

WIPO publishes a country-level patent-family indicator, but only through the IP
Statistics Data Center's interactive interface -- it is in no bulk download, and the
interface is a single-page app served by an undocumented private API. Wiring the
pipeline to that API would give a reviewer a deposit that breaks without explanation,
so the export is done by hand, once, and then pinned like any other raw input.

That keeps ground rule 5 intact: the input is cached under data/raw/, checksummed into
MANIFEST.sha256 and stamped with its retrieval date. Only the *re-download* is manual,
and this script says so loudly if the file is missing rather than silently producing a
half-analysis.

    docs/wipo_family_export.md   what to export and in what shape
    data/raw/wipo_families/wipo_patent_families.csv   where to put it

Usage:
    python pipeline/load_wipo_families.py            # validate + build the derived table
    python pipeline/load_wipo_families.py --check    # validate only, exit 1 if unusable
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import RAW, DERIVED  # noqa: E402
from _countries import COUNTRIES  # noqa: E402

SRC_DIR = RAW / "wipo_families"
SRC = SRC_DIR / "wipo_patent_families.csv"
OUT = DERIVED / "wipo_families_long.csv"

# Companion measures, from the hand-exported indicator set. RQ1 reports 6a and 7 side by
# side: 6a is every family, 7 only those extended to a foreign office. The two answer
# different questions and disagree by a factor of 25 for China against Singapore, which
# is a result rather than a nuisance -- see docs/indicator_survey.md.
EXTRA_DIR = RAW / "wipo_requested_plus_extra"
MEASURES = {
    "families": ("patent_7 -", "foreign_oriented"),      # indicator 7
    "grant_year": ("patent_6b-", "families_grant_year"), # indicator 6b, robustness
}

REQUIRED = {"year", "origin", "families"}
MIN_YEAR, MAX_YEAR = 2000, 2020        # minimum span the export must cover to be usable

# Window actually used for RQ1. Decided 2026-09-02 from the exported series, not assumed:
# 2023 carries plainly artefactual country values (the Philippines at 7% of its own
# preceding five-year mean, Indonesia at 862%) while 2024 is blank for every origin. 2022
# is stable across every economy in the set, and it is also the last year of the
# publication file -- so RQ1 (families) and RQ2 (publication-level green share) share one
# 2000-2022 span instead of needing two windows explained.
WINDOW_END = 2022

# The Data Center's "Download CSV" gives a wide table -- one row per origin, one column
# per year -- and labels rows with country names, not ISO codes. Accept that shape as it
# comes rather than making someone reshape it by hand and introduce errors doing so.
NAME_TO_CODE = {v.lower(): k for k, v in COUNTRIES.items()}
NAME_TO_CODE.update({
    "republic of korea": "KR",
    "korea, republic of": "KR",
    "south korea": "KR",
    "korea (republic of)": "KR",
    "viet nam": "VN",
    "vietnam": "VN",
    "lao people's democratic republic": "LA",
    "lao pdr": "LA",
    "laos": "LA",
    "brunei darussalam": "BN",
    "brunei": "BN",
    "timor-leste": "TL",
    "timor leste": "TL",
    "myanmar": "MM",
    "philippines": "PH",
    "china": "CN",
    "japan": "JP",
})
# Deliberately not mapped: "China, Hong Kong SAR" and "China, Macao SAR" are separate
# origins in WIPO's list and are not part of the ASEAN-11 + CN/KR/JP study set. They are
# dropped with a note rather than treated as China or as an error.
NOT_IN_STUDY_SET = {"china, hong kong sar", "hong kong", "china, macao sar", "macao"}


def _missing() -> int:
    print(f"MISSING: {SRC}", file=sys.stderr)
    print(__doc__.split("Usage:")[0].strip(), file=sys.stderr)
    print("\nNothing downstream of this can run until the export exists. This is the one "
          "manual input in the pipeline and it is deliberate.", file=sys.stderr)
    return 1


def _to_code(label: str) -> str | None:
    """WIPO origin label -> the ISO2 code the rest of the pipeline uses."""
    t = str(label).strip()
    if t.upper() in COUNTRIES:                     # already a code
        return t.upper()
    return NAME_TO_CODE.get(t.lower())


def _read_export() -> tuple[pd.DataFrame, list[str]]:
    """Read the Data Center CSV, which leads with a metadata preamble.

    The download starts with five or so lines naming the IP right, the indicator and the
    database vintage, then a blank line, then the real header. Those lines are provenance
    -- they are the only machine-readable record of which indicator produced the file --
    so they are returned rather than skipped past silently.
    """
    lines = SRC.read_text(encoding="utf-8-sig").splitlines()
    header = next((i for i, ln in enumerate(lines)
                   if ln.lower().lstrip('"').startswith("origin")), None)
    if header is None:
        raise SystemExit(f"{SRC.name}: no header row starting with 'Origin'. "
                         f"See docs/wipo_family_export.md.")
    preamble = [ln.strip() for ln in lines[:header] if ln.strip()]
    from io import StringIO
    # index_col=False is load-bearing. Every data row ends with a trailing comma while
    # the header does not, so the rows carry one more field than the header. Left to
    # itself pandas resolves that by promoting the first column to the index, which
    # shifts every column left by one -- the country name becomes the index, the code
    # lands under "Origin", and the year-2000 counts land under "Office". It parses
    # cleanly and is entirely wrong.
    df = pd.read_csv(StringIO("\n".join(lines[header:])), index_col=False)
    # The export ends each row with a trailing comma, giving one unnamed empty column.
    df = df.drop(columns=[c for c in df.columns
                          if str(c).startswith("Unnamed") and df[c].isna().all()])
    return df, preamble


def load() -> pd.DataFrame:
    df, preamble = _read_export()
    if preamble:
        print("export provenance:")
        for ln in preamble:
            print(f"  {ln}")
    df.columns = [str(c).strip() for c in df.columns]

    # WIPO's own two-letter codes are in the file; prefer them to matching on names.
    code_col = next((c for c in df.columns if c.lower() in
                     ("origin (code)", "origin code", "code")), None)
    if code_col:
        df["__code"] = df[code_col].astype(str).str.strip().str.upper()
    # "Office" is the aggregation level of the export ("Total"). Anything else means the
    # export was split by office, which is not what task 1.1 asked for.
    off = next((c for c in df.columns if c.lower() == "office"), None)
    if off is not None:
        # fillna before astype: pandas 3 keeps NaN as missing in a `str` column rather
        # than rendering it "nan", and a set mixing NaN with strings will not sort.
        levels = set(df[off].fillna("").astype(str).str.strip().str.lower())
        if levels - {"total", ""}:
            raise SystemExit(
                f"{SRC.name}: the 'Office' column contains {sorted(levels)}, so this export "
                f"is split by office. Re-export with the total, not per-office rows -- "
                f"summing offices here would reintroduce exactly the duplication that "
                f"moving to families is meant to remove.")
        df = df.drop(columns=[off])
    lower = {c.lower(): c for c in df.columns}

    if REQUIRED <= set(lower):                     # already long
        df = df[[lower["year"], lower["origin"], lower["families"]]]
        df.columns = ["year", "origin", "families"]
    else:
        # Wide: an origin column plus one column per year. The Data Center also emits a
        # leading row-number column and year headers like "2000 ..." -- tolerate both.
        year_cols = {c: int(m.group(0)) for c in df.columns
                     if (m := __import__("re").match(r"\s*(19|20)\d{2}", str(c)))}
        if not year_cols:
            raise SystemExit(
                f"{SRC.name}: cannot read this file. Expected either the long form "
                f"(year, origin, families) or the Data Center's wide export (an origin "
                f"column plus one column per year).\nFound: {list(df.columns)[:12]}\n"
                f"See docs/wipo_family_export.md.")
        # Prefer a column actually called "origin"; otherwise the first non-year column
        # whose values are not numeric (the export leads with a row-number column).
        # Do not test dtype identity here: pandas 3 types text columns as `str`, not
        # `object`, and an `== object` check silently finds nothing.
        candidates = [c for c in df.columns if c not in year_cols and c != "__code"]
        origin_col = next((c for c in candidates if str(c).strip().lower() == "origin"), None)
        if origin_col is None:
            origin_col = next(
                (c for c in candidates
                 if pd.to_numeric(df[c], errors="coerce").isna().all()), None)
        if origin_col is None:
            raise SystemExit(
                f"{SRC.name}: found year columns {sorted(year_cols.values())[:4]}... but no "
                f"origin column among {candidates}. Rename the country column to 'Origin'.")
        print(f"wide export detected: origin column '{origin_col}', "
              f"{len(year_cols)} year columns")
        ids = [origin_col] + (["__code"] if "__code" in df.columns else [])
        df = (df[[*ids, *year_cols]]
              .melt(id_vars=ids, var_name="year", value_name="families")
              .rename(columns={origin_col: "origin"}))
        df["year"] = df["year"].map(year_cols)
        # In a count indicator laid out as a grid, an empty cell means no families that
        # year -- but only where the grid is reporting at all. A year blank for EVERY
        # origin is not a year in which the world produced no patent families; it is a
        # year the database has not filled in yet, and reading it as zero would put a
        # fabricated collapse at the end of every series.
        df["families"] = df["families"].astype(str).str.replace(",", "", regex=False)
        df["families"] = pd.to_numeric(df["families"], errors="coerce")
        reported = df.groupby("year")["families"].apply(lambda v: v.notna().any())
        empty_years = sorted(int(y) for y, ok in reported.items() if not ok)
        if empty_years:
            print(f"dropped {empty_years}: blank for every origin, so not yet reported "
                  f"rather than zero")
            df = df[~df["year"].isin(empty_years)]
        df["families"] = df["families"].fillna(0)

    df["origin_label"] = df["origin"].astype(str).str.strip()
    if "__code" in df.columns:
        codes = df.pop("__code")
        df["origin"] = [c if c in COUNTRIES else _to_code(l)
                        for c, l in zip(codes, df["origin_label"])]
    else:
        df["origin"] = df["origin_label"].map(_to_code)

    # pandas .map() yields NaN, not None, for a label it could not map -- testing
    # `is None` here silently passed every unmapped country through as "fine".
    unresolved = sorted({l for l, c in zip(df.origin_label, df.origin) if pd.isna(c)})
    dropped = [l for l in unresolved if l.lower() in NOT_IN_STUDY_SET]
    unmapped = [l for l in unresolved if l.lower() not in NOT_IN_STUDY_SET]
    if dropped:
        print(f"dropped, not in the study set: {', '.join(dropped)}")
    if unmapped:
        print(f"WARNING: origin label(s) not recognised, and dropped: {unmapped}\n"
              f"  If one of these is a study country under a name this script does not "
              f"know, add it to NAME_TO_CODE in {Path(__file__).name} -- do not let it "
              f"fall out of the analysis silently.", file=sys.stderr)

    df = df.dropna(subset=["origin"])
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["families"] = pd.to_numeric(df["families"], errors="coerce")
    return df[["year", "origin", "families"]]


def validate(df: pd.DataFrame) -> list[str]:
    """Every way this export can be wrong that a script can see. Returns problems."""
    problems = []
    if df["year"].isna().any() or df["families"].isna().any():
        problems.append(f"{int(df.isna().any(axis=1).sum())} row(s) have a non-numeric "
                        "year or families value -- check for thousands separators, "
                        "footnote markers, or a 'total' row copied in with the data")
    unknown = sorted(set(df["origin"].dropna()) - set(COUNTRIES))
    if unknown:
        problems.append(f"origin codes not in the country set: {unknown} -- the export "
                        "should use WIPO's two-letter origin codes and cover only the 14 "
                        "study economies")
    absent = sorted(set(COUNTRIES) - set(df["origin"].dropna()))
    # Timor-Leste is already omitted from Table 3 for want of observations, and may not
    # be a selectable origin at all. Absent is worth saying; it is not worth blocking on.
    soft = {"TL"}
    hard = [c for c in absent if c not in soft]
    if hard:
        problems.append(f"no rows for {[COUNTRIES[c] for c in hard]}. Re-run the export "
                        "with those origins selected -- an absent country and a zero are "
                        "different things downstream, and Thailand and Lao PDR both appear "
                        "in Table 3")
    for c in absent:
        if c in soft:
            print(f"note: no rows for {COUNTRIES[c]} ({c}); it is omitted from Table 3 "
                  "anyway, but say so in Section 3.2 rather than leaving it silent")
    if not df.empty:
        yrs = df["year"].dropna()
        if yrs.min() > MIN_YEAR:
            problems.append(f"series starts at {int(yrs.min())}, the study window opens at "
                            f"{MIN_YEAR}")
        if yrs.max() < MAX_YEAR:
            problems.append(f"series ends at {int(yrs.max())}, task 1.1 needs at least "
                            f"{MAX_YEAR}")
    dupes = df.duplicated(["year", "origin"]).sum()
    if dupes:
        problems.append(f"{dupes} duplicate (year, origin) pair(s) -- the export should be "
                        "one row per country-year, not split by office or technology")
    neg = (df["families"].dropna() < 0).sum()
    if neg:
        problems.append(f"{neg} negative family count(s)")
    return problems


# Independent check against WIPO's own flagship publication, so a wrong export cannot
# pass silently. World Intellectual Property Indicators 2024, "Patent families" section,
# quotes these figures in prose; the export must reproduce them.
WIPI_2024 = {          # (country, year): value quoted in WIPI 2024, rounded as printed
    ("China", 2007): 133_200,
    ("China", 2021): 1_449_100,
    ("Japan", 2007): 305_000,
    ("Japan", 2021): 183_000,
}


def cross_check(df: pd.DataFrame) -> list[str]:
    """Compare the export against figures WIPO prints in WIPI 2024.

    This is the only external check available on a hand-made input: it catches the wrong
    indicator, the wrong report type, a column shift, or an export someone re-pulled with
    different settings. WIPI rounds, so the tolerance is 0.5%.
    """
    p = df.pivot_table(index="year", columns="country", values="families")
    problems = []
    for (country, year), expected in WIPI_2024.items():
        if country not in p.columns or year not in p.index:
            problems.append(f"cannot check {country} {year}: not in the export")
            continue
        got = p.loc[year, country]
        if abs(got - expected) / expected > 0.005:
            problems.append(f"{country} {year}: export has {got:,.0f}, WIPI 2024 prints "
                            f"~{expected:,} ({100 * (got / expected - 1):+.1f}%)")
    return problems


def truncation_report(df: pd.DataFrame) -> list[str]:
    """Is the recent tail of the series real, or still filling in?

    Families are anchored on earliest filing and accumulate members for years afterwards,
    so the last years of any family series are suspect by construction. The test is not
    whether the recent years look lower -- for these economies they often do not -- but
    whether individual countries move in ways no real process produces.
    """
    p = df.pivot_table(index="year", columns="country", values="families")
    lines, suspect = [], {}
    for y in sorted(p.index)[-4:]:
        base = p.loc[y - 5:y - 1]
        for c in p.columns:
            b = base[c].mean()
            if b and b > 10:                       # ignore countries too small to judge
                ratio = 100 * p.loc[y, c] / b
                if ratio < 40 or ratio > 250:
                    suspect.setdefault(int(y), []).append(f"{c} {ratio:.0f}%")
    for y in sorted(suspect):
        lines.append(f"  {y}: " + "; ".join(suspect[y]))
    return lines


def attach_measures(df: pd.DataFrame) -> pd.DataFrame:
    """Join indicators 7 and 6b onto the 6a series, one column each.

    Missing companion exports are a warning, not a failure: 6a alone is enough to run
    the pipeline, and only the RQ1 robustness column needs the others.
    """
    import glob
    from wipo_dc import read_export, blank_years

    for _, (pattern, col) in MEASURES.items():
        hits = [p for p in glob.glob(str(EXTRA_DIR / "*.csv")) if pattern in Path(p).name]
        if not hits:
            print(f"note: no export matching {pattern!r}; column '{col}' not built",
                  file=sys.stderr)
            continue
        extra, meta = read_export(Path(hits[0]))
        empty = blank_years(extra)
        if empty:
            print(f"  {col}: {empty} blank for every origin, dropped as unreported")
            extra = extra[~extra.year.isin(empty)]
        extra = (extra.dropna(subset=["origin"])
                      .groupby(["origin", "year"], as_index=False)["value"].sum()
                      .rename(columns={"value": col}))
        df = df.merge(extra, on=["origin", "year"], how="left")
        print(f"  {col}: from {meta.get('Indicator', '?')[:44]}")
    return df


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    a = ap.parse_args(argv)

    if not SRC.exists():
        return _missing()

    df = load()
    problems = validate(df)
    if problems:
        print(f"{SRC.name} is not usable yet:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    df["country"] = df["origin"].map(COUNTRIES)
    df = df.sort_values(["country", "year"]).reset_index(drop=True)
    print(f"{SRC.name}: {len(df)} country-years, "
          f"{int(df.year.min())}-{int(df.year.max())}, {df.origin.nunique()} economies  OK")
    print(df.pivot_table(index="year", columns="country", values="families")
            .tail(8).to_string())

    named = df.assign(country=df.origin.map(COUNTRIES))
    xc = cross_check(named)
    if xc:
        print("\nCROSS-CHECK FAILED against WIPO's own published figures:", file=sys.stderr)
        for ln in xc:
            print(f"  - {ln}", file=sys.stderr)
        print("  The export does not reproduce WIPI 2024. Most likely the indicator or the\n"
              "  report type differs from `6a - Patent family by origin` / `Total count by\n"
              "  applicant's origin`. See docs/wipo_family_export.md.", file=sys.stderr)
        return 1
    print(f"\ncross-check vs WIPI 2024: {len(WIPI_2024)}/{len(WIPI_2024)} figures reproduced")

    print(f"\ntruncation check (country-year vs its own preceding 5-year mean):")
    anomalies = truncation_report(named)
    if anomalies:
        for ln in anomalies:
            print(ln)
    else:
        print("  no country moves implausibly in the recent tail")
    kept = df[df.year <= WINDOW_END]
    print(f"\nRQ1 window: {MIN_YEAR}-{WINDOW_END} "
          f"({len(kept)} country-years). Years after {WINDOW_END} are loaded but excluded "
          f"-- see WINDOW_END in this file for why.")

    if a.check:
        return 0
    df = attach_measures(df)
    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}")
    print("Next: RQ1 numbers and Figures 1-2 move to this series; the green share in RQ2 "
          "stays at publication level (Option A hybrid). Say so in Section 3.2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
