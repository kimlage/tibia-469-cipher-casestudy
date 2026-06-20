from __future__ import annotations

import importlib.util
import json
import math
import copy
from collections import defaultdict
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_bits"
ITEM_TYPES = ["literal", "copy"]
BOS_ITEM = "BOS"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def log_bucket(value: int, cap: int) -> int:
    return min(cap, int(math.floor(math.log2(max(1, value)))))


def contextual_item_declaration_bits(current_declaration_bits: int, context_count: int) -> int:
    return current_declaration_bits + 1 + gamma_bits(context_count + 1)


def searched_split_declaration_bits(current_declaration_bits: int, context_count: int, split_book: int) -> int:
    return contextual_item_declaration_bits(current_declaration_bits, context_count) + gamma_bits(split_book + 1)


def collect_item_rows(formula: dict, books: dict[str, str]) -> tuple[list[dict], dict]:
    model = formula["policy"]["item_type_model"]
    order = int(model["order"])
    min_len = int(formula["policy"]["min_len"])
    rows = []
    stats = {
        "coded_items": 0,
        "forced_literal_to_copy": 0,
        "forced_remaining_short_to_literal": 0,
        "forced_rule_violations": [],
    }

    for book_index, book in enumerate(map(str, formula["policy"]["book_order"])):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        parts = []
        position = 0
        history = []
        for op_index, op in enumerate(ops):
            item_type = op["type"]
            remaining = book_length - position
            previous = history[-1] if history else BOS_ITEM
            forced_rule = None
            if previous == "literal":
                forced_rule = "literal_forces_copy"
                stats["forced_literal_to_copy"] += 1
                if item_type != "copy":
                    stats["forced_rule_violations"].append(
                        {"rule": forced_rule, "book": book, "item_index": op_index}
                    )
            elif remaining < min_len:
                forced_rule = "remaining_short_forces_literal"
                stats["forced_remaining_short_to_literal"] += 1
                if item_type != "literal":
                    stats["forced_rule_violations"].append(
                        {
                            "rule": forced_rule,
                            "book": book,
                            "item_index": op_index,
                            "remaining": remaining,
                        }
                    )
            else:
                context = tuple(([BOS_ITEM] * order + history)[-order:])
                rows.append(
                    {
                        "coded_item_id": len(rows),
                        "book": book,
                        "book_int": int(book),
                        "book_index": book_index,
                        "op_index": op_index,
                        "book_pos": position,
                        "remaining": remaining,
                        "length": int(op["length"]),
                        "item_type": item_type,
                        "previous_item_context": context,
                        "previous_item": previous,
                    }
                )
                stats["coded_items"] += 1

            if item_type == "literal":
                chunk = op["text"]
            elif item_type == "copy":
                # Only roundtrip shape is needed here; score_formula validates
                # the full copy source in the authoritative scorer.
                chunk = "?" * int(op["length"])
            else:
                raise ValueError(op)
            parts.append(chunk)
            history.append(item_type)
            position += int(op["length"])
            if forced_rule is not None:
                continue
        if position != len(books[book]):
            raise RuntimeError((book, position, len(books[book])))

    return rows, stats


def item_bits(
    rows: list[dict],
    alpha: float,
    context_fn: Callable[[dict], object],
) -> tuple[float, list[dict], dict[str, int]]:
    counts = defaultdict(lambda: {item_type: 0.0 for item_type in ITEM_TYPES})
    totals = defaultdict(float)
    context_uses: dict[str, int] = {}
    audit_rows = []
    bits = 0.0

    for row in rows:
        context_value = context_fn(row)
        context_label = json.dumps(context_value, sort_keys=True) if not isinstance(context_value, str) else context_value
        context = (context_label, row["previous_item_context"])
        item_type = row["item_type"]
        probability = (counts[context][item_type] + alpha) / (totals[context] + len(ITEM_TYPES) * alpha)
        bit_cost = -math.log2(probability)
        bits += bit_cost
        counts[context][item_type] += 1.0
        totals[context] += 1.0
        context_uses[context_label] = context_uses.get(context_label, 0) + 1
        audit_rows.append(
            {
                **row,
                "item_type_context": context_label,
                "adaptive_item_bits": bit_cost,
                "previous_context_observations": totals[context] - 1.0,
                "previous_context_same_item_observations": counts[context][item_type] - 1.0,
            }
        )

    return bits, audit_rows, dict(sorted(context_uses.items()))


def strip_audit_rows(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "audit_rows"}


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    model = formula["policy"]["item_type_model"]
    alpha = float(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    current_item_bits = float(current_score["item_type_stream_bits"])
    fixed_nonitem_bits = current_bits - current_item_bits
    item_rows, item_stats = collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    active_bits, active_audit_rows, active_context_counts = item_bits(item_rows, alpha, lambda _row: "global")
    if abs(active_bits - current_item_bits) > 1e-6:
        raise RuntimeError((active_bits, current_item_bits))

    candidate_specs: list[tuple[str, str, str, Callable[[dict], object], bool]] = [
        (
            "active_global_item_type_context",
            "active_global",
            "single global item-type context",
            lambda _row: "global",
            True,
        ),
        (
            "book_midpoint_35_item_type_context",
            "fixed_book_midpoint",
            "book_id < 35 versus book_id >= 35",
            lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
            True,
        ),
        (
            "book_quartile_item_type_context",
            "fixed_book_quartile",
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
            True,
        ),
        (
            "book_decade_item_type_context",
            "fixed_book_decade",
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
            True,
        ),
        (
            "book_parity_item_type_context",
            "fixed_book_parity",
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
            True,
        ),
        (
            "op_index_log_item_type_context",
            "op_index",
            "log bucket of item index within the book",
            lambda row: log_bucket(int(row["op_index"]) + 1, 6),
            True,
        ),
        (
            "remaining_log_item_type_context",
            "declared_remaining",
            "log bucket of remaining declared book length",
            lambda row: log_bucket(int(row["remaining"]), 8),
            True,
        ),
        (
            "item_length_log_context",
            "item_length",
            "log bucket of current item length after it is known",
            lambda row: log_bucket(int(row["length"]), 8),
            False,
        ),
    ]

    models = []
    for name, family, description, context_fn, decodable in candidate_specs:
        bits, audit_rows, counts = item_bits(item_rows, alpha, context_fn)
        context_count = len(counts)
        declaration_bits = (
            current_declaration_bits
            if name == "active_global_item_type_context"
            else contextual_item_declaration_bits(current_declaration_bits, context_count)
        )
        total_bits = fixed_nonitem_bits + bits + declaration_bits - current_declaration_bits
        models.append(
            {
                "model": name,
                "family": family,
                "context_description": description,
                "item_type_stream_bits": bits,
                "item_type_model_declaration_bits": declaration_bits,
                "context_count": context_count,
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_item_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": decodable,
                "audit_rows": audit_rows,
            }
        )

    searched_split_rows = []
    for split_book in range(1, 70):
        bits, audit_rows, counts = item_bits(
            item_rows,
            alpha,
            lambda row, split_book=split_book: "before_split"
            if int(row["book_int"]) < split_book
            else "after_split",
        )
        declaration_bits = searched_split_declaration_bits(current_declaration_bits, len(counts), split_book)
        total_bits = fixed_nonitem_bits + bits + declaration_bits - current_declaration_bits
        searched_split_rows.append(
            {
                "model": "searched_single_book_split_item_type_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "item_type_stream_bits": bits,
                "item_type_model_declaration_bits": declaration_bits,
                "context_count": len(counts),
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_item_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
                "audit_rows": audit_rows,
            }
        )
    best_searched_split = min(searched_split_rows, key=lambda row: row["total_bits"])
    models.append(best_searched_split)
    models.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in models if row["decodable"])
    promoted = (
        best_decodable["model"] != "active_global_item_type_context"
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    classification = (
        "controlled_post_midpoint_item_type_context_improvement"
        if promoted
        else "post_midpoint_item_type_context_not_promoted"
    )

    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        item_model = {
            **out["policy"]["item_type_model"],
            "extra_context_family": best_decodable["family"],
            "extra_context": best_decodable["context_description"],
            "extra_context_count": int(best_decodable["context_count"]),
            "extra_context_counts": best_decodable["context_counts"],
            "model_declaration_bits": int(best_decodable["item_type_model_declaration_bits"]),
        }
        if best_decodable["family"] == "searched_single_book_split":
            item_model["split_book"] = int(best_decodable["split_book"])
        out["policy"]["item_type_model"] = item_model
        out["policy"]["cost_model"] = out["policy"]["cost_model"] + "+item_type_extra_context"
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best_decodable["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_midpoint_alpha1_bits": current_bits - best_decodable["total_bits"],
            "item_type_context_order_stream_bits": best_decodable["item_type_stream_bits"],
            "item_type_model_declaration_bits": int(best_decodable["item_type_model_declaration_bits"]),
            "fixed_bits": float(formula["mdl_estimate_rough"]["fixed_bits"])
            - current_declaration_bits
            + int(best_decodable["item_type_model_declaration_bits"]),
        }
        promoted_score = midpoint.score_formula(out, books, frontier, context_module)
        if promoted_score["validation"]["errors"]:
            raise RuntimeError(promoted_score["validation"])
        if abs(promoted_score["total_bits"] - best_decodable["total_bits"]) > 1e-6:
            raise RuntimeError((promoted_score["total_bits"], best_decodable["total_bits"]))
        out["validation"] = {
            **out["validation"],
            "post_midpoint_item_type_context_roundtrip_audit": promoted_score["validation"],
            "item_type_context_stats": promoted_score["item_type_context_stats"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_midpoint_alpha1_item_type_context_search.v1",
        "test": "95_post_midpoint_alpha1_item_type_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "item_stats": item_stats,
        "current_item_type_stream_bits": current_item_bits,
        "current_item_type_model_declaration_bits": current_declaration_bits,
        "best_model": strip_audit_rows(best_decodable),
        "best_any_model": strip_audit_rows(models[0]),
        "models": [strip_audit_rows(row) for row in models],
        "searched_single_split_models": [
            strip_audit_rows(row)
            for row in sorted(searched_split_rows, key=lambda row: row["total_bits"])
        ],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable item-type context beats the active global "
            "previous-item model after charged declaration bits while preserving "
            "forced rules, 70/70 roundtrip, and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Midpoint Alpha1 Item-Type Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests whether the adaptive literal/copy item-type model",
        "should be split by a simple context after the midpoint alpha=1 formula",
        "became active. The recipe, literal models, copy-address ledger,",
        "copy-length model, forced rules, and book-length ledger are fixed.",
        "",
        "## Item-Type Context Models",
        "",
        "| Rank | Model | Contexts | Item bits | Model bits | Total bits | Delta vs current | Component delta | Decodable |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['context_count']}` | "
            f"`{row['item_type_stream_bits']:.3f}` | `{row['item_type_model_declaration_bits']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['component_delta_bits']:.3f}` | `{row['decodable']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Searched Split",
            "",
            f"- Split book: `{best_searched_split['split_book']}`",
            f"- Total bits: `{best_searched_split['total_bits']:.3f}`",
            f"- Delta vs current: `{best_searched_split['delta_vs_current_bits']:.3f}`",
            f"- Component delta: `{best_searched_split['component_delta_bits']:.3f}`",
            f"- Declaration delta: `{best_searched_split['declaration_delta_bits']}`",
            "",
            "## Interpretation",
            "",
            "An item-type context is promoted only if its component savings survive",
            "the extra declaration cost and the forced literal/copy rules remain",
            "valid. Otherwise the active global previous-item model remains the",
            "current formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical item-type-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
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
    write_result("95_post_midpoint_alpha1_item_type_context_search", result, lines)


if __name__ == "__main__":
    main()
