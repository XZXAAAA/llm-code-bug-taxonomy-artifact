# Software Metadata

This file is a draft metadata table for Elsevier Software Impacts. Replace `TBD`
fields after the repository and archived release are public.

| Field | Value |
|---|---|
| Software name | Bug Types in LLM-Generated Code |
| Current version | 0.1.0 |
| Permanent link to code/repository | TBD |
| Permanent link to reproducible capsule/archive | TBD |
| Software citation DOI | TBD |
| Legal code license | MIT |
| Code versioning system | Git |
| Software code languages | Python, LaTeX |
| Main Python dependencies | pandas, matplotlib, scipy, pyyaml, openai |
| External services | OpenRouter API for model generation and LLM-assisted labeling |
| Supported operating systems | Windows tested; Linux/macOS expected with Python 3.10+ |
| Installation requirements | Python 3.10+, package dependencies in `requirements.txt`, optional LaTeX for PDF build |
| Documentation | `README.md`, `REPRODUCIBILITY.md`, `PROTOCOL.md`, `submission_materials/` |
| Input data | HumanEval JSONL benchmark and generated model outputs |
| Output data | pass/fail results, bug labels, LOGIC sublabels, agreement tables, figures, arXiv package |
| Model metadata | `results/tables/model_metadata.csv`, generated from `config.yaml` |
| Prompt metadata | `submission_materials/PROMPT_INVENTORY.md` and `results/tables/prompt_inventory.csv` |
| Artifact manifest | `results/tables/artifact_manifest.csv` and `results/tables/artifact_manifest.json` |
| Submission statements | `submission_materials/SUBMISSION_STATEMENTS.md` |
| Archive metadata | `.zenodo.json` |
| Support email | zixiaox2@illinois.edu |

## Software Functionality

The software implements a reproducible empirical pipeline:

1. Generate code from multiple LLMs on HumanEval.
2. Extract runnable Python functions from model replies.
3. Execute benchmark tests in a subprocess harness.
4. Capture pass/fail status and failure signals.
5. Label failure categories through deterministic rules and LLM assistance.
6. Refine LOGIC failures into seven subtypes.
7. Run an independent blind LLM annotator for subtype agreement.
8. Produce tables, figures, and manuscript-ready artifacts.

## Reuse Potential

Researchers can reuse the software to:

- compare additional LLMs;
- test other benchmarks such as MBPP;
- replace or extend the taxonomy;
- add human annotation workflows;
- study repairability by bug type;
- reproduce and audit the reported results.

## Known Limitations

- Current results use HumanEval only.
- Current generation uses one sample per model/problem.
- Hosted model identifiers may route to provider-current weights.
- Model identifiers, provider endpoint, access date, and generation/labeler
  settings are recorded in `results/tables/model_metadata.csv`.
- Prompt templates and prompt hashes are recorded in
  `submission_materials/PROMPT_INVENTORY.md` and `results/tables/prompt_inventory.csv`.
- Fine-grained subtype labels are machine-assigned and show only fair LLM-vs-LLM agreement.
- A 40-item blind human-review sheet is included, but human labels are blank.
- Human validation remains optional future work unless completed before submission.
