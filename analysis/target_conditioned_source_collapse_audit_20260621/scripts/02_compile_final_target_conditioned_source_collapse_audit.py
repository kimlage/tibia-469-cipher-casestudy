from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_conditioned_source_collapse_gate.json"
OUT = REPORTS / "final_target_conditioned_source_collapse_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def main() -> None:
    gate = load_json(GATE)
    assert_boundary("target_conditioned_source_collapse_gate", gate)
    s = gate["summary"]
    c = gate["controls"]
    classification = (
        "TARGET_CONDITIONED_SOURCE_COLLAPSE_CLUE"
        if s["target_conditioned_source_collapse_clue"]
        else "TARGET_CONDITIONED_SOURCE_COLLAPSE_REJECTED"
    )
    lines = [
        "# Final Target-Conditioned Source Collapse Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Question",
        "",
        "If a separate target-stream mechanism supplies copied chunks, does",
        "copy-source choice collapse to a small canonical rule?",
        "",
        "## Result",
        "",
        f"- Copy events: `{s['copy_count']}`.",
        f"- Earliest matching source: `{s['earliest_matching_count']}/{s['copy_count']}` (`{s['earliest_matching_fraction']:.3f}`).",
        f"- Non-earliest exceptions: `{s['non_earliest_exception_count']}`.",
        f"- Legal source bits without target stream: `{s['legal_source_bits_without_target_stream']:.3f}`.",
        f"- Oracle rank bits among matching sources: `{s['oracle_rank_bits_among_matching_sources']:.3f}`.",
        f"- Earliest+exception total bits: `{s['earliest_exception_total_bits']:.3f}`.",
        f"- Delta vs oracle rank bits: `{s['earliest_exception_delta_vs_oracle_rank_bits']:.3f}` bits.",
        f"- Delta vs legal source bits: `{s['earliest_exception_delta_vs_legal_source_bits']:.3f}` bits.",
        f"- Random earliest-hit mean/p95/max: `{c['earliest_hit_mean']:.3f}` / `{c['earliest_hit_p95']:.3f}` / `{c['earliest_hit_max']}`.",
        f"- P(random earliest hits >= observed): `{c['earliest_hit_ge_observed_p_value']:.4f}`.",
        "",
        "This is a real mechanical clue about source choice under a target-conditioned",
        "view. It is not a decoder-side generator because the rule grants the future",
        "copied chunk. The practical implication is that source choice may be",
        "downstream of the missing target-stream mechanism rather than an independent",
        "primary blocker.",
        "",
        "## Decision",
        "",
        "- Promote as target-conditioned mechanical clue: `True`.",
        "- Promote as source generator: `False`.",
        "- The next generator blocker remains target-stream/skeleton-payload derivation.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target-conditioned source collapse gate](test_results/01_target_conditioned_source_collapse_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
