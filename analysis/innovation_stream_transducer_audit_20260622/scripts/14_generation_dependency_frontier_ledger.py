from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)

GATES = {
    "replay": TEST_RESULTS / "01_innovation_tape_replay_gate.json",
    "structure": TEST_RESULTS / "03_innovation_tape_structure_gate.json",
    "sync": TEST_RESULTS / "04_tape_synchronized_closed_loop_gate.json",
    "seed_subcodec": TEST_RESULTS / "05_seed_derived_tape_subcodec_gate.json",
    "seed_walk": TEST_RESULTS / "06_seed_walk_source_model_gate.json",
    "schedule": TEST_RESULTS / "07_innovation_tape_schedule_gate.json",
    "known_start_trigger": TEST_RESULTS / "08_tape_trigger_policy_gate.json",
    "decoder_visible_trigger": TEST_RESULTS / "09_decoder_visible_trigger_policy_gate.json",
    "boundary_candidate_trigger": TEST_RESULTS / "10_boundary_candidate_trigger_gate.json",
    "decoder_visible_boundary_candidate": TEST_RESULTS / "11_decoder_visible_boundary_candidate_trigger_gate.json",
    "internal_boundary_candidate": TEST_RESULTS / "12_internal_boundary_candidate_trigger_decomposition_gate.json",
    "book_start_mode": TEST_RESULTS / "13_book_start_mode_gate.json",
}

OUT_STEM = "14_generation_dependency_frontier_ledger"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def canonical_counts(ops_by_book: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    op_count = 0
    copy_ops = 0
    literal_ops = 0
    literal_digits = 0
    book_start_modes = Counter()
    internal_ops = 0
    for book in range(10, 70):
        ops = ops_by_book[str(book)]
        book_start_modes[ops[0]["type"]] += 1
        for op in ops:
            op_count += 1
            if int(op["target_start"]) != 0:
                internal_ops += 1
            if op["type"] == "copy":
                copy_ops += 1
            else:
                literal_ops += 1
                literal_digits += int(op["length"])
    return {
        "derived_books": 60,
        "seed_books": 10,
        "canonical_ops": op_count,
        "copy_ops": copy_ops,
        "literal_ops": literal_ops,
        "literal_digits": literal_digits,
        "book_start_ops": 60,
        "internal_ops": internal_ops,
        "book_start_literal_ops": book_start_modes["literal"],
        "book_start_copy_ops": book_start_modes["copy"],
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    gates = {name: load_json(path) for name, path in GATES.items()}
    for name, data in gates.items():
        assert_boundary(name, data)
    counts = canonical_counts(ledger["canonical_ops_by_book"])
    replay = gates["replay"]["summary"]
    structure = gates["structure"]["summary"]
    sync = gates["sync"]["summary"]
    seed_subcodec = gates["seed_subcodec"]["summary"]
    seed_walk = gates["seed_walk"]["summary"]
    schedule = gates["schedule"]["summary"]
    known_trigger = gates["known_start_trigger"]["summary"]
    decoder_trigger = gates["decoder_visible_trigger"]["summary"]
    candidate_trigger = gates["boundary_candidate_trigger"]["summary"]
    decoder_candidate = gates["decoder_visible_boundary_candidate"]["summary"]
    internal_candidate = gates["internal_boundary_candidate"]["summary"]
    book_start_mode = gates["book_start_mode"]["summary"]

    remaining_internal_starts = counts["internal_ops"]
    candidate_internal_hits = candidate_trigger["candidate_actual_starts"] - counts["book_start_ops"]
    candidate_missed_internal_starts = remaining_internal_starts - candidate_internal_hits

    frontier_items = [
        {
            "dependency": "row0_table",
            "status": "external_unchanged",
            "evidence": "All innovation-stream gates preserve row0_origin_status=unchanged_exogenous.",
            "remaining": "full row0 origin remains outside this generation route",
        },
        {
            "dependency": "seed_books_0_9_payload",
            "status": "external_seed_material",
            "evidence": "The innovation tape route generates only derived books 10..69 from granted seed material.",
            "remaining": "seed payload not derived here",
        },
        {
            "dependency": "literal_innovation_tape",
            "status": "tape_shaped_clue_promoted_not_generated",
            "evidence": (
                f"{counts['literal_digits']} literal digits; tape structure promoted, "
                f"Markov bits {structure['best_markov_bits']:.3f}; seed subcodec remains "
                f"{seed_subcodec['best_saving_vs_raw_bits']:.3f} bits vs raw tape."
            ),
            "remaining": "raw tape payload and its origin/order still external",
        },
        {
            "dependency": "tape_consumption_schedule",
            "status": "sparsity_weak_not_policy",
            "evidence": (
                f"schedule best feature {schedule['best_feature']}; feature delta "
                f"{schedule['best_feature_delta_bits']:.3f} bits; promotes={schedule['promotes_schedule_model']}."
            ),
            "remaining": "when to consume tape vs copy remains unresolved",
        },
        {
            "dependency": "book_start_existence",
            "status": "structural_clue_retained",
            "evidence": (
                f"right_ge:4 candidate labels recover {decoder_candidate['best_feature_start_hits']}/"
                f"{decoder_candidate['best_feature_actual_starts']} starts with decoder-visible book_start feature."
            ),
            "remaining": "only the existence of a first operation is explained",
        },
        {
            "dependency": "book_start_mode",
            "status": "rejected_policy_external",
            "evidence": (
                f"{book_start_mode['book_start_literals']}/{book_start_mode['book_start_copies']} "
                f"literal/copy starts; best non-global delta {book_start_mode['best_feature_delta_bits_vs_global']:.3f} bits."
            ),
            "remaining": "literal/copy mode at book start remains declared",
        },
        {
            "dependency": "internal_operation_starts",
            "status": "blocked_rejected_current_route",
            "evidence": (
                f"{remaining_internal_starts} internal canonical ops; right_ge:4 includes "
                f"{candidate_internal_hits} and misses {candidate_missed_internal_starts}; "
                f"internal candidate trigger hits {internal_candidate['best_feature_start_hits']}/"
                f"{internal_candidate['best_feature_actual_starts']} even with target-conditioned copy availability."
            ),
            "remaining": "internal op-start parser remains the main blocker",
        },
        {
            "dependency": "target_conditioned_copy_availability",
            "status": "conditional_clue_not_closed_loop",
            "evidence": (
                f"known-start trigger delta {known_trigger['best_feature_delta_bits_vs_global']:.3f} bits; "
                f"decoder-visible trigger delta {decoder_trigger['best_feature_delta_bits_vs_global']:.3f} bits."
            ),
            "remaining": "copy availability still relies on target future where promoted",
        },
        {
            "dependency": "copy_source_and_length",
            "status": "external_fields_after_shape",
            "evidence": (
                f"copy ops {counts['copy_ops']}; replay source+length hits "
                f"{replay['best_source_length_hits']}/{replay['best_canonical_copy_ops']} under target-conditioned replay."
            ),
            "remaining": "source and length fields are not generated",
        },
        {
            "dependency": "closed_loop_generation",
            "status": "not_promoted",
            "evidence": (
                f"sync exact books {sync['exact_in_finished_beam_books']}/{sync['book_count']}; "
                f"target-conditioned replay exact books {replay['best_exact_books']}/60 with shuffled p95 "
                f"{replay['best_shuffle_exact_book_p95']}."
            ),
            "remaining": "no closed-loop generated derived book set",
        },
    ]

    summary = {
        **counts,
        "classification": "GENERATION_FRONTIER_INTERNAL_STARTS_MAIN_BLOCKER",
        "compression_bound_status": "unchanged_8154_676268",
        "row0_origin_status": "unchanged_exogenous",
        "tape_structure_promoted": structure["promotes_tape_structure"],
        "closed_loop_exact_books": sync["exact_in_finished_beam_books"],
        "target_conditioned_replay_exact_books": replay["best_exact_books"],
        "right_ge4_candidate_positions": candidate_trigger["candidate_count"],
        "right_ge4_candidate_actual_starts": candidate_trigger["candidate_actual_starts"],
        "right_ge4_candidate_nonstarts": candidate_trigger["candidate_nonstarts"],
        "right_ge4_missed_internal_starts": candidate_missed_internal_starts,
        "internal_trigger_promoted": internal_candidate["promotes_internal_boundary_candidate_trigger"],
        "book_start_mode_promoted": book_start_mode["promotes_book_start_mode"],
        "next_aligned_route": (
            "derive internal operation starts without target-future oracle; book-start and "
            "tape-shape clues are useful but do not yet form a generator"
        ),
    }
    return {
        "schema": "generation_dependency_frontier_ledger_v1",
        "scope": "analysis_only_generation_frontier_after_innovation_stream_gates",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            **{name: rel(path) for name, path in GATES.items()},
        },
        "summary": summary,
        "frontier_items": frontier_items,
        "classification": summary["classification"],
        "decision": {
            "generator_status": "not_promoted",
            "main_blocker": "internal_operation_starts",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Generation Dependency Frontier Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Consolidate the post-gate dependency frontier after the innovation-stream",
        "transducer tests. This is a bookkeeping audit, not a compression sweep.",
        "",
        "## Summary",
        "",
        f"- Derived/seed books: `{s['derived_books']}` / `{s['seed_books']}`.",
        f"- Canonical ops/copy/literal: `{s['canonical_ops']}` / `{s['copy_ops']}` / `{s['literal_ops']}`.",
        f"- Literal tape digits: `{s['literal_digits']}`.",
        f"- Book-start/internal ops: `{s['book_start_ops']}` / `{s['internal_ops']}`.",
        f"- Book-start literal/copy modes: `{s['book_start_literal_ops']}` / `{s['book_start_copy_ops']}`.",
        f"- Right_ge:4 candidates/actual/nonstarts: `{s['right_ge4_candidate_positions']}` / `{s['right_ge4_candidate_actual_starts']}` / `{s['right_ge4_candidate_nonstarts']}`.",
        f"- Right_ge:4 missed internal starts: `{s['right_ge4_missed_internal_starts']}`.",
        f"- Tape structure promoted: `{s['tape_structure_promoted']}`.",
        f"- Closed-loop exact books: `{s['closed_loop_exact_books']}`.",
        f"- Target-conditioned replay exact books: `{s['target_conditioned_replay_exact_books']}`.",
        f"- Internal trigger promoted: `{s['internal_trigger_promoted']}`.",
        f"- Book-start mode promoted: `{s['book_start_mode_promoted']}`.",
        f"- Next aligned route: `{s['next_aligned_route']}`.",
        "",
        "## Frontier Items",
        "",
        "| Dependency | Status | Evidence | Remaining |",
        "| --- | --- | --- | --- |",
    ]
    for item in result["frontier_items"]:
        lines.append(
            f"| `{item['dependency']}` | `{item['status']}` | "
            f"{item['evidence']} | {item['remaining']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- No generator is promoted by this ledger.",
            "- The current main blocker is internal operation-start generation.",
            "- Book-start existence and tape-shaped payload are useful clues, but neither derives the internal skeleton.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
