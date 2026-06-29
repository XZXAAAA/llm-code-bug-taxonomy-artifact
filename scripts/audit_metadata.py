"""Validate citation metadata used for release/submission."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TITLE = "Bug Types in LLM-Generated Code: A Reproducible Empirical Pipeline"
EXPECTED_VERSION = "0.1.0"
EXPECTED_LICENSE = "MIT"
EXPECTED_AUTHOR_FAMILY = "Xie"
EXPECTED_AUTHOR_GIVEN = "Zixiao"
EXPECTED_AFFILIATION = "University of Illinois Urbana-Champaign"


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def audit_citation(failures: list[str]) -> None:
    path = ROOT / "CITATION.cff"
    if not path.exists():
        fail("missing CITATION.cff", failures)
        return
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"CITATION.cff is not valid YAML: {exc}", failures)
        return

    expected = {
        "cff-version": "1.2.0",
        "title": EXPECTED_TITLE,
        "type": "software",
        "license": EXPECTED_LICENSE,
        "version": EXPECTED_VERSION,
    }
    for key, value in expected.items():
        if data.get(key) == value:
            ok(f"CITATION.cff {key}={value}")
        else:
            fail(f"CITATION.cff {key}={data.get(key)!r}, expected {value!r}", failures)

    authors = data.get("authors", [])
    if authors and authors[0].get("family-names") == EXPECTED_AUTHOR_FAMILY and authors[0].get("given-names") == EXPECTED_AUTHOR_GIVEN:
        ok("CITATION.cff primary author is Xie, Zixiao")
    else:
        fail("CITATION.cff primary author is not Xie, Zixiao", failures)

    preferred = data.get("preferred-citation", {})
    if preferred.get("type") == "article" and preferred.get("journal") == "arXiv preprint":
        ok("CITATION.cff preferred citation describes the arXiv article")
    else:
        fail("CITATION.cff preferred citation is missing article/arXiv metadata", failures)


def main() -> None:
    failures: list[str] = []
    audit_citation(failures)
    if failures:
        print("\nMetadata audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)
    print("\nMetadata audit passed.")


if __name__ == "__main__":
    main()
