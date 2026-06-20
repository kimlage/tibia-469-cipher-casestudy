from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
ADAPTIVE = HERE / "scripts/79_post_adaptive_copy_length_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_adaptive_module():
    spec = importlib.util.spec_from_file_location("post_adaptive_frontier", ADAPTIVE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive module: {ADAPTIVE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def log_bucket(value: int, cap: int) -> int:
    return min(cap, int(math.floor(math.log2(max(1, value)))))


def collect_copy_rows(formula: dict, books: dict[str, str]) -> list[dict]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    rows = []
    copy_id = 0
    previous_length_index = None
    previous_same_book = None
    previous_symbol_count = None

    for book in map(str, formula["policy"]["book_order"]):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        book_start_digit = len(emitted)
        book_parts = []
        position = 0
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            remaining = book_length - position
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                target_digit_global = len(emitted)
                max_length = min(remaining, target_digit_global - source_digit_pos)
                symbol_count = max_length - min_len + 1
                length_index = length - min_len
                if symbol_count <= 0 or not 0 <= length_index < symbol_count:
                    raise RuntimeError((book, "copy_length_outside_bounds", op_index, op))
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    raise RuntimeError((book, "short_copy", op_index, op))
                same_book = source_digit_pos >= book_start_digit
                rows.append(
                    {
                        "copy_id": copy_id,
                        "book": book,
                        "book_int": int(book),
                        "op_index": op_index,
                        "target_digit_global": target_digit_global,
                        "source_digit_pos": source_digit_pos,
                        "distance": target_digit_global - source_digit_pos,
                        "same_book": same_book,
                        "remaining": remaining,
                        "length": length,
                        "max_length": max_length,
                        "symbol_count": symbol_count,
                        "length_index": length_index,
                        "previous_length_index": previous_length_index,
                        "previous_same_book": previous_same_book,
                        "previous_symbol_count": previous_symbol_count,
                    }
                )
                previous_length_index = length_index
                previous_same_book = same_book
                previous_symbol_count = symbol_count
                copy_id += 1
            else:
                raise ValueError(op)
            emitted += chunk
            book_parts.append(chunk)
            position += length
        if "".join(book_parts) != books[book]:
            raise RuntimeError(f"formula does not roundtrip book {book}")

    return rows


def adaptive_context_bits(
    rows: list[dict],
    alpha: int,
    context_fn: Callable[[dict], object],
) -> tuple[float, list[dict], dict[str, int]]:
    context_counts: dict[object, dict[int, int]] = {}
    context_totals: dict[str, int] = {}
    total_bits = 0.0
    audit_rows = []

    for row in rows:
        context = context_fn(row)
        counts = context_counts.setdefault(context, {})
        legal_observations = sum(counts.get(index, 0) for index in range(int(row["symbol_count"])))
        denominator = legal_observations + alpha * int(row["symbol_count"])
        numerator = counts.get(int(row["length_index"]), 0) + alpha
        bits = -math.log2(numerator / denominator)
        total_bits += bits
        context_label = json.dumps(context, sort_keys=True) if not isinstance(context, str) else context
        context_totals[context_label] = context_totals.get(context_label, 0) + 1
        audit_rows.append(
            {
                **row,
                "context": context_label,
                "adaptive_context_bits": bits,
                "previous_context_legal_observations": legal_observations,
                "previous_context_same_length_observations": counts.get(int(row["length_index"]), 0),
            }
        )
        length_index = int(row["length_index"])
        counts[length_index] = counts.get(length_index, 0) + 1

    return total_bits, audit_rows, context_totals


def fixed_context_declaration_bits(current_bits: int, context_count: int) -> int:
    return current_bits + 1 + gamma_bits(context_count + 1)


def searched_split_declaration_bits(current_bits: int, split_book: int, context_count: int) -> int:
    return fixed_context_declaration_bits(current_bits, context_count) + gamma_bits(split_book + 1)


def model_row(
    *,
    name: str,
    family: str,
    context_description: str,
    context_fn: Callable[[dict], object],
    rows: list[dict],
    alpha: int,
    current_length_bits: float,
    current_total_bits: float,
    fixed_nonlength_bits: float,
    current_declaration_bits: int,
    extra_declaration_bits: int | None = None,
    decodable: bool = True,
) -> dict:
    context_length_bits, audit_rows, context_counts = adaptive_context_bits(rows, alpha, context_fn)
    context_count = len(context_counts)
    declaration_bits = (
        fixed_context_declaration_bits(current_declaration_bits, context_count)
        if extra_declaration_bits is None
        else current_declaration_bits + extra_declaration_bits
    )
    total_bits = (
        fixed_nonlength_bits
        + context_length_bits
        + declaration_bits
        - current_declaration_bits
    )
    return {
        "model": name,
        "family": family,
        "context_description": context_description,
        "adaptive_copy_length_bits": context_length_bits,
        "copy_model_declaration_bits": declaration_bits,
        "context_count": context_count,
        "context_counts": context_counts,
        "total_bits": total_bits,
        "delta_vs_current_bits": total_bits - current_total_bits,
        "component_delta_bits": context_length_bits - current_length_bits,
        "declaration_delta_bits": declaration_bits - current_declaration_bits,
        "decodable": decodable,
        "audit_rows": audit_rows,
    }


def main() -> None:
    adaptive = load_adaptive_module()
    base_frontier = adaptive.load_frontier_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = adaptive.score_formula(formula, books, base_frontier)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    rows = collect_copy_rows(formula, books)
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_bits, active_audit_rows, active_context_counts = adaptive_context_bits(rows, alpha, lambda row: "global")
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))

    candidate_specs: list[tuple[str, str, str, Callable[[dict], object]]] = [
        (
            "book_midpoint_35_context",
            "fixed_book_midpoint",
            "book_id < 35 versus book_id >= 35",
            lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
        ),
        (
            "book_quartile_context",
            "fixed_book_quartile",
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_context",
            "fixed_book_decade",
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_context",
            "fixed_book_parity",
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "same_book_context",
            "source_scope",
            "same-book source versus prior-book source",
            lambda row: "same_book" if bool(row["same_book"]) else "prior_book",
        ),
        (
            "legal_symbol_count_log_context",
            "legal_length_space",
            "log bucket of legal copy-length symbol count",
            lambda row: log_bucket(int(row["symbol_count"]), 6),
        ),
        (
            "distance_log_context",
            "copy_distance",
            "log bucket of decoded copy distance",
            lambda row: log_bucket(int(row["distance"]), 12),
        ),
        (
            "remaining_log_context",
            "declared_remaining",
            "log bucket of remaining declared book length",
            lambda row: log_bucket(int(row["remaining"]), 8),
        ),
        (
            "previous_copy_length_log_context",
            "previous_copy_length",
            "previous copy length-index log bucket",
            lambda row: "start"
            if row["previous_length_index"] is None
            else log_bucket(int(row["previous_length_index"]) + 1, 6),
        ),
        (
            "copy_index_midpoint_context",
            "copy_index_midpoint",
            "first half versus second half of the copy-item stream",
            lambda row: "first_copy_half" if int(row["copy_id"]) < len(rows) / 2 else "second_copy_half",
        ),
    ]

    models = [
        {
            "model": "active_global_copy_length_context",
            "family": "active_global",
            "context_description": "single global adaptive copy-length prior",
            "adaptive_copy_length_bits": active_bits,
            "copy_model_declaration_bits": current_declaration_bits,
            "context_count": 1,
            "context_counts": active_context_counts,
            "total_bits": current_bits,
            "delta_vs_current_bits": 0.0,
            "component_delta_bits": 0.0,
            "declaration_delta_bits": 0,
            "decodable": True,
            "audit_rows": active_audit_rows,
        }
    ]
    for name, family, description, context_fn in candidate_specs:
        models.append(
            model_row(
                name=name,
                family=family,
                context_description=description,
                context_fn=context_fn,
                rows=rows,
                alpha=alpha,
                current_length_bits=current_length_bits,
                current_total_bits=current_bits,
                fixed_nonlength_bits=fixed_nonlength_bits,
                current_declaration_bits=current_declaration_bits,
            )
        )

    searched_split_rows = []
    for split_book in range(1, 70):
        length_bits, audit_rows, context_counts = adaptive_context_bits(
            rows,
            alpha,
            lambda row, split_book=split_book: "before_split"
            if int(row["book_int"]) < split_book
            else "after_split",
        )
        declaration_bits = searched_split_declaration_bits(
            current_declaration_bits,
            split_book,
            len(context_counts),
        )
        total_bits = fixed_nonlength_bits + length_bits + declaration_bits - current_declaration_bits
        searched_split_rows.append(
            {
                "model": "searched_single_book_split_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "adaptive_copy_length_bits": length_bits,
                "copy_model_declaration_bits": declaration_bits,
                "context_count": len(context_counts),
                "context_counts": context_counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": length_bits - current_length_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
                "audit_rows": audit_rows,
            }
        )
    best_searched_split = min(searched_split_rows, key=lambda row: row["total_bits"])
    models.append(best_searched_split)
    models.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in models if row["decodable"])
    promoted = best_decodable["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_adaptive_copy_length_midpoint_context_improvement"
        if promoted and best_decodable["model"] == "book_midpoint_35_context"
        else "post_adaptive_copy_length_context_candidate"
        if promoted
        else "post_adaptive_copy_length_context_not_promoted"
    )

    top_context_savings = sorted(
        best_decodable["audit_rows"],
        key=lambda row: row["adaptive_context_bits"],
    )[:20]

    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_length_model"] = {
            **out["policy"]["copy_length_model"],
            "context_family": best_decodable["family"],
            "context": best_decodable["context_description"],
            "context_count": int(best_decodable["context_count"]),
            "context_counts": best_decodable["context_counts"],
            "family": "contextual_adaptive_bounded_length_index_after_source_address",
            "model_declaration_bits": int(best_decodable["copy_model_declaration_bits"]),
            "replaces": formula["policy"]["copy_length_model"],
        }
        out["policy"]["cost_model"] = (
            out["policy"]["cost_model"]
            + "+midpoint_contextual_adaptive_bounded_copy_length_index"
        )
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best_decodable["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_post_adaptive_bits": current_bits - best_decodable["total_bits"],
            "previous_bounded_adaptive_copy_length_bits": current_length_bits,
            "bounded_adaptive_copy_length_bits": best_decodable["adaptive_copy_length_bits"],
            "copy_length_code_bits": best_decodable["adaptive_copy_length_bits"],
            "copy_model_declaration_bits": int(best_decodable["copy_model_declaration_bits"]),
            "copy_bits": current_score["copy_address_bits"] + best_decodable["adaptive_copy_length_bits"],
            "fixed_bits": float(formula["mdl_estimate_rough"]["fixed_bits"])
            - current_declaration_bits
            + int(best_decodable["copy_model_declaration_bits"]),
        }
        out["validation"] = {
            **out["validation"],
            "post_adaptive_copy_length_context_roundtrip_audit": current_score["validation"],
            "post_adaptive_copy_length_context_copy_items": len(rows),
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result_models = [{key: value for key, value in row.items() if key != "audit_rows"} for row in models]
    result = {
        "schema": "post_adaptive_copy_length_context_search.v1",
        "test": "84_post_adaptive_copy_length_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(rows),
        "current_copy_length_bits": current_length_bits,
        "current_copy_model_declaration_bits": current_declaration_bits,
        "best_model": {key: value for key, value in best_decodable.items() if key != "audit_rows"},
        "models": result_models,
        "searched_single_split_models": [
            {key: value for key, value in row.items() if key != "audit_rows"}
            for row in sorted(searched_split_rows, key=lambda row: row["total_bits"])
        ],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "top_context_savings": top_context_savings,
        "promotion_rule": (
            "promote only if a decodable copy-length context model beats the active "
            "global adaptive bounded copy-length ledger after charged context "
            "declaration bits while preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Adaptive Copy-Length Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the active adaptive bounded copy-length ledger with",
        "simple contexts available before the copy length is decoded. The recipe,",
        "source-address ledger, copy order, payload model, item-type model, forced",
        "rules, and book-length ledger are fixed.",
        "",
        "## Context Models",
        "",
        "| Rank | Model | Contexts | Length bits | Model bits | Total bits | Delta vs current | Component delta |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['context_count']}` | "
            f"`{row['adaptive_copy_length_bits']:.3f}` | `{row['copy_model_declaration_bits']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['component_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Searched Split",
            "",
            f"- Split book: `{best_searched_split['split_book']}`",
            f"- Component delta: `{best_searched_split['component_delta_bits']:.3f}` bits",
            f"- Charged total delta: `{best_searched_split['delta_vs_current_bits']:.3f}` bits",
            "",
            "## Interpretation",
            "",
            "The fixed midpoint context is decodable because book ids and book order are",
            "already declared. It is charged one context-family bit plus a context-count",
            "declaration. Exhaustive single-split search has a lower component cost at",
            "some split points, but the charged split index prevents promotion.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-length cost refinement only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("84_post_adaptive_copy_length_context_search", result, lines)


if __name__ == "__main__":
    main()
