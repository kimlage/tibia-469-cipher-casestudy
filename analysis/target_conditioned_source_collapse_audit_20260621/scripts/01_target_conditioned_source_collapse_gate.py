from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
SOURCE_POLICY_GATE = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "02_copy_source_policy_gate.json"
)
SKELETON_AMBIGUITY = (
    ROOT
    / "analysis"
    / "skeleton_decoder_ambiguity_audit_20260621"
    / "reports"
    / "test_results"
    / "01_skeleton_decoder_ambiguity_gate.json"
)

OUT_STEM = "01_target_conditioned_source_collapse_gate"
RANDOM_TRIALS = 10000
RANDOM_SEED = 46920260621


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


def log2_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    ) / math.log(2)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def run_random_controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    matching_counts = [int(row["matching_source_count"]) for row in rows]
    earliest_hits = []
    exception_costs = []
    for _ in range(RANDOM_TRIALS):
        hits = 0
        exception_rank_bits = 0.0
        exception_count = 0
        for count in matching_counts:
            rank = rng.randrange(count)
            if rank == 0:
                hits += 1
            else:
                exception_count += 1
                exception_rank_bits += math.log2(max(1, count - 1))
        earliest_hits.append(hits)
        exception_costs.append(
            log2_choose(len(matching_counts), exception_count) + exception_rank_bits
        )
    return {
        "trials": RANDOM_TRIALS,
        "seed": RANDOM_SEED,
        "earliest_hit_mean": mean(earliest_hits),
        "earliest_hit_p95": percentile([float(v) for v in earliest_hits], 95),
        "earliest_hit_max": max(earliest_hits),
        "earliest_hit_ge_observed_count": None,
        "exception_cost_mean": mean(exception_costs),
        "exception_cost_p05": percentile(exception_costs, 5),
        "exception_cost_p50": percentile(exception_costs, 50),
        "exception_cost_p95": percentile(exception_costs, 95),
        "exception_cost_min": min(exception_costs),
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    policy = load_json(SOURCE_POLICY_GATE)
    ambiguity = load_json(SKELETON_AMBIGUITY)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("copy_source_policy_gate", policy)
    assert_boundary("skeleton_decoder_ambiguity", ambiguity)
    if ledger["classification"] != "copy_source_ledger_audit_only":
        raise RuntimeError("copy source ledger boundary changed")
    rows = ledger["copy_rows"]
    copy_count = len(rows)
    earliest_rows = [row for row in rows if row["source_is_earliest_matching"]]
    exception_rows = [row for row in rows if not row["source_is_earliest_matching"]]
    legal_source_bits = sum(math.log2(int(row["legal_source_count"])) for row in rows)
    oracle_rank_bits = sum(
        math.log2(int(row["matching_source_count"])) for row in rows
    )
    exception_site_bits = log2_choose(copy_count, len(exception_rows))
    exception_rank_bits = sum(
        math.log2(max(1, int(row["matching_source_count"]) - 1))
        for row in exception_rows
    )
    earliest_exception_bits = exception_site_bits + exception_rank_bits
    controls = run_random_controls(rows)
    controls["earliest_hit_ge_observed_count"] = sum(
        1 for _ in []  # filled below for schema stability
    )
    # Re-run only the observed-hit count deterministically from the stored seed
    # so the random score table stays compact.
    rng = random.Random(RANDOM_SEED)
    ge = 0
    for _ in range(RANDOM_TRIALS):
        hits = sum(1 for row in rows if rng.randrange(int(row["matching_source_count"])) == 0)
        ge += int(hits >= len(earliest_rows))
    controls["earliest_hit_ge_observed_count"] = ge
    controls["earliest_hit_ge_observed_p_value"] = ge / RANDOM_TRIALS
    promotes_generator = False
    target_conditioned_clue = (
        len(earliest_rows) >= 0.95 * copy_count
        and controls["earliest_hit_ge_observed_p_value"] <= 0.01
        and earliest_exception_bits < oracle_rank_bits
    )
    summary = {
        "copy_count": copy_count,
        "earliest_matching_count": len(earliest_rows),
        "earliest_matching_fraction": len(earliest_rows) / copy_count,
        "non_earliest_exception_count": len(exception_rows),
        "single_matching_source_events": int(
            ledger["summary"]["single_matching_source_events"]
        ),
        "multi_matching_source_events": int(
            ledger["summary"]["multi_matching_source_events"]
        ),
        "legal_source_bits_without_target_stream": legal_source_bits,
        "oracle_rank_bits_among_matching_sources": oracle_rank_bits,
        "earliest_exception_site_bits": exception_site_bits,
        "earliest_exception_rank_bits": exception_rank_bits,
        "earliest_exception_total_bits": earliest_exception_bits,
        "earliest_exception_delta_vs_oracle_rank_bits": (
            earliest_exception_bits - oracle_rank_bits
        ),
        "earliest_exception_delta_vs_legal_source_bits": (
            earliest_exception_bits - legal_source_bits
        ),
        "target_conditioned_source_collapse_clue": target_conditioned_clue,
        "promotes_source_generator": promotes_generator,
        "interpretation": (
            "If a separate target-stream mechanism supplies copied chunks, "
            "copy-source selection mostly collapses to earliest matching source "
            "plus a small exception list. Without that target stream, the rule "
            "is oracle-only and cannot decode the books."
        ),
    }
    return {
        "schema": "target_conditioned_source_collapse_gate.v1",
        "classification": "target_conditioned_source_collapse_clue_not_generator",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "copy_source_policy_gate": rel(SOURCE_POLICY_GATE),
            "skeleton_decoder_ambiguity_gate": rel(SKELETON_AMBIGUITY),
        },
        "scope": {
            "analysis_only": True,
            "grants_target_chunks": True,
            "oracle_target_stream_diagnostic": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "controls": controls,
        "non_earliest_exception_rows": exception_rows,
        "decision": {
            "target_stream_status": "still_missing_required_condition",
            "copy_source_status": "collapses_under_target_condition_only",
            "compression_bound_status": "unchanged_8154_676268",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    c = data["controls"]
    lines = [
        "# Target-Conditioned Source Collapse Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether copy-source choice remains a primary blocker once the",
        "copied target chunk is granted by a hypothetical target-stream mechanism.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_count']}`.",
        f"- Earliest matching source: `{s['earliest_matching_count']}/{s['copy_count']}` (`{s['earliest_matching_fraction']:.3f}`).",
        f"- Non-earliest exceptions: `{s['non_earliest_exception_count']}`.",
        f"- Legal source bits without target stream: `{s['legal_source_bits_without_target_stream']:.3f}`.",
        f"- Oracle rank bits among matching sources: `{s['oracle_rank_bits_among_matching_sources']:.3f}`.",
        f"- Earliest+exception total bits: `{s['earliest_exception_total_bits']:.3f}`.",
        f"- Earliest+exception delta vs oracle rank: `{s['earliest_exception_delta_vs_oracle_rank_bits']:.3f}` bits.",
        f"- Earliest+exception delta vs legal source: `{s['earliest_exception_delta_vs_legal_source_bits']:.3f}` bits.",
        "",
        "## Random Rank Controls",
        "",
        f"- Trials: `{c['trials']}`.",
        f"- Earliest-hit mean/p95/max: `{c['earliest_hit_mean']:.3f}` / `{c['earliest_hit_p95']:.3f}` / `{c['earliest_hit_max']}`.",
        f"- P(random earliest hits >= observed): `{c['earliest_hit_ge_observed_p_value']:.4f}`.",
        f"- Random exception cost mean/p05/p95: `{c['exception_cost_mean']:.3f}` / `{c['exception_cost_p05']:.3f}` / `{c['exception_cost_p95']:.3f}`.",
        "",
        "## Non-Earliest Exceptions",
        "",
        "| Book | Op | Target | Length | Canonical rank | Matching sources |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in data["non_earliest_exception_rows"]:
        lines.append(
            "| "
            f"`{row['book']}` | "
            f"`{row['op_index']}` | "
            f"`{row['target_start']}` | "
            f"`{row['length']}` | "
            f"`{row['canonical_matching_rank']}` | "
            f"`{row['matching_source_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Target-conditioned source-collapse clue: `{s['target_conditioned_source_collapse_clue']}`.",
            f"- Promotes source generator: `{s['promotes_source_generator']}`.",
            "- This is not a decoder-side generator because it grants the future copied chunk.",
            "- The result shifts the blocker toward a target-stream mechanism: if copied chunks are generated first, source choice becomes mostly canonical.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    data = make_result()
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(data["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
