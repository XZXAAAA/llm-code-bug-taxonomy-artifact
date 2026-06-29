# Bug Types in LLM-Generated Code: Empirical Study

A reproducible empirical study of what kinds of bugs appear in LLM-generated
Python code. Four hosted models are evaluated on HumanEval; failures are
categorized into a bug taxonomy and compared across models.

For reviewer-style reproduction, start with [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Headline Results

- 656 generations: 4 models x 164 HumanEval problems.
- 546 pass, 110 fail, for an overall pass rate of 83.2%.
- RQ1: 87.3% of failures are wrong-output LOGIC errors: code runs, but returns a wrong
  result (95% Wilson CI: 79.8-92.3%).
- RQ1b: within LOGIC failures, mathematical-reasoning errors account for 44.8%
  (43/96; 95% CI: 35.2-54.7%) and wrong-algorithm choices for 21.9%
  (21/96; 95% CI: 14.8-31.1%).
- RQ2: the category-by-model test does not detect a statistically significant
  association: chi2 = 21.29, dof = 18, p = 0.27, Cramer's V = 0.254. This test
  is exploratory because the category-by-model table is sparse. A deterministic
  10,000-iteration permutation check gives p = 0.2691.
- RQ2 companion check: LOGIC/non-LOGIC by model also does not detect an association:
  chi2 = 3.394, dof = 3, p = 0.335, Cramer's V = 0.176; permutation p = 0.3445.
- Robustness: independent blind LLM-vs-LLM LOGIC subtype agreement is fair
  (Cohen's kappa = 0.305; exact agreement = 42/96, 43.8%).

## Reproduce

```bash
pip install -r requirements.txt

# Deterministic no-API artifact verification:
python scripts/run_fast_verification.py

# Full regeneration requires an OpenRouter API key:
# Set OPENROUTER_API_KEY in .env.

python src/generate.py          # 01 generate code from models
python src/run_tests.py         # 02 run unit tests -> data/processed/results.jsonl
python src/label.py             # 03 label failures -> data/processed/labeled.jsonl
python src/sublabel.py          # 04 refine LOGIC into 7 subtypes
python src/analyze.py           # 05 tables + figures for RQ1/RQ2
python src/analyze_logic.py     # 05b LOGIC subtype table + figure
python src/permutation_tests.py # 05c deterministic RQ2 permutation checks

# Independent automatic agreement check for the paper:
python src/second_annotator.py  # 06 independent blind LLM annotator
python src/kappa.py             # 07 LLM-vs-LLM agreement, optional human agreement
python scripts/prepare_human_review_sample.py  # 08 blind 40-item human-review sheet
python scripts/generate_prompt_inventory.py    # 09 prompt inventory and hashes

# Submission packaging:
python scripts/generate_model_metadata.py
python scripts/generate_artifact_manifest.py
python scripts/prepare_arxiv_package.py
python scripts/prepare_release_bundle.py

# Lightweight release audit:
python scripts/run_fast_verification.py
python scripts/audit_dataset_integrity.py
python scripts/audit_numeric_claims.py
python scripts/audit_text_cleanliness.py
python scripts/audit_metadata.py
python scripts/test_fill_release_links.py
python scripts/audit_release.py

# Final submission gate, expected to fail until TBD links are replaced and LaTeX is available:
python scripts/fill_release_links.py --repo-url <URL> --archive-url <DOI_URL> --arxiv-url <URL> --dry-run
python scripts/compile_manuscripts.py
python scripts/audit_submission_ready.py
```

`src/second_annotator.py` deliberately does not see the reference solution, the
primary label, or the primary explanation. The resulting statistic is reported as
LLM-vs-LLM agreement. It is not a substitute for human validation.

The current agreement result is reported as a limitation: the blind second
annotator agrees exactly on 42/96 LOGIC subtype labels and yields Cohen's kappa =
0.305. The largest disagreement is that the primary annotator uses MATH_REASONING
more often than the blind annotator.

The repository also includes a deterministic 40-item blind human-review sample in
`results/human_eval/`. The sheet is intentionally blank; the current paper does not
claim human validation. It should not claim human validation unless two human
reviewers complete it.

## Layout

```text
PROTOCOL.md                    pre-registered research design
REPRODUCIBILITY.md             artifact verification and full regeneration guide
config.yaml                    provider, models, generation settings
CITATION.cff                   citation metadata for software/archive release
.zenodo.json                   Zenodo metadata template
.github/workflows/             GitHub Actions release audit workflow
src/
  generate.py                  multi-model generation through OpenRouter
  run_tests.py                 pass/fail and failure signal extraction
  label.py                     main bug-type labeling
  sublabel.py                  LOGIC subtype labeling with reference solution
  second_annotator.py          independent blind LOGIC subtype annotator
  kappa.py                     agreement calculation
  prepare_human_review_sample.py blind human-review sample builder
  analyze.py                   RQ1/RQ2 tables and figures
  analyze_logic.py             LOGIC subtype tables and figures
  permutation_tests.py         deterministic RQ2 permutation checks for sparse tables
scripts/
  prepare_arxiv_package.py      self-contained arXiv source-package builder
  prepare_release_bundle.py     clean Zenodo/manual release ZIP builder
  fill_release_links.py         synchronize public repository/archive/arXiv links
  compile_manuscripts.py        compile arXiv and Software Impacts PDFs when LaTeX is available
  run_fast_verification.py      no-API reviewer verification entry point
  generate_model_metadata.py    machine-readable model/provider/run metadata
  generate_prompt_inventory.py  prompt inventory with hashes
  generate_artifact_manifest.py release artifact checksums and file metadata
  audit_dataset_integrity.py    row-level coverage and cross-file consistency checks
  audit_numeric_claims.py       structured check that paper numbers match result files
  audit_text_cleanliness.py     UTF-8 and mojibake guard for source and submission text
  audit_metadata.py             CFF and Zenodo metadata structure checks
  test_fill_release_links.py    temporary-copy self-test for DOI/link replacement
  audit_release.py              release consistency and secret-pattern audit
  audit_submission_ready.py     strict final gate for DOI/link/LaTeX readiness
data/raw/                      HumanEval and per-model generations
data/processed/                results, labels, subtype labels
results/tables/                CSV/TXT result tables
results/figures/               generated figures
paper/main.tex                 arXiv / research-paper manuscript draft
paper/software_impacts.tex     Software Impacts manuscript draft
submission_materials/          arXiv and Software Impacts preparation notes/templates
  PROMPT_INVENTORY.md          prompt templates, sources, and hashes
  PDF_BUILD_GUIDE.md           local TeX and Overleaf PDF build instructions
```

## Models

Generation models are `openai/gpt-4o-mini`, `deepseek/deepseek-chat`,
`qwen/qwen-2.5-72b-instruct`, and `meta-llama/llama-3.1-8b-instruct`.
All are accessed through OpenRouter. Generation uses one sample per problem,
temperature 0.2, and max 1024 tokens. The recorded access date is 2026-06-23.

Machine-readable model, provider, generation, and labeler metadata is written to
`results/tables/model_metadata.csv`. Hosted model identifiers may route to
provider-current weights, so exact regeneration depends on provider stability.

## Continuous Audit

The repository includes `.github/workflows/release-audit.yml`. On GitHub, it runs
the deterministic artifact verification path: regenerate analysis tables/figures
from released data, rebuild the artifact manifest and arXiv package, then run
`scripts/audit_release.py`. It does not call external model APIs and does not
require API keys.

## Manuscripts

The repository includes two manuscript drafts:

- `paper/main.tex`: research manuscript source for an arXiv-style preprint.
- `paper/software_impacts.tex`: software-article draft following the Software
  Impacts article structure.

Public repository, archive DOI, and preprint links can be synchronized after
release with `scripts/fill_release_links.py`.
