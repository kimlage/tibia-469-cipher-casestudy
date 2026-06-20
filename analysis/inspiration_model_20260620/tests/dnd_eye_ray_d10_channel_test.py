from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    k5 = load_json("analysis/eye_model_20260619/k5_eye_pair_model_results.json")
    eye5x2 = load_json("analysis/eye_model_20260619/eye_state_5x2_model_results.json")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "dnd_eye_ray_d10_channel_test",
        "hypothesis": "H19: D&D Beholder eye-ray structure inspired a 10-channel digit system.",
        "classification": "weak_clue",
        "translation_delta": "NONE",
        "metric": "existing K5/5x2 eye-channel searches vs label controls",
        "k5_label_accuracy": k5["best_label_rule"]["accuracy"],
        "k5_label_gain_p": k5["controls"]["label_gain_p"],
        "eye_state_5x2_label_accuracy": eye5x2["best_label_rule"]["accuracy"],
        "eye_state_5x2_label_gain_p": eye5x2["controls"]["label_gain_p"],
        "stop_rule": "Reject as origin formula unless it beats digit/order controls and reduces lookup cost.",
    }
    lines = [
        "# D&D Eye-Ray d10 Channel Test",
        "",
        verdict_line(result),
        "",
        "| Input | Result |",
        "|---|---:|",
        f"| K5 label accuracy | {result['k5_label_accuracy']:.3f} |",
        f"| K5 label gain p | {result['k5_label_gain_p']:.3f} |",
        f"| 5x2 label accuracy | {result['eye_state_5x2_label_accuracy']:.3f} |",
        f"| 5x2 label gain p | {result['eye_state_5x2_label_gain_p']:.3f} |",
        "",
        "The Beholder 10-channel analogy remains useful as a source-inspiration clue,",
        "but existing controlled eye models do not derive the row0 pair labels.",
    ]
    write_result("dnd_eye_ray_d10_channel_test", result, lines)


if __name__ == "__main__":
    main()
