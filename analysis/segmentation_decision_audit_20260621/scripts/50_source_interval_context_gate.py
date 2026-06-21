from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE22_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
GATE49 = TEST_RESULTS / "49_book_skeleton_alignment_gate.json"

OUT_STEM = "50_source_interval_context_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RADII = [2, 4, 8]
RANDOM_TRIALS = 400
RANDOM_SEED = 46950
BIG = 10**9


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


def load_books() -> dict[int, str]:
    return {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}


def emitted_before(books: dict[int, str], book: int, target_start: int) -> str:
    return "".join(books[index] for index in range(book)) + books[book][:target_start]


def padded_window(text: str, center: int, radius: int) -> str:
    left = text[max(0, center - radius) : center].rjust(radius, "^")
    right = text[center : min(len(text), center + radius)].ljust(radius, "$")
    return left + "|" + right


def hamming(left: str, right: str) -> int:
    if len(left) != len(right):
        raise RuntimeError("window lengths differ")
    return sum(1 for a, b in zip(left, right) if a != b)


def count_overlapping(text: str, needle: str) -> int:
    if not needle:
        return 0
    count = 0
    start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            return count
        count += 1
        start = pos + 1


def copy_features(
    books: dict[int, str],
    decision: dict[str, Any],
    branch: dict[str, Any],
) -> dict[str, Any]:
    op = branch["op"]
    book = int(decision["book"])
    target_start = int(decision["target_start"])
    target = books[book]
    emitted = emitted_before(books, book, target_start)
    if op["type"] != "copy" or op.get("source") is None:
        return {
            "is_copy": False,
            "payload_occurrences": 0,
            "source": None,
            "source_end": None,
            "length": int(op["length"]),
            "source_target_start_distance": BIG,
            "source_target_end_distance": BIG,
            "source_target_interval_distance": BIG,
            "max_source_context_recurrence": 0,
            "min_source_context_recurrence": 0,
            "radius_features": {},
        }
    source = int(op["source"])
    length = int(op["length"])
    source_end = source + length
    target_end = target_start + length
    payload = emitted[source:source_end]
    if source < 0 or source_end > len(emitted):
        raise RuntimeError({"type": "invalid_source", "op": op})
    if payload != target[target_start:target_end]:
        raise RuntimeError({"type": "invalid_payload", "op": op})

    radius_features = {}
    start_distances = []
    end_distances = []
    recurrences = []
    for radius in RADII:
        source_start_window = padded_window(emitted, source, radius)
        source_end_window = padded_window(emitted, source_end, radius)
        target_start_window = padded_window(target, target_start, radius)
        target_end_window = padded_window(target, target_end, radius)
        start_distance = hamming(source_start_window, target_start_window)
        end_distance = hamming(source_end_window, target_end_window)
        start_recurrence = count_overlapping(emitted, source_start_window.replace("|", ""))
        end_recurrence = count_overlapping(emitted, source_end_window.replace("|", ""))
        radius_features[str(radius)] = {
            "start_distance": start_distance,
            "end_distance": end_distance,
            "interval_distance": start_distance + end_distance,
            "start_recurrence": start_recurrence,
            "end_recurrence": end_recurrence,
        }
        start_distances.append(start_distance)
        end_distances.append(end_distance)
        recurrences.extend([start_recurrence, end_recurrence])
    return {
        "is_copy": True,
        "payload_occurrences": count_overlapping(emitted, payload),
        "source": source,
        "source_end": source_end,
        "length": length,
        "source_target_start_distance": min(start_distances),
        "source_target_end_distance": min(end_distances),
        "source_target_interval_distance": min(
            item["interval_distance"] for item in radius_features.values()
        ),
        "max_source_context_recurrence": max(recurrences),
        "min_source_context_recurrence": min(recurrences),
        "radius_features": radius_features,
    }


def branch_key(branch: dict[str, Any]) -> tuple[Any, ...]:
    op = branch["op"]
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def build_choice_rows() -> list[dict[str, Any]]:
    gate22 = load_module("gate22_for_gate50", GATE22_SCRIPT)
    books = load_books()
    rows = []
    for decision in gate22.collect_decisions()["decisions"]:
        branch_rows = []
        for branch in decision["branches"]:
            branch_rows.append(
                {
                    "branch": branch,
                    "features": copy_features(books, decision, branch),
                }
            )
        rows.append(
            {
                "book": int(decision["book"]),
                "target_start": int(decision["target_start"]),
                "stable_index": int(decision["stable_index"]),
                "kind": decision["kind"],
                "drift_class": decision["drift_class"],
                "active_op": decision["active_op"],
                "stable_op": decision["stable_op"],
                "branches": branch_rows,
            }
        )
    return rows


def policy_functions() -> dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]:
    out: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
        "prefer_active_control": lambda row: (
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "max_payload_occurrences": lambda row: (
            row["features"]["is_copy"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "max_source_context_recurrence": lambda row: (
            row["features"]["is_copy"],
            row["features"]["max_source_context_recurrence"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_context_recurrence": lambda row: (
            row["features"]["is_copy"],
            -row["features"]["min_source_context_recurrence"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_target_start_distance": lambda row: (
            row["features"]["is_copy"],
            -row["features"]["source_target_start_distance"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_target_end_distance": lambda row: (
            row["features"]["is_copy"],
            -row["features"]["source_target_end_distance"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
        "min_source_target_interval_distance": lambda row: (
            row["features"]["is_copy"],
            -row["features"]["source_target_interval_distance"],
            row["features"]["payload_occurrences"],
            row["features"]["length"],
            row["branch"]["is_active"],
            row["branch"]["label"],
        ),
    }
    for radius in RADII:
        out[f"min_interval_distance_r{radius}"] = (
            lambda row, radius=radius: (
                row["features"]["is_copy"],
                -row["features"]["radius_features"].get(str(radius), {}).get(
                    "interval_distance", BIG
                ),
                row["features"]["payload_occurrences"],
                row["features"]["length"],
                row["branch"]["is_active"],
                row["branch"]["label"],
            )
        )
        out[f"max_context_recurrence_r{radius}"] = (
            lambda row, radius=radius: (
                row["features"]["is_copy"],
                row["features"]["radius_features"].get(str(radius), {}).get(
                    "start_recurrence", 0
                )
                + row["features"]["radius_features"].get(str(radius), {}).get(
                    "end_recurrence", 0
                ),
                row["features"]["payload_occurrences"],
                row["features"]["length"],
                row["branch"]["is_active"],
                row["branch"]["label"],
            )
        )
    return out


def candidate_policy_names() -> list[str]:
    return [name for name in policy_functions() if name != "prefer_active_control"]


def choose(row: dict[str, Any], policy: str) -> dict[str, Any]:
    return max(row["branches"], key=policy_functions()[policy])


def score_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    detail_rows = []
    for row in rows:
        chosen = choose(row, policy)
        branch = chosen["branch"]
        detail_rows.append(
            {
                "book": row["book"],
                "target_start": row["target_start"],
                "stable_index": row["stable_index"],
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "chosen_is_stable": branch["is_stable"],
                "chosen_is_active": branch["is_active"],
                "chosen_op": branch["op"],
                "chosen_label": branch["label"],
                "chosen_features": chosen["features"],
                "stable_op": row["stable_op"],
                "active_op": row["active_op"],
            }
        )
    residual = [row for row in detail_rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in detail_rows if row["kind"] == "clean_control"]
    return {
        "policy": policy,
        "total_hits": sum(row["chosen_is_stable"] for row in detail_rows),
        "total_total": len(detail_rows),
        "residual_hits": sum(row["chosen_is_stable"] for row in residual),
        "residual_total": len(residual),
        "clean_false_changes": sum(not row["chosen_is_stable"] for row in clean),
        "clean_total": len(clean),
        "copy_branch_selected_count": sum(
            row["chosen_op"]["type"] == "copy" for row in detail_rows
        ),
        "residual_miss_books": [
            row["book"] for row in residual if not row["chosen_is_stable"]
        ],
        "rows": detail_rows,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["residual_hits"],
        row["total_hits"],
        -row["clean_false_changes"],
        row["policy"],
    )


def prequential_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = [
            score_policy(train, policy) for policy in candidate_policy_names()
        ]
        selected = max(train_scores, key=score_key)
        test_score = score_policy(test, selected["policy"])
        oracle = max(
            [score_policy(test, policy) for policy in candidate_policy_names()],
            key=score_key,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["policy"],
                "train_residual_hits": selected["residual_hits"],
                "train_residual_total": selected["residual_total"],
                "train_clean_false_changes": selected["clean_false_changes"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "oracle_test_policy": oracle["policy"],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "oracle_test_clean_false_changes": oracle["clean_false_changes"],
            }
        )
    return out


def random_branch_control(rows: list[dict[str, Any]], observed: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    hits = []
    for _ in range(RANDOM_TRIALS):
        total = 0
        for row in residual_rows:
            branch = rng.choice(row["branches"])["branch"]
            total += int(branch["is_stable"])
        hits.append(total)
    return {
        "observed_residual_hits": observed,
        "trials": RANDOM_TRIALS,
        "random_min": min(hits),
        "random_mean": sum(hits) / len(hits),
        "random_max": max(hits),
        "random_ge_observed_count": sum(hit >= observed for hit in hits),
        "p_ge_observed": (sum(hit >= observed for hit in hits) + 1)
        / (len(hits) + 1),
    }


def public_residual_rows(score: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in score["rows"]:
        if row["kind"] != "residual_first_drift":
            continue
        features = row["chosen_features"]
        rows.append(
            {
                "book": row["book"],
                "stable_index": row["stable_index"],
                "target_start": row["target_start"],
                "drift_class": row["drift_class"],
                "active_op": row["active_op"],
                "stable_op": row["stable_op"],
                "chosen_op": row["chosen_op"],
                "chosen_is_stable": row["chosen_is_stable"],
                "chosen_label": row["chosen_label"],
                "payload_occurrences": features["payload_occurrences"],
                "source_target_interval_distance": features[
                    "source_target_interval_distance"
                ],
                "max_source_context_recurrence": features[
                    "max_source_context_recurrence"
                ],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    gate49 = load_json(GATE49)
    assert_boundary("book_skeleton_alignment_gate", gate49)
    if gate49["classification"] != "book_skeleton_alignment_rejected":
        raise RuntimeError("gate50 expects gate49 rejection")
    rows = build_choice_rows()
    scoreboard = [score_policy(rows, policy) for policy in candidate_policy_names()]
    baseline = score_policy(rows, "prefer_active_control")
    best = max(scoreboard, key=score_key)
    preq = prequential_rows(rows)
    control = random_branch_control(rows, int(best["residual_hits"]))
    cells_with_residuals = sum(1 for row in preq if row["test_residual_total"] > 0)
    cells_all_residuals = sum(
        1
        for row in preq
        if row["test_residual_total"] > 0
        and row["test_residual_hits"] == row["test_residual_total"]
    )
    cells_zero_clean_false = sum(
        1 for row in preq if row["test_clean_false_changes"] == 0
    )
    promotes = (
        best["residual_hits"] == best["residual_total"]
        and best["clean_false_changes"] == 0
        and cells_all_residuals == cells_with_residuals
        and cells_zero_clean_false == len(preq)
        and control["p_ge_observed"] <= 0.05
    )
    if promotes:
        classification = "source_interval_context_parser_promoted"
    elif best["residual_hits"] > baseline["residual_hits"]:
        classification = "source_interval_context_weak_clue_not_promoted"
    else:
        classification = "source_interval_context_rejected"
    return {
        "schema": "source_interval_context_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "residual_branch_continuation_audit": rel(GATE22_SCRIPT),
            "book_skeleton_alignment_gate": rel(GATE49),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_source_interval_context": True,
        },
        "summary": {
            "decision_count": len(rows),
            "residual_count": best["residual_total"],
            "clean_control_count": best["clean_total"],
            "policy_count": len(candidate_policy_names()),
            "active_baseline_residual_hits": baseline["residual_hits"],
            "active_baseline_total_hits": baseline["total_hits"],
            "best_policy": best["policy"],
            "best_residual_hits": best["residual_hits"],
            "best_total_hits": best["total_hits"],
            "best_clean_false_changes": best["clean_false_changes"],
            "best_copy_branch_selected_count": best["copy_branch_selected_count"],
            "prequential_cells": len(preq),
            "prequential_cells_with_residuals": cells_with_residuals,
            "prequential_cover_all_residual_cells": cells_all_residuals,
            "prequential_zero_clean_false_change_cells": cells_zero_clean_false,
            "random_p_ge_observed": control["p_ge_observed"],
            "promotes_source_interval_context_parser": promotes,
            "interpretation": (
                "Gate 50 tests whether source interval context, payload recurrence, "
                "or source-target neighborhood similarity selects the remaining "
                "branch choices. It is a source/content structural test, not a "
                "compression sweep."
            ),
        },
        "scoreboard": [
            {
                "policy": row["policy"],
                "residual_hits": row["residual_hits"],
                "residual_total": row["residual_total"],
                "total_hits": row["total_hits"],
                "total_total": row["total_total"],
                "clean_false_changes": row["clean_false_changes"],
                "copy_branch_selected_count": row["copy_branch_selected_count"],
            }
            for row in sorted(scoreboard, key=score_key, reverse=True)
        ],
        "active_baseline": {
            "policy": baseline["policy"],
            "residual_hits": baseline["residual_hits"],
            "residual_total": baseline["residual_total"],
            "total_hits": baseline["total_hits"],
            "total_total": baseline["total_total"],
            "clean_false_changes": baseline["clean_false_changes"],
        },
        "prequential_rows": preq,
        "random_branch_control": control,
        "best_residual_rows": public_residual_rows(best),
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_interval_context_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    b = result["active_baseline"]
    lines = [
        "# Source Interval Context Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 50 tests whether the remaining branch choices are selected",
        "by source-side content structure: copied payload recurrence,",
        "source interval boundary recurrence, or source-target neighborhood",
        "similarity around the start/end of a candidate copy interval.",
        "",
        "The test uses observable branches from the residual branch",
        "continuation audit. It does not use plaintext, row0 semantics,",
        "or compression-bound retuning.",
        "",
        "## Summary",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Active baseline residual hits: `{b['residual_hits']}/{b['residual_total']}`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Best residual hits: `{s['best_residual_hits']}/{s['residual_count']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Random p(>= observed): `{s['random_p_ge_observed']:.3f}`.",
        "",
        "## Scoreboard",
        "",
        "| Policy | Residual hits | Total hits | Clean false changes | Copy branches selected |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["scoreboard"]:
        lines.append(
            f"| `{row['policy']}` | `{row['residual_hits']}/{row['residual_total']}` | "
            f"`{row['total_hits']}/{row['total_total']}` | "
            f"`{row['clean_false_changes']}` | "
            f"`{row['copy_branch_selected_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected policy | Train residual hits | Test residual hits | Test clean false changes | Oracle test policy | Oracle test residual hits |",
            "|---:|---|---:|---:|---:|---|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_policy']}` | "
            f"`{row['train_residual_hits']}/{row['train_residual_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | `{row['oracle_test_policy']}` | "
            f"`{row['oracle_test_residual_hits']}/{row['test_residual_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Rows Under Best Policy",
            "",
            "| Book | Op | Class | Active | Stable | Chosen | Hit | Payload occ. | Interval distance | Context recurrence |",
            "|---:|---:|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["best_residual_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['stable_index']}` | "
            f"`{row['drift_class']}` | `{row['active_op']}` | "
            f"`{row['stable_op']}` | `{row['chosen_op']}` | "
            f"`{row['chosen_is_stable']}` | "
            f"`{row['payload_occurrences']}` | "
            f"`{row['source_target_interval_distance']}` | "
            f"`{row['max_source_context_recurrence']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes source-interval context parser: `{s['promotes_source_interval_context_parser']}`.",
            f"- Prequential cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- Source interval context does not remove the remaining source/length dependency.",
            "- The result is analysis-only and does not change the compression bound.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
