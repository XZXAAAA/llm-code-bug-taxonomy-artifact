"""Permutation checks for RQ2 model-by-bug-type association tests.

The main paper reports chi-square tests for the full category-by-model table and
for the LOGIC/non-LOGIC companion table. Because the tables are sparse, this
script adds a deterministic permutation check that keeps each model's number of
failures fixed while shuffling bug labels across failed rows.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parents[1]
LABELED = ROOT / "data" / "processed" / "labeled.jsonl"
TAB = ROOT / "results" / "tables"

CAT_ORDER = [
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
]

N_PERMUTATIONS = 10_000
SEED = 20260624


def short(model: str) -> str:
    return model.split("/")[-1]


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_table(
    model_codes: list[int],
    label_codes: list[int],
    n_models: int,
    n_labels: int,
) -> list[list[int]]:
    table = [[0 for _ in range(n_models)] for _ in range(n_labels)]
    for model_code, label_code in zip(model_codes, label_codes, strict=True):
        table[label_code][model_code] += 1
    return [row for row in table if sum(row) > 0]


def chi_square_stat(table: list[list[int]]) -> float:
    return float(chi2_contingency(table)[0])


def permutation_p_value(
    model_codes: list[int],
    label_codes: list[int],
    n_models: int,
    n_labels: int,
) -> tuple[float, float]:
    observed = chi_square_stat(build_table(model_codes, label_codes, n_models, n_labels))
    rng = random.Random(SEED)
    exceed = 0
    shuffled = label_codes[:]
    for _ in range(N_PERMUTATIONS):
        rng.shuffle(shuffled)
        stat = chi_square_stat(build_table(model_codes, shuffled, n_models, n_labels))
        if stat >= observed - 1e-12:
            exceed += 1
    # Add-one smoothing avoids a zero p-value with finite simulations.
    p_value = (exceed + 1) / (N_PERMUTATIONS + 1)
    return observed, p_value


def main() -> None:
    TAB.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(LABELED)
    models = sorted({short(row["model"]) for row in rows})
    model_index = {model: i for i, model in enumerate(models)}
    category_index = {category: i for i, category in enumerate(CAT_ORDER)}
    binary_index = {"LOGIC": 0, "non_LOGIC": 1}

    model_codes = [model_index[short(row["model"])] for row in rows]
    category_codes = [category_index[row["category"]] for row in rows]
    binary_codes = [
        binary_index["LOGIC" if row["category"] == "LOGIC" else "non_LOGIC"]
        for row in rows
    ]

    full_observed, full_p = permutation_p_value(
        model_codes,
        category_codes,
        len(models),
        len(category_index),
    )
    binary_observed, binary_p = permutation_p_value(
        model_codes,
        binary_codes,
        len(models),
        len(binary_index),
    )

    text = (
        "Permutation checks for RQ2 model-by-bug-type association\n"
        f"seed = {SEED}\n"
        f"n_permutations = {N_PERMUTATIONS}\n"
        "\n"
        "Full category-by-model table\n"
        f"observed_chi2 = {full_observed:.3f}\n"
        f"permutation_p_value = {full_p:.4f}\n"
        "\n"
        "LOGIC/non-LOGIC by model table\n"
        f"observed_chi2 = {binary_observed:.3f}\n"
        f"permutation_p_value = {binary_p:.4f}\n"
        "\n"
        "Interpretation: permutation p-values are reported as robustness checks for sparse tables.\n"
    )
    (TAB / "permutation_tests.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
