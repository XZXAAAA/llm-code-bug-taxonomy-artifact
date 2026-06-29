"""Generate a prompt inventory for the released artifact."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT_MD = ROOT / "submission_materials" / "PROMPT_INVENTORY.md"
OUT_CSV = ROOT / "results" / "tables" / "prompt_inventory.csv"

sys.path.insert(0, str(SRC))
from generate import PROMPT_TMPL  # noqa: E402
from label import CLASSIFY_PROMPT  # noqa: E402
from second_annotator import PROMPT as SECOND_ANNOTATOR_PROMPT  # noqa: E402
from sublabel import PROMPT as SUBLABEL_PROMPT  # noqa: E402


PROMPTS = [
    {
        "id": "generation_prompt",
        "stage": "code_generation",
        "source": "src/generate.py",
        "template_symbol": "PROMPT_TMPL",
        "template": PROMPT_TMPL,
    },
    {
        "id": "primary_failure_label_prompt",
        "stage": "primary_failure_labeling",
        "source": "src/label.py",
        "template_symbol": "CLASSIFY_PROMPT",
        "template": CLASSIFY_PROMPT,
    },
    {
        "id": "primary_logic_subtype_prompt",
        "stage": "logic_subtype_labeling",
        "source": "src/sublabel.py",
        "template_symbol": "PROMPT",
        "template": SUBLABEL_PROMPT,
    },
    {
        "id": "blind_second_logic_subtype_prompt",
        "stage": "blind_second_logic_subtype_labeling",
        "source": "src/second_annotator.py",
        "template_symbol": "PROMPT",
        "template": SECOND_ANNOTATOR_PROMPT,
    },
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for item in PROMPTS:
        template = item["template"]
        rows.append(
            {
                "id": item["id"],
                "stage": item["stage"],
                "source": item["source"],
                "template_symbol": item["template_symbol"],
                "characters": len(template),
                "sha256": sha256_text(template),
            }
        )

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "stage", "source", "template_symbol", "characters", "sha256"],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Prompt Inventory",
        "",
        "This file records the prompt templates used by the released pipeline. "
        "Templates are shown before runtime problem/code substitution.",
        "",
        "| ID | Stage | Source | Symbol | Characters | SHA-256 |",
        "|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {stage} | `{source}` | `{template_symbol}` | {characters} | `{sha256}` |".format(
                **row
            )
        )
    lines.append("")

    for item in PROMPTS:
        lines.extend(
            [
                f"## {item['id']}",
                "",
                f"- Stage: `{item['stage']}`",
                f"- Source: `{item['source']}`",
                f"- Symbol: `{item['template_symbol']}`",
                f"- SHA-256: `{sha256_text(item['template'])}`",
                "",
                "```text",
                item["template"],
                "```",
                "",
            ]
        )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote prompt inventory -> {OUT_MD}")
    print(f"wrote prompt inventory table -> {OUT_CSV}")


if __name__ == "__main__":
    main()
