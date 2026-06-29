# Reproducibility Guide

This guide is written for reviewers, readers, and future maintainers who want to
verify the paper's claims or reuse the software artifact.

The repository supports two levels of reproduction:

1. **Fast artifact verification**: no API key required. This verifies the released
   data, tables, figures, agreement outputs, checksums, and manuscript package.
2. **Full pipeline regeneration**: API key required. This regenerates model outputs
   and LLM-assisted labels through OpenRouter or another OpenAI-compatible endpoint.

## Environment

Recommended:

- Python 3.10 or newer.
- A fresh virtual environment.
- Optional: LaTeX (`pdflatex`, `bibtex`) for compiling manuscripts.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Fast Artifact Verification

This path verifies the released artifact without making external model API calls.

Recommended one-command path:

```bash
python scripts/run_fast_verification.py
```

Expanded command sequence:

```bash
python src/analyze.py
python src/analyze_logic.py
python src/permutation_tests.py
python src/kappa.py
python scripts/prepare_human_review_sample.py
python scripts/generate_model_metadata.py
python scripts/generate_prompt_inventory.py
python scripts/generate_artifact_manifest.py
python scripts/prepare_arxiv_package.py
python scripts/prepare_release_bundle.py
python scripts/audit_dataset_integrity.py
python scripts/audit_numeric_claims.py
python scripts/audit_text_cleanliness.py
python scripts/audit_metadata.py
python scripts/test_fill_release_links.py
python scripts/audit_release.py
```

Expected result:

- `scripts/audit_release.py` ends with `Release audit passed.`
- `scripts/run_fast_verification.py` ends with `Fast verification passed.`
- `scripts/audit_dataset_integrity.py` ends with `Dataset integrity audit passed.`
- `scripts/audit_numeric_claims.py` ends with `Numeric claim audit passed.`
- `scripts/audit_text_cleanliness.py` ends with `Text cleanliness audit passed.`
- `scripts/audit_metadata.py` ends with `Metadata audit passed.`
- `scripts/test_fill_release_links.py` ends with `Release-link fill self-test passed.`
- `results/tables/chisq.txt` reports:
  - `chi2 = 21.290`
  - `p-value = 0.265`
  - `Cramer's V = 0.254`
  - `cells with expected count < 5 = 24/28`
- `results/tables/logic_binary_chisq.txt` reports:
  - `chi2 = 3.394`
  - `p-value = 0.3347`
  - `Cramer's V = 0.176`
  - `cells with expected count < 5 = 3/8`
- `results/tables/permutation_tests.txt` reports deterministic 10,000-iteration
  RQ2 permutation checks:
  - full category-by-model permutation p-value = `0.2691`
  - LOGIC/non-LOGIC permutation p-value = `0.3445`
- `results/tables/pass_rates.csv`, `category_frequency.csv`, and
  `logic_subcategory.csv` include Wilson 95% confidence intervals for the reported
  binomial proportions.
- `results/tables/model_metadata.csv` records model identifiers, provider endpoint,
  access date, generation settings, and labeler settings.
- `submission_materials/PROMPT_INVENTORY.md` and
  `results/tables/prompt_inventory.csv` record prompt templates, source symbols,
  and SHA-256 hashes.
- `results/tables/auto_label_agreement.txt` reports:
  - `n_aligned=96`
  - `exact_agreement=42/96 (43.8%)`
  - `cohens_kappa=0.305 (fair)`
- `build/arxiv_package/` contains a self-contained arXiv source package.
- `build/release/llm-code-bug-taxonomy-artifact-v0.1.0.zip` contains a clean release bundle
  for Zenodo or manual artifact sharing.
- `results/human_eval/review_sheet.csv` contains 40 blind review items with blank
  human-label fields.

This mode is the recommended first check for reviewers because it is deterministic
with respect to the released data files.

The same fast verification path is encoded in `.github/workflows/release-audit.yml`
for public GitHub repositories. It does not require external API keys.

## Full Pipeline Regeneration

This path regenerates the model generations and labels. It requires external API
access and may produce slightly different results if hosted model providers update
their model routing.

Create `.env`:

```text
OPENROUTER_API_KEY=your_key_here
```

Then run:

```bash
python src/generate.py
python src/run_tests.py
python src/label.py
python src/sublabel.py
python src/analyze.py
python src/analyze_logic.py
python src/permutation_tests.py
python src/second_annotator.py
python src/kappa.py
python scripts/prepare_human_review_sample.py
python scripts/generate_model_metadata.py
python scripts/generate_prompt_inventory.py
python scripts/generate_artifact_manifest.py
python scripts/prepare_arxiv_package.py
python scripts/prepare_release_bundle.py
python scripts/audit_dataset_integrity.py
python scripts/audit_numeric_claims.py
python scripts/audit_text_cleanliness.py
python scripts/audit_metadata.py
python scripts/test_fill_release_links.py
python scripts/audit_release.py
```

Important:

- `.env` is intentionally ignored by Git.
- Do not commit API keys.
- Hosted model identifiers may route to provider-current weights, so exact
  regeneration can differ from the released artifact.
- The released JSONL and CSV files are the authoritative artifact for the current
  paper draft.

## Core Claims and Evidence

| Claim | Evidence file |
|---|---|
| 656 total generations | `data/processed/results.jsonl` |
| 546 pass, 110 fail | `data/processed/results.jsonl`, checked by `scripts/audit_release.py` |
| 87.3% of failures are LOGIC; 95% CI 79.8-92.3 | `results/tables/category_frequency.csv` |
| LOGIC subtype distribution with 95% CIs | `results/tables/logic_subcategory.csv` |
| RQ2 full-category chi-square and Cramer's V | `results/tables/chisq.txt` |
| RQ2 LOGIC/non-LOGIC companion test | `results/tables/logic_binary_chisq.txt` |
| RQ2 sparse-table permutation checks | `results/tables/permutation_tests.txt` |
| LLM-vs-LLM subtype agreement | `results/tables/auto_label_agreement.txt` |
| Optional human-review instrument | `results/human_eval/review_sheet.csv`, `results/human_eval/review_key.csv` |
| Model/provider/run metadata | `results/tables/model_metadata.csv`, `config.yaml` |
| Prompt templates and hashes | `submission_materials/PROMPT_INVENTORY.md`, `results/tables/prompt_inventory.csv` |
| Data/file checksums | `results/tables/artifact_manifest.csv` |
| Data schema | `submission_materials/DATA_DICTIONARY.md` |
| One-command deterministic verification | `scripts/run_fast_verification.py` |
| Dataset coverage and cross-file consistency | `scripts/audit_dataset_integrity.py` |
| Manuscript numeric-claim consistency | `scripts/audit_numeric_claims.py` |
| UTF-8 and mojibake guard for source/submission text | `scripts/audit_text_cleanliness.py` |
| CFF and Zenodo metadata structure checks | `scripts/audit_metadata.py` |
| DOI/link replacement self-test | `scripts/test_fill_release_links.py` |

## Manuscript Builds

arXiv package:

```bash
python scripts/prepare_arxiv_package.py
cd build/arxiv_package
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Software Impacts manuscript:

```bash
pdflatex paper/software_impacts.tex
```

Or compile both manuscripts with the helper script:

```bash
python scripts/compile_manuscripts.py
```

This local environment may not include LaTeX. If `pdflatex` is unavailable, use a
local TeX distribution or Overleaf to compile the manuscripts. Detailed local and
Overleaf steps are in `submission_materials/PDF_BUILD_GUIDE.md`.

## Final Submission Gate

After replacing all public repository, arXiv, and archive DOI placeholders, run:

```bash
python scripts/fill_release_links.py --repo-url <URL> --archive-url <DOI_URL> --arxiv-url <URL>
python scripts/compile_manuscripts.py
python scripts/audit_submission_ready.py
```

This strict gate intentionally fails while `TBD` placeholders remain or while
`pdflatex`/`bibtex` are unavailable. Use `scripts/audit_release.py` for ordinary
artifact verification before those external release steps are complete.

## Known Limitations

- Current results are based on HumanEval only.
- Current generations use one sample per model/problem.
- Fine-grained subtype labels are machine-assigned and have fair LLM-vs-LLM
  agreement, not human validation.
- A 40-item blind human-review sheet is included, but its label fields are blank
  until reviewers complete it.
- The RQ2 chi-square tests are exploratory because the full category table is
  sparse and the LOGIC/non-LOGIC companion table still has some low expected counts.
- Public repository and archive DOI fields are still `TBD` until the artifact is
  released.

## Troubleshooting

- If `openai` or `yaml` imports fail, reinstall dependencies with
  `pip install -r requirements.txt`.
- If full regeneration fails with an API error, verify `.env` and provider access.
- If `scripts/audit_release.py` reports a stale arXiv package, rerun
  `python scripts/prepare_arxiv_package.py`.
- If `scripts/audit_release.py` reports a missing release bundle, rerun
  `python scripts/prepare_release_bundle.py`.
- If `scripts/run_fast_verification.py` fails, inspect the first failing command
  printed after the `==>` marker.
- If `scripts/audit_release.py` reports missing manifest entries, rerun
  `python scripts/generate_artifact_manifest.py`.
- If `scripts/audit_dataset_integrity.py` fails, inspect the reported key mismatch
  before regenerating downstream tables or editing manuscript claims.
- If `scripts/audit_numeric_claims.py` fails, compare the cited manuscript phrase
  with the corresponding CSV/TXT result table before editing either file.
- If LaTeX compilation fails, first confirm that the generated arXiv package has
  local figure paths and all required PNG files.
