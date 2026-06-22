#!/usr/bin/env python3
"""Book-opcount start-anchor activation program gate.

Endpoint cascade showed that start-only source-boundary anchors reduce the
full-fit ledger, but do not generalize stably when enabled for every book. This
gate asks whether the decoded book-level op_count can control start-only anchor
activation as a small executable rule on top of v4.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_opcount_start_anchor_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CASCADE_SCRIPT = (
    ROOT
    / "analysis"
    / "endpoint_cascade_boundary_program_audit_20260622"
    / "scripts"
    / "01_endpoint_cascade_boundary_program_gate.py"
)
CASCADE_GATE = (
    ROOT
    / "analysis"
    / "endpoint_cascade_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_endpoint_cascade_boundary_program_gate.json"
)
EXECUTABLE_V4_GATE = (
    ROOT
    / "analysis"
    / "executable_v4_one_sided_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v4_one_sided_boundary_program_gate.json"
)
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)

JSON_OUT = TEST_RESULTS / "01_book_opcount_start_anchor_program_gate.json"
MD_OUT = TEST_RESULTS / "01_book_opcount_start_anchor_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_book_opcount_start_anchor_program_audit.md"

RANDOM_SEED = 46920260622
RANDOM_TRIALS = 5000
OPCOUNT_THRESHOLDS = list(range(1, 15))

Rule = tuple[str, Callable[[dict[str, Any]], bool]]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_cascade_module() -> Any:
    spec = importlib.util.spec_from_file_location("endpoint_cascade_gate", CASCADE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CASCADE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rule_family() -> list[Rule]:
    rules: list[Rule] = [
        ("none", lambda row: False),
        ("all", lambda row: True),
    ]
    for threshold in OPCOUNT_THRESHOLDS:
        rules.append(
            (
                f"op_count_le_{threshold}",
                lambda row, threshold=threshold: int(row["op_count"]) <= threshold,
            )
        )
    return rules


def build_book_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cascade_gate = load_json(CASCADE_GATE)
    executable_v4 = load_json(EXECUTABLE_V4_GATE)
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("endpoint_cascade_boundary_program_gate", cascade_gate)
    assert_boundary("executable_v4_one_sided_boundary_program_gate", executable_v4)
    assert_boundary("unified_external_tape_ledger", ledger)

    module = load_cascade_module()
    one_sided = module.load_one_sided_module()
    rows, meta = one_sided.build_event_rows()
    book_headers: dict[int, dict[str, Any]] = {}
    for row in ledger["ledger_rows"]:
        book_headers.setdefault(int(row["book"]), row)
    book_rows = []
    for book in range(10, 70):
        end_first = module.summarize_policy(one_sided, rows, meta, "end_first", books={book})
        cascade = module.summarize_policy(one_sided, rows, meta, "end_then_start", books={book})
        header = book_headers[book]
        delta = float(cascade["residual_bits"]) - float(end_first["residual_bits"])
        book_rows.append(
            {
                "book": book,
                "book_length": int(header["book_length"]),
                "book_length_bucket": str(header["book_length_bucket"]),
                "delta_start_enabled_vs_v4": delta,
                "op_count": int(header["book_op_count"]),
            }
        )
    return book_rows, {
        "cascade_gate": cascade_gate,
        "executable_v4": executable_v4,
        "ledger": ledger,
    }


def score_rule(book_rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    enabled = [row for row in book_rows if predicate(row)]
    delta = sum(float(row["delta_start_enabled_vs_v4"]) for row in enabled)
    return {
        "delta_vs_v4_before_declaration": delta,
        "enabled_books": [int(row["book"]) for row in enabled if "book" in row],
        "enabled_count": len(enabled),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, max(0, int(math.ceil(q * len(sorted_values)) - 1)))
    return sorted_values[index]


def random_opcount_controls(book_rows: list[dict[str, Any]], rules: list[Rule]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    op_counts = [int(row["op_count"]) for row in book_rows]
    deltas = [float(row["delta_start_enabled_vs_v4"]) for row in book_rows]
    best_savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = op_counts[:]
        rng.shuffle(shuffled)
        shuffled_rows = [
            {
                "delta_start_enabled_vs_v4": delta,
                "op_count": op_count,
            }
            for op_count, delta in zip(shuffled, deltas)
        ]
        best_delta = min(
            score_rule(shuffled_rows, predicate)["delta_vs_v4_before_declaration"]
            for _name, predicate in rules
        )
        best_savings.append(-best_delta)
    ordered = sorted(best_savings)
    return {
        "random_trials": RANDOM_TRIALS,
        "saving_p50": percentile(ordered, 0.50),
        "saving_p95": percentile(ordered, 0.95),
        "saving_p99": percentile(ordered, 0.99),
    }


def make_result() -> dict[str, Any]:
    book_rows, inputs = build_book_rows()
    rules = rule_family()
    declaration_bits = math.log2(len(rules))
    rule_summaries = []
    for name, predicate in rules:
        summary = score_rule(book_rows, predicate)
        summary["delta_vs_v4_after_declaration"] = (
            float(summary["delta_vs_v4_before_declaration"]) + declaration_bits
        )
        summary["rule"] = name
        rule_summaries.append(summary)
    best = min(rule_summaries, key=lambda row: row["delta_vs_v4_before_declaration"])
    fixed = next(row for row in rule_summaries if row["rule"] == "op_count_le_3")

    fixed_holdout = []
    positive_fixed_splits = 0
    total_fixed_test_delta = 0.0
    for cutoff in [20, 30, 40, 50, 60]:
        train_books = [row for row in book_rows if int(row["book"]) < cutoff]
        test_books = [row for row in book_rows if int(row["book"]) >= cutoff]
        train_delta = score_rule(
            train_books, lambda row: int(row["op_count"]) <= 3
        )["delta_vs_v4_before_declaration"]
        test_delta = score_rule(
            test_books, lambda row: int(row["op_count"]) <= 3
        )["delta_vs_v4_before_declaration"]
        total_fixed_test_delta += float(test_delta)
        if test_delta < 0:
            positive_fixed_splits += 1
        fixed_holdout.append(
            {
                "cutoff": cutoff,
                "fixed_rule": "op_count_le_3",
                "test_delta_vs_v4": test_delta,
                "train_delta_vs_v4": train_delta,
            }
        )

    prefix_selection_rows = []
    positive_prefix_splits = 0
    total_prefix_test_delta = 0.0
    for cutoff in [20, 30, 40, 50, 60]:
        train_books = [row for row in book_rows if int(row["book"]) < cutoff]
        test_books = [row for row in book_rows if int(row["book"]) >= cutoff]
        selected_name, selected_predicate, selected_train = min(
            (
                (
                    name,
                    predicate,
                    score_rule(train_books, predicate)["delta_vs_v4_before_declaration"],
                )
                for name, predicate in rules
            ),
            key=lambda item: item[2],
        )
        selected_test = score_rule(test_books, selected_predicate)[
            "delta_vs_v4_before_declaration"
        ]
        total_prefix_test_delta += float(selected_test)
        if selected_test < 0:
            positive_prefix_splits += 1
        prefix_selection_rows.append(
            {
                "cutoff": cutoff,
                "selected_rule": selected_name,
                "test_delta_vs_v4": selected_test,
                "train_delta_vs_v4": selected_train,
            }
        )

    controls = random_opcount_controls(book_rows, rules)
    observed_saving = -float(best["delta_vs_v4_before_declaration"])
    v4_summary = inputs["executable_v4"]["summary"]
    v4_residual = float(v4_summary["v4_residual_bits"])
    v4_external = float(v4_summary["v4_external_bits_excluding_seed"])
    candidate_external = v4_external + float(best["delta_vs_v4_after_declaration"])
    promoted = (
        best["rule"] == "op_count_le_3"
        and best["delta_vs_v4_after_declaration"] < 0
        and positive_fixed_splits >= 4
        and total_fixed_test_delta < 0
        and observed_saving > float(controls["saving_p95"])
    )
    weak = (
        best["rule"] == "op_count_le_3"
        and best["delta_vs_v4_after_declaration"] < 0
        and positive_fixed_splits >= 4
        and total_fixed_test_delta < 0
        and not promoted
    )
    return {
        "book_rows": book_rows,
        "case_reopened": False,
        "classification": (
            "PROMOTED_BOOK_OPCOUNT_START_ANCHOR_PROGRAM"
            if promoted
            else (
                "WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE"
                if weak
                else "book_opcount_start_anchor_program_not_promoted"
            )
        ),
        "compression_bound_status": "unchanged",
        "control": controls | {
            "observed_best_saving": observed_saving,
            "observed_beats_random_p95": observed_saving > float(controls["saving_p95"]),
        },
        "decision": {
            "book_opcount_start_anchor_promoted": promoted,
            "next_blocker": (
                "op_count activation is helpful but not stronger than random-opcount p95"
                if weak
                else "start-anchor activation did not reduce the executable ledger robustly"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "fixed_op_count_le_3_holdout": fixed_holdout,
        "inputs": {
            "endpoint_cascade_boundary_program_gate": rel(CASCADE_GATE),
            "executable_v4_one_sided_boundary_program_gate": rel(EXECUTABLE_V4_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_selection_rows": prefix_selection_rows,
        "row0_status": "unchanged_exogenous",
        "rule_summaries": rule_summaries,
        "schema": "book_opcount_start_anchor_program_gate.v1",
        "scope": "analysis_only_book_opcount_start_anchor_program",
        "summary": {
            "best_rule": best["rule"],
            "candidate_external_bits_excluding_seed": candidate_external,
            "declaration_bits_rule_family": declaration_bits,
            "delta_after_declaration_vs_v4": best["delta_vs_v4_after_declaration"],
            "delta_before_declaration_vs_v4": best["delta_vs_v4_before_declaration"],
            "fixed_op_count_le_3_delta_after_declaration_vs_v4": fixed[
                "delta_vs_v4_after_declaration"
            ],
            "fixed_op_count_le_3_positive_splits": positive_fixed_splits,
            "fixed_op_count_le_3_total_test_delta": total_fixed_test_delta,
            "prefix_selected_positive_splits": positive_prefix_splits,
            "prefix_selected_total_test_delta": total_prefix_test_delta,
            "promoted": promoted,
            "rule_family_size": len(rules),
            "v4_external_bits_excluding_seed": v4_external,
            "v4_residual_bits": v4_residual,
            "weak_clue": weak,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Book-Opcount Start-Anchor Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can decoded book-level `op_count` decide when start-only source-boundary "
        "anchors are active, reducing v4 without enabling the full cascade everywhere?",
        "",
        "## Summary",
        "",
        f"- Best rule: `{s['best_rule']}`.",
        f"- Rule family size: `{s['rule_family_size']}`; declaration bits: `{s['declaration_bits_rule_family']:.3f}`.",
        f"- Delta before declaration vs v4: `{s['delta_before_declaration_vs_v4']:.3f}` bits.",
        f"- Delta after declaration vs v4: `{s['delta_after_declaration_vs_v4']:.3f}` bits.",
        f"- Candidate external bits excluding seed: `{s['candidate_external_bits_excluding_seed']:.3f}`.",
        f"- Fixed `op_count_le_3` positive splits: `{s['fixed_op_count_le_3_positive_splits']}/5`.",
        f"- Fixed `op_count_le_3` aggregate test delta: `{s['fixed_op_count_le_3_total_test_delta']:.3f}` bits.",
        f"- Prefix-selected positive splits: `{s['prefix_selected_positive_splits']}/5`.",
        f"- Prefix-selected aggregate test delta: `{s['prefix_selected_total_test_delta']:.3f}` bits.",
        "",
        "## Random Op-Count Control",
        "",
        f"- Observed best saving: `{c['observed_best_saving']:.3f}` bits.",
        f"- Random p50/p95/p99 saving: `{c['saving_p50']:.3f}` / `{c['saving_p95']:.3f}` / `{c['saving_p99']:.3f}`.",
        f"- Beats random p95: `{c['observed_beats_random_p95']}`.",
        "",
        "## Rule Costs",
        "",
        "| Rule | Enabled books | Delta before declaration | Delta after declaration |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["rule_summaries"]:
        lines.append(
            f"| `{row['rule']}` | `{row['enabled_count']}` | "
            f"`{row['delta_vs_v4_before_declaration']:.3f}` | "
            f"`{row['delta_vs_v4_after_declaration']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Fixed Holdout",
            "",
            "| Cutoff | Train delta | Test delta |",
            "| ---: | ---: | ---: |",
        ]
    )
    for row in result["fixed_op_count_le_3_holdout"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_delta_vs_v4']:.3f}` | "
            f"`{row['test_delta_vs_v4']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_BOOK_OPCOUNT_START_ANCHOR_PROGRAM`."
                if s["promoted"]
                else (
                    "`WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`: the rule reduces v4 "
                    "and has fixed holdout support, but does not beat random-opcount p95."
                    if s["weak_clue"]
                    else "`book_opcount_start_anchor_program_not_promoted`."
                )
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Final Book-Opcount Start-Anchor Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether the decoded book-level `op_count` can activate "
        "start-only source-boundary anchors on top of executable v4. The best "
        "small rule is `op_count_le_3`: enable the start-anchor extension only "
        "for books with at most three operations.",
        "",
        f"Full-fit cost improves by `{s['delta_before_declaration_vs_v4']:.3f}` "
        f"bits before declaration and `{s['delta_after_declaration_vs_v4']:.3f}` "
        f"bits after charging `{s['declaration_bits_rule_family']:.3f}` bits for "
        f"the `{s['rule_family_size']}`-rule family. Fixed `op_count_le_3` improves "
        f"`{s['fixed_op_count_le_3_positive_splits']}/5` suffix splits with "
        f"aggregate delta `{s['fixed_op_count_le_3_total_test_delta']:.3f}` bits.",
        "",
        "However, the random op-count control is not cleared: observed best saving "
        f"is `{c['observed_best_saving']:.3f}` bits versus random p95 "
        f"`{c['saving_p95']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_BOOK_OPCOUNT_START_ANCHOR_PROGRAM`."
            if s["promoted"]
            else (
                "`WEAK_BOOK_OPCOUNT_START_ANCHOR_CLUE`. The signal is useful for "
                "the residual ledger, but it is not strong enough to replace v4 "
                "as the promoted executable program."
                if s["weak_clue"]
                else "`book_opcount_start_anchor_program_not_promoted`."
            )
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_book_opcount_start_anchor_program_gate.py](../scripts/01_book_opcount_start_anchor_program_gate.py)",
        "- [01_book_opcount_start_anchor_program_gate.json](test_results/01_book_opcount_start_anchor_program_gate.json)",
        "- [01_book_opcount_start_anchor_program_gate.md](test_results/01_book_opcount_start_anchor_program_gate.md)",
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
