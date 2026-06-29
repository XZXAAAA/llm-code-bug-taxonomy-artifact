"""Compute label agreement for LOGIC subtype annotations.

Primary mode:
  Compare the original subtype labels with an independent blind second LLM
  annotator from data/processed/logic_sublabeled_blind2.jsonl.

Optional mode:
  If results/human_eval/review_sheet.csv has human labels filled in, also report
  Coder A vs Coder B and human-consensus vs LLM agreement.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
HE = ROOT / "results" / "human_eval"
OUT = ROOT / "results" / "tables" / "auto_label_agreement.txt"
CONFUSION_OUT = ROOT / "results" / "tables" / "auto_label_confusion.csv"
DISAGREE_OUT = ROOT / "results" / "tables" / "auto_label_disagreements.csv"


def cohens_kappa(a: list[str], b: list[str]) -> float:
    if len(a) != len(b):
        raise ValueError("Both label lists must have the same length")
    if not a:
        raise ValueError("Cannot compute kappa on an empty label list")

    labels = sorted(set(a) | set(b))
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = 0.0
    for label in labels:
        pe += (a.count(label) / n) * (b.count(label) / n)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def interpret(kappa: float) -> str:
    for threshold, name in [
        (0.81, "almost perfect"),
        (0.61, "substantial"),
        (0.41, "moderate"),
        (0.21, "fair"),
        (0.0, "slight"),
    ]:
        if kappa >= threshold:
            return name
    return "poor"


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_confusion(keys: list[tuple[str, str]], primary: dict, second: dict) -> None:
    labels = sorted(set(primary.values()) | set(second.values()))
    rows: dict[str, Counter[str]] = {label: Counter() for label in labels}
    for key in keys:
        rows[primary[key]][second[key]] += 1

    with CONFUSION_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["primary_label", *labels])
        for label in labels:
            writer.writerow([label, *[rows[label][other] for other in labels]])


def _write_disagreements(keys: list[tuple[str, str]], primary_rows: dict, second_rows: dict) -> int:
    disagreements = [
        (
            task_id,
            model,
            primary_rows[(task_id, model)]["subcategory"],
            second_rows[(task_id, model)]["subcategory"],
            primary_rows[(task_id, model)].get("reason", ""),
            second_rows[(task_id, model)].get("reason", ""),
        )
        for task_id, model in keys
        if primary_rows[(task_id, model)]["subcategory"]
        != second_rows[(task_id, model)]["subcategory"]
    ]

    with DISAGREE_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "task_id",
                "model",
                "primary_label",
                "blind_second_label",
                "primary_reason",
                "blind_second_reason",
            ]
        )
        writer.writerows(disagreements)
    return len(disagreements)


def automatic_agreement() -> str:
    primary_path = PROCESSED / "logic_sublabeled.jsonl"
    second_path = PROCESSED / "logic_sublabeled_blind2.jsonl"
    if not primary_path.exists():
        return "Automatic agreement skipped: data/processed/logic_sublabeled.jsonl not found."
    if not second_path.exists():
        return (
            "Automatic agreement skipped: run `python src/second_annotator.py` "
            "to create data/processed/logic_sublabeled_blind2.jsonl."
        )

    primary_rows = {
        (row["task_id"], row["model"]): row for row in _read_jsonl(primary_path)
    }
    second_rows = {
        (row["task_id"], row["model"]): row for row in _read_jsonl(second_path)
    }
    primary = {key: row["subcategory"] for key, row in primary_rows.items()}
    second = {key: row["subcategory"] for key, row in second_rows.items()}
    keys = sorted(primary.keys() & second.keys())
    missing = sorted(primary.keys() ^ second.keys())
    if len(keys) != len(primary):
        return (
            "Automatic agreement incomplete: "
            f"aligned {len(keys)}/{len(primary)} primary LOGIC subtype labels. "
            "Run `python src/second_annotator.py` to regenerate the complete blind "
            "second-annotator file before reporting kappa."
        )

    a = [primary[key] for key in keys]
    b = [second[key] for key in keys]
    kappa = cohens_kappa(a, b)
    exact = sum(1 for x, y in zip(a, b) if x == y)
    disagreement_count = _write_disagreements(keys, primary_rows, second_rows)
    _write_confusion(keys, primary, second)
    primary_counts = Counter(a)
    second_counts = Counter(b)

    lines = [
        "Independent LLM-vs-LLM LOGIC subtype agreement",
        f"n_aligned={len(keys)}",
        f"exact_agreement={exact}/{len(keys)} ({exact / len(keys):.1%})",
        f"cohens_kappa={kappa:.3f} ({interpret(kappa)})",
        f"disagreements={disagreement_count}",
        f"primary_distribution={dict(sorted(primary_counts.items()))}",
        f"blind_second_distribution={dict(sorted(second_counts.items()))}",
        f"confusion_matrix={CONFUSION_OUT.relative_to(ROOT)}",
        f"disagreement_file={DISAGREE_OUT.relative_to(ROOT)}",
    ]
    if missing:
        lines.append(f"unaligned_items={len(missing)}")
    return "\n".join(lines)


def optional_human_agreement() -> str | None:
    sheet_path = HE / "review_sheet.csv"
    key_path = HE / "review_key.csv"
    if not sheet_path.exists() or not key_path.exists():
        return None

    sheet = list(csv.DictReader(sheet_path.open(encoding="utf-8-sig")))
    if not sheet:
        return None

    coder_a = [row.get("label_coderA", "").strip().upper() for row in sheet]
    coder_b = [row.get("label_coderB", "").strip().upper() for row in sheet]
    if not all(coder_a) or not all(coder_b):
        return "Optional human agreement skipped: review_sheet.csv still has blank human labels."

    key = {
        row["id"]: row["llm_label"]
        for row in csv.DictReader(key_path.open(encoding="utf-8-sig"))
    }
    llm = [key[row["id"]] for row in sheet]
    kappa_ab = cohens_kappa(coder_a, coder_b)

    lines = [
        "",
        "Optional human-review agreement",
        f"Coder A vs Coder B: kappa={kappa_ab:.3f} ({interpret(kappa_ab)})",
    ]
    agreed = [(a, l) for a, b, l in zip(coder_a, coder_b, llm) if a == b]
    if agreed:
        human = [item[0] for item in agreed]
        llm_agreed = [item[1] for item in agreed]
        kappa_hl = cohens_kappa(human, llm_agreed)
        lines.append(
            "Human-consensus vs original LLM: "
            f"kappa={kappa_hl:.3f} ({interpret(kappa_hl)}), n={len(agreed)}"
        )
    return "\n".join(lines)


def main() -> None:
    reports = [automatic_agreement()]
    human_report = optional_human_agreement()
    if human_report:
        reports.append(human_report)
    text = "\n".join(reports) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
