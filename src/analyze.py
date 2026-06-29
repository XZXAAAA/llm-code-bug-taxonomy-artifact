"""Generate RQ1/RQ2 tables and figures.

Outputs:
  results/tables/pass_rates.csv
  results/tables/category_frequency.csv
  results/tables/category_by_model.csv
  results/tables/category_by_model_std_residuals.csv
  results/tables/chisq.txt
  results/tables/logic_binary_by_model.csv
  results/tables/logic_binary_chisq.txt
  results/figures/fig1_category_freq.png
  results/figures/fig2_category_by_model.png
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import chi2_contingency  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "processed" / "results.jsonl"
LABELED = ROOT / "data" / "processed" / "labeled.jsonl"
TAB = ROOT / "results" / "tables"
FIG = ROOT / "results" / "figures"

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


def independence_summary(p_value: float) -> str:
    if p_value < 0.05:
        return "reject independence at alpha=0.05"
    return "does not reject independence at alpha=0.05"


def short(model: str) -> str:
    return model.split("/")[-1]


def read_jsonl(path: Path) -> pd.DataFrame:
    return pd.DataFrame(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


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
    TAB.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    res = read_jsonl(RESULTS)
    lab = read_jsonl(LABELED)
    res["model"] = res["model"].map(short)
    lab["model"] = lab["model"].map(short)

    pass_rates = res.groupby("model")["passed"].agg(["sum", "count"]).rename(
        columns={"sum": "pass_count", "count": "n"}
    )
    pass_rates["pass_count"] = pass_rates["pass_count"].astype(int)
    pass_rates["pass_rate"] = (pass_rates["pass_count"] / pass_rates["n"] * 100).round(1)
    pass_ci = pass_rates.apply(
        lambda row: wilson_interval_pct(int(row["pass_count"]), int(row["n"])),
        axis=1,
        result_type="expand",
    )
    pass_rates["ci95_low"] = pass_ci[0]
    pass_rates["ci95_high"] = pass_ci[1]
    pass_rates = pass_rates[["pass_count", "n", "pass_rate", "ci95_low", "ci95_high"]]
    pass_rates.to_csv(TAB / "pass_rates.csv")
    print("== Pass rates ==\n", pass_rates, "\n")

    freq = lab["category"].value_counts().reindex(CAT_ORDER).dropna().astype(int)
    freq_df = freq.rename("count").to_frame()
    total_failures = int(freq_df["count"].sum())
    freq_df["pct"] = (freq_df["count"] / total_failures * 100).round(1)
    freq_ci = freq_df["count"].apply(lambda count: wilson_interval_pct(int(count), total_failures))
    freq_df["ci95_low"] = [item[0] for item in freq_ci]
    freq_df["ci95_high"] = [item[1] for item in freq_ci]
    freq_df.to_csv(TAB / "category_frequency.csv")
    print("== RQ1 category frequency ==\n", freq_df, "\n")

    category_by_model = (
        pd.crosstab(lab["category"], lab["model"])
        .reindex(CAT_ORDER)
        .dropna(how="all")
        .fillna(0)
        .astype(int)
    )
    category_by_model.to_csv(TAB / "category_by_model.csv")
    print("== RQ2 category x model ==\n", category_by_model, "\n")

    # Sparse categories make the chi-square test exploratory. We report both the
    # p-value and Cramer's V, plus standardized residuals for transparent auditing.
    ct_test = category_by_model.loc[category_by_model.sum(axis=1) > 0]
    chi2, p, dof, expected = chi2_contingency(ct_test.values)
    n = int(ct_test.values.sum())
    cramers_v = math.sqrt(chi2 / (n * min(ct_test.shape[0] - 1, ct_test.shape[1] - 1)))
    residuals = (ct_test - expected) / expected**0.5
    residuals.round(3).to_csv(TAB / "category_by_model_std_residuals.csv")
    low_expected = int((expected < 5).sum())
    chisq_text = (
        "Chi-square test of bug-category distribution across models\n"
        f"chi2 = {chi2:.3f}, dof = {dof}, p-value = {p:.4g}\n"
        f"Cramer's V = {cramers_v:.3f}\n"
        f"cells with expected count < 5 = {low_expected}/{expected.size}\n"
        f"=> {independence_summary(p)}\n"
        "Note: sparse categories make this an exploratory test; interpret with caution.\n"
    )
    (TAB / "chisq.txt").write_text(chisq_text, encoding="utf-8")
    print(chisq_text)

    logic_binary = pd.DataFrame(
        {
            "LOGIC": category_by_model.loc["LOGIC"],
            "non_LOGIC": category_by_model.drop(index="LOGIC").sum(axis=0),
        }
    ).T.astype(int)
    logic_binary.to_csv(TAB / "logic_binary_by_model.csv")
    binary_chi2, binary_p, binary_dof, binary_expected = chi2_contingency(logic_binary.values)
    binary_n = int(logic_binary.values.sum())
    binary_v = math.sqrt(
        binary_chi2 / (binary_n * min(logic_binary.shape[0] - 1, logic_binary.shape[1] - 1))
    )
    binary_low_expected = int((binary_expected < 5).sum())
    binary_text = (
        "Chi-square test of LOGIC vs non-LOGIC failures across models\n"
        f"chi2 = {binary_chi2:.3f}, dof = {binary_dof}, p-value = {binary_p:.4g}\n"
        f"Cramer's V = {binary_v:.3f}\n"
        f"cells with expected count < 5 = {binary_low_expected}/{binary_expected.size}\n"
        f"=> {independence_summary(binary_p)}\n"
        "Note: this two-class test is a lower-dimensional companion to the sparse full-category test.\n"
    )
    (TAB / "logic_binary_chisq.txt").write_text(binary_text, encoding="utf-8")
    print(binary_text)

    plt.figure(figsize=(8, 4.5))
    freq.plot(kind="bar", color="#4C72B0")
    plt.ylabel("Number of failures")
    plt.xlabel("Bug category")
    plt.title("RQ1: Distribution of bug types in LLM-generated code")
    plt.tight_layout()
    plt.savefig(FIG / "fig1_category_freq.png", dpi=150)
    plt.close()

    category_pct = category_by_model.div(category_by_model.sum(axis=0), axis=1) * 100
    category_pct.T.plot(kind="bar", stacked=True, figsize=(9, 5), colormap="tab20")
    plt.ylabel("% of failures")
    plt.xlabel("Model")
    plt.title("RQ2: Bug-type composition by model")
    plt.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "fig2_category_by_model.png", dpi=150)
    plt.close()

    print("figures saved -> results/figures/")


if __name__ == "__main__":
    main()
