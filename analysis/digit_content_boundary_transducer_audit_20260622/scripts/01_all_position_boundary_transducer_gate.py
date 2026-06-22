#!/usr/bin/env python3
"""All-position digit/content boundary transducer gate.

This is the first concrete gate for the route selected by
`generative_route_frontier_synthesis`: move below operation-token sequences and
test a digit-level content/boundary transducer.

The gate does not grant:

- operation-token sequence;
- book multiset/order;
- exact internal operation starts;
- target-conditioned copy availability.

It scores every internal digit position in derived books 10..69 with a
three-way label: `nonstart`, `literal`, or `copy`. Features are decoder-visible
under teacher-forced emitted prefix: previous digits, position buckets, and
whether recent suffixes have occurred in prior emitted material. Promotion
requires beating both a true-count composition baseline and shuffled-label
controls under prefix holdout.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "digit_content_boundary_transducer_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
ROUTE_SYNTHESIS = (
    ROOT
    / "analysis"
    / "generative_route_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_generative_route_frontier_synthesis.json"
)

JSON_OUT = TEST_RESULTS / "01_all_position_boundary_transducer_gate.json"
MD_OUT = TEST_RESULTS / "01_all_position_boundary_transducer_gate.md"
FINAL_OUT = FRONT / "reports" / "final_digit_content_boundary_transducer_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
LABELS = ["nonstart", "literal", "copy"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def log2_multinomial(counts: Counter[str]) -> float:
    total = sum(counts.values())
    value = math.lgamma(total + 1)
    for count in counts.values():
        value -= math.lgamma(count + 1)
    return value / math.log(2)


def bucket_fraction(pos: int, length: int, bins: int, prefix: str) -> str:
    if length <= 1:
        return f"{prefix}_only"
    frac = pos / length
    idx = min(bins - 1, max(0, int(frac * bins)))
    return f"{prefix}_q{idx:02d}"


def length_bucket(length: int) -> str:
    for cut in [80, 120, 180, 260]:
        if length <= cut:
            return f"booklen_le_{cut}"
    return "booklen_gt_260"


def phase(book: int) -> str:
    return f"phase_{(book // 10) * 10}_{(book // 10) * 10 + 9}"


def build_start_labels(ledger: dict[str, Any]) -> dict[int, dict[int, str]]:
    labels: dict[int, dict[int, str]] = defaultdict(dict)
    for row in ledger["ledger_rows"]:
        book = int(row["book"])
        start = int(row["target_start"])
        if start == 0:
            continue
        labels[book][start] = row["op_type"]
    return labels


def prior_material_for(books: dict[int, str], book: int, pos: int) -> str:
    return "".join(books[idx] for idx in range(book)) + books[book][:pos]


def position_rows(books: dict[int, str], starts: dict[int, dict[int, str]]) -> dict[int, list[dict[str, Any]]]:
    rows_by_book: dict[int, list[dict[str, Any]]] = {}
    for book in range(10, 70):
        text = books[book]
        rows = []
        for pos in range(1, len(text)):
            prefix = text[:pos]
            prev1 = prefix[-1:] or "START"
            prev2 = prefix[-2:] if len(prefix) >= 2 else f"START{prev1}"
            prev3 = prefix[-3:] if len(prefix) >= 3 else f"START{prev2}"
            prior = prior_material_for(books, book, pos)
            suffix2 = prefix[-2:] if len(prefix) >= 2 else ""
            suffix3 = prefix[-3:] if len(prefix) >= 3 else ""
            suffix4 = prefix[-4:] if len(prefix) >= 4 else ""
            # Exclude the suffix occurrence ending at the current prefix.
            prior_without_suffix = prior[:-1]
            row = {
                "book": book,
                "book_length": len(text),
                "label": starts.get(book, {}).get(pos, "nonstart"),
                "phase": phase(book),
                "pos": pos,
                "pos_bucket": bucket_fraction(pos, len(text), 8, "pos"),
                "prev1": prev1,
                "prev2": prev2,
                "prev3": prev3,
                "length_bucket": length_bucket(len(text)),
                "suffix2_seen": "s2_seen" if suffix2 and suffix2 in prior_without_suffix else "s2_new",
                "suffix3_seen": "s3_seen" if suffix3 and suffix3 in prior_without_suffix else "s3_new",
                "suffix4_seen": "s4_seen" if suffix4 and suffix4 in prior_without_suffix else "s4_new",
            }
            rows.append(row)
        rows_by_book[book] = rows
    return rows_by_book


FAMILIES = [
    "global",
    "pos_bucket",
    "length_pos",
    "phase_pos",
    "prev1",
    "prev2",
    "prev3",
    "prev2_pos",
    "prev3_pos",
    "suffix2_seen",
    "suffix3_seen",
    "suffix4_seen",
    "suffix3_pos",
    "prev2_suffix3",
    "length_prev2",
]


def feature(row: dict[str, Any], family: str) -> str:
    if family == "global":
        return "global"
    if family == "pos_bucket":
        return row["pos_bucket"]
    if family == "length_pos":
        return f"{row['length_bucket']}|{row['pos_bucket']}"
    if family == "phase_pos":
        return f"{row['phase']}|{row['pos_bucket']}"
    if family == "prev1":
        return row["prev1"]
    if family == "prev2":
        return row["prev2"]
    if family == "prev3":
        return row["prev3"]
    if family == "prev2_pos":
        return f"{row['prev2']}|{row['pos_bucket']}"
    if family == "prev3_pos":
        return f"{row['prev3']}|{row['pos_bucket']}"
    if family == "suffix2_seen":
        return row["suffix2_seen"]
    if family == "suffix3_seen":
        return row["suffix3_seen"]
    if family == "suffix4_seen":
        return row["suffix4_seen"]
    if family == "suffix3_pos":
        return f"{row['suffix3_seen']}|{row['pos_bucket']}"
    if family == "prev2_suffix3":
        return f"{row['prev2']}|{row['suffix3_seen']}"
    if family == "length_prev2":
        return f"{row['length_bucket']}|{row['prev2']}"
    raise KeyError(family)


def train_counts(rows_by_book: dict[int, list[dict[str, Any]]], books: list[int], family: str) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for book in books:
        for row in rows_by_book[book]:
            counts[feature(row, family)][row["label"]] += 1
    return counts


def score_rows(
    rows_by_book: dict[int, list[dict[str, Any]]],
    books: list[int],
    family: str,
    counts: dict[str, Counter[str]],
    override_labels: dict[tuple[int, int], str] | None = None,
) -> tuple[float, Counter[str], Counter[str]]:
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    bits = 0.0
    actual = Counter()
    predicted = Counter()
    for book in books:
        for row in rows_by_book[book]:
            label = override_labels.get((book, row["pos"]), row["label"]) if override_labels else row["label"]
            context = feature(row, family)
            counter = counts.get(context) or global_counts
            total = sum(counter.values())
            denom = total + ALPHA * len(LABELS)
            prob = (counter.get(label, 0) + ALPHA) / denom
            bits += -math.log2(prob)
            actual[label] += 1
            best_label = min(
                LABELS,
                key=lambda candidate: (
                    -((counter.get(candidate, 0) + ALPHA) / denom),
                    candidate,
                ),
            )
            predicted[best_label] += 1
    return bits, actual, predicted


def composition_bits(rows_by_book: dict[int, list[dict[str, Any]]], books: list[int]) -> float:
    total = 0.0
    for book in books:
        total += log2_multinomial(Counter(row["label"] for row in rows_by_book[book]))
    return total


def descriptor_penalty(counts: dict[str, Counter[str]]) -> float:
    states = len(counts)
    cells = sum(len(counter) for counter in counts.values())
    return math.log2(len(FAMILIES)) + states + 0.25 * cells


def loo_score(rows_by_book: dict[int, list[dict[str, Any]]], train_books: list[int], family: str) -> float:
    if len(train_books) < 2:
        return float("inf")
    total = 0.0
    for heldout in train_books:
        subtrain = [book for book in train_books if book != heldout]
        counts = train_counts(rows_by_book, subtrain, family)
        bits, _, _ = score_rows(rows_by_book, [heldout], family, counts)
        total += bits
    return total + descriptor_penalty(train_counts(rows_by_book, train_books, family))


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def shuffled_label_controls(
    rows_by_book: dict[int, list[dict[str, Any]]],
    test_books: list[int],
    family: str,
    counts: dict[str, Counter[str]],
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    bits = []
    for _ in range(RANDOM_TRIALS):
        override = {}
        for book in test_books:
            labels = [row["label"] for row in rows_by_book[book]]
            rng.shuffle(labels)
            for row, label in zip(rows_by_book[book], labels):
                override[(book, row["pos"])] = label
        value, _, _ = score_rows(rows_by_book, test_books, family, counts, override)
        bits.append(value)
    return {
        "bits_mean": sum(bits) / len(bits),
        "bits_p05": percentile(bits, 5),
        "bits_p50": percentile(bits, 50),
        "bits_p95": percentile(bits, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def metrics(actual: Counter[str], predicted: Counter[str]) -> dict[str, Any]:
    # Predicted counter alone cannot give TP. Compute reported majority behavior;
    # exact TP is intentionally not inferred from aggregate counters.
    starts = actual["literal"] + actual["copy"]
    predicted_starts = predicted["literal"] + predicted["copy"]
    return {
        "actual_copy": actual["copy"],
        "actual_literal": actual["literal"],
        "actual_nonstart": actual["nonstart"],
        "actual_starts": starts,
        "predicted_copy": predicted["copy"],
        "predicted_literal": predicted["literal"],
        "predicted_nonstart": predicted["nonstart"],
        "predicted_starts": predicted_starts,
    }


def cutoff_gate(cutoff: int, rows_by_book: dict[int, list[dict[str, Any]]], seed_offset: int) -> dict[str, Any]:
    train_books = [book for book in range(10, cutoff)]
    test_books = [book for book in range(cutoff, 70)]
    family_scores = [
        {"family": family, "loo_train_mdl_bits": loo_score(rows_by_book, train_books, family)}
        for family in FAMILIES
    ]
    selected_family = min(family_scores, key=lambda item: (item["loo_train_mdl_bits"], item["family"]))["family"]
    counts = train_counts(rows_by_book, train_books, selected_family)
    model_bits, actual, predicted = score_rows(rows_by_book, test_books, selected_family, counts)
    global_counts = train_counts(rows_by_book, train_books, "global")
    global_bits, _, _ = score_rows(rows_by_book, test_books, "global", global_counts)
    comp_bits = composition_bits(rows_by_book, test_books)
    controls = shuffled_label_controls(rows_by_book, test_books, selected_family, counts, seed_offset)
    return {
        "cutoff": cutoff,
        "train_books": train_books,
        "test_books": test_books,
        "test_positions": sum(len(rows_by_book[book]) for book in test_books),
        "selected_family": selected_family,
        "family_scores": family_scores,
        "model_bits": model_bits,
        "global_bits": global_bits,
        "composition_bits": comp_bits,
        "delta_vs_global": model_bits - global_bits,
        "delta_vs_composition": model_bits - comp_bits,
        "beats_composition": model_bits < comp_bits,
        "beats_shuffled_p05": model_bits < controls["bits_p05"],
        "label_metrics": metrics(actual, predicted),
        "shuffled_label_controls": controls,
    }


def make_result() -> dict[str, Any]:
    route = load_json(ROUTE_SYNTHESIS)
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("generative_route_frontier_synthesis", route)
    assert_boundary("unified_residual_control_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    starts = build_start_labels(ledger)
    rows_by_book = position_rows(books, starts)
    cutoff_rows = [
        cutoff_gate(cutoff, rows_by_book, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    total_model = sum(row["model_bits"] for row in cutoff_rows)
    total_global = sum(row["global_bits"] for row in cutoff_rows)
    total_comp = sum(row["composition_bits"] for row in cutoff_rows)
    beats_comp = sum(row["beats_composition"] for row in cutoff_rows)
    beats_shuffle = sum(row["beats_shuffled_p05"] for row in cutoff_rows)
    total_actual_starts = sum(row["label_metrics"]["actual_starts"] for row in cutoff_rows)
    total_predicted_starts = sum(row["label_metrics"]["predicted_starts"] for row in cutoff_rows)
    promoted = total_model < total_comp and beats_comp >= 4 and beats_shuffle >= 4 and total_predicted_starts > 0
    weak = total_model < total_global and beats_shuffle >= 3
    classification = (
        "PROMOTED_DIGIT_BOUNDARY_TRANSDUCER_CANDIDATE"
        if promoted
        else "WEAK_DIGIT_BOUNDARY_CLUE_NOT_GENERATOR"
        if weak
        else "DIGIT_BOUNDARY_TRANSDUCER_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": promoted,
            "grants_exact_internal_starts": False,
            "grants_operation_token_sequence": False,
            "grants_target_conditioned_copy_availability": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "generative_route_frontier_synthesis": rel(ROUTE_SYNTHESIS),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "all_position_digit_boundary_transducer_gate.v1",
        "scope": "analysis_only_digit_prefix_features_for_internal_start_and_mode_labels",
        "summary": {
            "beats_composition_cells": beats_comp,
            "beats_shuffled_p05_cells": beats_shuffle,
            "cutoffs": CUTOFFS,
            "total_actual_starts": total_actual_starts,
            "total_composition_bits": total_comp,
            "total_delta_vs_composition": total_model - total_comp,
            "total_delta_vs_global": total_model - total_global,
            "total_global_bits": total_global,
            "total_model_bits": total_model,
            "total_predicted_starts": total_predicted_starts,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# All-Position Digit Boundary Transducer Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test the selected digit-level content/boundary route without granting the "
        "operation-token sequence, exact internal starts, or target-conditioned copy "
        "availability. Every internal digit position is labeled as `nonstart`, "
        "`literal`, or `copy`.",
        "",
        "## Summary",
        "",
        f"- Model bits: `{s['total_model_bits']:.3f}`.",
        f"- Global label bits: `{s['total_global_bits']:.3f}`.",
        f"- Composition baseline bits: `{s['total_composition_bits']:.3f}`.",
        f"- Delta vs global: `{s['total_delta_vs_global']:.3f}` bits.",
        f"- Delta vs composition: `{s['total_delta_vs_composition']:.3f}` bits.",
        f"- Cells beating composition: `{s['beats_composition_cells']}/5`.",
        f"- Cells beating shuffled-label p05: `{s['beats_shuffled_p05_cells']}/5`.",
        f"- Actual start labels: `{s['total_actual_starts']}`.",
        f"- Predicted start labels: `{s['total_predicted_starts']}`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Family | Positions | Model bits | Composition bits | Delta | Shuffle p05 | Predicted starts |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_family']}` | `{row['test_positions']}` | "
            f"`{row['model_bits']:.3f}` | `{row['composition_bits']:.3f}` | "
            f"`{row['delta_vs_composition']:.3f}` | `{row['beats_shuffled_p05']}` | "
            f"`{row['label_metrics']['predicted_starts']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires reducing the true-count composition baseline and "
            "beating shuffled-label controls. Beating only global/nonstart-heavy "
            "coding is not enough to reduce the internal-start dependency.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Digit Content Boundary Transducer Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can decoder-visible digit-prefix/content features derive internal operation "
        "starts and literal/copy modes without granting the operation-token sequence "
        "or target-conditioned copy availability?",
        "",
        "## Result",
        "",
        f"The all-position model costs `{s['total_model_bits']:.3f}` bits versus "
        f"`{s['total_composition_bits']:.3f}` true-count composition bits "
        f"(`{s['total_delta_vs_composition']:.3f}` bits worse). It beats composition in "
        f"`{s['beats_composition_cells']}/5` cells and shuffled-label p05 in "
        f"`{s['beats_shuffled_p05_cells']}/5` cells. Across held-out scoring it "
        f"has `{s['total_actual_starts']}` true start labels and predicts "
        f"`{s['total_predicted_starts']}` start labels.",
        "",
        "## Decision",
        "",
        "This is the first strict pilot of the selected digit/content-boundary route. "
        "It is promoted only if it reduces the internal-start/mode dependency after "
        "controls. Row0, plaintext, translation, and compression_bound remain "
        "unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)",
        "- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)",
        "- [01_all_position_boundary_transducer_gate.md](test_results/01_all_position_boundary_transducer_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
