# Software Impacts Manuscript Outline

Working title:

**A Reproducible Pipeline for Classifying Bug Types in LLM-Generated Code**

Software Impacts should be written as a software artifact paper. The empirical
findings are evidence of usefulness, but the main contribution should be the
reusable pipeline.

Current draft:

- `paper/software_impacts.tex`

Before formal submission, replace all `TBD` repository/archive placeholders and
compile the manuscript in a LaTeX environment.

## 1. Code Metadata

The draft metadata table is maintained in `submission_materials/SOFTWARE_METADATA.md`.
Before submission, replace all `TBD` repository/archive fields with public links.

The current software release files include:

- `LICENSE`: MIT License.
- `CITATION.cff`: citation metadata with repository/archive placeholders.
- `requirements.txt`: Python dependency list.
- `scripts/audit_release.py`: release consistency audit.

The Software Impacts article should include or adapt the following metadata:

- Current code version.
- Permanent link to code/repository used for this paper.
- Permanent link to reproducible capsule or archived release.
- Legal code license.
- Code versioning system.
- Software code languages, tools, and services used.
- Compilation/installation requirements.
- Operating systems tested.
- Dependencies.
- Developer documentation/manual.
- Support email.

## 2. Motivation and Significance

Explain the problem:

- LLM code evaluation usually reports pass/fail.
- Debugging and review need failure-type information.
- Some related studies do not release all intermediate artifacts needed to inspect the labeling pipeline.

Explain why the software matters:

- It turns model generations into executable tests, failure signals, labels, tables, and figures.
- It can be reused for other models, benchmarks, and taxonomies.
- It supports reproducible empirical software-engineering studies.

## 3. Software Description

Describe modules:

- `generate.py`: model generation.
- `sanitize.py`: code extraction.
- `harness.py` and `run_tests.py`: test execution and failure capture.
- `label.py`: primary bug-category labeling.
- `sublabel.py`: LOGIC subtype labeling.
- `second_annotator.py`: independent blind automatic agreement check.
- `kappa.py`: agreement calculation.
- `analyze.py` and `analyze_logic.py`: tables and figures.

Include a simple workflow diagram in the final manuscript if space allows.

## 4. Illustrative Results

Use the current results as a demonstration:

- 656 generations.
- 110 failures.
- 87.3% (96/110; 95% Wilson CI: 79.8-92.3%) LOGIC failures.
- LOGIC subtype distribution led by math reasoning (43/96; 95% CI: 35.2-54.7%) and wrong algorithm (21/96; 95% CI: 14.8-31.1%).
- No statistically significant cross-model bug-profile difference was detected in this sample.
- LOGIC/non-LOGIC companion test also did not detect a significant cross-model difference.
- 40-item blind human-review sheet included as an instrument; no completed human-validation result yet.

Keep this section concise. The venue wants the software impact, not a full empirical
software engineering paper.

## 5. Impact

Possible impact claims:

- Enables reproducible comparison of LLM failure modes.
- Helps researchers move beyond pass@k.
- Helps educators demonstrate common LLM code-generation failure modes.
- Provides a baseline pipeline for future benchmark/model studies.

Avoid overclaiming:

- Do not say the taxonomy is universal.
- Do not say the labels are human-validated unless that work is done.
- Do not say model differences are absent in general; only say they were not detected in this sample.

## 6. Reuse Potential

Explain how others can adapt it:

- Swap HumanEval for MBPP or another benchmark.
- Add more models through OpenRouter or another OpenAI-compatible endpoint.
- Replace or extend the taxonomy.
- Add human annotation.
- Use the included blind review sheet and coding guide for a human validation subset.
- Add repair experiments.

## 7. Availability

Before submission, fill in:

- Repository URL.
- Release DOI.
- License.
- Documentation URL.
- Data availability statement.

## 8. Statements

Draft statements to prepare:

```text
Conflict of interest: The author declares no competing interests.
Funding: This research received no specific grant from any funding agency.
Data availability: The benchmark, generated outputs, labels, and analysis artifacts
needed to reproduce the reported results are available in the accompanying repository.
```

Update these statements if the final situation changes.
