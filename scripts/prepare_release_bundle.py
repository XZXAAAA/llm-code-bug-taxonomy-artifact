"""Create a clean release ZIP for Zenodo or manual artifact sharing."""

from __future__ import annotations

import zipfile
from pathlib import Path

from generate_artifact_manifest import ROOT, iter_files

VERSION = "0.1.0"
OUT_DIR = ROOT / "build" / "release"
OUT_ZIP = OUT_DIR / f"llm-code-bug-taxonomy-artifact-v{VERSION}.zip"

EXTRA_FILES = [
    ROOT / "results" / "tables" / "artifact_manifest.csv",
    ROOT / "results" / "tables" / "artifact_manifest.json",
]

FORBIDDEN_PARTS = {
    ".git",
    "__pycache__",
    "build",
}

FORBIDDEN_NAMES = {
    ".env",
}


def _validate_member(path: Path) -> None:
    rel = path.relative_to(ROOT)
    if any(part in FORBIDDEN_PARTS for part in rel.parts):
        raise ValueError(f"refusing to package forbidden path: {rel}")
    if path.name in FORBIDDEN_NAMES:
        raise ValueError(f"refusing to package forbidden file: {rel}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(iter_files()) + [path for path in EXTRA_FILES if path.exists()]
    files = sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            _validate_member(path)
            rel = path.relative_to(ROOT).as_posix()
            zf.write(path, rel)

    print(f"wrote {len(files)} files -> {OUT_ZIP}")


if __name__ == "__main__":
    main()
