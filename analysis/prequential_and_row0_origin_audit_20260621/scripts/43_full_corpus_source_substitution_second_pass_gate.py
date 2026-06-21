from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_second_pass_formula_469.json"
)
GATE42_RESULT = TEST_RESULTS / "42_full_corpus_source_substitution_frontier_gate.json"
GATE42_SCRIPT = HERE / "scripts" / "42_full_corpus_source_substitution_frontier_gate.py"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_second_pass_bits"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_result() -> dict[str, Any]:
    gate42 = load_module("gate42_source_substitution_frontier", GATE42_SCRIPT)
    gate42.SOURCE_FORMULA = SOURCE_FORMULA
    gate42.OUT_FORMULA = OUT_FORMULA
    gate42.GATE41_RESULT = GATE42_RESULT
    gate42.ACTIVE_TOTAL_KEY = ACTIVE_TOTAL_KEY
    gate42.OUT_TOTAL_KEY = OUT_TOTAL_KEY

    result = gate42.make_result()
    result["schema"] = "full_corpus_source_substitution_second_pass_gate.v1"
    result["inputs"] = {
        "source_formula": rel(SOURCE_FORMULA),
        "books_digits": rel(gate42.BOOKS_DIGITS),
        "gate42_result": rel(GATE42_RESULT),
    }
    result["scope"]["pass"] = 2
    result["scope"]["starts_from_bound_bits"] = result["summary"]["active_total_bits"]
    result["summary"]["previous_bound_bits"] = result["summary"]["active_total_bits"]
    result["decision"]["recipe_discovery_status"] = (
        "fixed_recipe_second_pass_source_substitution_frontier_tested"
    )
    if result["summary"]["candidate_gain_bits"] > 0:
        result["classification"] = (
            "full_corpus_source_substitution_second_pass_improves_bound"
        )
        result["decision"][
            "compression_bound_status"
        ] = "improved_by_second_pass_source_substitution"
    else:
        result["classification"] = (
            "full_corpus_source_substitution_second_pass_frontier_closed"
        )
        result["decision"][
            "compression_bound_status"
        ] = "unchanged_8160_827_source_substitution_bound"
    return result


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "43_full_corpus_source_substitution_second_pass_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full-Corpus Source Substitution Second-Pass Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 42 promoted a single/pair source-substitution improvement. This gate",
        "reruns the exact same local frontier on the promoted `8160.827` bit formula",
        "to test whether another single or pair same-chunk source substitution remains.",
        "Segmentation and copy lengths remain fixed.",
        "",
        "## Summary",
        "",
        f"- Active total bits: `{s['active_total_bits']:.3f}`.",
        f"- Candidate total bits: `{s['candidate_total_bits']:.3f}`.",
        f"- Candidate gain: `{s['candidate_gain_bits']:+.3f}` bits.",
        f"- Active copy-source bits: `{s['active_copy_source_bits']:.3f}`.",
        f"- Candidate copy-source bits: `{s['candidate_copy_source_bits']:.3f}`.",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Candidate source options: `{s['candidate_source_option_count']}`.",
        f"- Single substitutions searched: `{s['single_substitution_count']}`.",
        f"- Positive singles: `{s['positive_single_count']}`.",
        f"- Pair substitutions searched: `{s['pair_substitution_count']}`.",
        f"- Positive pairs: `{s['positive_pair_count']}`.",
        f"- Best arity: `{s['best_arity']}`.",
    ]
    if result["candidate_output_formula"]:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [{Path(result['candidate_output_formula']).name}](../../../authorial_mechanism_20260620/{Path(result['candidate_output_formula']).name})",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Substitutions",
            "",
            "| Event | Book | Op | Length | Old source | New source | Gain bits |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in s["best_substitutions"]:
        lines.append(
            f"| `{row['event_index']}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['length']}` | `{row['original_source']}` | "
            f"`{row['candidate_source']}` | `{row['gain_bits']:+.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is still a fixed-recipe local frontier. It can promote another",
            "compression-bound step only if a second-pass single or pair source",
            "substitution survives the full adaptive source-stream rescore.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Recipe segmentation and copy lengths remain fixed.",
            "- Triple and higher-order source substitutions are outside this gate.",
        ]
    )
    (TEST_RESULTS / "43_full_corpus_source_substitution_second_pass_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
