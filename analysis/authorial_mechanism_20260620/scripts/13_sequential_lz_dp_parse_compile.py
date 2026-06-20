from __future__ import annotations

import bisect
import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "sequential_lz_dp_parse_formula_469.json"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
RUN_LITERAL_RESULT = HERE / "reports" / "test_results" / "12_sequential_lz_literal_run_cost_compile.json"

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


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def add_index_entries(available: str, index: dict[str, list[int]], min_len: int, previous_len: int) -> None:
    for end in range(max(min_len, previous_len + 1), len(available) + 1):
        start = end - min_len
        key = available[start:end]
        if SEP not in key:
            index.setdefault(key, []).append(start)


def literal_run_bits(length: int) -> float:
    return 1 + gamma_bits(length + 1) + length * LOG2_10


def copy_bits(emitted_len: int, length: int, min_len: int) -> float:
    return 1 + math.log2(max(2, emitted_len)) + gamma_bits(length - min_len + 1)


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


def encode_book_dp(
    text: str,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
) -> tuple[list[dict], float]:
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
            cost = copy_bits(emitted_len, length, min_len) + dp[pos + length]
            if cost < best_cost:
                best_cost = cost
                best_choice = ("copy", source_pos, length)

        if best_choice is None:
            raise RuntimeError(f"no parse choice at position {pos}")
        dp[pos] = best_cost
        choice[pos] = best_choice

    ops: list[dict] = []
    pos = 0
    while pos < n:
        item = choice[pos]
        assert item is not None
        if item[0] == "literal":
            length = item[1]
            ops.append({"type": "literal", "text": text[pos : pos + length], "length": length})
            pos += length
        elif item[0] == "copy":
            _, source_pos, length = item
            ops.append(
                {
                    "type": "copy",
                    "source_pos": source_pos,
                    "length": length,
                    "target_start": pos,
                }
            )
            pos += length
        else:
            raise ValueError(item)

    return ops, dp[0]


def encode_books_dp(books: dict[str, str], order: list[str], min_len: int) -> dict:
    available = ""
    index: dict[str, list[int]] = {}
    recipes = {}
    total_bits = gamma_bits(len(order) + 1)
    book_header_bits = 0
    literal_bits = 0.0
    copy_cost_bits = 0.0
    literal_digits = 0
    literal_runs = 0
    copy_items = 0
    copied_digits = 0

    for book in order:
        text = books[str(book)]
        book_header = gamma_bits(len(text) + 1)
        book_header_bits += book_header
        total_bits += book_header
        ops, op_bits = encode_book_dp(text, available, index, min_len)
        total_bits += op_bits

        emitted_len_at_book_start = len(available)
        pos = 0
        for op in ops:
            if op["type"] == "literal":
                length = op["length"]
                literal_digits += length
                literal_runs += 1
                literal_bits += literal_run_bits(length)
                pos += length
            elif op["type"] == "copy":
                length = op["length"]
                copy_items += 1
                copied_digits += length
                copy_cost_bits += copy_bits(emitted_len_at_book_start + op["target_start"], length, min_len)
                pos += length
            else:
                raise ValueError(op)

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

    baseline_bits = sum(len(books[book]) for book in order) * LOG2_10
    return {
        "min_len": min_len,
        "book_order": [str(book) for book in order],
        "recipes": recipes,
        "total_bits": total_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
        "copy_bits": copy_cost_bits,
        "baseline_bits": baseline_bits,
        "gain_vs_raw_digits_bits": baseline_bits - total_bits,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
        "book_count": len(order),
        "books_roundtrip_ok": len(order) - len(errors),
        "errors": errors,
    }


def best_encoding_dp(books: dict[str, str], order: list[str], min_lens: list[int]) -> dict:
    rows = [encode_books_dp(books, order, min_len) for min_len in min_lens]
    rows.sort(key=lambda row: (row["total_bits"], -row["copied_digits"], row["literal_digits"]))
    best = rows[0]
    best["search_space"] = {"min_lens": min_lens, "parse": "dynamic_programming"}
    return best


def shuffled_digits_books(books: dict[str, str], rng: random.Random) -> dict[str, str]:
    out = {}
    for book, text in books.items():
        chars = list(text)
        rng.shuffle(chars)
        out[book] = "".join(chars)
    return out


def random_digits_books(books: dict[str, str], rng: random.Random) -> dict[str, str]:
    return {
        book: "".join(str(rng.randrange(10)) for _ in range(len(text)))
        for book, text in books.items()
    }


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_bits_le_observed": (sum(value <= observed for value in values) + 1) / (len(values) + 1),
    }


def run_controls(books: dict[str, str], order: list[str], min_lens: list[int], observed_bits: float, runs: int = 100) -> dict:
    digit_shuffle = []
    random_same_lengths = []
    order_shuffle = []
    for seed in range(runs):
        rng = random.Random(4691300 + seed)
        digit_shuffle.append(best_encoding_dp(shuffled_digits_books(books, rng), order, min_lens)["total_bits"])
        random_same_lengths.append(best_encoding_dp(random_digits_books(books, rng), order, min_lens)["total_bits"])
        shuffled_order = order[:]
        rng.shuffle(shuffled_order)
        order_shuffle.append(best_encoding_dp(books, shuffled_order, min_lens)["total_bits"])
    return {
        "within_book_digit_shuffle_bits": summarize(digit_shuffle, observed_bits),
        "random_same_lengths_bits": summarize(random_same_lengths, observed_bits),
        "book_order_shuffle_bits": summarize(order_shuffle, observed_bits),
    }


def classify(best: dict, baseline_bits: float, controls: dict) -> str:
    if best["errors"]:
        return "sequential_lz_dp_parse_failed_roundtrip"
    if best["total_bits"] >= baseline_bits:
        return "sequential_lz_dp_parse_not_better"
    if (
        controls["within_book_digit_shuffle_bits"]["p_bits_le_observed"] <= 0.01
        and controls["random_same_lengths_bits"]["p_bits_le_observed"] <= 0.01
    ):
        return "controlled_sequential_lz_dp_parse_formula"
    return "sequential_lz_dp_parse_generic_compression_not_promoted"


def main() -> None:
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = sorted(books, key=numeric_key)
    min_lens = [6]
    baseline = load_json(RUN_LITERAL_RESULT)
    baseline_bits = baseline["best_encoding"]["run_literal_cost"]["total_bits"]

    best = best_encoding_dp(books, order, min_lens)
    observed_bits = best["total_bits"]
    controls = run_controls(books, order, min_lens, observed_bits)
    classification = classify(best, baseline_bits, controls)

    formula = {
        "schema": "sequential_lz_dp_parse_formula.v1",
        "classification": classification,
        "scope": "mechanical_generator_only_no_semantics",
        "source_books": str(BOOKS_DIGITS.relative_to(ROOT)),
        "translation_delta": "NONE",
        "policy": {
            "book_order": [str(book) for book in order],
            "min_len": best["min_len"],
            "parse": "dynamic_programming_min_cost_under_run_literal_cost",
            "min_len_scope": "fixed_from_prior_best_run_literal_formula",
            "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
            "cost_model": "gamma(book_count)+gamma(book_lengths)+literal_run_ops+absolute_source_copy_ops",
        },
        "book_recipes": best["recipes"],
        "validation": {
            "book_count": best["book_count"],
            "books_roundtrip_ok": best["books_roundtrip_ok"],
            "errors": best["errors"],
        },
        "mdl_estimate_rough": {
            "sequential_lz_run_literal_bits": baseline_bits,
            "sequential_lz_dp_parse_bits": observed_bits,
            "gain_vs_run_literal_bits": baseline_bits - observed_bits,
            "raw_digit_bits": best["baseline_bits"],
            "literal_digits": best["literal_digits"],
            "literal_runs": best["literal_runs"],
            "copy_items": best["copy_items"],
            "copied_digits": best["copied_digits"],
        },
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }
    OUT.write_text(json.dumps(formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "sequential_lz_dp_parse_compile.v1",
        "test": "13_sequential_lz_dp_parse_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "validation": formula["validation"],
        "best_encoding": {
            key: value
            for key, value in best.items()
            if key not in {"recipes", "book_order"}
        },
        "baseline_sequential_lz_run_literal_bits": baseline_bits,
        "controls": controls,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Sequential LZ Dynamic-Parse Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "The previous sequential LZ run-literal formula kept the original greedy",
        "parse. This pass keeps the same copy/reference vocabulary and cost",
        "model, fixes `min_len=6` from that prior best formula, and chooses",
        "each book parse by dynamic programming under the literal-run cost. The",
        "emitted books and copy sources remain mechanical digit operations only.",
        "",
        "## Best Real Encoding",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Min match | `{best['min_len']}` |",
        f"| DP-parse LZ bits | `{observed_bits:.1f}` |",
        f"| Run-literal greedy bits | `{baseline_bits:.1f}` |",
        f"| Gain vs run-literal greedy | `{baseline_bits - observed_bits:.1f}` |",
        f"| Raw digit baseline bits | `{best['baseline_bits']:.1f}` |",
        f"| Literal digits | `{best['literal_digits']}` |",
        f"| Literal runs | `{best['literal_runs']}` |",
        f"| Copy items | `{best['copy_items']}` |",
        f"| Copied digits | `{best['copied_digits']}` |",
        f"| Book roundtrip | `{best['books_roundtrip_ok']}/{best['book_count']}` |",
        "",
        "## Negative Controls",
        "",
        "| Control | Runs | Mean bits | Min bits | p(bits <= observed) |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, row in controls.items():
        lines.append(
            f"| `{key}` | `{row['runs']}` | `{row['mean']:.1f}` | "
            f"`{row['min']:.1f}` | `{row['p_bits_le_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a parser optimization inside the existing mechanical",
            "copy/reference generator. It tightens the book fabrication upper",
            "bound but does not explain row0 or introduce plaintext.",
        ]
    )
    write_result("13_sequential_lz_dp_parse_compile", result, lines)


if __name__ == "__main__":
    main()
