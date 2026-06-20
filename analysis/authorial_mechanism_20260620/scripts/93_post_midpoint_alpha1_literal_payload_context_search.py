from __future__ import annotations

import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits"
DIGITS = [str(i) for i in range(10)]
BOS_DIGIT = "^"


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


def contextual_payload_declaration_bits(current_declaration_bits: int, context_count: int) -> int:
    return current_declaration_bits + 1 + gamma_bits(context_count + 1)


def searched_split_declaration_bits(current_declaration_bits: int, context_count: int, split_book: int) -> int:
    return contextual_payload_declaration_bits(current_declaration_bits, context_count) + gamma_bits(split_book + 1)


def collect_literal_digit_rows(formula: dict, books: dict[str, str]) -> list[dict]:
    model = formula["policy"]["literal_payload_model"]
    order = int(model["order"])
    emitted = ""
    rows = []
    literal_run_id = 0

    for book_index, book in enumerate(map(str, formula["policy"]["book_order"])):
        book_parts = []
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            length = int(op["length"])
            if op["type"] == "literal":
                text = op["text"]
                if len(text) != length:
                    raise RuntimeError((book, "literal_length_mismatch", op_index, op))
                for literal_offset, digit in enumerate(text):
                    previous_context = (BOS_DIGIT * order + emitted)[-order:]
                    rows.append(
                        {
                            "literal_digit_id": len(rows),
                            "literal_run_id": literal_run_id,
                            "book": book,
                            "book_int": int(book),
                            "book_index": book_index,
                            "op_index": op_index,
                            "book_pos": book_pos + literal_offset,
                            "literal_offset": literal_offset,
                            "literal_run_length": length,
                            "digit": digit,
                            "previous_digit_context": previous_context,
                            "global_digit_pos": len(emitted),
                        }
                    )
                    emitted += digit
                chunk = text
                literal_run_id += 1
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    raise RuntimeError((book, "short_copy", op_index, op))
                emitted += chunk
            else:
                raise ValueError(op)
            book_parts.append(chunk)
            book_pos += length
        if "".join(book_parts) != books[book]:
            raise RuntimeError(f"formula does not roundtrip book {book}")

    return rows


def payload_bits(
    rows: list[dict],
    alpha: float,
    context_fn: Callable[[dict], object],
) -> tuple[float, list[dict], dict[str, int]]:
    counts = defaultdict(lambda: {digit: 0.0 for digit in DIGITS})
    totals = defaultdict(float)
    context_uses: dict[str, int] = {}
    audit_rows = []
    bits = 0.0

    for row in rows:
        context_value = context_fn(row)
        context_label = json.dumps(context_value, sort_keys=True) if not isinstance(context_value, str) else context_value
        context = (context_label, row["previous_digit_context"])
        digit = row["digit"]
        probability = (counts[context][digit] + alpha) / (totals[context] + len(DIGITS) * alpha)
        bit_cost = -math.log2(probability)
        bits += bit_cost
        counts[context][digit] += 1.0
        totals[context] += 1.0
        context_uses[context_label] = context_uses.get(context_label, 0) + 1
        audit_rows.append(
            {
                **row,
                "payload_context": context_label,
                "adaptive_payload_bits": bit_cost,
                "previous_context_observations": totals[context] - 1.0,
                "previous_context_same_digit_observations": counts[context][digit] - 1.0,
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

    model = formula["policy"]["literal_payload_model"]
    alpha = float(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    current_payload_bits = float(current_score["literal_payload_bits"])
    fixed_nonpayload_bits = current_bits - current_payload_bits
    literal_rows = collect_literal_digit_rows(formula, books)

    active_bits, active_audit_rows, active_context_counts = payload_bits(literal_rows, alpha, lambda _row: "global")
    if abs(active_bits - current_payload_bits) > 1e-6:
        raise RuntimeError((active_bits, current_payload_bits))

    candidate_specs: list[tuple[str, str, str, Callable[[dict], object]]] = [
        (
            "active_global_literal_payload_context",
            "active_global",
            "single global payload context",
            lambda _row: "global",
        ),
        (
            "book_midpoint_35_literal_payload_context",
            "fixed_book_midpoint",
            "book_id < 35 versus book_id >= 35",
            lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
        ),
        (
            "book_quartile_literal_payload_context",
            "fixed_book_quartile",
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_literal_payload_context",
            "fixed_book_decade",
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_literal_payload_context",
            "fixed_book_parity",
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "literal_run_length_log_context",
            "literal_run_length",
            "log bucket of current literal-run length",
            lambda row: log_bucket(int(row["literal_run_length"]), 6),
        ),
        (
            "literal_offset_log_context",
            "literal_offset",
            "log bucket of digit offset inside the literal run",
            lambda row: log_bucket(int(row["literal_offset"]) + 1, 6),
        ),
        (
            "copy_index_proxy_global_position_context",
            "global_position",
            "log bucket of generated digit position before literal digit",
            lambda row: log_bucket(int(row["global_digit_pos"]) + 1, 14),
        ),
    ]

    models = []
    for name, family, description, context_fn in candidate_specs:
        bits, audit_rows, counts = payload_bits(literal_rows, alpha, context_fn)
        context_count = len(counts)
        declaration_bits = (
            current_declaration_bits
            if name == "active_global_literal_payload_context"
            else contextual_payload_declaration_bits(current_declaration_bits, context_count)
        )
        total_bits = fixed_nonpayload_bits + bits + declaration_bits - current_declaration_bits
        models.append(
            {
                "model": name,
                "family": family,
                "context_description": description,
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": context_count,
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_payload_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
                "audit_rows": audit_rows,
            }
        )

    searched_split_rows = []
    for split_book in range(1, 70):
        bits, audit_rows, counts = payload_bits(
            literal_rows,
            alpha,
            lambda row, split_book=split_book: "before_split"
            if int(row["book_int"]) < split_book
            else "after_split",
        )
        declaration_bits = searched_split_declaration_bits(current_declaration_bits, len(counts), split_book)
        total_bits = fixed_nonpayload_bits + bits + declaration_bits - current_declaration_bits
        searched_split_rows.append(
            {
                "model": "searched_single_book_split_literal_payload_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": len(counts),
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_payload_bits,
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
        best_decodable["model"] != "active_global_literal_payload_context"
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    classification = (
        "controlled_post_midpoint_literal_payload_context_improvement"
        if promoted
        else "post_midpoint_literal_payload_context_not_promoted"
    )

    result = {
        "schema": "post_midpoint_alpha1_literal_payload_context_search.v1",
        "test": "93_post_midpoint_alpha1_literal_payload_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "literal_digit_items": len(literal_rows),
        "literal_runs": len({row["literal_run_id"] for row in literal_rows}),
        "current_literal_payload_bits": current_payload_bits,
        "current_literal_payload_model_declaration_bits": current_declaration_bits,
        "best_model": strip_audit_rows(best_decodable),
        "models": [strip_audit_rows(row) for row in models],
        "searched_single_split_models": [
            strip_audit_rows(row)
            for row in sorted(searched_split_rows, key=lambda row: row["total_bits"])
        ],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable literal-payload context beats the active "
            "global previous-emitted-digit payload model after charged declaration "
            "bits while preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Midpoint Alpha1 Literal Payload Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests whether the adaptive literal payload model should be",
        "split by a simple context after the midpoint alpha=1 formula became",
        "active. The recipe, literal-run length model, copy-address ledger,",
        "copy-length model, item-type model, forced rules, and book-length ledger",
        "are fixed.",
        "",
        "## Payload Context Models",
        "",
        "| Rank | Model | Contexts | Payload bits | Model bits | Total bits | Delta vs current | Component delta |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['context_count']}` | "
            f"`{row['literal_payload_bits']:.3f}` | `{row['literal_payload_model_declaration_bits']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['component_delta_bits']:.3f}` |"
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
            "A literal-payload context is promoted only if its component savings",
            "survive the extra declaration cost. Otherwise the active global",
            "previous-emitted-digit payload model remains the current formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical payload-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("93_post_midpoint_alpha1_literal_payload_context_search", result, lines)


if __name__ == "__main__":
    main()
