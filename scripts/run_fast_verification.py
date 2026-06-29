"""Run the deterministic no-API verification path used for artifact review."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    ["src/analyze.py"],
    ["src/analyze_logic.py"],
    ["src/permutation_tests.py"],
    ["src/kappa.py"],
    ["scripts/prepare_human_review_sample.py"],
    ["scripts/generate_model_metadata.py"],
    ["scripts/generate_prompt_inventory.py"],
    ["scripts/generate_artifact_manifest.py"],
    ["scripts/prepare_arxiv_package.py"],
    ["scripts/prepare_release_bundle.py"],
    ["scripts/audit_text_cleanliness.py"],
    ["scripts/audit_metadata.py"],
    ["scripts/test_fill_release_links.py"],
    ["scripts/audit_dataset_integrity.py"],
    ["scripts/audit_numeric_claims.py"],
    ["scripts/audit_release.py"],
]


def main() -> None:
    for command in COMMANDS:
        printable = " ".join(["python", *command])
        print(f"\n==> {printable}")
        subprocess.run([sys.executable, *command], cwd=ROOT, check=True)
    print("\nFast verification passed.")


if __name__ == "__main__":
    main()
