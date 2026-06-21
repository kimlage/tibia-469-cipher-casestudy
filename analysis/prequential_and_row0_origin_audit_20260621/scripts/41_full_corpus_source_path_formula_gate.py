from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_137 = AUTHORIAL / "scripts" / "137_copy_source_default_decodability_audit.py"
GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE39_SCRIPT = HERE / "scripts" / "39_multicutoff_source_choice_optimizer_gate.py"
GATE40_SCRIPT = HERE / "scripts" / "40_multicutoff_global_source_path_optimizer_gate.py"
GATE40_RESULT = TEST_RESULTS / "40_multicutoff_global_source_path_optimizer_gate.json"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_bits"
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
    if decision.get("row0_origin_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced plaintext status")


def build_formula_copy_events(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    gate39,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append({"book": int(book), "op_index": op_index, "type": "literal_mismatch"})
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                errors.append({"book": int(book), "op_index": op_index, "type": "bad_op"})
                continue

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            legal_source_count = max(1, len(emitted) - min_len + 1)
            chunk = emitted[source : source + length]
            if target[book_pos : book_pos + length] != chunk:
                errors.append({"book": int(book), "op_index": op_index, "type": "copy_mismatch"})
            candidates = gate39.legal_sources_for_chunk(
                emitted=emitted,
                chunk=chunk,
                legal_source_count=legal_source_count,
            )
            if source not in candidates:
                candidates.append(source)
            candidates = sorted(set(candidates))
            events.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "length": length,
                    "original_source": source,
                    "legal_source_count": legal_source_count,
                    "candidates": candidates,
                }
            )
            emitted += chunk
            book_pos += length
        if book_pos != len(target):
            errors.append(
                {
                    "book": int(book),
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )
    return {"events": events, "errors": errors}


def apply_source_choices(formula: dict[str, Any], choices: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = copy.deepcopy(formula)
    for choice in choices:
        if not choice["source_changed"]:
            continue
        book = str(choice["book"])
        op_index = int(choice["op_index"])
        candidate["book_recipes"][book]["ops"][op_index]["source_digit_pos"] = int(
            choice["source_digit_pos"]
        )
    return candidate


def score_source_formula(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    audit137,
) -> dict[str, Any]:
    collected = audit137.collect_source_rows(formula, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    model = audit137.score_source_default_exception(collected["rows"])
    return {
        "rows": collected["rows"],
        "model": model,
        "copy_source_bits": float(model["stream_bits"]) + 12.0,
    }


def make_result() -> dict[str, Any]:
    gate40_result = load_json(GATE40_RESULT)
    assert_boundary("multicutoff_global_source_path_optimizer_gate", gate40_result)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit137 = load_module("audit137", AUDIT_137)
    gate37 = load_module("gate37_source_state_reprice", GATE37_SCRIPT)
    gate39 = load_module("gate39_source_choice", GATE39_SCRIPT)
    gate40 = load_module("gate40_global_source_path", GATE40_SCRIPT)

    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    active_total_bits = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    active_copy_source_bits = float(
        formula["mdl_estimate_rough"]["copy_source_default_exception_bits"]
    )
    active_score = score_source_formula(formula=formula, books=books, audit137=audit137)
    if not math.isclose(active_score["copy_source_bits"], active_copy_source_bits, abs_tol=1e-9):
        raise RuntimeError(
            {
                "type": "active_source_rescore_mismatch",
                "rescored": active_score["copy_source_bits"],
                "formula": active_copy_source_bits,
            }
        )

    event_data = build_formula_copy_events(formula=formula, books=books, gate39=gate39)
    if event_data["errors"]:
        raise RuntimeError(event_data["errors"])
    max_source_count = sum(len(text) for text in books.values()) + 1
    frozen_counts = gate37.source_counts(
        active_score["rows"],
        max_source_count=max_source_count,
    )
    optimized = gate40.optimize_source_path(
        events=event_data["events"],
        initial_previous_end=None,
        source_train_counts=frozen_counts,
        gate37=gate37,
    )
    original_frozen = gate40.original_reprice_for_events(
        events=event_data["events"],
        initial_previous_end=None,
        source_train_counts=frozen_counts,
        gate37=gate37,
    )
    candidate_formula = apply_source_choices(formula, optimized["choices"])
    candidate_score = score_source_formula(
        formula=candidate_formula,
        books=books,
        audit137=audit137,
    )
    candidate_copy_source_bits = candidate_score["copy_source_bits"]
    candidate_total_bits = active_total_bits - active_copy_source_bits + candidate_copy_source_bits
    candidate_gain_bits = active_total_bits - candidate_total_bits
    changed_sources = [choice for choice in optimized["choices"] if choice["source_changed"]]

    classification = (
        "full_corpus_source_path_formula_improves_bound"
        if candidate_gain_bits > 0
        else "full_corpus_source_path_formula_not_promoted"
    )
    output_formula = None
    if candidate_gain_bits > 0:
        candidate_formula["classification"] = classification
        candidate_formula["source_formula"] = rel(SOURCE_FORMULA)
        candidate_formula["source_path_optimization_compile"] = {
            "optimizer": "frozen-count exact DP candidate, adaptively rescored source stream",
            "changed_source_count": len(changed_sources),
            "copy_event_count": len(event_data["events"]),
            "frozen_source_bits": optimized["source_bits"],
            "original_frozen_source_bits": original_frozen["source_bits"],
            "frozen_source_delta_bits": optimized["source_bits"] - original_frozen["source_bits"],
            "adaptive_candidate_copy_source_bits": candidate_copy_source_bits,
            "adaptive_active_copy_source_bits": active_copy_source_bits,
            "candidate_gain_bits": candidate_gain_bits,
            "max_state_count": optimized["max_state_count"],
            "transition_count": optimized["transition_count"],
        }
        candidate_formula["policy"] = {
            **candidate_formula["policy"],
            "copy_source_path_optimization": {
                "source": "41_full_corpus_source_path_formula_gate",
                "scope": "fixed recipe segmentation and copy lengths; source positions changed only among equal-chunk legal sources",
                "adaptive_rescore": True,
            },
        }
        candidate_formula["mdl_estimate_rough"] = {
            **candidate_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_total_bits,
            "previous_active_source_default_exception_bits": active_total_bits,
            "gain_vs_previous_active_source_default_exception_bits": candidate_gain_bits,
            "copy_source_path_optimized_bits": candidate_copy_source_bits,
            "copy_source_path_optimized_stream_bits": candidate_score["model"]["stream_bits"],
            "copy_source_path_optimized_flag_bits": candidate_score["model"]["flag_bits"],
            "copy_source_path_optimized_source_bits": candidate_score["model"][
                "exception_source_bits"
            ],
            "copy_source_default_exception_bits": candidate_copy_source_bits,
            "copy_source_default_exception_stream_bits": candidate_score["model"]["stream_bits"],
            "copy_source_default_exception_flag_bits": candidate_score["model"]["flag_bits"],
            "copy_source_default_exception_source_bits": candidate_score["model"][
                "exception_source_bits"
            ],
            "copy_address_bits": candidate_copy_source_bits,
        }
        candidate_formula["boundary"] = {
            **candidate_formula["boundary"],
            "translation_delta": "NONE",
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        }
        OUT_FORMULA.write_text(
            json.dumps(candidate_formula, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_formula = rel(OUT_FORMULA)

    return {
        "schema": "full_corpus_source_path_formula_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate40_result": rel(GATE40_RESULT),
        },
        "candidate_output_formula": output_formula,
        "scope": {
            "optimization": "exact DP over fixed copy-source choices under frozen full-corpus source counts, then exact adaptive rescore",
            "fixed_segmentation": True,
            "fixed_copy_lengths": True,
            "same_chunk_source_choices_only": True,
            "row0_origin_changed": False,
        },
        "summary": {
            "active_total_bits": active_total_bits,
            "candidate_total_bits": candidate_total_bits,
            "candidate_gain_bits": candidate_gain_bits,
            "active_copy_source_bits": active_copy_source_bits,
            "candidate_copy_source_bits": candidate_copy_source_bits,
            "adaptive_copy_source_delta_bits": candidate_copy_source_bits - active_copy_source_bits,
            "frozen_original_source_bits": original_frozen["source_bits"],
            "frozen_optimized_source_bits": optimized["source_bits"],
            "frozen_source_delta_bits": optimized["source_bits"] - original_frozen["source_bits"],
            "copy_event_count": len(event_data["events"]),
            "changed_source_count": len(changed_sources),
            "candidate_count": sum(len(event["candidates"]) for event in event_data["events"]),
            "source_default_count": candidate_score["model"]["default_count"],
            "source_exception_count": candidate_score["model"]["exception_count"],
            "active_source_default_count": active_score["model"]["default_count"],
            "active_source_exception_count": active_score["model"]["exception_count"],
            "max_state_count": optimized["max_state_count"],
            "transition_count": optimized["transition_count"],
            "sample_changed_sources": changed_sources[:20],
            "remaining_blockers": [
                "The candidate generator uses frozen full-corpus source counts, then verifies by adaptive rescore.",
                "Segmentation and copy lengths remain fixed; this is not a complete active parser.",
                "Row0 origin remains exogenous.",
            ],
        },
        "decision": {
            "compression_bound_status": (
                "improved_by_source_path_formula"
                if candidate_gain_bits > 0
                else "unchanged_8177_317_active_bound"
            ),
            "recipe_discovery_status": "source_path_candidate_adaptively_rescored_fixed_recipe",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "41_full_corpus_source_path_formula_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full-Corpus Source Path Formula Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 40 showed that global source-path optimization helps under frozen",
        "prefix counts. This gate tests whether the same structural idea can become",
        "a full-corpus formula improvement: generate a candidate by exact DP over",
        "same-chunk legal source choices, then rescore the candidate with the real",
        "adaptive source default/exception stream.",
        "",
        "## Summary",
        "",
        f"- Active total bits: `{s['active_total_bits']:.3f}`.",
        f"- Candidate total bits: `{s['candidate_total_bits']:.3f}`.",
        f"- Candidate gain: `{s['candidate_gain_bits']:+.3f}` bits.",
        f"- Active copy-source bits: `{s['active_copy_source_bits']:.3f}`.",
        f"- Candidate copy-source bits: `{s['candidate_copy_source_bits']:.3f}`.",
        f"- Adaptive copy-source delta: `{s['adaptive_copy_source_delta_bits']:+.3f}` bits.",
        f"- Frozen source delta used by optimizer: `{s['frozen_source_delta_bits']:+.3f}` bits.",
        f"- Changed sources: `{s['changed_source_count']}/{s['copy_event_count']}`.",
        f"- Candidate legal source options considered: `{s['candidate_count']}`.",
        f"- Active defaults/exceptions: `{s['active_source_default_count']}` / `{s['active_source_exception_count']}`.",
        f"- Candidate defaults/exceptions: `{s['source_default_count']}` / `{s['source_exception_count']}`.",
        f"- Max DP state count: `{s['max_state_count']}`.",
        f"- Total DP transitions: `{s['transition_count']}`.",
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
            "## Interpretation",
            "",
            "The optimization is accepted only if the adaptive rescore improves the",
            "full-corpus formula. The frozen-count DP is used only to propose a path;",
            "it is not itself counted as the final score.",
            "",
            "Segmentation and copy lengths remain fixed, so this does not solve the",
            "complete active parser problem.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Source choices remain explicit formula data unless derived by a future parser.",
        ]
    )
    (TEST_RESULTS / "41_full_corpus_source_path_formula_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
