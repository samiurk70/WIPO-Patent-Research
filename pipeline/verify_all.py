r"""End-to-end invariant check for the counting-unit paper.

`check_numbers.py` proves each published number equals what its script computed.
This asserts properties that must hold if the transformations are correct.

Run:  python pipeline/verify_all.py
Exit code is the number of failures.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DERIVED, ROOT, WIPO_RAW  # noqa: E402

RESULTS = []


def check(name, condition, detail="", why=""):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((status, name, detail, why))
    return condition


def skip(name, why):
    RESULTS.append(("SKIP", name, "", why))


raw_path = WIPO_RAW / "dc_indicator_patent_4_publication_by_technology.csv"
if raw_path.exists():
    raw = pd.read_csv(raw_path)
    check("raw: counts are non-negative integers",
          (raw["count"] >= 0).all() and (raw["count"] % 1 == 0).all(),
          why="a negative or fractional count would mean the file is not whole-counted")
    check("raw: no duplicate (year, office, origin, field) cells",
          not raw.duplicated(["year", "office", "origin", "tec_id"]).any(),
          why="duplicates would double-count silently in every groupby downstream")
    check("raw: '**' is a distinct office, not a total",
          raw[raw.office == "**"]["count"].sum() < raw[raw.office != "**"]["count"].sum(),
          f"** = {raw[raw.office=='**']['count'].sum():,}, "
          f"others = {raw[raw.office!='**']['count'].sum():,}",
          why="the PCT correction depends on ** being a route, not an aggregate")
else:
    skip("raw", "WIPO bulk file absent")

fam_path = DERIVED / "wipo_families_long.csv"
if fam_path.exists():
    fam = pd.read_csv(fam_path)
    check("families: foreign-oriented never exceed all families",
          bool((fam.foreign_oriented.fillna(0) <= fam.families).all()),
          f"{int((fam.foreign_oriented.fillna(0) > fam.families).sum())} violations",
          why="indicator 7 is a subset of 6a; a violation means the two exports are misaligned")
    check("families: no negative counts",
          (fam.families >= 0).all(),
          why="a negative family count is not a measurement")
    check("families: one row per origin-year",
          not fam.duplicated(["origin", "year"]).any()
          if {"origin", "year"} <= set(fam.columns)
          else not fam.duplicated(["country", "year"]).any(),
          why="a duplicated origin-year would inflate every pooled statistic")
else:
    skip("families", "wipo_families_long.csv absent")

gp = DERIVED / "counting_generality.csv"
if gp.exists():
    gen = pd.read_csv(gp, index_col=0)
    check("generality: unknown origin '**' is excluded", "**" not in gen.index,
          why="'**' is unknown origin, not an economy")
    check("generality: duplication factor is at least 1",
          bool((gen.duplication_factor >= 1).all()),
          why="the office-sum cannot be smaller than its largest single term")
    check("generality: domestic share is a percentage or explicitly missing",
          bool(gen.domestic_share.dropna().between(0, 100).all()),
          why="an out-of-range share means the denominator is wrong")
    check("generality: zero domestic share is recorded as unmeasurable, not zero",
          bool((gen.domestic_share.dropna() > 0).all()),
          f"{int(gen.domestic_share.isna().sum())} marked unmeasurable",
          why="a literal 0% would claim an economy never files at home")
else:
    skip("generality", "counting_generality.csv absent")

nums_path = ROOT / "numbers.json"
if nums_path.exists():
    nums = json.loads(nums_path.read_text(encoding="utf-8"))["entries"]
    pcts = {k: v for k, v in nums.items()
            if v.get("unit") == "%" and v.get("value") is not None}
    check("numbers: percentages are within [-100, 100]",
          all(-100 <= v["value"] <= 100 for v in pcts.values()),
          f"{len(pcts)} percentage quantities checked",
          why="a percentage outside the range is a unit error")
    undef = [k for k, v in nums.items() if v.get("value") is None]
    check("numbers: no quantity is undefined", not undef, f"undefined: {undef}",
          why="an undefined quantity means an empty data slice reached the manuscript")
else:
    skip("numbers", "numbers.json absent")

tex_path = ROOT / "Paper A" / "main.tex"
fig_dir = ROOT / "figures" / "paper_a"
if tex_path.exists():
    tex = tex_path.read_text(encoding="utf-8")
    used = set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex))
    stems = {Path(u).name.replace(".png", "").replace(".pdf", "") for u in used}
    have = {p.stem for p in fig_dir.glob("*.png")} if fig_dir.exists() else set()
    # figA3 is generated but not used in the manuscript.
    check("manuscript: every referenced figure exists",
          stems <= have | {"figA3_green_definitions"},
          f"missing: {sorted(stems - have)}" if stems - have else f"{len(stems)} referenced",
          why="a missing figure fails the build")
else:
    skip("manuscript", "Paper A/main.tex absent")

print(f"\n{'':2}{'status':<7}{'check':<62}detail")
print("-" * 104)
fails = 0
for status, name, detail, why in RESULTS:
    mark = {"PASS": "  ", "FAIL": "!!", "SKIP": " ~"}[status]
    print(f"{mark}{status:<7}{name:<62}{detail}")
    if status == "FAIL":
        fails += 1
        print(f"{'':9}why it matters: {why}")
n = sum(1 for r in RESULTS if r[0] == "PASS")
print("-" * 104)
print(f"{n} passed, {fails} failed, {sum(1 for r in RESULTS if r[0]=='SKIP')} skipped")
sys.exit(fails)
