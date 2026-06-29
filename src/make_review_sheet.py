"""06: 生成人工复核表，用于 Cohen's kappa 一致性验证。

为避免锚定偏差，复核表不含 LLM 标签；两位人工独立填写。
LLM 标签单独存到 review_key.csv，事后用 kappa.py 计算一致性。

产出:
  results/human_eval/review_sheet.csv   两位编码者填写（含题目、buggy代码、7类选项）
  results/human_eval/review_key.csv     LLM 标签（隐藏，事后比对）
  results/human_eval/CODING_GUIDE.md    子类定义
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humaneval import load_problems  # noqa: E402
from label import load_generations  # noqa: E402
from sanitize import extract_code  # noqa: E402
from sublabel import SUBCATS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "data" / "processed" / "logic_sublabeled.jsonl"
OUT = ROOT / "results" / "human_eval"
N_SAMPLE = 40
SEED = 42


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in SUB.read_text(encoding="utf-8").splitlines() if l.strip()]
    random.seed(SEED)
    sample = random.sample(rows, min(N_SAMPLE, len(rows)))

    problems = load_problems()
    gens = load_generations()

    # 编码指南
    guide = ["# Coding guide — LOGIC subtypes\n",
             "Read the problem and the buggy code; choose ONE subtype code.",
             "Do NOT look at review_key.csv until both coders are done.\n"]
    for code, desc in SUBCATS.items():
        guide.append(f"- **{code}**: {desc}")
    (OUT / "CODING_GUIDE.md").write_text("\n".join(guide), encoding="utf-8")

    # 复核表（无 LLM 标签）
    with (OUT / "review_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "task_id", "model", "problem_spec", "buggy_code",
                    "label_coderA", "label_coderB"])
        for i, r in enumerate(sample):
            p = problems[r["task_id"]]
            code = extract_code(gens.get((r["task_id"], r["model"], 0), ""))
            w.writerow([i, r["task_id"], r["model"].split("/")[-1],
                        p["prompt"].strip(), code.strip(), "", ""])

    # 答案键（LLM 标签，单独存）
    with (OUT / "review_key.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "llm_label"])
        for i, r in enumerate(sample):
            w.writerow([i, r["subcategory"]])

    print(f"wrote {len(sample)}-item review sheet -> {OUT}/review_sheet.csv")
    print("  fill label_coderA / label_coderB independently, then run src/kappa.py")


if __name__ == "__main__":
    main()
