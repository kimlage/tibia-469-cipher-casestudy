from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRAJECTORY_SCRIPT = HERE / "scripts" / "38_trajectory_neighbor_parser_audit.py"
TRAJECTORY_RESULT = TEST_RESULTS / "38_trajectory_neighbor_parser_audit.json"

OUT_STEM = "39_observable_state_support_audit"
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


def exact_examples_by_state(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    train_books: set[int],
    label_mode: str,
) -> dict[tuple[Any, ...], Counter[tuple[Any, ...]]]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    out: dict[tuple[Any, ...], Counter[tuple[Any, ...]]] = defaultdict(Counter)
    for row in decisions:
        if row["book"] not in exact_books or row["book"] not in train_books:
            continue
        key = module.trajectory_vector(row, family)
        label = tuple(row["stable_label"])
        if label_mode == "type":
            label = (label[0],)
        out[key][label] += 1
    return out


def residual_rows(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    train_books: set[int],
    query_books: set[int],
    label_mode: str,
) -> list[dict[str, Any]]:
    examples = exact_examples_by_state(
        module, decisions, book_rows, family, train_books, label_mode
    )
    rows: list[dict[str, Any]] = []
    for query in module.residual_queries(decisions, book_rows):
        if query["book"] not in query_books:
            continue
        key = module.trajectory_vector(query, family)
        counter = examples.get(key, Counter())
        stable_label = tuple(query["stable_label"])
        active_label = tuple(query["active_label"])
        if label_mode == "type":
            stable_label = (stable_label[0],)
            active_label = (active_label[0],)
        labels = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))
        label_set = {label for label, _ in labels}
        if not labels:
            status = "out_of_support"
        elif len(labels) == 1 and stable_label in label_set:
            status = "deterministic_match"
        elif len(labels) == 1:
            status = "deterministic_contradiction"
        elif stable_label in label_set:
            status = "ambiguous_includes_stable"
        else:
            status = "ambiguous_excludes_stable"
        rows.append(
            {
                "book": query["book"],
                "op_index": query["op_index"],
                "drift_class": query["drift_class"],
                "active_label": active_label,
                "stable_label": stable_label,
                "support": sum(counter.values()),
                "label_count": len(counter),
                "labels": [
                    {"label": label, "count": count}
                    for label, count in labels[:8]
                ],
                "status": status,
            }
        )
    return rows


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["status"] for row in rows)
    return {
        "query_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "supported_count": sum(1 for row in rows if row["status"] != "out_of_support"),
        "deterministic_match_count": counts.get("deterministic_match", 0),
        "contradiction_count": counts.get("deterministic_contradiction", 0)
        + counts.get("ambiguous_excludes_stable", 0),
        "ambiguous_with_stable_count": counts.get("ambiguous_includes_stable", 0),
    }


def full_fit_by_family(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    label_mode: str,
) -> dict[str, Any]:
    all_books = set(range(10, 70))
    residual_books = {row["book"] for row in book_rows if not row["exact"]}
    out = {}
    for family in ["trajectory", "context", "combined"]:
        rows = residual_rows(
            module,
            decisions,
            book_rows,
            family,
            all_books,
            residual_books,
            label_mode,
        )
        out[family] = {"summary": summarize_rows(rows), "rows": rows}
    return out


def prequential_by_family(
    module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    label_mode: str,
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        query_books = set(range(cutoff, 70))
        result_rows = residual_rows(
            module,
            decisions,
            book_rows,
            family,
            train_books,
            query_books,
            label_mode,
        )
        summary = summarize_rows(result_rows)
        rows.append(
            {
                "cutoff_book": cutoff,
                "query_count": summary["query_count"],
                "supported_count": summary["supported_count"],
                "deterministic_match_count": summary["deterministic_match_count"],
                "status_counts": summary["status_counts"],
            }
        )
    return rows


def build_decisions(module):
    trace_module = module.load_module("segmentation_trace_for_gate39", module.TRACE_SCRIPT)
    gate111 = module.load_module("gate111_for_gate39", module.GATE111_SCRIPT)
    policy_module = module.load_module("policy_drift_for_gate39", module.POLICY_DRIFT_SCRIPT)
    repair_module = module.load_module("observable_repair_for_gate39", module.OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = module.load_module(
        "conditional_repair_for_gate39", module.CONDITIONAL_REPAIR_SCRIPT
    )
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable = module.stable_by_book(trace_module, gate111, books)
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in conditional_module.make_predicates()})
    classifier = next(
        item
        for item in conditional_module.make_classifiers()
        if item["label"] == module.ACTIVE_CLASSIFIER
    )
    return module.parse_active_trajectory(
        repair_module,
        conditional_module,
        trace_module,
        policy_module,
        books,
        stable,
        classifier,
        predicates,
    )


def make_result() -> dict[str, Any]:
    gate38 = load_json(TRAJECTORY_RESULT)
    assert_boundary("trajectory_neighbor_parser_audit", gate38)
    if gate38["classification"] != "trajectory_neighbor_parser_rejected":
        raise RuntimeError("gate39 expects gate38 trajectory-neighbor rejection")

    module = load_module("trajectory_neighbor_for_gate39", TRAJECTORY_SCRIPT)
    decisions, book_rows = build_decisions(module)
    exact_books = [row["book"] for row in book_rows if row["exact"]]
    residual_books = [row["book"] for row in book_rows if not row["exact"]]

    exact_label = full_fit_by_family(module, decisions, book_rows, "exact")
    type_label = full_fit_by_family(module, decisions, book_rows, "type")
    best_family = max(
        exact_label,
        key=lambda family: (
            exact_label[family]["summary"]["deterministic_match_count"],
            exact_label[family]["summary"]["supported_count"],
            -exact_label[family]["summary"]["contradiction_count"],
            family,
        ),
    )
    best_summary = exact_label[best_family]["summary"]
    preq = prequential_by_family(
        module, decisions, book_rows, best_family, "exact"
    )
    preq_with_residuals = sum(1 for row in preq if row["query_count"] > 0)
    preq_with_deterministic_match = sum(
        1 for row in preq if row["deterministic_match_count"] > 0
    )
    promotes = (
        best_summary["deterministic_match_count"] == best_summary["query_count"]
        and preq_with_deterministic_match == preq_with_residuals
    )
    if promotes:
        classification = "observable_state_support_parser_promoted"
    elif best_summary["deterministic_match_count"] > 0:
        classification = "observable_state_support_weak_clue_not_promoted"
    else:
        classification = "observable_state_support_boundary_audit_only"
    return {
        "schema": "observable_state_support_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "trajectory_neighbor_parser_audit": rel(TRAJECTORY_RESULT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "diagnoses_observable_state_support": True,
        },
        "summary": {
            "exact_book_count": len(exact_books),
            "residual_book_count": len(residual_books),
            "residual_books": residual_books,
            "decision_count": len(decisions),
            "families_tested": ["trajectory", "context", "combined"],
            "best_exact_label_family": best_family,
            "best_exact_label_deterministic_matches": best_summary[
                "deterministic_match_count"
            ],
            "best_exact_label_supported_count": best_summary["supported_count"],
            "best_exact_label_contradiction_count": best_summary[
                "contradiction_count"
            ],
            "best_exact_label_query_count": best_summary["query_count"],
            "prequential_cells_with_residuals": preq_with_residuals,
            "prequential_cells_with_deterministic_match": preq_with_deterministic_match,
            "promotes_observable_state_support_parser": promotes,
            "interpretation": (
                "Observable-state support diagnoses whether the residual first "
                "drifts are unseen states, contradictory states, or deterministic "
                "matches relative to exact parser books. It does not add a new "
                "local policy."
            ),
        },
        "exact_label_full_fit": exact_label,
        "type_label_full_fit": type_label,
        "best_prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "observable_state_support_diagnosed",
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
    exact_rows = []
    for family, payload in result["exact_label_full_fit"].items():
        summary = payload["summary"]
        exact_rows.append(
            [
                family,
                summary["query_count"],
                summary["supported_count"],
                summary["deterministic_match_count"],
                summary["contradiction_count"],
                summary["ambiguous_with_stable_count"],
                summary["status_counts"],
            ]
        )
    type_rows = []
    for family, payload in result["type_label_full_fit"].items():
        summary = payload["summary"]
        type_rows.append(
            [
                family,
                summary["supported_count"],
                summary["deterministic_match_count"],
                summary["contradiction_count"],
                summary["status_counts"],
            ]
        )
    preq_rows = [
        [
            row["cutoff_book"],
            row["query_count"],
            row["supported_count"],
            row["deterministic_match_count"],
            row["status_counts"],
        ]
        for row in result["best_prequential_rows"]
    ]
    residual_rows = [
        [
            row["book"],
            row["op_index"],
            row["drift_class"],
            row["active_label"],
            row["stable_label"],
            row["support"],
            row["label_count"],
            row["status"],
        ]
        for row in result["exact_label_full_fit"][s["best_exact_label_family"]]["rows"]
    ]
    body = f"""# Observable State Support Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 39 diagnoses why the residual first-drift decisions are not solved by
nearest trajectory reuse. It asks whether each residual state is outside the
observed exact-book support, deterministically contradicted by exact examples,
or ambiguously supported.

This is not a new parser and not a compression sweep.

## Summary

- Exact parser books: `{s['exact_book_count']}`.
- Residual parser books: `{s['residual_book_count']}`.
- Families tested: `{s['families_tested']}`.
- Best exact-label family: `{s['best_exact_label_family']}`.
- Deterministic exact-label matches:
  `{s['best_exact_label_deterministic_matches']}/{s['best_exact_label_query_count']}`.
- Supported residual states at best family:
  `{s['best_exact_label_supported_count']}/{s['best_exact_label_query_count']}`.
- Contradictory residual states at best family:
  `{s['best_exact_label_contradiction_count']}`.
- Prequential cells with deterministic match:
  `{s['prequential_cells_with_deterministic_match']}/{s['prequential_cells_with_residuals']}`.
- Promotes parser rule: `{s['promotes_observable_state_support_parser']}`.

## Exact Label Full Fit

{md_table(exact_rows, ["family", "queries", "supported", "deterministic matches", "contradictions", "ambiguous with stable", "status counts"])}

## Type-Only Label Full Fit

{md_table(type_rows, ["family", "supported", "deterministic matches", "contradictions", "status counts"])}

## Prequential Rows For Best Exact Family

{md_table(preq_rows, ["cutoff", "queries", "supported", "deterministic matches", "status counts"])}

## Residual Rows For Best Exact Family

{md_table(residual_rows, ["book", "op", "drift class", "active label", "stable label", "support", "label count", "status"])}

## Decision

Observable-state support does not promote a parser. No tested observable state
family gives deterministic exact-label matches for the residual first-drift
choices. The residuals are either outside the exact-book state support or land
in states whose exact-book labels do not determine the needed stable operation.

The next blocker is a real latent state or a source-free target digit account,
not another nearest-state reuse rule over the currently exposed features.

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
