# Claims audit

`check_numbers.py` proves that a number in the prose is the number the script produced.
It cannot prove the number means what the sentence says it means. That gap is where this
paper's original problems lived — every figure agreed with every table while the counting
unit underneath them was wrong — so interpretive claims get audited here, separately.

**How to use this file.** Every substantive claim introduced during the revision gets a
row: what it rests on, how it was tested, and what would falsify it. A claim whose only
support is "it seemed right" is marked as such rather than quietly promoted. When a test
comes out against a claim, the claim is corrected and the retraction is recorded — the
history stays visible.

**Status key:** ✅ tested and held · ⚠️ documentary only, not independently tested ·
↩️ overstated once, corrected · ❓ open

---

## ↩️ Figure 7 and Section 4.2 were using different RTA denominators

**Corrected 2026-09-03.** `make_figures_extra.py` dropped the PCT international
phase from the world green share (2.03%). `check_numbers.py` still included it
(1.94%), so the manuscript quoted Vietnam 1.55, Philippines 1.75, China 1.45
while the bars showed 1.48, 1.67, 1.39. Ranking unchanged; magnitudes not.
The gate now excludes PCT and `verify_all.py` asserts the two scripts agree.
Prose updated to 2.03 / 1.48 / 1.67 / 1.39 / 1.28 / 0.37 / 0.39.

## ↩️ Figure 4(b) was OLS residuals of levels, not the rank partial

**Corrected 2026-09-03.** Caption quoted Spearman partial −0.21. The panel
residualised levels, whose Pearson is −0.40. The figure now residualises ranks,
so the picture is the statistic. Caption says so.

## ↩️ The 4.5-order median included three unrecorded 2022 family counts as zero

**Corrected 2026-09-03.** Cambodia, Lao PDR and Brunei have families in adjacent
years and none with earliest filing year 2022 in the export. That is a coverage
limit of a thin series, not a measured zero of invention. Including those zeros
pulled the median down and the China gap up by half an order. Median is now
among the seven members with a 2022 record: about **four** orders on all
families and about **three** on foreign-oriented. Same rule on both bases.

## ↩️ Brunei "about nine publications a year"

**Corrected 2026-09-03.** 32 publications over 2018–2022 is 6.4 a year. The
appendix already said six. The taxonomy paragraph now matches.

## ↩️ China "passing Japan around 2010"

**Corrected 2026-09-03.** China is still below Japan in 2010 (254,577 vs
262,898). First exceedance is 2011. The gate had `claimed=2010, tol=1`, which
is how a one-year error looked like a pass.

---

## ✅ `**` in the WIPO office column is the PCT international phase

**Why it matters:** the whole PCT double-count correction rests on it. If `**` were an
"unknown office" bucket, dropping it would have deleted real data.

**Test.** If `**` is the PCT route, the share of an origin's publications appearing under
it must track that origin's known propensity to file internationally. It does, on both
sample constructions. The all-year audit table (below) was the first check. Paper A's
Table 2 uses the 2018–2022, `tec_id>0`, 68-economy filters and is the manuscript
series; see the R2 correction row. R3 adds the discriminating origin-level rank
check against published PCT applications (Spearman +0.991; see the R3 row).

All-year construction (audit, not Table 2):

| Russia | China | Korea | India | Japan | US | Germany | Netherlands | Sweden |
|---|---|---|---|---|---|---|---|---|
| 3.0% | 3.6% | 6.7% | 9.4% | 9.5% | 13.8% | 13.2% | 17.2% | 18.4% |

Domestic-heavy filing systems at the bottom, heavy PCT users at the top. An
"unknown office" bucket would show no such ordering. Volume also matches published PCT
totals (309,728 in 2020 against roughly 275,000 PCT applications).

**Would falsify it:** WIPO documentation defining `**` otherwise; or a country's `**`
share diverging from its known PCT behaviour.

## ↩️ Table 2 PCT-layer shares are the 68-economy filtered window, not the all-year audit table

**Corrected 2026-09-03 (R2).** An earlier audit row recorded Russia 3.0, China 3.6,
Korea 6.7, India 9.4, Japan 9.5, Germany 13.2, US 13.8, Netherlands 17.2, Sweden
18.4 on an all-year, less-filtered construction. The manuscript Table 2 uses the
same 2018–2022, `tec_id>0`, 68-economy filters as the rest of Paper A: Russia 4.5,
China 3.9, Korea 8.8, India 7.5, Japan 14.3, Germany 13.7, US 13.3, Netherlands
16.6, Sweden 18.8. Two orderings reverse (India/Korea, US/Germany) and the bottom
rank moves from Russia to China. Both sets are script-produced; they answer
different sample constructions. Do not mix them.

The 309,728 office-`**` publications in 2020 sit against WIPO's estimated 275,900
PCT applications filed that year (PCT Yearly Review 2021). They differ because
publications lag applications by about eighteen months and because whole-counted
field assignments exceed document counts.

## ↩️ High D is an EPC architecture effect, not a generic international-orientation gradient

**Corrected 2026-09-03 (R2), rewritten 2026-09-03 (R3).** R2 treated EPC
membership as a proxy for a regional office coexisting with national
publications, and introduced a matched-$H$ table as primary evidence. That
table interleaves: New Zealand 3.87 beside Sweden 3.88, and none of the four
rows is EP-led. R3's blocking statistic is the partial Spearman of $D$ with
EPC status controlling for $H$ on the measurable-home 58: **+0.413**
($p=0.0016$; Fisher-z 95% CI $[0.171, 0.608]$). That is not near zero, so
there is a residual EPC association after $H$ is held. The H-quartile table
replaces the matched comparison as the display of that association (Q1 median
$D$ 2.57 non-EPC vs 3.77 EPC). The matched rows are retained only to show
that EP-as-leader is not required. The five highest measurable-home values
remain EPC; all ten EP-as-leader origins are EPC contracting states.

On the measurable-home 58 the comparison is EPC 1.15 / 2.82 / 4.48 against
non-EPC 1.05 / 1.63 / 3.87 (New Zealand). The all-68 non-EPC maximum of 4.10 is
Antigua and Barbuda, an unmeasurable-home micro-state, and is not the relevant
counterexample.

## ✅ Office `**` tracks published PCT applications by origin

**R3 discriminating test.** Spearman of 2020 office-`**` publications against
WIPO's published 2020 PCT applications by origin is **+0.991** over the twenty
largest named origins (95% CI $[0.977, 0.997]$). Sweden matches exactly
(4,356 = 4,356). The $Q$–$H$ correlation does not discriminate an unknown-office
bucket from the PCT reading; this rank check would. A file-specific dictionary
is still absent, so the identification is no longer only inferential from
behaviour, but it is still without a dictionary confirmation.

**Would falsify it:** WIPO documentation defining `**` otherwise; or
origin-level `**` volumes failing to track published PCT filings by origin.

## ⚠️ The leading-office recommendation is validated only on seven non-EPC origins

**Not independently tested on EPC origins.** The seven-economy overlap is China,
Japan, Korea, Malaysia, the Philippines, Singapore and Thailand. None is an EPC
origin. Singapore, the only low-H analogue for typical EPC profiles, has the
largest genuine leading-office error in that overlap (0.22, Philippines set aside
as the year-anchor case). Family exports for Switzerland, Germany, the Netherlands
and Sweden were not in the pinned input at this revision. The manuscript therefore
scopes the recommendation to this overlap.

**Would strengthen it:** Data Center indicators 6a and 7 for those four EPC
origins, same applicant-origin attribution and window.

## ✅ The capacity gap is 500× on all families and 20× on foreign-oriented

**Test.** Stable across two decades rather than a single-year artefact: 62× / 5× in 2005,
150× / 8× in 2010, 500× / 20× in 2022. China's foreign-oriented share sits at 3–7%
throughout and Singapore's at 85–93%. Both indicators are the same unit (families), the
same attribution (applicant origin) and the same source, so they are directly comparable.

**Would falsify it:** indicators 6a and 7 differing in attribution or coverage in a way
WIPO documents but this analysis missed.

## ✅ The family export is the right series, correctly parsed

**Test.** Reproduces four figures WIPI 2024 prints in prose, to within its rounding —
China 2007 and 2021, Japan 2007 and 2021. Asserted on every run; the loader refuses the
file if it fails. This is what caught the trailing-comma column shift that had silently
put year-2000 counts in the "Office" column.

## ✅ Indonesia's 0.00% green share supports no claim of decline

**Test.** Clopper-Pearson interval on 0 of 130 is [0, 2.80], which contains the ASEAN
aggregate (1.06) and most individual shares in the region. Standard exact method for a
binomial proportion; no distributional assumption beyond independence of publications.

## ✅ GDP as (GDP per capita × population)

**Why it matters:** the 85.8% coverage figure and the 0.45%-vs-0.19% normalisation.

**Test.** Against published World Bank GDP for 2022: Indonesia exact, Thailand 0.1%,
Malaysia 0.2%, China 2.0%, Singapore 3.4%. The method is how per-capita is derived in the
first place, so agreement is expected; the residuals are recall error in the comparison
values, not method error. A 3% error in one country cannot move an 85.8% share or a 2.4×
ratio materially.

## ↩️ Families are anchored on earliest filing, publications on publication year

**Corrected 2026-09-03.** The anchoring claim stands on documentary evidence: WIPO
qualifies indicator 6b as "based on the earliest grant year" and leaves 6a unqualified,
and WIPO's methodology describes its family indicators as first-filing based.

**What was retracted.** An earlier version claimed the data confirmed a two-year lag,
citing correlations of 0.25 / 0.32 / 0.41 at lags 0 / 1 / 2 against the publication
series. Re-testing the same way between 6a and 6b — which should show a clean
grant-minus-filing offset — gave best lags scattered across +1, +2 and +6 years with
modest correlations and no consistent signal. **Annual country-level counts are too noisy
to pin a lag of this size, and the original test was too weak to have been presented as
confirmation.** The manuscript now rests the interval between the two series on the
statutory eighteen-month publication rule instead of on an estimate.

**Lesson recorded:** correlating two monotonically rising series, even differenced, over
~16 country-years is not a test. It was reported as one.

## ⚠️ Schmoch field 24 covers 11 IPC subclasses against GTIS's 157

**Not independently tested.** Both figures are computed from WIPO's own published
concordance files by regex over IPC subclass codes. The direction is not in doubt — field
24 is pollution abatement and GTIS spans clean energy, storage and mobility — but the
exact counts depend on the parser, and a missed code format would shift them. The derived
"5% of the taxonomy" is already stated as coverage of the taxonomy rather than of patent
volume, which is the claim that would be wrong to make.

**To test properly:** hand-check the subclass extraction against a sample of the source
spreadsheets.

## ⚠️ The six-economy IP balance aggregate covers 85.8% of regional GDP

**Not independently tested.** Follows directly from which countries report both series in
WDI and from the GDP method above (which is tested). The residual risk is that WDI's
missingness differs from the underlying IMF source — which is exactly the open Viet Nam
question below.

## ⚠️ The eleven references added in task 1.7

**Every DOI resolves and every record was fetched live from Crossref** — none was written
from memory, which is the failure mode that matters here. `verify_refs.py` reports 0
MISMATCH and 0 DEAD across all 36.

**Not fully verified, and deliberately marked:**

- **Three OECD working papers have no author metadata in Crossref** (Haščič and Migotto;
  Martínez; Dernis and Khan; plus Squicciarini et al.). Their authors are supplied by hand
  in `HUMAN_SUPPLIED_AUTHORS` and reported as unverified on every run. If any is wrong, the
  paper attributes a document to the wrong people.
- **Crossref confirms a DOI resolves to a record with a given title and authors. It does
  not confirm the reference supports the sentence citing it.** That judgement is human and
  is not discharged.

## ⚠️ The novelty claim in contribution 1

**Tested, and the test is weak by nature.** A structured search of OpenAlex — six queries,
140 distinct works from 2010 on — scored each result's title for four ingredients (patent
counts, governance indicators, IP balance of payments, Southeast Asian scope). **One title
carried even two, and it was unrelated** (patents and external finance).

**What this cannot establish.** Title-only matching is crude and abstracts were not
searched; six queries is not systematic; and a keyword search returning nothing is weak
evidence of absence in any case. **The manuscript therefore claims novelty "to our
knowledge" and says explicitly that the claim is bounded by this search** rather than
asserting it about the literature at large. Do not strengthen that wording.

**A failure worth recording.** The first cross-check against Semantic Scholar returned
zero results, which looked like confirmation. It was HTTP 429 — rate-limited by the
reference-verification runs earlier the same session. An API failure had presented as a
finding. Checked before it was used; it would have made the novelty claim look
corroborated by two indexes when only one had answered.

## ✅ The RQ5 fidelity claim

**Test.** Two independent comparisons, both of which could have failed: the family series
reproduces four figures WIPO prints in prose in WIPI 2024 to within their rounding, and
resident application counts agree exactly between the World Bank and WIPO across every
country-year compared.

**Bounded deliberately.** These confirm retrieval and aggregation preserve source values.
They do **not** compare the open route against a commercial database at patent level,
which is the test that would establish the WIPO aggregates themselves are not losing
something. §6.3 says so rather than implying the checks cover it.

## ✅ R&D intensity predicts patent productivity, net of income

**Test.** Spearman +0.951 raw; **+0.816** [0.105, 1.000] partialling out log GDP per
capita. Leave-one-out on the *partial* — the estimate the paper reports — moves it only
between **+0.757 and +0.893** across all twelve omissions, with **no sign flips**. No
single economy carries it.

**Method validated.** The residual-based partial correlation agrees with the closed-form
recursive formula to five decimal places for both variables, so the implementation is not
the thing being tested.

## ✅ Governance carries nothing independent of income — but read the power first

**Test.** Raw Spearman +0.791 (p=0.001) looks strong. Regulatory quality correlates with
log GDP per capita at **+0.923**, and partialling income out leaves **−0.208**, 95% CI
**[−0.664, +0.865]**, p=0.50.

**The leave-one-out is what settles it, and I nearly shipped without running it.** On the
partial, omissions span **−0.333 to +0.140**, and **dropping Indonesia flips the sign**.
So −0.208 is not a small negative effect; it is noise. Only the raw correlation had a
leave-one-out in the first version of this analysis, which would have left the reported
estimate unexamined.

**⚠️ The binding caveat, and it must reach the manuscript.** At n=12–13 a Spearman test
detects a true rho of 0.5 only **34%** of the time and 0.3 only **15%** (simulated, 4,000
draws). **This design could not have found a moderate governance effect even if one
exists.** The defensible claim is therefore *"this evidence cannot support the governance
relationship"* — not *"governance does not matter"*. Writing the second would be a worse
error than the over-claim the revision is fixing, because it would be a null presented as
a finding.

**Would falsify it:** a larger country set, or within-country variation over time — which
is what the panel specification in the appendix is for.

## ↩️ The Philippines family data is NOT anomalous

**Retracted 2026-09-03.** I described the Philippines as having anomalous family data,
because its family count exceeds its publication count in the recent window, and I
reasoned that this "cannot happen under a subset relation". I marked it red in Figure A2,
wrote it into `counting_generality.md`, and encoded it as an invariant in `verify_all.py`.

**All three were wrong, and my own manuscript said so.** Section 3.2 states that the two
series are **not nested**: families are anchored on earliest filing year and publications
on publication year about eighteen months later. Within a fixed window an economy can
therefore record more families than publications. There is no subset relation to violate.

The pattern is also exactly where the mechanism predicts. The publications-to-families
ratio falls monotonically with domestic filing share — China at 95% domestic gives 1.07,
Singapore at 5% gives 2.04 — and the Philippines at 81% domestic sits at the low end,
where the year-anchor offset is enough to push it below one.

**How it was caught.** `verify_all.py` asserted the nesting as an invariant, and Myanmar
failed it too. Two exceptions rather than one prompted the check of whether the invariant
was right, and it was not. **A check that encodes a wrong assumption produces confident
wrong answers**, which is worse than no check.

The invariant now tests what the mechanism actually implies — that the ratio stays within
a plausible band and falls with domestic filing — rather than a nesting the paper denies.

## ❓ Open

- **IMF BOP coverage of Viet Nam.** Probed; the endpoint answers but the series key
  returned nothing. Not proof of absence. Viet Nam is the largest single gap in the
  headline deficit, so this matters.
- **Whether the two Research Square entries have mangled author lists.**
  `verify_refs.py` compares titles only, so a correct DOI with a wrong author list reports
  as OK. Needs eyes on the submitted file.
- **Every DOI**, by hand, before submission. Ground rule 7; the tool narrows, a human closes.
- **The reference count is 36, against the plan's target of 40–45.** Not padded to reach it:
  the plan's actual objection was that 25 was thin for the claims being made, and the gaps
  it named are now filled. The remaining shortfall should be closed by task 1.6's novelty
  search, which needs a targeted literature review anyway, rather than by adding references
  that no claim depends on.
