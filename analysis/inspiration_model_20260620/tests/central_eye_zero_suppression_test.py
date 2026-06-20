from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    zero = load_json("analysis/generator_search_20260618/zero_compact_rule_results.json")
    selected = zero["selected_by_balanced_accuracy"]
    mdl = zero["selected_by_mdl_gain"]
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "central_eye_zero_suppression_test",
        "hypothesis": "H20: zero/omitted zero may encode a central-eye or suppression channel.",
        "classification": "weak_clue",
        "translation_delta": "NONE",
        "metric": "zero omission holdout balanced accuracy and rough MDL classification",
        "overall_classification": zero["overall_classification"],
        "selected_balanced_accuracy_model": selected["name"],
        "selected_holdout_balanced_accuracy": selected["holdout"]["balanced_accuracy"],
        "selected_mdl_model": mdl["name"],
        "selected_mdl_gain_bits": mdl["holdout_mdl_gain_vs_code_only_bits"],
        "stop_rule": "Keep as support only unless a zero/suppression rule beats code-only MDL and controls.",
    }
    lines = [
        "# Central-Eye Zero Suppression Test",
        "",
        verdict_line(result),
        "",
        f"Existing zero audit classification: `{result['overall_classification']}`.",
        "",
        "| Selected view | Model | Holdout metric |",
        "|---|---|---:|",
        f"| balanced accuracy | `{result['selected_balanced_accuracy_model']}` | {result['selected_holdout_balanced_accuracy']:.3f} |",
        f"| rough MDL gain | `{result['selected_mdl_model']}` | {result['selected_mdl_gain_bits']:.1f} bits |",
        "",
        "The D&D central-eye framing is a useful label for the existing zero/render",
        "signal, but it does not create a formula or semantic value.",
    ]
    write_result("central_eye_zero_suppression_test", result, lines)


if __name__ == "__main__":
    main()
