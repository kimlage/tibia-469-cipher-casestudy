from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    external = load_json("analysis/post_review_20260619/external_numeric_string_classifier_results.json")
    classes = {row["name"]: row["classification"] for row in external["rows"]}
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "dreamer_duality_layer_split_test",
        "classification": "watchlist_only",
        "translation_delta": "NONE",
        "metric": "source-class separation between book layer, phrase triggers, copy holdouts, and numeric anchors",
        "classes": classes,
        "stop_rule": "Accept only if a preregistered layer split predicts held-out source class or mechanical coverage.",
    }
    lines = [
        "# Dreamer Duality Layer Split Test",
        "",
        verdict_line(result),
        "",
        "Current source classes already support keeping phrase/external/book layers",
        "separate. Dreamer/Nightmare/Bones duality adds no new predictive split yet.",
    ]
    write_result("dreamer_duality_layer_split_test", result, lines)


if __name__ == "__main__":
    main()
