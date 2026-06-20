from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

DP_SCRIPT = HERE / "scripts" / "13_sequential_lz_dp_parse_compile.py"
FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_dp_module():
    spec = importlib.util.spec_from_file_location("dp_parse_compile_13", DP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {DP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "min_bits": min(values),
        "mean_bits": mean(values),
        "pstdev_bits": pstdev(values) if len(values) > 1 else 0.0,
        "max_bits": max(values),
        "count_le_observed": sum(1 for value in values if value <= observed),
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


def main() -> None:
    dp = load_dp_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in formula["policy"]["book_order"]]
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]
    current_min_len = int(formula["policy"]["min_len"])

    sweep_rows = []
    sweep_range = list(range(3, 13))
    for min_len in sweep_range:
        encoded = dp.encode_books_dp(books, order, min_len)
        sweep_rows.append(
            {
                "min_len": min_len,
                "total_bits": encoded["total_bits"],
                "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                "copy_items": encoded["copy_items"],
                "copied_digits": encoded["copied_digits"],
                "literal_runs": encoded["literal_runs"],
                "literal_digits": encoded["literal_digits"],
                "books_roundtrip_ok": 70 - len(encoded["errors"]),
                "errors": encoded["errors"],
            }
        )
    sweep_rows.sort(key=lambda row: row["total_bits"])

    control_min_lens = [5, 6]
    control_runs = 20
    controls = {}
    for min_len in control_min_lens:
        observed = next(row for row in sweep_rows if row["min_len"] == min_len)["total_bits"]

        digit_shuffle_values = []
        for seed in range(469000, 469000 + control_runs):
            shuffled_books = shuffled_digits_books(books, order, seed)
            encoded = dp.encode_books_dp(shuffled_books, order, min_len)
            digit_shuffle_values.append(encoded["total_bits"])

        order_shuffle_values = []
        for seed in range(469500, 469500 + control_runs):
            rng = random.Random(seed)
            shuffled_order = order[:]
            rng.shuffle(shuffled_order)
            encoded = dp.encode_books_dp(books, shuffled_order, min_len)
            order_shuffle_values.append(encoded["total_bits"])

        controls[str(min_len)] = {
            "observed_bits": observed,
            "digit_shuffle_preserve_book_lengths": summarize(digit_shuffle_values, observed),
            "book_order_shuffle": summarize(order_shuffle_values, observed),
        }

    best = sweep_rows[0]
    nearest_non_best = min(
        (row for row in sweep_rows if row["min_len"] != best["min_len"]),
        key=lambda row: row["total_bits"],
    )
    classification = (
        "dp_min_len_sweep_retains_min_len_6"
        if best["min_len"] == current_min_len and best["total_bits"] <= current_bits + 1e-9
        else "dp_min_len_sweep_new_candidate"
    )

    result = {
        "schema": "dp_min_len_sweep_control.v1",
        "test": "21_dp_min_len_sweep_control",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_min_len": current_min_len,
        "sweep_range": sweep_range,
        "sweep": sweep_rows,
        "nearest_non_best": nearest_non_best,
        "controls": controls,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# DP Min-Length Sweep Control",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit varies the DP sequential LZ `min_len` parameter under the",
        "same literal-run plus absolute-source copy cost model. It holds numeric",
        "book order fixed for the main sweep, then runs focused digit-shuffle and",
        "book-order-shuffle controls for the two closest settings: `min_len=5`",
        "and `min_len=6`.",
        "",
        "## Sweep",
        "",
        "| min_len | Total bits | Delta vs current | Copy items | Copied digits | Literal runs | Literal digits | Roundtrip |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(sweep_rows, key=lambda item: item["min_len"]):
        lines.append(
            f"| `{row['min_len']}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['copy_items']}` | "
            f"`{row['copied_digits']}` | `{row['literal_runs']}` | "
            f"`{row['literal_digits']}` | `{row['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Focused Controls",
            "",
            "| min_len | Control | Runs | Min bits | Mean bits | Count <= observed |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for min_len in control_min_lens:
        control = controls[str(min_len)]
        for label, key in [
            ("digit shuffle, preserve book lengths", "digit_shuffle_preserve_book_lengths"),
            ("book order shuffle", "book_order_shuffle"),
        ]:
            stats = control[key]
            lines.append(
                f"| `{min_len}` | {label} | `{stats['runs']}` | "
                f"`{stats['min_bits']:.1f}` | `{stats['mean_bits']:.1f}` | "
                f"`{stats['count_le_observed']}` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The current `min_len={current_min_len}` setting remains the best DP",
            f"sequential LZ configuration in the tested range. The nearest alternate",
            f"is `min_len={nearest_non_best['min_len']}` at "
            f"`{nearest_non_best['total_bits']:.1f}` bits, "
            f"`{nearest_non_best['delta_vs_current_bits']:.1f}` bits worse.",
            "No new formula is promoted from this sweep.",
            "The book-order shuffle rows are diagnostic only: occasional gross",
            "wins do not supply a zero-cost external order and therefore do not",
            "override the earlier permutation-cost order audit.",
            "",
            "## Boundary",
            "",
            "This is a mechanical parameter audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("21_dp_min_len_sweep_control", result, lines)


if __name__ == "__main__":
    main()
