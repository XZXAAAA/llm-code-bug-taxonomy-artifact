# arXiv Package Notes

The current manuscript is in `paper/main.tex`. It is convenient for local drafting,
but arXiv should receive a self-contained source package.

## Current Issue

The manuscript currently references figures through paths like:

```tex
\includegraphics{../results/figures/fig1_category_freq.png}
```

arXiv source packages are safer when all files are in one folder or simple
subfolders. Before upload, copy the three figures into the paper package and update
the paths.

## Suggested Package Folder

Run the package helper:

```bash
python scripts/prepare_arxiv_package.py
```

It creates:

```text
build/arxiv_package/
  main.tex
  references.bib
  fig1_category_freq.png
  fig2_category_by_model.png
  fig3_logic_subcat.png
  MANIFEST.txt
```

The helper also rewrites the figure paths in `main.tex`:

```tex
\includegraphics[width=0.95\linewidth]{fig1_category_freq.png}
\includegraphics[width=0.95\linewidth]{fig3_logic_subcat.png}
\includegraphics[width=0.95\linewidth]{fig2_category_by_model.png}
```

## Pre-Upload Commands

From the package folder:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Fix every missing-file warning before upload.

## Do Not Upload

- `.env`
- API keys
- private logs
- local virtual environments
- raw temporary cache files
- screenshots that reveal private workspace information

## Recommended Abstract Positioning

Call the study a reproducible empirical pilot unless the second annotator and any
human validation have been completed. This protects the paper from overclaiming.
