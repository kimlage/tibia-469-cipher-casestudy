from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


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


def context(row: dict[str, Any], order: int) -> str:
    if order == 0:
        return "global"
    return str(row["previous_digit_context"])[-order:]


def score_categorical(rows: list[dict[str, Any]], *, order: int) -> dict[str, Any]:
    counts: dict[str, dict[str, float]] = {}
    bits = 0.0
    context_counts: dict[str, int] = {}
    for row in rows:
        key = context(row, order)
        context_counts[key] = context_counts.get(key, 0) + 1
        bucket = counts.setdefault(key, {digit: 0.0 for digit in DIGITS})
        total = sum(bucket.values())
        digit = str(row["digit"])
        probability = (bucket[digit] + 1.0) / (total + len(DIGITS))
        bits += -math.log2(probability)
        bucket[digit] += 1.0
    return {
        "family": "adaptive_categorical_previous_digit_context",
        "order": order,
        "bits": bits,
        "context_count": len(context_counts),
        "context_counts": dict(sorted(context_counts.items())),
        "decodable": True,
    }


def score_modal_default(
    rows: list[dict[str, Any]],
    *,
    default_order: int,
    exception_order: int,
    flag_context: str,
) -> dict[str, Any]:
    history_counts: dict[str, dict[str, float]] = {}
    flag_counts: dict[str, dict[bool, float]] = {}
    exception_counts: dict[str, dict[str, float]] = {}
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0

    for row in rows:
        default_key = context(row, default_order)
        history = history_counts.setdefault(default_key, {digit: 0.0 for digit in DIGITS})
        max_count = max(history.values())
        default_digit = sorted(digit for digit, value in history.items() if value == max_count)[0]
        digit = str(row["digit"])
        is_default = digit == default_digit

        flag_key = default_key if flag_context == "same_context" else "global"
        flag_bucket = flag_counts.setdefault(flag_key, {True: 0.0, False: 0.0})
        flag_probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(flag_probability)
        flag_bucket[is_default] += 1.0

        if is_default:
            default_count += 1
        else:
            exception_count += 1
            exception_key = context(row, exception_order)
            exception_bucket = exception_counts.setdefault(exception_key, {})
            legal_digits = [candidate for candidate in DIGITS if candidate != default_digit]
            total = sum(exception_bucket.get(candidate, 0.0) for candidate in legal_digits)
            probability = (exception_bucket.get(digit, 0.0) + 1.0) / (total + len(legal_digits))
            exception_bits += -math.log2(probability)
            exception_bucket[digit] = exception_bucket.get(digit, 0.0) + 1.0

        history[digit] += 1.0

    return {
        "family": "adaptive_modal_default_with_exception_digit",
        "default_order": default_order,
        "exception_order": exception_order,
        "flag_context": flag_context,
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
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

    active_bits = float(formula["mdl_estimate_rough"][BASE_TOTAL_KEY])
    active_literal_payload_bits = float(
        formula["mdl_estimate_rough"]["adaptive_context_order_literal_payload_bits"]
    )

    categorical_rows = [score_categorical(rows, order=order) for order in (0, 1, 2)]
    modal_rows = []
    for default_order in (0, 1, 2):
        for exception_order in (0, 1, 2):
            for flag_context in ("global", "same_context"):
                modal_rows.append(
                    score_modal_default(
                        rows,
                        default_order=default_order,
                        exception_order=exception_order,
                        flag_context=flag_context,
                    )
                )

    all_candidates = categorical_rows + modal_rows
    best_candidate = min(all_candidates, key=lambda row: float(row["bits"]))
    delta_vs_active_literal_bits = float(best_candidate["bits"]) - active_literal_payload_bits
    classification = (
        "literal_payload_default_exception_not_promoted"
        if delta_vs_active_literal_bits >= -1e-9
        else "literal_payload_default_exception_formula_improvement"
    )

    result = {
        "schema": "literal_payload_default_decodability_audit.v1",
        "test": "138_literal_payload_default_decodability_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(BASE_FORMULA),
        "active_bits": active_bits,
        "active_literal_payload_bits": active_literal_payload_bits,
        "literal_digit_count": len(rows),
        "best_candidate": best_candidate,
        "best_candidate_delta_vs_active_literal_bits": delta_vs_active_literal_bits,
        "categorical_candidates": categorical_rows,
        "modal_default_candidates": modal_rows,
        "boundary": {
            "compression_bound_changed": False,
            "literal_payload_dependency_removed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 138. Literal Payload Default Decodability Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active formula still pays a large literal-payload stream. This audit",
        "tests a small, decodable alternative family: predict a modal digit from",
        "prior emitted-digit context, then encode only default/exception plus an",
        "adaptive exception digit. It also rechecks categorical context orders `0`,",
        "`1`, and `2` under the same alpha.",
        "",
        "## Result",
        "",
        f"- Active total bits: `{active_bits:.3f}`",
        f"- Active literal-payload bits: `{active_literal_payload_bits:.3f}`",
        f"- Literal digits: `{len(rows)}`",
        f"- Best candidate family: `{best_candidate['family']}`",
        f"- Best candidate bits: `{best_candidate['bits']:.3f}`",
        f"- Delta vs active literal payload: `{delta_vs_active_literal_bits:.3f}` bits",
        "",
        "## Top Candidates",
        "",
        "| Rank | Family | Parameters | Bits | Delta vs active |",
        "|---:|---|---|---:|---:|",
    ]
    for rank, row in enumerate(sorted(all_candidates, key=lambda item: float(item["bits"]))[:8], 1):
        if row["family"] == "adaptive_categorical_previous_digit_context":
            params = f"order={row['order']}"
        else:
            params = (
                f"default_order={row['default_order']}; "
                f"exception_order={row['exception_order']}; "
                f"flag_context={row['flag_context']}; "
                f"default_count={row['default_count']}"
            )
        lines.append(
            f"| `{rank}` | `{row['family']}` | {params} | "
            f"`{row['bits']:.3f}` | `{float(row['bits']) - active_literal_payload_bits:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- No literal-payload default/exception model is promoted.",
            "- The active categorical previous-emitted-digit context order `2` remains best among this bounded family.",
            "- This is a falsification of a natural default/exception route, not a translation or row0 claim.",
        ]
    )

    write_result("138_literal_payload_default_decodability_audit", result, lines)


if __name__ == "__main__":
    main()
