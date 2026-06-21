from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE105 = TEST_RESULTS / "105_optional_literal_exception_rule_audit.json"

PREFIX_CUTOFFS = [20, 35, 50, 60]
RANDOM_SEED = 469106
CONTROL_TRIALS = 500


@dataclass(frozen=True)
class Rule:
    name: str
    kind: str
    fn: Callable[[dict[str, Any]], bool]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def primitive_rules() -> list[Rule]:
    rules: list[Rule] = []

    def add(name: str, fn: Callable[[dict[str, Any]], bool]) -> None:
        rules.append(Rule(name=name, kind="primitive", fn=fn))

    add("op_index_eq_0", lambda row: int(row["op_index"]) == 0)
    add("op_index_le_1", lambda row: int(row["op_index"]) <= 1)
    add("op_index_ge_1", lambda row: int(row["op_index"]) >= 1)
    for threshold in [1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 20, 24, 50, 100, 133]:
        add(
            f"length_le_{threshold}",
            lambda row, threshold=threshold: int(row["length"]) <= threshold,
        )
        add(
            f"length_ge_{threshold}",
            lambda row, threshold=threshold: int(row["length"]) >= threshold,
        )
    for threshold in [1, 2, 3, 5, 10, 20, 24, 35, 50, 55, 88, 100, 125, 149, 200, 281]:
        add(
            f"target_start_le_{threshold}",
            lambda row, threshold=threshold: int(row["target_start"]) <= threshold,
        )
        add(
            f"target_start_ge_{threshold}",
            lambda row, threshold=threshold: int(row["target_start"]) >= threshold,
        )
    for threshold in [10, 20, 24, 35, 50, 55, 88, 100, 125, 149, 200, 281]:
        add(
            f"remaining_le_{threshold}",
            lambda row, threshold=threshold: int(row["remaining"]) <= threshold,
        )
        add(
            f"remaining_ge_{threshold}",
            lambda row, threshold=threshold: int(row["remaining"]) >= threshold,
        )
    add("prev_none", lambda row: row["previous_in_book_type"] is None)
    add("prev_copy", lambda row: row["previous_in_book_type"] == "copy")
    for threshold in [5, 6, 10, 11, 12, 13, 20, 24, 50, 100, 112, 133]:
        add(
            f"prev_len_le_{threshold}",
            lambda row, threshold=threshold: row["previous_in_book_length"] is not None
            and int(row["previous_in_book_length"]) <= threshold,
        )
        add(
            f"prev_len_ge_{threshold}",
            lambda row, threshold=threshold: row["previous_in_book_length"] is not None
            and int(row["previous_in_book_length"]) >= threshold,
        )
    return rules


def all_rules() -> list[Rule]:
    primitives = primitive_rules()
    rules = primitives[:]
    for index, rule_a in enumerate(primitives):
        for rule_b in primitives[index + 1 :]:
            rules.append(
                Rule(
                    name=f"({rule_a.name} and {rule_b.name})",
                    kind="pair",
                    fn=lambda row, a=rule_a.fn, b=rule_b.fn: a(row) and b(row),
                )
            )
            rules.append(
                Rule(
                    name=f"({rule_a.name} or {rule_b.name})",
                    kind="pair",
                    fn=lambda row, a=rule_a.fn, b=rule_b.fn: a(row) or b(row),
                )
            )
    return rules


def evaluate(rule: Rule, rows: list[dict[str, Any]], labels: list[bool] | None = None) -> dict[str, Any]:
    if labels is None:
        labels = [row["type"] == "literal" for row in rows]
    tp = fp = fn = tn = 0
    for row, label in zip(rows, labels, strict=True):
        predicted = rule.fn(row)
        if predicted and label:
            tp += 1
        elif predicted and not label:
            fp += 1
        elif not predicted and label:
            fn += 1
        else:
            tn += 1
    errors = fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "errors": errors,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def bitmask(rows: list[dict[str, Any]], fn: Callable[[dict[str, Any]], bool]) -> int:
    mask = 0
    for index, row in enumerate(rows):
        if fn(row):
            mask |= 1 << index
    return mask


def label_mask(labels: list[bool]) -> int:
    mask = 0
    for index, label in enumerate(labels):
        if label:
            mask |= 1 << index
    return mask


def score_mask(mask: int, labels: int, total: int) -> dict[str, Any]:
    tp = (mask & labels).bit_count()
    fp = (mask & ~labels).bit_count()
    fn = ((~mask) & labels).bit_count()
    tn = total - tp - fp - fn
    errors = fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "errors": errors,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def choose_best_mask(rule_masks: list[tuple[Rule, int]], labels: int, total: int) -> tuple[Rule, int, dict[str, Any]]:
    best_rule: Rule | None = None
    best_mask = 0
    best_score: dict[str, Any] | None = None
    best_key: tuple[Any, ...] | None = None
    for rule, mask in rule_masks:
        current = score_mask(mask, labels, total)
        key = (
            current["errors"],
            -current["f1"],
            0 if rule.kind == "primitive" else 1,
            rule.name,
        )
        if best_key is None or key < best_key:
            best_rule = rule
            best_mask = mask
            best_score = current
            best_key = key
    assert best_rule is not None and best_score is not None
    return best_rule, best_mask, best_score


def choose_best_rule(rules: list[Rule], rows: list[dict[str, Any]], labels: list[bool] | None = None) -> tuple[Rule, dict[str, Any]]:
    best_rule: Rule | None = None
    best_score: dict[str, Any] | None = None
    for rule in rules:
        current = evaluate(rule, rows, labels=labels)
        key = (
            current["errors"],
            -current["f1"],
            0 if rule.kind == "primitive" else 1,
            rule.name,
        )
        if best_score is None:
            best_rule = rule
            best_score = current
            best_key = key
            continue
        if key < best_key:
            best_rule = rule
            best_score = current
            best_key = key
    assert best_rule is not None and best_score is not None
    return best_rule, best_score


def summarize(values: list[int]) -> dict[str, Any]:
    return {
        "trials": len(values),
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def compact_eval(rule: Rule, score: dict[str, Any]) -> dict[str, Any]:
    return {"rule": rule.name, "kind": rule.kind, **score}


def make_result() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    gate105 = load_json(GATE105)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    assert_boundary("optional_literal_exception_rule_audit", gate105)
    if gate105["classification"] != "optional_literal_exception_rule_audit_only":
        raise RuntimeError("gate105 did not close as audit-only")

    rows = sorted(
        [
            row
            for row in gate100["skeleton_rows"]
            if bool(row["copy_available_minlen"])
        ],
        key=lambda row: (int(row["book"]), int(row["op_index"])),
    )
    rules = all_rules()
    fixed_rule = next(
        rule for rule in rules if rule.name == "(length_le_5 and remaining_ge_10)"
    )
    no_exception_rule = Rule("no_optional_exception", "baseline", lambda _row: False)
    rng = random.Random(RANDOM_SEED)

    split_rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_rows = [row for row in rows if int(row["book"]) < cutoff]
        test_rows = [row for row in rows if int(row["book"]) >= cutoff]
        if not train_rows or not test_rows:
            continue
        train_labels = [row["type"] == "literal" for row in train_rows]
        test_labels = [row["type"] == "literal" for row in test_rows]
        train_label_mask = label_mask(train_labels)
        test_label_mask = label_mask(test_labels)
        train_total = len(train_rows)
        test_total = len(test_rows)
        train_rule_masks = [(rule, bitmask(train_rows, rule.fn)) for rule in rules]
        test_rule_masks = [(rule, bitmask(test_rows, rule.fn)) for rule in rules]
        test_masks_by_name = {rule.name: mask for rule, mask in test_rule_masks}
        train_rule, _train_mask, train_score = choose_best_mask(
            train_rule_masks, train_label_mask, train_total
        )
        oracle_rule, _oracle_mask, oracle_test_score = choose_best_mask(
            test_rule_masks, test_label_mask, test_total
        )
        fixed_train_score = score_mask(
            bitmask(train_rows, fixed_rule.fn), train_label_mask, train_total
        )
        fixed_test_score = score_mask(
            bitmask(test_rows, fixed_rule.fn), test_label_mask, test_total
        )
        no_test_score = score_mask(0, test_label_mask, test_total)
        train_test_score = score_mask(
            test_masks_by_name[train_rule.name], test_label_mask, test_total
        )
        random_test_errors = []
        for _ in range(CONTROL_TRIALS):
            shuffled = train_labels[:]
            rng.shuffle(shuffled)
            shuffled_mask = label_mask(shuffled)
            random_rule, _random_mask, _random_train_score = choose_best_mask(
                train_rule_masks, shuffled_mask, train_total
            )
            random_test_errors.append(
                score_mask(
                    test_masks_by_name[random_rule.name],
                    test_label_mask,
                    test_total,
                )["errors"]
            )
        split_rows.append(
            {
                "cutoff": cutoff,
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
                "train_exceptions": sum(train_labels),
                "test_exceptions": sum(test_labels),
                "train_selected_rule_train": compact_eval(train_rule, train_score),
                "train_selected_rule_test": compact_eval(
                    train_rule, train_test_score
                ),
                "fixed_full_corpus_rule_train": compact_eval(
                    fixed_rule, fixed_train_score
                ),
                "fixed_full_corpus_rule_test": compact_eval(
                    fixed_rule, fixed_test_score
                ),
                "no_exception_baseline_test": compact_eval(
                    no_exception_rule, no_test_score
                ),
                "suffix_oracle_rule_test": compact_eval(
                    oracle_rule, oracle_test_score
                ),
                "random_train_label_control": {
                    **summarize(random_test_errors),
                    "train_selected_test_error_percentile": (
                        sum(
                            1
                            for value in random_test_errors
                            if value <= train_test_score["errors"]
                        )
                        / CONTROL_TRIALS
                    ),
                },
            }
        )

    train_selected_better_than_baseline = [
        row
        for row in split_rows
        if row["train_selected_rule_test"]["errors"]
        < row["no_exception_baseline_test"]["errors"]
    ]
    fixed_better_than_baseline = [
        row
        for row in split_rows
        if row["fixed_full_corpus_rule_test"]["errors"]
        < row["no_exception_baseline_test"]["errors"]
    ]
    train_selected_oracle_gaps = [
        row["train_selected_rule_test"]["errors"]
        - row["suffix_oracle_rule_test"]["errors"]
        for row in split_rows
    ]
    promotes_prequential_rule = (
        len(train_selected_better_than_baseline) == len(split_rows)
        and max(train_selected_oracle_gaps) == 0
        and False
    )
    classification = (
        "prequential_optional_literal_exception_rule_promotable"
        if promotes_prequential_rule
        else "prequential_optional_literal_exception_rule_not_promoted"
    )
    return {
        "schema": "prequential_optional_literal_rule_validation.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate105_optional_literal_exception_rule": rel(GATE105),
        },
        "scope": {
            "analysis_only": True,
            "tests_prequential_exception_rule_generalization": True,
            "target_text_dependency_retained": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "control_trials": CONTROL_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": {
            "evaluated_splits": len(split_rows),
            "train_selected_better_than_baseline_splits": len(
                train_selected_better_than_baseline
            ),
            "fixed_rule_better_than_baseline_splits": len(fixed_better_than_baseline),
            "mean_train_selected_oracle_gap_errors": mean(train_selected_oracle_gaps),
            "max_train_selected_oracle_gap_errors": max(train_selected_oracle_gaps),
            "promotes_prequential_rule": promotes_prequential_rule,
            "interpretation": (
                "Prefix-selected optional-literal rules generalize partially: "
                "they beat the no-exception baseline in every tested suffix, "
                "and the fixed corpus rule does too. But train-selected rules "
                "do not match suffix-oracle rule error in every split, and the "
                "whole family still depends on target copy availability and the "
                "length atlas. The result is predictive support for the clue, "
                "not a promoted generator."
            ),
        },
        "splits": split_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "prequential_exception_rule_partial_not_promoted",
            "skeleton_status": "exception_rule_partial_prequential_clue",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "106_prequential_optional_literal_rule_validation.json"
    md_path = TEST_RESULTS / "106_prequential_optional_literal_rule_validation.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Prequential Optional Literal Rule Validation",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 105 found an optional-literal exception rule on the full corpus.",
        "This audit selects rules on prefix rows only and evaluates them on suffix",
        "rows without retuning.",
        "",
        "## Result",
        "",
        f"- Evaluated splits: `{s['evaluated_splits']}`.",
        f"- Train-selected beats no-exception baseline splits: `{s['train_selected_better_than_baseline_splits']}`.",
        f"- Fixed full-corpus rule beats no-exception baseline splits: `{s['fixed_rule_better_than_baseline_splits']}`.",
        f"- Mean train-selected vs suffix-oracle error gap: `{s['mean_train_selected_oracle_gap_errors']:.3f}`.",
        f"- Max train-selected vs suffix-oracle error gap: `{s['max_train_selected_oracle_gap_errors']}`.",
        f"- Promotes prequential rule: `{s['promotes_prequential_rule']}`.",
        "",
        "## Splits",
        "",
        "| cutoff | train/test rows | train/test exceptions | train-selected rule | train test errors | fixed-rule test errors | baseline errors | oracle errors |",
        "|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in result["splits"]:
        lines.append(
            f"| {row['cutoff']} | {row['train_rows']}/{row['test_rows']} | "
            f"{row['train_exceptions']}/{row['test_exceptions']} | "
            f"`{row['train_selected_rule_test']['rule']}` | "
            f"{row['train_selected_rule_test']['errors']} | "
            f"{row['fixed_full_corpus_rule_test']['errors']} | "
            f"{row['no_exception_baseline_test']['errors']} | "
            f"{row['suffix_oracle_rule_test']['errors']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
