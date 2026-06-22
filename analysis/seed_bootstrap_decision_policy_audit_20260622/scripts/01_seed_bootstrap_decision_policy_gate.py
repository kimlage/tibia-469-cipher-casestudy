#!/usr/bin/env python3
"""Seed bootstrap decision-policy gate.

The seed copy surface is strong, but the first target-free transducer failed.
This audit isolates the missing part: the copy/literal decision policy. It
stays on the true seed prefix path, exposes only decoder-visible state
(already-emitted prefix, seed book position/remaining length, literal-tape
pointer), and asks whether small prefix-selected rules can predict the oracle
surface action under holdout.

This is not a generator. A positive result would only promote a decision-policy
clue; source/length selection and full decoding would remain separate gates.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "seed_bootstrap_decision_policy_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SURFACE_SCRIPT = (
    ROOT
    / "analysis"
    / "seed_bootstrap_copy_surface_audit_20260622"
    / "scripts"
    / "01_seed_bootstrap_copy_surface_gate.py"
)
SURFACE_FINAL = (
    ROOT
    / "analysis"
    / "seed_bootstrap_copy_surface_audit_20260622"
    / "reports"
    / "final_seed_bootstrap_copy_surface_audit.md"
)
TRANSDUCER_FINAL = (
    ROOT
    / "analysis"
    / "seed_bootstrap_transducer_program_audit_20260622"
    / "reports"
    / "final_seed_bootstrap_transducer_program_audit.md"
)

JSON_OUT = TEST_RESULTS / "01_seed_bootstrap_decision_policy_gate.json"
MD_OUT = TEST_RESULTS / "01_seed_bootstrap_decision_policy_gate.md"
FINAL_OUT = FRONT / "reports" / "final_seed_bootstrap_decision_policy_audit.md"

RANDOM_SEED = 46920260627
RANDOM_TRIALS = 300
PREFIX_CUTOFF_BOOKS = [3, 5, 7, 9]
CONTEXTS = [2, 3, 4, 5, 6]


Row = dict[str, Any]
Rule = Callable[[Row], str]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_surface_module() -> Any:
    spec = importlib.util.spec_from_file_location("seed_bootstrap_surface", SURFACE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SURFACE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_books() -> dict[int, str]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    return {book: books[book] for book in range(10)}


def seed_stream_and_offsets() -> tuple[str, list[int], list[int]]:
    books = seed_books()
    lengths = [len(books[book]) for book in range(10)]
    offsets = []
    cursor = 0
    for length in lengths:
        offsets.append(cursor)
        cursor += length
    return "".join(books[book] for book in range(10)), lengths, offsets


def oracle_ops(stream: str) -> list[dict[str, Any]]:
    surface = load_surface_module()
    score = surface.greedy_copy_surface(stream, 4)
    # The surface audit stores only copy rows, so reconstruct literal rows by
    # walking through the sampled logic from the promoted gate.
    ops = []
    copy_by_start = {int(row["start"]): int(row["length"]) for row in score["op_rows_sample"]}
    # Recompute fully, using the same public function shape but with local
    # previous-substring checks so all copy starts are retained.
    i = 0
    while i < len(stream):
        best = 0
        for source in range(0, i):
            length = 0
            while i + length < len(stream) and source + length < i and stream[source + length] == stream[i + length] and length < 64:
                length += 1
            if length > best:
                best = length
        if best >= 4:
            ops.append({"kind": "copy", "length": best, "start": i})
            i += best
        else:
            ops.append({"digit": stream[i], "kind": "literal", "length": 1, "start": i})
            i += 1
    return ops


def book_for_pos(pos: int, offsets: list[int], lengths: list[int]) -> tuple[int, int, int]:
    for book, start in enumerate(offsets):
        end = start + lengths[book]
        if start <= pos < end:
            return book, pos - start, end - pos
    return 9, lengths[9], 0


def suffix_stats(prefix: str, ctx: int) -> dict[str, Any]:
    if len(prefix) < ctx:
        return {"repeat_count": 0, "distinct_next": 0, "next_digits": []}
    suffix = prefix[-ctx:]
    next_digits = []
    for start in range(0, len(prefix) - ctx):
        if prefix[start : start + ctx] == suffix and start + ctx < len(prefix):
            next_digits.append(prefix[start + ctx])
    return {
        "repeat_count": len(next_digits),
        "distinct_next": len(set(next_digits)),
        "next_digits": sorted(set(next_digits)),
    }


def build_rows() -> dict[str, Any]:
    stream, lengths, offsets = seed_stream_and_offsets()
    ops = oracle_ops(stream)
    literal_tape = "".join(op["digit"] for op in ops if op["kind"] == "literal")
    literal_index = 0
    rows = []
    for op_index, op in enumerate(ops):
        pos = int(op["start"])
        prefix = stream[:pos]
        book, book_pos, remaining = book_for_pos(pos, offsets, lengths)
        row: Row = {
            "action": op["kind"],
            "book": book,
            "book_pos": book_pos,
            "global_pos": pos,
            "literal_index": literal_index,
            "literal_next": literal_tape[literal_index] if literal_index < len(literal_tape) else None,
            "op_index": op_index,
            "remaining_in_book": remaining,
        }
        for ctx in CONTEXTS:
            stats = suffix_stats(prefix, ctx)
            row[f"ctx{ctx}_repeat_count"] = stats["repeat_count"]
            row[f"ctx{ctx}_distinct_next"] = stats["distinct_next"]
            row[f"ctx{ctx}_literal_in_next"] = (
                row["literal_next"] in stats["next_digits"] if row["literal_next"] is not None else False
            )
        rows.append(row)
        if op["kind"] == "literal":
            literal_index += 1
    return {
        "book_lengths": lengths,
        "literal_tape_digits": len(literal_tape),
        "rows": rows,
        "seed_digits": len(stream),
    }


def rule_specs() -> dict[str, Rule]:
    specs: dict[str, Rule] = {
        "always_literal": lambda row: "literal",
        "always_copy": lambda row: "copy",
    }
    for ctx in CONTEXTS:
        specs[f"ctx{ctx}_repeat_any"] = (
            lambda row, ctx=ctx: "copy" if int(row[f"ctx{ctx}_repeat_count"]) > 0 else "literal"
        )
        specs[f"ctx{ctx}_deterministic_next"] = (
            lambda row, ctx=ctx: "copy" if int(row[f"ctx{ctx}_distinct_next"]) == 1 else "literal"
        )
        specs[f"ctx{ctx}_repeat_literal_not_next"] = (
            lambda row, ctx=ctx: "copy"
            if int(row[f"ctx{ctx}_repeat_count"]) > 0 and not bool(row[f"ctx{ctx}_literal_in_next"])
            else "literal"
        )
        specs[f"ctx{ctx}_repeat_literal_in_next"] = (
            lambda row, ctx=ctx: "copy"
            if int(row[f"ctx{ctx}_repeat_count"]) > 0 and bool(row[f"ctx{ctx}_literal_in_next"])
            else "literal"
        )
    return specs


def score_rule(rows: list[Row], rule: Rule) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = rule(row)
        truth = row["action"]
        if truth == "copy" and pred == "copy":
            tp += 1
        elif truth == "literal" and pred == "copy":
            fp += 1
        elif truth == "literal" and pred == "literal":
            tn += 1
        elif truth == "copy" and pred == "literal":
            fn += 1
    total = tp + fp + tn + fn
    return {
        "accuracy": (tp + tn) / total if total else 0.0,
        "copy_precision": tp / (tp + fp) if tp + fp else 0.0,
        "copy_recall": tp / (tp + fn) if tp + fn else 0.0,
        "copy_tp": tp,
        "false_copy": fp,
        "false_literal": fn,
        "literal_tn": tn,
        "rows": total,
    }


def train_select(train: list[Row]) -> tuple[str, dict[str, Any]]:
    specs = rule_specs()
    scored = {
        name: score_rule(train, rule)
        for name, rule in specs.items()
    }
    selected = max(
        scored,
        key=lambda name: (
            scored[name]["accuracy"],
            scored[name]["copy_recall"],
            scored[name]["copy_precision"],
        ),
    )
    return selected, scored[selected]


def prefix_holdouts(rows: list[Row]) -> list[dict[str, Any]]:
    specs = rule_specs()
    out = []
    for cutoff in PREFIX_CUTOFF_BOOKS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        selected, train_score = train_select(train)
        test_score = score_rule(test, specs[selected])
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_rule": selected,
                "test": test_score,
                "train": train_score,
            }
        )
    return out


def shuffled_label_control(rows: list[Row]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    observed = prefix_holdouts(rows)
    observed_mean = sum(row["test"]["accuracy"] for row in observed) / len(observed)
    labels = [row["action"] for row in rows]
    means = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        fake = [dict(row, action=label) for row, label in zip(rows, shuffled)]
        scores = prefix_holdouts(fake)
        means.append(sum(row["test"]["accuracy"] for row in scores) / len(scores))
    means.sort()
    return {
        "observed_mean_test_accuracy": observed_mean,
        "p05_mean_test_accuracy": means[int(0.05 * (RANDOM_TRIALS - 1))],
        "p50_mean_test_accuracy": means[int(0.50 * (RANDOM_TRIALS - 1))],
        "p95_mean_test_accuracy": means[int(0.95 * (RANDOM_TRIALS - 1))],
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    data = build_rows()
    rows = data["rows"]
    holdouts = prefix_holdouts(rows)
    control = shuffled_label_control(rows)
    mean_accuracy = control["observed_mean_test_accuracy"]
    positive_splits = sum(1 for row in holdouts if row["test"]["accuracy"] > row["train"]["accuracy"] - 0.10)
    beats_control = mean_accuracy > control["p95_mean_test_accuracy"]
    promoted = beats_control and mean_accuracy >= 0.70
    weak = beats_control and mean_accuracy >= 0.60
    classification = (
        "PROMOTED_SEED_BOOTSTRAP_DECISION_POLICY_CLUE"
        if promoted
        else "WEAK_SEED_BOOTSTRAP_DECISION_POLICY_CLUE"
        if weak
        else "seed_bootstrap_decision_policy_not_promoted"
    )
    action_counts = Counter(row["action"] for row in rows)
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "control": control,
        "decision": {
            "generator_status": "not_generator_teacher_forced_decision_surface",
            "next_blocker": (
                "copy/literal decision policy is only a clue unless integrated "
                "into a target-free seed decoder with source and length choices"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "holdouts": holdouts,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "seed_bootstrap_copy_surface_final": rel(SURFACE_FINAL),
            "seed_bootstrap_transducer_final": rel(TRANSDUCER_FINAL),
            "surface_script": rel(SURFACE_SCRIPT),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "seed_bootstrap_decision_policy_gate.v1",
        "scope": "analysis_only_seed_bootstrap_decision_policy",
        "summary": {
            "action_counts": dict(action_counts),
            "beats_shuffled_label_p95": beats_control,
            "classification": classification,
            "literal_tape_digits": data["literal_tape_digits"],
            "mean_test_accuracy": mean_accuracy,
            "positive_splits": positive_splits,
            "promoted": promoted,
            "rows": len(rows),
            "seed_digits": data["seed_digits"],
            "weak": weak,
        },
        "translation_delta": "NONE",
        "validation": {
            "book_lengths": data["book_lengths"],
            "validation_errors": [],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Seed Bootstrap Decision-Policy Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Rows: `{s['rows']}`.",
        f"- Action counts: `{s['action_counts']}`.",
        f"- Mean test accuracy: `{s['mean_test_accuracy']:.3f}`.",
        f"- Shuffled-label p95 mean accuracy: `{c['p95_mean_test_accuracy']:.3f}`.",
        f"- Beats shuffled p95: `{s['beats_shuffled_label_p95']}`.",
        "",
        "## Prefix Holdout",
        "",
        "| Cutoff book | Rule | Train acc | Test acc | Test recall | Test precision |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["holdouts"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_rule']}` | "
            f"`{row['train']['accuracy']:.3f}` | `{row['test']['accuracy']:.3f}` | "
            f"`{row['test']['copy_recall']:.3f}` | `{row['test']['copy_precision']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_SEED_BOOTSTRAP_DECISION_POLICY_CLUE`."
                if s["promoted"]
                else "`seed_bootstrap_decision_policy_not_promoted`: simple visible-state rules do not promote as a bootstrap decision policy."
            ),
            "",
            "This remains teacher-forced on the true prefix path; it is not an executable seed generator.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Final Seed Bootstrap Decision-Policy Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit isolates the policy missing from the failed target-free seed "
        "transducer. It stays on the true seed prefix path and tests whether "
        "small decoder-visible rules can predict the oracle surface action "
        "(`copy` vs `literal`) under prefix holdout.",
        "",
        f"The oracle surface has `{s['rows']}` decision rows with action counts "
        f"`{s['action_counts']}`. Prefix-selected visible-state rules reach mean "
        f"test accuracy `{s['mean_test_accuracy']:.3f}`. Shuffled-label controls "
        f"have p95 mean accuracy `{c['p95_mean_test_accuracy']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_SEED_BOOTSTRAP_DECISION_POLICY_CLUE`."
            if s["promoted"]
            else "`seed_bootstrap_decision_policy_not_promoted`."
        ),
        "",
        "This does not generate the seed stream. It only tests the decision layer "
        "on the correct prefix path; source and length selection remain external. "
        "The result should be used to decide whether a richer bootstrap policy "
        "is worth integrating into a decoder.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_seed_bootstrap_decision_policy_gate.py](../scripts/01_seed_bootstrap_decision_policy_gate.py)",
        "- [01_seed_bootstrap_decision_policy_gate.json](test_results/01_seed_bootstrap_decision_policy_gate.json)",
        "- [01_seed_bootstrap_decision_policy_gate.md](test_results/01_seed_bootstrap_decision_policy_gate.md)",
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
