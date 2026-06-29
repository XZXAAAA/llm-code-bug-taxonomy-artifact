"""Self-test release-link replacement on temporary copies of metadata files."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import yaml

import fill_release_links

ROOT = Path(__file__).resolve().parents[1]

TARGET_FILES = [
    "CITATION.cff",
    ".zenodo.json",
    "paper/software_impacts.tex",
    "submission_materials/SOFTWARE_METADATA.md",
    "submission_materials/SUBMISSION_STATEMENTS.md",
]

REPO_URL = "https://github.com/example/llm-bug-types"
ARCHIVE_URL = "https://doi.org/10.5281/zenodo.1234567"
ARXIV_URL = "https://arxiv.org/abs/2601.00001"


def copy_target_files(tmp_root: Path) -> None:
    for rel in TARGET_FILES:
        src = ROOT / rel
        dst = tmp_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def assert_no_tbd(tmp_root: Path) -> None:
    offenders = []
    for rel in TARGET_FILES:
        text = (tmp_root / rel).read_text(encoding="utf-8")
        if "TBD" in text:
            offenders.append(rel)
    if offenders:
        raise AssertionError(f"TBD placeholders remain after link fill: {offenders}")


def assert_expected_links(tmp_root: Path) -> None:
    citation = yaml.safe_load((tmp_root / "CITATION.cff").read_text(encoding="utf-8"))
    if citation["repository-code"] != REPO_URL:
        raise AssertionError("CITATION.cff repository-code was not filled")
    if citation["url"] != ARCHIVE_URL:
        raise AssertionError("CITATION.cff archive URL was not filled")
    if citation["preferred-citation"]["url"] != ARXIV_URL:
        raise AssertionError("CITATION.cff preferred-citation URL was not filled")

    zenodo = json.loads((tmp_root / ".zenodo.json").read_text(encoding="utf-8"))
    related = {item["relation"]: item["identifier"] for item in zenodo["related_identifiers"]}
    if related.get("isSupplementTo") != ARXIV_URL:
        raise AssertionError(".zenodo.json arXiv related identifier was not filled")
    if related.get("isIdenticalTo") != REPO_URL:
        raise AssertionError(".zenodo.json repository related identifier was not filled")

    software_impacts = (tmp_root / "paper/software_impacts.tex").read_text(encoding="utf-8")
    for link in [REPO_URL, ARCHIVE_URL]:
        if link not in software_impacts:
            raise AssertionError(f"paper/software_impacts.tex missing {link}")

    metadata = (tmp_root / "submission_materials/SOFTWARE_METADATA.md").read_text(encoding="utf-8")
    for link in [REPO_URL, ARCHIVE_URL]:
        if link not in metadata:
            raise AssertionError(f"SOFTWARE_METADATA.md missing {link}")

    statements = (tmp_root / "submission_materials/SUBMISSION_STATEMENTS.md").read_text(encoding="utf-8")
    for link in [REPO_URL, ARCHIVE_URL, ARXIV_URL]:
        if link not in statements:
            raise AssertionError(f"SUBMISSION_STATEMENTS.md missing {link}")


def main() -> None:
    original_root = fill_release_links.ROOT
    with tempfile.TemporaryDirectory(prefix="release-link-test-") as tmp:
        tmp_root = Path(tmp)
        copy_target_files(tmp_root)

        fill_release_links.ROOT = tmp_root
        try:
            changed = [
                fill_release_links.update_citation(REPO_URL, ARCHIVE_URL, ARXIV_URL, dry_run=False),
                fill_release_links.update_zenodo(REPO_URL, ARXIV_URL, dry_run=False),
                fill_release_links.update_software_impacts(REPO_URL, ARCHIVE_URL, dry_run=False),
                fill_release_links.update_software_metadata(REPO_URL, ARCHIVE_URL, dry_run=False),
                fill_release_links.update_submission_statements(REPO_URL, ARCHIVE_URL, ARXIV_URL, dry_run=False),
            ]
        finally:
            fill_release_links.ROOT = original_root

        if not all(changed):
            raise AssertionError("expected every release-link target file to change")
        assert_no_tbd(tmp_root)
        assert_expected_links(tmp_root)

    print("Release-link fill self-test passed.")


if __name__ == "__main__":
    main()
