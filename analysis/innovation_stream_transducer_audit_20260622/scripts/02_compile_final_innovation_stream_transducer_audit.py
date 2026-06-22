from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

REPLAY_GATE = TEST_RESULTS / "01_innovation_tape_replay_gate.json"
STRUCTURE_GATE = TEST_RESULTS / "03_innovation_tape_structure_gate.json"
SYNC_GATE = TEST_RESULTS / "04_tape_synchronized_closed_loop_gate.json"
SEED_SUBCODEC_GATE = TEST_RESULTS / "05_seed_derived_tape_subcodec_gate.json"
SEED_WALK_GATE = TEST_RESULTS / "06_seed_walk_source_model_gate.json"
SCHEDULE_GATE = TEST_RESULTS / "07_innovation_tape_schedule_gate.json"
TRIGGER_GATE = TEST_RESULTS / "08_tape_trigger_policy_gate.json"
DECODER_VISIBLE_TRIGGER_GATE = TEST_RESULTS / "09_decoder_visible_trigger_policy_gate.json"
BOUNDARY_CANDIDATE_TRIGGER_GATE = TEST_RESULTS / "10_boundary_candidate_trigger_gate.json"
DECODER_VISIBLE_BOUNDARY_CANDIDATE_TRIGGER_GATE = (
    TEST_RESULTS / "11_decoder_visible_boundary_candidate_trigger_gate.json"
)
INTERNAL_BOUNDARY_CANDIDATE_TRIGGER_GATE = (
    TEST_RESULTS / "12_internal_boundary_candidate_trigger_decomposition_gate.json"
)
BOOK_START_MODE_GATE = TEST_RESULTS / "13_book_start_mode_gate.json"
FRONTIER_LEDGER = TEST_RESULTS / "14_generation_dependency_frontier_ledger.json"
LENGTH_CONTROL_GATE = TEST_RESULTS / "15_length_control_tape_gate.json"
OUT = REPORTS / "final_innovation_stream_transducer_audit.md"


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
    replay = load_json(REPLAY_GATE)
    structure = load_json(STRUCTURE_GATE)
    sync = load_json(SYNC_GATE)
    seed_subcodec = load_json(SEED_SUBCODEC_GATE)
    seed_walk = load_json(SEED_WALK_GATE)
    schedule = load_json(SCHEDULE_GATE)
    trigger = load_json(TRIGGER_GATE)
    decoder_visible_trigger = load_json(DECODER_VISIBLE_TRIGGER_GATE)
    boundary_candidate_trigger = load_json(BOUNDARY_CANDIDATE_TRIGGER_GATE)
    decoder_visible_boundary_candidate_trigger = load_json(
        DECODER_VISIBLE_BOUNDARY_CANDIDATE_TRIGGER_GATE
    )
    internal_boundary_candidate_trigger = load_json(
        INTERNAL_BOUNDARY_CANDIDATE_TRIGGER_GATE
    )
    book_start_mode = load_json(BOOK_START_MODE_GATE)
    frontier = load_json(FRONTIER_LEDGER)
    length_control = load_json(LENGTH_CONTROL_GATE)
    assert_boundary("innovation_tape_replay_gate", replay)
    assert_boundary("innovation_tape_structure_gate", structure)
    assert_boundary("tape_synchronized_closed_loop_gate", sync)
    assert_boundary("seed_derived_tape_subcodec_gate", seed_subcodec)
    assert_boundary("seed_walk_source_model_gate", seed_walk)
    assert_boundary("innovation_tape_schedule_gate", schedule)
    assert_boundary("tape_trigger_policy_gate", trigger)
    assert_boundary("decoder_visible_trigger_policy_gate", decoder_visible_trigger)
    assert_boundary("boundary_candidate_trigger_gate", boundary_candidate_trigger)
    assert_boundary(
        "decoder_visible_boundary_candidate_trigger_gate",
        decoder_visible_boundary_candidate_trigger,
    )
    assert_boundary(
        "internal_boundary_candidate_trigger_decomposition_gate",
        internal_boundary_candidate_trigger,
    )
    assert_boundary("book_start_mode_gate", book_start_mode)
    assert_boundary("generation_dependency_frontier_ledger", frontier)
    assert_boundary("length_control_tape_gate", length_control)
    s = replay["summary"]
    t = structure["summary"]
    u = sync["summary"]
    v = seed_subcodec["summary"]
    w = seed_walk["summary"]
    x = schedule["summary"]
    y = trigger["summary"]
    z = decoder_visible_trigger["summary"]
    aa = boundary_candidate_trigger["summary"]
    ab = decoder_visible_boundary_candidate_trigger["summary"]
    ac = internal_boundary_candidate_trigger["summary"]
    ad = book_start_mode["summary"]
    ae = frontier["summary"]
    af = length_control["summary"]
    if (
        length_control["summary"]["promotes_predictive_length_control_clue"]
        and not length_control["summary"]["promotes_cutpoint_replacement"]
    ):
        classification = "INNOVATION_STREAM_LENGTH_CONTROL_CLUE_PROMOTED_CUTPOINT_REPLACEMENT_REJECTED"
    elif frontier["classification"] == "GENERATION_FRONTIER_INTERNAL_STARTS_MAIN_BLOCKER":
        classification = "INNOVATION_STREAM_FRONTIER_INTERNAL_STARTS_MAIN_BLOCKER"
    elif (
        not book_start_mode["summary"]["promotes_book_start_mode"]
        and not internal_boundary_candidate_trigger["summary"][
            "promotes_internal_boundary_candidate_trigger"
        ]
    ):
        classification = "INNOVATION_STREAM_BOOKSTART_MODE_REJECTED_INTERNAL_TRIGGER_REJECTED"
    elif (
        decoder_visible_boundary_candidate_trigger["summary"][
            "promotes_decoder_visible_boundary_candidate_trigger"
        ]
        and not internal_boundary_candidate_trigger["summary"][
            "promotes_internal_boundary_candidate_trigger"
        ]
    ):
        classification = "INNOVATION_STREAM_BOOKSTART_DOMINATED_INTERNAL_TRIGGER_REJECTED"
    elif decoder_visible_boundary_candidate_trigger["summary"][
        "promotes_decoder_visible_boundary_candidate_trigger"
    ]:
        classification = "INNOVATION_STREAM_DECODER_VISIBLE_BOOKSTART_TRIGGER_CLUE_PROMOTED_INTERNAL_REJECTED"
    elif boundary_candidate_trigger["summary"]["promotes_boundary_candidate_trigger"]:
        classification = "INNOVATION_STREAM_BOUNDARY_CANDIDATE_TRIGGER_CLUE_PROMOTED_GENERATOR_NOT_PROMOTED"
    elif trigger["summary"]["promotes_conditional_trigger_clue"]:
        classification = "INNOVATION_STREAM_CONDITIONAL_TRIGGER_CLUE_PROMOTED_TARGET_FREE_TRIGGER_REJECTED"
    elif trigger["summary"]["weak_conditional_trigger_clue"]:
        classification = "INNOVATION_STREAM_CONDITIONAL_TRIGGER_CLUE_WEAK"
    elif schedule["summary"]["promotes_schedule_model"]:
        classification = "INNOVATION_STREAM_TAPE_SCHEDULE_PROMOTED"
    elif schedule["summary"]["weak_schedule_clue"]:
        classification = "INNOVATION_STREAM_MIXED_TAPE_STRUCTURE_PROMOTED_SYNC_WEAK_SCHEDULE_SPARSITY_WEAK"
    elif seed_walk["summary"]["promotes_seed_walk_subcodec"]:
        classification = "INNOVATION_STREAM_SEED_WALK_SUBCODEC_PROMOTED"
    elif seed_subcodec["summary"]["promotes_seed_subcodec"]:
        classification = "INNOVATION_STREAM_SEED_TAPE_SUBCODEC_PROMOTED"
    elif seed_subcodec["summary"]["weak_seed_subcodec_clue"]:
        classification = "INNOVATION_STREAM_MIXED_TAPE_STRUCTURE_PROMOTED_SYNC_WEAK_SEED_SUBCODEC_WEAK"
    elif sync["summary"]["weak_tape_synchronization_clue"]:
        classification = "INNOVATION_STREAM_MIXED_TAPE_STRUCTURE_PROMOTED_SYNC_WEAK"
    elif structure["summary"]["promotes_tape_structure"]:
        classification = "INNOVATION_STREAM_MIXED_TAPE_STRUCTURE_PROMOTED"
    else:
        classification = replay["classification"]
    lines = [
        "# Final Innovation Stream Transducer Audit",
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
        "Can the fixed operation skeleton be replaced by an online copy transducer",
        "plus a small external innovation tape made from the literal payload?",
        "",
        "## Result",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Literal tape chunks: `{s['literal_tape_chunks']}`.",
        f"- Best threshold: `{s['best_threshold']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Best exact nontrivial books: `{s['best_exact_nontrivial_books']}`.",
        f"- Best cutpoint hits: `{s['best_cutpoint_hits']}/{s['best_canonical_cutpoints']}`.",
        f"- Best source+length hits: `{s['best_source_length_hits']}/{s['best_canonical_copy_ops']}`.",
        f"- Best shuffled-tape exact-book p95: `{s['best_shuffle_exact_book_p95']}`.",
        f"- Best blind replay exact books: `{s['best_blind_exact_books']}`.",
        f"- Best seed tape coverage: `{t['best_seed_covered_digits']}/{t['literal_tape_digits']}`.",
        f"- Best seed coverage control p95: `{t['best_seed_control_p95']:.3f}`.",
        f"- Best prior-tape coverage: `{t['best_prior_covered_digits']}/{t['literal_tape_digits']}`.",
        f"- Best Markov tape bits: `{t['best_markov_bits']:.3f}`.",
        f"- Promotes tape structure: `{t['promotes_tape_structure']}`.",
        f"- Tape-synchronized exact books in beam: `{u['exact_in_finished_beam_books']}/60`.",
        f"- Tape-synchronized exact-in-beam shuffled p95: `{u['exact_in_finished_beam_control_p95']}`.",
        f"- Tape-synchronized true-prefix survival: `{u['true_prefix_survival_books']}/60`.",
        f"- Tape-synchronized mean true-prefix max fraction: `{u['mean_true_prefix_max_fraction']:.6f}`.",
        f"- Seed-subcodec best saving vs raw tape: `{v['best_saving_vs_raw_bits']:.3f}` bits.",
        f"- Seed-subcodec best control saving p95: `{v['best_control_saving_p95']:.3f}` bits.",
        f"- Seed-subcodec copy digits: `{v['best_copy_digits']}/{v['literal_tape_digits']}`.",
        f"- Promotes seed subcodec: `{v['promotes_seed_subcodec']}`.",
        f"- Weak seed subcodec clue: `{v['weak_seed_subcodec_clue']}`.",
        f"- Seed-walk best total bits: `{w['best_walk_total_bits']:.3f}`.",
        f"- Seed-walk best saving vs absolute-source subcodec: `{w['best_walk_saving_vs_absolute_bits']:.3f}`.",
        f"- Seed-walk best saving vs raw tape: `{w['best_walk_saving_vs_raw_bits']:.3f}`.",
        f"- Promotes seed-walk subcodec: `{w['promotes_seed_walk_subcodec']}`.",
        f"- Weak seed-walk clue: `{w['weak_seed_walk_clue']}`.",
        f"- Tape schedule best feature: `{x['best_feature']}`.",
        f"- Tape schedule exact books: `{x['best_exact_books']}/{x['best_test_books']}`.",
        f"- Tape schedule saving vs count baseline: `{x['best_saving_vs_baseline_bits']:.3f}` bits.",
        f"- Tape schedule global-majority exact books: `{x['best_global_exact_books']}/{x['best_global_test_books']}`.",
        f"- Tape schedule global-majority saving: `{x['best_global_saving_vs_baseline_bits']:.3f}` bits.",
        f"- Tape schedule best feature delta bits: `{x['best_feature_delta_bits']:.3f}`.",
        f"- Tape schedule best feature delta exact: `{x['best_feature_delta_exact']}`.",
        f"- Tape schedule random exact p95: `{x['random_exact_p95']:.3f}`.",
        f"- Promotes tape schedule: `{x['promotes_schedule_model']}`.",
        f"- Trigger best feature: `{y['best_feature']}`.",
        f"- Trigger best feature exact ops: `{y['best_feature_exact_ops']}/{y['best_feature_test_ops']}`.",
        f"- Trigger best feature literal hits: `{y['best_feature_literal_hits']}/{y['best_feature_test_literal_ops']}`.",
        f"- Trigger best feature delta vs global: `{y['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Trigger best feature exact delta vs global: `{y['best_feature_delta_exact_vs_global']}`.",
        f"- Trigger forced literal ops with no copy available: `{y['forced_literal_ops_no_copy_available']}/{y['literal_ops']}`.",
        f"- Promotes conditional trigger clue: `{y['promotes_conditional_trigger_clue']}`.",
        f"- Decoder-visible trigger best feature: `{z['best_feature']}`.",
        f"- Decoder-visible trigger exact ops: `{z['best_feature_exact_ops']}/{z['best_feature_test_ops']}`.",
        f"- Decoder-visible trigger literal hits: `{z['best_feature_literal_hits']}/{z['best_feature_test_literal_ops']}`.",
        f"- Decoder-visible trigger delta vs global: `{z['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Target-conditioning gap bits: `{z['target_conditioning_gap_bits']:.3f}`.",
        f"- Promotes decoder-visible trigger: `{z['promotes_decoder_visible_trigger']}`.",
        f"- Boundary-candidate trigger feature: `{aa['best_feature']}`.",
        f"- Boundary-candidate trigger exact candidates: `{aa['best_feature_exact_candidates']}/{aa['best_feature_test_candidates']}`.",
        f"- Boundary-candidate trigger start hits: `{aa['best_feature_start_hits']}/{aa['best_feature_actual_starts']}`.",
        f"- Boundary-candidate trigger literal/copy hits: `{aa['best_feature_literal_hits']}/{aa['best_feature_copy_hits']}`.",
        f"- Boundary-candidate trigger delta vs same-cutoff global: `{aa['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Promotes boundary-candidate trigger: `{aa['promotes_boundary_candidate_trigger']}`.",
        f"- Decoder-visible boundary-candidate feature: `{ab['best_feature']}`.",
        f"- Decoder-visible boundary-candidate start hits: `{ab['best_feature_start_hits']}/{ab['best_feature_actual_starts']}`.",
        f"- Decoder-visible boundary-candidate delta vs global: `{ab['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Internal decoder-visible boundary-candidate start hits: `{ab['internal_best_feature_start_hits']}/{ab['internal_best_feature_actual_starts']}`.",
        f"- Promotes internal decoder-visible boundary-candidate trigger: `{ab['promotes_internal_decoder_visible_boundary_candidate_trigger']}`.",
        f"- Internal target-conditioned boundary-candidate start hits: `{ac['best_feature_start_hits']}/{ac['best_feature_actual_starts']}`.",
        f"- Internal target-conditioned boundary-candidate delta vs global: `{ac['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Promotes internal boundary-candidate trigger: `{ac['promotes_internal_boundary_candidate_trigger']}`.",
        f"- Book-start mode literal/copy counts: `{ad['book_start_literals']}/{ad['book_start_copies']}`.",
        f"- Book-start mode best feature: `{ad['best_feature']}`.",
        f"- Book-start mode best feature delta vs global: `{ad['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Promotes book-start mode: `{ad['promotes_book_start_mode']}`.",
        f"- Frontier main blocker: `{frontier['decision']['main_blocker']}`.",
        f"- Frontier internal ops: `{ae['internal_ops']}`.",
        f"- Frontier right_ge:4 missed internal starts: `{ae['right_ge4_missed_internal_starts']}`.",
        f"- Length-control unique lengths: `{af['unique_lengths']}`.",
        f"- Length-control raw composition bits with fixed op counts: `{af['raw_composition_bits_fixed_op_counts_all_books']:.3f}`.",
        f"- Length-control beats shuffled paid p95 cutoffs: `{af['beats_shuffle_paid_p95_cutoffs']}/{len(af['cutoffs_tested'])}`.",
        f"- Length-control type-granted best cutoffs: `{af['type_granted_best_cutoffs']}/{len(af['cutoffs_tested'])}`.",
        f"- Length-control beats fixed-op composition cutoffs: `{af['beats_fixed_op_composition_cutoffs']}/{len(af['cutoffs_tested'])}`.",
        f"- Promotes length-control clue: `{af['promotes_predictive_length_control_clue']}`.",
        f"- Promotes cutpoint replacement: `{af['promotes_cutpoint_replacement']}`.",
        "",
        "The first gate tests the right external-input hypothesis: a canonical",
        "literal tape plus an online copy transducer. It separates a",
        "target-conditioned upper bound from a blind replay control, so any",
        "positive result is not overclaimed as a closed-loop generator. The",
        "second gate asks whether the tape itself has seed-derived, recurrent,",
        "or Markov structure beyond shuffled controls. The synchronization gate",
        "then asks whether that structured tape is enough to drive a closed-loop",
        "copy transducer when only the tape start, book length, and prior material",
        "are granted. The seed-subcodec gate prices the seed-coverage clue as a",
        "real dependency reduction for the tape itself. The seed-walk gate then",
        "tests whether source addresses can be replaced by a cheaper source walk.",
        "The schedule gate asks whether per-book tape consumption can be predicted",
        "from online mechanical features beyond a global sparsity baseline. The",
        "trigger gate then moves one level down, asking whether literal-vs-copy",
        "can be predicted at known operation starts when true-prefix,",
        "target-conditioned copy availability is granted. The decoder-visible",
        "trigger gate removes that target-conditioned availability while still",
        "granting known operation starts and true tape state. The boundary",
        "candidate trigger gate then replaces exact operation starts with the",
        "previously promoted `right_ge:4` boundary candidate set and asks for",
        "three-way `nonstart/literal/copy` labels. The decoder-visible boundary",
        "candidate gate removes target-conditioned copy availability from that",
        "candidate-label problem and decomposes book-start versus internal starts.",
        "The internal decomposition gate then removes book-start candidates from",
        "the target-conditioned candidate-label problem itself. The book-start",
        "mode gate then asks whether the remaining first-operation literal/copy",
        "choice has a target-free rule beyond global majority. The frontier",
        "ledger consolidates the surviving dependencies after these gates. The",
        "length-control gate then tests a different constructive framing: if the",
        "operation lengths are treated as a control tape, internal starts follow",
        "by cumulative sum. That stream has prefix-holdout structure beyond",
        "shuffled controls, but the useful contexts usually require operation",
        "type and the paid model does not beat fixed-op-count cutpoint",
        "composition. It is therefore a clue about the control stream, not a",
        "replacement for the internal-start atlas.",
        "",
        "## Decision",
        "",
        "- Innovation tape replay is not promoted as a generator.",
        "- The literal payload can now be discussed as one tape-shaped dependency rather than only per-operation payload.",
        "- Tape structure is promoted as a mechanical clue because it beats same-multiset shuffled controls.",
        "- This does not yet derive when the transducer should consume the tape.",
        "- Tape-synchronized closed-loop generation is not promoted unless exact books survive above shuffled controls.",
        "- Tape synchronization is only a weak prefix-survival clue under the current beam.",
        "- Seed-derived tape subcodec is not promoted because paid references are still worse than raw tape.",
        "- Seed-derived tape subcodec remains a weak clue because paid coverage beats shuffled controls.",
        "- Seed-walk source model is rejected because deltas are more expensive than absolute source positions.",
        "- Tape schedule feature model is not promoted unless it improves over global-majority sparsity.",
        "- Tape schedule sparsity is retained only as a weak clue.",
        "- Conditional trigger policy is promoted as a dependency-reduction clue: copy availability explains many literal/copy decisions after paying table/correction cost.",
        "- The trigger clue is not a closed-loop generator because it still grants operation starts and target-conditioned copy availability.",
        "- Decoder-visible trigger policy is rejected: without target-conditioned copy availability, the trigger clue collapses to the copy-majority baseline.",
        "- Boundary-candidate trigger policy is promoted as a composed dependency-reduction clue, but still leaves missed operation starts and target-conditioned copy availability unresolved.",
        "- Decoder-visible boundary-candidate trigger policy is promoted only as a book-start clue; the internal-only trigger decomposition is not promoted.",
        "- Internal boundary-candidate trigger is rejected even with target-conditioned copy availability, so the composed candidate-trigger gain is book-start dominated.",
        "- Book-start mode policy is rejected: the existence of a first operation is structural, but its literal/copy mode remains declared.",
        "- The consolidated frontier identifies internal operation-start generation as the main blocker.",
        "- Length-control tape structure is promoted as a clue, but cutpoint replacement is rejected.",
        "- The length-control clue usually depends on the operation type stream, so it is not source-free skeleton generation.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Innovation tape replay gate](test_results/01_innovation_tape_replay_gate.md)",
        "- [Innovation tape structure gate](test_results/03_innovation_tape_structure_gate.md)",
        "- [Tape synchronized closed loop gate](test_results/04_tape_synchronized_closed_loop_gate.md)",
        "- [Seed derived tape subcodec gate](test_results/05_seed_derived_tape_subcodec_gate.md)",
        "- [Seed walk source model gate](test_results/06_seed_walk_source_model_gate.md)",
        "- [Innovation tape schedule gate](test_results/07_innovation_tape_schedule_gate.md)",
        "- [Tape trigger policy gate](test_results/08_tape_trigger_policy_gate.md)",
        "- [Decoder visible trigger policy gate](test_results/09_decoder_visible_trigger_policy_gate.md)",
        "- [Boundary candidate trigger gate](test_results/10_boundary_candidate_trigger_gate.md)",
        "- [Decoder visible boundary candidate trigger gate](test_results/11_decoder_visible_boundary_candidate_trigger_gate.md)",
        "- [Internal boundary candidate trigger decomposition gate](test_results/12_internal_boundary_candidate_trigger_decomposition_gate.md)",
        "- [Book start mode gate](test_results/13_book_start_mode_gate.md)",
        "- [Generation dependency frontier ledger](test_results/14_generation_dependency_frontier_ledger.md)",
        "- [Length control tape gate](test_results/15_length_control_tape_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
