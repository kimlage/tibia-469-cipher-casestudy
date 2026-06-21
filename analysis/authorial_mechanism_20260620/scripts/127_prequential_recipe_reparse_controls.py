from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_126 = HERE / "scripts" / "126_prequential_recipe_reparse_audit.py"
CONTROL_CUTOFFS = [20, 35, 50]
CONTROL_TRIALS = 8
RANDOM_SEED = 46920260620


def load_audit_126():
    spec = importlib.util.spec_from_file_location("prequential_recipe_reparse_audit", AUDIT_126)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_126}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def summarize(values: list[float], observed: float) -> dict[str, float | int]:
    if not values:
        raise ValueError("empty control values")
    return {
        "trials": len(values),
        "min": min(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "max": max(values),
        "p_control_ge_observed": (1 + sum(value >= observed for value in values)) / (len(values) + 1),
    }


def random_digits_like(books: dict[str, str], test_books: list[int], rng: random.Random) -> dict[str, str]:
    out = dict(books)
    for book in test_books:
        text = books[str(book)]
        out[str(book)] = "".join(str(rng.randrange(10)) for _ in text)
    return out


def shuffle_each_book(books: dict[str, str], test_books: list[int], rng: random.Random) -> dict[str, str]:
    out = dict(books)
    for book in test_books:
        chars = list(books[str(book)])
        rng.shuffle(chars)
        out[str(book)] = "".join(chars)
    return out


def shuffle_suffix_pool(books: dict[str, str], test_books: list[int], rng: random.Random) -> dict[str, str]:
    out = dict(books)
    lengths = {book: len(books[str(book)]) for book in test_books}
    pool = list("".join(books[str(book)] for book in test_books))
    rng.shuffle(pool)
    cursor = 0
    for book in test_books:
        length = lengths[book]
        out[str(book)] = "".join(pool[cursor : cursor + length])
        cursor += length
    return out


def raw_uniform_bits(books: dict[str, str], test_books: list[int]) -> float:
    return sum(len(books[str(book)]) for book in test_books) * math.log2(10)


def run_reparse_gain(audit126, *, formula: dict[str, Any], books: dict[str, str], cutoff: int, train_counts: dict[str, Any]) -> dict[str, Any]:
    reparse = audit126.reparse_suffix(cutoff=cutoff, formula=formula, books=books, train_counts=train_counts)
    test_books = list(range(cutoff, 70))
    raw_bits = raw_uniform_bits(books, test_books)
    return {
        "bits": reparse["aggregate"]["bits"],
        "raw_uniform_bits": raw_bits,
        "gain_vs_raw_bits": raw_bits - reparse["aggregate"]["bits"],
        "roundtrip": reparse["validation"],
    }


def main() -> None:
    audit126 = load_audit_126()
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for cutoff in CONTROL_CUTOFFS:
        train_counts = audit126.train_counts_for_cutoff(
            cutoff=cutoff,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        test_books = list(range(cutoff, 70))
        observed = run_reparse_gain(audit126, formula=formula, books=books, cutoff=cutoff, train_counts=train_counts)
        control_values: dict[str, list[float]] = {
            "random_same_lengths": [],
            "shuffle_each_book": [],
            "shuffle_suffix_pool": [],
        }
        control_roundtrip_failures = {key: 0 for key in control_values}
        for trial in range(CONTROL_TRIALS):
            rng = random.Random(RANDOM_SEED + cutoff * 1000 + trial)
            controls = {
                "random_same_lengths": random_digits_like(books, test_books, rng),
                "shuffle_each_book": shuffle_each_book(books, test_books, rng),
                "shuffle_suffix_pool": shuffle_suffix_pool(books, test_books, rng),
            }
            for name, control_books in controls.items():
                row = run_reparse_gain(
                    audit126,
                    formula=formula,
                    books=control_books,
                    cutoff=cutoff,
                    train_counts=train_counts,
                )
                control_values[name].append(float(row["gain_vs_raw_bits"]))
                if row["roundtrip"]["books_roundtrip_ok"] != row["roundtrip"]["book_count"]:
                    control_roundtrip_failures[name] += 1

        rows.append(
            {
                "cutoff": cutoff,
                "test_book_count": len(test_books),
                "observed": observed,
                "controls": {
                    name: summarize(values, float(observed["gain_vs_raw_bits"]))
                    for name, values in control_values.items()
                },
                "control_roundtrip_failures": control_roundtrip_failures,
            }
        )

    observed_beats_all_control_means = all(
        all(row["observed"]["gain_vs_raw_bits"] > control["mean"] for control in row["controls"].values())
        for row in rows
    )
    observed_stronger_than_random_same_lengths = all(
        row["controls"]["random_same_lengths"]["p_control_ge_observed"] <= 1 / (CONTROL_TRIALS + 1)
        for row in rows
    )
    classification = (
        "controlled_recipe_reparse_signal_above_negative_controls"
        if observed_beats_all_control_means and observed_stronger_than_random_same_lengths
        else "recipe_reparse_control_signal_mixed"
    )

    result = {
        "schema": "prequential_recipe_reparse_controls.v1",
        "test": "127_prequential_recipe_reparse_controls",
        "classification": classification,
        "translation_delta": "NONE",
        "source_audit": rel(AUDIT_126),
        "control_cutoffs": CONTROL_CUTOFFS,
        "control_trials": CONTROL_TRIALS,
        "rows": rows,
        "summary": {
            "observed_beats_all_control_means": observed_beats_all_control_means,
            "observed_stronger_than_random_same_lengths_at_all_cutoffs": observed_stronger_than_random_same_lengths,
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "translation_claim": False,
            "plaintext_claim": False,
            "case_reopened": False,
        },
    }

    lines = [
        "# 127. Prequential Recipe Reparse Controls",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 126 showed that deterministic frozen-count reparsing beats raw",
        "digits and the active suffix recipe. This control audit asks whether that",
        "signal is stronger than simple negative controls with the same train",
        "prefix and test-book lengths.",
        "",
        "Controls:",
        "",
        "- `random_same_lengths`: each test book is replaced by iid decimal digits.",
        "- `shuffle_each_book`: each test book keeps its digit multiset but is shuffled.",
        "- `shuffle_suffix_pool`: the whole test suffix digit pool is shuffled and",
        "  repartitioned into the same book lengths.",
        "",
        "## Result",
        "",
        "| Cutoff | Observed gain | Random mean | Random p>=obs | Per-book shuffle mean | Pool shuffle mean |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        controls = row["controls"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed']['gain_vs_raw_bits']:.3f}` | "
            f"`{controls['random_same_lengths']['mean']:.3f}` | "
            f"`{controls['random_same_lengths']['p_control_ge_observed']:.4f}` | "
            f"`{controls['shuffle_each_book']['mean']:.3f}` | "
            f"`{controls['shuffle_suffix_pool']['mean']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The observed suffixes beat random same-length controls at every tested",
            "cutoff. This makes the audit-126 recipe-reparse signal harder to dismiss",
            "as generic LZ behavior on long decimal strings. The shuffled controls",
            "remain useful diagnostics for digit-multiset effects and are kept in",
            "the JSON for exact comparison.",
            "",
            "This remains analysis-only. It does not lower `compression_bound`,",
            "derive `row0`, translate the books, or promote an authorial method.",
        ]
    )
    write_result("127_prequential_recipe_reparse_controls", result, lines)


if __name__ == "__main__":
    main()
