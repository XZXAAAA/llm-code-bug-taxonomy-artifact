"""Run an independent blind LLM annotator for LOGIC subcategories.

This script is the publication-friendly robustness check for the subtype labels:
it asks a different model to label the same LOGIC failures without seeing the
reference solution, the original subtype label, or the original explanation.

Input:
  data/processed/labeled.jsonl
  data/raw/generations/*.jsonl
  data/raw/HumanEval.jsonl

Output:
  data/processed/logic_sublabeled_blind2.jsonl
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import load_env  # noqa: E402
from humaneval import load_problems  # noqa: E402
from label import load_generations  # noqa: E402
from sanitize import extract_code  # noqa: E402
from sublabel import SUBCATS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LABELED = ROOT / "data" / "processed" / "labeled.jsonl"
OUT = ROOT / "data" / "processed" / "logic_sublabeled_blind2.jsonl"

PROMPT = """You are an independent annotator for a research study on bugs in
AI-generated Python code. The code runs but returns a wrong result on hidden tests.

Choose exactly ONE root-cause subcategory code.

Subcategories:
- WRONG_ALGO: wrong overall algorithm/approach; a different method is needed.
- MISSING_EDGE: fails to handle a special input (empty, None, single element, all-equal).
- BOUNDARY: off-by-one, first/last, inclusive vs exclusive, index-range logic.
- STATE_UPDATE: incorrect accumulator/counter/loop-variable/in-place update.
- MATH_REASONING: wrong formula, operation, rounding, sign, or carry.
- PREMATURE_SIMPL: ignored a stated requirement / over-simplified the problem.
- SPEC_PARTIAL: only implemented some of the required cases/branches.

Do not assume a category from surface keywords. Infer the likely root cause from
the problem specification and the buggy code. You are not given any reference
solution or previous label.

Problem specification:
{spec}

Model's buggy code:
{code}

Reply with JSON: {{"subcategory": "<CODE>", "reason": "<short reason>"}}"""


def _config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def _client() -> tuple[OpenAI, str]:
    load_env()
    cfg = _config()
    provider = cfg["provider"]
    labeling = cfg.get("labeling", {})
    api_key_env = provider["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"Missing API key: set {api_key_env} in .env")

    model = os.getenv(
        "SECOND_LABELER_MODEL",
        labeling.get("second_labeler_default_model", "deepseek/deepseek-chat"),
    )
    return (
        OpenAI(
            base_url=provider["base_url"],
            api_key=api_key,
            timeout=60,
            max_retries=3,
        ),
        model,
    )


def _classify(client: OpenAI, model: str, spec: str, code: str) -> dict[str, str]:
    labeling = _config().get("labeling", {})
    temperature = labeling.get("second_labeler_temperature", 0)
    max_tokens = labeling.get("second_labeler_max_tokens", 180)

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT.format(spec=spec[:1800], code=code[:1800]),
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            choices = getattr(resp, "choices", None)
            content = choices[0].message.content if choices else None
            if not content or not content.strip():
                raise ValueError("empty response content")
            data = json.loads(content)
            subcategory = str(data.get("subcategory", "")).strip().upper()
            if subcategory not in SUBCATS:
                subcategory = "WRONG_ALGO"
            return {
                "subcategory": subcategory,
                "reason": str(data.get("reason", ""))[:500],
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2 * attempt)
    raise RuntimeError(f"second annotator failed: {last_error}")


def main() -> None:
    client, annotator_model = _client()
    problems = load_problems()
    generations = load_generations()
    rows = [
        json.loads(line)
        for line in LABELED.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    logic_rows = [row for row in rows if row["category"] == "LOGIC"]

    print(f"LOGIC failures to blind-label: {len(logic_rows)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Resume safely after transient provider failures by skipping rows already written.
    done: set[tuple[str, str]] = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["model"]))

    n_new = n_fail = 0
    with OUT.open("a", encoding="utf-8") as out:
        for row in logic_rows:
            task_id = row["task_id"]
            model = row["model"]
            if (task_id, model) in done:
                continue
            code = extract_code(generations.get((task_id, model, 0), ""))
            try:
                result = _classify(client, annotator_model, problems[task_id]["prompt"], code)
            except Exception as exc:  # noqa: BLE001
                # Skip persistent row-level failures; agreement is computed on the aligned subset.
                print(f"  skip {task_id} [{model}]: {str(exc)[:80]}")
                n_fail += 1
                continue
            out.write(
                json.dumps(
                    {
                        "task_id": task_id,
                        "model": model,
                        "subcategory": result["subcategory"],
                        "reason": result["reason"],
                        "annotator_model": annotator_model,
                        "blind": True,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            out.flush()
            n_new += 1

    print(f"wrote {n_new} new blind labels ({n_fail} skipped) -> {OUT}")


if __name__ == "__main__":
    main()
