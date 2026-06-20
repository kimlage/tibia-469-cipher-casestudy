from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    external = load_json("analysis/post_review_20260619/external_numeric_string_classifier_results.json")
    rows = {row["name"]: row for row in external["rows"]}
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "numeric_identity_key_seed_search",
        "classification": "watchlist_only",
        "translation_delta": "NONE",
        "metric": "existing classifier status for 3478/486486-adjacent external anchors",
        "honeminas_primary_vectors": rows.get("honeminas_primary_vectors", {}).get("classification"),
        "secret_library_74032_45331": rows.get("secret_library_74032_45331", {}).get("classification"),
        "stop_rule": "Seeds remain watchlist unless they beat same-length and digit-multiset controls while improving MDL.",
    }
    lines = [
        "# Numeric Identity Key/Seed Search",
        "",
        verdict_line(result),
        "",
        "| Anchor family | Existing classification |",
        "|---|---|",
        f"| Honeminas vectors / 3478 | `{result['honeminas_primary_vectors']}` |",
        f"| Secret Library 74032 45331 | `{result['secret_library_74032_45331']}` |",
        "",
        "Numeric identity anchors are source-class and seed-watchlist material only.",
    ]
    write_result("numeric_identity_key_seed_search", result, lines)


if __name__ == "__main__":
    main()
