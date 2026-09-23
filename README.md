# How much does the counting unit matter?

Open-data pipeline and manuscript for a methods paper on the WIPO
patent-publications-by-technology bulk file. The paper measures how summing
that file across filing offices inflates origin counts relative to the
cell-wise leading office, and when that inflation is not a common multiplier.

Target journal: *World Patent Information* (Elsevier).

The manuscript is `Paper A/main.tex`. Per-economy home-office share, PCT-layer
share, and duplication factor for the 68 economies are in
`data/derived/counting_generality.csv`.

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip

python pipeline/run.py all     # families -> figures -> tables -> verify
```

`all` does not re-download anything. The raw files below are already in this
archive, and `data/raw/MANIFEST.sha256` pins them.
`python pipeline/make_manifest.py --check` verifies the checksums.

`python pipeline/run.py raw` re-downloads the bulk zip only. Use it when you
intend to refresh that file, then rebuild the manifest.

`python pipeline/run.py verify` recomputes every numeric claim in
`Latex/main.tex`, writes `numbers.json`, and fails if the manuscript
contains a number the pipeline did not produce.

### Compile the manuscript

```bash
cd "Latex"
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

## Data in this archive

| Path | What it is |
|---|---|
| `data/raw/wipo/` | WIPO patent-publications-by-technology bulk file. Retrieved 30 July 2026. `pipeline/fetch_wipo.py` can download this zip again. |
| `data/raw/wipo_families/wipo_patent_families.csv` | Indicator 6a, patent families by applicant origin, earliest filing year. Hand export, 2 September 2026, after the May 2026 Data Center update. Not in the bulk zip. |
| `data/raw/wipo_requested_plus_extra/` | The same export session, including indicator 7 (foreign-oriented families). |
| `data/derived/` | Tables written by the pipeline, including `counting_generality.csv`. |
| `figures/paper_a/` | Figure files used by the manuscript. |

Publications are dated by publication year. Families are dated by earliest
filing year. The two series are not a record-level join. The family check in
the paper uses the seven origins present in both sources: China, Japan,
Korea, Malaysia, the Philippines, Singapore, and Thailand.

A replacement family export has to be indicator 6a, total count by applicant
origin, plus indicator 7 on the same basis. Put the 6a file at
`data/raw/wipo_families/wipo_patent_families.csv` and the companion export in
`data/raw/wipo_requested_plus_extra/`. The loader checks the China and Japan
totals against *World Intellectual Property Indicators 2024*.

## What is not in the deposit

`research-kit/` is a local checking toolkit: manuscript checks, an overlap
screen, and a knowledge graph. It does not calculate the duplication factor,
the figures, or `numbers.json`. Those are `pipeline/`. The kit also holds
extracted text of other people's papers, which is why the directory is
omitted.

`Latex/Ref Papers/` is the local PDF library. It is not an input to the
pipeline.

Drafting notes are omitted as well: the claims audit, the journal-guidelines
worksheet, the writer quantity crib, and the original family-export task
sheet. Two generated notes remain, because they are outputs of the pipeline
rather than instructions: `docs/counting_generality.md` and
`docs/counting_unit_evidence.md`.

## Layout

- `Latex/` — Elsevier CAS manuscript, bibliography, and highlights
- `pipeline/` — retrieval, family loader, duplication measures, figures, numbers gate
- `figures/paper_a/` — PNG and PDF figures
- `data/raw/` — pinned inputs and `MANIFEST.sha256`
- `data/derived/` — counting tables
- `numbers.json` — machine-readable record of the numeric claims
