# Coding Guide: LOGIC Subtypes

Read the problem prompt and generated code. Choose exactly one subtype code.

Do not open `review_key.csv` until both reviewers have completed
`review_sheet.csv`.

Valid labels:

- `WRONG_ALGO`: wrong overall algorithm or approach; a different method is needed.
- `MISSING_EDGE`: fails to handle a special input, such as empty input, single element, or all-equal values.
- `BOUNDARY`: boundary condition error, such as off-by-one, first/last element, inclusive/exclusive range, or index logic.
- `STATE_UPDATE`: incorrect accumulator, counter, loop variable, mutation, or state update.
- `MATH_REASONING`: wrong formula, operation, rounding, sign, carry, or other mathematical reasoning step.
- `PREMATURE_SIMPL`: ignored a stated requirement or over-simplified the problem.
- `SPEC_PARTIAL`: implemented only some required cases or branches.

If no subtype fits, write the closest label and explain the uncertainty in the
corresponding notes column.
