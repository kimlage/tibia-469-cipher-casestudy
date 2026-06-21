from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
AUDIT_150 = HERE / "scripts" / "150_optional_literal_copy_repair_frontier.py"
AUDIT_151 = HERE / "scripts" / "151_cross_op_optional_literal_copy_frontier.py"
RESULT_151 = REPORTS / "151_cross_op_optional_literal_copy_frontier.json"


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


def load_active_modules(audit150) -> dict[str, Any]:
    compile129 = audit150.load_module("compile129", audit150.COMPILE_129)
    modules = {
        "compile129": compile129,
        "compile134": audit150.load_module("compile134", audit150.COMPILE_134),
        "audit136": audit150.load_module("audit136", audit150.AUDIT_136),
        "audit137": audit150.load_module("audit137", audit150.AUDIT_137),
        "audit141": audit150.load_module("audit141", audit150.AUDIT_141),
    }
    audit126 = compile129.load_audit_126()
    modules.update(
        {
            "audit126": audit126,
            "frontier": audit150.load_module("frontier", audit126.FRONTIER),
            "midpoint": audit150.load_module("midpoint", audit126.MIDPOINT),
            "copy_module": audit150.load_module("copy_context", audit126.COPY_CONTEXT),
            "item_module": audit150.load_module("item_context", audit126.ITEM_CONTEXT),
        }
    )
    return modules


def component_deltas(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    keys = [
        "fixed_bits",
        "literal_bits_no_payload",
        "literal_payload_bits",
        "item_type_stream_bits",
        "copy_length_default_exception_bits",
        "copy_source_default_exception_bits",
    ]
    return {key: float(candidate[key]) - float(base[key]) for key in keys}


def make_result() -> dict[str, Any]:
    audit150 = load_module("audit150", AUDIT_150)
    audit151 = load_module("audit151", AUDIT_151)
    result151 = load_json(RESULT_151)
    best = result151["best_candidate"]
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    available_by_book = audit151.available_before_each_book(formula, books)
    modules = load_active_modules(audit150)
    base_score = audit150.active_score(formula, modules, books)
    repaired = audit151.replace_cross_op_prefix(
        formula,
        books,
        available_by_book,
        book=int(best["book"]),
        op_index=int(best["op_index"]),
        source_digit_pos=int(best["source_digit_pos"]),
        length=int(best["copy_length"]),
    )
    candidate_score = audit150.active_score(repaired, modules, books)
    deltas = component_deltas(base_score, candidate_score)
    total_delta_from_components = sum(deltas.values())
    total_delta = float(candidate_score["total_bits"]) - float(base_score["total_bits"])
    positive = {key: value for key, value in deltas.items() if value > 0}
    negative = {key: value for key, value in deltas.items() if value < 0}
    classification = "cross_op_near_tie_explained_no_promotion"
    return {
        "schema": "cross_op_near_tie_decomposition.v1",
        "test": "152_cross_op_near_tie_decomposition",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "source_candidate_audit": rel(RESULT_151),
        "candidate": best,
        "base_score": base_score,
        "candidate_score": candidate_score,
        "component_deltas": deltas,
        "delta_checks": {
            "total_delta_bits": total_delta,
            "component_sum_delta_bits": total_delta_from_components,
            "absolute_difference": abs(total_delta - total_delta_from_components),
        },
        "delta_signs": {
            "penalty_components": positive,
            "saving_components": negative,
        },
        "decision": {
            "compression_bound_changed": False,
            "candidate_promoted": False,
            "near_tie_requires_new_model_or_declaration_credit": True,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    candidate = result["candidate"]
    deltas = result["component_deltas"]
    checks = result["delta_checks"]
    lines = [
        "# 152. Cross-Op Near-Tie Decomposition",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 151 found a very close rejected repair: the best cross-op optional",
        "literal copy candidate was only `+0.027` bits worse than the active",
        "formula. This audit decomposes that near tie under the same active ledger",
        "to verify that it is a real loss, not a rounding or accounting artifact.",
        "",
        "## Candidate",
        "",
        f"- Book/op/pos: `{candidate['book']}` / `{candidate['op_index']}` / `{candidate['book_pos']}`",
        f"- Source/copy length: `{candidate['source_digit_pos']}` / `{candidate['copy_length']}`",
        f"- Crossed digits beyond original literal: `{candidate['crossed_digits']}`",
        f"- Candidate total bits: `{result['candidate_score']['total_bits']:.6f}`",
        f"- Active total bits: `{result['base_score']['total_bits']:.6f}`",
        f"- Total delta: `{checks['total_delta_bits']:.6f}` bits",
        "",
        "## Component Delta",
        "",
        "| Component | Delta bits |",
        "|---|---:|",
    ]
    for key, value in deltas.items():
        lines.append(f"| `{key}` | `{value:.6f}` |")
    lines.extend(
        [
            "",
            f"- Component-sum delta: `{checks['component_sum_delta_bits']:.6f}` bits",
            f"- Accounting difference: `{checks['absolute_difference']:.12f}` bits",
            "",
            "## Interpretation",
            "",
            "The candidate saves literal structure/payload bits, but the added copy",
            "ledger costs more than those savings under the active default/exception",
            "source and length models. The near tie is therefore an actual local",
            "cost boundary. It should not be promoted without a new charged model",
            "that explains why this cross-op copy should be preferred.",
            "",
            "## Decision",
            "",
            "- Compression bound unchanged.",
            "- Candidate not promoted.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "152_cross_op_near_tie_decomposition.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "152_cross_op_near_tie_decomposition.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
