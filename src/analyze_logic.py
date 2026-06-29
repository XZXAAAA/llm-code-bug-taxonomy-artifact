"""Generate LOGIC subtype tables and figure.

Outputs:
  results/tables/logic_subcategory.csv
  results/tables/logic_subcat_by_model.csv
  results/figures/fig3_logic_subcat.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "data" / "processed" / "logic_sublabeled.jsonl"
TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"

ORDER = [
    "WRONG_ALGO",
    "MISSING_EDGE",
    "BOUNDARY",
    "STATE_UPDATE",
    "MATH_REASONING",
    "PREMATURE_SIMPL",
    "SPEC_PARTIAL",
]
LABELS = {
    "WRONG_ALGO": "Wrong algorithm",
    "MISSING_EDGE": "Missing edge case",
    "BOUNDARY": "Boundary condition",
    "STATE_UPDATE": "State/update error",
    "MATH_REASONING": "Math reasoning error",
    "PREMATURE_SIMPL": "Premature simplification",
    "SPEC_PARTIAL": "Spec partial impl.",
}


def short(model: str) -> str:
    return model.split("/")[-1]


def wilson_interval_pct(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, returned as percentages."""
    if total <= 0:
        raise ValueError("total must be positive")
    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    half_width = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return round((center - half_width) * 100, 1), round((center + half_width) * 100, 1)


def main() -> None:
    rows = [json.loads(line) for line in SUB.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    df["model"] = df["model"].map(short)

    freq = df["subcategory"].value_counts().reindex(ORDER).fillna(0).astype(int)
    fd = freq.rename("count").to_frame()
    total_logic = int(fd["count"].sum())
    fd["pct_of_logic"] = (fd["count"] / total_logic * 100).round(1)
    freq_ci = fd["count"].apply(lambda count: wilson_interval_pct(int(count), total_logic))
    fd["ci95_low"] = [item[0] for item in freq_ci]
    fd["ci95_high"] = [item[1] for item in freq_ci]
    fd.index = [LABELS[i] for i in fd.index]
    fd.to_csv(TAB / "logic_subcategory.csv")
    print("== LOGIC subcategory frequency ==\n", fd, "\n")

    ct = pd.crosstab(df["subcategory"], df["model"]).reindex(ORDER).fillna(0).astype(int)
    ct.index = [LABELS[i] for i in ct.index]
    ct.to_csv(TAB / "logic_subcat_by_model.csv")
    print("== subcategory x model ==\n", ct, "\n")

    plt.figure(figsize=(8.5, 4.5))
    freq.index = [LABELS[i] for i in freq.index]
    freq.plot(kind="barh", color="#C44E52")
    plt.gca().invert_yaxis()
    plt.xlabel("Number of logic failures")
    plt.title("Refined taxonomy: subtypes of LOGIC errors (n=96)")
    plt.tight_layout()
    plt.savefig(FIG / "fig3_logic_subcat.png", dpi=150)
    plt.close()
    print("figure saved -> results/figures/fig3_logic_subcat.png")


if __name__ == "__main__":
    main()
