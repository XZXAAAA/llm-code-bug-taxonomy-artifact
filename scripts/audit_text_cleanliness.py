"""Check source and submission text for encoding artifacts and stale markers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_DIRS = [
    "src",
    "scripts",
    "paper",
    "submission_materials",
    "results/human_eval",
    ".github",
]

SCAN_FILES = [
    "README.md",
    "REPRODUCIBILITY.md",
    "PROTOCOL.md",
    "config.yaml",
    "requirements.txt",
    "CITATION.cff",
    ".zenodo.json",
]

TEXT_SUFFIXES = {
    ".bib",
    ".cff",
    ".csv",
    ".json",
    ".md",
    ".py",
    ".tex",
    ".txt",
    ".yaml",
    ".yml",
}

MOJIBAKE_CODEPOINTS = [
    0xFFFD,  # replacement character
    0x9422,
    0x6748,
    0x9365,
    0x7481,
    0x93C3,
    0x951B,
    0x9286,
    0x6D93,
    0x7EEB,
    0x701B,
    0x752F,
    0x6DC7,
    0x699B,
    0x6D60,
    0x59AF,
    0x9A9E,
    0x7035,
    0x6769,
    0x6D5C,
    0x7F01,
    0x7ED7,
    0x7EDB,
    0x9428,
    0x704F,
    0x93B4,
    0x93CD,
    0x9350,
    0x94CF,
    0x95C4,
    0x9359,
    0x5A09,
    0x6F6F,
    0x6437,
    0x95B2,
    0x762F,
    0x8FAB,
    0x89E6,
    0x7D88,
    0x5B95,
    0x93B6,
    0x6FB6,
    0x5D87,
]
MOJIBAKE_MARKERS = [chr(codepoint) for codepoint in MOJIBAKE_CODEPOINTS]


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_FILES:
        path = ROOT / rel
        if path.exists():
            files.append(path)
    for rel_dir in SCAN_DIRS:
        path = ROOT / rel_dir
        if not path.exists():
            continue
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.name == "audit_text_cleanliness.py":
                continue
            if "official_templates" in child.parts:
                continue
            if child.suffix.lower() in TEXT_SUFFIXES:
                files.append(child)
    return sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix())


def main() -> None:
    failures: list[str] = []
    for path in iter_text_files():
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        if b"\x00" in raw:
            failures.append(f"{rel}: contains NUL byte")
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: not valid UTF-8 ({exc})")
            continue
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                failures.append(f"{rel}: contains mojibake marker U+{ord(marker):04X}")
                break

    if failures:
        print("Text cleanliness audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print(f"Text cleanliness audit passed ({len(iter_text_files())} files checked).")


if __name__ == "__main__":
    main()
