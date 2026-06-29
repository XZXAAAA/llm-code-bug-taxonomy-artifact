# Submission Statements

These statements are draft text for arXiv, Software Impacts, PeerJ Computer
Science, or repository/archive submissions. Replace `TBD` fields before formal
submission.

## Highlights

- Provides a reproducible pipeline for analyzing bug types in LLM-generated Python code.
- Releases generated outputs, execution results, labels, agreement files, tables, figures, and checksum manifests.
- Reports that 87.3% (96/110; 95% Wilson CI: 79.8-92.3%) of observed failures are wrong-output LOGIC errors in the current HumanEval artifact.
- Includes a blind second LLM annotator and reports fair subtype-label agreement (Cohen's kappa = 0.305).
- Includes a 40-item blind human-review sheet for optional future validation; the current artifact does not claim completed human validation.
- Packages both an arXiv research manuscript and a Software Impacts software-article draft.

## Conflict of Interest

The author declares no competing interests.

## Funding

This research received no specific grant from any funding agency in the public,
commercial, or not-for-profit sectors.

## Data Availability

The benchmark inputs, generated model outputs, execution results, bug labels,
LOGIC subtype labels, agreement outputs, result tables, figures, artifact manifest,
and reproduction scripts are included in the accompanying repository/archive. API
keys are excluded. Hosted model identifiers may route to provider-current weights,
so the released JSONL/CSV files should be treated as the authoritative artifact for
the reported results.

Repository URL: TBD

Archive DOI: TBD

## Code Availability

The source code is available under the MIT License.

Repository URL: TBD

Archived release: TBD

## CRediT Author Statement

Zixiao Xie: Conceptualization, Methodology, Software, Validation, Formal analysis,
Investigation, Data curation, Writing - original draft, Writing - review and
editing, Visualization.

## Ethics Statement

This study uses public benchmark data and generated code artifacts. It does not
use human-subject data, private company data, user data, or personally identifiable
information. API keys used for generation and labeling are excluded from the
repository and archive.

## Limitations Statement

The current artifact is a reproducible pilot. Results are limited to HumanEval,
Python, one sample per model/problem, and hosted model identifiers accessed through
OpenRouter. Fine-grained subtype labels are machine-assigned and show only fair
LLM-vs-LLM agreement. A blind human-review sheet is included, but the human-label
fields are blank; the results should not be described as human-validated.

## Suggested arXiv Comment

Reproducible pilot study; includes code, generated outputs, labels, figures, and
artifact-audit scripts. Repository and archived artifact: TBD.
