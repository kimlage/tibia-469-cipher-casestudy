from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_126 = HERE / "scripts" / "126_prequential_recipe_reparse_audit.py"
FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json"
)
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json"
)
CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_bits"
)
ITEM_TYPES = ["literal", "copy"]
DIGITS = [str(i) for i in range(10)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_audit_126():
    return load_module("prequential_recipe_reparse_audit", AUDIT_126)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def score_fixed_rows(
    rows: list[dict[str, Any]],
    *,
    alphabet: list[str],
    alpha: float,
    context_fn,
    symbol_key: str,
) -> tuple[float, dict[str, int]]:
    counts: dict[Any, dict[str, float]] = {}
    context_counts: dict[str, int] = {}
    bits = 0.0
    for row in rows:
        context = context_fn(row)
        context_label = json.dumps(context, sort_keys=True) if not isinstance(context, str) else context
        bucket = counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        total = sum(bucket.get(symbol, 0.0) for symbol in alphabet)
        symbol = row[symbol_key]
        probability = (bucket.get(symbol, 0.0) + alpha) / (total + len(alphabet) * alpha)
        bits += -math.log2(probability)
        bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
        context_counts[context_label] = context_counts.get(context_label, 0) + 1
    return bits, dict(sorted(context_counts.items()))


def score_splitonly_formula(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    audit126,
    frontier,
    midpoint,
    copy_module,
    item_module,
) -> dict[str, Any]:
    base = midpoint.score_formula(formula, books, frontier, copy_module)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    item_model = formula["policy"]["item_type_model"]
    item_bits, item_context_counts = score_fixed_rows(
        item_rows,
        alphabet=ITEM_TYPES,
        alpha=float(item_model["alpha"]),
        context_fn=lambda row: audit126.item_context_key(item_model, int(row["book_int"])),
        symbol_key="item_type",
    )
    errors = list(base["validation"]["errors"]) + list(item_stats["forced_rule_violations"])
    total_bits = (
        float(base["fixed_bits"])
        + float(base["literal_bits_no_payload"])
        + float(base["literal_payload_bits"])
        + float(base["copy_bits"])
        + item_bits
    )
    return {
        **base,
        "total_bits": total_bits,
        "item_type_stream_bits": item_bits,
        "item_type_split_only_stream_bits": item_bits,
        "item_type_split_only_context_counts": item_context_counts,
        "item_type_split_only_stats": {
            **item_stats,
            "context_count": len(item_context_counts),
            "context_counts": item_context_counts,
        },
        "legacy_context_order_item_type_stream_bits": base["item_type_stream_bits"],
        "validation": {
            **base["validation"],
            "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
            "errors": errors,
        },
    }


def update_counts_from_encoded_book(
    *,
    encoded: dict[str, Any],
    book: str,
    text: str,
    available_before: str,
    formula: dict[str, Any],
    counts: dict[str, Any],
    audit126,
) -> None:
    min_len = int(formula["policy"]["min_len"])
    payload_model = formula["policy"]["literal_payload_model"]
    item_model = formula["policy"]["item_type_model"]
    local_emitted = available_before
    book_pos = 0
    history: list[str] = []
    book_length = len(text)
    for op_index, op in enumerate(encoded["ops"]):
        item_type = op["type"]
        remaining = book_length - book_pos
        previous = history[-1] if history else "BOS"
        forced = previous == "literal" or remaining < min_len
        if not forced:
            item_context = audit126.item_context_key(item_model, int(book))
            item_bucket = counts["item"].setdefault(item_context, {item: 0.0 for item in ITEM_TYPES})
            item_bucket[item_type] = item_bucket.get(item_type, 0.0) + 1.0

        if item_type == "literal":
            chunk = op["text"]
            for digit in chunk:
                payload_context = ("global", audit126.payload_context(local_emitted, int(payload_model["order"])))
                payload_bucket = counts["payload"].setdefault(payload_context, {digit_symbol: 0.0 for digit_symbol in DIGITS})
                payload_bucket[digit] = payload_bucket.get(digit, 0.0) + 1.0
                local_emitted += digit
        elif item_type == "copy":
            source_digit_pos = int(op["source_digit_pos"])
            length = int(op["length"])
            target_digit_global = len(local_emitted)
            max_length = min(remaining, target_digit_global - source_digit_pos)
            symbol_count = max_length - min_len + 1
            length_index = length - min_len
            if symbol_count <= 0 or not 0 <= length_index < symbol_count:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "bad_copy_length",
                        "symbol_count": symbol_count,
                        "length_index": length_index,
                    }
                )
            copy_context = audit126.copy_context_key(int(book))
            copy_bucket = counts["copy"].setdefault(copy_context, {})
            copy_bucket[length_index] = copy_bucket.get(length_index, 0.0) + 1.0
            chunk = local_emitted[source_digit_pos : source_digit_pos + length]
            if len(chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_copy"})
            local_emitted += chunk
        else:
            raise ValueError(op)
        history.append(item_type)
        book_pos += int(op["length"])
    if local_emitted != available_before + text:
        raise RuntimeError({"book": book, "type": "book_mismatch_after_update"})


def online_reparse_formula(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    audit126,
) -> tuple[dict[str, Any], dict[str, Any]]:
    counts = {"copy": {}, "payload": {}, "item": {}}
    available = ""
    recipes = {}
    book_rows = []
    for book in map(str, formula["policy"]["book_order"]):
        encoded = audit126.encode_book_frozen_reparse(
            book=book,
            text=books[book],
            available=available,
            formula=formula,
            train_counts=counts,
        )
        if encoded["validation"]["errors"]:
            raise RuntimeError(encoded["validation"])
        clean_ops = []
        for op in encoded["ops"]:
            if op["type"] == "literal":
                clean_ops.append({"type": "literal", "text": op["text"], "length": int(op["length"])})
            elif op["type"] == "copy":
                clean_ops.append(
                    {
                        "type": "copy",
                        "source_digit_pos": int(op["source_digit_pos"]),
                        "length": int(op["length"]),
                        "target_start": int(op["target_start"]),
                    }
                )
            else:
                raise ValueError(op)
        recipes[book] = {"length": len(books[book]), "ops": clean_ops}
        book_rows.append({key: value for key, value in encoded.items() if key != "ops"})
        update_counts_from_encoded_book(
            encoded={"ops": clean_ops},
            book=book,
            text=books[book],
            available_before=available,
            formula=formula,
            counts=counts,
            audit126=audit126,
        )
        available += books[book]

    out = copy.deepcopy(formula)
    out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula.v1"
    out["classification"] = "deterministic_online_reparse_candidate"
    out["source_baseline_formula"] = rel(FORMULA)
    out["book_recipes"] = recipes
    out["policy"]["recipe_generation"] = {
        "family": "deterministic_online_lz_reparse",
        "order": "declared numeric book order",
        "description": (
            "Each book is reparsed with the active deterministic LZ parser using "
            "only component counts from previously emitted books; counts are "
            "updated after committing the parsed book."
        ),
        "source_audit": rel(AUDIT_126),
    }
    return out, {"book_rows": book_rows}


def main() -> None:
    audit126 = load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    active_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    active_score = score_splitonly_formula(
        formula=formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if active_score["validation"]["errors"]:
        raise RuntimeError(active_score["validation"])
    if abs(active_score["total_bits"] - active_bits) > 1e-6:
        raise RuntimeError((active_score["total_bits"], active_bits))

    candidate_formula, reparse_audit = online_reparse_formula(formula=formula, books=books, audit126=audit126)
    candidate_score = score_splitonly_formula(
        formula=candidate_formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if candidate_score["validation"]["errors"]:
        raise RuntimeError(candidate_score["validation"])

    delta = candidate_score["total_bits"] - active_bits
    promoted = delta < -1e-9
    classification = (
        "controlled_online_reparse_formula_improvement"
        if promoted
        else "online_reparse_formula_not_promoted"
    )
    output_formula = None
    if promoted:
        candidate_formula["classification"] = classification
        candidate_formula["mdl_estimate_rough"] = {
            **candidate_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_score["total_bits"],
            f"previous_{CURRENT_TOTAL_KEY}": active_bits,
            "gain_vs_previous_splitonly_bits": active_bits - candidate_score["total_bits"],
            "literal_bits_no_payload": candidate_score["literal_bits_no_payload"],
            "adaptive_context_order_literal_payload_bits": candidate_score["literal_payload_bits"],
            "copy_bits": candidate_score["copy_bits"],
            "copy_address_bits": candidate_score["copy_address_bits"],
            "copy_length_code_bits": candidate_score["copy_length_code_bits"],
            "bounded_adaptive_copy_length_bits": candidate_score["copy_length_code_bits"],
            "item_type_split_only_stream_bits": candidate_score["item_type_split_only_stream_bits"],
            "literal_runs": candidate_score["literal_runs"],
            "literal_digits": candidate_score["literal_digits"],
            "copy_items": candidate_score["copy_items"],
            "copied_digits": candidate_score["copied_digits"],
            "forced_literal_length_count": candidate_score["forced_literal_length_count"],
            "forced_literal_length_saved_bits": candidate_score["forced_literal_length_saved_bits"],
        }
        candidate_formula["validation"] = {
            **candidate_formula["validation"],
            "online_reparse_roundtrip_audit": candidate_score["validation"],
            "literal_payload_context_stats": candidate_score["literal_payload_context_stats"],
            "midpoint_copy_length_context_counts": candidate_score["midpoint_copy_length_context_counts"],
            "item_type_split_only_stats": candidate_score["item_type_split_only_stats"],
        }
        candidate_formula["boundary"] = {
            **candidate_formula["boundary"],
            "translation_delta": "NONE",
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        }
        OUT_FORMULA.write_text(json.dumps(candidate_formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output_formula = rel(OUT_FORMULA)

    result = {
        "schema": "online_deterministic_reparse_compile.v1",
        "test": "129_online_deterministic_reparse_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(FORMULA),
        "output_formula": output_formula,
        "active_compression_bound_bits": active_bits,
        "candidate_total_bits": candidate_score["total_bits"],
        "candidate_delta_vs_active_bits": delta,
        "candidate_gain_vs_active_bits": active_bits - candidate_score["total_bits"],
        "promoted": promoted,
        "active_summary": {
            "literal_runs": active_score["literal_runs"],
            "literal_digits": active_score["literal_digits"],
            "copy_items": active_score["copy_items"],
            "copied_digits": active_score["copied_digits"],
        },
        "candidate_summary": {
            "literal_runs": candidate_score["literal_runs"],
            "literal_digits": candidate_score["literal_digits"],
            "copy_items": candidate_score["copy_items"],
            "copied_digits": candidate_score["copied_digits"],
        },
        "reparse_audit": reparse_audit,
        "candidate_score_audit": candidate_score,
        "promotion_rule": (
            "Promote only if the deterministic online full-corpus parser beats "
            "the active split-only compression bound after full rescoring, 70/70 "
            "roundtrip, forced-rule validity, and translation_delta NONE."
        ),
        "boundary": {
            "compression_bound_changed": promoted,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 129. Online Deterministic Reparse Compile",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 126-128 showed that deterministic reparsing has predictive suffix",
        "signal but does not promote numeric order as authorial. This compile asks",
        "whether the same deterministic parser can replace the active full-corpus",
        "recipe: each book is parsed using only counts from previously committed",
        "books, then the complete candidate formula is rescored under the active",
        "cost ledger.",
        "",
        "## Result",
        "",
        f"- Active compression bound: `{active_bits:.3f}` bits",
        f"- Online reparse candidate: `{candidate_score['total_bits']:.3f}` bits",
        f"- Delta vs active: `{delta:.3f}` bits",
        f"- Roundtrip: `{candidate_score['validation']['books_roundtrip_ok']}/70`",
        "",
        "| Metric | Active | Candidate |",
        "|---|---:|---:|",
        f"| Literal runs | `{active_score['literal_runs']}` | `{candidate_score['literal_runs']}` |",
        f"| Literal digits | `{active_score['literal_digits']}` | `{candidate_score['literal_digits']}` |",
        f"| Copy items | `{active_score['copy_items']}` | `{candidate_score['copy_items']}` |",
        f"| Copied digits | `{active_score['copied_digits']}` | `{candidate_score['copied_digits']}` |",
        "",
        "## Interpretation",
        "",
    ]
    if promoted:
        lines.extend(
            [
                "The deterministic online parser improves the full-corpus charged",
                "formula while preserving roundtrip and all non-semantic boundaries.",
                "This is a mechanical recipe-generation improvement, not a row0 or",
                "plaintext claim.",
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    else:
        lines.extend(
            [
                "The deterministic online parser does not beat the current full-corpus",
                "compression bound. The suffix-reparse signal remains predictive",
                "analysis, but the active recipe remains the cheaper committed formula.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
            "- Any promotion is mechanical recipe generation only.",
        ]
    )
    write_result("129_online_deterministic_reparse_compile", result, lines)


if __name__ == "__main__":
    main()
