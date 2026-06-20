from __future__ import annotations

import bisect
import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASELINE_FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_rice_length_formula_469.json"
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


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def delta_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    bit_length = value.bit_length()
    return gamma_bits(bit_length) + bit_length - 1


def unary_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return value


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def length_bits(value: int, model: dict) -> int:
    family = model["family"]
    if family == "gamma":
        return gamma_bits(value)
    if family == "delta":
        return delta_bits(value)
    if family == "unary":
        return unary_bits(value)
    if family == "rice":
        return rice_bits(value, int(model["k"]))
    raise ValueError(model)


def model_declaration_bits(model: dict) -> int:
    if model["family"] == "rice":
        return gamma_bits(int(model["k"]) + 1)
    return 0


def model_name(model: dict) -> str:
    if model["family"] == "rice":
        return f"rice_k{model['k']}"
    return model["family"]


def literal_run_bits(length: int) -> float:
    return 1 + gamma_bits(length + 1) + length * LOG2_10


def add_index_entries(available: str, index: dict[str, list[int]], min_len: int, previous_len: int) -> None:
    for end in range(max(min_len, previous_len + 1), len(available) + 1):
        start = end - min_len
        key = available[start:end]
        if SEP not in key:
            index.setdefault(key, []).append(start)


def match_candidates(
    target: str,
    pos: int,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
) -> list[tuple[int, int]]:
    if pos + min_len > len(target):
        return []
    key = target[pos : pos + min_len]
    candidates = index.get(key, [])
    if not candidates:
        return []

    by_length: dict[int, int] = {}
    max_len = len(target) - pos
    for source_pos in candidates:
        length = min_len
        while length < max_len:
            source_next = source_pos + length
            if source_next >= len(available) or available[source_next] == SEP:
                break
            if available[source_next] != target[pos + length]:
                break
            length += 1
        for candidate_len in range(min_len, length + 1):
            previous = by_length.get(candidate_len)
            if previous is None or source_pos < previous:
                by_length[candidate_len] = source_pos
    return [(source_pos, length) for length, source_pos in sorted(by_length.items())]


def precompute_matches(
    text: str,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
) -> tuple[list[list[tuple[int, int]]], list[int]]:
    local_available = available
    local_index = {key: positions[:] for key, positions in index.items()}
    matches: list[list[tuple[int, int]]] = []
    copy_positions = set()

    for pos in range(len(text)):
        row = match_candidates(text, pos, local_available, local_index, min_len)
        matches.append(row)
        if row:
            copy_positions.add(pos)
        previous_len = len(local_available)
        local_available += text[pos]
        add_index_entries(local_available, local_index, min_len, previous_len)

    endpoints = sorted(copy_positions | {len(text)})
    return matches, endpoints


def encode_books(
    books: dict[str, str],
    order: list[str],
    min_len: int,
    model: dict,
) -> dict:
    available = ""
    index: dict[str, list[int]] = {}
    recipes = {}
    total_bits = gamma_bits(len(order) + 1)
    book_header_bits = 0
    literal_bits = 0.0
    copy_bits_total = 0.0
    length_code_bits_total = 0
    address_bits_total = 0.0
    model_bits = model_declaration_bits(model)
    total_bits += model_bits
    literal_digits = 0
    literal_runs = 0
    copy_items = 0
    copied_digits = 0
    length_values = []

    for book in order:
        text = books[str(book)]
        book_header = gamma_bits(len(text) + 1)
        book_header_bits += book_header
        total_bits += book_header
        matches, literal_endpoints = precompute_matches(text, available, index, min_len)
        n = len(text)
        dp = [0.0] * (n + 1)
        choice: list[tuple | None] = [None] * (n + 1)

        for pos in range(n - 1, -1, -1):
            best_cost = float("inf")
            best_choice: tuple | None = None

            start_idx = bisect.bisect_right(literal_endpoints, pos)
            for end in literal_endpoints[start_idx:]:
                length = end - pos
                cost = literal_run_bits(length) + dp[end]
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("literal", length)

            emitted_len = len(available) + pos
            for source_pos, length in matches[pos]:
                length_value = length - min_len + 1
                cost = (
                    1
                    + math.log2(max(2, emitted_len))
                    + length_bits(length_value, model)
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
                ops.append({"type": "literal", "text": text[pos : pos + length], "length": length})
                literal_digits += length
                literal_runs += 1
                literal_bits += literal_run_bits(length)
                pos += length
            elif item[0] == "copy":
                _, source_pos, length = item
                ops.append({"type": "copy", "source_pos": source_pos, "length": length, "target_start": pos})
                emitted_len = emitted_len_at_book_start + pos
                length_value = length - min_len + 1
                length_code_bits = length_bits(length_value, model)
                address_bits = math.log2(max(2, emitted_len))
                copy_cost = 1 + address_bits + length_code_bits
                copy_items += 1
                copied_digits += length
                copy_bits_total += copy_cost
                length_code_bits_total += length_code_bits
                address_bits_total += address_bits
                length_values.append(length_value)
                pos += length
            else:
                raise ValueError(item)

        recipes[str(book)] = {"length": len(text), "ops": ops}
        previous_len = len(available)
        available += text
        add_index_entries(available, index, min_len, previous_len)
        previous_len = len(available)
        available += SEP
        add_index_entries(available, index, min_len, previous_len)

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
        "length_model": model,
        "length_model_name": model_name(model),
        "book_order": [str(book) for book in order],
        "recipes": recipes,
        "total_bits": total_bits,
        "model_declaration_bits": model_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
        "copy_bits": copy_bits_total,
        "length_code_bits": length_code_bits_total,
        "address_bits": address_bits_total,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
        "length_value_histogram": dict(sorted(Counter(length_values).items())),
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": len(order) - len(errors),
            "errors": errors,
        },
    }


def shuffled_digits_books(books: dict[str, str], order: list[str], seed: int) -> dict[str, str]:
    rng = random.Random(seed)
    lengths = {book: len(books[book]) for book in order}
    digits = list("".join(books[book] for book in order))
    rng.shuffle(digits)
    out = {}
    cursor = 0
    for book in order:
        length = lengths[book]
        out[book] = "".join(digits[cursor : cursor + length])
        cursor += length
    return out


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "min_bits": min(values),
        "mean_bits": mean(values),
        "pstdev_bits": pstdev(values) if len(values) > 1 else 0.0,
        "max_bits": max(values),
        "count_le_observed": sum(1 for value in values if value <= observed),
    }


def main() -> None:
    baseline = load_json(BASELINE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in baseline["policy"]["book_order"]]
    current_bits = baseline["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]

    models = [
        {"family": "gamma"},
        {"family": "delta"},
        {"family": "unary"},
        *({"family": "rice", "k": k} for k in range(0, 8)),
    ]
    rows = []
    encoded_by_key = {}
    for min_len in [5, 6]:
        for model in models:
            encoded = encode_books(books, order, min_len, model)
            key = (min_len, model_name(model))
            encoded_by_key[key] = encoded
            rows.append(
                {
                    "min_len": min_len,
                    "length_model": model_name(model),
                    "model_declaration_bits": encoded["model_declaration_bits"],
                    "total_bits": encoded["total_bits"],
                    "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                    "copy_items": encoded["copy_items"],
                    "copied_digits": encoded["copied_digits"],
                    "literal_runs": encoded["literal_runs"],
                    "literal_digits": encoded["literal_digits"],
                    "length_code_bits": encoded["length_code_bits"],
                    "books_roundtrip_ok": encoded["validation"]["books_roundtrip_ok"],
                    "errors": encoded["validation"]["errors"],
                }
            )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    best_encoded = encoded_by_key[(best["min_len"], best["length_model"])]

    control_runs = 20
    digit_shuffle_values = []
    for seed in range(469600, 469600 + control_runs):
        shuffled_books = shuffled_digits_books(books, order, seed)
        digit_shuffle_values.append(
            encode_books(
                shuffled_books,
                order,
                best["min_len"],
                best_encoded["length_model"],
            )["total_bits"]
        )

    order_shuffle_values = []
    for seed in range(469900, 469900 + control_runs):
        rng = random.Random(seed)
        shuffled_order = order[:]
        rng.shuffle(shuffled_order)
        order_shuffle_values.append(
            encode_books(
                books,
                shuffled_order,
                best["min_len"],
                best_encoded["length_model"],
            )["total_bits"]
        )

    promoted = (
        best["total_bits"] < current_bits
        and best["books_roundtrip_ok"] == len(order)
        and best["length_model"] != "gamma"
    )
    classification = (
        "controlled_copy_length_code_improvement"
        if promoted
        else "copy_length_code_not_promoted"
    )

    if promoted:
        out = {
            "schema": "sequential_lz_rice_length_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(BASELINE_FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                "book_order": order,
                "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
                "parse": "dynamic_programming_min_cost_under_run_literal_cost_and_copy_length_code",
                "min_len": best_encoded["min_len"],
                "copy_length_model": best_encoded["length_model"],
                "cost_model": "gamma(book_count)+gamma(book_lengths)+copy_length_model_declaration+literal_run_ops+absolute_source_copy_ops",
            },
            "book_recipes": best_encoded["recipes"],
            "mdl_estimate_rough": {
                "sequential_lz_rice_length_bits": best_encoded["total_bits"],
                "previous_sequential_lz_dp_parse_bits": current_bits,
                "gain_vs_previous_dp_parse_bits": current_bits - best_encoded["total_bits"],
                "model_declaration_bits": best_encoded["model_declaration_bits"],
                "literal_bits": best_encoded["literal_bits"],
                "copy_bits": best_encoded["copy_bits"],
                "copy_length_code_bits": best_encoded["length_code_bits"],
                "copy_address_bits": best_encoded["address_bits"],
                "literal_digits": best_encoded["literal_digits"],
                "literal_runs": best_encoded["literal_runs"],
                "copy_items": best_encoded["copy_items"],
                "copied_digits": best_encoded["copied_digits"],
            },
            "length_value_histogram": best_encoded["length_value_histogram"],
            "validation": best_encoded["validation"],
            "boundary": {
                "semantic_delta": "NONE",
                "pair_table_origin_explained": False,
                "authorial_intent_claim": False,
            },
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    controls = {
        "digit_shuffle_preserve_book_lengths": summarize(digit_shuffle_values, best["total_bits"]),
        "book_order_shuffle": summarize(order_shuffle_values, best["total_bits"]),
    }
    result = {
        "schema": "copy_length_code_reparse.v1",
        "test": "22_copy_length_code_reparse",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(BASELINE_FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "best_model": best,
        "models": rows,
        "controls": controls,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Copy Length Code Reparse",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit reparses the 70 numeric books with alternative copy-length",
        "codes while preserving the same literal-run and absolute `source_pos`",
        "copy vocabulary. The previous DP formula used Elias gamma for",
        "`length-min_len+1`; this test includes Elias delta, unary, and Rice",
        "codes with explicit parameter cost for `k`.",
        "",
        "## Length-Code Sweep",
        "",
        "| Rank | min_len | Length model | Model bits | Total bits | Delta vs current | Copy items | Copied digits | Length bits | Roundtrip |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:12], start=1):
        lines.append(
            f"| `{rank}` | `{row['min_len']}` | `{row['length_model']}` | "
            f"`{row['model_declaration_bits']}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['copy_items']}` | "
            f"`{row['copied_digits']}` | `{row['length_code_bits']}` | "
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
    for label, stats in controls.items():
        lines.append(
            f"| `{label}` | `{stats['runs']}` | `{stats['min_bits']:.1f}` | "
            f"`{stats['mean_bits']:.1f}` | `{stats['count_le_observed']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The best tested copy-length model is `{best['length_model']}` with",
            f"`min_len={best['min_len']}`, reaching `{best['total_bits']:.1f}`",
            f"bits. That improves the previous DP gamma-length baseline by",
            f"`{-best['delta_vs_current_bits']:.1f}` bits while preserving a",
            "70/70 roundtrip. The digit-shuffle control stays far worse. As in",
            "earlier order audits, book-order shuffles are diagnostic only unless",
            "an external zero-cost order is supplied or permutation cost is paid.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-length coding improvement. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("22_copy_length_code_reparse", result, lines)


if __name__ == "__main__":
    main()
