from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"


def load_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def verdict_line(result: dict) -> str:
    return f"Verdict: `{result['classification']}`. Translation delta: `{result['translation_delta']}`."


def blocked(name: str, reason: str, *, classification: str = "blocked_waiting_for_official_source") -> None:
    result = {
        "schema": "inspiration_test_result.v1",
        "test": name,
        "classification": classification,
        "translation_delta": "NONE",
        "blocker": reason,
    }
    write_result(
        name,
        result,
        [
            f"# {name}",
            "",
            verdict_line(result),
            "",
            f"Blocker: {reason}",
        ],
    )
