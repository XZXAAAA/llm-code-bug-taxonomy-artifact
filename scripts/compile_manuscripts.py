"""Compile arXiv and Software Impacts manuscripts when LaTeX is available."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARXIV_DIR = ROOT / "build" / "arxiv_package"
PDF_DIR = ROOT / "build" / "pdf"
SI_BUILD = ROOT / "build" / "software_impacts"


def require_tool(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"{name} not found. Install LaTeX locally or compile in Overleaf.")


def run(cmd: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(cmd)}  (cwd={cwd.relative_to(ROOT)})")
    subprocess.run(cmd, cwd=cwd, check=True)


def compile_arxiv() -> Path:
    run([sys.executable, "scripts/prepare_arxiv_package.py"], ROOT)
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], ARXIV_DIR)
    run(["bibtex", "main"], ARXIV_DIR)
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], ARXIV_DIR)
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], ARXIV_DIR)
    pdf = ARXIV_DIR / "main.pdf"
    if not pdf.exists():
        raise RuntimeError("arXiv PDF was not produced")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / "main_arxiv.pdf"
    shutil.copy2(pdf, out)
    return out


def compile_software_impacts() -> Path:
    SI_BUILD.mkdir(parents=True, exist_ok=True)
    run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory",
            str(SI_BUILD),
            str(ROOT / "paper" / "software_impacts.tex"),
        ],
        ROOT,
    )
    pdf = SI_BUILD / "software_impacts.pdf"
    if not pdf.exists():
        raise RuntimeError("Software Impacts PDF was not produced")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / "software_impacts.pdf"
    shutil.copy2(pdf, out)
    return out


def main() -> None:
    require_tool("pdflatex")
    require_tool("bibtex")
    arxiv_pdf = compile_arxiv()
    si_pdf = compile_software_impacts()
    print(f"compiled {arxiv_pdf.relative_to(ROOT)}")
    print(f"compiled {si_pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
