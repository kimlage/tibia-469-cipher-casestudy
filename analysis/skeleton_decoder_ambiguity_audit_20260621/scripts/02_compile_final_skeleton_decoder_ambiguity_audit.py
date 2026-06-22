from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_skeleton_decoder_ambiguity_gate.json"
OUT = REPORTS / "final_skeleton_decoder_ambiguity_audit.md"


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
    assert_boundary("skeleton_decoder_ambiguity_gate", gate)
    s = gate["summary"]
    classification = (
        "SKELETON_DECODER_GENERATOR_PROMOTED"
        if s["promotes_skeleton_decoder_generator"]
        else "SKELETON_DECODER_AMBIGUITY_BLOCKS_GENERATOR"
    )
    lines = [
        "# Final Skeleton Decoder Ambiguity Audit",
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
        "If the exact source-free operation skeleton is granted, can a decoder",
        "emit the books without declared copy-source choices and literal payload?",
        "",
        "## Result",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Skeleton operations/copies/literals: `{s['operation_count']}` / `{s['copy_count']}` / `{s['literal_run_count']}`.",
        f"- Copied/literal digits: `{s['copied_digits']}` / `{s['literal_digits']}`.",
        f"- Seed payload digits granted operationally: `{s['seed_payload_digits']}`.",
        f"- Legal source branching lower bound: `{s['legal_source_log2_total']:.3f}` bits.",
        f"- Literal payload branching: `{s['literal_payload_log2_total']:.3f}` bits.",
        f"- Combined decoder ambiguity lower bound after skeleton: `{s['combined_decoder_ambiguity_log2_lower_bound']:.3f}` bits.",
        f"- Equivalent lower-bound decimal choices: `10^{s['combined_decoder_ambiguity_log10_lower_bound']:.3f}`.",
        f"- Copy events with unique target-oracle source: `{s['target_oracle_unique_source_count']}/{s['copy_count']}`.",
        f"- Target-oracle source-choice residual: `{s['target_oracle_matching_source_log2_total']:.3f}` bits.",
        "",
        "The exact skeleton is therefore a stable atlas, not a decoder-side",
        "generator. The target-oracle matching-source count is diagnostic only:",
        "it grants the future copied chunk and cannot be used as a generation",
        "rule without reintroducing target-text oracle access.",
        "",
        "## Decision",
        "",
        "- No skeleton decoder generator is promoted.",
        "- Copy-source choices remain a declared dependency.",
        "- Literal payload remains a declared dependency.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Skeleton decoder ambiguity gate](test_results/01_skeleton_decoder_ambiguity_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
