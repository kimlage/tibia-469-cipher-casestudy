from __future__ import annotations

import copy
import importlib.util
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
ACTIVE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json"
)
ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_bits"
)
RANDOM_SEED = 130469
RANDOM_ORDER_COUNT = 6


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


def log2_factorial(value: int) -> float:
    return math.lgamma(value + 1) / math.log(2)


def order_signature(order: list[int]) -> str:
    return ",".join(str(item) for item in order)


def named_orders(numeric_order: list[int], books: dict[str, str]) -> list[dict[str, Any]]:
    evens = [book for book in numeric_order if book % 2 == 0]
    odds = [book for book in numeric_order if book % 2 == 1]
    by_length = sorted(numeric_order, key=lambda book: (len(books[str(book)]), book))
    return [
        {
            "name": "numeric",
            "family": "canonical",
            "order": numeric_order,
            "descriptor_bits": 0.0,
            "descriptor_note": "canonical declared numeric order",
        },
        {
            "name": "reverse_numeric",
            "family": "simple_control",
            "order": list(reversed(numeric_order)),
            "descriptor_bits": 1.0,
            "descriptor_note": "one-bit direction flag after numeric order",
        },
        {
            "name": "evens_then_odds",
            "family": "simple_control",
            "order": evens + odds,
            "descriptor_bits": 2.0,
            "descriptor_note": "parity block plus direction flag",
        },
        {
            "name": "odds_then_evens",
            "family": "simple_control",
            "order": odds + evens,
            "descriptor_bits": 2.0,
            "descriptor_note": "parity block plus direction flag",
        },
        {
            "name": "length_ascending",
            "family": "content_derived_control",
            "order": by_length,
            "descriptor_bits": log2_factorial(len(numeric_order)),
            "descriptor_note": "content-derived order charged like arbitrary permutation",
        },
    ]


def random_orders(numeric_order: list[int]) -> list[dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    seen = {order_signature(numeric_order)}
    rows = []
    while len(rows) < RANDOM_ORDER_COUNT:
        order = list(numeric_order)
        rng.shuffle(order)
        signature = order_signature(order)
        if signature in seen:
            continue
        seen.add(signature)
        rows.append(
            {
                "name": f"random_{len(rows):02d}",
                "family": "random_permutation_control",
                "order": order,
                "descriptor_bits": log2_factorial(len(numeric_order)),
                "descriptor_note": "arbitrary permutation control charged as log2(70!)",
            }
        )
    return rows


def evaluate_order(
    *,
    order_case: dict[str, Any],
    base_formula: dict[str, Any],
    books: dict[str, str],
    compile129,
    audit126,
    frontier,
    midpoint,
    copy_module,
    item_module,
) -> dict[str, Any]:
    formula = copy.deepcopy(base_formula)
    formula["policy"]["book_order"] = list(order_case["order"])
    candidate_formula, reparse_audit = compile129.online_reparse_formula(
        formula=formula,
        books=books,
        audit126=audit126,
    )
    score = compile129.score_splitonly_formula(
        formula=candidate_formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if score["validation"]["errors"]:
        raise RuntimeError({"name": order_case["name"], "errors": score["validation"]["errors"]})

    raw_bits = float(score["total_bits"])
    descriptor_bits = float(order_case["descriptor_bits"])
    charged_bits = raw_bits + descriptor_bits
    return {
        "name": order_case["name"],
        "family": order_case["family"],
        "descriptor_bits": descriptor_bits,
        "descriptor_note": order_case["descriptor_note"],
        "raw_bits": raw_bits,
        "charged_bits": charged_bits,
        "roundtrip_ok": int(score["validation"]["books_roundtrip_ok"]),
        "literal_runs": int(score["literal_runs"]),
        "literal_digits": int(score["literal_digits"]),
        "copy_items": int(score["copy_items"]),
        "copied_digits": int(score["copied_digits"]),
        "order_prefix": list(order_case["order"][:10]),
        "order_suffix": list(order_case["order"][-10:]),
        "book_rows": reparse_audit["book_rows"],
    }


def summarize_random(rows: list[dict[str, Any]], numeric_raw_bits: float, numeric_charged_bits: float) -> dict[str, Any]:
    raw = [float(row["raw_bits"]) for row in rows]
    charged = [float(row["charged_bits"]) for row in rows]
    return {
        "count": len(rows),
        "raw_min_bits": min(raw),
        "raw_mean_bits": statistics.mean(raw),
        "raw_max_bits": max(raw),
        "raw_stdev_bits": statistics.pstdev(raw),
        "charged_min_bits": min(charged),
        "charged_mean_bits": statistics.mean(charged),
        "charged_max_bits": max(charged),
        "random_raw_le_numeric_count": sum(value <= numeric_raw_bits for value in raw),
        "random_charged_le_numeric_count": sum(value <= numeric_charged_bits for value in charged),
        "p_random_raw_le_numeric_empirical": sum(value <= numeric_raw_bits for value in raw) / len(raw),
        "p_random_charged_le_numeric_empirical": sum(value <= numeric_charged_bits for value in charged) / len(charged),
    }


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    base_formula = load_json(ACTIVE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    numeric_order = [int(book) for book in base_formula["policy"]["book_order"]]
    active_bits = float(base_formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    arbitrary_order_bits = log2_factorial(len(numeric_order))

    cases = named_orders(numeric_order, books) + random_orders(numeric_order)
    rows = [
        evaluate_order(
            order_case=case,
            base_formula=base_formula,
            books=books,
            compile129=compile129,
            audit126=audit126,
            frontier=frontier,
            midpoint=midpoint,
            copy_module=copy_module,
            item_module=item_module,
        )
        for case in cases
    ]

    numeric_row = next(row for row in rows if row["name"] == "numeric")
    if abs(float(numeric_row["raw_bits"]) - active_bits) > 1e-6:
        raise RuntimeError({"numeric_recomputed": numeric_row["raw_bits"], "active_bits": active_bits})

    for row in rows:
        row["raw_delta_vs_numeric_bits"] = float(row["raw_bits"]) - float(numeric_row["raw_bits"])
        row["charged_delta_vs_numeric_bits"] = float(row["charged_bits"]) - float(numeric_row["charged_bits"])

    simple_rows = [row for row in rows if row["family"] == "simple_control"]
    random_rows = [row for row in rows if row["family"] == "random_permutation_control"]
    best_raw = min(rows, key=lambda row: float(row["raw_bits"]))
    best_charged = min(rows, key=lambda row: float(row["charged_bits"]))
    best_simple_charged = min(simple_rows, key=lambda row: float(row["charged_bits"]))
    random_summary = summarize_random(random_rows, float(numeric_row["raw_bits"]), float(numeric_row["charged_bits"]))

    if best_charged["name"] != "numeric":
        classification = "simple_order_control_beats_numeric_not_promoted_without_external_order"
    elif random_summary["random_raw_le_numeric_count"]:
        classification = "online_reparse_order_not_raw_numeric_unique"
    else:
        classification = "numeric_online_reparse_survives_order_controls"

    result = {
        "schema": "online_reparse_order_control_audit.v1",
        "test": "130_online_reparse_order_control_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(ACTIVE_FORMULA),
        "active_compression_bound_bits": active_bits,
        "numeric_recomputed_bits": numeric_row["raw_bits"],
        "arbitrary_order_descriptor_bits": arbitrary_order_bits,
        "random_seed": RANDOM_SEED,
        "random_order_count": RANDOM_ORDER_COUNT,
        "best_raw": {
            "name": best_raw["name"],
            "family": best_raw["family"],
            "raw_bits": best_raw["raw_bits"],
            "raw_delta_vs_numeric_bits": best_raw["raw_delta_vs_numeric_bits"],
        },
        "best_charged": {
            "name": best_charged["name"],
            "family": best_charged["family"],
            "charged_bits": best_charged["charged_bits"],
            "charged_delta_vs_numeric_bits": best_charged["charged_delta_vs_numeric_bits"],
        },
        "best_simple_charged": {
            "name": best_simple_charged["name"],
            "charged_bits": best_simple_charged["charged_bits"],
            "charged_delta_vs_numeric_bits": best_simple_charged["charged_delta_vs_numeric_bits"],
        },
        "random_summary": random_summary,
        "rows": rows,
        "promotion_rule": (
            "This audit does not promote arbitrary order search. A non-numeric "
            "order can lower the committed bound only if it has a compact, "
            "predeclared or externally evidenced descriptor after order cost."
        ),
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    sorted_rows = sorted(rows, key=lambda row: float(row["raw_bits"]))
    simple_table = [row for row in rows if row["family"] != "random_permutation_control"]
    lines = [
        "# 130. Online Reparse Order Control Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 129 lowered the charged full-corpus bound by using a deterministic",
        "online parser in numeric book order. This audit tests whether that gain",
        "is tied to a compact/canonical order or whether arbitrary book",
        "permutations obtain similar raw compression.",
        "",
        "## Result",
        "",
        f"- Numeric online bound: `{numeric_row['raw_bits']:.3f}` bits",
        f"- Best raw order: `{best_raw['name']}` at `{best_raw['raw_bits']:.3f}` bits "
        f"(`{best_raw['raw_delta_vs_numeric_bits']:+.3f}` vs numeric)",
        f"- Best charged order: `{best_charged['name']}` at `{best_charged['charged_bits']:.3f}` bits "
        f"(`{best_charged['charged_delta_vs_numeric_bits']:+.3f}` vs numeric)",
        f"- Random raw <= numeric: `{random_summary['random_raw_le_numeric_count']}/{RANDOM_ORDER_COUNT}`",
        f"- Random charged <= numeric: `{random_summary['random_charged_le_numeric_count']}/{RANDOM_ORDER_COUNT}`",
        f"- Arbitrary-order descriptor cost: `{arbitrary_order_bits:.3f}` bits",
        "",
        "## Named Orders",
        "",
        "| Order | Raw bits | Raw delta | Descriptor | Charged delta | Roundtrip |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in simple_table:
        lines.append(
            f"| `{row['name']}` | `{row['raw_bits']:.3f}` | "
            f"`{row['raw_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['descriptor_bits']:.3f}` | "
            f"`{row['charged_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['roundtrip_ok']}/70` |"
        )
    lines.extend(
        [
            "",
            "## Random Controls",
            "",
            f"- Raw min/mean/max: `{random_summary['raw_min_bits']:.3f}` / "
            f"`{random_summary['raw_mean_bits']:.3f}` / `{random_summary['raw_max_bits']:.3f}` bits",
            f"- Raw stdev: `{random_summary['raw_stdev_bits']:.3f}` bits",
            f"- Empirical `p(random raw <= numeric)`: "
            f"`{random_summary['p_random_raw_le_numeric_empirical']:.4f}`",
            f"- Empirical `p(random charged <= numeric)`: "
            f"`{random_summary['p_random_charged_le_numeric_empirical']:.4f}`",
            "",
            "## Lowest Raw Rows",
            "",
            "| Rank | Order | Family | Raw bits | Raw delta | Charged delta |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(sorted_rows[:8], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['family']}` | "
            f"`{row['raw_bits']:.3f}` | `{row['raw_delta_vs_numeric_bits']:+.3f}` | "
            f"`{row['charged_delta_vs_numeric_bits']:+.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if best_charged["name"] != "numeric":
        lines.extend(
            [
                "A compact control order beats numeric even after the small descriptor",
                "charge used here, but this audit does not promote it as authorial.",
                "It must be treated as an order-origin question until an external or",
                "predeclared order rule justifies the descriptor.",
            ]
        )
    elif random_summary["random_raw_le_numeric_count"]:
        lines.extend(
            [
                "At least one arbitrary random order matches or beats numeric before",
                "charging order description. After charging `log2(70!)`, random order",
                "does not beat numeric; the result therefore validates compression",
                "opportunity but not a unique authorial order.",
            ]
        )
    else:
        lines.extend(
            [
                "Numeric order remains the best raw and charged order among the tested",
                "named and random controls. This supports the online reparse as a",
                "compact mechanical recipe rather than arbitrary order overfitting.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
            "- Arbitrary order search is not promoted as a new bound.",
        ]
    )
    write_result("130_online_reparse_order_control_audit", result, lines)


if __name__ == "__main__":
    main()
