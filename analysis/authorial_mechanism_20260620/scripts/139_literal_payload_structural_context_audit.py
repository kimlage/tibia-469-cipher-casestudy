from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BASE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
)
COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
DIGITS = [str(index) for index in range(10)]


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


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def previous_context(row: dict[str, Any], order: int) -> str:
    if order == 0:
        return "global"
    return str(row["previous_digit_context"])[-order:]


def offset_first_rest(row: dict[str, Any]) -> str:
    return "first" if int(row["literal_offset"]) == 0 else "rest"


def offset_bucket(row: dict[str, Any]) -> str:
    offset = int(row["literal_offset"])
    if offset == 0:
        return "o0"
    if offset == 1:
        return "o1"
    if offset == 2:
        return "o2"
    return "o3p"


def run_length_bucket(row: dict[str, Any]) -> str:
    length = int(row["literal_run_length"])
    if length == 1:
        return "len1"
    if length <= 5:
        return "len2_5"
    if length <= 20:
        return "len6_20"
    return "len21p"


def book_half(row: dict[str, Any]) -> str:
    return "first_half" if int(row["book_int"]) < 35 else "second_half"


def book_parity(row: dict[str, Any]) -> str:
    return f"book_parity_{int(row['book_int']) % 2}"


def score_candidate(
    rows: list[dict[str, Any]],
    *,
    label: str,
    declaration_bits: float,
    key_fn: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    counts: dict[Any, dict[str, float]] = {}
    bits = 0.0
    for row in rows:
        key = key_fn(row)
        bucket = counts.setdefault(key, {digit: 0.0 for digit in DIGITS})
        total = sum(bucket.values())
        digit = str(row["digit"])
        probability = (bucket[digit] + 1.0) / (total + len(DIGITS))
        bits += -math.log2(probability)
        bucket[digit] += 1.0
    return {
        "label": label,
        "stream_bits": bits,
        "declaration_bits": declaration_bits,
        "total_bits": bits + declaration_bits,
        "context_count": len(counts),
        "decodable": True,
    }


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = compile129.load_audit_126()
    payload_module = load_module("payload_context", audit126.PAYLOAD_CONTEXT)

    formula = load_json(BASE_FORMULA)
    normalized = compile134.normalize_ops(formula)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    rows = payload_module.collect_literal_digit_rows(normalized, books)
    active_total_bits = float(formula["mdl_estimate_rough"][BASE_TOTAL_KEY])
    active_literal_payload_bits = float(
        formula["mdl_estimate_rough"]["adaptive_context_order_literal_payload_bits"]
    )

    candidates = [
        score_candidate(
            rows,
            label="active_prev2",
            declaration_bits=0.0,
            key_fn=lambda row: previous_context(row, 2),
        ),
        score_candidate(
            rows,
            label="prev2_plus_offset_first_rest",
            declaration_bits=4.0,
            key_fn=lambda row: (previous_context(row, 2), offset_first_rest(row)),
        ),
        score_candidate(
            rows,
            label="prev2_plus_offset_4bucket",
            declaration_bits=6.0,
            key_fn=lambda row: (previous_context(row, 2), offset_bucket(row)),
        ),
        score_candidate(
            rows,
            label="prev2_plus_run_length_bucket",
            declaration_bits=6.0,
            key_fn=lambda row: (previous_context(row, 2), run_length_bucket(row)),
        ),
        score_candidate(
            rows,
            label="prev2_plus_book_half",
            declaration_bits=4.0,
            key_fn=lambda row: (previous_context(row, 2), book_half(row)),
        ),
        score_candidate(
            rows,
            label="prev2_plus_book_parity",
            declaration_bits=4.0,
            key_fn=lambda row: (previous_context(row, 2), book_parity(row)),
        ),
        score_candidate(
            rows,
            label="prev2_plus_half_plus_offset_first_rest",
            declaration_bits=8.0,
            key_fn=lambda row: (
                previous_context(row, 2),
                book_half(row),
                offset_first_rest(row),
            ),
        ),
        score_candidate(
            rows,
            label="prev1_plus_offset_first_rest",
            declaration_bits=4.0,
            key_fn=lambda row: (previous_context(row, 1), offset_first_rest(row)),
        ),
        score_candidate(
            rows,
            label="global_plus_offset_first_rest",
            declaration_bits=4.0,
            key_fn=lambda row: ("global", offset_first_rest(row)),
        ),
    ]
    best = min(candidates, key=lambda row: float(row["total_bits"]))
    delta_vs_active = float(best["total_bits"]) - active_literal_payload_bits
    classification = (
        "literal_payload_structural_context_not_promoted"
        if delta_vs_active >= -1e-9
        else "literal_payload_structural_context_formula_improvement"
    )

    result = {
        "schema": "literal_payload_structural_context_audit.v1",
        "test": "139_literal_payload_structural_context_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(BASE_FORMULA),
        "active_total_bits": active_total_bits,
        "active_literal_payload_bits": active_literal_payload_bits,
        "literal_digit_count": len(rows),
        "best_candidate": best,
        "best_candidate_delta_vs_active_literal_bits": delta_vs_active,
        "candidates": candidates,
        "boundary": {
            "compression_bound_changed": False,
            "literal_payload_dependency_removed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 139. Literal Payload Structural Context Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 138 rejected modal default/exception literal payload models. This",
        "audit tests a separate bounded family: whether structural context inside",
        "literal runs improves the active previous-emitted-digit order-2 payload",
        "model. Tested contexts include literal-run offset, run-length bucket, book",
        "half/parity, and small combinations with the active `prev2` context.",
        "",
        "## Result",
        "",
        f"- Active total bits: `{active_total_bits:.3f}`",
        f"- Active literal-payload bits: `{active_literal_payload_bits:.3f}`",
        f"- Literal digits: `{len(rows)}`",
        f"- Best candidate: `{best['label']}`",
        f"- Best candidate bits: `{best['total_bits']:.3f}`",
        f"- Delta vs active literal payload: `{delta_vs_active:.3f}` bits",
        "",
        "| Rank | Candidate | Contexts | Stream bits | Decl bits | Total bits | Delta vs active |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(sorted(candidates, key=lambda item: float(item["total_bits"])), 1):
        lines.append(
            f"| `{rank}` | `{row['label']}` | `{row['context_count']}` | "
            f"`{row['stream_bits']:.3f}` | `{row['declaration_bits']:.1f}` | "
            f"`{row['total_bits']:.3f}` | "
            f"`{float(row['total_bits']) - active_literal_payload_bits:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- No structural literal-payload context is promoted.",
            "- Literal-run offset, run-length bucket, book half/parity, and their bounded combinations all over-split the literal stream.",
            "- The active categorical previous-emitted-digit order-2 model remains the best tested literal-payload mechanism.",
            "- `translation_delta`: `NONE`; row0/table origin is unchanged.",
        ]
    )

    write_result("139_literal_payload_structural_context_audit", result, lines)


if __name__ == "__main__":
    main()
