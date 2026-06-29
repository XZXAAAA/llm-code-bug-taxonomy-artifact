"""Prepare a deterministic human-review sample for LOGIC subtype validation.

The generated review sheet is intentionally blind: it contains the problem prompt
and generated code, but not the LLM-assigned subtype labels. Human labels can be
filled in later by two reviewers. `src/kappa.py` will detect the completed sheet
and report optional human agreement.
"""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sanitize import extract_code  # noqa: E402

SAMPLE_SIZE = 40
SEED = 20260624
LOGIC_LABELS = [
    "WRONG_ALGO",
    "MISSING_EDGE",
    "BOUNDARY",
    "STATE_UPDATE",
    "MATH_REASONING",
    "PREMATURE_SIMPL",
    "SPEC_PARTIAL",
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_generations() -> dict[tuple[str, str, int], str]:
    generations: dict[tuple[str, str, int], str] = {}
    for path in (ROOT / "data" / "raw" / "generations").glob("*.jsonl"):
        for row in read_jsonl(path):
            generations[(row["task_id"], row["model"], int(row.get("sample", 0)))] = row["raw_reply"]
    return generations


def allocate_sample_sizes(groups: dict[str, list[dict]], total: int) -> dict[str, int]:
    n_rows = sum(len(rows) for rows in groups.values())
    allocation = {
        label: max(1, round(len(rows) / n_rows * total))
        for label, rows in groups.items()
        if rows
    }
    while sum(allocation.values()) > total:
        candidates = [label for label, n in allocation.items() if n > 1]
        label = max(candidates, key=lambda item: (allocation[item], len(groups[item])))
        allocation[label] -= 1
    while sum(allocation.values()) < total:
        label = max(groups, key=lambda item: len(groups[item]) - allocation.get(item, 0))
        allocation[label] = allocation.get(label, 0) + 1
    return allocation


def main() -> None:
    rng = random.Random(SEED)
    problems = {row["task_id"]: row for row in read_jsonl(ROOT / "data" / "raw" / "HumanEval.jsonl")}
    generations = load_generations()
    primary_rows = read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled.jsonl")
    blind_rows = {
        (row["task_id"], row["model"]): row
        for row in read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled_blind2.jsonl")
    }

    groups: dict[str, list[dict]] = defaultdict(list)
    for row in primary_rows:
        groups[row["subcategory"]].append(row)

    allocation = allocate_sample_sizes(groups, SAMPLE_SIZE)
    selected: list[dict] = []
    for label in LOGIC_LABELS:
        rows = sorted(groups.get(label, []), key=lambda row: (row["task_id"], row["model"]))
        rng.shuffle(rows)
        selected.extend(rows[: allocation.get(label, 0)])
    selected = sorted(selected, key=lambda row: (row["subcategory"], row["task_id"], row["model"]))

    out_dir = ROOT / "results" / "human_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = out_dir / "review_sheet.csv"
    key_path = out_dir / "review_key.csv"
    protocol_path = out_dir / "README.md"

    sheet_fields = [
        "id",
        "task_id",
        "prompt",
        "generated_code",
        "label_coderA",
        "label_coderB",
        "notes_coderA",
        "notes_coderB",
    ]
    key_fields = [
        "id",
        "task_id",
        "model",
        "llm_label",
        "blind_second_label",
        "llm_reason",
        "blind_second_reason",
    ]

    with sheet_path.open("w", newline="", encoding="utf-8") as sheet_handle, key_path.open(
        "w", newline="", encoding="utf-8"
    ) as key_handle:
        sheet_writer = csv.DictWriter(sheet_handle, fieldnames=sheet_fields)
        key_writer = csv.DictWriter(key_handle, fieldnames=key_fields)
        sheet_writer.writeheader()
        key_writer.writeheader()
        for index, row in enumerate(selected, start=1):
            review_id = f"HR{index:03d}"
            task_id = row["task_id"]
            model = row["model"]
            raw_reply = generations[(task_id, model, 0)]
            second = blind_rows.get((task_id, model), {})
            sheet_writer.writerow(
                {
                    "id": review_id,
                    "task_id": task_id,
                    "prompt": problems[task_id]["prompt"].strip(),
                    "generated_code": extract_code(raw_reply).strip(),
                    "label_coderA": "",
                    "label_coderB": "",
                    "notes_coderA": "",
                    "notes_coderB": "",
                }
            )
            key_writer.writerow(
                {
                    "id": review_id,
                    "task_id": task_id,
                    "model": model,
                    "llm_label": row["subcategory"],
                    "blind_second_label": second.get("subcategory", ""),
                    "llm_reason": row.get("reason", ""),
                    "blind_second_reason": second.get("reason", ""),
                }
            )

    protocol_path.write_text(
        "\n".join(
            [
                "# Human Review Sample",
                "",
                "This folder contains a deterministic 40-item stratified sample of LOGIC failures for optional human validation.",
                "",
                "- `review_sheet.csv` is the blind sheet for two human reviewers.",
                "- `review_key.csv` stores the original LLM labels and must not be used during blind review.",
                "- Valid labels: " + ", ".join(LOGIC_LABELS) + ".",
                "- Fill `label_coderA` and `label_coderB` before running `python src/kappa.py` for optional human agreement.",
                "- Blank labels mean that no human-validation claim should be made.",
                "",
                f"Sampling seed: {SEED}.",
                f"Requested sample size: {SAMPLE_SIZE}.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(selected)} review items -> {sheet_path}")
    print(f"wrote review key -> {key_path}")


if __name__ == "__main__":
    main()
