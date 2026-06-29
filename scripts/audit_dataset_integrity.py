"""Audit dataset coverage and row-level consistency across generated artifacts."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def ok(message: str) -> None:
    print(f"OK: {message}")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def raw_generation_path(model: str) -> Path:
    return ROOT / "data" / "raw" / "generations" / f"{model.replace('/', '__')}.jsonl"


def key(row: dict) -> tuple[str, str, int]:
    return (row["task_id"], row["model"], int(row.get("sample", 0)))


def pair_key(row: dict) -> tuple[str, str]:
    return (row["task_id"], row["model"])


def audit_generation_matrix(failures: list[str]) -> tuple[set[str], set[str], set[tuple[str, str, int]]]:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    models = list(cfg["models"])
    problems = read_jsonl(ROOT / "data" / "raw" / "HumanEval.jsonl")
    task_ids = {row["task_id"] for row in problems}
    expected_keys = {(task_id, model, 0) for model in models for task_id in task_ids}

    if len(task_ids) == 164:
        ok("HumanEval input has 164 unique task IDs")
    else:
        fail(f"HumanEval input has {len(task_ids)} unique task IDs, expected 164", failures)
    if len(problems) == len(task_ids):
        ok("HumanEval task IDs are unique")
    else:
        fail("HumanEval contains duplicate task IDs", failures)

    raw_keys: set[tuple[str, str, int]] = set()
    for model in models:
        path = raw_generation_path(model)
        if not path.exists():
            fail(f"missing raw generation file for {model}: {path.relative_to(ROOT)}", failures)
            continue
        rows = read_jsonl(path)
        keys = [key(row) for row in rows]
        duplicate_keys = [item for item, count in Counter(keys).items() if count > 1]
        model_task_ids = {row["task_id"] for row in rows}
        samples = {int(row.get("sample", 0)) for row in rows}
        row_models = {row.get("model") for row in rows}
        if len(rows) == 164:
            ok(f"{path.relative_to(ROOT)} has 164 rows")
        else:
            fail(f"{path.relative_to(ROOT)} has {len(rows)} rows, expected 164", failures)
        if not duplicate_keys:
            ok(f"{path.relative_to(ROOT)} has no duplicate task/model/sample keys")
        else:
            fail(f"{path.relative_to(ROOT)} has duplicate keys: {duplicate_keys[:5]}", failures)
        if model_task_ids == task_ids:
            ok(f"{path.relative_to(ROOT)} covers all HumanEval task IDs")
        else:
            fail(
                f"{path.relative_to(ROOT)} task coverage mismatch: "
                f"missing={sorted(task_ids - model_task_ids)[:5]}, extra={sorted(model_task_ids - task_ids)[:5]}",
                failures,
            )
        if samples == {0}:
            ok(f"{path.relative_to(ROOT)} uses sample index 0 only")
        else:
            fail(f"{path.relative_to(ROOT)} has unexpected sample indexes: {sorted(samples)}", failures)
        if row_models == {model}:
            ok(f"{path.relative_to(ROOT)} model field matches config")
        else:
            fail(f"{path.relative_to(ROOT)} has unexpected model fields: {sorted(row_models)}", failures)
        raw_keys.update(keys)

    if raw_keys == expected_keys:
        ok("raw generations match the expected 4 x 164 x sample-0 matrix")
    else:
        fail(
            f"raw generation matrix mismatch: missing={len(expected_keys - raw_keys)}, "
            f"extra={len(raw_keys - expected_keys)}",
            failures,
        )

    return set(models), task_ids, expected_keys


def audit_results_and_labels(
    models: set[str],
    task_ids: set[str],
    expected_keys: set[tuple[str, str, int]],
    failures: list[str],
) -> None:
    results = read_jsonl(ROOT / "data" / "processed" / "results.jsonl")
    result_keys = [key(row) for row in results]
    duplicate_results = [item for item, count in Counter(result_keys).items() if count > 1]
    result_key_set = set(result_keys)
    if result_key_set == expected_keys:
        ok("results.jsonl matches the expected raw generation key matrix")
    else:
        fail(
            f"results.jsonl key mismatch: missing={len(expected_keys - result_key_set)}, "
            f"extra={len(result_key_set - expected_keys)}",
            failures,
        )
    if not duplicate_results:
        ok("results.jsonl has no duplicate task/model/sample keys")
    else:
        fail(f"results.jsonl has duplicate keys: {duplicate_results[:5]}", failures)

    failed_pairs = {pair_key(row) for row in results if not row.get("passed")}
    passed_pairs = {pair_key(row) for row in results if row.get("passed")}
    if failed_pairs.isdisjoint(passed_pairs):
        ok("each task/model pair has a single pass/fail status")
    else:
        fail("some task/model pairs are both pass and fail", failures)

    labels = read_jsonl(ROOT / "data" / "processed" / "labeled.jsonl")
    label_pairs = [pair_key(row) for row in labels]
    label_pair_set = set(label_pairs)
    duplicate_labels = [item for item, count in Counter(label_pairs).items() if count > 1]
    if label_pair_set == failed_pairs:
        ok("labeled.jsonl has exactly one label for each failed result")
    else:
        fail(
            f"labeled.jsonl mismatch: missing_failed={len(failed_pairs - label_pair_set)}, "
            f"extra_labels={len(label_pair_set - failed_pairs)}",
            failures,
        )
    if not duplicate_labels:
        ok("labeled.jsonl has no duplicate task/model labels")
    else:
        fail(f"labeled.jsonl has duplicate labels: {duplicate_labels[:5]}", failures)

    label_models = {row["model"] for row in labels}
    label_tasks = {row["task_id"] for row in labels}
    if label_models <= models and label_tasks <= task_ids:
        ok("labeled.jsonl model and task IDs are within the configured dataset")
    else:
        fail("labeled.jsonl contains model or task IDs outside the configured dataset", failures)

    logic_pairs = {pair_key(row) for row in labels if row.get("category") == "LOGIC"}
    sublabels = read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled.jsonl")
    sublabel_pairs = [pair_key(row) for row in sublabels]
    sublabel_pair_set = set(sublabel_pairs)
    duplicate_sublabels = [item for item, count in Counter(sublabel_pairs).items() if count > 1]
    if sublabel_pair_set == logic_pairs:
        ok("logic_sublabeled.jsonl covers exactly the primary LOGIC labels")
    else:
        fail(
            f"logic_sublabeled.jsonl mismatch: missing_logic={len(logic_pairs - sublabel_pair_set)}, "
            f"extra={len(sublabel_pair_set - logic_pairs)}",
            failures,
        )
    if not duplicate_sublabels:
        ok("logic_sublabeled.jsonl has no duplicate task/model rows")
    else:
        fail(f"logic_sublabeled.jsonl has duplicate rows: {duplicate_sublabels[:5]}", failures)

    blind = read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled_blind2.jsonl")
    blind_pairs = [pair_key(row) for row in blind]
    blind_pair_set = set(blind_pairs)
    duplicate_blind = [item for item, count in Counter(blind_pairs).items() if count > 1]
    if blind_pair_set == logic_pairs:
        ok("logic_sublabeled_blind2.jsonl covers exactly the primary LOGIC labels")
    else:
        fail(
            f"logic_sublabeled_blind2.jsonl mismatch: missing_logic={len(logic_pairs - blind_pair_set)}, "
            f"extra={len(blind_pair_set - logic_pairs)}",
            failures,
        )
    if not duplicate_blind:
        ok("logic_sublabeled_blind2.jsonl has no duplicate task/model rows")
    else:
        fail(f"logic_sublabeled_blind2.jsonl has duplicate rows: {duplicate_blind[:5]}", failures)


def audit_human_review_sample(failures: list[str]) -> None:
    logic_pairs = {
        pair_key(row)
        for row in read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled.jsonl")
    }
    sheet_path = ROOT / "results" / "human_eval" / "review_sheet.csv"
    key_path = ROOT / "results" / "human_eval" / "review_key.csv"
    with sheet_path.open(newline="", encoding="utf-8") as fh:
        sheet = list(csv.DictReader(fh))
    with key_path.open(newline="", encoding="utf-8") as fh:
        key_rows = list(csv.DictReader(fh))

    sheet_ids = [row["id"] for row in sheet]
    key_ids = [row["id"] for row in key_rows]
    if len(sheet) == 40 and len(key_rows) == 40:
        ok("human review sheet and key each have 40 rows")
    else:
        fail(f"human review row counts are sheet={len(sheet)}, key={len(key_rows)}, expected 40", failures)
    if len(sheet_ids) == len(set(sheet_ids)) and len(key_ids) == len(set(key_ids)):
        ok("human review sheet and key IDs are unique")
    else:
        fail("human review sheet or key contains duplicate IDs", failures)
    if set(sheet_ids) == set(key_ids):
        ok("human review sheet and key contain the same review IDs")
    else:
        fail("human review sheet and key ID sets differ", failures)

    sampled_pairs = {(row["task_id"], row["model"]) for row in key_rows}
    if sampled_pairs <= logic_pairs:
        ok("human review sample is a subset of LOGIC subtype rows")
    else:
        fail("human review key contains rows outside LOGIC subtype data", failures)

    blank_human_fields = all(
        not row.get("label_coderA", "").strip()
        and not row.get("label_coderB", "").strip()
        and not row.get("notes_coderA", "").strip()
        and not row.get("notes_coderB", "").strip()
        for row in sheet
    )
    if blank_human_fields:
        ok("human review sheet has blank human-label and note fields")
    else:
        fail("human review sheet has nonblank human-label or note fields", failures)


def audit_category_values(failures: list[str]) -> None:
    allowed_categories = {
        "LOGIC",
        "BOUNDARY",
        "SPEC",
        "FORMAT",
        "API_MISUSE",
        "TYPE",
        "INCOMPLETE",
        "TIMEOUT",
        "SYNTAX",
        "OTHER",
    }
    allowed_subcategories = {
        "WRONG_ALGO",
        "MISSING_EDGE",
        "BOUNDARY",
        "STATE_UPDATE",
        "MATH_REASONING",
        "PREMATURE_SIMPL",
        "SPEC_PARTIAL",
    }
    labels = read_jsonl(ROOT / "data" / "processed" / "labeled.jsonl")
    sublabels = read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled.jsonl")
    blind = read_jsonl(ROOT / "data" / "processed" / "logic_sublabeled_blind2.jsonl")
    categories = {row.get("category") for row in labels}
    subcats = {row.get("subcategory") for row in sublabels}
    blind_subcats = {row.get("subcategory") for row in blind}

    if categories <= allowed_categories:
        ok("primary labels use only configured bug categories")
    else:
        fail(f"unexpected primary categories: {sorted(categories - allowed_categories)}", failures)
    if subcats <= allowed_subcategories:
        ok("primary LOGIC subtype labels use only configured subcategories")
    else:
        fail(f"unexpected primary subcategories: {sorted(subcats - allowed_subcategories)}", failures)
    if blind_subcats <= allowed_subcategories:
        ok("blind second LOGIC subtype labels use only configured subcategories")
    else:
        fail(f"unexpected blind subcategories: {sorted(blind_subcats - allowed_subcategories)}", failures)


def main() -> None:
    failures: list[str] = []
    models, task_ids, expected_keys = audit_generation_matrix(failures)
    audit_results_and_labels(models, task_ids, expected_keys, failures)
    audit_category_values(failures)
    audit_human_review_sample(failures)

    if failures:
        print("\nDataset integrity audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("\nDataset integrity audit passed.")


if __name__ == "__main__":
    main()
