from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_literal_payload_reference_subcodec_gate.json"
OUT = REPORTS / "final_literal_payload_reference_subcodec_audit.md"


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
    assert_boundary("literal_payload_reference_subcodec_gate", gate)
    s = gate["summary"]
    c = gate["controls"]
    classification = (
        "LITERAL_PAYLOAD_REFERENCE_SUBCODEC_PROMOTED"
        if s["promotes_literal_payload_reference_subcodec"]
        else "LITERAL_PAYLOAD_REFERENCE_SUBCODEC_REJECTED"
    )
    lines = [
        "# Final Literal Payload Reference Subcodec Audit",
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
        "Can literal payload chunks that already occurred in emitted text be",
        "replaced by a declared-reference subcodec after paying mode/source cost?",
        "",
        "## Result",
        "",
        f"- Literal chunks/digits: `{s['literal_chunk_count']}` / `{s['literal_digit_count']}`.",
        f"- Chunks with prior occurrence: `{s['prior_occurrence_rows']}`.",
        f"- Prior-occurrence digits: `{s['prior_occurrence_digits']}`.",
        f"- Raw uniform payload bits: `{s['raw_bits']:.3f}`.",
        f"- Beneficial references before mode cost: `{s['beneficial_reference_count_without_mode']}` chunks / `{s['beneficial_reference_digits_without_mode']}` digits.",
        f"- No-mode reference delta: `{s['no_mode_delta_vs_raw_bits']:.3f}` bits.",
        f"- Charged reference delta: `{s['charged_delta_vs_raw_bits']:.3f}` bits.",
        f"- Charged selected references: `{s['charged_selected_reference_count']}` chunks / `{s['charged_selected_reference_digits']}` digits.",
        f"- Random charged delta mean/p05/p95: `{c['delta_mean']:.3f}` / `{c['delta_p05']:.3f}` / `{c['delta_p95']:.3f}`.",
        "",
        "The recurrence is real but not usable as a promoted subcodec under this",
        "paid model: the apparent no-mode saving disappears once literal chunks",
        "need mode decisions and source addresses.",
        "",
        "## Decision",
        "",
        "- No literal-payload reference subcodec is promoted.",
        "- Whole-chunk recurrence remains a diagnostic clue only.",
        "- Literal payload remains a declared dependency.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Literal payload reference subcodec gate](test_results/01_literal_payload_reference_subcodec_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
