from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx2_param_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
ITEM_CONTEXT = HERE / "scripts/95_post_midpoint_alpha1_item_type_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx2_param_minaddr_repair2_bits"


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


def item_type_base_declaration_bits(alpha: int, order: int, forced_rule_bits: int) -> int:
    return gamma_bits(alpha + 1) + forced_rule_bits + (0 if order == 1 else 1 + gamma_bits(order))


def extra_context_declaration_bits(family: str, context_count: int, split_book: int | None = None) -> int:
    if family in ("global", "active_global"):
        return 0
    bits = 1 + gamma_bits(context_count + 1)
    if family == "searched_single_book_split":
        if split_book is None:
            raise ValueError("searched split requires split_book")
        bits += gamma_bits(split_book + 1)
    return bits


def collect_extra_context_counts(rows: list[dict], family: str, split_book: int | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        book = int(row["book_int"])
        if family in ("global", "active_global"):
            label = "global"
        elif family == "fixed_book_midpoint":
            label = "first_half" if book < 35 else "second_half"
        elif family == "fixed_book_quartile":
            label = str(min(3, book // 18))
        elif family == "fixed_book_decade":
            label = str(book // 10)
        elif family == "fixed_book_parity":
            label = str(book % 2)
        elif family == "op_index":
            label = str(log_bucket(int(row["op_index"]) + 1, 6))
        elif family == "declared_remaining":
            label = str(log_bucket(int(row["remaining"]), 8))
        elif family == "searched_single_book_split":
            if split_book is None:
                raise ValueError("searched split requires split_book")
            label = "before_split" if book < split_book else "after_split"
        else:
            raise ValueError(family)
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def set_extra_context(model: dict, family: str, split_book: int | None, counts: dict[str, int]) -> dict:
    out = dict(model)
    out["extra_context_family"] = family
    out["extra_context_count"] = len(counts)
    out["extra_context_counts"] = counts
    if family == "searched_single_book_split":
        out["split_book"] = int(split_book)
        out["extra_context"] = f"book_id < {split_book} versus book_id >= {split_book}"
    else:
        out.pop("split_book", None)
        out["extra_context"] = family
    if family in ("global", "active_global"):
        out.pop("extra_context", None)
        out.pop("extra_context_count", None)
        out.pop("extra_context_counts", None)
    return out


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    item_context = load_module("post_midpoint_item_type_context_search", ITEM_CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    current_model = formula["policy"]["item_type_model"]
    current_item_decl = int(current_model["model_declaration_bits"])
    current_fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    forced_rule_bits = int(current_model["forced_rule_bits"])
    item_rows, item_stats = item_context.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    family_specs: list[tuple[str, list[int | None]]] = [
        ("global", [None]),
        ("fixed_book_midpoint", [None]),
        ("fixed_book_quartile", [None]),
        ("fixed_book_decade", [None]),
        ("fixed_book_parity", [None]),
        ("op_index", [None]),
        ("declared_remaining", [None]),
        ("searched_single_book_split", list(range(1, 70))),
    ]

    rows = []
    candidates_tested = 0
    for family, split_books in family_specs:
        for split_book in split_books:
            counts = collect_extra_context_counts(item_rows, family, split_book)
            extra_decl = extra_context_declaration_bits(family, len(counts), split_book)
            for order in range(1, 8):
                for alpha in range(1, 33):
                    declaration_bits = item_type_base_declaration_bits(alpha, order, forced_rule_bits) + extra_decl
                    candidate = copy.deepcopy(formula)
                    candidate_model = set_extra_context(candidate["policy"]["item_type_model"], family, split_book, counts)
                    candidate_model["order"] = order
                    candidate_model["alpha"] = alpha
                    candidate_model["model_declaration_bits"] = declaration_bits
                    candidate["policy"]["item_type_model"] = candidate_model
                    candidate["mdl_estimate_rough"]["fixed_bits"] = (
                        current_fixed_bits - current_item_decl + declaration_bits
                    )
                    score = midpoint.score_formula(candidate, books, frontier, context_module)
                    if score["validation"]["errors"]:
                        raise RuntimeError(score["validation"])
                    candidates_tested += 1
                    total_bits = score["total_bits"]
                    rows.append(
                        {
                            "family": family,
                            "split_book": split_book,
                            "order": order,
                            "alpha": alpha,
                            "extra_context_counts": counts,
                            "extra_context_count": len(counts),
                            "item_type_stream_bits": score["item_type_stream_bits"],
                            "model_declaration_bits": declaration_bits,
                            "total_bits": total_bits,
                            "delta_vs_current_bits": total_bits - current_bits,
                            "component_delta_bits": score["item_type_stream_bits"] - current_score["item_type_stream_bits"],
                            "declaration_delta_bits": declaration_bits - current_item_decl,
                        }
                    )

    rows.sort(key=lambda row: row["total_bits"])
    best_by_family: dict[str, dict] = {}
    for row in rows:
        key = row["family"] if row["split_book"] is None else f"{row['family']}@{row['split_book']}"
        best_by_family.setdefault(key, row)
    best = rows[0]
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_item_type_context_family_improvement"
        if promoted
        else "post_itemctx_param_item_type_context_family_not_promoted"
    )

    if promoted:
        out = copy.deepcopy(formula)
        counts = dict(best["extra_context_counts"])
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx2_param_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["item_type_model"] = set_extra_context(
            out["policy"]["item_type_model"],
            best["family"],
            best["split_book"],
            counts,
        )
        out["policy"]["item_type_model"]["order"] = int(best["order"])
        out["policy"]["item_type_model"]["alpha"] = int(best["alpha"])
        out["policy"]["item_type_model"]["model_declaration_bits"] = int(best["model_declaration_bits"])
        out["policy"]["cost_model"] = out["policy"]["cost_model"] + "+item_type_context_family_resweep"
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_itemctx_param_bits": current_bits - best["total_bits"],
            "item_type_context_order_stream_bits": best["item_type_stream_bits"],
            "item_type_model_declaration_bits": int(best["model_declaration_bits"]),
            "fixed_bits": current_fixed_bits - current_item_decl + int(best["model_declaration_bits"]),
        }
        promoted_score = midpoint.score_formula(out, books, frontier, context_module)
        if promoted_score["validation"]["errors"]:
            raise RuntimeError(promoted_score["validation"])
        if abs(promoted_score["total_bits"] - best["total_bits"]) > 1e-6:
            raise RuntimeError((promoted_score["total_bits"], best["total_bits"]))
        out["validation"] = {
            **out["validation"],
            "post_itemctx_param_item_type_context_family_roundtrip_audit": promoted_score["validation"],
            "item_type_context_stats": promoted_score["item_type_context_stats"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_itemctx_param_item_type_context_family_search.v1",
        "test": "104_post_itemctx_param_item_type_context_family_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "item_stats": item_stats,
        "candidates_tested": candidates_tested,
        "current_item_type_stream_bits": current_score["item_type_stream_bits"],
        "current_item_type_model_declaration_bits": current_item_decl,
        "best_model": best,
        "best_by_family": best_by_family,
        "top_models": rows[:100],
        "promotion_rule": (
            "promote only if a decodable item-type extra-context family plus order/alpha "
            "beats the active itemctx_param model after charged declaration bits while "
            "preserving forced rules, 70/70 roundtrip, and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Item-Type Context Family Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests item-type extra-context families after the itemctx_param",
        "promotion. For each decodable family it sweeps item-type context order",
        "`1..7` and alpha `1..32`, charging family, searched-split, order, alpha,",
        "and forced-rule declaration bits. The recipe, payload model, copy-address",
        "ledger, copy-length model, forced rules, and book-length ledger are fixed.",
        "",
        "## Top Models",
        "",
        "| Rank | Family | Split | Order | Alpha | Total bits | Delta | Stream bits | Model bits |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        split = "" if row["split_book"] is None else str(row["split_book"])
        lines.append(
            f"| `{rank}` | `{row['family']}` | `{split}` | `{row['order']}` | `{row['alpha']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['item_type_stream_bits']:.3f}` | `{row['model_declaration_bits']}` |"
        )
    lines.extend(
        [
            "",
            "## Best By Family",
            "",
            "| Family | Split | Order | Alpha | Total bits | Delta |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for key, row in sorted(best_by_family.items(), key=lambda item: item[1]["total_bits"])[:20]:
        split = "" if row["split_book"] is None else str(row["split_book"])
        lines.append(
            f"| `{row['family']}` | `{split}` | `{row['order']}` | `{row['alpha']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "An item-type context family is promoted only if its stream savings survive",
            "the charged family/order/alpha declaration bits and the authoritative",
            "scorer validates 70/70 roundtrip. Otherwise the active searched split at",
            "book `6`, order `1`, alpha `2` remains the current formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical item-type ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    if promoted:
        lines.extend(["", "## Promoted Formula", "", f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})"])
    write_result("104_post_itemctx_param_item_type_context_family_search", result, lines)


if __name__ == "__main__":
    main()
