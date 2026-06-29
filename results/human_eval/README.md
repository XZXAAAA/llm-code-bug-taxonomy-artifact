# Human Review Sample

This folder contains a deterministic 40-item stratified sample of LOGIC failures for optional human validation.

- `review_sheet.csv` is the blind sheet for two human reviewers.
- `review_key.csv` stores the original LLM labels and must not be used during blind review.
- Valid labels: WRONG_ALGO, MISSING_EDGE, BOUNDARY, STATE_UPDATE, MATH_REASONING, PREMATURE_SIMPL, SPEC_PARTIAL.
- Fill `label_coderA` and `label_coderB` before running `python src/kappa.py` for optional human agreement.
- Blank labels mean that no human-validation claim should be made.

Sampling seed: 20260624.
Requested sample size: 40.
