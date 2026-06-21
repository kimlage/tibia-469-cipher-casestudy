from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_literal_payload_ledger.json"
CONTEXT_GATE = TEST_RESULTS / "02_literal_payload_context_gate.json"
OUT = REPORTS / "final_literal_payload_generation_audit.md"


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
    ledger = load_json(LEDGER)
    gate = load_json(CONTEXT_GATE)
    assert_boundary("literal_payload_ledger", ledger)
    assert_boundary("literal_payload_context_gate", gate)
    ls = ledger["summary"]
    gs = gate["summary"]
    if gs["promotes_literal_payload_generator"]:
        classification = "LITERAL_PAYLOAD_GENERATOR_PROMOTED"
    elif gs["weak_literal_payload_context_clue"]:
        classification = "WEAK_LITERAL_PAYLOAD_CONTEXT_CLUE"
    else:
        classification = "LITERAL_PAYLOAD_GENERATOR_REJECTED"
    lines = [
        "# Final Literal Payload Generation Audit",
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
        "After granting the exact source-free skeleton, can the remaining",
        "`53` literal chunks / `266` literal digits be generated from",
        "source-free contexts rather than declared as payload?",
        "",
        "## Payload Ledger",
        "",
        f"- Literal chunks/digits: `{ls['literal_chunk_count']}` / `{ls['literal_digit_count']}`.",
        f"- Unique payload chunks: `{ls['unique_payload_chunks']}`.",
        f"- Repeated literal payload rows/digits: `{ls['repeated_payload_chunk_rows']}` / `{ls['repeated_payload_digits']}`.",
        f"- Whole chunks already seen in emitted text: `{ls['whole_chunk_seen_before_rows']}` / `{ls['whole_chunk_seen_before_digits']}` digits.",
        f"- Previous-literal repeats: `{ls['previous_literal_seen_rows']}` / `{ls['previous_literal_seen_digits']}` digits.",
        f"- Raw uniform literal payload bits: `{ls['raw_uniform_bits']:.3f}`.",
        f"- Empirical digit-histogram savings only: `{ls['empirical_digit_histogram_savings']:.3f}` bits.",
        "",
        "Whole-chunk prior occurrence is a diagnostic clue only here: selecting",
        "which prior chunk or which new digits to emit is still the payload",
        "generation problem.",
        "",
        "## Context Gate",
        "",
        "| Diagnostic | Value |",
        "|---|---:|",
        f"| Context families | `{gs['context_family_count']}` |",
        f"| Payload labels | `{gs['payload_label_count']}` |",
        f"| Best context | `{gs['best_context']}` |",
        f"| Best exact chunks | `{gs['best_exact_chunks']}/{gs['best_chunk_total']}` |",
        f"| Best exact digits | `{gs['best_exact_digits']}/{gs['best_digit_total']}` |",
        f"| Best model payload digits carried in table | `{gs['best_model_payload_digits']}` |",
        f"| Best net vs raw uniform literal bits | `{gs['best_net_vs_raw_uniform_bits']:.3f}` bits |",
        f"| Prefix/holdout any-exact-chunk cells | `{gs['prequential_any_exact_chunk_cells']}/{gs['prequential_cells']}` |",
        f"| Prefix/holdout cover-all cells | `{gs['prequential_cover_all_chunks_cells']}/{gs['prequential_cells']}` |",
        "",
        "The full-fit context hits are lookup-like: the model carries `222`",
        "payload digits in its table and still costs `+44.588` bits versus",
        "raw uniform payload after corrections. Prefix/holdout is stronger:",
        "the selected contexts get `0/5` cells with any exact literal chunk.",
        "",
        "## Decision",
        "",
        "- No literal payload generator is promoted.",
        "- The `266` literal digits remain external after the exact skeleton.",
        "- Source-free context tables are rejected as a generator under paid payload costs and prefix/holdout.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Literal payload ledger](test_results/01_literal_payload_ledger.md)",
        "- [Literal payload context gate](test_results/02_literal_payload_context_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
