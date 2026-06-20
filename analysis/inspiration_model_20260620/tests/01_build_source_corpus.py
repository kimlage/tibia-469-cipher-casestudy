from __future__ import annotations

from pathlib import Path

from _common import HERE, verdict_line, write_result


def main() -> None:
    registry = HERE / "source_registry.yaml"
    text = registry.read_text(encoding="utf-8")
    source_count = text.count("\n  - id:")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "01_build_source_corpus",
        "classification": "accepted_mechanical",
        "translation_delta": "NONE",
        "source_count": source_count,
        "metric": "registry exists with evidence classes, allowed uses, and blocked uses",
        "stop_rule": "No source can move semantic verdict unless registry class is official_gt.",
    }
    lines = [
        "# Build Source Corpus",
        "",
        verdict_line(result),
        "",
        f"Registry entries counted: `{source_count}`.",
        "",
        "The corpus is intentionally provenance-oriented. It can support source",
        "family closure and mechanical hypotheses, not plaintext promotion.",
    ]
    write_result("01_build_source_corpus", result, lines)


if __name__ == "__main__":
    main()
