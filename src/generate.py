"""Generate HumanEval solutions through an OpenAI-compatible chat API.

Output:
  data/raw/generations/{model_slug}.jsonl

Each row:
  {task_id, model, sample, raw_reply}
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humaneval import load_problems  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "generations"

PROMPT_TMPL = (
    "Complete the following Python function. "
    "Return ONLY the complete function in a single ```python code block, "
    "no explanation.\n\n```python\n{prompt}\n```"
)


def slug(model: str) -> str:
    return model.replace("/", "__").replace(":", "_")


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_env()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    provider = cfg["provider"]
    generation = cfg["generation"]
    api_key = os.getenv(provider["api_key_env"], "").strip()
    if not api_key:
        sys.exit(f"Missing API key: set {provider['api_key_env']} in .env")

    def new_client() -> OpenAI:
        return OpenAI(
            base_url=provider["base_url"],
            api_key=api_key,
            timeout=60.0,
            max_retries=2,
        )

    client = new_client()

    def chat_with_retry(model: str, content: str, attempts: int = 5) -> str:
        """Return response text, retrying transient empty/error responses."""
        nonlocal client
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": content}],
                    temperature=float(generation["temperature"]),
                    max_tokens=int(generation["max_tokens"]),
                )
                choices = getattr(response, "choices", None)
                if choices and choices[0].message.content:
                    finish_reason = getattr(choices[0], "finish_reason", None)
                    if finish_reason not in ("error",):
                        return choices[0].message.content
                finish = getattr(choices[0], "finish_reason", None) if choices else None
                last_error = RuntimeError(f"empty/invalid response (finish={finish})")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            time.sleep(2 * attempt)
            client = new_client()
        raise RuntimeError(f"generation failed after retries: {last_error}")

    problems = list(load_problems().items())
    if generation.get("limit_problems"):
        problems = problems[: int(generation["limit_problems"])]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for model in cfg["models"]:
        out = OUT_DIR / f"{slug(model)}.jsonl"
        done = set()
        if out.exists():
            for line in out.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    done.add((row["task_id"], row["sample"]))
        n_ok = 0
        with out.open("a", encoding="utf-8") as handle:
            for task_id, problem in problems:
                for sample in range(int(generation["samples_per_problem"])):
                    if (task_id, sample) in done:
                        continue
                    try:
                        reply = chat_with_retry(model, PROMPT_TMPL.format(prompt=problem["prompt"]))
                        handle.write(
                            json.dumps(
                                {
                                    "task_id": task_id,
                                    "model": model,
                                    "sample": sample,
                                    "raw_reply": reply,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                        handle.flush()
                        n_ok += 1
                    except Exception as exc:  # noqa: BLE001
                        print(f"  [{model}] {task_id} s{sample} ERROR: {str(exc)[:100]}")
                        time.sleep(2)
        print(f"[{model}] wrote {n_ok} new generations -> {out.name}")


if __name__ == "__main__":
    main()
