"""Load the local HumanEval benchmark JSONL file."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUMANEVAL = ROOT / "data" / "raw" / "HumanEval.jsonl"


def load_problems() -> dict[str, dict]:
    """Return a mapping from task_id to HumanEval problem dictionary."""
    problems: dict[str, dict] = {}
    with HUMANEVAL.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            problem = json.loads(line)
            problems[problem["task_id"]] = problem
    return problems


if __name__ == "__main__":
    loaded = load_problems()
    print(f"loaded {len(loaded)} HumanEval problems")
    sample = loaded["HumanEval/0"]
    print("entry_point:", sample["entry_point"])
    print("prompt head:", sample["prompt"][:120].replace("\n", " "))
