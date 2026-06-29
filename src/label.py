"""Assign primary bug-category labels to failing generations.

Deterministic signals such as syntax errors, timeouts, and exception types are
mapped by rule. Assertion failures are classified with an LLM because the code
runs but returns a wrong result.

Input:
  data/processed/results.jsonl
  data/raw/generations/*.jsonl

Output:
  data/processed/labeled.jsonl
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
from sanitize import extract_code  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "processed" / "results.jsonl"
GEN_DIR = ROOT / "data" / "raw" / "generations"
OUT = ROOT / "data" / "processed" / "labeled.jsonl"

TAXONOMY = {
    "SYNTAX": "Code does not parse.",
    "API_MISUSE": "Nonexistent or misused API, name, attribute, or library.",
    "TYPE": "Type mismatch or wrong argument count/order.",
    "BOUNDARY": "Edge or special-input handling error.",
    "TIMEOUT": "Infinite loop or excessive runtime.",
    "LOGIC": "Algorithmic or logic error; runs but returns a wrong result.",
    "SPEC": "Misunderstood the problem statement.",
    "FORMAT": "Right idea but wrong return shape or output format.",
    "INCOMPLETE": "Stub, missing branch, or incomplete implementation.",
    "OTHER": "None of the above.",
}

EXC_MAP = {
    "NameError": "API_MISUSE",
    "AttributeError": "API_MISUSE",
    "ImportError": "API_MISUSE",
    "ModuleNotFoundError": "API_MISUSE",
    "TypeError": "TYPE",
    "IndexError": "BOUNDARY",
    "KeyError": "BOUNDARY",
    "ZeroDivisionError": "BOUNDARY",
    "StopIteration": "BOUNDARY",
    "ValueError": "BOUNDARY",
    "OverflowError": "BOUNDARY",
    "RecursionError": "TIMEOUT",
}

CLASSIFY_PROMPT = """You are labeling a bug in AI-generated Python code that RUNS but FAILS the unit tests (wrong output).
Pick exactly ONE category code that best describes the root cause.

Categories:
- LOGIC: algorithmic/logic error (wrong computation)
- BOUNDARY: fails only on edge/special inputs (empty, first/last, negatives)
- SPEC: misunderstood the problem; implemented something different
- FORMAT: right idea but wrong return shape/format/rounding
- INCOMPLETE: stub or missing branch (e.g., returns None / pass)
- OTHER: none of the above

Problem specification:
{spec}

Model's code:
{code}

Answer with a JSON object: {{"category": "<CODE>", "reason": "<short reason>"}}"""


def rule_label(status: str, error_type: str) -> str | None:
    if status == "syntax":
        return "SYNTAX"
    if status == "timeout":
        return "TIMEOUT"
    if status == "exception":
        return EXC_MAP.get(error_type, "OTHER")
    return None


def load_generations() -> dict[tuple[str, str, int], str]:
    generations = {}
    for path in GEN_DIR.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                generations[(row["task_id"], row["model"], row["sample"])] = row["raw_reply"]
    return generations


def main() -> None:
    load_env()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    provider = cfg["provider"]
    labeling = cfg.get("labeling", {})
    client = OpenAI(
        base_url=provider["base_url"],
        api_key=os.environ[provider["api_key_env"]],
    )
    labeler = labeling.get("primary_labeler_model", "openai/gpt-4o-mini")
    labeler_temperature = float(labeling.get("primary_labeler_temperature", 0))
    labeler_max_tokens = int(labeling.get("primary_labeler_max_tokens", 150))
    problems = load_problems()
    generations = load_generations()

    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    failures = [row for row in rows if not row["passed"]]
    print(f"failures to label: {len(failures)}")

    n_llm = 0
    with OUT.open("w", encoding="utf-8") as out:
        for row in failures:
            category = rule_label(row["status"], row["error_type"])
            method = "rule"
            reason = row.get("signal", "")
            if category is None:
                code = extract_code(generations.get((row["task_id"], row["model"], row["sample"]), ""))
                spec = problems[row["task_id"]]["prompt"]
                try:
                    response = client.chat.completions.create(
                        model=labeler,
                        messages=[
                            {
                                "role": "user",
                                "content": CLASSIFY_PROMPT.format(spec=spec[:1500], code=code[:1500]),
                            }
                        ],
                        temperature=labeler_temperature,
                        max_tokens=labeler_max_tokens,
                        response_format={"type": "json_object"},
                    )
                    data = json.loads(response.choices[0].message.content)
                    category = data.get("category", "OTHER")
                    reason = data.get("reason", "")
                    if category not in TAXONOMY:
                        category = "OTHER"
                    method = "llm"
                    n_llm += 1
                except Exception as exc:  # noqa: BLE001
                    category, method, reason = "OTHER", "llm_error", str(exc)[:80]
            out.write(
                json.dumps(
                    {
                        "task_id": row["task_id"],
                        "model": row["model"],
                        "category": category,
                        "method": method,
                        "error_type": row["error_type"],
                        "reason": reason,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"labeled {len(failures)} failures ({n_llm} via LLM) -> {OUT.name}")


if __name__ == "__main__":
    main()
