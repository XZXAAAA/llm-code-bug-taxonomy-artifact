"""Generate machine-readable model and labeling metadata for the release."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables" / "model_metadata.csv"


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    provider = cfg["provider"]
    generation = cfg["generation"]
    labeling = cfg["labeling"]

    rows: list[dict[str, str | int | float]] = []
    for model_id in cfg["models"]:
        rows.append(
            {
                "role": "generation",
                "model_id": model_id,
                "provider_name": provider["name"],
                "base_url": provider["base_url"],
                "access_date": generation["access_date"],
                "benchmark": "HumanEval",
                "samples_per_problem": generation["samples_per_problem"],
                "temperature": generation["temperature"],
                "max_tokens": generation["max_tokens"],
            }
        )

    rows.append(
        {
            "role": "primary_failure_labeler",
            "model_id": labeling["primary_labeler_model"],
            "provider_name": provider["name"],
            "base_url": provider["base_url"],
            "access_date": generation["access_date"],
            "benchmark": "HumanEval failures",
            "samples_per_problem": "",
            "temperature": labeling["primary_labeler_temperature"],
            "max_tokens": labeling["primary_labeler_max_tokens"],
        }
    )
    rows.append(
        {
            "role": "primary_logic_subtype_labeler",
            "model_id": labeling["logic_subtype_labeler_model"],
            "provider_name": provider["name"],
            "base_url": provider["base_url"],
            "access_date": generation["access_date"],
            "benchmark": "HumanEval LOGIC failures",
            "samples_per_problem": "",
            "temperature": labeling["logic_subtype_labeler_temperature"],
            "max_tokens": labeling["logic_subtype_labeler_max_tokens"],
        }
    )
    rows.append(
        {
            "role": "blind_second_subtype_labeler_default",
            "model_id": labeling["second_labeler_default_model"],
            "provider_name": provider["name"],
            "base_url": provider["base_url"],
            "access_date": generation["access_date"],
            "benchmark": "HumanEval LOGIC failures",
            "samples_per_problem": "",
            "temperature": labeling["second_labeler_temperature"],
            "max_tokens": labeling["second_labeler_max_tokens"],
        }
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
