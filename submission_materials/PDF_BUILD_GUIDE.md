# PDF Build Guide

This repository can prepare self-contained manuscript source packages, but the
current local Windows environment may not include a TeX distribution. Use this
guide before arXiv upload or Elsevier Software Impacts submission.

## Required PDFs

- `build/pdf/main_arxiv.pdf`: research manuscript for arXiv.
- `build/pdf/software_impacts.pdf`: Software Impacts manuscript draft.

## Option A: Local TeX Build

Install a TeX distribution that provides `pdflatex` and `bibtex`, such as TeX
Live or MiKTeX. Then run:

```bash
python scripts/prepare_arxiv_package.py
python scripts/compile_manuscripts.py
python scripts/audit_submission_ready.py
```

Expected result after public links are filled:

```text
Submission-ready audit passed.
```

If compilation fails, inspect:

- `build/arxiv_package/main.log`
- `build/arxiv_package/main.blg`
- `build/software_impacts/software_impacts.log`

Do not submit until missing-file, undefined-citation, and fatal LaTeX errors are
resolved.

## Option B: Overleaf Build

Use Overleaf if a local TeX installation is not available.

### arXiv Manuscript

1. Run:

   ```bash
   python scripts/prepare_arxiv_package.py
   ```

2. Create a blank Overleaf project.
3. Upload every file from `build/arxiv_package/`:

   ```text
   main.tex
   references.bib
   fig1_category_freq.png
   fig2_category_by_model.png
   fig3_logic_subcat.png
   MANIFEST.txt
   ```

4. Set `main.tex` as the main file.
5. Compile with pdfLaTeX.
6. Confirm that all three figures render and that references are resolved.

### Software Impacts Manuscript

1. Create a separate Overleaf project.
2. Upload `paper/software_impacts.tex`.
3. Compile with pdfLaTeX.
4. Confirm that the code metadata table is readable and that the public
   repository/archive placeholders have been replaced before formal submission.

## arXiv Upload Package

Upload the contents of `build/arxiv_package/`, not `paper/main.tex` directly.
The helper rewrites figure paths so arXiv can find the PNG files without local
directory references.

## Final Checks

Before creating a GitHub release or Zenodo DOI:

```bash
python src/analyze.py
python src/analyze_logic.py
python src/kappa.py
python scripts/prepare_human_review_sample.py
python scripts/generate_artifact_manifest.py
python scripts/prepare_arxiv_package.py
python scripts/prepare_release_bundle.py
python scripts/audit_release.py
```

After GitHub, Zenodo, and arXiv links are available, run:

```bash
python scripts/fill_release_links.py --repo-url <URL> --archive-url <DOI_URL> --arxiv-url <ARXIV_URL>
python scripts/audit_submission_ready.py
```

`audit_submission_ready.py` is expected to fail while `TBD` placeholders remain
or while `pdflatex`/`bibtex` are unavailable.
