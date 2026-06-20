from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    surface = load_json("analysis/generator_search_20260618/directed_pair_surface_results.json")
    orientation = load_json("analysis/generator_search_20260618/orientation_render_rule_results.json")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "subjective_viewer_render_transform_suite",
        "classification": "accepted_mechanical",
        "translation_delta": "NONE",
        "metric": "mirror-copy lower surface, directed exception, book/pair holdout orientation",
        "directed_surface_classification": surface["conclusion"]["classification"],
        "book_holdout_best_accuracy": orientation["book_holdout"]["rows"][0]["accuracy"],
        "book_holdout_best_model": orientation["book_holdout"]["rows"][0]["model"],
        "pair_holdout_best_accuracy": orientation["pair_holdout"]["rows"][0]["accuracy"],
        "pair_holdout_best_model": orientation["pair_holdout"]["rows"][0]["model"],
        "stop_rule": "Accepted only as render/orientation layer; rejected as matrix-origin formula.",
    }
    lines = [
        "# Subjective-Viewer Render Transform Suite",
        "",
        verdict_line(result),
        "",
        "| Check | Result |",
        "|---|---|",
        f"| directed surface | `{result['directed_surface_classification']}` |",
        f"| book holdout best | `{result['book_holdout_best_model']}` at {result['book_holdout_best_accuracy']:.3f} |",
        f"| pair holdout best | `{result['pair_holdout_best_model']}` at {result['pair_holdout_best_accuracy']:.3f} |",
        "",
        "This is accepted as a mechanical render/orientation layer, not as a new",
        "translation path or pair-label formula.",
    ]
    write_result("subjective_viewer_render_transform_suite", result, lines)


if __name__ == "__main__":
    main()
