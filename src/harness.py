"""Small subprocess-based HumanEval execution harness.

Given a HumanEval problem and a generated completion, this module builds a full
Python program, runs it in a subprocess with a timeout, and returns a compact
failure signal for downstream bug labeling.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Result:
    passed: bool
    status: str
    error_type: str
    signal: str


def build_program(problem: dict, completion: str) -> str:
    """Combine prompt, completion, tests, and check call into one program."""
    return (
        problem["prompt"]
        + completion
        + "\n\n"
        + problem["test"]
        + f"\n\ncheck({problem['entry_point']})\n"
    )


def _parse_signal(stderr: str) -> tuple[str, str, str]:
    """Parse stderr into status, error type, and a short signal string."""
    text = stderr.strip()
    last = text.splitlines()[-1] if text else ""
    if "SyntaxError" in text or "IndentationError" in text:
        error_type = last.split(":")[0].strip()
        return "syntax", error_type, last
    if last and ":" in last and last.split(":")[0].isidentifier():
        error_type = last.split(":")[0].strip()
        if error_type == "AssertionError":
            return "fail_assert", error_type, last
        return "exception", error_type, last
    if last == "AssertionError":
        return "fail_assert", "AssertionError", last
    return "exception", last.split(":")[0].strip() if last else "Unknown", last


def evaluate(problem: dict, completion: str, timeout: float = 10.0) -> Result:
    """Evaluate a generated function body/completion against a HumanEval problem."""
    return evaluate_program(build_program(problem, completion), timeout)


def evaluate_program(program: str, timeout: float = 10.0) -> Result:
    """Run a complete Python program and return a compact execution result."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(program)
        path = handle.name
    try:
        proc = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            return Result(True, "pass", "", "")
        status, error_type, signal = _parse_signal(proc.stderr)
        return Result(False, status, error_type, signal)
    except subprocess.TimeoutExpired:
        return Result(False, "timeout", "Timeout", f"exceeded {timeout}s")
    finally:
        try:
            Path(path).unlink()
        except OSError:
            pass
