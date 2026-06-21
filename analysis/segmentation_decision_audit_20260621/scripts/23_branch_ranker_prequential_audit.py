from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BRANCH_CONTINUATION_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
BRANCH_CONTINUATION = TEST_RESULTS / "22_residual_branch_continuation_audit.json"

OUT_STEM = "23_branch_ranker_prequential_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
EPOCHS = 8
PERMUTATION_CONTROLS = 100
TRAINING_MODES = [
    {"label": "uniform", "clean_weight": 1, "residual_weight": 1},
    {"label": "residual_weight5", "clean_weight": 1, "residual_weight": 5},
    {"label": "residual_weight20", "clean_weight": 1, "residual_weight": 20},
    {"label": "residual_only", "clean_weight": 0, "residual_weight": 1},
]


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


def branch_features(decision: dict[str, Any], branch: dict[str, Any]) -> dict[str, float]:
    op = branch["op"]
    metrics = branch["metrics"]
    active = decision["active_op"]
    length = int(op["length"])
    active_length = int(active["length"])
    suffix_total_digits = (
        metrics["suffix_literal_digits"] + metrics["suffix_copy_digits"]
    )
    copy_share = (
        0.0 if suffix_total_digits == 0 else metrics["suffix_copy_digits"] / suffix_total_digits
    )
    label = branch["label"]
    return {
        "bias": 1.0,
        "is_active": 1.0 if branch["is_active"] else 0.0,
        "is_copy": 1.0 if op["type"] == "copy" else 0.0,
        "is_literal": 1.0 if op["type"] == "literal" else 0.0,
        "is_immediate_copy_branch": 1.0 if "immediate_copy" in label else 0.0,
        "is_literal_stop_branch": 1.0 if "literal_stop" in label else 0.0,
        "len_scaled": length / 60.0,
        "len_le1": 1.0 if length <= 1 else 0.0,
        "len_le5": 1.0 if length <= 5 else 0.0,
        "len_le8": 1.0 if length <= 8 else 0.0,
        "len_ge10": 1.0 if length >= 10 else 0.0,
        "delta_active_len_scaled": (length - active_length) / 60.0,
        "suffix_ops_scaled": metrics["suffix_op_count"] / 30.0,
        "suffix_literal_digits_scaled": metrics["suffix_literal_digits"] / 200.0,
        "suffix_copy_digits_scaled": metrics["suffix_copy_digits"] / 200.0,
        "suffix_copy_count_scaled": metrics["suffix_copy_count"] / 30.0,
        "suffix_copy_share": copy_share,
    }


def score_features(weights: dict[str, float], features: dict[str, float]) -> float:
    return sum(weights.get(key, 0.0) * value for key, value in features.items())


def stable_branch(decision: dict[str, Any]) -> dict[str, Any] | None:
    for branch in decision["branches"]:
        if branch["is_stable"]:
            return branch
    return None


def choose_branch(weights: dict[str, float], decision: dict[str, Any]) -> dict[str, Any]:
    return max(
        decision["branches"],
        key=lambda branch: (
            score_features(weights, branch_features(decision, branch)),
            branch["is_active"],
            -int(branch["op"]["length"]),
            branch["label"],
        ),
    )


def train_pairwise(
    decisions: list[dict[str, Any]],
    epochs: int = EPOCHS,
    random_positive: bool = False,
    seed: int = 0,
    clean_weight: int = 1,
    residual_weight: int = 1,
) -> dict[str, float]:
    rng = random.Random(seed)
    weights: dict[str, float] = {}
    train_rows = []
    for row in decisions:
        if not row["branches"]:
            continue
        weight = residual_weight if row["kind"] == "residual_first_drift" else clean_weight
        for _ in range(weight):
            train_rows.append(row)
    for _ in range(epochs):
        for decision in train_rows:
            if random_positive:
                positive = rng.choice(decision["branches"])
            else:
                positive = stable_branch(decision)
                if positive is None:
                    continue
            positive_features = branch_features(decision, positive)
            positive_score = score_features(weights, positive_features)
            for negative in decision["branches"]:
                if negative is positive:
                    continue
                negative_features = branch_features(decision, negative)
                if positive_score <= score_features(weights, negative_features):
                    for key, value in positive_features.items():
                        weights[key] = weights.get(key, 0.0) + value
                    for key, value in negative_features.items():
                        weights[key] = weights.get(key, 0.0) - value
                    positive_score = score_features(weights, positive_features)
    return weights


def evaluate(weights: dict[str, float], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        if not decision["branches"]:
            continue
        chosen = choose_branch(weights, decision)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "chosen_is_stable": chosen["is_stable"],
                "chosen_is_active": chosen["is_active"],
                "chosen_label": chosen["label"],
                "chosen_op": chosen["op"],
                "stable_op": decision["stable_op"],
                "drift_class": decision["drift_class"],
            }
        )
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in rows if row["kind"] == "clean_control"]
    return {
        "total_hits": sum(1 for row in rows if row["chosen_is_stable"]),
        "total_total": len(rows),
        "residual_hits": sum(1 for row in residual_rows if row["chosen_is_stable"]),
        "residual_total": len(residual_rows),
        "clean_hits": sum(1 for row in clean_rows if row["chosen_is_stable"]),
        "clean_total": len(clean_rows),
        "clean_false_changes": sum(
            1 for row in clean_rows if not row["chosen_is_stable"]
        ),
        "residual_miss_books": [
            row["book"] for row in residual_rows if not row["chosen_is_stable"]
        ],
        "clean_false_change_books_sample": sorted(
            {row["book"] for row in clean_rows if not row["chosen_is_stable"]}
        )[:20],
    }


def top_weights(weights: dict[str, float], limit: int = 12) -> list[dict[str, Any]]:
    return [
        {"feature": key, "weight": value}
        for key, value in sorted(
            weights.items(), key=lambda item: (-abs(item[1]), item[0])
        )[:limit]
    ]


def prequential_rows(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in decisions if row["book"] < cutoff]
        test = [row for row in decisions if row["book"] >= cutoff]
        mode_rows = []
        for mode in TRAINING_MODES:
            weights = train_pairwise(
                train,
                clean_weight=mode["clean_weight"],
                residual_weight=mode["residual_weight"],
            )
            train_score = evaluate(weights, train)
            test_score = evaluate(weights, test)
            mode_rows.append(
                {
                    "mode": mode["label"],
                    "weights": weights,
                    "train_score": train_score,
                    "test_score": test_score,
                }
            )
        selected = max(
            mode_rows,
            key=lambda row: (
                row["train_score"]["total_hits"],
                row["train_score"]["residual_hits"],
                -row["train_score"]["clean_false_changes"],
                row["mode"],
            ),
        )
        oracle = max(
            mode_rows,
            key=lambda row: (
                row["test_score"]["total_hits"],
                row["test_score"]["residual_hits"],
                -row["test_score"]["clean_false_changes"],
                row["mode"],
            ),
        )
        train_score = selected["train_score"]
        test_score = selected["test_score"]
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_mode": selected["mode"],
                "train_total_hits": train_score["total_hits"],
                "train_total": train_score["total_total"],
                "train_residual_hits": train_score["residual_hits"],
                "train_residual_total": train_score["residual_total"],
                "train_clean_false_changes": train_score["clean_false_changes"],
                "test_total_hits": test_score["total_hits"],
                "test_total": test_score["total_total"],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_residual_miss_books": test_score["residual_miss_books"],
                "oracle_mode": oracle["mode"],
                "oracle_test_total_hits": oracle["test_score"]["total_hits"],
                "oracle_test_residual_hits": oracle["test_score"]["residual_hits"],
                "selected_matches_oracle_total_hits": (
                    test_score["total_hits"] == oracle["test_score"]["total_hits"]
                ),
                "top_weights": top_weights(selected["weights"], limit=8),
            }
        )
    return rows


def permutation_control(
    decisions: list[dict[str, Any]], real_total_hits: int
) -> dict[str, Any]:
    total_hits: list[int] = []
    residual_hits: list[int] = []
    clean_false_changes: list[int] = []
    for seed in range(PERMUTATION_CONTROLS):
        weights = train_pairwise(
            decisions,
            random_positive=True,
            seed=seed,
            clean_weight=1,
            residual_weight=5,
        )
        score = evaluate(weights, decisions)
        total_hits.append(score["total_hits"])
        residual_hits.append(score["residual_hits"])
        clean_false_changes.append(score["clean_false_changes"])
    at_least_real = sum(1 for value in total_hits if value >= real_total_hits)
    return {
        "controls": PERMUTATION_CONTROLS,
        "total_hits_min": min(total_hits),
        "total_hits_median": sorted(total_hits)[len(total_hits) // 2],
        "total_hits_max": max(total_hits),
        "residual_hits_max": max(residual_hits),
        "clean_false_changes_min": min(clean_false_changes),
        "p_total_hits_ge_real": (at_least_real + 1) / (PERMUTATION_CONTROLS + 1),
    }


def make_result() -> dict[str, Any]:
    branch_continuation = load_json(BRANCH_CONTINUATION)
    assert_boundary("residual_branch_continuation_audit", branch_continuation)
    if branch_continuation["summary"]["promotes_branch_continuation_rule"]:
        raise RuntimeError("gate23 expects gate22 to be rejected")

    gate22 = load_module("branch_continuation_for_gate23", BRANCH_CONTINUATION_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    residual_decisions = [
        row for row in decisions if row["kind"] == "residual_first_drift"
    ]
    clean_decisions = [row for row in decisions if row["kind"] == "clean_control"]

    baseline_weights = {"is_active": 1.0}
    baseline_score = evaluate(baseline_weights, decisions)
    full_mode_rows = []
    for mode in TRAINING_MODES:
        weights = train_pairwise(
            decisions,
            clean_weight=mode["clean_weight"],
            residual_weight=mode["residual_weight"],
        )
        score = evaluate(weights, decisions)
        full_mode_rows.append(
            {
                "mode": mode["label"],
                "score": score,
                "top_weights": top_weights(weights),
            }
        )
    full_mode_rows.sort(
        key=lambda row: (
            -row["score"]["total_hits"],
            -row["score"]["residual_hits"],
            row["score"]["clean_false_changes"],
            row["mode"],
        )
    )
    full_score = full_mode_rows[0]["score"]
    preq = prequential_rows(decisions)
    perm = permutation_control(decisions, full_score["total_hits"])
    promotes = (
        all(row["test_clean_false_changes"] == 0 for row in preq)
        and all(row["test_residual_hits"] == row["test_residual_total"] for row in preq)
        and full_score["residual_hits"] == len(residual_decisions)
        and full_score["clean_false_changes"] == 0
    )
    classification = (
        "branch_ranker_promoted_prequential_parser"
        if promotes
        else "branch_ranker_prequential_rejected"
    )
    return {
        "schema": "branch_ranker_prequential_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "residual_branch_continuation_audit": rel(BRANCH_CONTINUATION),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_training_label": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(decisions),
            "residual_decision_count": len(residual_decisions),
            "clean_control_count": len(clean_decisions),
            "feature_count": len(branch_features(decisions[0], decisions[0]["branches"][0])),
            "epochs": EPOCHS,
            "training_modes": [row["label"] for row in TRAINING_MODES],
            "baseline_active_total_hits": baseline_score["total_hits"],
            "baseline_active_residual_hits": baseline_score["residual_hits"],
            "baseline_active_clean_false_changes": baseline_score[
                "clean_false_changes"
            ],
            "best_full_fit_mode": full_mode_rows[0]["mode"],
            "full_fit_total_hits": full_score["total_hits"],
            "full_fit_residual_hits": full_score["residual_hits"],
            "full_fit_clean_false_changes": full_score["clean_false_changes"],
            "prequential_cells": len(preq),
            "prequential_zero_clean_false_change_cells": sum(
                1 for row in preq if row["test_clean_false_changes"] == 0
            ),
            "prequential_cover_all_test_residual_cells": sum(
                1
                for row in preq
                if row["test_residual_hits"] == row["test_residual_total"]
            ),
            "promotes_branch_ranker": promotes,
            "interpretation": (
                "Gate 23 trains a small pairwise branch ranker on prefix stable-"
                "projection labels and evaluates it on future books. Features "
                "are observable branch and continuation metrics; stable prefix "
                "match is not used as a feature."
            ),
        },
        "baseline_active_score": baseline_score,
        "full_fit_mode_scoreboard": [
            {
                "mode": row["mode"],
                "total_hits": row["score"]["total_hits"],
                "residual_hits": row["score"]["residual_hits"],
                "clean_false_changes": row["score"]["clean_false_changes"],
                "residual_miss_books": row["score"]["residual_miss_books"],
            }
            for row in full_mode_rows
        ],
        "full_fit_score": full_score,
        "full_fit_top_weights": full_mode_rows[0]["top_weights"],
        "prequential_rows": preq,
        "permutation_control": perm,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "branch_ranker_rejected"
            if not promotes
            else "branch_ranker_promoted",
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
    lines = [
        "# Branch Ranker Prequential Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 23 asks whether the branch choices rejected by gate 22 can be",
        "learned as a small prefix-trained ranker. The ranker sees only",
        "observable branch and continuation features; stable projection is",
        "used as the training/evaluation label, not as a feature.",
        "",
        "## Scoreboard",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Residual decisions: `{s['residual_decision_count']}`.",
        f"- Clean controls: `{s['clean_control_count']}`.",
        f"- Features: `{s['feature_count']}`.",
        f"- Training modes: `{s['training_modes']}`.",
        "",
        "| Model | Total hits | Residual hits | Clean false changes |",
        "|---|---:|---:|---:|",
        f"| Active-branch baseline | `{s['baseline_active_total_hits']}/{s['decision_count']}` | `{s['baseline_active_residual_hits']}/{s['residual_decision_count']}` | `{s['baseline_active_clean_false_changes']}` |",
        f"| Full-fit pairwise ranker `{s['best_full_fit_mode']}` | `{s['full_fit_total_hits']}/{s['decision_count']}` | `{s['full_fit_residual_hits']}/{s['residual_decision_count']}` | `{s['full_fit_clean_false_changes']}` |",
        "",
        "## Full-Fit Modes",
        "",
        "| Mode | Total hits | Residual hits | Clean false changes |",
        "|---|---:|---:|---:|",
    ]
    for row in result["full_fit_mode_scoreboard"]:
        lines.append(
            f"| `{row['mode']}` | `{row['total_hits']}/{s['decision_count']}` | "
            f"`{row['residual_hits']}/{s['residual_decision_count']}` | "
            f"`{row['clean_false_changes']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Mode | Train hits | Test hits | Test residual hits | Test clean false changes |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_mode']}` | "
            f"`{row['train_total_hits']}/{row['train_total']}` | "
            f"`{row['test_total_hits']}/{row['test_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` |"
        )
    perm = result["permutation_control"]
    lines.extend(
        [
            "",
            "## Permutation Control",
            "",
            f"- Controls: `{perm['controls']}`.",
            f"- Total-hit range under random branch labels: `{perm['total_hits_min']}..{perm['total_hits_max']}`.",
            f"- Median total hits under random branch labels: `{perm['total_hits_median']}`.",
            f"- Max residual hits under random branch labels: `{perm['residual_hits_max']}`.",
            f"- Minimum clean false changes under random branch labels: `{perm['clean_false_changes_min']}`.",
            f"- `p(total_hits >= real_full_fit)`: `{perm['p_total_hits_ge_real']:.3f}`.",
            "",
            "## Decision",
            "",
            f"- Promotes branch ranker: `{s['promotes_branch_ranker']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- Prequential cover-all-test-residual cells: `{s['prequential_cover_all_test_residual_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- The learned ranker does not become a generative parser under prefix/holdout.",
            "- Compression bound is unchanged.",
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
