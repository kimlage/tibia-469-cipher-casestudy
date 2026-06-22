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
RESCUE_SURFACE = TEST_RESULTS / "05_closed_loop_rescue_surface_audit.json"
COPY_DIAGNOSTIC = TEST_RESULTS / "06_copy_state_rescue_diagnostic.json"
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
    rescue_surface = load_json(RESCUE_SURFACE)
    copy_diagnostic = load_json(COPY_DIAGNOSTIC)
    assert_boundary("latent_transducer_beam_gate", beam_gate)
    assert_boundary("closed_loop_digit_survival_gate", closed_loop_gate)
    assert_boundary("closed_loop_rescue_ledger", rescue_ledger)
    assert_boundary("closed_loop_rescue_surface_audit", rescue_surface)
    assert_boundary("copy_state_rescue_diagnostic", copy_diagnostic)
    s = beam_gate["summary"]
    c = closed_loop_gate["summary"]
    r = rescue_ledger["summary"]
    rs = rescue_surface["summary"]
    ce = copy_diagnostic["event_summary"]
    cc = copy_diagnostic["copy_op_summary"]
    if rescue_ledger["classification"] == "closed_loop_rescue_high_external_control":
        classification = "latent_transducer_closed_loop_high_external_control_copy_pruning_mapped"
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
        f"- Rescue surface events classified: `{rs['event_count']}`.",
        f"- Rescue surface counts: `{rs['surface_counts']}`.",
        f"- Rescue surface copy/literal fraction: `{rs['copy_surface_fraction']:.6f}` / `{rs['literal_surface_fraction']:.6f}`.",
        f"- Rescue surface exact/near internal cutpoint fraction: `{rs['at_internal_cutpoint_fraction']:.6f}` / `{rs['near_internal_cutpoint_fraction']:.6f}`.",
        f"- Rescue surface operation-start fraction: `{rs['at_op_start_fraction']:.6f}`.",
        f"- Rescue surface early <=20% fraction: `{rs['early_20pct_fraction']:.6f}`.",
        f"- Copy-state diagnostic copy-surface last-kind counts: `{ce['copy_surface_last_kind_counts']}`.",
        f"- Copy-state diagnostic true-copy event fraction inside copy spans: `{ce['copy_surface_true_copy_event_fraction']:.6f}`.",
        f"- Copy-state diagnostic copy ops tested: `{cc['copy_ops_tested']}`.",
        f"- Copy-state diagnostic source-match ops: `{cc['source_match_ops']}/{cc['copy_ops_tested']}`.",
        f"- Copy-state diagnostic inventory/pruned prefix digit fraction: `{cc['inventory_prefix_digit_fraction']:.6f}` / `{cc['pruned_prefix_digit_fraction']:.6f}`.",
        f"- Copy-state diagnostic ops with any pruned prefix: `{cc['ops_with_any_pruned_prefix']}`.",
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
        "artifact. A surface audit maps those rescues back onto the canonical",
        "skeleton after decoding. The failures are not concentrated at visible",
        "boundaries: only `27/1732` are exact internal cutpoints and `82/1732`",
        "are within one digit of an internal cutpoint, while `1721/1732` fall",
        "inside canonical copy spans. That leaves the blocker at decoder-visible",
        "copy-state/content control, not a simple boundary trigger. A copy-state",
        "diagnostic then asks whether those failures come from absent source",
        "material or from candidate pruning/ranking. The answer is narrow but",
        "useful: inside copy spans, only `16/1721` rescue events arrive via a",
        "copy emission; `1705/1721` arrive by single literal steps. For the `32`",
        "sampled canonical copy ops, the source payload matches in `32/32` and",
        "some correct prefix exists in the raw inventory in `32/32`, covering",
        "`1063/1240` copy digits, but the pruned candidate set contains a correct",
        "prefix in `0/32`. The live blocker is therefore candidate pruning/ranking",
        "or copy-continuation state, not missing prior material.",
        "",
        "## Decision",
        "",
        "- The route changes from local endpoint/source selectors to a joint latent-transducer audit.",
        "- The first beam gate is a parser/generator prototype, not a promoted formula.",
        "- Closed-loop digit survival is rejected under the current beam.",
        "- The rescue ledger is high external-control, so oracle steering is not promoted as a compact latent state.",
        "- Rescue surface labels are diagnostic only; they do not produce a decoder-visible state.",
        "- Copy-state diagnostics identify a concrete next route: replace blind cheapest-chunk pruning with a decoder-visible copy-control state.",
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
        "- [Closed loop rescue surface audit](test_results/05_closed_loop_rescue_surface_audit.md)",
        "- [Copy state rescue diagnostic](test_results/06_copy_state_rescue_diagnostic.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
