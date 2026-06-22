#!/usr/bin/env python3
"""Within-book order program gate.

The previous factorization localized one remaining field: given a per-book
multiset of joint operation tokens, the exact within-book order still costs
about 587 bits across repeated prefix holdouts. This gate tests whether that
order field can be reduced by a prefix-trained sequential policy.

The policy is intentionally constrained:

- the true per-book multiset is granted;
- the model emits one token at a time without replacement;
- scoring uses only the already-emitted prefix, step position, book metadata,
  and the remaining multiset;
- promotion requires savings over uniform permutations and shuffled-order
  controls.

This is not a full generator because it still grants the book multiset.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "within_book_order_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
MULTISET_AUDIT = (
    ROOT
    / "analysis"
    / "book_multiset_order_factorization_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_multiset_order_factorization_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_within_book_order_program_gate.json"
MD_OUT = TEST_RESULTS / "01_within_book_order_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_within_book_order_program_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
BEAM_WIDTH = 20


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


def fraction_bucket(index: int, total: int, bins: int, prefix: str) -> str:
    if total <= 1:
        return f"{prefix}_only"
    frac = index / (total - 1)
    bucket = min(bins - 1, max(0, int(frac * bins)))
    return f"{prefix}_q{bucket:02d}"


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
    frac = start / max(1, max_tape_end)
    bucket = min(5, max(0, int(frac * 6)))
    return f"lit_tape_q{bucket:02d}"


def behavior_symbol(row: dict[str, Any], max_tape_end: int) -> str:
    if row["op_type"] == "literal":
        return f"lit:{row['length_bucket']}:{literal_tape_bucket(row, max_tape_end)}"
    rank_bucket = row.get("copy_hint_rank_bucket") or "rank_none"
    return f"copy:{row['length_bucket']}:{rank_bucket}:{occ_bucket(row.get('copy_hint_source_occurrences'))}"


def load_sequences() -> dict[int, dict[str, Any]]:
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
    out: dict[int, dict[str, Any]] = {}
    for book, rows in grouped.items():
        rows = sorted(rows, key=lambda item: int(item["op_index"]))
        out[book] = {
            "book": book,
            "book_phase": rows[0]["book_phase"],
            "book_length": int(rows[0]["book_length"]),
            "tokens": [row["joint_token"] for row in rows],
        }
    return out


def token_parts(token: str) -> dict[str, str]:
    control, behavior = token.split("|", 1)
    op_type, length_bucket = control.split(":", 1)
    return {
        "behavior": behavior,
        "control": control,
        "length_bucket": length_bucket,
        "op_type": op_type,
    }


def context_for(
    family: str,
    book_info: dict[str, Any],
    prefix: list[str],
    step: int,
    total: int,
) -> str:
    pos = fraction_bucket(step, total, 5, "pos")
    if family == "global":
        return "global"
    if family == "position":
        return pos
    if family == "book_phase":
        return book_info["book_phase"]
    if family == "phase_position":
        return f"{book_info['book_phase']}|{pos}"
    if not prefix:
        prev = {"control": "START", "behavior": "START", "op_type": "START", "length_bucket": "START"}
    else:
        prev = token_parts(prefix[-1])
    if family == "prev_control":
        return prev["control"]
    if family == "prev_op_type":
        return prev["op_type"]
    if family == "prev_length_bucket":
        return prev["length_bucket"]
    if family == "prev_behavior":
        return prev["behavior"]
    if family == "prev_control_position":
        return f"{prev['control']}|{pos}"
    if family == "prev_op_type_position":
        return f"{prev['op_type']}|{pos}"
    raise KeyError(family)


FAMILIES = [
    "global",
    "position",
    "book_phase",
    "phase_position",
    "prev_control",
    "prev_op_type",
    "prev_length_bucket",
    "prev_behavior",
    "prev_control_position",
    "prev_op_type_position",
]


def train_counts(
    books: dict[int, dict[str, Any]],
    train_book_ids: list[int],
    family: str,
    shuffled_tokens: dict[int, list[str]] | None = None,
) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for book in train_book_ids:
        info = books[book]
        tokens = shuffled_tokens[book] if shuffled_tokens else info["tokens"]
        prefix: list[str] = []
        for step, token in enumerate(tokens):
            context = context_for(family, info, prefix, step, len(tokens))
            counts[context][token] += 1
            prefix.append(token)
    return counts


def uniform_order_bits(tokens: list[str]) -> float:
    counts = Counter(tokens)
    total = len(tokens)
    value = math.lgamma(total + 1)
    for count in counts.values():
        value -= math.lgamma(count + 1)
    return value / math.log(2)


def token_weight(token: str, context: str, counts: dict[str, Counter[str]], global_counts: Counter[str], vocab_size: int) -> float:
    counter = counts.get(context)
    if counter:
        total = sum(counter.values())
        return (counter.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)
    total = sum(global_counts.values())
    return (global_counts.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)


def order_policy_bits(
    books: dict[int, dict[str, Any]],
    book_ids: list[int],
    family: str,
    counts: dict[str, Counter[str]],
    vocab: set[str],
    override_tokens: dict[int, list[str]] | None = None,
) -> tuple[float, int, int]:
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    vocab_size = max(1, len(vocab))
    bits = 0.0
    top1_hits = 0
    total_steps = 0
    for book in book_ids:
        info = books[book]
        tokens = override_tokens[book] if override_tokens else info["tokens"]
        remaining = Counter(tokens)
        prefix: list[str] = []
        for step, token in enumerate(tokens):
            context = context_for(family, info, prefix, step, len(tokens))
            denom = 0.0
            best_token = None
            best_score = -1.0
            for candidate, amount in remaining.items():
                if amount <= 0:
                    continue
                score = amount * token_weight(candidate, context, counts, global_counts, vocab_size)
                denom += score
                if score > best_score or (score == best_score and (best_token is None or candidate < best_token)):
                    best_score = score
                    best_token = candidate
            numer = remaining[token] * token_weight(token, context, counts, global_counts, vocab_size)
            bits += -math.log2(numer / denom)
            if best_token == token:
                top1_hits += 1
            total_steps += 1
            remaining[token] -= 1
            if remaining[token] == 0:
                del remaining[token]
            prefix.append(token)
    return bits, top1_hits, total_steps


def beam_contains_true(
    info: dict[str, Any],
    family: str,
    counts: dict[str, Counter[str]],
    vocab: set[str],
) -> bool:
    true_tokens = info["tokens"]
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    vocab_size = max(1, len(vocab))
    beam: list[tuple[float, tuple[str, ...], Counter[str]]] = [
        (0.0, tuple(), Counter(true_tokens))
    ]
    for step, true_token in enumerate(true_tokens):
        next_beam: list[tuple[float, tuple[str, ...], Counter[str]]] = []
        for neg_log_prob, prefix_tuple, remaining in beam:
            prefix = list(prefix_tuple)
            context = context_for(family, info, prefix, step, len(true_tokens))
            denom = 0.0
            weights = {}
            for candidate, amount in remaining.items():
                if amount <= 0:
                    continue
                weight = amount * token_weight(candidate, context, counts, global_counts, vocab_size)
                weights[candidate] = weight
                denom += weight
            for candidate, weight in weights.items():
                new_remaining = Counter(remaining)
                new_remaining[candidate] -= 1
                if new_remaining[candidate] == 0:
                    del new_remaining[candidate]
                next_beam.append(
                    (
                        neg_log_prob - math.log2(weight / denom),
                        prefix_tuple + (candidate,),
                        new_remaining,
                    )
                )
        next_beam.sort(key=lambda item: (item[0], item[1]))
        beam = next_beam[:BEAM_WIDTH]
        true_prefix = tuple(true_tokens[: step + 1])
        if not any(prefix == true_prefix for _, prefix, _ in beam):
            return False
    return True


def descriptor_penalty(counts: dict[str, Counter[str]]) -> float:
    states = len(counts)
    cells = sum(len(counter) for counter in counts.values())
    return math.log2(len(FAMILIES)) + states + 0.25 * cells


def loo_train_score(books: dict[int, dict[str, Any]], train_ids: list[int], family: str, vocab: set[str]) -> float:
    if len(train_ids) < 2:
        return float("inf")
    score = 0.0
    for heldout in train_ids:
        sub_train = [book for book in train_ids if book != heldout]
        counts = train_counts(books, sub_train, family)
        bits, _, _ = order_policy_bits(books, [heldout], family, counts, vocab)
        score += bits
    return score + descriptor_penalty(train_counts(books, train_ids, family))


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def shuffled_train_controls(
    books: dict[int, dict[str, Any]],
    train_ids: list[int],
    test_ids: list[int],
    family: str,
    vocab: set[str],
    uniform_bits: float,
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
        counts = train_counts(books, train_ids, family, shuffled_tokens=shuffled)
        bits, _, _ = order_policy_bits(books, test_ids, family, counts, vocab)
        savings.append(uniform_bits - bits)
    return {
        "saving_mean": sum(savings) / len(savings),
        "saving_p05": percentile(savings, 5),
        "saving_p50": percentile(savings, 50),
        "saving_p95": percentile(savings, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def shuffled_test_controls(
    books: dict[int, dict[str, Any]],
    test_ids: list[int],
    family: str,
    counts: dict[str, Counter[str]],
    vocab: set[str],
    uniform_bits: float,
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 10000 + seed_offset)
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = {}
        for book in test_ids:
            tokens = list(books[book]["tokens"])
            rng.shuffle(tokens)
            shuffled[book] = tokens
        bits, _, _ = order_policy_bits(books, test_ids, family, counts, vocab, override_tokens=shuffled)
        savings.append(uniform_bits - bits)
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
    vocab = {token for info in books.values() for token in info["tokens"]}
    family_scores = [
        {"family": family, "loo_train_mdl_bits": loo_train_score(books, train_ids, family, vocab)}
        for family in FAMILIES
    ]
    selected_family = min(family_scores, key=lambda item: (item["loo_train_mdl_bits"], item["family"]))["family"]
    counts = train_counts(books, train_ids, selected_family)
    policy_bits, top1_hits, total_steps = order_policy_bits(books, test_ids, selected_family, counts, vocab)
    uniform_bits = sum(uniform_order_bits(books[book]["tokens"]) for book in test_ids)
    train_controls = shuffled_train_controls(
        books, train_ids, test_ids, selected_family, vocab, uniform_bits, seed_offset
    )
    test_controls = shuffled_test_controls(
        books, test_ids, selected_family, counts, vocab, uniform_bits, seed_offset
    )
    exact_books = 0
    true_in_beam = 0
    nontrivial_exact_books = 0
    nontrivial_in_beam = 0
    for book in test_ids:
        info = books[book]
        counts_book = train_counts(books, train_ids, selected_family)
        # Greedy exactness is equivalent to all top-1 hits in this book.
        bits, hits, steps = order_policy_bits(books, [book], selected_family, counts_book, vocab)
        is_exact = hits == steps
        in_beam = beam_contains_true(info, selected_family, counts_book, vocab)
        exact_books += int(is_exact)
        true_in_beam += int(in_beam)
        if len(info["tokens"]) > 2:
            nontrivial_exact_books += int(is_exact)
            nontrivial_in_beam += int(in_beam)
    saving = uniform_bits - policy_bits
    return {
        "cutoff": cutoff,
        "train_books": train_ids,
        "test_books": test_ids,
        "test_ops": total_steps,
        "selected_family": selected_family,
        "family_scores": family_scores,
        "uniform_order_bits": uniform_bits,
        "policy_order_bits": policy_bits,
        "saving_vs_uniform_order": saving,
        "top1_hits": top1_hits,
        "top1_accuracy": top1_hits / max(1, total_steps),
        "greedy_exact_books": exact_books,
        "greedy_nontrivial_exact_books": nontrivial_exact_books,
        "true_sequence_in_beam": true_in_beam,
        "nontrivial_true_sequence_in_beam": nontrivial_in_beam,
        "beats_shuffled_train_p95": saving > train_controls["saving_p95"],
        "beats_shuffled_test_p95": saving > test_controls["saving_p95"],
        "shuffled_train_controls": train_controls,
        "shuffled_test_controls": test_controls,
    }


def make_result() -> dict[str, Any]:
    multiset = load_json(MULTISET_AUDIT)
    assert_boundary("book_multiset_order_factorization", multiset)
    books = load_sequences()
    cutoff_rows = [
        cutoff_gate(cutoff, books, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    total_uniform = sum(row["uniform_order_bits"] for row in cutoff_rows)
    total_policy = sum(row["policy_order_bits"] for row in cutoff_rows)
    total_saving = total_uniform - total_policy
    train_control_cells = sum(row["beats_shuffled_train_p95"] for row in cutoff_rows)
    test_control_cells = sum(row["beats_shuffled_test_p95"] for row in cutoff_rows)
    total_exact = sum(row["greedy_exact_books"] for row in cutoff_rows)
    total_nontrivial_exact = sum(row["greedy_nontrivial_exact_books"] for row in cutoff_rows)
    total_in_beam = sum(row["true_sequence_in_beam"] for row in cutoff_rows)
    total_nontrivial_in_beam = sum(row["nontrivial_true_sequence_in_beam"] for row in cutoff_rows)
    promoted = (
        total_saving > 0
        and train_control_cells >= 4
        and test_control_cells >= 4
        and total_nontrivial_in_beam > 0
    )
    weak = total_saving > 0 and (train_control_cells >= 3 or test_control_cells >= 3)
    classification = (
        "PROMOTED_WITHIN_BOOK_ORDER_PROGRAM_CANDIDATE"
        if promoted
        else "WEAK_WITHIN_BOOK_ORDER_CLUE_NOT_GENERATOR"
        if weak
        else "WITHIN_BOOK_ORDER_PROGRAM_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": False,
            "grants_book_multiset": True,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "why_not_generator": (
                "This gate grants the exact per-book multiset. Even if an order "
                "policy works, a full generator still needs to generate the multiset "
                "and the payload/copy fields. Promotion additionally requires controls."
            ),
        },
        "inputs": {
            "book_multiset_order_factorization": rel(MULTISET_AUDIT),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "within_book_order_program_gate.v1",
        "scope": "analysis_only_order_policy_given_true_book_multiset",
        "summary": {
            "beam_width": BEAM_WIDTH,
            "beats_shuffled_test_p95_cells": test_control_cells,
            "beats_shuffled_train_p95_cells": train_control_cells,
            "cutoffs": CUTOFFS,
            "total_greedy_exact_books": total_exact,
            "total_greedy_nontrivial_exact_books": total_nontrivial_exact,
            "total_policy_order_bits": total_policy,
            "total_saving_vs_uniform_order": total_saving,
            "total_true_sequence_in_beam": total_in_beam,
            "total_nontrivial_true_sequence_in_beam": total_nontrivial_in_beam,
            "total_uniform_order_bits": total_uniform,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Within-Book Order Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Given the true per-book multiset of joint operation tokens, test whether a "
        "prefix-trained no-replacement sequential policy can reduce the exact "
        "within-book order index.",
        "",
        "## Summary",
        "",
        f"- Uniform order bits: `{s['total_uniform_order_bits']:.3f}`.",
        f"- Policy order bits: `{s['total_policy_order_bits']:.3f}`.",
        f"- Saving vs uniform order: `{s['total_saving_vs_uniform_order']:.3f}` bits.",
        f"- Cells beating shuffled-train p95: `{s['beats_shuffled_train_p95_cells']}/5`.",
        f"- Cells beating shuffled-test p95: `{s['beats_shuffled_test_p95_cells']}/5`.",
        f"- Greedy exact books: `{s['total_greedy_exact_books']}`.",
        f"- Greedy nontrivial exact books: `{s['total_greedy_nontrivial_exact_books']}`.",
        f"- True sequence in beam{BEAM_WIDTH}: `{s['total_true_sequence_in_beam']}`.",
        f"- Nontrivial true sequence in beam{BEAM_WIDTH}: `{s['total_nontrivial_true_sequence_in_beam']}`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Family | Test ops | Uniform bits | Policy bits | Saving | Train p95 | Test p95 | Beam hits |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_family']}` | `{row['test_ops']}` | "
            f"`{row['uniform_order_bits']:.3f}` | `{row['policy_order_bits']:.3f}` | "
            f"`{row['saving_vs_uniform_order']:.3f}` | "
            f"`{row['beats_shuffled_train_p95']}` | `{row['beats_shuffled_test_p95']}` | "
            f"`{row['true_sequence_in_beam']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This can only become a generator component if it reduces the granted "
            "order index under holdout and survives shuffled-order controls. The "
            "book multiset is still granted in this gate.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Within-Book Order Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Given the true per-book joint-token multiset, can a prefix-trained "
        "sequential policy generate or reduce the exact within-book order index?",
        "",
        "## Result",
        "",
        f"The no-replacement order policy costs `{s['total_policy_order_bits']:.3f}` "
        f"bits versus `{s['total_uniform_order_bits']:.3f}` uniform order bits "
        f"(`{-s['total_saving_vs_uniform_order']:.3f}` bits worse than uniform). "
        f"It beats shuffled-train p95 "
        f"in `{s['beats_shuffled_train_p95_cells']}/5` cells and shuffled-test p95 "
        f"in `{s['beats_shuffled_test_p95_cells']}/5` cells. Beam{BEAM_WIDTH} keeps "
        f"the true sequence in `{s['total_true_sequence_in_beam']}` held-out books, "
        f"`{s['total_nontrivial_true_sequence_in_beam']}` nontrivial.",
        "",
        "## Decision",
        "",
        "The gate grants the exact book multiset, so even a positive order result "
        "would be only a component. Row0, plaintext, translation, and "
        "compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_within_book_order_program_gate.py](../scripts/01_within_book_order_program_gate.py)",
        "- [01_within_book_order_program_gate.json](test_results/01_within_book_order_program_gate.json)",
        "- [01_within_book_order_program_gate.md](test_results/01_within_book_order_program_gate.md)",
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
