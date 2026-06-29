# Release Checklist

Use this checklist before arXiv, Zenodo, Software Impacts, or PeerJ submission.

## Repository Hygiene

- [ ] No `.env` file committed.
- [ ] No API keys in tracked files.
- [ ] `LICENSE` exists and matches the license named in `CITATION.cff`.
- [ ] `CITATION.cff` has real repository metadata and no invalid placeholder URLs.
- [ ] `CITATION.cff` has real repository and archive URLs.
- [ ] `python scripts/fill_release_links.py --repo-url <URL> --archive-url <DOI_URL> --arxiv-url <URL>` has been run after public links are available.
- [ ] `README.md` explains how to reproduce the pipeline.
- [ ] `REPRODUCIBILITY.md` explains fast verification and full regeneration.
- [ ] `PROTOCOL.md` states labeling limitations accurately.
- [ ] `requirements.txt` includes all import-time dependencies.
- [ ] Generated outputs needed for reproduction are included or archived.
- [ ] GitHub Actions `release-audit.yml` passes after publishing the repository.

## Reproducibility

- [ ] `python scripts/run_fast_verification.py` passes.
- [ ] `python scripts/audit_release.py` passes.
- [ ] `python src/run_tests.py` can regenerate `data/processed/results.jsonl`.
- [ ] `python src/analyze.py` regenerates RQ1/RQ2 tables and figures.
- [ ] `python src/analyze_logic.py` regenerates LOGIC subtype tables and figure.
- [ ] `python src/permutation_tests.py` regenerates RQ2 sparse-table permutation checks.
- [ ] `python src/kappa.py` regenerates automatic agreement outputs.
- [ ] `python scripts/generate_model_metadata.py` regenerates model/provider/run metadata.
- [ ] `python scripts/generate_prompt_inventory.py` regenerates prompt inventory and hashes.
- [ ] `python scripts/generate_artifact_manifest.py` regenerates artifact checksums.
- [ ] `python scripts/prepare_arxiv_package.py` generates `build/arxiv_package/`.
- [ ] `python scripts/prepare_release_bundle.py` generates the clean release ZIP.
- [ ] `python scripts/audit_dataset_integrity.py` verifies raw/results/labels coverage and key consistency.
- [ ] `python scripts/audit_numeric_claims.py` verifies manuscript/support-document numbers against result files.
- [ ] `python scripts/audit_text_cleanliness.py` verifies UTF-8 text and rejects configured mojibake markers.
- [ ] `python scripts/audit_metadata.py` verifies citation metadata structure.
- [ ] `python scripts/test_fill_release_links.py` verifies DOI/link replacement on temporary copies.
- [ ] `python scripts/compile_manuscripts.py` generates manuscript PDFs in `build/pdf/`.
- [ ] `python scripts/audit_submission_ready.py` passes after repository/DOI links and LaTeX are ready.
- [ ] `submission_materials/PDF_BUILD_GUIDE.md` has been followed if local LaTeX is unavailable.

## Manuscript

- [ ] `paper/main.tex` compiles from the generated arXiv package.
- [ ] The paper reports Cohen's kappa = 0.305 as fair, not as strong validation.
- [ ] The paper does not claim human validation unless the human review sheet is completed.
- [x] Related work section has a sharpened comparison with Tambon et al. 2025.
- [ ] Figure paths are local inside the arXiv package.

## Software Impacts

- [x] Software Impacts template version is prepared at `paper/software_impacts.tex`.
- [ ] `paper/software_impacts.tex` compiles in a LaTeX environment.
- [ ] `paper/software_impacts.tex` has real repository/archive links instead of `TBD`.
- [ ] `submission_materials/SOFTWARE_METADATA.md` has real repository/archive links.
- [ ] Zenodo or another archive DOI is created.
- [x] Conflict of interest statement is drafted in `submission_materials/SUBMISSION_STATEMENTS.md`.
- [x] Funding statement is drafted in `submission_materials/SUBMISSION_STATEMENTS.md`.
- [x] Data availability statement is drafted in `submission_materials/SUBMISSION_STATEMENTS.md`.
- [x] Highlights are drafted in `submission_materials/SUBMISSION_STATEMENTS.md`.
