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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_formula_469.json"
)
GATE55_RESULT = TEST_RESULTS / "55_targetmax_resegmentation_saturation_gate.json"
GATE42_SCRIPT = HERE / "scripts" / "42_full_corpus_source_substitution_frontier_gate.py"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_bits"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def patch_output_formula_metadata(result: dict[str, Any]) -> None:
    output = result.get("candidate_output_formula")
    if not output:
        return
    path = ROOT / output
    formula = load_json(path)
    formula["classification"] = result["classification"]
    formula["source_formula"] = rel(SOURCE_FORMULA)
    compile_info = formula.setdefault(
        "post_targetmax_source_substitution_frontier_compile", {}
    )
    compile_info.update(
        {
            "source": "56_post_targetmax_source_substitution_frontier_gate",
            "previous_gate": rel(GATE55_RESULT),
            "best_gain_bits": result["summary"]["candidate_gain_bits"],
            "best_arity": result["summary"]["best_arity"],
            "substitutions": result["summary"]["best_substitutions"],
            "active_total_bits": result["summary"]["active_total_bits"],
            "candidate_total_bits": result["summary"]["candidate_total_bits"],
        }
    )
    formula["policy"] = {
        **formula["policy"],
        "post_targetmax_source_substitution_frontier": {
            "source": "56_post_targetmax_source_substitution_frontier_gate",
            "scope": "single and pair same-chunk legal source substitutions after target-max saturation; segmentation and copy lengths fixed",
            "adaptive_rescore": True,
        },
    }
    formula["mdl_estimate_rough"][OUT_TOTAL_KEY] = result["summary"][
        "candidate_total_bits"
    ]
    formula["mdl_estimate_rough"][
        f"previous_{ACTIVE_TOTAL_KEY}"
    ] = result["summary"]["active_total_bits"]
    formula["mdl_estimate_rough"][
        "gain_vs_previous_targetmax_saturated_bits"
    ] = result["summary"]["candidate_gain_bits"]
    formula["boundary"] = {
        **formula["boundary"],
        "translation_delta": "NONE",
        "row0_origin_changed": False,
        "semantic_delta": "NONE",
        "authorial_intent_claim": False,
    }
    path.write_text(json.dumps(formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_result() -> dict[str, Any]:
    gate55 = load_json(GATE55_RESULT)
    assert_boundary("targetmax_resegmentation_saturation_gate", gate55)
    gate42 = load_module("gate42_source_substitution_frontier", GATE42_SCRIPT)
    gate42.SOURCE_FORMULA = SOURCE_FORMULA
    gate42.OUT_FORMULA = OUT_FORMULA
    gate42.GATE41_RESULT = GATE55_RESULT
    gate42.ACTIVE_TOTAL_KEY = ACTIVE_TOTAL_KEY
    gate42.OUT_TOTAL_KEY = OUT_TOTAL_KEY

    result = gate42.make_result()
    result["schema"] = "post_targetmax_source_substitution_frontier_gate.v1"
    result["inputs"] = {
        "source_formula": rel(SOURCE_FORMULA),
        "books_digits": rel(gate42.BOOKS_DIGITS),
        "gate55_result": rel(GATE55_RESULT),
    }
    result["scope"]["starts_after_targetmax_saturation"] = True
    result["scope"]["starts_from_bound_bits"] = result["summary"]["active_total_bits"]
    result["summary"]["previous_bound_bits"] = result["summary"]["active_total_bits"]
    result["decision"]["recipe_discovery_status"] = (
        "fixed_recipe_post_targetmax_source_substitution_frontier_tested"
    )
    if result["summary"]["candidate_gain_bits"] > 0:
        result["classification"] = (
            "post_targetmax_source_substitution_frontier_improves_bound"
        )
        result["decision"][
            "compression_bound_status"
        ] = "improved_by_post_targetmax_source_substitution"
    else:
        result["classification"] = (
            "post_targetmax_source_substitution_frontier_closed"
        )
        result["decision"][
            "compression_bound_status"
        ] = "unchanged_targetmax_saturated_bound"
    result["decision"][
        "generation_explanation_status"
    ] = "fixed_recipe_source_frontier_after_resegmentation"
    result["decision"]["row0_origin_status"] = "unchanged_exogenous"
    result["decision"]["translation_or_plaintext_status"] = "NONE"
    patch_output_formula_metadata(result)
    return result


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "56_post_targetmax_source_substitution_frontier_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Post-Target-Max Source Substitution Frontier Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 55 saturated the local target-max resegmentation frontier. This",
        "gate asks whether that resegmentation changed the adaptive source stream",
        "enough to reopen the exact single/pair same-chunk source-substitution",
        "frontier. Segmentation and copy lengths remain fixed.",
        "",
        "## Summary",
        "",
        f"- Active total bits: `{s['active_total_bits']:.6f}`.",
        f"- Candidate total bits: `{s['candidate_total_bits']:.6f}`.",
        f"- Candidate gain: `{s['candidate_gain_bits']:+.6f}` bits.",
        f"- Active copy-source bits: `{s['active_copy_source_bits']:.6f}`.",
        f"- Candidate copy-source bits: `{s['candidate_copy_source_bits']:.6f}`.",
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
            f"`{row['candidate_source']}` | `{row['gain_bits']:+.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a post-resegmentation source frontier. A positive result updates",
            "only the mechanical compression bound; it does not derive row0, change",
            "segmentation, change copy lengths, or add semantics.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Recipe segmentation and copy lengths remain fixed.",
            "- Triple and higher-order source substitutions are outside this gate.",
        ]
    )
    (TEST_RESULTS / "56_post_targetmax_source_substitution_frontier_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
