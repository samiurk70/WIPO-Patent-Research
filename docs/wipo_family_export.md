# Exporting the WIPO patent-family series (task 1.1, Option A)

This is the **one manual input** in the pipeline. Everything else is fetched by script
from a public endpoint. Read `docs/counting_unit_evidence.md` §4 for why: WIPO publishes
the family indicator only through the Data Center's interactive interface, and building
on its private API would hand a reviewer a deposit that breaks without explanation.

It needs doing once, takes an afternoon at most, and after that the file is pinned like
any other raw input.

## What to export

**Where:** WIPO IP Statistics Data Center — <https://www3.wipo.int/ipstats/>

**Indicator: `6a - Patent family by origin`.** Confirmed present in the interface
2026-09-02, under the **PATENT** tab.

**Report type: `Total count by applicant's origin`.** This matters — it matches the
applicant-origin attribution of the publication file already in the pipeline, so the two
series are on the same basis.

WIPO compiles its family indicators from PATSTAT and reports them **first-filing based**
— families are attributed to the year of earliest filing, not the publication year. That
matters; see *Truncation* below. Do not substitute a triadic-families or IP5-families
series, which are far more restrictive definitions and read as near-zero for most of the
ASEAN set.

**Dimensions:** origin (applicant/inventor country) × year. **Not** broken down by
office, technology field, or anything else — one row per country-year.

**Origins — all 14, using WIPO's two-letter codes:**

| | | | |
|---|---|---|---|
| BN Brunei Darussalam | KH Cambodia | ID Indonesia | LA Lao PDR |
| MY Malaysia | MM Myanmar | PH Philippines | SG Singapore |
| TH Thailand | VN Viet Nam | TL Timor-Leste | CN China |
| KR Korea, Rep. | JP Japan | | |

**Years:** From **2000** to the latest available (currently **2024**). Export the whole
range — the truncation decision below is made from the data, not before it.

Note that the family series runs to 2024 while the publication file stops at 2022. That
is a real difference in vintage, not an error, and Section 3.2 has to state which window
each research question uses.

**Note which attribution the interface used** (applicant residence vs inventor
residence) and write it into `RETRIEVED.txt`. The publication file this pipeline already
uses is **applicant origin**; if the family series is inventor-based, that difference has
to be stated in Section 3.2, not quietly absorbed.

## Where to put it

```
data/raw/wipo_families/wipo_patent_families.csv
data/raw/wipo_families/RETRIEVED.txt
```

**Use the "Download CSV" link on the results page and save the file as it comes.** The
loader reads the Data Center's own wide export — a leading row-number column, an `Origin`
column of country *names*, and one column per year — and reshapes it itself. It also maps
the names WIPO uses (`Republic of Korea`, `Lao People's Democratic Republic`, `Viet Nam`)
to the codes the pipeline uses. Do not reshape it by hand; that is where transcription
errors come from.

The long form is accepted too, if you ever have it:

```csv
year,origin,families
2000,SG,716
2000,MY,165
```

Two things the loader assumes, both recorded here so they are not silent:

- **An empty cell in the grid means zero families that year**, not an unreported one.
  That is right for a count indicator laid out as a grid, and it is what the Data Center
  shows for Cambodia and Myanmar in most years.
- **Origins outside the study set are dropped with a note** — `China, Hong Kong SAR` is a
  separate origin in WIPO's list and is not one of the fourteen. An origin the loader does
  *not* recognise raises a warning rather than disappearing, so a study country under an
  unexpected name cannot fall out of the analysis unnoticed.

`RETRIEVED.txt` should say: the date, the exact indicator name as the interface labels
it, the attribution basis (applicant or inventor), the year basis (earliest filing), and
any filter you set. A sentence each is enough — it is what Section 3.2 gets written from.

## Then

```bash
python pipeline/load_wipo_families.py --check   # validates; tells you exactly what is wrong
python pipeline/make_manifest.py                # pins it into data/raw/MANIFEST.sha256
python pipeline/load_wipo_families.py           # builds data/derived/wipo_families_long.csv
```

The validator checks for every failure a script can see: missing countries, duplicate
country-years, non-numeric cells, a series that starts after 2000 or stops early,
unknown origin codes, negative counts. It refuses rather than half-working.

## Truncation — decide this from the exported data, do not assume it

**First, the good news, tested 2026-09-02:** the *publication* series is **not**
truncated. World publications in 2022 are 101.1% of the 2019–2021 mean, so publication
year 2022 is complete and nothing in the current numbers needs a truncation correction.
Truncation is a **family-series problem only**, which is why it cannot be settled before
the export exists.

(The country-level swings in 2022 — Brunei at 16% of its own recent mean, the
Philippines 28%, Malaysia 190% — are small-N volatility, not truncation. That is
evidence for task 1.4, not for a window change.)


Families anchored on earliest filing accumulate members for years afterwards, and there
is an 18-month publication lag on top. The most recent years in the series are therefore
**systematically undercounted**, and the current 2018–2022 window — used by Table 3 and
Figures 5, 6 and 7 — sits squarely in the affected range.

Once the file exists, plot families per year per country and look for where the recent
tail bends down. Then either move the window back (2016–2020 is the plan's suggestion)
or apply an explicit correction and show it. Either way it goes in the methods section.
Plan §2.1 has the reasoning.

## What changes when this lands

RQ1 capacity — Figures 1 and 2, and every RQ1 number — moves to the family series. The
RQ2 green **share** stays at publication level, because WIPO's family series carries no
technology-field breakdown. That split is the whole of Option A and it must be stated
in one unmissable sentence in Section 3.2, along with what it assumes: that duplication
rates do not vary systematically across technology fields. Left implicit, a reviewer
reads it as inconsistency rather than a considered choice.

Expect the gap to **widen**. China files 91.7% of its publications at its own office and
Singapore 4.0%, so deduplication takes far more from Singapore than from China. The
headline is currently "more than four orders of magnitude"; it will move again, and so
will every adjective attached to it.


---

# The export landed — what it says (2026-09-02)

13 economies, 2000–2024, applicant origin, indicator `6a`. Timor-Leste returns no result;
Lao PDR is present but single-digit and sparse. Both are notes, not problems.

## Window: 2000–2022

Decided from the data, as the plan asked. 2024 is blank for **every** origin — not
reported yet, and read as zero it would have put a fabricated collapse at the end of every
series. 2023 carries two plainly artefactual country values: the **Philippines at 7%** of
its own preceding five-year mean, **Indonesia at 862%**. 2022 is stable everywhere.

2022 is also the last year of the publication file, so RQ1 and RQ2 share one 2000–2022
span instead of needing two windows explained. The plan's guess of 2016–2020 was more
cautious than the data requires.

## The gap widens, as §2.1 predicted — and by more than the publication fix showed

Publications-to-families in 2022: China **1.0**, Viet Nam 1.1, Korea 1.5, Japan 1.9,
Singapore **2.1**, Thailand 3.2. China's count barely moves because it is already almost
entirely domestic; Singapore's halves.

**China-to-Singapore goes from 251× at publication level to 500× at family level.**
China-to-median-ASEAN is 4.5 orders of magnitude.

## The complication that has to go in Section 3.2

**The two series are not nested, and families are not "publications with duplicates
removed".** The publications-to-families ratio is below 1 for several country-years — the
Philippines at 0.3 in 2022, Viet Nam at 0.6 in 2005 — which is impossible under a subset
relation. Two reasons, both structural:

1. **Different year anchors.** Families are attributed to **earliest filing**; publications
   to **publication year**, 18 months or more later. The same invention lands in different
   years in the two series.
2. **Different populations.** A family whose members have not published yet is counted in
   the family series and absent from the publication series.

So Section 3.2 cannot describe the hybrid as "capacity deduplicated, shares not". It has
to say these are two different measurements on two different year bases, state why each
is the right instrument for its research question, and state the assumption the split
rests on. Presenting families as a cleaned-up version of the publication count would be a
misdescription a referee could catch from the numbers alone.

The sub-1 ratios cluster in the small economies, which is one more argument for the
task 1.4 suppression threshold.


## The export is verified against WIPO's own publication

*World Intellectual Property Indicators 2024* quotes patent-family figures in prose. The
export reproduces all four to within WIPI's own rounding:

| | WIPI 2024 prints | this export |
|---|---:|---:|
| China 2007 | ~133,200 | 133,112 |
| China 2021 | ~1,449,100 | 1,449,194 |
| Japan 2007 | 305,000 | 305,042 |
| Japan 2021 | 183,000 | 182,883 |

`load_wipo_families.py` now asserts this on every run and refuses the file if it fails.
It is the only external check available on an input no script produces, and it catches
the wrong indicator, the wrong report type, or a column shift — the failure modes a
hand-made export actually has.

WIPI also supplies two statements worth citing in Section 3.2:

- **What the indicator is for:** "WIPO has developed indicators for patent families with
  the aim of capturing the actual number of unique inventions by excluding double counting
  so far as possible."
- **Why the recent tail is unusable:** "The drawback of such data is the consequent time
  lag, which can be up to three years." That is WIPO's own justification for stopping at
  2022 rather than a judgement call of ours.

WIPI separately confirms 2022 as "the latest year for which complete data are available
owing to the delay between application and publication" for the technology (publication)
series — matching the truncation test run against the bulk file.


## The year basis is settled: 6a is anchored on earliest FILING

Two independent lines of evidence, since WIPI never states it outright.

**The indicator list says so by contrast.** The Data Center offers both:

- `6a - Patent family by origin`
- `6b - Patent family by origin (based on the earliest grant year)`

6b carries the qualifier; 6a does not. A qualifier is only needed to mark a departure from
the default, so 6a is the filing-anchored series and 6b is its grant-anchored variant.

**The data is consistent with it but does not prove it.** An earlier version of this file
claimed the lag was confirmed by correlating year-on-year growth against the publication
series, where alignment improved as publications were shifted about two years later
(mean r 0.25 / 0.32 / 0.41 at lags 0 / 1 / 2). **That was overstated and is retracted as
evidence.** Repeating the test between 6a and 6b — which should show a clean grant-minus-
filing offset if the anchoring story is right — gives best lags scattered across +1, +2
and +6 years with modest correlations (r 0.29 to 0.69) and no consistent signal. Annual
country-level counts are too noisy to pin a lag of this size.

What supports the claim is documentary, and that is enough:

1. **WIPO's naming.** 6b is qualified "based on the earliest grant year"; 6a is not. A
   qualifier marks a departure from a default.
2. **WIPO's own methodology note**, which describes its family indicators as first-filing
   based.

And the size of the gap between the two series does not need estimating from noisy
counts at all: **an application publishes 18 months after its earliest priority date**
under the Patent Cooperation Treaty and essentially every national law. That is a
statutory fact, and it is the right basis for the statement in Section 3.2.

**So Section 3.2 can state it plainly:** RQ1 counts families by earliest filing year, RQ2
counts publications by publication year, and the two are roughly two years apart on the
same invention. That is the honest description of the Option A hybrid — not "capacity
deduplicated, shares not".

## Two further indicators worth exporting

The same Patent tab offers fourteen indicators. Two bear directly on open problems.

**`7 - Foreign-oriented patent family by origin`** — families with at least one filing
office outside the applicant's home country. WIPI's own words: they "reduce bias toward
domestic filings, making them more reliable for cross-country comparison." That is
precisely the asymmetry measured in `docs/counting_unit_evidence.md` — China filing 91.7%
at home against Singapore's 4.0% — and indicator 7 neutralises it by construction. It is
the natural robustness series for RQ1 and it answers the reviewer objection before it is
made. **Highest value of anything still unexported.**

**`4b - Patent publications by renewable energy`** — a WIPO-published green measure on the
*same publication basis* as `4a`, the bulk file already in the pipeline, so it is directly
comparable with the existing green share. It does not solve the field-24 problem — renewable
energy is a narrower subset, not the full green inventory — but it is a second green
measure from the same source on the same counting basis, which is worth more than a
defence written in prose.

Lower priority: `9` and `10` (resident applications per 100bn USD GDP and per million
population, by origin) are WIPO's own normalisations of quantities this paper computes
itself, and would make a cheap cross-check.
