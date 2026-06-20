from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_118 = HERE / "scripts" / "118_prequential_generation_model_audit.py"
CONTROL_TRIALS = 1000
RANDOM_SEED = 469120


def load_audit_118():
    spec = importlib.util.spec_from_file_location("prequential_generation_model_audit", AUDIT_118)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_118}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)

    def q(frac: float) -> float:
        index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * frac)))
        return ordered[index]

    return {
        "min": ordered[0],
        "p05": q(0.05),
        "median": q(0.50),
        "p95": q(0.95),
        "max": ordered[-1],
    }


def main() -> None:
    audit118 = load_audit_118()
    frontier = audit118.load_module("minaddr_frontier", audit118.FRONTIER)
    midpoint = audit118.load_module("post_midpoint_frontier", audit118.MIDPOINT)
    context_module = audit118.load_module("copy_length_context", audit118.CONTEXT)
    payload_module = audit118.load_module("literal_payload_context", audit118.PAYLOAD_CONTEXT)
    item_module = audit118.load_module("item_type_context", audit118.ITEM_CONTEXT)

    formula = audit118.load_json(audit118.FORMULA)
    books = {str(key): value for key, value in audit118.load_json(audit118.BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][audit118.CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    copy_rows = context_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    copy_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    payload_alpha = float(formula["policy"]["literal_payload_model"]["alpha"])
    item_model = formula["policy"]["item_type_model"]
    item_alpha = float(item_model["alpha"])
    item_key = audit118.item_context_key(item_model)

    def split(rows: list[dict[str, Any]], train_books: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        train_rows = [row for row in rows if int(row["book_int"]) in train_books]
        holdout_rows = [row for row in rows if int(row["book_int"]) not in train_books]
        return train_rows, holdout_rows

    def score_split(train_books: set[int]) -> dict[str, Any]:
        train_copy, holdout_copy = split(copy_rows, train_books)
        train_payload, holdout_payload = split(payload_rows, train_books)
        train_item, holdout_item = split(item_rows, train_books)

        copy_counts = audit118.copy_counts(train_copy, copy_alpha)
        payload_counts = audit118.fixed_alphabet_counts(
            train_payload,
            alphabet=audit118.DIGITS,
            context_key=audit118.payload_context_key,
            symbol_key="digit",
        )
        item_counts = audit118.fixed_alphabet_counts(
            train_item,
            alphabet=audit118.ITEM_TYPES,
            context_key=item_key,
            symbol_key="item_type",
        )

        copy_online = audit118.score_copy_rows(holdout_copy, copy_counts, copy_alpha, update=True)
        copy_frozen = audit118.score_copy_rows(holdout_copy, copy_counts, copy_alpha, update=False)
        copy_uniform = sum(math.log2(int(row["symbol_count"])) for row in holdout_copy)

        payload_online = audit118.score_fixed_alphabet_rows(
            holdout_payload,
            payload_counts,
            alpha=payload_alpha,
            alphabet=audit118.DIGITS,
            context_key=audit118.payload_context_key,
            symbol_key="digit",
            update=True,
        )
        payload_frozen = audit118.score_fixed_alphabet_rows(
            holdout_payload,
            payload_counts,
            alpha=payload_alpha,
            alphabet=audit118.DIGITS,
            context_key=audit118.payload_context_key,
            symbol_key="digit",
            update=False,
        )
        payload_uniform = len(holdout_payload) * math.log2(10)

        item_online = audit118.score_fixed_alphabet_rows(
            holdout_item,
            item_counts,
            alpha=item_alpha,
            alphabet=audit118.ITEM_TYPES,
            context_key=item_key,
            symbol_key="item_type",
            update=True,
        )
        item_frozen = audit118.score_fixed_alphabet_rows(
            holdout_item,
            item_counts,
            alpha=item_alpha,
            alphabet=audit118.ITEM_TYPES,
            context_key=item_key,
            symbol_key="item_type",
            update=False,
        )
        item_uniform = len(holdout_item) * math.log2(2)

        online_bits = copy_online + payload_online + item_online
        frozen_bits = copy_frozen + payload_frozen + item_frozen
        uniform_bits = copy_uniform + payload_uniform + item_uniform
        return {
            "train_books": sorted(train_books),
            "holdout_books": [book for book in range(70) if book not in train_books],
            "event_counts": {
                "copy_length_holdout_rows": len(holdout_copy),
                "literal_payload_holdout_rows": len(holdout_payload),
                "item_type_holdout_rows": len(holdout_item),
            },
            "holdout_prefix_online_bits": online_bits,
            "holdout_prefix_frozen_bits": frozen_bits,
            "holdout_uniform_bits": uniform_bits,
            "online_vs_uniform_bits": online_bits - uniform_bits,
            "frozen_vs_uniform_bits": frozen_bits - uniform_bits,
        }

    rng = random.Random(RANDOM_SEED)
    rows = []
    for cutoff in audit118.TRAIN_CUTOFFS:
        prefix_books = set(range(cutoff))
        observed = score_split(prefix_books)
        online_controls: list[float] = []
        frozen_controls: list[float] = []
        for _ in range(CONTROL_TRIALS):
            train_books = set(rng.sample(range(70), cutoff))
            score = score_split(train_books)
            online_controls.append(score["online_vs_uniform_bits"])
            frozen_controls.append(score["frozen_vs_uniform_bits"])

        online_p_prefix_better = (
            sum(1 for value in online_controls if value <= observed["online_vs_uniform_bits"]) + 1
        ) / (CONTROL_TRIALS + 1)
        frozen_p_prefix_better = (
            sum(1 for value in frozen_controls if value <= observed["frozen_vs_uniform_bits"]) + 1
        ) / (CONTROL_TRIALS + 1)

        rows.append(
            {
                "train_book_count": cutoff,
                "observed_numeric_prefix": observed,
                "random_train_set_controls": {
                    "trials": CONTROL_TRIALS,
                    "seed": RANDOM_SEED,
                    "online_vs_uniform_bits": {
                        "mean": mean(online_controls),
                        **quantiles(online_controls),
                    },
                    "frozen_vs_uniform_bits": {
                        "mean": mean(frozen_controls),
                        **quantiles(frozen_controls),
                    },
                    "p_control_as_good_or_better_online": online_p_prefix_better,
                    "p_control_as_good_or_better_frozen": frozen_p_prefix_better,
                },
            }
        )

    prefix_online_beats_uniform = sum(
        1 for row in rows if row["observed_numeric_prefix"]["online_vs_uniform_bits"] < 0
    )
    prefix_frozen_beats_uniform = sum(
        1 for row in rows if row["observed_numeric_prefix"]["frozen_vs_uniform_bits"] < 0
    )
    prefix_online_order_specific = sum(
        1
        for row in rows
        if row["random_train_set_controls"]["p_control_as_good_or_better_online"] <= 0.05
    )
    prefix_frozen_order_specific = sum(
        1
        for row in rows
        if row["random_train_set_controls"]["p_control_as_good_or_better_frozen"] <= 0.05
    )
    classification = (
        "prequential_predictive_not_numeric_order_specific"
        if prefix_online_beats_uniform == len(rows)
        and prefix_frozen_beats_uniform == len(rows)
        and prefix_online_order_specific == 0
        and prefix_frozen_order_specific == 0
        else "prequential_numeric_order_signal_partial"
    )

    result = {
        "schema": "prequential_order_control_audit.v1",
        "test": "120_prequential_order_control_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(audit118.FORMULA.relative_to(ROOT)),
        "source_prequential_audit": str((REPORTS / "118_prequential_generation_model_audit.json").relative_to(ROOT)),
        "compression_bound_bits": current_bits,
        "control_trials": CONTROL_TRIALS,
        "random_seed": RANDOM_SEED,
        "rows": rows,
        "summary": {
            "prefix_online_beats_uniform_cutoffs": prefix_online_beats_uniform,
            "prefix_frozen_beats_uniform_cutoffs": prefix_frozen_beats_uniform,
            "prefix_online_order_specific_cutoffs_at_p05": prefix_online_order_specific,
            "prefix_frozen_order_specific_cutoffs_at_p05": prefix_frozen_order_specific,
            "interpretation": (
                "The learned components remain predictive versus uniform, but numeric "
                "prefix training is not unusually good against random same-size train "
                "sets. Treat audit 118 as learned distribution evidence, not as a "
                "numeric book-order generation proof."
            ),
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_order_promoted": False,
        },
    }

    lines = [
        "# 120. Prequential Order Control Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 118 showed that prefix-trained learned components beat uniform on",
        "future books. This control asks whether the numeric prefixes `0..N` are",
        "special, or whether random same-size training sets provide the same or",
        "better learned distributions.",
        "",
        "Lower `vs uniform` values are better because they save more bits.",
        "",
        "## Results",
        "",
        "| Train books | Prefix online vs uniform | Control online mean | Online p(control <= prefix) | Prefix frozen vs uniform | Control frozen mean | Frozen p(control <= prefix) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        observed = row["observed_numeric_prefix"]
        controls = row["random_train_set_controls"]
        lines.append(
            f"| `{row['train_book_count']}` | "
            f"`{observed['online_vs_uniform_bits']:.3f}` | "
            f"`{controls['online_vs_uniform_bits']['mean']:.3f}` | "
            f"`{controls['p_control_as_good_or_better_online']:.4f}` | "
            f"`{observed['frozen_vs_uniform_bits']:.3f}` | "
            f"`{controls['frozen_vs_uniform_bits']['mean']:.3f}` | "
            f"`{controls['p_control_as_good_or_better_frozen']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The prefix-trained components still beat uniform on every cutoff, so",
            "the learned payload/copy-length/item-type distributions are not empty.",
            "However, numeric prefixes are not unusually strong compared with random",
            "same-size train sets; in these controls, random sets usually save more",
            "bits because they sample the full corpus distribution more evenly.",
            "",
            "Therefore the prequential result should be kept as partial learned-",
            "component evidence, not as a proof that the books were authored or",
            "generated in numeric order.",
            "",
            "## Boundary",
            "",
            "- `compression_bound` remains `8561.792` bits.",
            "- No row0/table origin formula is promoted.",
            "- No plaintext, glossary, or authorial-intent claim is introduced.",
        ]
    )

    write_result("120_prequential_order_control_audit", result, lines)


if __name__ == "__main__":
    main()
