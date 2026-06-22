from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_chunk_signature_gate.json"
OUT = REPORTS / "final_target_chunk_signature_audit.md"


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
    assert_boundary("target_chunk_signature_gate", gate)
    s = gate["summary"]
    classification = "TARGET_CHUNK_SIGNATURE_GENERATOR_REJECTED"
    lines = [
        "# Final Target Chunk Signature Audit",
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
        "After rejecting an exact target-chunk dictionary, can the missing",
        "target-stream be reduced to a compact coarse-signature layer rather",
        "than exact copied/literal payload?",
        "",
        "## Result",
        "",
        f"- Operation chunks: `{s['operation_chunk_count']}` (`{s['copy_chunk_count']}` copy, `{s['literal_chunk_count']}` literal).",
        f"- Target-stream digits: `{s['target_stream_digit_count']}`.",
        f"- Exact unique chunks from the dictionary audit: `{s['exact_chunk_unique_count']}/{s['operation_chunk_count']}` (`{s['exact_chunk_unique_fraction']:.3f}`).",
        f"- Best non-payload signature family: `{s['best_non_payload_family']}`.",
        f"- Best non-payload signatures/singletons/selector bits: `{s['best_non_payload_signature_count']}` / `{s['best_non_payload_singleton_rows']}` / `{s['best_non_payload_selector_bits']:.3f}`.",
        f"- Least-unique payload family: `{s['least_unique_payload_family']}` with `{s['least_unique_payload_signature_count']}` signatures and `{s['least_unique_payload_selector_bits']:.3f}` selector bits.",
        f"- Most-exact payload family: `{s['most_exact_payload_family']}` with `{s['most_exact_payload_singleton_rows']}` singleton rows over `{s['most_exact_payload_signature_count']}` signatures.",
        "",
        "The non-payload signatures are too coarse: they reduce labels only by",
        "leaving the exact target digits unresolved. Payload-derived signatures",
        "become specific, but that specificity comes from first/last digits,",
        "checksums, support sets, or histograms already read from the target",
        "chunk. Same-length random controls show no promotable special structure.",
        "",
        "## Decision",
        "",
        "- No target-chunk signature generator is promoted.",
        "- The target-stream blocker remains open.",
        "- This is a falsification of a shallow latent-signature shortcut, not a new compression result.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target chunk signature gate](test_results/01_target_chunk_signature_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
