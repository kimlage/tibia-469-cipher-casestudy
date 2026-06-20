from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    external = load_json("analysis/post_review_20260619/external_numeric_string_classifier_results.json")
    mapping = {
        "chayenne": "copy_holdout",
        "your_true_colour": "external_numeric_event",
        "secret_library_74032_45331": "numeric_identity_or_book_anchor",
        "honeminas_primary_vectors": "formula_lore",
        "avar_tar": "negative_control",
    }
    rows = []
    for row in external["rows"]:
        rows.append({
            "name": row["name"],
            "prior_classification": row["classification"],
            "authorial_source_class": mapping.get(row["name"], "watchlist_only"),
            "semantic_value": row["semantic_value"],
        })
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "authorial_source_classifier",
        "classification": "accepted_mechanical",
        "translation_delta": "NONE",
        "metric": "deterministic source-class routing for known 469-adjacent sources",
        "rows": rows,
        "stop_rule": "New sources default to watchlist/rejected unless provenance and class are explicit.",
    }
    lines = [
        "# Authorial Source Classifier",
        "",
        verdict_line(result),
        "",
        "| Source | Authorial/source class | Prior classifier | Semantic value |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['name']}` | `{row['authorial_source_class']}` | `{row['prior_classification']}` | `{row['semantic_value']}` |")
    write_result("authorial_source_classifier", result, lines)


if __name__ == "__main__":
    main()
