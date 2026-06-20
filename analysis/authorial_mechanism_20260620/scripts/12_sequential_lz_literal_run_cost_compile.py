from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
OUT = HERE / "sequential_lz_run_literal_formula_469.json"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SEQ10 = HERE / "scripts" / "10_sequential_lz_book_formula_compile.py"
SEQ10_RESULT = HERE / "reports" / "test_results" / "10_sequential_lz_book_formula_compile.json"

LOG2_10 = math.log2(10)


def load_seq10():
    spec = importlib.util.spec_from_file_location("seq10", SEQ10)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def recost_with_literal_runs(encoded: dict, books: dict[str, str], order: list[str]) -> dict:
    min_len = encoded["min_len"]
    total_bits = gamma_bits(len(order) + 1)
    emitted_len = 0
    literal_digits = 0
    literal_runs = 0
    copy_items = 0
    copied_digits = 0
    copy_bits = 0.0
    literal_bits = 0.0
    book_header_bits = 0

    for book in order:
        recipe = encoded["recipes"][str(book)]
        book_header_bits += gamma_bits(len(books[str(book)]) + 1)
        for op in recipe["ops"]:
            if op["type"] == "literal":
                length = op["length"]
                bits = 1 + gamma_bits(length + 1) + length * LOG2_10
                literal_runs += 1
                literal_digits += length
                literal_bits += bits
                total_bits += bits
                emitted_len += length
            elif op["type"] == "copy":
                length = op["length"]
                bits = 1 + math.log2(max(2, emitted_len)) + gamma_bits(length - min_len + 1)
                copy_items += 1
                copied_digits += length
                copy_bits += bits
                total_bits += bits
                emitted_len += length
            else:
                raise ValueError(op)
        emitted_len += 1  # separator
    total_bits += book_header_bits
    return {
        "total_bits": total_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
        "copy_bits": copy_bits,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
    }


def best_encoding_run_cost(seq10, books: dict[str, str], order: list[str], min_lens: list[int]) -> dict:
    rows = []
    for min_len in min_lens:
        encoded = seq10.encode_books(books, order, min_len)
        cost = recost_with_literal_runs(encoded, books, order)
        rows.append({**encoded, "run_literal_cost": cost})
    rows.sort(key=lambda row: (row["run_literal_cost"]["total_bits"], -row["copied_digits"]))
    best = rows[0]
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


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_bits_le_observed": (sum(value <= observed for value in values) + 1) / (len(values) + 1),
    }


def run_controls(seq10, books: dict[str, str], order: list[str], min_lens: list[int], observed_bits: float, runs: int = 160) -> dict:
    digit_shuffle = []
    random_same_lengths = []
    order_shuffle = []
    for seed in range(runs):
        rng = random.Random(4691200 + seed)
        digit_shuffle.append(
            best_encoding_run_cost(seq10, shuffled_digits_books(books, rng), order, min_lens)["run_literal_cost"][
                "total_bits"
            ]
        )
        random_same_lengths.append(
            best_encoding_run_cost(seq10, random_digits_books(books, rng), order, min_lens)["run_literal_cost"][
                "total_bits"
            ]
        )
        shuffled_order = order[:]
        rng.shuffle(shuffled_order)
        order_shuffle.append(best_encoding_run_cost(seq10, books, shuffled_order, min_lens)["run_literal_cost"]["total_bits"])
    return {
        "within_book_digit_shuffle_bits": summarize(digit_shuffle, observed_bits),
        "random_same_lengths_bits": summarize(random_same_lengths, observed_bits),
        "book_order_shuffle_bits": summarize(order_shuffle, observed_bits),
    }


def classify(best: dict, baseline_bits: float, controls: dict) -> str:
    if best["errors"]:
        return "sequential_lz_run_literal_failed_roundtrip"
    if best["run_literal_cost"]["total_bits"] >= baseline_bits:
        return "sequential_lz_run_literal_not_better"
    if (
        controls["within_book_digit_shuffle_bits"]["p_bits_le_observed"] <= 0.01
        and controls["random_same_lengths_bits"]["p_bits_le_observed"] <= 0.01
    ):
        return "controlled_sequential_lz_run_literal_formula"
    return "sequential_lz_run_literal_generic_compression_not_promoted"


def main() -> None:
    seq10 = load_seq10()
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = sorted(books, key=seq10.numeric_key)
    min_lens = [6, 8, 10, 12, 15, 20]
    baseline = load_json(SEQ10_RESULT)
    baseline_bits = baseline["best_encoding"]["total_bits"]

    best = best_encoding_run_cost(seq10, books, order, min_lens)
    observed_bits = best["run_literal_cost"]["total_bits"]
    controls = run_controls(seq10, books, order, min_lens, observed_bits)
    classification = classify(best, baseline_bits, controls)

    formula = {
        "schema": "sequential_lz_run_literal_formula.v1",
        "classification": classification,
        "scope": "mechanical_generator_only_no_semantics",
        "source_books": str(BOOKS_DIGITS.relative_to(ROOT)),
        "translation_delta": "NONE",
        "policy": {
            "book_order": [str(book) for book in order],
            "min_len": best["min_len"],
            "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
            "cost_model": "gamma(book_count)+gamma(book_lengths)+literal_run_ops+copy_ops",
        },
        "book_recipes": best["recipes"],
        "validation": {
            "book_count": best["book_count"],
            "books_roundtrip_ok": best["books_roundtrip_ok"],
            "errors": best["errors"],
        },
        "mdl_estimate_rough": {
            "sequential_lz_v1_bits": baseline_bits,
            "sequential_lz_run_literal_bits": observed_bits,
            "gain_vs_sequential_lz_v1_bits": baseline_bits - observed_bits,
            "raw_digit_bits": best["baseline_bits"],
            "literal_digits": best["run_literal_cost"]["literal_digits"],
            "literal_runs": best["run_literal_cost"]["literal_runs"],
            "copy_items": best["run_literal_cost"]["copy_items"],
            "copied_digits": best["run_literal_cost"]["copied_digits"],
        },
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }
    OUT.write_text(json.dumps(formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "sequential_lz_literal_run_cost_compile.v1",
        "test": "12_sequential_lz_literal_run_cost_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "output_formula": str(OUT.relative_to(ROOT)),
        "validation": formula["validation"],
        "best_encoding": {
            key: value
            for key, value in best.items()
            if key not in {"recipes", "book_order"}
        },
        "baseline_sequential_lz_v1_bits": baseline_bits,
        "controls": controls,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Sequential LZ Literal-Run Cost Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "The previous sequential LZ formula already emits literal runs, but its",
        "rough cost charged a literal flag per digit. This pass keeps the same",
        "copy/reference generator family and charges each literal run as",
        "`flag + gamma(length+1) + digits`, then lets the real corpus and controls",
        "choose the best `min_len` from the same set.",
        "",
        "## Best Real Encoding",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Min match | `{best['min_len']}` |",
        f"| Run-literal LZ bits | `{observed_bits:.1f}` |",
        f"| Sequential LZ v1 bits | `{baseline_bits:.1f}` |",
        f"| Gain vs v1 | `{baseline_bits - observed_bits:.1f}` |",
        f"| Raw digit baseline bits | `{best['baseline_bits']:.1f}` |",
        f"| Literal digits | `{best['run_literal_cost']['literal_digits']}` |",
        f"| Literal runs | `{best['run_literal_cost']['literal_runs']}` |",
        f"| Copy items | `{best['run_literal_cost']['copy_items']}` |",
        f"| Copied digits | `{best['run_literal_cost']['copied_digits']}` |",
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
            "This is a cost/model refinement of the mechanical copy/reference",
            "generator. It tightens the book fabrication upper bound but does not",
            "explain row0 or introduce plaintext.",
        ]
    )
    write_result("12_sequential_lz_literal_run_cost_compile", result, lines)


if __name__ == "__main__":
    main()
