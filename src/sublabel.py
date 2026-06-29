"""Refine primary LOGIC failures into seven root-cause subcategories.

Input:
  data/processed/labeled.jsonl
  data/raw/generations/*.jsonl
  data/raw/HumanEval.jsonl

Output:
  data/processed/logic_sublabeled.jsonl

Each output row contains task_id, model, subcategory, and reason.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import load_env  # noqa: E402
from humaneval import load_problems  # noqa: E402
from label import load_generations  # noqa: E402
from sanitize import extract_code  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LABELED = ROOT / "data" / "processed" / "labeled.jsonl"
OUT = ROOT / "data" / "processed" / "logic_sublabeled.jsonl"

SUBCATS = {
    "WRONG_ALGO": "Wrong overall algorithm/approach; a different method is needed.",
    "MISSING_EDGE": "Fails to handle a special input (empty, None, single element, all-equal).",
    "BOUNDARY": "Boundary condition error (off-by-one, first/last, inclusive vs exclusive, index logic).",
    "STATE_UPDATE": "Incorrect state/update (accumulator, counter, loop variable, in-place mutation).",
    "MATH_REASONING": "Mathematical reasoning error (wrong formula, operation, rounding, sign, carry).",
    "PREMATURE_SIMPL": "Premature simplification; ignored a stated requirement / over-simplified.",
    "SPEC_PARTIAL": "Partial implementation of the spec; only some required cases/branches handled.",
}

PROMPT = """You are categorizing the ROOT CAUSE of a logic bug in AI-generated Python code.
The code runs but returns a WRONG result on the hidden tests.
Choose exactly ONE subcategory code.

Subcategories:
- WRONG_ALGO: wrong overall algorithm/approach; a different method is needed.
- MISSING_EDGE: fails to handle a special input (empty, None, single element, all-equal).
- BOUNDARY: off-by-one, first/last, inclusive vs exclusive, index-range logic.
- STATE_UPDATE: incorrect accumulator/counter/loop-variable/in-place update.
- MATH_REASONING: wrong formula, operation, rounding, sign, or carry.
- PREMATURE_SIMPL: ignored a stated requirement / over-simplified the problem.
- SPEC_PARTIAL: only implemented some of the required cases/branches.

Problem specification:
{spec}

Reference correct solution (for comparison only):
{ref}

Model's buggy code:
{code}

Reply with JSON: {{"subcategory": "<CODE>", "reason": "<short reason>"}}"""


def main() -> None:
    load_env()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    provider = cfg["provider"]
    labeling = cfg.get("labeling", {})
    client = OpenAI(
        base_url=provider["base_url"],
        api_key=os.environ[provider["api_key_env"]],
        timeout=60,
        max_retries=3,
    )
    labeler = labeling.get("logic_subtype_labeler_model", "openai/gpt-4o-mini")
    labeler_temperature = float(labeling.get("logic_subtype_labeler_temperature", 0))
    labeler_max_tokens = int(labeling.get("logic_subtype_labeler_max_tokens", 160))

    problems = load_problems()
    generations = load_generations()
    labels = [
        json.loads(line)
        for line in LABELED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    logic_rows = [row for row in labels if row["category"] == "LOGIC"]
    print(f"LOGIC failures to sub-label: {len(logic_rows)}")

    n = 0
    with OUT.open("w", encoding="utf-8") as out:
        for row in logic_rows:
            problem = problems[row["task_id"]]
            code = extract_code(generations.get((row["task_id"], row["model"], 0), ""))
            try:
                response = client.chat.completions.create(
                    model=labeler,
                    messages=[
                        {
                            "role": "user",
                            "content": PROMPT.format(
                                spec=problem["prompt"][:1400],
                                ref=problem["canonical_solution"][:600],
                                code=code[:1400],
                            ),
                        }
                    ],
                    temperature=labeler_temperature,
                    max_tokens=labeler_max_tokens,
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                subcategory = data.get("subcategory", "WRONG_ALGO")
                if subcategory not in SUBCATS:
                    subcategory = "WRONG_ALGO"
                reason = data.get("reason", "")
            except Exception as exc:  # noqa: BLE001
                subcategory = "WRONG_ALGO"
                reason = f"(labeler error: {str(exc)[:60]})"
            out.write(
                json.dumps(
                    {
                        "task_id": row["task_id"],
                        "model": row["model"],
                        "subcategory": subcategory,
                        "reason": reason,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            n += 1
    print(f"sub-labeled {n} LOGIC failures -> {OUT.name}")


if __name__ == "__main__":
    main()
