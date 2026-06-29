"""Strict final-submission audit.

Use this only after the public repository, arXiv URL, archive DOI, and LaTeX
environment are available. Unlike audit_release.py, this script fails on `TBD`
placeholders and missing TeX tools.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NO_TBD_FILES = [
    "CITATION.cff",
    "paper/software_impacts.tex",
    "submission_materials/SOFTWARE_METADATA.md",
    "submission_materials/SUBMISSION_STATEMENTS.md",
]


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def run_release_audit(failures: list[str]) -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/audit_release.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        ok("scripts/audit_release.py passes")
    else:
        print(proc.stdout)
        print(proc.stderr)
        fail("scripts/audit_release.py failed", failures)


def audit_no_tbd(failures: list[str]) -> None:
    for rel in NO_TBD_FILES:
        path = ROOT / rel
        if not path.exists():
            fail(f"missing {rel}", failures)
            continue
        text = path.read_text(encoding="utf-8")
        if "TBD" in text:
            fail(f"{rel} still contains TBD placeholder", failures)
        else:
            ok(f"{rel} has no TBD placeholder")


def audit_tex_tools(failures: list[str]) -> None:
    missing = False
    for tool in ["pdflatex", "bibtex"]:
        if shutil.which(tool):
            ok(f"found {tool}")
        else:
            fail(f"{tool} not found; install LaTeX or compile in Overleaf", failures)
            missing = True
    if not missing:
        proc = subprocess.run(
            [sys.executable, "scripts/compile_manuscripts.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            ok("scripts/compile_manuscripts.py passes")
        else:
            print(proc.stdout)
            print(proc.stderr)
            fail("scripts/compile_manuscripts.py failed", failures)


def audit_release_bundle(failures: list[str]) -> None:
    bundle = ROOT / "build" / "release" / "llm-code-bug-taxonomy-artifact-v0.1.0.zip"
    if bundle.exists():
        ok(f"found release bundle: {bundle.relative_to(ROOT)}")
    else:
        fail("missing release bundle; run scripts/prepare_release_bundle.py", failures)


def audit_submission_text(failures: list[str]) -> None:
    statements = ROOT / "submission_materials" / "SUBMISSION_STATEMENTS.md"
    text = statements.read_text(encoding="utf-8") if statements.exists() else ""
    for snippet in [
        "The author declares no competing interests.",
        "This research received no specific grant",
        "The source code is available under the MIT License.",
    ]:
        if snippet in text:
            ok(f"submission statements contain: {snippet}")
        else:
            fail(f"submission statements missing: {snippet}", failures)


def main() -> None:
    failures: list[str] = []
    run_release_audit(failures)
    audit_no_tbd(failures)
    audit_tex_tools(failures)
    audit_release_bundle(failures)
    audit_submission_text(failures)

    if failures:
        print("\nSubmission-ready audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("\nSubmission-ready audit passed.")


if __name__ == "__main__":
    main()
