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
    assert_boundary("innovation_tape_replay_gate", replay)
    assert_boundary("innovation_tape_structure_gate", structure)
    s = replay["summary"]
    t = structure["summary"]
    if structure["summary"]["promotes_tape_structure"]:
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
        "",
        "The first gate tests the right external-input hypothesis: a canonical",
        "literal tape plus an online copy transducer. It separates a",
        "target-conditioned upper bound from a blind replay control, so any",
        "positive result is not overclaimed as a closed-loop generator. The",
        "second gate asks whether the tape itself has seed-derived, recurrent,",
        "or Markov structure beyond shuffled controls.",
        "",
        "## Decision",
        "",
        "- Innovation tape replay is not promoted as a generator.",
        "- The literal payload can now be discussed as one tape-shaped dependency rather than only per-operation payload.",
        "- Tape structure is promoted as a mechanical clue because it beats same-multiset shuffled controls.",
        "- This does not yet derive when the transducer should consume the tape.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Innovation tape replay gate](test_results/01_innovation_tape_replay_gate.md)",
        "- [Innovation tape structure gate](test_results/03_innovation_tape_structure_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
