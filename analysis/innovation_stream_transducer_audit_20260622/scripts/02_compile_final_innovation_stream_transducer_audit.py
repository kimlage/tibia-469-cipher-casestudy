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
    assert_boundary("innovation_tape_replay_gate", replay)
    assert_boundary("innovation_tape_structure_gate", structure)
    assert_boundary("tape_synchronized_closed_loop_gate", sync)
    assert_boundary("seed_derived_tape_subcodec_gate", seed_subcodec)
    assert_boundary("seed_walk_source_model_gate", seed_walk)
    s = replay["summary"]
    t = structure["summary"]
    u = sync["summary"]
    v = seed_subcodec["summary"]
    w = seed_walk["summary"]
    if seed_walk["summary"]["promotes_seed_walk_subcodec"]:
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
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
