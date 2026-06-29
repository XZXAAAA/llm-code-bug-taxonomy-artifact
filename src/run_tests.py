"""Evaluate all generated programs with the HumanEval test harness.

Input:
  data/raw/generations/*.jsonl

Output:
  data/processed/results.jsonl

Each output row contains task_id, model, sample, passed, status, error_type,
and signal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import Result, evaluate_program  # noqa: E402
from humaneval import load_problems  # noqa: E402
from sanitize import build_program  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "data" / "raw" / "generations"
OUT = ROOT / "data" / "processed" / "results.jsonl"


def main() -> None:
    problems = load_problems()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = npass = 0
    with OUT.open("w", encoding="utf-8") as out:
        for gf in sorted(GEN_DIR.glob("*.jsonl")):
            for line in gf.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                g = json.loads(line)
                p = problems[g["task_id"]]
                program = build_program(p, g["raw_reply"])
                r: Result = evaluate_program(program, timeout=10)
                out.write(
                    json.dumps(
                        {
                            "task_id": g["task_id"],
                            "model": g["model"],
                            "sample": g["sample"],
                            "passed": r.passed,
                            "status": r.status,
                            "error_type": r.error_type,
                            "signal": r.signal,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n += 1
                npass += int(r.passed)
            print(f"  done {gf.name}")
    print(f"evaluated {n} generations, pass={npass} ({npass / max(n, 1) * 100:.1f}%) -> {OUT.name}")


if __name__ == "__main__":
    main()
