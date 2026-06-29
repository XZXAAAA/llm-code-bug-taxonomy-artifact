"""Extract runnable Python code from chat-style model replies."""

from __future__ import annotations

import re


def extract_code(text: str) -> str:
    """Extract Python code, preferring fenced code blocks when present."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        return max(blocks, key=len).strip()

    # Fallback for truncated replies that start a code fence but never close it.
    match = re.search(r"```(?:python|py)?\s*\n(.*)", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.replace("```python", "").replace("```py", "").replace("```", "").strip()


def _prompt_preamble(prompt: str, entry_point: str) -> str:
    """Return any prompt text before the target function definition."""
    marker = f"def {entry_point}"
    index = prompt.find(marker)
    return prompt[:index] if index != -1 else ""


def build_program(problem: dict, raw_reply: str) -> str:
    """Combine model code with HumanEval tests into a complete runnable program.

    If the model returned a full function definition, keep that function and
    preserve any imports or helpers from the benchmark prompt. If the model
    returned only a function body, append it to the prompt.
    """
    code = extract_code(raw_reply)
    entry = problem["entry_point"]
    test = problem["test"]
    check = f"\n\ncheck({entry})\n"

    if re.search(rf"def\s+{re.escape(entry)}\s*\(", code):
        preamble = _prompt_preamble(problem["prompt"], entry)
        return preamble + "\n" + code + "\n\n" + test + check
    return problem["prompt"] + code + "\n\n" + test + check
