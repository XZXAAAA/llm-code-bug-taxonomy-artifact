"""Prepare a self-contained arXiv source package.

The drafting manuscript references figures through ../results/figures/*.png.
arXiv submissions are safer when the TeX file, bibliography, and figures are in
one simple package folder. This script copies the required files and rewrites the
figure paths for upload.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FIGURES = ROOT / "results" / "figures"
OUT = ROOT / "build" / "arxiv_package"

FIGURE_NAMES = [
    "fig1_category_freq.png",
    "fig2_category_by_model.png",
    "fig3_logic_subcat.png",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    tex = (PAPER / "main.tex").read_text(encoding="utf-8")
    for figure_name in FIGURE_NAMES:
        tex = tex.replace(f"../results/figures/{figure_name}", figure_name)
    (OUT / "main.tex").write_text(tex, encoding="utf-8")

    shutil.copy2(PAPER / "references.bib", OUT / "references.bib")
    for figure_name in FIGURE_NAMES:
        shutil.copy2(FIGURES / figure_name, OUT / figure_name)

    manifest = "\n".join(
        [
            "arXiv package contents:",
            "main.tex",
            "references.bib",
            *FIGURE_NAMES,
            "",
            "Compile check:",
            "pdflatex main.tex",
            "bibtex main",
            "pdflatex main.tex",
            "pdflatex main.tex",
        ]
    )
    (OUT / "MANIFEST.txt").write_text(manifest + "\n", encoding="utf-8")
    print(f"Prepared arXiv package: {OUT}")


if __name__ == "__main__":
    main()
