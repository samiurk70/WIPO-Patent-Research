# How much does the counting unit matter?

Open-data pipeline and manuscript for a methods paper on the WIPO
patent-publications-by-technology bulk file. The paper measures how summing
that file across filing offices inflates origin counts relative to the
cell-wise leading office, and when that inflation is not a common multiplier.

Target journal: *World Patent Information* (Elsevier).

## Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip

python pipeline/run.py raw     # download + checksum the WIPO bulk file
python pipeline/run.py all     # families -> figures -> tables -> verify
```

The patent-family series is not in the bulk download. Export it once from the
WIPO IP Statistics Data Center and pin it under `data/raw/wipo_families/`
as described in [`docs/wipo_family_export.md`](docs/wipo_family_export.md).

The WIPO bulk file, family export, and Data Center extracts live under `data/raw/`.
Derived counting tables live under `data/derived/`. Both are committed so a clone
can reproduce the paper without a separate download. `data/raw/MANIFEST.sha256`
pins the exact raw inputs; `python pipeline/make_manifest.py --check` verifies
them.

### The numbers gate

`python pipeline/run.py verify` recomputes every numeric claim in
`Paper A/main.tex` from the raw data, writes `numbers.json`, and scans the
manuscript for numeric tokens that no recomputed quantity accounts for.

To have it gate pushes: `git config core.hooksPath .githooks` (the hook must
be executable).

- `Paper A/numbers_allow.txt` — structural tokens that are not data claims
- `Paper A/numbers_waivers.txt` — known discrepancies, reported without blocking

### Compile the manuscript

```bash
cd "Paper A"
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

## Layout

- `Paper A/` — Elsevier CAS manuscript, bibliography, highlights, compiled PDF
- `pipeline/` — retrieval, duplication measures, figures, and the numbers gate
- `figures/paper_a/` — committed PNG and PDF figures
- `docs/` — family-export notes, claims audit, and supporting quantities
- `data/raw/` — WIPO bulk file, family export, and Data Center extracts
- `data/derived/` — counting tables written by the pipeline
- `data/raw/MANIFEST.sha256` — checksums of those raw inputs

## Data sources

| Source | What | Access |
|---|---|---|
| WIPO IP Statistics | Patent publications by office × applicant origin × year × technology field | bulk CSV |
| WIPO IP Statistics Data Center | Patent families by origin (indicator 6a) and foreign-oriented families (indicator 7) | hand export, pinned |

Every input is public. The bulk zip and the hand-exported family series are in
`data/raw/`; `pipeline/fetch_wipo.py` can also re-download the zip.
