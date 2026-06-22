#!/usr/bin/env python3
"""Sequence mutation program gate.

Recent gates showed that per-book token bags and within-book order do not
separate cleanly into a generator. This gate tests a joint alternative: maybe a
future book's operation-token sequence is produced by mutating a previous
book-level sequence.

The edit cost here is intentionally labeled a lower bound:

- exact target tokens inserted/substituted are charged with a prefix token model;
- edit operations are charged, but matched-position coding is not fully paid;
- oracle source choice is reported separately and never promoted.

If even this optimistic edit program fails, sequence-mutation reuse is not the
next main route. If it succeeds, it is only a clue requiring a stricter codec.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "sequence_mutation_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
ORDER_AUDIT = (
    ROOT
    / "analysis"
    / "within_book_order_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_within_book_order_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_sequence_mutation_program_gate.json"
MD_OUT = TEST_RESULTS / "01_sequence_mutation_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_sequence_mutation_program_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
ACTION_BITS = math.log2(3)
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
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


def occ_bucket(value: int | None) -> str:
    if value is None:
        return "occ_none"
    if value <= 1:
        return "occ_1"
    if value <= 3:
        return "occ_2_3"
    return "occ_4p"


def literal_tape_bucket(row: dict[str, Any], max_tape_end: int) -> str:
    start = row.get("literal_tape_start")
    if start is None:
        return "lit_tape_none"
    bucket = min(5, max(0, int((start / max(1, max_tape_end)) * 6)))
    return f"lit_tape_q{bucket:02d}"


def behavior_symbol(row: dict[str, Any], max_tape_end: int) -> str:
    if row["op_type"] == "literal":
        return f"lit:{row['length_bucket']}:{literal_tape_bucket(row, max_tape_end)}"
    rank_bucket = row.get("copy_hint_rank_bucket") or "rank_none"
    return f"copy:{row['length_bucket']}:{rank_bucket}:{occ_bucket(row.get('copy_hint_source_occurrences'))}"


def load_books() -> dict[int, dict[str, Any]]:
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("unified_residual_control_ledger", ledger)
    max_tape_end = max(
        int(row["literal_tape_end"])
        for row in ledger["ledger_rows"]
        if row.get("literal_tape_end") is not None
    )
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in ledger["ledger_rows"]:
        row = dict(raw)
        row["control_symbol"] = row["type_length_symbol"]
        row["behavior_symbol"] = behavior_symbol(row, max_tape_end)
        row["joint_token"] = f"{row['control_symbol']}|{row['behavior_symbol']}"
        grouped[int(row["book"])].append(row)
    books = {}
    for book, rows in grouped.items():
        rows = sorted(rows, key=lambda row: int(row["op_index"]))
        tokens = [row["joint_token"] for row in rows]
        books[book] = {
            "book": book,
            "book_length": int(rows[0]["book_length"]),
            "book_phase": rows[0]["book_phase"],
            "copy_count": sum(row["op_type"] == "copy" for row in rows),
            "literal_count": sum(row["op_type"] == "literal" for row in rows),
            "op_count": len(tokens),
            "tokens": tokens,
        }
    return books


def token_model(books: dict[int, dict[str, Any]], train_ids: list[int]) -> tuple[Counter[str], set[str]]:
    counts = Counter()
    vocab = set()
    for book in train_ids:
        counts.update(books[book]["tokens"])
        vocab.update(books[book]["tokens"])
    return counts, vocab


def token_bits(token: str, counts: Counter[str], vocab: set[str]) -> float:
    total = sum(counts.values())
    vocab_size = max(1, len(vocab | {token}))
    prob = (counts.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)
    return -math.log2(prob)


def sequence_unigram_bits(tokens: list[str], counts: Counter[str], vocab: set[str]) -> float:
    return sum(token_bits(token, counts, vocab) for token in tokens)


def edit_lower_bound_bits(
    source: list[str],
    target: list[str],
    counts: Counter[str],
    vocab: set[str],
) -> tuple[float, dict[str, int]]:
    # Optimistic weighted Levenshtein. Matches are free; insert/substitute pay
    # target token payload plus an edit action. Delete pays only an action.
    rows = len(source) + 1
    cols = len(target) + 1
    dp = [[0.0 for _ in range(cols)] for _ in range(rows)]
    ops = [[{"insert": 0, "delete": 0, "substitute": 0, "match": 0} for _ in range(cols)] for _ in range(rows)]
    for i in range(1, rows):
        dp[i][0] = dp[i - 1][0] + ACTION_BITS
        ops[i][0] = dict(ops[i - 1][0])
        ops[i][0]["delete"] += 1
    for j in range(1, cols):
        dp[0][j] = dp[0][j - 1] + ACTION_BITS + token_bits(target[j - 1], counts, vocab)
        ops[0][j] = dict(ops[0][j - 1])
        ops[0][j]["insert"] += 1
    for i in range(1, rows):
        for j in range(1, cols):
            choices: list[tuple[float, str, dict[str, int]]] = []
            if source[i - 1] == target[j - 1]:
                next_ops = dict(ops[i - 1][j - 1])
                next_ops["match"] += 1
                choices.append((dp[i - 1][j - 1], "match", next_ops))
            next_ops = dict(ops[i - 1][j])
            next_ops["delete"] += 1
            choices.append((dp[i - 1][j] + ACTION_BITS, "delete", next_ops))
            next_ops = dict(ops[i][j - 1])
            next_ops["insert"] += 1
            choices.append(
                (
                    dp[i][j - 1] + ACTION_BITS + token_bits(target[j - 1], counts, vocab),
                    "insert",
                    next_ops,
                )
            )
            next_ops = dict(ops[i - 1][j - 1])
            next_ops["substitute"] += 1
            choices.append(
                (
                    dp[i - 1][j - 1] + ACTION_BITS + token_bits(target[j - 1], counts, vocab),
                    "substitute",
                    next_ops,
                )
            )
            best = min(choices, key=lambda item: (item[0], item[1]))
            dp[i][j] = best[0]
            ops[i][j] = best[2]
    return dp[-1][-1], ops[-1][-1]


def choose_source(books: dict[int, dict[str, Any]], train_ids: list[int], target_book: int, policy: str) -> int:
    target = books[target_book]
    if policy == "previous_book":
        prior = [book for book in train_ids if book < target_book]
        return max(prior) if prior else max(train_ids)
    if policy == "book_length_nearest":
        return min(train_ids, key=lambda book: (abs(books[book]["book_length"] - target["book_length"]), book))
    if policy == "op_count_nearest":
        return min(train_ids, key=lambda book: (abs(books[book]["op_count"] - target["op_count"]), book))
    if policy == "literal_count_nearest":
        return min(train_ids, key=lambda book: (abs(books[book]["literal_count"] - target["literal_count"]), book))
    if policy == "phase_then_length":
        same_phase = [book for book in train_ids if books[book]["book_phase"] == target["book_phase"]]
        pool = same_phase or train_ids
        return min(pool, key=lambda book: (abs(books[book]["book_length"] - target["book_length"]), book))
    raise KeyError(policy)


POLICIES = [
    "previous_book",
    "book_length_nearest",
    "op_count_nearest",
    "literal_count_nearest",
    "phase_then_length",
]
GRANTED_POLICIES = {"op_count_nearest", "literal_count_nearest"}


def policy_cost(
    books: dict[int, dict[str, Any]],
    train_ids: list[int],
    test_ids: list[int],
    policy: str,
    counts: Counter[str],
    vocab: set[str],
    shuffled_train_tokens: dict[int, list[str]] | None = None,
) -> dict[str, Any]:
    total = 0.0
    total_baseline = 0.0
    op_counts = Counter()
    sources = {}
    exact_matches = 0
    for target_book in test_ids:
        source_book = choose_source(books, train_ids, target_book, policy)
        source_tokens = (
            shuffled_train_tokens[source_book]
            if shuffled_train_tokens and source_book in shuffled_train_tokens
            else books[source_book]["tokens"]
        )
        target_tokens = books[target_book]["tokens"]
        bits, ops = edit_lower_bound_bits(source_tokens, target_tokens, counts, vocab)
        total += bits
        total_baseline += sequence_unigram_bits(target_tokens, counts, vocab)
        op_counts.update(ops)
        sources[target_book] = source_book
        exact_matches += int(ops["insert"] == 0 and ops["delete"] == 0 and ops["substitute"] == 0)
    return {
        "edit_lower_bound_bits": total,
        "sequence_unigram_bits": total_baseline,
        "saving_vs_sequence_unigram": total_baseline - total,
        "source_by_book": sources,
        "exact_sequence_matches": exact_matches,
        "edit_ops": dict(op_counts),
    }


def oracle_cost(
    books: dict[int, dict[str, Any]],
    train_ids: list[int],
    test_ids: list[int],
    counts: Counter[str],
    vocab: set[str],
) -> dict[str, Any]:
    total = 0.0
    total_baseline = 0.0
    sources = {}
    op_counts = Counter()
    for target_book in test_ids:
        rows = []
        for source_book in train_ids:
            bits, ops = edit_lower_bound_bits(books[source_book]["tokens"], books[target_book]["tokens"], counts, vocab)
            rows.append((bits, source_book, ops))
        bits, source_book, ops = min(rows, key=lambda item: (item[0], item[1]))
        total += bits + math.log2(max(1, len(train_ids)))
        total_baseline += sequence_unigram_bits(books[target_book]["tokens"], counts, vocab)
        sources[target_book] = source_book
        op_counts.update(ops)
    return {
        "edit_lower_bound_bits_with_source_index": total,
        "sequence_unigram_bits": total_baseline,
        "saving_vs_sequence_unigram": total_baseline - total,
        "source_by_book": sources,
        "edit_ops": dict(op_counts),
        "oracle_source_index_bits_per_book": math.log2(max(1, len(train_ids))),
    }


def loo_policy_score(books: dict[int, dict[str, Any]], train_ids: list[int], policy: str) -> float:
    if len(train_ids) < 2:
        return float("inf")
    total = 0.0
    for heldout in train_ids:
        sub_train = [book for book in train_ids if book != heldout]
        counts, vocab = token_model(books, sub_train)
        total += policy_cost(books, sub_train, [heldout], policy, counts, vocab)["edit_lower_bound_bits"]
    penalty = math.log2(len(POLICIES))
    if policy in GRANTED_POLICIES:
        penalty += 32.0
    return total + penalty


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def shuffled_train_controls(
    books: dict[int, dict[str, Any]],
    train_ids: list[int],
    test_ids: list[int],
    policy: str,
    counts: Counter[str],
    vocab: set[str],
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = {}
        for book in train_ids:
            tokens = list(books[book]["tokens"])
            rng.shuffle(tokens)
            shuffled[book] = tokens
        result = policy_cost(books, train_ids, test_ids, policy, counts, vocab, shuffled_train_tokens=shuffled)
        savings.append(result["saving_vs_sequence_unigram"])
    return {
        "saving_mean": sum(savings) / len(savings),
        "saving_p05": percentile(savings, 5),
        "saving_p50": percentile(savings, 50),
        "saving_p95": percentile(savings, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def random_source_controls(
    books: dict[int, dict[str, Any]],
    train_ids: list[int],
    test_ids: list[int],
    counts: Counter[str],
    vocab: set[str],
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 10000 + seed_offset)
    savings = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        baseline = 0.0
        for target_book in test_ids:
            source_book = rng.choice(train_ids)
            bits, _ = edit_lower_bound_bits(books[source_book]["tokens"], books[target_book]["tokens"], counts, vocab)
            total += bits
            baseline += sequence_unigram_bits(books[target_book]["tokens"], counts, vocab)
        savings.append(baseline - total)
    return {
        "saving_mean": sum(savings) / len(savings),
        "saving_p05": percentile(savings, 5),
        "saving_p50": percentile(savings, 50),
        "saving_p95": percentile(savings, 95),
        "seed": RANDOM_SEED + 10000 + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(cutoff: int, books: dict[int, dict[str, Any]], seed_offset: int) -> dict[str, Any]:
    all_books = sorted(books)
    train_ids = [book for book in all_books if book < cutoff]
    test_ids = [book for book in all_books if book >= cutoff]
    counts, vocab = token_model(books, train_ids)
    policy_rows = []
    for policy in POLICIES:
        score = loo_policy_score(books, train_ids, policy)
        result = policy_cost(books, train_ids, test_ids, policy, counts, vocab)
        result.update(
            {
                "grants_skeleton_counts": policy in GRANTED_POLICIES,
                "loo_train_mdl_bits": score,
                "policy": policy,
            }
        )
        policy_rows.append(result)
    selected = min(policy_rows, key=lambda row: (row["loo_train_mdl_bits"], row["grants_skeleton_counts"], row["policy"]))
    train_controls = shuffled_train_controls(books, train_ids, test_ids, selected["policy"], counts, vocab, seed_offset)
    random_controls = random_source_controls(books, train_ids, test_ids, counts, vocab, seed_offset)
    selected["beats_shuffled_train_p95"] = selected["saving_vs_sequence_unigram"] > train_controls["saving_p95"]
    selected["beats_random_source_p95"] = selected["saving_vs_sequence_unigram"] > random_controls["saving_p95"]
    return {
        "cutoff": cutoff,
        "train_books": train_ids,
        "test_books": test_ids,
        "test_ops": sum(books[book]["op_count"] for book in test_ids),
        "selected": selected,
        "oracle_lower_bound": oracle_cost(books, train_ids, test_ids, counts, vocab),
        "policy_rows": policy_rows,
        "random_source_controls": random_controls,
        "shuffled_train_controls": train_controls,
    }


def make_result() -> dict[str, Any]:
    order_audit = load_json(ORDER_AUDIT)
    assert_boundary("within_book_order_program", order_audit)
    books = load_books()
    cutoff_rows = [cutoff_gate(cutoff, books, index) for index, cutoff in enumerate(CUTOFFS)]
    selected_rows = [row["selected"] for row in cutoff_rows]
    total_edit = sum(row["edit_lower_bound_bits"] for row in selected_rows)
    total_baseline = sum(row["sequence_unigram_bits"] for row in selected_rows)
    total_saving = total_baseline - total_edit
    train_control_cells = sum(row["beats_shuffled_train_p95"] for row in selected_rows)
    random_control_cells = sum(row["beats_random_source_p95"] for row in selected_rows)
    granted_cells = sum(row["grants_skeleton_counts"] for row in selected_rows)
    total_oracle = sum(row["oracle_lower_bound"]["edit_lower_bound_bits_with_source_index"] for row in cutoff_rows)
    total_oracle_baseline = sum(row["oracle_lower_bound"]["sequence_unigram_bits"] for row in cutoff_rows)
    promoted = (
        total_saving > 0
        and train_control_cells >= 4
        and random_control_cells >= 4
        and granted_cells == 0
    )
    weak = total_saving > 0 and (train_control_cells >= 3 or random_control_cells >= 3)
    classification = (
        "PROMOTED_SEQUENCE_MUTATION_CANDIDATE_LOWER_BOUND"
        if promoted
        else "WEAK_SEQUENCE_MUTATION_CLUE_LOWER_BOUND"
        if weak
        else "SEQUENCE_MUTATION_PROGRAM_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": False,
            "lower_bound_only": True,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "why_not_generator": (
                "Edit matches and source/mutation syntax are not fully charged, and "
                "oracle source choice is reported separately. A positive result would "
                "still require a stricter executable edit codec."
            ),
        },
        "inputs": {
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
            "within_book_order_program": rel(ORDER_AUDIT),
        },
        "plaintext_claim": False,
        "schema": "sequence_mutation_program_gate.v1",
        "scope": "analysis_only_joint_operation_sequence_mutation_lower_bound",
        "summary": {
            "beats_random_source_p95_cells": random_control_cells,
            "beats_shuffled_train_p95_cells": train_control_cells,
            "cutoffs": CUTOFFS,
            "selected_grants_skeleton_count_cells": granted_cells,
            "total_oracle_lower_bound_bits_with_source_index": total_oracle,
            "total_oracle_saving_vs_sequence_unigram": total_oracle_baseline - total_oracle,
            "total_policy_edit_lower_bound_bits": total_edit,
            "total_saving_vs_sequence_unigram": total_saving,
            "total_sequence_unigram_bits": total_baseline,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Sequence Mutation Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether a future book's joint operation-token sequence can be encoded "
        "as an optimistic edit script from a previous training-book sequence.",
        "",
        "## Summary",
        "",
        f"- Selected edit lower-bound bits: `{s['total_policy_edit_lower_bound_bits']:.3f}`.",
        f"- Sequence unigram baseline bits: `{s['total_sequence_unigram_bits']:.3f}`.",
        f"- Saving vs sequence unigram: `{s['total_saving_vs_sequence_unigram']:.3f}` bits.",
        f"- Cells beating shuffled-train p95: `{s['beats_shuffled_train_p95_cells']}/5`.",
        f"- Cells beating random-source p95: `{s['beats_random_source_p95_cells']}/5`.",
        f"- Selected cells using skeleton-count policies: `{s['selected_grants_skeleton_count_cells']}/5`.",
        f"- Oracle lower-bound saving with paid source index: `{s['total_oracle_saving_vs_sequence_unigram']:.3f}` bits.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Policy | Test ops | Edit lb bits | Baseline bits | Saving | Shuffle p95 | Random p95 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in result["cutoff_rows"]:
        selected = row["selected"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['policy']}` | `{row['test_ops']}` | "
            f"`{selected['edit_lower_bound_bits']:.3f}` | `{selected['sequence_unigram_bits']:.3f}` | "
            f"`{selected['saving_vs_sequence_unigram']:.3f}` | "
            f"`{selected['beats_shuffled_train_p95']}` | `{selected['beats_random_source_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This is a lower-bound test. It can reject sequence mutation if weak, but "
            "it cannot by itself promote a generator because matched positions and "
            "full edit syntax are not completely charged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Sequence Mutation Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can a held-out book's joint operation-token sequence be generated as a "
        "small edit/mutation from a previous book sequence, instead of declaring "
        "bag and order independently?",
        "",
        "## Result",
        "",
        f"The selected mutation policies cost `{s['total_policy_edit_lower_bound_bits']:.3f}` "
        f"optimistic edit bits versus `{s['total_sequence_unigram_bits']:.3f}` "
        f"sequence-unigram bits (`{-s['total_saving_vs_sequence_unigram']:.3f}` bits worse). "
        f"They beat shuffled-train p95 in `{s['beats_shuffled_train_p95_cells']}/5` "
        f"cells and random-source p95 in `{s['beats_random_source_p95_cells']}/5`. "
        f"The oracle lower bound with paid source index is "
        f"`{-s['total_oracle_saving_vs_sequence_unigram']:.3f}` bits worse than unigram.",
        "",
        "## Decision",
        "",
        "This is a lower-bound edit test, not a full executable codec. Row0, "
        "plaintext, translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_sequence_mutation_program_gate.py](../scripts/01_sequence_mutation_program_gate.py)",
        "- [01_sequence_mutation_program_gate.json](test_results/01_sequence_mutation_program_gate.json)",
        "- [01_sequence_mutation_program_gate.md](test_results/01_sequence_mutation_program_gate.md)",
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
