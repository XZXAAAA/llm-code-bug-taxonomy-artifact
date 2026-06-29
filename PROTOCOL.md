# Research Protocol

**Working title:** An Empirical Study of Bug Types in LLM-Generated Code: A Taxonomy and Cross-Model Analysis

**Author:** Zixiao Xie

**Status:** reproducible pilot, targeting arXiv + Software Impacts

This protocol documents what the study measures, how labels are produced, and what
claims are allowed. The project should not claim human-validated labels unless a
human review is actually completed.

## 1. Motivation and Gap

LLM code-generation benchmarks usually report functional correctness, such as
pass@k. That tells us how often code passes tests, but not how models fail when
they fail. This study focuses on the failure side: bug categories, logic-error
subtypes, and whether the distribution differs across models.

## 2. Research Questions

- RQ1: What categories of bugs occur in LLM-generated code, and how frequent is each category?
- RQ1b: Within the observed LOGIC failure class, what subtype of reasoning error is responsible?
- RQ2: Do bug-type distributions differ across models?
- RQ3: Do bug-type distributions differ by task difficulty or task characteristics? Deferred.
- RQ4: Which bug types are easiest or hardest to repair? Future work.

## 3. Data

- Benchmark: HumanEval, 164 Python problems with unit tests.
- Models: GPT-4o-mini, DeepSeek-Chat, Qwen2.5-72B-Instruct, and Llama-3.1-8B-Instruct through OpenRouter.
- Generation setting: one sample per problem, temperature 0.2, max 1024 tokens.
- Recorded access date for the current artifact: 2026-06-23.
- Machine-readable model and labeler metadata: `results/tables/model_metadata.csv`.
- Failure set: a generation is a failure if it does not pass the benchmark tests.
- No company or internship data is used.

## 4. Method

1. Generate one solution per model/problem pair.
2. Sanitize the model reply into runnable Python code.
3. Run HumanEval tests in a subprocess with timeout protection.
4. Label each failure into one primary bug category.
5. Refine LOGIC failures into seven subtypes.
6. Run an independent blind second LLM annotator for LOGIC subtypes.
7. Report LLM-vs-LLM agreement using Cohen's kappa.
8. Add deterministic permutation checks for sparse RQ2 contingency tables.
9. Prepare a blind 40-item human-review sample for optional human validation.
10. Optionally add completed human labels on the sampled subset.

## 5. Taxonomy

| Code | Category | Short definition |
|------|----------|------------------|
| LOGIC | Logic / algorithmic error | Wrong logic though it runs |
| BOUNDARY | Boundary / off-by-one | Edge cases, empty input, first/last element |
| API_MISUSE | Wrong / hallucinated API | Nonexistent or misused library/function |
| TYPE | Type / signature error | Type mismatch, wrong arg count/order |
| TIMEOUT | Timeout | Infinite loop or excessive runtime |
| SYNTAX | Syntax error | Code does not parse |
| INCOMPLETE | Incomplete implementation | Stub, pass, missing branch |
| SPEC | Spec misunderstanding | Misread the problem statement |
| FORMAT | Output format error | Right idea, wrong format or return shape |
| OTHER | Other | Anything not above |

## 6. LOGIC Subtypes

| Code | Short definition |
|------|------------------|
| WRONG_ALGO | Wrong overall approach; a different method is needed |
| MISSING_EDGE | Unhandled special input |
| BOUNDARY | Off-by-one, inclusive/exclusive, first/last logic |
| STATE_UPDATE | Wrong accumulator, counter, mutation, or loop state |
| MATH_REASONING | Wrong formula, operation, rounding, sign, or carry |
| PREMATURE_SIMPL | Ignored a stated requirement or over-simplified the problem |
| SPEC_PARTIAL | Only some required cases or branches are implemented |

## 7. Labeling Policy

The project uses automatic labels and must describe them accurately.

- Rule-based labels are used for deterministic failure signals such as syntax errors, timeouts, and exception types.
- Assertion failures are labeled by an LLM classifier because the code runs but returns a wrong result.
- LOGIC subtype labels are produced by an LLM classifier that sees the problem, buggy code, and reference solution.
- A second independent LLM annotator is used as a robustness check. It is blind: it does not see the reference solution, primary label, or primary explanation.
- The agreement statistic is LLM-vs-LLM Cohen's kappa, not human inter-rater agreement.
- Human validation can be added later, but the paper must not imply it has been done unless the review sheet is completed.

## 8. Implemented Pipeline

```text
humaneval.py            benchmark loader
generate.py             generation through OpenRouter
sanitize.py             runnable code extraction
harness.py              sandboxed test runner
run_tests.py            pass/fail and failure signal extraction
label.py                primary bug-category labels
sublabel.py             LOGIC subtype labels with reference solution
second_annotator.py     blind second LLM subtype labels
kappa.py                LLM-vs-LLM agreement and optional human agreement
prepare_human_review_sample.py blind human-review sample generation
analyze.py              RQ1/RQ2 analysis
analyze_logic.py        LOGIC subtype analysis
permutation_tests.py    deterministic RQ2 permutation checks
generate_model_metadata.py model/provider/run metadata table
```

## 9. Current Status

Completed:

- 656 generations.
- 110 failures identified.
- 96 LOGIC failures sub-labeled.
- RQ1, RQ1b, and RQ2 tables/figures generated.
- RQ2 full-category effect size added: Cramer's V = 0.254, with sparse-cell warning.
- RQ2 LOGIC/non-LOGIC companion test added: chi2 = 3.394, p = 0.335, Cramer's V = 0.176.
- Deterministic 10,000-iteration permutation checks added for RQ2 sparse-table robustness.
- Blind second LLM subtype annotation completed for all 96 LOGIC failures.
- LLM-vs-LLM agreement computed: exact agreement 42/96 (43.8%), Cohen's kappa 0.305 (fair).
- Blind 40-item human-review sheet generated, with labels intentionally blank.
- Related work positioning revised to treat Tambon et al. as the closest taxonomy baseline and to frame this project as a reproducible artifact-oriented pilot.
- Submission material folder added for arXiv and Software Impacts preparation.

Still needed:

- Package the software artifact publicly with a license and archived release DOI.
- Prepare arXiv source paths and Software Impacts template version.
- Re-check the closest-prior-work discussion after a full reading of Tambon et al. 2025.
- Decide whether to add a small human validation sample before journal submission.

## 10. Target Venues

Primary path:

1. arXiv preprint for visibility and timestamp.
2. Elsevier Software Impacts as the main submission.

Stretch:

- PeerJ Computer Science, if the paper is strengthened into a fuller CS empirical study.

Not recommended as the first target:

- IEEE Access, because the current contribution is better suited to a reproducible software artifact than to a broad high-volume research article.
