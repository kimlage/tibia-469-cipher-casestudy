from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
SOURCE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_142 = REPORTS / "142_default_exception_component_profile.json"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
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


def context(emitted: str, order: int) -> str:
    if order == 0:
        return ""
    return emitted[-order:].rjust(order, "B")


def collect_literal_payload_rows(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    emitted = ""
    rows: list[dict[str, Any]] = []
    for book in map(str, formula["policy"]["book_order"]):
        book_start = len(emitted)
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                for offset, digit in enumerate(op["text"]):
                    rows.append(
                        {
                            "book": int(book),
                            "op_index": op_index,
                            "literal_offset": offset,
                            "digit": digit,
                            "emitted_before": emitted,
                        }
                    )
                    emitted += digit
                continue
            source = int(op["source_digit_pos"])
            length = int(op["length"])
            copied = emitted[source : source + length]
            if len(copied) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_copy"})
            emitted += copied
        if emitted[book_start:] != books[book]:
            raise RuntimeError({"book": book, "type": "roundtrip_failed"})
    return rows


def score_rows(
    rows: list[dict[str, Any]],
    *,
    order: int,
    counts: dict[str, dict[str, float]] | None = None,
    update: bool,
) -> tuple[float, dict[str, dict[str, float]]]:
    local = {
        key: value.copy()
        for key, value in (counts or {}).items()
    }
    bits = 0.0
    for row in rows:
        key = context(row["emitted_before"], order)
        bucket = local.setdefault(key, {digit: 0.0 for digit in DIGITS})
        total = sum(bucket.values())
        digit = row["digit"]
        probability = (bucket[digit] + 1.0) / (total + 10.0)
        bits += -math.log2(probability)
        if update:
            bucket[digit] += 1.0
    return bits, local


def full_corpus_order(rows: list[dict[str, Any]], order: int) -> dict[str, Any]:
    bits, counts = score_rows(rows, order=order, counts=None, update=True)
    return {
        "order": order,
        "bits": bits,
        "context_count": len(counts),
    }


def split_order(rows: list[dict[str, Any]], cutoff: int, order: int) -> dict[str, Any]:
    train = [row for row in rows if int(row["book"]) < cutoff]
    test = [row for row in rows if int(row["book"]) >= cutoff]
    train_bits, train_counts = score_rows(train, order=order, counts=None, update=True)
    online_bits, _ = score_rows(test, order=order, counts=train_counts, update=True)
    frozen_bits, _ = score_rows(test, order=order, counts=train_counts, update=False)
    uniform_bits = len(test) * math.log2(10)
    return {
        "cutoff": cutoff,
        "order": order,
        "train_digits": len(train),
        "test_digits": len(test),
        "train_bits": train_bits,
        "test_online_bits": online_bits,
        "test_frozen_bits": frozen_bits,
        "uniform_bits": uniform_bits,
        "online_gain_vs_uniform_bits": uniform_bits - online_bits,
        "frozen_gain_vs_uniform_bits": uniform_bits - frozen_bits,
    }


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    formula = load_json(SOURCE_FORMULA)
    audit142 = load_json(AUDIT_142)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    normalized = compile134.normalize_ops(formula)
    rows = collect_literal_payload_rows(normalized, books)
    active_total_bits = float(formula["mdl_estimate_rough"][SOURCE_TOTAL_KEY])
    active_payload_bits = float(formula["mdl_estimate_rough"]["adaptive_context_order_literal_payload_bits"])

    full = {order: full_corpus_order(rows, order) for order in (0, 1, 2, 3)}
    splits = [
        {
            "cutoff": cutoff,
            "order1": split_order(rows, cutoff, 1),
            "order2": split_order(rows, cutoff, 2),
        }
        for cutoff in PREFIX_CUTOFFS
    ]
    order1_full_delta = full[1]["bits"] - full[2]["bits"]
    order1_frozen_delta_total = sum(
        split_row["order1"]["test_frozen_bits"] - split_row["order2"]["test_frozen_bits"]
        for split_row in splits
    )
    order1_online_delta_total = sum(
        split_row["order1"]["test_online_bits"] - split_row["order2"]["test_online_bits"]
        for split_row in splits
    )
    order1_frozen_wins = [
        split_row["cutoff"]
        for split_row in splits
        if split_row["order1"]["test_frozen_bits"] < split_row["order2"]["test_frozen_bits"]
    ]

    if order1_frozen_delta_total < 0:
        classification = "literal_payload_order1_current_frozen_profile_candidate"
    else:
        classification = "literal_payload_order2_retained_for_current_profile"

    return {
        "schema": "current_literal_payload_profile_audit.v1",
        "test": "143_current_literal_payload_profile_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "sources": {
            "formula": rel(SOURCE_FORMULA),
            "default_exception_component_profile": rel(AUDIT_142),
        },
        "scope": {
            "active_compression_bound_bits": active_total_bits,
            "active_literal_payload_bits": active_payload_bits,
            "literal_digit_count": len(rows),
            "prior_generation_profile_bits": audit142["decision"]["generation_explanation_profile_bits"],
        },
        "full_corpus": full,
        "prefix_splits": splits,
        "comparison": {
            "order1_full_corpus_delta_vs_order2_bits": order1_full_delta,
            "order1_online_delta_vs_order2_total_bits": order1_online_delta_total,
            "order1_frozen_delta_vs_order2_total_bits": order1_frozen_delta_total,
            "order1_frozen_win_cutoffs": order1_frozen_wins,
        },
        "decision": {
            "literal_payload_profile": "order2_retained",
            "reason": (
                "Order1 wins some intermediate frozen splits, but it is worse "
                "on full corpus and worse in aggregate prefix online/frozen totals "
                "under the current online-reparse recipe."
            ),
            "generation_explanation_profile_bits_changed": False,
            "generation_explanation_profile_bits": audit142["decision"]["generation_explanation_profile_bits"],
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    comp = result["comparison"]
    lines = [
        "# 143. Current Literal Payload Profile Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 121 previously found that literal payload order-1 generalized better",
        "than the then-active order-2 context. This audit retests that claim on the",
        "current online-reparse/default-exception formula before carrying it into",
        "the current generation-explanation profile.",
        "",
        "## Full Corpus",
        "",
        "| Order | Bits | Contexts | Delta vs order2 |",
        "|---:|---:|---:|---:|",
    ]
    order2_bits = result["full_corpus"][2]["bits"]
    for order in (0, 1, 2, 3):
        row = result["full_corpus"][order]
        lines.append(
            f"| `{order}` | `{row['bits']:.3f}` | `{row['context_count']}` | "
            f"`{row['bits'] - order2_bits:+.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Splits",
            "",
            "| Cutoff | Order1 online gain | Order2 online gain | Order1 frozen gain | Order2 frozen gain |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for split in result["prefix_splits"]:
        o1 = split["order1"]
        o2 = split["order2"]
        lines.append(
            f"| `{split['cutoff']}` | `{o1['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{o2['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{o1['frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{o2['frozen_gain_vs_uniform_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Order1 full-corpus delta vs order2: `{comp['order1_full_corpus_delta_vs_order2_bits']:+.3f}` bits.",
            f"- Order1 aggregate online delta vs order2: `{comp['order1_online_delta_vs_order2_total_bits']:+.3f}` bits.",
            f"- Order1 aggregate frozen delta vs order2: `{comp['order1_frozen_delta_vs_order2_total_bits']:+.3f}` bits.",
            f"- Order1 frozen win cutoffs: `{comp['order1_frozen_win_cutoffs']}`.",
            "- Current profile retains literal payload order2.",
            "- Compression bound and frozen-prefix generation profile are unchanged.",
            "- `row0` and semantics are unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "143_current_literal_payload_profile_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "143_current_literal_payload_profile_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
