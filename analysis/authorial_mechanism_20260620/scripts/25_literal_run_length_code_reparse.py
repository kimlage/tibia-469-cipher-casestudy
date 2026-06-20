from __future__ import annotations

import bisect
import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

ENCODER_SCRIPT = HERE / "scripts" / "22_copy_length_code_reparse.py"
RICE_FORMULA = HERE / "sequential_lz_rice_length_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_rice_literal_length_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

SEP = "#"
LOG2_10 = math.log2(10)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_encoder_module():
    spec = importlib.util.spec_from_file_location("copy_length_code_reparse_22", ENCODER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {ENCODER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def model_clone(model: dict) -> dict:
    return json.loads(json.dumps(model))


def literal_run_bits(length: int, literal_length_model: dict, encoder) -> float:
    return 1 + encoder.length_bits(length + 1, literal_length_model) + length * LOG2_10


def encode_books(
    books: dict[str, str],
    order: list[str],
    min_len: int,
    copy_length_model: dict,
    literal_length_model: dict,
    encoder,
) -> dict:
    available = ""
    index: dict[str, list[int]] = {}
    recipes = {}
    total_bits = encoder.gamma_bits(len(order) + 1)
    book_header_bits = 0
    literal_bits = 0.0
    copy_bits_total = 0.0
    copy_length_code_bits_total = 0
    literal_length_code_bits_total = 0
    address_bits_total = 0.0
    copy_model_bits = encoder.model_declaration_bits(copy_length_model)
    literal_model_bits = encoder.model_declaration_bits(literal_length_model)
    total_bits += copy_model_bits + literal_model_bits
    literal_digits = 0
    literal_runs = 0
    copy_items = 0
    copied_digits = 0
    copy_length_values = []
    literal_length_values = []

    for book in order:
        text = books[str(book)]
        book_header = encoder.gamma_bits(len(text) + 1)
        book_header_bits += book_header
        total_bits += book_header
        matches, literal_endpoints = encoder.precompute_matches(text, available, index, min_len)
        n = len(text)
        dp = [0.0] * (n + 1)
        choice: list[tuple | None] = [None] * (n + 1)

        for pos in range(n - 1, -1, -1):
            best_cost = float("inf")
            best_choice: tuple | None = None

            start_idx = bisect.bisect_right(literal_endpoints, pos)
            for end in literal_endpoints[start_idx:]:
                length = end - pos
                cost = literal_run_bits(length, literal_length_model, encoder) + dp[end]
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("literal", length)

            emitted_len = len(available) + pos
            for source_pos, length in matches[pos]:
                length_value = length - min_len + 1
                cost = (
                    1
                    + math.log2(max(2, emitted_len))
                    + encoder.length_bits(length_value, copy_length_model)
                    + dp[pos + length]
                )
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("copy", source_pos, length)

            if best_choice is None:
                raise RuntimeError(f"no parse choice at {book}:{pos}")
            dp[pos] = best_cost
            choice[pos] = best_choice

        total_bits += dp[0]

        pos = 0
        ops = []
        emitted_len_at_book_start = len(available)
        while pos < n:
            item = choice[pos]
            assert item is not None
            if item[0] == "literal":
                length = int(item[1])
                text_chunk = text[pos : pos + length]
                ops.append({"type": "literal", "text": text_chunk, "length": length})
                literal_digits += length
                literal_runs += 1
                literal_bits += literal_run_bits(length, literal_length_model, encoder)
                literal_length_code_bits_total += encoder.length_bits(length + 1, literal_length_model)
                literal_length_values.append(length + 1)
                pos += length
            elif item[0] == "copy":
                _, source_pos, length = item
                ops.append({"type": "copy", "source_pos": source_pos, "length": length, "target_start": pos})
                emitted_len = emitted_len_at_book_start + pos
                length_value = length - min_len + 1
                length_code_bits = encoder.length_bits(length_value, copy_length_model)
                address_bits = math.log2(max(2, emitted_len))
                copy_cost = 1 + address_bits + length_code_bits
                copy_items += 1
                copied_digits += length
                copy_bits_total += copy_cost
                copy_length_code_bits_total += length_code_bits
                address_bits_total += address_bits
                copy_length_values.append(length_value)
                pos += length
            else:
                raise ValueError(item)

        recipes[str(book)] = {"length": len(text), "ops": ops}
        previous_len = len(available)
        available += text
        encoder.add_index_entries(available, index, min_len, previous_len)
        previous_len = len(available)
        available += SEP
        encoder.add_index_entries(available, index, min_len, previous_len)

    errors = []
    emitted = ""
    rendered = {}
    for book in order:
        parts = []
        for op in recipes[str(book)]["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                chunk = emitted[op["source_pos"] : op["source_pos"] + op["length"]]
            else:
                raise ValueError(op)
            parts.append(chunk)
            emitted += chunk
        rendered[str(book)] = "".join(parts)
        if rendered[str(book)] != books[str(book)]:
            errors.append(str(book))
        emitted += SEP

    return {
        "min_len": min_len,
        "copy_length_model": model_clone(copy_length_model),
        "copy_length_model_name": encoder.model_name(copy_length_model),
        "literal_length_model": model_clone(literal_length_model),
        "literal_length_model_name": encoder.model_name(literal_length_model),
        "book_order": [str(book) for book in order],
        "recipes": recipes,
        "total_bits": total_bits,
        "copy_model_declaration_bits": copy_model_bits,
        "literal_model_declaration_bits": literal_model_bits,
        "model_declaration_bits": copy_model_bits + literal_model_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
        "copy_bits": copy_bits_total,
        "copy_length_code_bits": copy_length_code_bits_total,
        "literal_length_code_bits": literal_length_code_bits_total,
        "address_bits": address_bits_total,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
        "copy_length_value_histogram": dict(sorted(Counter(copy_length_values).items())),
        "literal_length_value_histogram": dict(sorted(Counter(literal_length_values).items())),
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": len(order) - len(errors),
            "errors": errors,
        },
    }


def main() -> None:
    encoder = load_encoder_module()
    formula = load_json(RICE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in formula["policy"]["book_order"]]
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_rice_length_bits"]
    copy_length_model = formula["policy"]["copy_length_model"]
    current_min_len = int(formula["policy"]["min_len"])
    current_literal_model_name = "gamma"

    literal_models = [
        {"family": "gamma"},
        {"family": "delta"},
        {"family": "unary"},
        *({"family": "rice", "k": k} for k in range(0, 11)),
    ]
    sweep_range = list(range(3, 13))
    rows = []
    encoded_by_key = {}
    for min_len in sweep_range:
        for literal_model in literal_models:
            encoded = encode_books(
                books,
                order,
                min_len,
                copy_length_model,
                literal_model,
                encoder,
            )
            key = (min_len, encoded["literal_length_model_name"])
            encoded_by_key[key] = encoded
            rows.append(
                {
                    "min_len": min_len,
                    "copy_length_model": encoded["copy_length_model_name"],
                    "literal_length_model": encoded["literal_length_model_name"],
                    "model_declaration_bits": encoded["model_declaration_bits"],
                    "literal_model_declaration_bits": encoded["literal_model_declaration_bits"],
                    "total_bits": encoded["total_bits"],
                    "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                    "copy_items": encoded["copy_items"],
                    "copied_digits": encoded["copied_digits"],
                    "literal_runs": encoded["literal_runs"],
                    "literal_digits": encoded["literal_digits"],
                    "copy_length_code_bits": encoded["copy_length_code_bits"],
                    "literal_length_code_bits": encoded["literal_length_code_bits"],
                    "books_roundtrip_ok": encoded["validation"]["books_roundtrip_ok"],
                    "errors": encoded["validation"]["errors"],
                }
            )

    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    best_encoded = encoded_by_key[(best["min_len"], best["literal_length_model"])]
    current_row = next(
        row
        for row in rows
        if row["min_len"] == current_min_len
        and row["literal_length_model"] == current_literal_model_name
    )
    promoted = (
        best["total_bits"] < current_bits
        and best["books_roundtrip_ok"] == len(order)
        and (
            best["min_len"] != current_min_len
            or best["literal_length_model"] != current_literal_model_name
        )
    )
    classification = (
        "controlled_literal_length_code_improvement"
        if promoted
        else "literal_length_code_not_promoted"
    )

    control_runs = 20
    digit_shuffle_values = []
    for seed in range(470100, 470100 + control_runs):
        shuffled_books = encoder.shuffled_digits_books(books, order, seed)
        digit_shuffle_values.append(
            encode_books(
                shuffled_books,
                order,
                best["min_len"],
                copy_length_model,
                best_encoded["literal_length_model"],
                encoder,
            )["total_bits"]
        )

    order_shuffle_values = []
    for seed in range(470300, 470300 + control_runs):
        rng = random.Random(seed)
        shuffled_order = order[:]
        rng.shuffle(shuffled_order)
        order_shuffle_values.append(
            encode_books(
                books,
                shuffled_order,
                best["min_len"],
                copy_length_model,
                best_encoded["literal_length_model"],
                encoder,
            )["total_bits"]
        )

    if promoted:
        out = {
            "schema": "sequential_lz_rice_literal_length_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(RICE_FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                "book_order": order,
                "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
                "parse": "dynamic_programming_min_cost_under_run_literal_cost_copy_length_code_and_literal_length_code",
                "min_len": best_encoded["min_len"],
                "copy_length_model": best_encoded["copy_length_model"],
                "literal_run_length_model": best_encoded["literal_length_model"],
                "cost_model": "gamma(book_count)+gamma(book_lengths)+copy_length_model_declaration+literal_length_model_declaration+literal_run_ops+absolute_source_copy_ops",
            },
            "book_recipes": best_encoded["recipes"],
            "mdl_estimate_rough": {
                "sequential_lz_rice_literal_length_bits": best_encoded["total_bits"],
                "previous_sequential_lz_rice_length_bits": current_bits,
                "gain_vs_previous_rice_length_bits": current_bits - best_encoded["total_bits"],
                "model_declaration_bits": best_encoded["model_declaration_bits"],
                "copy_model_declaration_bits": best_encoded["copy_model_declaration_bits"],
                "literal_model_declaration_bits": best_encoded["literal_model_declaration_bits"],
                "literal_bits": best_encoded["literal_bits"],
                "copy_bits": best_encoded["copy_bits"],
                "copy_length_code_bits": best_encoded["copy_length_code_bits"],
                "literal_length_code_bits": best_encoded["literal_length_code_bits"],
                "copy_address_bits": best_encoded["address_bits"],
                "literal_digits": best_encoded["literal_digits"],
                "literal_runs": best_encoded["literal_runs"],
                "copy_items": best_encoded["copy_items"],
                "copied_digits": best_encoded["copied_digits"],
            },
            "copy_length_value_histogram": best_encoded["copy_length_value_histogram"],
            "literal_length_value_histogram": best_encoded["literal_length_value_histogram"],
            "validation": best_encoded["validation"],
            "boundary": {
                "semantic_delta": "NONE",
                "pair_table_origin_explained": False,
                "authorial_intent_claim": False,
            },
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "literal_run_length_code_reparse.v1",
        "test": "25_literal_run_length_code_reparse",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(RICE_FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
            "current_formula_bits": current_bits,
            "current_model": current_row,
            "best_model": best,
            "controls": {
                "digit_shuffle_preserve_book_lengths": encoder.summarize(
                    digit_shuffle_values, best["total_bits"]
                ),
                "book_order_shuffle": encoder.summarize(order_shuffle_values, best["total_bits"]),
            },
            "sweep_range": sweep_range,
            "literal_rice_k_range": list(range(0, 11)),
            "models": rows,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Literal Run Length Code Reparse",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit reparses the promoted Rice-length sequential LZ formula while",
        "keeping copy-source addressing and copy-length coding fixed. It varies",
        "only the code used for literal-run lengths, including gamma, delta,",
        "unary, and Rice `k=0..10` with explicit parameter cost.",
        "",
        "## Literal-Length Sweep",
        "",
        "| Rank | min_len | Copy length | Literal length | Model bits | Total bits | Delta vs current | Copy items | Literal runs | Literal digits | Literal length bits | Roundtrip |",
        "|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:16], start=1):
        lines.append(
            f"| `{rank}` | `{row['min_len']}` | `{row['copy_length_model']}` | "
            f"`{row['literal_length_model']}` | `{row['model_declaration_bits']}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` | "
            f"`{row['copy_items']}` | `{row['literal_runs']}` | "
            f"`{row['literal_digits']}` | `{row['literal_length_code_bits']}` | "
            f"`{row['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Focused Controls",
            "",
            "| Control | Runs | Min bits | Mean bits | Count <= observed |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label, stats in result["controls"].items():
        lines.append(
            f"| `{label}` | `{stats['runs']}` | `{stats['min_bits']:.1f}` | "
            f"`{stats['mean_bits']:.1f}` | `{stats['count_le_observed']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The best tested literal-length model is `{best['literal_length_model']}`",
            f"with `min_len={best['min_len']}`, reaching `{best['total_bits']:.1f}`",
            f"bits. The previous Rice-length formula costs `{current_bits:.1f}`",
            f"bits, so the controlled delta is `{best['delta_vs_current_bits']:.1f}`",
            "bits with 70/70 roundtrip.",
            "",
            "## Boundary",
            "",
            "This is a mechanical literal-length coding audit only. It does not",
            "alter row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("25_literal_run_length_code_reparse", result, lines)


if __name__ == "__main__":
    main()
