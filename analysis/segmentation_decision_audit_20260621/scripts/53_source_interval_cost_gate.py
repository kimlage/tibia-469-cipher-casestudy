from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE41 = TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"
GATE50 = TEST_RESULTS / "50_source_interval_context_gate.json"
GATE52 = TEST_RESULTS / "52_source_interval_observable_precision_gate.json"

OUT_STEM = "53_source_interval_cost_gate"


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


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def multiset_order_bits(labels: list[tuple[Any, ...]]) -> float:
    counts = Counter(labels)
    return log2_factorial(len(labels)) - sum(
        log2_factorial(count) for count in counts.values()
    )


def stable_label_by_book(gate50: dict[str, Any]) -> dict[int, tuple[Any, ...]]:
    out = {}
    for row in gate50["best_residual_rows"]:
        stable = row["stable_op"]
        out[int(row["book"])] = (stable["type"], int(stable["length"]))
    return out


def cost_for_rule(
    name: str,
    score: dict[str, Any],
    rule_count: int,
    decision_universe: int,
    residual_total: int,
    labels_by_book: dict[int, tuple[Any, ...]],
) -> dict[str, Any]:
    clean_false = int(score["clean_false_changes"])
    residual_misses = int(score["residual_total"]) - int(score["residual_hits"])
    missed_labels = [
        labels_by_book[int(book)] for book in score.get("residual_miss_books", [])
    ]
    rule_id_bits = math.log2(rule_count)
    clean_rollback_bits = log2_comb(decision_universe, clean_false)
    # Do not charge residual misses inside the known residual set. That would
    # grant the site lookup this rule is supposed to replace.
    residual_miss_site_bits = log2_comb(decision_universe, residual_misses)
    residual_miss_label_bits = multiset_order_bits(missed_labels)
    total = (
        rule_id_bits
        + clean_rollback_bits
        + residual_miss_site_bits
        + residual_miss_label_bits
    )
    return {
        "model": name,
        "policy": score["policy"],
        "predicate": score["predicate"],
        "residual_hits": int(score["residual_hits"]),
        "residual_misses": residual_misses,
        "clean_false_changes": clean_false,
        "rule_id_bits": rule_id_bits,
        "clean_rollback_bits": clean_rollback_bits,
        "residual_miss_site_bits": residual_miss_site_bits,
        "residual_miss_label_bits": residual_miss_label_bits,
        "total_bits": total,
        "missed_label_counts": {
            repr(key): value for key, value in sorted(Counter(missed_labels).items())
        },
    }


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    gate50 = load_json(GATE50)
    gate52 = load_json(GATE52)
    for name, data in [
        ("latent_state_lookup_cost_gate", gate41),
        ("source_interval_context_gate", gate50),
        ("source_interval_observable_precision_gate", gate52),
    ]:
        assert_boundary(name, data)
    if gate52["classification"] != "source_interval_observable_precision_weak_clue_not_promoted":
        raise RuntimeError("gate53 expects gate52 weak-clue state")

    summary41 = gate41["summary"]
    summary52 = gate52["summary"]
    baseline_lookup_bits = float(summary41["first_drift_lookup_lower_bound_bits"])
    source_decision_universe = int(
        summary52["decision_policy_rows"] / summary52["policy_count"]
    )
    decision_universe = max(int(summary41["decision_universe"]), source_decision_universe)
    residual_total = int(summary52["best_residual_total"])
    rule_count = int(summary52["scored_rule_count"])
    labels_by_book = stable_label_by_book(gate50)
    best = gate52["scoreboard_top"][0]
    best_zero = gate52["best_zero_fp_score"]
    best_cost = cost_for_rule(
        "best_observable_full_fit_rule",
        best,
        rule_count,
        decision_universe,
        residual_total,
        labels_by_book,
    )
    zero_cost = None
    if best_zero is not None:
        zero_cost = cost_for_rule(
            "best_observable_zero_fp_rule",
            best_zero,
            rule_count,
            decision_universe,
            residual_total,
            labels_by_book,
        )
    candidate_costs = [best_cost] + ([] if zero_cost is None else [zero_cost])
    for row in candidate_costs:
        row["net_vs_lookup_bits"] = row["total_bits"] - baseline_lookup_bits
    best_promotable = min(candidate_costs, key=lambda row: row["total_bits"])
    weak_cost_reduction = best_promotable["total_bits"] < baseline_lookup_bits
    promotes = False
    classification = (
        "source_interval_cost_weak_clue_not_promoted"
        if weak_cost_reduction
        else "source_interval_cost_rule_rejected"
    )
    return {
        "schema": "source_interval_cost_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
            "source_interval_context_gate": rel(GATE50),
            "source_interval_observable_precision_gate": rel(GATE52),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "prices_source_interval_signal_against_lookup": True,
        },
        "summary": {
            "baseline_lookup_bits": baseline_lookup_bits,
            "decision_universe": decision_universe,
            "source_decision_universe": source_decision_universe,
            "residual_total": residual_total,
            "rule_count": rule_count,
            "rule_id_bits": math.log2(rule_count),
            "best_model": best_promotable["model"],
            "best_model_bits": best_promotable["total_bits"],
            "best_model_net_vs_lookup_bits": best_promotable["net_vs_lookup_bits"],
            "best_full_fit_bits": best_cost["total_bits"],
            "best_full_fit_net_vs_lookup_bits": best_cost["net_vs_lookup_bits"],
            "best_zero_fp_bits": None if zero_cost is None else zero_cost["total_bits"],
            "best_zero_fp_net_vs_lookup_bits": None
            if zero_cost is None
            else zero_cost["net_vs_lookup_bits"],
            "weak_cost_reduction_before_holdout": weak_cost_reduction,
            "promotes_source_interval_cost_rule": promotes,
            "interpretation": (
                "Gate 53 prices the observable source-interval weak clue "
                "against the gate-41 residual lookup after charging for rule "
                "selection, clean rollbacks, and remaining residual misses in "
                "the full decision universe."
            ),
        },
        "cost_rows": candidate_costs,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_interval_signal_priced_against_lookup",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    lines = [
        "# Source Interval Cost Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 53 prices the observable source-interval weak clue against",
        "the gate-41 residual lookup. A rule must pay for rule selection,",
        "clean rollbacks, and remaining residual misses in the full decision",
        "universe before it can",
        "be credited as reducing ad hoc explanation.",
        "",
        "## Summary",
        "",
        f"- Baseline residual lookup: `{s['baseline_lookup_bits']:.3f}` bits.",
        f"- Decision universe: `{s['decision_universe']}`.",
        f"- Source-branch decision universe: `{s['source_decision_universe']}`.",
        f"- Residual total: `{s['residual_total']}`.",
        f"- Rule count: `{s['rule_count']}`.",
        f"- Rule ID bits: `{s['rule_id_bits']:.3f}`.",
        f"- Best priced model: `{s['best_model']}`.",
        f"- Best priced model bits: `{s['best_model_bits']:.3f}`.",
        f"- Best priced net vs lookup: `{s['best_model_net_vs_lookup_bits']:.3f}`.",
        f"- Weak cost reduction before holdout: `{s['weak_cost_reduction_before_holdout']}`.",
        "",
        "## Cost Rows",
        "",
        "| Model | Residual hits | Residual misses | Clean false changes | Total bits | Net vs lookup |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["cost_rows"]:
        lines.append(
            f"| `{row['model']}` | `{row['residual_hits']}` | "
            f"`{row['residual_misses']}` | `{row['clean_false_changes']}` | "
            f"`{row['total_bits']:.3f}` | `{row['net_vs_lookup_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes source-interval cost rule: `{s['promotes_source_interval_cost_rule']}`.",
            f"- {s['interpretation']}",
            "- The source-interval clue remains audit-only: any small priced saving is not a parser rule without clean holdout and broad residual coverage.",
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
