from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "sequential_lz_book_formula_469.json"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
HIERARCHICAL = HERE / "hierarchical_reference_formula_469.json"

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


def best_previous_match(
    target: str,
    pos: int,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
) -> dict | None:
    if pos + min_len > len(target):
        return None
    key = target[pos : pos + min_len]
    candidates = index.get(key, [])
    if not candidates:
        return None
    max_len = len(target) - pos
    best = None
    for source_pos in candidates:
        length = min_len
        while length < max_len:
            source_next = source_pos + length
            if source_next >= len(available) or available[source_next] == SEP:
                break
            if available[source_next] != target[pos + length]:
                break
            length += 1
        if best is None or length > best["length"] or (
            length == best["length"] and source_pos < best["source_pos"]
        ):
            best = {"source_pos": source_pos, "length": length}
    return best


def merge_literal(ops: list[dict], text: str) -> None:
    if ops and ops[-1]["type"] == "literal":
        ops[-1]["text"] += text
        ops[-1]["length"] += len(text)
    else:
        ops.append({"type": "literal", "text": text, "length": len(text)})


def encode_books(books: dict[str, str], order: list[str], min_len: int) -> dict:
    available = ""
    index: dict[str, list[int]] = {}
    recipes = {}
    literal_digits = 0
    literal_runs = 0
    copy_items = 0
    copied_digits = 0
    total_bits = gamma_bits(len(order) + 1)

    for book in order:
        text = books[book]
        ops: list[dict] = []
        pos = 0
        total_bits += gamma_bits(len(text) + 1)
        while pos < len(text):
            match = best_previous_match(text, pos, available, index, min_len)
            ref_len_bits = gamma_bits(match["length"] - min_len + 1) if match else 0
            ref_pos_bits = math.log2(max(2, len(available))) if match else 0.0
            ref_bits = 1 + ref_pos_bits + ref_len_bits
            lit_bits = 1 + LOG2_10
            if match is not None and match["length"] * lit_bits > ref_bits:
                chunk = text[pos : pos + match["length"]]
                ops.append(
                    {
                        "type": "copy",
                        "source_pos": match["source_pos"],
                        "length": match["length"],
                        "target_start": pos,
                    }
                )
                total_bits += ref_bits
                copy_items += 1
                copied_digits += match["length"]
                previous_len = len(available)
                available += chunk
                add_index_entries(available, index, min_len, previous_len)
                pos += match["length"]
            else:
                chunk = text[pos]
                merge_literal(ops, chunk)
                total_bits += lit_bits
                literal_digits += 1
                previous_len = len(available)
                available += chunk
                add_index_entries(available, index, min_len, previous_len)
                pos += 1
        literal_runs += sum(1 for op in ops if op["type"] == "literal")
        recipes[str(book)] = {"length": len(text), "ops": ops}
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


def best_encoding(books: dict[str, str], order: list[str], min_lens: list[int]) -> dict:
    encodings = [encode_books(books, order, min_len) for min_len in min_lens]
    encodings.sort(key=lambda row: (row["total_bits"], -row["copied_digits"]))
    best = encodings[0]
    best["search_space"] = {"min_lens": min_lens}
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


def summarize(values: list[float], observed: float, lower_is_better: bool = True) -> dict:
    if lower_is_better:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_as_or_more_extreme": p,
    }


def run_controls(books: dict[str, str], order: list[str], min_lens: list[int], observed_bits: float, runs: int = 160) -> dict:
    digit_shuffle_bits = []
    random_bits = []
    order_shuffle_bits = []
    for seed in range(runs):
        rng = random.Random(4691000 + seed)
        digit_shuffle_bits.append(best_encoding(shuffled_digits_books(books, rng), order, min_lens)["total_bits"])
        random_bits.append(best_encoding(random_digits_books(books, rng), order, min_lens)["total_bits"])
        shuffled_order = order[:]
        rng.shuffle(shuffled_order)
        order_shuffle_bits.append(best_encoding(books, shuffled_order, min_lens)["total_bits"])
    return {
        "within_book_digit_shuffle_bits": summarize(digit_shuffle_bits, observed_bits, True),
        "random_same_lengths_bits": summarize(random_bits, observed_bits, True),
        "book_order_shuffle_bits": summarize(order_shuffle_bits, observed_bits, True),
    }


def classify(best: dict, controls: dict, hierarchical_bits: float) -> str:
    if best["errors"]:
        return "sequential_lz_formula_failed_roundtrip"
    if best["total_bits"] >= hierarchical_bits:
        return "sequential_lz_not_better_than_hierarchical"
    if (
        controls["within_book_digit_shuffle_bits"]["p_as_or_more_extreme"] <= 0.01
        and controls["random_same_lengths_bits"]["p_as_or_more_extreme"] <= 0.01
    ):
        if controls["book_order_shuffle_bits"]["p_as_or_more_extreme"] <= 0.05:
            return "controlled_sequential_lz_book_formula"
        return "controlled_sequential_lz_formula_order_not_promoted"
    return "sequential_lz_generic_compression_not_promoted"


def main() -> None:
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    hierarchical = load_json(HIERARCHICAL)
    hierarchical_bits = hierarchical["mdl_estimate_rough"]["hierarchical_reference_formula_bits"]
    order = sorted(books, key=numeric_key)
    min_lens = [6, 8, 10, 12, 15, 20]
    best = best_encoding(books, order, min_lens)
    controls = run_controls(books, order, min_lens, best["total_bits"])
    classification = classify(best, controls, hierarchical_bits)

    output = {
        "schema": "sequential_lz_book_formula.v1",
        "scope": "mechanical_generator_only_no_semantics",
        "source_books": str(BOOKS_DIGITS.relative_to(ROOT)),
        "translation_delta": "NONE",
        "policy": {
            "book_order": best["book_order"],
            "min_len": best["min_len"],
            "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
            "cost_model": "gamma(book_count)+gamma(book_lengths)+literal/copy ops",
        },
        "book_recipes": best["recipes"],
        "validation": {
            "book_count": best["book_count"],
            "books_roundtrip_ok": best["books_roundtrip_ok"],
            "errors": best["errors"],
        },
        "mdl_estimate_rough": {
            "raw_digit_bits": best["baseline_bits"],
            "sequential_lz_bits": best["total_bits"],
            "hierarchical_reference_formula_bits": hierarchical_bits,
            "gain_vs_raw_digit_bits": best["gain_vs_raw_digits_bits"],
            "gain_vs_hierarchical_reference_formula_bits": hierarchical_bits - best["total_bits"],
            "literal_digits": best["literal_digits"],
            "copy_items": best["copy_items"],
            "copied_digits": best["copied_digits"],
        },
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "sequential_lz_book_formula_compile.v1",
        "test": "10_sequential_lz_book_formula_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "validation": output["validation"],
        "best_encoding": {key: value for key, value in best.items() if key != "recipes"},
        "hierarchical_reference_formula_bits": hierarchical_bits,
        "controls": controls,
        "boundary": output["boundary"],
    }

    lines = [
        "# Sequential LZ Book Formula Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This compiler materializes the earlier LZ-style upper-bound idea as a",
        "self-contained book generator: each book is emitted in numeric order as",
        "literal digit runs plus references to already emitted prior-book or",
        "current-prefix digits. The real corpus and every control choose the best",
        "`min_len` from the same search set.",
        "",
        "## Best Real Encoding",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Min match | `{best['min_len']}` |",
        f"| Sequential LZ bits | `{best['total_bits']:.1f}` |",
        f"| Hierarchical reference bits | `{hierarchical_bits:.1f}` |",
        f"| Gain vs hierarchical | `{hierarchical_bits - best['total_bits']:.1f}` |",
        f"| Raw digit baseline bits | `{best['baseline_bits']:.1f}` |",
        f"| Literal digits | `{best['literal_digits']}` |",
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
            f"`{row['min']:.1f}` | `{row['p_as_or_more_extreme']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a mechanical copy/reference generator and a tighter upper bound",
            "on book fabrication cost. It does not explain the row0 pair table and",
            "does not introduce plaintext.",
        ]
    )
    write_result("10_sequential_lz_book_formula_compile", result, lines)


if __name__ == "__main__":
    main()
