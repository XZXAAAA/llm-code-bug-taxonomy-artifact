"""Generate checksums and basic metadata for release artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "tables" / "artifact_manifest.csv"
OUT_JSON = ROOT / "results" / "tables" / "artifact_manifest.json"

INCLUDE_DIRS = [
    "config.yaml",
    ".github",
    "README.md",
    "REPRODUCIBILITY.md",
    "PROTOCOL.md",
    "CITATION.cff",
    "LICENSE",
    "requirements.txt",
    "src",
    "scripts",
    "paper",
    "data/raw",
    "data/processed",
    "results/tables",
    "results/figures",
    "results/human_eval",
    "submission_materials",
]

EXCLUDE_PARTS = {
    "__pycache__",
    "official_templates",
}

EXCLUDE_NAMES = {
    "artifact_manifest.csv",
    "artifact_manifest.json",
}

TEXT_LIKE_EXTENSIONS = {
    ".bib",
    ".cff",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".tex",
    ".txt",
    ".yaml",
    ".yml",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int | str:
    if path.suffix.lower() not in TEXT_LIKE_EXTENSIONS:
        return ""
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return ""


def iter_files() -> list[Path]:
    files: list[Path] = []
    for item in INCLUDE_DIRS:
        path = ROOT / item
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                if not child.is_file():
                    continue
                rel = child.relative_to(ROOT)
                if any(part in EXCLUDE_PARTS for part in rel.parts):
                    continue
                if child.name in EXCLUDE_NAMES:
                    continue
                files.append(child)
    return sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())


def main() -> None:
    rows = []
    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        rows.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "lines": line_count(path),
                "sha256": sha256(path),
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "lines", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} artifact records -> {OUT_CSV}")


if __name__ == "__main__":
    main()
