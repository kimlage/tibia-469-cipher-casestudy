from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SEQ10 = HERE / "scripts" / "10_sequential_lz_book_formula_compile.py"


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


def log2_factorial(n: int) -> float:
    return sum(math.log2(value) for value in range(1, n + 1))


def main() -> None:
    seq10 = load_seq10()
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    numeric_order = sorted(books, key=seq10.numeric_key)
    min_lens = [6, 8, 10, 12, 15, 20]
    numeric = seq10.best_encoding(books, numeric_order, min_lens)

    runs = 800
    rng = random.Random(4691100)
    best = None
    values = []
    for _ in range(runs):
        order = numeric_order[:]
        rng.shuffle(order)
        encoded = seq10.best_encoding(books, order, min_lens)
        values.append(encoded["total_bits"])
        if best is None or encoded["total_bits"] < best["total_bits"]:
            best = {**encoded, "book_order": order}

    assert best is not None
    order_cost = log2_factorial(len(numeric_order))
    gross_gain = numeric["total_bits"] - best["total_bits"]
    net_gain_after_order_cost = gross_gain - order_cost
    p_better_or_equal = (sum(value <= numeric["total_bits"] for value in values) + 1) / (runs + 1)
    p_best_or_better = (sum(value <= best["total_bits"] for value in values) + 1) / (runs + 1)
    classification = (
        "order_search_not_promoted_after_permutation_cost"
        if net_gain_after_order_cost <= 0
        else "candidate_order_optimized_sequential_lz"
    )

    result = {
        "schema": "sequential_lz_order_search.v1",
        "test": "11_sequential_lz_order_search",
        "classification": classification,
        "translation_delta": "NONE",
        "numeric_order_bits": numeric["total_bits"],
        "best_sampled_order_bits": best["total_bits"],
        "gross_gain_bits": gross_gain,
        "charged_permutation_bits_log2_70_factorial": order_cost,
        "net_gain_after_order_cost_bits": net_gain_after_order_cost,
        "runs": runs,
        "p_sampled_order_beats_or_equals_numeric": p_better_or_equal,
        "p_sampled_order_beats_or_equals_best": p_best_or_better,
        "best_order": best["book_order"],
        "best_min_len": best["min_len"],
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Sequential LZ Book Order Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit checks whether changing the emission order of the 70 books",
        "improves the sequential LZ book formula enough to justify storing or",
        "explaining a non-numeric order. The sampled order is charged by a rough",
        "`log2(70!)` permutation cost before any promotion.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Numeric-order bits | `{numeric['total_bits']:.1f}` |",
        f"| Best sampled-order bits | `{best['total_bits']:.1f}` |",
        f"| Gross gain | `{gross_gain:.1f}` |",
        f"| Permutation cost `log2(70!)` | `{order_cost:.1f}` |",
        f"| Net gain after order cost | `{net_gain_after_order_cost:.1f}` |",
        f"| Random sampled orders | `{runs}` |",
        f"| p(sampled <= numeric) | `{p_better_or_equal:.4f}` |",
        "",
        "## Boundary",
        "",
        "Some arbitrary orders compress slightly better than numeric order, but the",
        "sampled gain does not pay for the order description. Numeric book order",
        "therefore remains the preferred mechanical default for the sequential LZ",
        "formula unless a source-backed physical/order manifest supplies the order",
        "for free.",
    ]
    write_result("11_sequential_lz_order_search", result, lines)


if __name__ == "__main__":
    main()
