from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_chunk_dictionary_gate.json"
OUT = REPORTS / "final_target_chunk_dictionary_audit.md"


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
    assert_boundary("target_chunk_dictionary_gate", gate)
    s = gate["summary"]
    classification = (
        "TARGET_CHUNK_DICTIONARY_PROMOTED"
        if s["promotes_target_chunk_dictionary"]
        else "TARGET_CHUNK_DICTIONARY_REJECTED"
    )
    lines = [
        "# Final Target Chunk Dictionary Audit",
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
        "Can the missing target-stream be represented as a compact dictionary",
        "of exact operation chunks after the exact skeleton is granted?",
        "",
        "## Result",
        "",
        f"- Operation chunks: `{s['operation_chunk_count']}` (`{s['copy_chunk_count']}` copy, `{s['literal_chunk_count']}` literal).",
        f"- Copy/literal digits: `{s['copy_digit_count']}` / `{s['literal_digit_count']}`.",
        f"- Unique chunks overall: `{s['all_unique_chunks']}/{s['operation_chunk_count']}` (`{s['all_unique_fraction']:.3f}`).",
        f"- Unique copy chunks: `{s['copy_unique_chunks']}/{s['copy_chunk_count']}` (`{s['copy_unique_fraction']:.3f}`).",
        f"- Unique literal chunks: `{s['literal_unique_chunks']}/{s['literal_chunk_count']}` (`{s['literal_unique_fraction']:.3f}`).",
        f"- Repeated chunks/rows/digits overall: `{s['all_repeated_chunks']}` / `{s['all_repeated_rows']}` / `{s['all_repeated_digits']}`.",
        f"- Target-conditioned baseline bits: `{s['target_conditioned_baseline_bits']:.3f}`.",
        f"- All-chunk dictionary bits: `{s['all_chunk_dictionary_bits']:.3f}`.",
        f"- Dictionary delta vs baseline: `{s['all_chunk_dictionary_delta_vs_baseline']:.3f}` bits.",
        f"- Repeated-only dictionary delta vs raw target stream: `{s['all_chunk_repeated_only_delta_vs_raw_stream']:.3f}` bits.",
        "",
        "Exact copied chunks are almost all unique. The repeated-only view shows",
        "there is some recurrence, but a full exact-chunk dictionary mostly turns",
        "the target stream into raw copied payload declarations. This rejects the",
        "simplest dictionary account while leaving richer latent/state mechanisms open.",
        "",
        "## Decision",
        "",
        "- No target-chunk dictionary generator is promoted.",
        "- The target-stream blocker is not solved by a small exact-chunk library.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target chunk dictionary gate](test_results/01_target_chunk_dictionary_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
