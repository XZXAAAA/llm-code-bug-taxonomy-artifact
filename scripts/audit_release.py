"""Audit repository state before paper/software release.

This is a lightweight consistency check, not a full reproduction run. It verifies
that key artifacts exist, row counts match the claims in the manuscript, agreement
outputs are complete, arXiv packaging has local figure paths, and tracked text files
do not contain obvious secret-looking API keys.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "REPRODUCIBILITY.md",
    "PROTOCOL.md",
    ".github/workflows/release-audit.yml",
    "LICENSE",
    "CITATION.cff",
    "requirements.txt",
    "paper/main.tex",
    "paper/software_impacts.tex",
    "paper/references.bib",
    "src/generate.py",
    "src/run_tests.py",
    "src/label.py",
    "src/sublabel.py",
    "src/second_annotator.py",
    "src/permutation_tests.py",
    "src/kappa.py",
    "scripts/prepare_arxiv_package.py",
    "scripts/prepare_release_bundle.py",
    "scripts/fill_release_links.py",
    "scripts/test_fill_release_links.py",
    "scripts/compile_manuscripts.py",
    "scripts/run_fast_verification.py",
    "scripts/generate_model_metadata.py",
    "scripts/generate_prompt_inventory.py",
    "scripts/audit_dataset_integrity.py",
    "scripts/audit_numeric_claims.py",
    "scripts/audit_text_cleanliness.py",
    "scripts/audit_metadata.py",
    "scripts/generate_artifact_manifest.py",
    "scripts/audit_submission_ready.py",
    "scripts/prepare_human_review_sample.py",
    "submission_materials/SOFTWARE_METADATA.md",
    "submission_materials/DATA_DICTIONARY.md",
    "submission_materials/SUBMISSION_STATEMENTS.md",
    "submission_materials/RELEASE_CHECKLIST.md",
    "submission_materials/PDF_BUILD_GUIDE.md",
    "submission_materials/PROMPT_INVENTORY.md",
    "results/human_eval/CODING_GUIDE.md",
    "results/human_eval/README.md",
    "results/human_eval/review_sheet.csv",
    "results/human_eval/review_key.csv",
]

TEXT_EXTENSIONS = {
    ".bib",
    ".cff",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".tex",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"sk-or-[A-Za-z0-9_-]{16,}"),
]

OVERCLAIM_PHRASES = [
    "central finding",
    "silent logic errors dominate",
    "logic dominates",
    "fail overwhelmingly",
    "reviewing has shifted",
    "the bottleneck is",
    "bigger models fail",
    "end-to-end reproducible",
    "transparent empirical",
    "state-of-the-art",
    "breakthrough",
    "game-changing",
    "seamless",
    "powerful",
    "perfect",
    "victory lap",
    "honest and publishable",
]

SUPPORTING_DOCS = [
    "README.md",
    "PROTOCOL.md",
    "REPRODUCIBILITY.md",
    "submission_materials/SOFTWARE_METADATA.md",
    "submission_materials/SUBMISSION_STATEMENTS.md",
    "submission_materials/SOFTWARE_IMPACTS_OUTLINE.md",
    "submission_materials/PDF_BUILD_GUIDE.md",
    "submission_materials/DATA_DICTIONARY.md",
    "submission_materials/RELEASE_CHECKLIST.md",
]


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def audit_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if path.exists():
            ok(f"found {rel}")
        else:
            fail(f"missing {rel}", failures)


def audit_counts(failures: list[str]) -> None:
    expected = {
        "data/processed/results.jsonl": 656,
        "data/processed/labeled.jsonl": 110,
        "data/processed/logic_sublabeled.jsonl": 96,
        "data/processed/logic_sublabeled_blind2.jsonl": 96,
    }
    for rel, n_expected in expected.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"missing {rel}", failures)
            continue
        n_actual = count_jsonl(path)
        if n_actual == n_expected:
            ok(f"{rel} has {n_actual} rows")
        else:
            fail(f"{rel} has {n_actual} rows, expected {n_expected}", failures)

    results_path = ROOT / "data/processed/results.jsonl"
    if results_path.exists():
        rows = [
            json.loads(line)
            for line in results_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        passed = sum(1 for row in rows if row.get("passed"))
        failed = len(rows) - passed
        if passed == 546 and failed == 110:
            ok("pass/fail counts match README: 546 pass, 110 fail")
        else:
            fail(f"pass/fail counts are {passed}/{failed}, expected 546/110", failures)


def audit_agreement(failures: list[str]) -> None:
    path = ROOT / "results/tables/auto_label_agreement.txt"
    if not path.exists():
        fail("missing results/tables/auto_label_agreement.txt", failures)
        return
    text = path.read_text(encoding="utf-8")
    required = [
        "n_aligned=96",
        "exact_agreement=42/96 (43.8%)",
        "cohens_kappa=0.305 (fair)",
    ]
    for item in required:
        if item in text:
            ok(f"agreement contains {item}")
        else:
            fail(f"agreement missing {item}", failures)


def audit_rq2_statistics(failures: list[str]) -> None:
    chisq = ROOT / "results/tables/chisq.txt"
    residuals = ROOT / "results/tables/category_by_model_std_residuals.csv"
    binary_chisq = ROOT / "results/tables/logic_binary_chisq.txt"
    binary_table = ROOT / "results/tables/logic_binary_by_model.csv"
    permutation_tests = ROOT / "results/tables/permutation_tests.txt"
    if not chisq.exists():
        fail("missing results/tables/chisq.txt", failures)
        return
    text = chisq.read_text(encoding="utf-8")
    for item in [
        "chi2 = 21.290",
        "p-value = 0.265",
        "Cramer's V = 0.254",
        "cells with expected count < 5 = 24/28",
        "=> does not reject independence at alpha=0.05",
    ]:
        if item in text:
            ok(f"chisq.txt contains {item}")
        else:
            fail(f"chisq.txt missing {item}", failures)
    if residuals.exists():
        ok("found category_by_model_std_residuals.csv")
    else:
        fail("missing category_by_model_std_residuals.csv", failures)
    if binary_table.exists():
        ok("found logic_binary_by_model.csv")
    else:
        fail("missing logic_binary_by_model.csv", failures)
    if not binary_chisq.exists():
        fail("missing results/tables/logic_binary_chisq.txt", failures)
        return
    binary_text = binary_chisq.read_text(encoding="utf-8")
    for item in [
        "chi2 = 3.394",
        "p-value = 0.3347",
        "Cramer's V = 0.176",
        "cells with expected count < 5 = 3/8",
        "=> does not reject independence at alpha=0.05",
    ]:
        if item in binary_text:
            ok(f"logic_binary_chisq.txt contains {item}")
        else:
            fail(f"logic_binary_chisq.txt missing {item}", failures)
    if not permutation_tests.exists():
        fail("missing results/tables/permutation_tests.txt", failures)
        return
    permutation_text = permutation_tests.read_text(encoding="utf-8")
    for item in [
        "seed = 20260624",
        "n_permutations = 10000",
        "observed_chi2 = 21.290",
        "permutation_p_value = 0.2691",
        "observed_chi2 = 3.394",
        "permutation_p_value = 0.3445",
    ]:
        if item in permutation_text:
            ok(f"permutation_tests.txt contains {item}")
        else:
            fail(f"permutation_tests.txt missing {item}", failures)


def audit_interval_tables(failures: list[str]) -> None:
    expected_values = {
        "results/tables/pass_rates.csv": [
            ("deepseek-chat", "pass_rate", "93.3"),
            ("deepseek-chat", "ci95_low", "88.4"),
            ("deepseek-chat", "ci95_high", "96.2"),
            ("llama-3.1-8b-instruct", "pass_rate", "65.2"),
            ("llama-3.1-8b-instruct", "ci95_low", "57.7"),
            ("llama-3.1-8b-instruct", "ci95_high", "72.1"),
        ],
        "results/tables/category_frequency.csv": [
            ("LOGIC", "pct", "87.3"),
            ("LOGIC", "ci95_low", "79.8"),
            ("LOGIC", "ci95_high", "92.3"),
        ],
        "results/tables/logic_subcategory.csv": [
            ("Math reasoning error", "pct_of_logic", "44.8"),
            ("Math reasoning error", "ci95_low", "35.2"),
            ("Math reasoning error", "ci95_high", "54.7"),
            ("Wrong algorithm", "pct_of_logic", "21.9"),
            ("Wrong algorithm", "ci95_low", "14.8"),
            ("Wrong algorithm", "ci95_high", "31.1"),
        ],
    }
    for rel, checks in expected_values.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"missing {rel}", failures)
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        index_field = "" if "" in (rows[0].keys() if rows else []) else rows[0].keys().__iter__().__next__()
        by_name = {row[index_field]: row for row in rows}
        for row_name, column, expected in checks:
            actual = by_name.get(row_name, {}).get(column)
            if actual == expected:
                ok(f"{rel} has {row_name} {column}={expected}")
            else:
                fail(f"{rel} has {row_name} {column}={actual}, expected {expected}", failures)


def audit_model_metadata(failures: list[str]) -> None:
    path = ROOT / "results" / "tables" / "model_metadata.csv"
    if not path.exists():
        fail("missing results/tables/model_metadata.csv", failures)
        return

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_role_model = {(row["role"], row["model_id"]): row for row in rows}

    expected_generation_models = {
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
    }
    actual_generation_models = {
        row["model_id"] for row in rows if row.get("role") == "generation"
    }
    if actual_generation_models == expected_generation_models:
        ok("model_metadata.csv contains all generation models")
    else:
        fail(
            "model_metadata.csv generation models are "
            f"{sorted(actual_generation_models)}, expected {sorted(expected_generation_models)}",
            failures,
        )

    for model_id in expected_generation_models:
        row = by_role_model.get(("generation", model_id), {})
        checks = {
            "provider_name": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "access_date": "2026-06-23",
            "benchmark": "HumanEval",
            "samples_per_problem": "1",
            "temperature": "0.2",
            "max_tokens": "1024",
        }
        for column, expected in checks.items():
            actual = row.get(column)
            if actual == expected:
                ok(f"model_metadata.csv has {model_id} {column}={expected}")
            else:
                fail(
                    f"model_metadata.csv has {model_id} {column}={actual}, expected {expected}",
                    failures,
                )

    labeler_checks = [
        (
            "primary_failure_labeler",
            "openai/gpt-4o-mini",
            {"temperature": "0", "max_tokens": "150"},
        ),
        (
            "primary_logic_subtype_labeler",
            "openai/gpt-4o-mini",
            {"temperature": "0", "max_tokens": "160"},
        ),
        (
            "blind_second_subtype_labeler_default",
            "deepseek/deepseek-chat",
            {"temperature": "0", "max_tokens": "180"},
        ),
    ]
    for role, model_id, checks in labeler_checks:
        row = by_role_model.get((role, model_id), {})
        if row:
            ok(f"model_metadata.csv contains {role} {model_id}")
        else:
            fail(f"model_metadata.csv missing {role} {model_id}", failures)
            continue
        for column, expected in checks.items():
            actual = row.get(column)
            if actual == expected:
                ok(f"model_metadata.csv has {role} {column}={expected}")
            else:
                fail(
                    f"model_metadata.csv has {role} {column}={actual}, expected {expected}",
                    failures,
                )


def audit_prompt_inventory(failures: list[str]) -> None:
    csv_path = ROOT / "results" / "tables" / "prompt_inventory.csv"
    md_path = ROOT / "submission_materials" / "PROMPT_INVENTORY.md"
    if not csv_path.exists():
        fail("missing results/tables/prompt_inventory.csv", failures)
        return
    if not md_path.exists():
        fail("missing submission_materials/PROMPT_INVENTORY.md", failures)
        return

    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    expected_ids = {
        "generation_prompt",
        "primary_failure_label_prompt",
        "primary_logic_subtype_prompt",
        "blind_second_logic_subtype_prompt",
    }
    actual_ids = {row.get("id", "") for row in rows}
    if actual_ids == expected_ids:
        ok("prompt_inventory.csv contains all expected prompt IDs")
    else:
        fail(f"prompt_inventory.csv IDs are {sorted(actual_ids)}, expected {sorted(expected_ids)}", failures)

    md_text = md_path.read_text(encoding="utf-8")
    for row in rows:
        prompt_id = row.get("id", "")
        digest = row.get("sha256", "")
        if prompt_id in md_text and digest in md_text:
            ok(f"PROMPT_INVENTORY.md contains {prompt_id} and its hash")
        else:
            fail(f"PROMPT_INVENTORY.md missing {prompt_id} or its hash", failures)
        if len(digest) == 64:
            ok(f"prompt_inventory.csv has 64-character hash for {prompt_id}")
        else:
            fail(f"prompt_inventory.csv has invalid hash for {prompt_id}: {digest}", failures)


def audit_human_review_instrument(failures: list[str]) -> None:
    sheet_path = ROOT / "results" / "human_eval" / "review_sheet.csv"
    key_path = ROOT / "results" / "human_eval" / "review_key.csv"
    guide_path = ROOT / "results" / "human_eval" / "CODING_GUIDE.md"
    readme_path = ROOT / "results" / "human_eval" / "README.md"
    for path in [sheet_path, key_path, guide_path, readme_path]:
        if path.exists():
            ok(f"found {path.relative_to(ROOT)}")
        else:
            fail(f"missing {path.relative_to(ROOT)}", failures)
            return

    with sheet_path.open(newline="", encoding="utf-8") as fh:
        sheet_rows = list(csv.DictReader(fh))
    with key_path.open(newline="", encoding="utf-8") as fh:
        key_rows = list(csv.DictReader(fh))
    if len(sheet_rows) == 40:
        ok("human review sheet has 40 rows")
    else:
        fail(f"human review sheet has {len(sheet_rows)} rows, expected 40", failures)
    if len(key_rows) == 40:
        ok("human review key has 40 rows")
    else:
        fail(f"human review key has {len(key_rows)} rows, expected 40", failures)

    blank_labels = all(
        not row.get("label_coderA", "").strip() and not row.get("label_coderB", "").strip()
        for row in sheet_rows
    )
    if blank_labels:
        ok("human review sheet label fields are blank; no human-validation claim is implied")
    else:
        fail("human review sheet contains filled human labels; update paper claims and agreement outputs", failures)

    valid_labels = {
        "WRONG_ALGO",
        "MISSING_EDGE",
        "BOUNDARY",
        "STATE_UPDATE",
        "MATH_REASONING",
        "PREMATURE_SIMPL",
        "SPEC_PARTIAL",
    }
    key_labels = {row.get("llm_label", "") for row in key_rows}
    if key_labels <= valid_labels:
        ok("human review key uses only configured LOGIC subtype labels")
    else:
        fail(f"human review key has unexpected labels: {sorted(key_labels - valid_labels)}", failures)


def audit_artifact_manifest(failures: list[str]) -> None:
    manifest = ROOT / "results/tables/artifact_manifest.csv"
    if not manifest.exists():
        fail("missing results/tables/artifact_manifest.csv", failures)
        return
    text = manifest.read_text(encoding="utf-8")
    required_paths = [
        "paper/main.tex",
        "paper/software_impacts.tex",
        "data/processed/results.jsonl",
        "data/processed/labeled.jsonl",
        "data/raw/HumanEval.jsonl",
        "data/raw/generations/deepseek__deepseek-chat.jsonl",
        "data/processed/logic_sublabeled.jsonl",
        "data/processed/logic_sublabeled_blind2.jsonl",
        "results/tables/chisq.txt",
        "results/tables/logic_binary_chisq.txt",
        "results/tables/logic_binary_by_model.csv",
        "results/tables/permutation_tests.txt",
        "results/tables/model_metadata.csv",
        "results/tables/prompt_inventory.csv",
        "results/tables/auto_label_agreement.txt",
        "results/human_eval/review_sheet.csv",
        "results/human_eval/review_key.csv",
        "results/human_eval/CODING_GUIDE.md",
        "scripts/run_fast_verification.py",
        "scripts/generate_prompt_inventory.py",
        "scripts/audit_dataset_integrity.py",
        "scripts/audit_numeric_claims.py",
        "scripts/audit_text_cleanliness.py",
        "scripts/audit_metadata.py",
        "scripts/test_fill_release_links.py",
        "REPRODUCIBILITY.md",
        ".github/workflows/release-audit.yml",
        "submission_materials/DATA_DICTIONARY.md",
        "submission_materials/SUBMISSION_STATEMENTS.md",
        "submission_materials/PDF_BUILD_GUIDE.md",
        "submission_materials/PROMPT_INVENTORY.md",
    ]
    for rel in required_paths:
        if rel in text:
            ok(f"artifact manifest includes {rel}")
        else:
            fail(f"artifact manifest missing {rel}", failures)


def audit_requirements(failures: list[str]) -> None:
    path = ROOT / "requirements.txt"
    if not path.exists():
        fail("missing requirements.txt", failures)
        return
    text = path.read_text(encoding="utf-8").lower()
    required_packages = ["pandas", "matplotlib", "scipy", "pyyaml", "openai"]
    for package in required_packages:
        if package in text:
            ok(f"requirements.txt includes {package}")
        else:
            fail(f"requirements.txt missing {package}", failures)


def audit_numeric_claims_script(failures: list[str]) -> None:
    script = ROOT / "scripts" / "audit_numeric_claims.py"
    if not script.exists():
        fail("missing scripts/audit_numeric_claims.py", failures)
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ok("scripts/audit_numeric_claims.py passes")
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        fail("scripts/audit_numeric_claims.py failed", failures)


def audit_text_cleanliness_script(failures: list[str]) -> None:
    script = ROOT / "scripts" / "audit_text_cleanliness.py"
    if not script.exists():
        fail("missing scripts/audit_text_cleanliness.py", failures)
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ok("scripts/audit_text_cleanliness.py passes")
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        fail("scripts/audit_text_cleanliness.py failed", failures)


def audit_metadata_script(failures: list[str]) -> None:
    script = ROOT / "scripts" / "audit_metadata.py"
    if not script.exists():
        fail("missing scripts/audit_metadata.py", failures)
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ok("scripts/audit_metadata.py passes")
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        fail("scripts/audit_metadata.py failed", failures)


def audit_release_link_fill_script(failures: list[str]) -> None:
    script = ROOT / "scripts" / "test_fill_release_links.py"
    if not script.exists():
        fail("missing scripts/test_fill_release_links.py", failures)
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ok("scripts/test_fill_release_links.py passes")
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        fail("scripts/test_fill_release_links.py failed", failures)


def audit_dataset_integrity_script(failures: list[str]) -> None:
    script = ROOT / "scripts" / "audit_dataset_integrity.py"
    if not script.exists():
        fail("missing scripts/audit_dataset_integrity.py", failures)
        return
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        ok("scripts/audit_dataset_integrity.py passes")
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        fail("scripts/audit_dataset_integrity.py failed", failures)


def audit_reproducibility_guide(failures: list[str]) -> None:
    path = ROOT / "REPRODUCIBILITY.md"
    if not path.exists():
        fail("missing REPRODUCIBILITY.md", failures)
        return
    text = path.read_text(encoding="utf-8")
    required_snippets = [
        "Fast Artifact Verification",
        "Full Pipeline Regeneration",
        "python scripts/audit_release.py",
        "OPENROUTER_API_KEY",
        "Core Claims and Evidence",
    ]
    for snippet in required_snippets:
        if snippet in text:
            ok(f"REPRODUCIBILITY.md contains {snippet}")
        else:
            fail(f"REPRODUCIBILITY.md missing {snippet}", failures)


def audit_pdf_build_guide(failures: list[str]) -> None:
    path = ROOT / "submission_materials" / "PDF_BUILD_GUIDE.md"
    if not path.exists():
        fail("missing submission_materials/PDF_BUILD_GUIDE.md", failures)
        return
    text = path.read_text(encoding="utf-8")
    required_snippets = [
        "Overleaf",
        "python scripts/prepare_arxiv_package.py",
        "python scripts/compile_manuscripts.py",
        "python scripts/audit_submission_ready.py",
        "build/arxiv_package/",
        "paper/software_impacts.tex",
    ]
    for snippet in required_snippets:
        if snippet in text:
            ok(f"PDF_BUILD_GUIDE.md contains {snippet}")
        else:
            fail(f"PDF_BUILD_GUIDE.md missing {snippet}", failures)


def audit_submission_metadata(failures: list[str]) -> None:
    statements = ROOT / "submission_materials/SUBMISSION_STATEMENTS.md"
    if not statements.exists():
        fail("missing submission_materials/SUBMISSION_STATEMENTS.md", failures)
    else:
        text = statements.read_text(encoding="utf-8")
        for snippet in [
            "Conflict of Interest",
            "Funding",
            "Data Availability",
            "CRediT Author Statement",
            "Highlights",
        ]:
            if snippet in text:
                ok(f"SUBMISSION_STATEMENTS.md contains {snippet}")
            else:
                fail(f"SUBMISSION_STATEMENTS.md missing {snippet}", failures)

    citation = ROOT / "CITATION.cff"
    if citation.exists():
        text = citation.read_text(encoding="utf-8")
        for snippet in [
            "license: MIT",
            "version: \"0.1.0\"",
            "repository-code: \"https://github.com/XZXAAAA/llm-code-bug-taxonomy-artifact\"",
        ]:
            if snippet in text:
                ok(f"CITATION.cff contains {snippet}")
            else:
                fail(f"CITATION.cff missing {snippet}", failures)


def audit_ci_workflow(failures: list[str]) -> None:
    path = ROOT / ".github/workflows/release-audit.yml"
    if not path.exists():
        fail("missing .github/workflows/release-audit.yml", failures)
        return
    text = path.read_text(encoding="utf-8")
    required = [
        "pip install -r requirements.txt",
        "python scripts/run_fast_verification.py",
    ]
    for snippet in required:
        if snippet in text:
            ok(f"release-audit workflow contains {snippet}")
        else:
            fail(f"release-audit workflow missing {snippet}", failures)
    forbidden = ["python src/generate.py", "OPENROUTER_API_KEY"]
    for snippet in forbidden:
        if snippet in text:
            fail(f"release-audit workflow should not require external API: found {snippet}", failures)
        else:
            ok(f"release-audit workflow does not contain {snippet}")


def audit_release_bundle(failures: list[str]) -> None:
    bundle = ROOT / "build" / "release" / "llm-code-bug-taxonomy-artifact-v0.1.0.zip"
    if not bundle.exists():
        fail("missing build/release/llm-code-bug-taxonomy-artifact-v0.1.0.zip", failures)
        return

    with zipfile.ZipFile(bundle) as zf:
        names = set(zf.namelist())

    required = [
        "README.md",
        "REPRODUCIBILITY.md",
        "CITATION.cff",
        "paper/main.tex",
        "paper/software_impacts.tex",
        "data/raw/HumanEval.jsonl",
        "data/processed/results.jsonl",
        "results/tables/artifact_manifest.csv",
        "results/tables/model_metadata.csv",
        "results/tables/prompt_inventory.csv",
        "results/tables/permutation_tests.txt",
        "results/tables/logic_binary_chisq.txt",
        "results/human_eval/review_sheet.csv",
        "results/human_eval/review_key.csv",
        "results/human_eval/CODING_GUIDE.md",
        "submission_materials/PDF_BUILD_GUIDE.md",
        "submission_materials/PROMPT_INVENTORY.md",
        "scripts/run_fast_verification.py",
        "scripts/generate_model_metadata.py",
        "scripts/generate_prompt_inventory.py",
        "scripts/audit_dataset_integrity.py",
        "scripts/audit_numeric_claims.py",
        "scripts/audit_text_cleanliness.py",
        "scripts/audit_metadata.py",
        "scripts/test_fill_release_links.py",
        "scripts/audit_release.py",
        "scripts/audit_submission_ready.py",
        "scripts/fill_release_links.py",
        "scripts/compile_manuscripts.py",
    ]
    for name in required:
        if name in names:
            ok(f"release bundle contains {name}")
        else:
            fail(f"release bundle missing {name}", failures)

    forbidden_fragments = [".env", ".git/", "build/", "__pycache__/"]
    offenders = [
        name for name in names
        if any(fragment in name for fragment in forbidden_fragments)
    ]
    if offenders:
        fail(f"release bundle contains forbidden paths: {sorted(offenders)[:5]}", failures)
    else:
        ok("release bundle contains no forbidden secret/build/cache paths")


def audit_manuscript_text(failures: list[str]) -> None:
    path = ROOT / "paper/main.tex"
    if not path.exists():
        fail("missing paper/main.tex", failures)
        return
    text = path.read_text(encoding="utf-8")
    if "TODO" in text or "DELTA" in text:
        fail("paper/main.tex still contains TODO/DELTA marker", failures)
    else:
        ok("paper/main.tex has no TODO/DELTA marker")
    for citation in ["tambon2024bugs", "jain2024livecodebench", "li2024deveval"]:
        if citation in text:
            ok(f"paper/main.tex cites {citation}")
        else:
            fail(f"paper/main.tex does not cite {citation}", failures)

    references = ROOT / "paper" / "references.bib"
    if references.exists():
        bib = references.read_text(encoding="utf-8")
        for snippet in [
            "Moradi Dakhel, Arghavan",
            "Desmarais, Michel C.",
            "doi={10.1007/s10664-025-10661-1}",
        ]:
            if snippet in bib:
                ok(f"paper/references.bib contains {snippet}")
            else:
                fail(f"paper/references.bib missing {snippet}", failures)

    required_claims = [
        "546 (83.2\\%) pass and 110 fail",
        "LOGIC errors account for 87.3\\% (96/110; 95\\% CI: 79.8--92.3\\%)",
        "mathematical-reasoning errors (44.8\\%, 43/96; 95\\% CI:",
        "wrong-algorithm choices (21.9\\%, 21/96; 95\\% CI:",
        "64/96 (66.7\\%)",
        "95\\% Wilson CI: 79.8--92.3\\%",
        "95\\% CI: 35.2--54.7\\%",
        "95\\% CI: 14.8--31.1\\%",
        "$\\chi^2=3.394$",
        "$p=0.335$",
        "$V=0.176$",
        "$\\chi^2=21.29$",
        "$V=0.254$",
        "24/28 expected cells",
        "$p=0.2691$",
        "40-item",
        "blind review sheet",
        "human-validation result is reported",
        "42/96 (43.8\\%)",
        "$\\kappa$ is 0.305",
    ]
    for claim in required_claims:
        if claim in text:
            ok(f"paper/main.tex contains numeric claim: {claim}")
        else:
            fail(f"paper/main.tex missing numeric claim: {claim}", failures)

    software_impacts = ROOT / "paper/software_impacts.tex"
    if not software_impacts.exists():
        fail("missing paper/software_impacts.tex", failures)
        return
    si_text = software_impacts.read_text(encoding="utf-8")
    forbidden_template_markers = [
        "Once you have completed the template",
        "Please fill in this column",
        "Reminder: Before you submit",
        "Title / name of your software",
    ]
    for marker in forbidden_template_markers:
        if marker in si_text:
            fail(f"paper/software_impacts.tex still contains template marker: {marker}", failures)
            break
    else:
        ok("paper/software_impacts.tex has no obvious template-instruction markers")

    for item in [
        "MIT License",
        "0.1.0",
        "A Reproducible Pipeline for Classifying Bug Types in LLM-Generated Code",
        "Cohen's $\\kappa=0.305$",
        "Impact Overview",
        "https://doi.org/10.5281/zenodo.21025967",
    ]:
        if item in si_text:
            ok(f"paper/software_impacts.tex contains {item}")
        else:
            fail(f"paper/software_impacts.tex missing {item}", failures)
    if "TBD" in si_text:
        ok("paper/software_impacts.tex still has explicit TBD placeholders for public repository/archive links")
    else:
        ok("paper/software_impacts.tex has no TBD placeholders")

    for rel, candidate in [("paper/main.tex", text), ("paper/software_impacts.tex", si_text)]:
        lower = candidate.lower()
        offenders = [phrase for phrase in OVERCLAIM_PHRASES if phrase in lower]
        if offenders:
            fail(f"{rel} contains overclaiming or promotional phrase(s): {offenders}", failures)
        else:
            ok(f"{rel} avoids configured overclaiming/promotional phrases")


def audit_supporting_document_text(failures: list[str]) -> None:
    required_readme_claims = [
        "656 generations: 4 models x 164 HumanEval problems.",
        "546 pass, 110 fail",
        "87.3% of failures are wrong-output LOGIC errors",
        "44.8%",
        "43/96",
        "21.9%",
        "21/96",
        "chi2 = 21.29",
        "Cramer's V = 0.254",
        "chi2 = 3.394",
        "Cramer's V = 0.176",
        "p = 0.2691",
        "permutation p = 0.3445",
        "Cohen's kappa = 0.305",
        "42/96, 43.8%",
        "95% Wilson CI: 79.8-92.3%",
        "95% CI: 35.2-54.7%",
        "95% CI: 14.8-31.1%",
        "40-item blind human-review sample",
        "claim human validation",
    ]
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for claim in required_readme_claims:
            if claim in text:
                ok(f"README.md contains claim: {claim}")
            else:
                fail(f"README.md missing claim: {claim}", failures)

    for rel in SUPPORTING_DOCS:
        path = ROOT / rel
        if not path.exists():
            fail(f"missing supporting document {rel}", failures)
            continue
        lower = path.read_text(encoding="utf-8").lower()
        offenders = [phrase for phrase in OVERCLAIM_PHRASES if phrase in lower]
        if offenders:
            fail(f"{rel} contains overclaiming or promotional phrase(s): {offenders}", failures)
        else:
            ok(f"{rel} avoids configured overclaiming/promotional phrases")


def audit_arxiv_package(failures: list[str]) -> None:
    package = ROOT / "build/arxiv_package"
    required = [
        "main.tex",
        "references.bib",
        "fig1_category_freq.png",
        "fig2_category_by_model.png",
        "fig3_logic_subcat.png",
        "MANIFEST.txt",
    ]
    for name in required:
        path = package / name
        if path.exists():
            ok(f"arXiv package contains {name}")
        else:
            fail(f"arXiv package missing {name}", failures)
    main = package / "main.tex"
    if main.exists():
        text = main.read_text(encoding="utf-8")
        if "../results" in text:
            fail("arXiv package still references ../results", failures)
        else:
            ok("arXiv package uses local figure paths")
        source = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
        expected = source
        for figure_name in [
            "fig1_category_freq.png",
            "fig2_category_by_model.png",
            "fig3_logic_subcat.png",
        ]:
            expected = expected.replace(f"../results/figures/{figure_name}", figure_name)
        if text == expected:
            ok("arXiv package main.tex matches current paper/main.tex with local figure paths")
        else:
            fail("arXiv package main.tex is stale; rerun scripts/prepare_arxiv_package.py", failures)


def audit_secret_patterns(failures: list[str]) -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts or "build" in rel.parts or path.name == ".env":
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                offenders.append(str(rel))
                break
    if offenders:
        fail(f"secret-looking key patterns found in {sorted(offenders)}", failures)
    else:
        ok("no obvious secret-looking API keys in tracked text artifacts")


def main() -> None:
    failures: list[str] = []
    audit_required_files(failures)
    audit_counts(failures)
    audit_agreement(failures)
    audit_rq2_statistics(failures)
    audit_interval_tables(failures)
    audit_model_metadata(failures)
    audit_prompt_inventory(failures)
    audit_human_review_instrument(failures)
    audit_artifact_manifest(failures)
    audit_requirements(failures)
    audit_text_cleanliness_script(failures)
    audit_metadata_script(failures)
    audit_release_link_fill_script(failures)
    audit_dataset_integrity_script(failures)
    audit_numeric_claims_script(failures)
    audit_reproducibility_guide(failures)
    audit_pdf_build_guide(failures)
    audit_submission_metadata(failures)
    audit_ci_workflow(failures)
    audit_manuscript_text(failures)
    audit_supporting_document_text(failures)
    audit_arxiv_package(failures)
    audit_release_bundle(failures)
    audit_secret_patterns(failures)

    if failures:
        print("\nRelease audit failed:")
        for item in failures:
            print(f"- {item}")
        sys.exit(1)

    print("\nRelease audit passed.")


if __name__ == "__main__":
    main()
