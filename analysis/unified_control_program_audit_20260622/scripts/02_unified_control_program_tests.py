from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_unified_residual_control_ledger.json"
OUT_STEM = "02_unified_control_program_tests"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 250
RANDOM_SEED = 46920260622
MIN_PROMOTION_SAVING_BITS = 10.0


LabelFn = Callable[[dict[str, Any]], str]
FeatureFn = Callable[[dict[str, Any]], str]


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


def logp(counter: Counter[str], key: str, alphabet: set[str]) -> float:
    return -math.log2((counter.get(key, 0) + 1) / (sum(counter.values()) + len(alphabet)))


def train_test(rows: list[dict[str, Any]], cutoff: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        [row for row in rows if int(row["book"]) < cutoff],
        [row for row in rows if int(row["book"]) >= cutoff],
    )


def label_cost(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    label_fn: LabelFn,
    feature_fn: FeatureFn | None = None,
) -> dict[str, Any]:
    all_labels = {label_fn(row) for row in train + test}
    global_counter = Counter(label_fn(row) for row in train)
    counters: dict[str, Counter[str]] = {}
    if feature_fn is not None:
        for row in train:
            counters.setdefault(feature_fn(row), Counter())[label_fn(row)] += 1
    bits = 0.0
    fallback = 0
    for row in test:
        counter = global_counter
        if feature_fn is not None:
            key = feature_fn(row)
            if key in counters:
                counter = counters[key]
            else:
                fallback += 1
        bits += logp(counter, label_fn(row), all_labels)
    return {"bits": bits, "fallback_rows": fallback, "test_rows": len(test)}


def full_stream_prequential_bits(rows: list[dict[str, Any]], label_fn: LabelFn) -> float:
    alphabet = {label_fn(row) for row in rows}
    counter: Counter[str] = Counter()
    total = 0.0
    for row in rows:
        label = label_fn(row)
        total += logp(counter, label, alphabet)
        counter[label] += 1
    return total


def residual_cost_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    type_bits = len(rows) * math.log2(2)
    length_uniform_bits = sum(math.log2(max(1, int(row["remaining_before_op"]))) for row in rows)
    literal_bits = sum(float(row["literal_payload_bits"]) for row in rows)
    source_bits = sum(float(row["source_address_bits"]) for row in rows)
    same_length_hint_bits = sum(float(row["same_length_chunk_hint_bits"]) for row in rows)
    rank_hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    type_length_stream_bits = full_stream_prequential_bits(rows, lambda row: row["type_length_symbol"])
    length_bucket_stream_bits = full_stream_prequential_bits(rows, lambda row: row["length_bucket"])
    op_type_stream_bits = full_stream_prequential_bits(rows, lambda row: row["op_type"])
    separated_source = type_bits + length_uniform_bits + literal_bits + source_bits
    separated_hint = type_bits + length_uniform_bits + literal_bits + rank_hint_bits
    control_stream_hint = type_length_stream_bits + literal_bits + rank_hint_bits
    innovation_copy_hint_control = (
        op_type_stream_bits + length_bucket_stream_bits + literal_bits + rank_hint_bits
    )
    return {
        "target_start_bits": 0.0,
        "op_type_uniform_bits": type_bits,
        "length_uniform_bits": length_uniform_bits,
        "literal_payload_bits": literal_bits,
        "source_address_bits": source_bits,
        "same_length_chunk_hint_bits": same_length_hint_bits,
        "copy_hint_rank_bits": rank_hint_bits,
        "op_type_stream_bits": op_type_stream_bits,
        "length_bucket_stream_bits": length_bucket_stream_bits,
        "type_length_stream_bits": type_length_stream_bits,
        "cost_models": {
            "start_type_length_literal_source_separated": separated_source,
            "start_type_length_literal_copy_hint": separated_hint,
            "innovation_tape_copy_hint_type_length_stream": control_stream_hint,
            "innovation_tape_copy_hint_separate_control_streams": innovation_copy_hint_control,
        },
        "reductions": {
            "copy_hint_vs_source_address_bits": source_bits - rank_hint_bits,
            "type_length_stream_vs_uniform_type_plus_length_bits": (
                type_bits + length_uniform_bits - type_length_stream_bits
            ),
            "best_unified_vs_separated_source_bits": separated_source
            - min(control_stream_hint, innovation_copy_hint_control, separated_hint),
        },
        "external_streams_remaining": [
            "op_type_control",
            "length_control",
            "literal_innovation_tape",
            "copy_hint_rank_stream",
        ],
        "derived_fields": ["target_start_from_prior_lengths"],
    }


def coupling_specs() -> dict[str, tuple[LabelFn, FeatureFn, str]]:
    return {
        "length_bucket_to_hint_rank_bucket": (
            lambda row: row["copy_hint_rank_bucket"] or "not_copy",
            lambda row: row["length_bucket"],
            "copy",
        ),
        "op_type_position_to_literal_consumption": (
            lambda row: "literal:" + row["length_bucket"]
            if row["op_type"] == "literal"
            else "copy:none",
            lambda row: row["op_type"] + "|" + row["op_pos_bucket"],
            "all",
        ),
        "book_phase_to_control_symbol": (
            lambda row: row["type_length_symbol"],
            lambda row: row["book_phase"],
            "all",
        ),
        "previous_op_to_next_control_symbol": (
            lambda row: row["type_length_symbol"],
            lambda row: row.get("prev_type_length_symbol") or "START",
            "all",
        ),
        "joint_type_length_to_hint_or_literal_behavior": (
            lambda row: "hint:" + (row["copy_hint_rank_bucket"] or "none")
            if row["op_type"] == "copy"
            else "literal:" + row["length_bucket"],
            lambda row: row["type_length_symbol"],
            "all",
        ),
    }


def add_prev_symbols(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    prev: str | None = None
    prev_book: int | None = None
    for row in rows:
        new = dict(row)
        if prev_book == int(row["book"]):
            new["prev_type_length_symbol"] = prev
        else:
            new["prev_type_length_symbol"] = None
        out.append(new)
        prev = row["type_length_symbol"]
        prev_book = int(row["book"])
    return out


def rows_for_scope(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    if scope == "copy":
        return [row for row in rows if row["op_type"] == "copy"]
    return rows


def coupling_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = add_prev_symbols(rows)
    rng = random.Random(RANDOM_SEED)
    results: dict[str, Any] = {}
    audit_only_leaky = {
        "op_type_position_to_literal_consumption",
        "joint_type_length_to_hint_or_literal_behavior",
    }
    for name, (label_fn, feature_fn, scope) in coupling_specs().items():
        scoped = rows_for_scope(rows, scope)
        cutoff_rows = []
        observed_total = 0.0
        baseline_total = 0.0
        for cutoff in PREFIX_CUTOFFS:
            train, test = train_test(scoped, cutoff)
            baseline = label_cost(train, test, label_fn)
            model = label_cost(train, test, label_fn, feature_fn)
            saving = baseline["bits"] - model["bits"]
            observed_total += saving
            baseline_total += baseline["bits"]
            cutoff_rows.append(
                {
                    "cutoff": cutoff,
                    "train_rows": len(train),
                    "test_rows": len(test),
                    "baseline_bits": baseline["bits"],
                    "model_bits": model["bits"],
                    "saving_bits": saving,
                    "fallback_rows": model["fallback_rows"],
                }
            )
        control_savings = []
        labels = [label_fn(row) for row in scoped]
        for _trial in range(RANDOM_TRIALS):
            shuffled = labels[:]
            rng.shuffle(shuffled)
            label_by_index = {id(row): label for row, label in zip(scoped, shuffled)}
            shuffled_label_fn = lambda row, mapping=label_by_index: mapping[id(row)]
            total = 0.0
            for cutoff in PREFIX_CUTOFFS:
                train, test = train_test(scoped, cutoff)
                baseline = label_cost(train, test, shuffled_label_fn)
                model = label_cost(train, test, shuffled_label_fn, feature_fn)
                total += baseline["bits"] - model["bits"]
            control_savings.append(total)
        control_savings.sort()
        p95 = control_savings[int(0.95 * (RANDOM_TRIALS - 1))]
        leaky = name in audit_only_leaky
        promoted = (
            not leaky
            and observed_total > MIN_PROMOTION_SAVING_BITS
            and observed_total > p95
        )
        if leaky:
            status = "AUDIT_ONLY_LEAKY_FEATURE"
        elif promoted:
            status = "PROMOTED_COUPLING_CLUE"
        elif observed_total > p95:
            status = "WEAK_COUPLING_BELOW_EFFECT_GATE"
        else:
            status = "REJECTED_CONTROL"
        results[name] = {
            "scope": scope,
            "rows": len(scoped),
            "cutoff_rows": cutoff_rows,
            "observed_total_saving_bits": observed_total,
            "baseline_total_bits": baseline_total,
            "random_saving_p95": p95,
            "beats_random_p95": observed_total > p95,
            "promoted": promoted,
            "status": status,
            "audit_only_leaky_feature": leaky,
            "minimum_promotion_saving_bits": MIN_PROMOTION_SAVING_BITS,
        }
    promoted = [name for name, row in results.items() if row["promoted"]]
    return {
        "relations": results,
        "promoted_relations": promoted,
        "promotes_control_coupling": bool(promoted),
    }


def unified_program_holdout(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = add_prev_symbols(rows)
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        train, test = train_test(rows, cutoff)
        type_bits = label_cost(train, test, lambda row: row["op_type"])["bits"]
        length_bits = label_cost(train, test, lambda row: row["length_bucket"])["bits"]
        type_length_bits = label_cost(train, test, lambda row: row["type_length_symbol"])["bits"]
        literal_bits = sum(float(row["literal_payload_bits"]) for row in test)
        copy_hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in test)
        source_bits = sum(float(row["source_address_bits"]) for row in test)
        uniform_type_bits = len(test) * math.log2(2)
        uniform_length_bits = sum(
            math.log2(max(1, int(row["remaining_before_op"]))) for row in test
        )
        independent_source = uniform_type_bits + uniform_length_bits + literal_bits + source_bits
        unified_type_length_hint = type_length_bits + literal_bits + copy_hint_bits
        separate_stream_hint = type_bits + length_bits + literal_bits + copy_hint_bits
        best_unified = min(unified_type_length_hint, separate_stream_hint)
        cutoff_rows.append(
            {
                "cutoff": cutoff,
                "train_rows": len(train),
                "test_rows": len(test),
                "type_bits": type_bits,
                "length_bucket_bits": length_bits,
                "type_length_bits": type_length_bits,
                "literal_bits": literal_bits,
                "copy_hint_bits": copy_hint_bits,
                "source_address_bits": source_bits,
                "independent_source_bits": independent_source,
                "unified_type_length_hint_bits": unified_type_length_hint,
                "separate_stream_hint_bits": separate_stream_hint,
                "best_unified_bits": best_unified,
                "reduction_vs_independent_source_bits": independent_source - best_unified,
                "exact_books_without_atlas": 0,
                "exact_ops_without_atlas": 0,
            }
        )
    total_independent = sum(row["independent_source_bits"] for row in cutoff_rows)
    total_unified = sum(row["best_unified_bits"] for row in cutoff_rows)
    return {
        "cutoff_rows": cutoff_rows,
        "summary": {
            "total_independent_source_bits": total_independent,
            "total_best_unified_bits": total_unified,
            "total_reduction_vs_independent_source_bits": total_independent - total_unified,
            "exact_books_without_atlas": 0,
            "exact_ops_without_atlas": 0,
            "fields_still_external": [
                "type_length_control_stream",
                "literal_innovation_tape",
                "copy_hint_rank_stream",
                "seed_books_0_9",
                "row0",
            ],
        },
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    assert_boundary("unified_residual_control_ledger", ledger)
    rows = sorted(
        ledger["ledger_rows"],
        key=lambda row: (int(row["book"]), int(row["op_index"])),
    )
    residual = residual_cost_ledger(rows)
    coupling = coupling_gate(rows)
    holdout = unified_program_holdout(rows)
    promoted = (
        coupling["promotes_control_coupling"]
        or holdout["summary"]["exact_books_without_atlas"] > 0
    )
    return {
        "schema": "unified_control_program_tests_v1",
        "scope": "analysis_only_residual_cost_coupling_holdout",
        "inputs": {"unified_residual_control_ledger": rel(LEDGER)},
        "residual_cost_ledger": residual,
        "control_tape_coupling_gate": coupling,
        "unified_program_holdout": holdout,
        "classification": (
            "unified_control_program_partial_coupling"
            if promoted
            else "unified_control_program_not_promoted"
        ),
        "decision": {
            "promotes_generator": False,
            "promotes_control_coupling": coupling["promotes_control_coupling"],
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    r = result["residual_cost_ledger"]
    h = result["unified_program_holdout"]["summary"]
    c = result["control_tape_coupling_gate"]
    lines = [
        "# Unified Control Program Tests",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Residual Cost Ledger",
        "",
        f"- Source-address bits: `{r['source_address_bits']:.3f}`.",
        f"- Copy-hint rank bits: `{r['copy_hint_rank_bits']:.3f}`.",
        f"- Literal innovation tape bits: `{r['literal_payload_bits']:.3f}`.",
        f"- Type:length stream bits: `{r['type_length_stream_bits']:.3f}`.",
        f"- Separated source model: `{r['cost_models']['start_type_length_literal_source_separated']:.3f}`.",
        f"- Separated copy-hint model: `{r['cost_models']['start_type_length_literal_copy_hint']:.3f}`.",
        f"- Innovation tape + copy hint + type:length stream: `{r['cost_models']['innovation_tape_copy_hint_type_length_stream']:.3f}`.",
        f"- Copy-hint saving vs source address: `{r['reductions']['copy_hint_vs_source_address_bits']:.3f}`.",
        f"- Best unified saving vs separated source: `{r['reductions']['best_unified_vs_separated_source_bits']:.3f}`.",
        f"- External streams remaining: `{r['external_streams_remaining']}`.",
        "",
        "## Control-Tape Coupling Gate",
        "",
        f"- Promoted relations: `{c['promoted_relations']}`.",
        f"- Promotes control coupling: `{c['promotes_control_coupling']}`.",
        "",
        "| Relation | Rows | Observed Saving | Random p95 | Promoted | Status |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for name, row in c["relations"].items():
        lines.append(
            f"| `{name}` | `{row['rows']}` | `{row['observed_total_saving_bits']:.3f}` | "
            f"`{row['random_saving_p95']:.3f}` | `{row['promoted']}` | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Unified Program Holdout",
            "",
            f"- Total independent source bits: `{h['total_independent_source_bits']:.3f}`.",
            f"- Total best unified bits: `{h['total_best_unified_bits']:.3f}`.",
            f"- Total reduction vs independent source: `{h['total_reduction_vs_independent_source_bits']:.3f}`.",
            f"- Exact books without atlas: `{h['exact_books_without_atlas']}`.",
            f"- Exact ops without atlas: `{h['exact_ops_without_atlas']}`.",
            f"- Fields still external: `{h['fields_still_external']}`.",
            "",
            "| Cutoff | Test Ops | Independent Source | Best Unified | Reduction | Exact Books |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["unified_program_holdout"]["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_rows']}` | "
            f"`{row['independent_source_bits']:.3f}` | "
            f"`{row['best_unified_bits']:.3f}` | "
            f"`{row['reduction_vs_independent_source_bits']:.3f}` | "
            f"`{row['exact_books_without_atlas']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This organizes the residual program into explicit streams; it does not generate books without those streams.",
            "- A promoted coupling relation would be evidence for synchronization; otherwise the result is residual organization, not a generator.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "residual_costs": result["residual_cost_ledger"]["cost_models"],
                "coupling_promoted": result["control_tape_coupling_gate"]["promoted_relations"],
                "holdout_summary": result["unified_program_holdout"]["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
