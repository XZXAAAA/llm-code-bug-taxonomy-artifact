"""Fill public repository, archive DOI, and arXiv links across release files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str, dry_run: bool) -> bool:
    old = _read(path)
    changed = old != text
    if changed and not dry_run:
        path.write_text(text, encoding="utf-8")
    return changed


def update_citation(repo_url: str, archive_url: str, arxiv_url: str, dry_run: bool) -> bool:
    path = ROOT / "CITATION.cff"
    text = _read(path)
    text = text.replace('repository-code: "TBD"', f'repository-code: "{repo_url}"')
    text = text.replace('url: "TBD"', f'url: "{archive_url}"', 1)
    text = text.replace('  url: "TBD"', f'  url: "{arxiv_url}"')
    return _write(path, text, dry_run)


def update_zenodo(repo_url: str, arxiv_url: str, dry_run: bool) -> bool:
    path = ROOT / ".zenodo.json"
    data = json.loads(_read(path))
    data["related_identifiers"] = [
        {
            "identifier": arxiv_url,
            "relation": "isSupplementTo",
            "scheme": "url",
            "resource_type": "publication-preprint",
        },
        {
            "identifier": repo_url,
            "relation": "isIdenticalTo",
            "scheme": "url",
            "resource_type": "software",
        },
    ]
    data["notes"] = "Do not archive .env or API keys."
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return _write(path, text, dry_run)


def update_software_impacts(repo_url: str, archive_url: str, dry_run: bool) -> bool:
    path = ROOT / "paper" / "software_impacts.tex"
    text = _read(path)
    text = text.replace("TBD: public repository URL", repo_url)
    text = text.replace("TBD: archived release DOI or reproducible capsule URL", archive_url)
    text = text.replace("TBD: archived software DOI", archive_url)
    return _write(path, text, dry_run)


def update_software_metadata(repo_url: str, archive_url: str, dry_run: bool) -> bool:
    path = ROOT / "submission_materials" / "SOFTWARE_METADATA.md"
    text = _read(path)
    text = text.replace("| Permanent link to code/repository | TBD |", f"| Permanent link to code/repository | {repo_url} |")
    text = text.replace("| Permanent link to reproducible capsule/archive | TBD |", f"| Permanent link to reproducible capsule/archive | {archive_url} |")
    text = text.replace("| Software citation DOI | TBD |", f"| Software citation DOI | {archive_url} |")
    text = text.replace(
        "This file is a draft metadata table for Elsevier Software Impacts. Replace `TBD`\nfields after the repository and archived release are public.\n\n",
        "",
    )
    return _write(path, text, dry_run)


def update_submission_statements(repo_url: str, archive_url: str, arxiv_url: str, dry_run: bool) -> bool:
    path = ROOT / "submission_materials" / "SUBMISSION_STATEMENTS.md"
    text = _read(path)
    text = text.replace(
        "These statements are draft text for arXiv, Software Impacts, PeerJ Computer\n"
        "Science, or repository/archive submissions. Replace `TBD` fields before formal\n"
        "submission.\n\n",
        "These statements are draft text for arXiv, Software Impacts, PeerJ Computer\n"
        "Science, or repository/archive submissions.\n\n",
    )
    text = text.replace("Repository URL: TBD", f"Repository URL: {repo_url}")
    text = text.replace("Archive DOI: TBD", f"Archive DOI: {archive_url}")
    text = text.replace("Archived release: TBD", f"Archived release: {archive_url}")
    text = text.replace(
        "artifact-audit scripts. Repository and archived artifact: TBD.",
        f"artifact-audit scripts. Repository: {repo_url}. Archived artifact: {archive_url}. arXiv: {arxiv_url}.",
    )
    return _write(path, text, dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", required=True, help="Public repository URL")
    parser.add_argument("--archive-url", required=True, help="Archive DOI/URL, e.g. Zenodo DOI URL")
    parser.add_argument("--arxiv-url", required=True, help="arXiv preprint URL")
    parser.add_argument("--dry-run", action="store_true", help="Report changed files without writing")
    args = parser.parse_args()

    changed = {
        "CITATION.cff": update_citation(args.repo_url, args.archive_url, args.arxiv_url, args.dry_run),
        ".zenodo.json": update_zenodo(args.repo_url, args.arxiv_url, args.dry_run),
        "paper/software_impacts.tex": update_software_impacts(args.repo_url, args.archive_url, args.dry_run),
        "submission_materials/SOFTWARE_METADATA.md": update_software_metadata(args.repo_url, args.archive_url, args.dry_run),
        "submission_materials/SUBMISSION_STATEMENTS.md": update_submission_statements(args.repo_url, args.archive_url, args.arxiv_url, args.dry_run),
    }

    mode = "would update" if args.dry_run else "updated"
    for path, did_change in changed.items():
        print(f"{mode if did_change else 'unchanged'}: {path}")


if __name__ == "__main__":
    main()
