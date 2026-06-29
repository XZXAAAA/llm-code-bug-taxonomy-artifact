# Prompt Inventory

This file records the prompt templates used by the released pipeline. Templates are shown before runtime problem/code substitution.

| ID | Stage | Source | Symbol | Characters | SHA-256 |
|---|---|---|---|---:|---|
| generation_prompt | code_generation | `src/generate.py` | `PROMPT_TMPL` | 147 | `7597a0dbdeb022a2bbaba23e7557b37ecd03c4832afb08f493c60125a2b54b97` |
| primary_failure_label_prompt | primary_failure_labeling | `src/label.py` | `CLASSIFY_PROMPT` | 664 | `8c3963f823262adbefa58c6c61f3327042e91560292448ea5308b994deea3958` |
| primary_logic_subtype_prompt | logic_subtype_labeling | `src/sublabel.py` | `PROMPT` | 927 | `395699dc9772311ab22d00b05ca55d6afda7ba673f8693f218d10d21064aab40` |
| blind_second_logic_subtype_prompt | blind_second_logic_subtype_labeling | `src/second_annotator.py` | `PROMPT` | 1077 | `7be6dda669fb01d12253770c984885f875d9c50aa722fe8e73e81147989bfc10` |

## generation_prompt

- Stage: `code_generation`
- Source: `src/generate.py`
- Symbol: `PROMPT_TMPL`
- SHA-256: `7597a0dbdeb022a2bbaba23e7557b37ecd03c4832afb08f493c60125a2b54b97`

```text
Complete the following Python function. Return ONLY the complete function in a single ```python code block, no explanation.

```python
{prompt}
```
```

## primary_failure_label_prompt

- Stage: `primary_failure_labeling`
- Source: `src/label.py`
- Symbol: `CLASSIFY_PROMPT`
- SHA-256: `8c3963f823262adbefa58c6c61f3327042e91560292448ea5308b994deea3958`

```text
You are labeling a bug in AI-generated Python code that RUNS but FAILS the unit tests (wrong output).
Pick exactly ONE category code that best describes the root cause.

Categories:
- LOGIC: algorithmic/logic error (wrong computation)
- BOUNDARY: fails only on edge/special inputs (empty, first/last, negatives)
- SPEC: misunderstood the problem; implemented something different
- FORMAT: right idea but wrong return shape/format/rounding
- INCOMPLETE: stub or missing branch (e.g., returns None / pass)
- OTHER: none of the above

Problem specification:
{spec}

Model's code:
{code}

Answer with a JSON object: {{"category": "<CODE>", "reason": "<short reason>"}}
```

## primary_logic_subtype_prompt

- Stage: `logic_subtype_labeling`
- Source: `src/sublabel.py`
- Symbol: `PROMPT`
- SHA-256: `395699dc9772311ab22d00b05ca55d6afda7ba673f8693f218d10d21064aab40`

```text
You are categorizing the ROOT CAUSE of a logic bug in AI-generated Python code.
The code runs but returns a WRONG result on the hidden tests.
Choose exactly ONE subcategory code.

Subcategories:
- WRONG_ALGO: wrong overall algorithm/approach; a different method is needed.
- MISSING_EDGE: fails to handle a special input (empty, None, single element, all-equal).
- BOUNDARY: off-by-one, first/last, inclusive vs exclusive, index-range logic.
- STATE_UPDATE: incorrect accumulator/counter/loop-variable/in-place update.
- MATH_REASONING: wrong formula, operation, rounding, sign, or carry.
- PREMATURE_SIMPL: ignored a stated requirement / over-simplified the problem.
- SPEC_PARTIAL: only implemented some of the required cases/branches.

Problem specification:
{spec}

Reference correct solution (for comparison only):
{ref}

Model's buggy code:
{code}

Reply with JSON: {{"subcategory": "<CODE>", "reason": "<short reason>"}}
```

## blind_second_logic_subtype_prompt

- Stage: `blind_second_logic_subtype_labeling`
- Source: `src/second_annotator.py`
- Symbol: `PROMPT`
- SHA-256: `7be6dda669fb01d12253770c984885f875d9c50aa722fe8e73e81147989bfc10`

```text
You are an independent annotator for a research study on bugs in
AI-generated Python code. The code runs but returns a wrong result on hidden tests.

Choose exactly ONE root-cause subcategory code.

Subcategories:
- WRONG_ALGO: wrong overall algorithm/approach; a different method is needed.
- MISSING_EDGE: fails to handle a special input (empty, None, single element, all-equal).
- BOUNDARY: off-by-one, first/last, inclusive vs exclusive, index-range logic.
- STATE_UPDATE: incorrect accumulator/counter/loop-variable/in-place update.
- MATH_REASONING: wrong formula, operation, rounding, sign, or carry.
- PREMATURE_SIMPL: ignored a stated requirement / over-simplified the problem.
- SPEC_PARTIAL: only implemented some of the required cases/branches.

Do not assume a category from surface keywords. Infer the likely root cause from
the problem specification and the buggy code. You are not given any reference
solution or previous label.

Problem specification:
{spec}

Model's buggy code:
{code}

Reply with JSON: {{"subcategory": "<CODE>", "reason": "<short reason>"}}
```
