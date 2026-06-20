from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    classifier = load_json("analysis/post_review_20260619/external_numeric_string_classifier_results.json")
    rows = {row["name"]: row for row in classifier["rows"]}
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "npc_keyword_trigger_mechanism_audit",
        "classification": "weak_clue",
        "translation_delta": "NONE",
        "metric": "source-class split between phrase triggers, copy holdouts, numeric anchors, and controls",
        "classified_sources": list(rows),
        "chayenne": rows.get("chayenne", {}).get("classification"),
        "avar_tar": rows.get("avar_tar", {}).get("classification"),
        "stop_rule": "Phrase layer may be modeled as trigger/context only; no sentence translation without official gloss.",
    }
    lines = [
        "# NPC Keyword Trigger Mechanism Audit",
        "",
        verdict_line(result),
        "",
        "| Source | Classification | Semantic value |",
        "|---|---|---|",
    ]
    for row in classifier["rows"]:
        lines.append(f"| `{row['name']}` | `{row['classification']}` | `{row['semantic_value']}` |")
    lines += [
        "",
        "The phrase layer is best treated as source-class/trigger material. It does",
        "not supply book-layer plaintext.",
    ]
    write_result("npc_keyword_trigger_mechanism_audit", result, lines)


if __name__ == "__main__":
    main()
