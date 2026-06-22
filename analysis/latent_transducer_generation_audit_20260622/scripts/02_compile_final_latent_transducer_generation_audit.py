from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BEAM_GATE = TEST_RESULTS / "01_latent_transducer_beam_gate.json"
CLOSED_LOOP_GATE = TEST_RESULTS / "03_closed_loop_digit_survival_gate.json"
RESCUE_LEDGER = TEST_RESULTS / "04_closed_loop_rescue_ledger.json"
OUT = REPORTS / "final_latent_transducer_generation_audit.md"


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
    beam_gate = load_json(BEAM_GATE)
    closed_loop_gate = load_json(CLOSED_LOOP_GATE)
    rescue_ledger = load_json(RESCUE_LEDGER)
    assert_boundary("latent_transducer_beam_gate", beam_gate)
    assert_boundary("closed_loop_digit_survival_gate", closed_loop_gate)
    assert_boundary("closed_loop_rescue_ledger", rescue_ledger)
    s = beam_gate["summary"]
    c = closed_loop_gate["summary"]
    r = rescue_ledger["summary"]
    if rescue_ledger["classification"] == "closed_loop_rescue_high_external_control":
        classification = "latent_transducer_closed_loop_high_external_control"
    else:
        classification = beam_gate["classification"]
    lines = [
        "# Final Latent Transducer Generation Audit",
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
        "Can a prefix-trained joint transducer choose literal spans, copy spans,",
        "boundaries, and copy sources together, instead of relying on the fixed",
        "261-operation skeleton atlas?",
        "",
        "## Result",
        "",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Aggregate exact books: `{s['aggregate_exact_books']}`.",
        f"- Aggregate nontrivial exact books: `{s['aggregate_nontrivial_exact_books']}`.",
        f"- Aggregate cutpoint hits: `{s['aggregate_cutpoint_hits']}/{s['aggregate_canonical_cutpoints']}`.",
        f"- Cells beating random cutpoint p95: `{s['cells_beating_random_cutpoint_p95']}/{s['cutoff_count']}`.",
        f"- Aggregate source+length hits: `{s['aggregate_source_length_hits']}/{s['aggregate_canonical_copy_ops']}`.",
        f"- Aggregate cutpoint atlas bits: `{s['aggregate_cutpoint_atlas_bits']:.3f}`.",
        f"- Aggregate cutpoint correction bits: `{s['aggregate_cutpoint_correction_bits']:.3f}`.",
        f"- Aggregate cutpoint saving vs atlas: `{s['aggregate_cutpoint_saving_vs_atlas_bits']:.3f}`.",
        f"- Predicted literal digits: `{s['aggregate_predicted_literal_digits']}`.",
        f"- Canonical literal digits: `{s['aggregate_canonical_literal_digits']}`.",
        f"- Closed-loop top-1 exact books: `{c['top1_exact_books']}/{c['tested_book_instances']}`.",
        f"- Closed-loop exact books surviving finished beam: `{c['exact_in_finished_beam_books']}/{c['tested_book_instances']}`.",
        f"- Closed-loop true-prefix survival books: `{c['true_prefix_survival_books']}/{c['tested_book_instances']}`.",
        f"- Closed-loop mean true-prefix max fraction: `{c['mean_true_prefix_max_fraction']:.6f}`.",
        f"- Rescue ledger sampled book instances: `{r['tested_book_instances']}`.",
        f"- Rescue ledger forced exact books: `{r['forced_exact_books']}`.",
        f"- Rescue ledger books needing no rescue: `{r['books_without_rescue']}`.",
        f"- Rescue ledger total rescue events: `{r['total_rescue_events']}`.",
        f"- Rescue ledger total rescue bits: `{r['total_rescue_bits']:.3f}`.",
        f"- Rescue ledger rescue/raw ratio: `{r['rescue_bits_fraction_of_raw']:.6f}`.",
        f"- Rescue ledger max true-prefix rank: `{r['max_true_rank']}`.",
        f"- Rescue ledger low external-control regime: `{r['low_external_control_regime']}`.",
        "",
        "The new route tests the right object: a single parser where literal, copy,",
        "length, source, and boundary decisions compete in one beam. But this first",
        "gate is still teacher-forced by the target digit stream and does not",
        "promote a closed-loop generator unless it produces nontrivial exact books",
        "under holdout. A second survival gate removes within-book target teacher",
        "forcing while still granting book length and true prior material; the",
        "true stream does not survive as a closed-loop generator. A sampled rescue",
        "ledger then measures how much oracle steering would be needed to keep the",
        "true prefix alive. The answer is not small: on first/middle/last suffix",
        "books per cutoff, every instance needs rescues and the rescue ledger costs",
        "more than raw digit emission. The closed-loop blocker is therefore a",
        "substantial missing state/control problem, not a near-miss beam-width",
        "artifact.",
        "",
        "## Decision",
        "",
        "- The route changes from local endpoint/source selectors to a joint latent-transducer audit.",
        "- The first beam gate is a parser/generator prototype, not a promoted formula.",
        "- Closed-loop digit survival is rejected under the current beam.",
        "- The rescue ledger is high external-control, so oracle steering is not promoted as a compact latent state.",
        "- Promotion requires nontrivial exact holdout books and paid correction reduction.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Latent transducer beam gate](test_results/01_latent_transducer_beam_gate.md)",
        "- [Closed loop digit survival gate](test_results/03_closed_loop_digit_survival_gate.md)",
        "- [Closed loop rescue ledger](test_results/04_closed_loop_rescue_ledger.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
