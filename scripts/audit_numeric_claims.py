"""Check that manuscript and support-document numeric claims match result files."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT_TARGETS = {
    "paper/main.tex": ROOT / "paper" / "main.tex",
    "paper/software_impacts.tex": ROOT / "paper" / "software_impacts.tex",
    "README.md": ROOT / "README.md",
    "submission_materials/SUBMISSION_STATEMENTS.md": ROOT
    / "submission_materials"
    / "SUBMISSION_STATEMENTS.md",
}

STALE_PHRASE_TARGETS = {
    **TEXT_TARGETS,
    "results/tables/chisq.txt": ROOT / "results" / "tables" / "chisq.txt",
    "results/tables/logic_binary_chisq.txt": ROOT / "results" / "tables" / "logic_binary_chisq.txt",
}


def _rows_jsonl(rel: str) -> list[dict]:
    path = ROOT / rel
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _csv_by_key(rel: str, key: str) -> dict[str, dict[str, str]]:
    path = ROOT / rel
    with path.open(newline="", encoding="utf-8") as fh:
        return {row[key]: row for row in csv.DictReader(fh)}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _percent(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator * 100:.1f}"


def _require_contains(
    rel: str,
    text: str,
    snippet: str,
    failures: list[str],
) -> None:
    if _normalize_spaces(snippet) in _normalize_spaces(text):
        print(f"OK: {rel} contains {snippet}")
    else:
        failures.append(f"{rel} missing numeric claim: {snippet}")
        print(f"FAIL: {rel} missing numeric claim: {snippet}")


def _require_regex(
    rel: str,
    text: str,
    pattern: str,
    description: str,
    failures: list[str],
) -> None:
    if re.search(pattern, text, flags=re.DOTALL):
        print(f"OK: {rel} matches {description}")
    else:
        failures.append(f"{rel} missing numeric claim pattern: {description}")
        print(f"FAIL: {rel} missing numeric claim pattern: {description}")


def _claim_values() -> dict[str, str]:
    results = _rows_jsonl("data/processed/results.jsonl")
    labeled = _rows_jsonl("data/processed/labeled.jsonl")
    logic = _rows_jsonl("data/processed/logic_sublabeled.jsonl")
    blind = _rows_jsonl("data/processed/logic_sublabeled_blind2.jsonl")
    pass_rows = _csv_by_key("results/tables/pass_rates.csv", "model")
    categories = _csv_by_key("results/tables/category_frequency.csv", "category")
    subcats = _csv_by_key("results/tables/logic_subcategory.csv", "")

    total = len(results)
    passed = sum(1 for row in results if row.get("passed"))
    failed = total - passed
    logic_count = int(categories["LOGIC"]["count"])
    math_count = int(subcats["Math reasoning error"]["count"])
    wrong_algo_count = int(subcats["Wrong algorithm"]["count"])

    if len(labeled) != failed:
        raise AssertionError(f"labeled row count {len(labeled)} != failed count {failed}")
    if len(logic) != logic_count:
        raise AssertionError(f"logic subtype row count {len(logic)} != LOGIC count {logic_count}")
    if len(blind) != logic_count:
        raise AssertionError(f"blind second-label row count {len(blind)} != LOGIC count {logic_count}")

    agreement = _read("results/tables/auto_label_agreement.txt")
    exact_match = re.search(r"exact_agreement=(\d+)/(\d+) \(([\d.]+)%\)", agreement)
    kappa_match = re.search(r"cohens_kappa=([\d.]+) \(fair\)", agreement)
    if not exact_match or not kappa_match:
        raise AssertionError("agreement file missing exact agreement or kappa")

    chisq = _read("results/tables/chisq.txt")
    logic_chisq = _read("results/tables/logic_binary_chisq.txt")
    permutation_tests = _read("results/tables/permutation_tests.txt")
    permutation_values = re.findall(r"permutation_p_value = ([\d.]+)", permutation_tests)
    if len(permutation_values) != 2:
        raise AssertionError("permutation_tests.txt must contain exactly two permutation p-values")

    return {
        "total": str(total),
        "passed": str(passed),
        "failed": str(failed),
        "overall_pass_rate": _percent(passed, total),
        "logic_count": str(logic_count),
        "logic_pct": categories["LOGIC"]["pct"],
        "logic_ci_low": categories["LOGIC"]["ci95_low"],
        "logic_ci_high": categories["LOGIC"]["ci95_high"],
        "math_count": str(math_count),
        "math_pct": subcats["Math reasoning error"]["pct_of_logic"],
        "math_ci_low": subcats["Math reasoning error"]["ci95_low"],
        "math_ci_high": subcats["Math reasoning error"]["ci95_high"],
        "wrong_algo_count": str(wrong_algo_count),
        "wrong_algo_pct": subcats["Wrong algorithm"]["pct_of_logic"],
        "wrong_algo_ci_low": subcats["Wrong algorithm"]["ci95_low"],
        "wrong_algo_ci_high": subcats["Wrong algorithm"]["ci95_high"],
        "logic_top_two_count": str(math_count + wrong_algo_count),
        "logic_top_two_pct": _percent(math_count + wrong_algo_count, logic_count),
        "deepseek_pass": pass_rows["deepseek-chat"]["pass_rate"],
        "gpt_pass": pass_rows["gpt-4o-mini"]["pass_rate"],
        "qwen_pass": pass_rows["qwen-2.5-72b-instruct"]["pass_rate"],
        "llama_pass": pass_rows["llama-3.1-8b-instruct"]["pass_rate"],
        "rq2_chi2": re.search(r"chi2 = ([\d.]+)", chisq).group(1),
        "rq2_p": re.search(r"p-value = ([\d.]+)", chisq).group(1),
        "rq2_v": re.search(r"Cramer's V = ([\d.]+)", chisq).group(1),
        "rq2_sparse": re.search(r"cells with expected count < 5 = (\d+/\d+)", chisq).group(1),
        "binary_chi2": re.search(r"chi2 = ([\d.]+)", logic_chisq).group(1),
        "binary_p": re.search(r"p-value = ([\d.]+)", logic_chisq).group(1),
        "binary_v": re.search(r"Cramer's V = ([\d.]+)", logic_chisq).group(1),
        "binary_sparse": re.search(r"cells with expected count < 5 = (\d+/\d+)", logic_chisq).group(1),
        "rq2_permutation_p": permutation_values[0],
        "binary_permutation_p": permutation_values[1],
        "exact_num": exact_match.group(1),
        "exact_den": exact_match.group(2),
        "exact_pct": exact_match.group(3),
        "kappa": kappa_match.group(1),
    }


def audit_main_tex(values: dict[str, str], failures: list[str]) -> None:
    rel = "paper/main.tex"
    text = TEXT_TARGETS[rel].read_text(encoding="utf-8")
    claims = [
        f"{values['passed']} ({values['overall_pass_rate']}\\%) pass and {values['failed']} fail",
        (
            f"LOGIC failures account for {values['logic_pct']}\\% of failures: "
            "the generated code executes but"
        ),
        (
            f"({values['logic_count']}/{values['failed']}; 95\\% CI: "
            f"{values['logic_ci_low']}--{values['logic_ci_high']}\\%)"
        ),
        (
            f"mathematical-reasoning errors ({values['math_pct']}\\%, "
            f"{values['math_count']}/{values['logic_count']}; 95\\% CI: "
            f"{values['math_ci_low']}--{values['math_ci_high']}\\%)"
        ),
        (
            f"wrong-algorithm choices ({values['wrong_algo_pct']}\\%, "
            f"{values['wrong_algo_count']}/{values['logic_count']}; 95\\% CI: "
            f"{values['wrong_algo_ci_low']}--{values['wrong_algo_ci_high']}\\%)"
        ),
        f"{values['logic_top_two_count']}/{values['logic_count']} ({values['logic_top_two_pct']}\\%)",
        f"$\\chi^2={float(values['rq2_chi2']):.2f}$",
        f"$p={float(values['rq2_p']):.2f}$",
        f"$V={values['rq2_v']}$",
        values["rq2_sparse"] + " expected cells",
        f"$p={values['rq2_permutation_p']}$",
        f"$\\chi^2={values['binary_chi2']}$",
        f"$p={float(values['binary_p']):.3f}$",
        f"$V={values['binary_v']}$",
        values["binary_sparse"] + " expected cells",
        f"permutation p-value is {values['binary_permutation_p']}",
        f"{values['exact_num']}/{values['exact_den']} ({values['exact_pct']}\\%)",
        f"$\\kappa$ is {values['kappa']}",
    ]
    for claim in claims:
        _require_contains(rel, text, claim, failures)


def audit_readme(values: dict[str, str], failures: list[str]) -> None:
    rel = "README.md"
    text = TEXT_TARGETS[rel].read_text(encoding="utf-8")
    claims = [
        f"{values['total']} generations: 4 models x 164 HumanEval problems.",
        f"{values['passed']} pass, {values['failed']} fail",
        f"{values['logic_pct']}% of failures are wrong-output LOGIC errors",
        f"{values['math_pct']}%",
        f"{values['math_count']}/{values['logic_count']}",
        f"{values['wrong_algo_pct']}%",
        f"{values['wrong_algo_count']}/{values['logic_count']}",
        f"chi2 = {float(values['rq2_chi2']):.2f}",
        f"Cramer's V = {values['rq2_v']}",
        f"p = {values['rq2_permutation_p']}",
        f"chi2 = {values['binary_chi2']}",
        f"Cramer's V = {values['binary_v']}",
        f"permutation p = {values['binary_permutation_p']}",
        f"Cohen's kappa = {values['kappa']}",
        f"{values['exact_num']}/{values['exact_den']}, {values['exact_pct']}%",
    ]
    for claim in claims:
        _require_contains(rel, text, claim, failures)


def audit_software_impacts(values: dict[str, str], failures: list[str]) -> None:
    rel = "paper/software_impacts.tex"
    text = TEXT_TARGETS[rel].read_text(encoding="utf-8")
    claims = [
        f"{values['total']} HumanEval generations",
        f"{values['passed']} pass and {values['failed']} fail",
        f"{values['logic_pct']}\\% are wrong-output LOGIC errors",
        (
            f"{values['math_pct']}\\%, {values['math_count']}/{values['logic_count']}; "
            f"95\\% CI: {values['math_ci_low']}--{values['math_ci_high']}\\%"
        ),
        (
            f"{values['wrong_algo_pct']}\\%, {values['wrong_algo_count']}/{values['logic_count']}; "
            f"95\\% CI: {values['wrong_algo_ci_low']}--{values['wrong_algo_ci_high']}\\%"
        ),
        f"$\\chi^2={values['rq2_chi2']}$",
        f"$p={values['rq2_p']}$",
        f"$V={values['rq2_v']}$",
        f"$p={values['rq2_permutation_p']}$",
        f"$\\chi^2={values['binary_chi2']}$",
        f"$p={float(values['binary_p']):.3f}$",
        f"$V={values['binary_v']}$",
        f"permutation $p={values['binary_permutation_p']}$",
        f"{values['exact_num']}/{values['exact_den']} ({values['exact_pct']}\\%)",
        f"$\\kappa={values['kappa']}$",
    ]
    for claim in claims:
        _require_contains(rel, text, claim, failures)


def audit_submission_statements(values: dict[str, str], failures: list[str]) -> None:
    rel = "submission_materials/SUBMISSION_STATEMENTS.md"
    text = TEXT_TARGETS[rel].read_text(encoding="utf-8")
    _require_contains(
        rel,
        text,
        (
            f"{values['logic_pct']}% ({values['logic_count']}/{values['failed']}; "
            f"95% Wilson CI: {values['logic_ci_low']}-{values['logic_ci_high']}%)"
        ),
        failures,
    )


def audit_no_stale_numeric_phrases(failures: list[str]) -> None:
    stale_patterns = [
        r"silent LOGIC errors",
        r"silent logic errors",
        r"is not significant",
        r"not significant at alpha=0\.05",
        r"no significant cross-model difference",
    ]
    for rel, path in STALE_PHRASE_TARGETS.items():
        text = path.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            _require_regex(
                rel,
                text,
                rf"^(?!.*{pattern}).*$",
                f"absence of stale phrase /{pattern}/",
                failures,
            )


def main() -> None:
    failures: list[str] = []
    values = _claim_values()
    audit_main_tex(values, failures)
    audit_readme(values, failures)
    audit_software_impacts(values, failures)
    audit_submission_statements(values, failures)
    audit_no_stale_numeric_phrases(failures)

    if failures:
        print("\nNumeric claim audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("\nNumeric claim audit passed.")


if __name__ == "__main__":
    main()
