from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRAJECTORY_SCRIPT = HERE / "scripts" / "38_trajectory_neighbor_parser_audit.py"
STATE_SUPPORT_SCRIPT = HERE / "scripts" / "39_observable_state_support_audit.py"
STATE_SUPPORT_RESULT = TEST_RESULTS / "39_observable_state_support_audit.json"

OUT_STEM = "40_latent_state_requirement_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


SplitFn = tuple[str, Callable[[dict[str, Any]], Any]]


def split_functions() -> list[SplitFn]:
    return [
        ("none", lambda row: "all"),
        ("book_parity", lambda row: row["book"] % 2),
        ("book_mod3", lambda row: row["book"] % 3),
        ("book_mod5", lambda row: row["book"] % 5),
        ("book_decade", lambda row: row["book"] // 10),
        ("book_half", lambda row: "low" if row["book"] < 40 else "high"),
        ("op_index_parity", lambda row: row["op_index"] % 2),
        ("op_index_bucket", lambda row: min(int(row["op_index"]), 8)),
        ("target_half", lambda row: "left" if row["target_start"] * 2 < row["target_length"] else "right"),
        ("active_type", lambda row: row["active_label"][0]),
        ("active_length_bucket", lambda row: length_bucket(int(row["active_label"][1]))),
    ]


def length_bucket(value: int) -> str:
    for cut in [1, 3, 5, 8, 13, 21, 34, 55]:
        if value <= cut:
            return f"le{cut}"
    return "gt55"


def augmented_key(module, row: dict[str, Any], family: str, split: SplitFn) -> tuple[Any, ...]:
    return module.trajectory_vector(row, family) + ((split[0], split[1](row)),)


def exact_examples_by_key(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    split: SplitFn,
    train_books: set[int],
) -> dict[tuple[Any, ...], Counter[tuple[Any, ...]]]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    out: dict[tuple[Any, ...], Counter[tuple[Any, ...]]] = defaultdict(Counter)
    for row in decisions:
        if row["book"] not in exact_books or row["book"] not in train_books:
            continue
        out[augmented_key(module, row, family, split)][tuple(row["stable_label"])] += 1
    return out


def residual_queries(module, decisions: list[dict[str, Any]], book_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return module.residual_queries(decisions, book_rows)


def score_family_split(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    split: SplitFn,
    train_books: set[int],
    query_books: set[int],
) -> dict[str, Any]:
    examples = exact_examples_by_key(
        module, decisions, book_rows, family, split, train_books
    )
    rows = []
    for query in residual_queries(module, decisions, book_rows):
        if query["book"] not in query_books:
            continue
        key = augmented_key(module, query, family, split)
        counter = examples.get(key, Counter())
        stable = tuple(query["stable_label"])
        if not counter:
            status = "out_of_support"
            deterministic = False
        elif len(counter) == 1 and stable in counter:
            status = "deterministic_match"
            deterministic = True
        elif len(counter) == 1:
            status = "deterministic_contradiction"
            deterministic = False
        elif stable in counter:
            status = "ambiguous_includes_stable"
            deterministic = False
        else:
            status = "ambiguous_excludes_stable"
            deterministic = False
        rows.append(
            {
                "book": query["book"],
                "op_index": query["op_index"],
                "stable_label": stable,
                "active_label": tuple(query["active_label"]),
                "support": sum(counter.values()),
                "label_count": len(counter),
                "status": status,
                "deterministic_match": deterministic,
            }
        )
    counts = Counter(row["status"] for row in rows)
    return {
        "family": family,
        "split": split[0],
        "query_count": len(rows),
        "deterministic_matches": counts.get("deterministic_match", 0),
        "supported_count": sum(1 for row in rows if row["status"] != "out_of_support"),
        "out_of_support_count": counts.get("out_of_support", 0),
        "contradiction_count": counts.get("deterministic_contradiction", 0)
        + counts.get("ambiguous_excludes_stable", 0),
        "ambiguous_with_stable_count": counts.get("ambiguous_includes_stable", 0),
        "status_counts": dict(sorted(counts.items())),
        "rows": rows,
    }


def prequential_score(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    split: SplitFn,
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        score = score_family_split(
            module,
            decisions,
            book_rows,
            family,
            split,
            set(range(10, cutoff)),
            set(range(cutoff, 70)),
        )
        rows.append(
            {
                "cutoff_book": cutoff,
                "query_count": score["query_count"],
                "deterministic_matches": score["deterministic_matches"],
                "supported_count": score["supported_count"],
                "status_counts": score["status_counts"],
            }
        )
    return rows


def latent_lower_bound(rows: list[dict[str, Any]]) -> dict[str, Any]:
    # This is an oracle lower bound, not a promoted rule: each distinct stable
    # label required in an unsupported/contradictory observable state needs a
    # latent distinction if the exposed state is retained.
    needed_pairs = {
        (row["status"], row["stable_label"])
        for row in rows
        if row["status"] != "deterministic_match"
    }
    needed_labels = {row["stable_label"] for row in rows if row["status"] != "deterministic_match"}
    return {
        "residuals_needing_latent_resolution": sum(
            1 for row in rows if row["status"] != "deterministic_match"
        ),
        "distinct_stable_labels_needing_resolution": len(needed_labels),
        "status_label_pairs_needing_resolution": len(needed_pairs),
        "minimum_oracle_bits_for_residual_index": (
            0.0 if not rows else math.log2(max(1, len(rows)))
        ),
        "minimum_oracle_bits_for_distinct_labels": (
            0.0 if not needed_labels else math.log2(len(needed_labels))
        ),
    }


def make_result() -> dict[str, Any]:
    gate39 = load_json(STATE_SUPPORT_RESULT)
    assert_boundary("observable_state_support_audit", gate39)
    if gate39["classification"] != "observable_state_support_boundary_audit_only":
        raise RuntimeError("gate40 expects gate39 boundary audit")

    traj = load_module("trajectory_for_gate40", TRAJECTORY_SCRIPT)
    state_support = load_module("state_support_for_gate40", STATE_SUPPORT_SCRIPT)
    decisions, book_rows = state_support.build_decisions(traj)
    exact_books = [row["book"] for row in book_rows if row["exact"]]
    residual_books = [row["book"] for row in book_rows if not row["exact"]]

    all_books = set(range(10, 70))
    residual_set = set(residual_books)
    scores = []
    for family in ["trajectory", "context", "combined"]:
        for split in split_functions():
            scores.append(
                score_family_split(
                    traj,
                    decisions,
                    book_rows,
                    family,
                    split,
                    all_books,
                    residual_set,
                )
            )
    best = max(
        scores,
        key=lambda row: (
            row["deterministic_matches"],
            row["supported_count"],
            -row["contradiction_count"],
            row["family"],
            row["split"],
        ),
    )
    best_split = next(split for split in split_functions() if split[0] == best["split"])
    preq = prequential_score(
        traj, decisions, book_rows, best["family"], best_split
    )
    preq_cells_with_residuals = sum(1 for row in preq if row["query_count"] > 0)
    preq_cells_with_match = sum(1 for row in preq if row["deterministic_matches"] > 0)
    lower_bound = latent_lower_bound(best["rows"])
    promotes = (
        best["deterministic_matches"] == best["query_count"]
        and preq_cells_with_match == preq_cells_with_residuals
    )
    if promotes:
        classification = "latent_state_split_parser_promoted"
    elif best["deterministic_matches"] > 0:
        classification = "latent_state_split_weak_clue_not_promoted"
    else:
        classification = "latent_state_requirement_audit_only"
    return {
        "schema": "latent_state_requirement_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "observable_state_support_audit": rel(STATE_SUPPORT_RESULT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "quantifies_latent_state_requirement": True,
        },
        "summary": {
            "exact_book_count": len(exact_books),
            "residual_book_count": len(residual_books),
            "residual_books": residual_books,
            "families_tested": ["trajectory", "context", "combined"],
            "splits_tested": [name for name, _ in split_functions()],
            "score_count": len(scores),
            "best_family": best["family"],
            "best_split": best["split"],
            "best_deterministic_matches": best["deterministic_matches"],
            "best_query_count": best["query_count"],
            "best_supported_count": best["supported_count"],
            "best_out_of_support_count": best["out_of_support_count"],
            "prequential_cells_with_residuals": preq_cells_with_residuals,
            "prequential_cells_with_match": preq_cells_with_match,
            "promotes_latent_state_split_parser": promotes,
            **lower_bound,
            "interpretation": (
                "Latent-state requirement tests whether simple observable splits "
                "of the exposed state repair the support failure, and records a "
                "lower bound on residual distinctions if they do not."
            ),
        },
        "scoreboard": [
            {
                "family": row["family"],
                "split": row["split"],
                "deterministic_matches": row["deterministic_matches"],
                "supported_count": row["supported_count"],
                "out_of_support_count": row["out_of_support_count"],
                "contradiction_count": row["contradiction_count"],
                "status_counts": row["status_counts"],
            }
            for row in sorted(
                scores,
                key=lambda row: (
                    -row["deterministic_matches"],
                    -row["supported_count"],
                    row["contradiction_count"],
                    row["family"],
                    row["split"],
                ),
            )
        ],
        "best_rows": best["rows"],
        "best_prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "latent_state_requirement_quantified",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    scoreboard_rows = [
        [
            row["family"],
            row["split"],
            row["deterministic_matches"],
            row["supported_count"],
            row["out_of_support_count"],
            row["contradiction_count"],
            row["status_counts"],
        ]
        for row in result["scoreboard"][:18]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["query_count"],
            row["deterministic_matches"],
            row["supported_count"],
            row["status_counts"],
        ]
        for row in result["best_prequential_rows"]
    ]
    residual_rows = [
        [
            row["book"],
            row["op_index"],
            row["active_label"],
            row["stable_label"],
            row["support"],
            row["label_count"],
            row["status"],
        ]
        for row in result["best_rows"]
    ]
    body = f"""# Latent State Requirement Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 40 asks whether the gate-39 support failure can be repaired by simple
observable latent-state splits such as book parity, book decade, operation
bucket, target half, or active operation class. If not, it quantifies the
minimum residual distinctions a true latent state would still need.

This is a requirement audit, not a promoted parser.

## Summary

- Exact parser books: `{s['exact_book_count']}`.
- Residual parser books: `{s['residual_book_count']}`.
- Families tested: `{s['families_tested']}`.
- Splits tested: `{s['splits_tested']}`.
- Score count: `{s['score_count']}`.
- Best split: `{s['best_family']} + {s['best_split']}`.
- Best deterministic matches:
  `{s['best_deterministic_matches']}/{s['best_query_count']}`.
- Best supported residual states:
  `{s['best_supported_count']}/{s['best_query_count']}`.
- Best out-of-support residual states:
  `{s['best_out_of_support_count']}/{s['best_query_count']}`.
- Prequential cells with any deterministic match:
  `{s['prequential_cells_with_match']}/{s['prequential_cells_with_residuals']}`.
- Residuals needing latent resolution:
  `{s['residuals_needing_latent_resolution']}`.
- Distinct stable labels needing resolution:
  `{s['distinct_stable_labels_needing_resolution']}`.
- Minimum oracle bits for distinct labels:
  `{s['minimum_oracle_bits_for_distinct_labels']:.3f}`.
- Promotes parser rule: `{s['promotes_latent_state_split_parser']}`.

## Top Split Scoreboard

{md_table(scoreboard_rows, ["family", "split", "deterministic matches", "supported", "out of support", "contradictions", "status counts"])}

## Prequential Rows For Best Split

{md_table(preq_rows, ["cutoff", "queries", "deterministic matches", "supported", "status counts"])}

## Residual Rows For Best Split

{md_table(residual_rows, ["book", "op", "active label", "stable label", "support", "label count", "status"])}

## Decision

No simple observable split promotes a parser. The best split still leaves the
residual first-drift choices without deterministic support. A real improvement
must introduce a falsifiable latent state with enough structure to predict
these distinctions, or explain the target digit stream source-free.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
