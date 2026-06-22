from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
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
REPLAY_GATE = TEST_RESULTS / "01_innovation_tape_replay_gate.json"
STRUCTURE_GATE = TEST_RESULTS / "03_innovation_tape_structure_gate.json"

OUT_STEM = "04_tape_synchronized_closed_loop_gate"
SEED_BOOKS = list(range(10))
BEAM_WIDTH = 240
COPY_CANDIDATE_LIMIT = 80
COPY_LENGTHS = list(range(5, 41)) + [50, 60, 80, 120, 160]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 12


@dataclass(frozen=True)
class State:
    text: str
    tape_pos: int
    score: float
    op_count: int
    copy_count: int


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


def canonical_tape_and_starts(
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[int, int], dict[int, int]]:
    parts = []
    starts = {}
    counts = {}
    pos = 0
    for book in range(10, 70):
        starts[book] = pos
        count = 0
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                payload = op.get("payload", "")
                parts.append(payload)
                count += len(payload)
                pos += len(payload)
        counts[book] = count
    return "".join(parts), starts, counts


def source_chunks(source_text: str) -> dict[int, list[tuple[float, str]]]:
    by_length: dict[int, dict[str, float]] = {}
    for length in COPY_LENGTHS:
        if length > len(source_text):
            continue
        best: dict[str, float] = {}
        for start in range(0, len(source_text) - length + 1):
            chunk = source_text[start : start + length]
            score = 2.0 - math.log2(length) + 0.01 * math.log2(start + 1)
            prior = best.get(chunk)
            if prior is None or score < prior:
                best[chunk] = score
        by_length[length] = sorted((score, chunk) for chunk, score in best.items())
    return by_length


def copy_candidates(
    chunks_by_length: dict[int, list[tuple[float, str]]],
    remaining: int,
) -> list[tuple[float, str]]:
    rows = []
    for length, candidates in chunks_by_length.items():
        if length <= remaining:
            rows.extend(candidates[: max(1, COPY_CANDIDATE_LIMIT // 8)])
    rows.sort(key=lambda item: item[0])
    return rows[:COPY_CANDIDATE_LIMIT]


def prefix_match_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index
    return limit


def decode_book(
    chunks_by_length: dict[int, list[tuple[float, str]]],
    target: str,
    tape: str,
    tape_start: int,
) -> dict[str, Any]:
    target_len = len(target)
    beam = [State(text="", tape_pos=tape_start, score=0.0, op_count=0, copy_count=0)]
    finished: list[State] = []
    true_prefix_max_len = 0
    true_prefix_survives = False
    step_count = 0
    while beam and step_count < target_len + 20:
        step_count += 1
        expansions: dict[tuple[str, int], State] = {}
        for state in beam:
            if len(state.text) == target_len:
                finished.append(state)
                continue
            remaining = target_len - len(state.text)
            if state.tape_pos < len(tape):
                text = state.text + tape[state.tape_pos]
                candidate = State(
                    text=text,
                    tape_pos=state.tape_pos + 1,
                    score=state.score + 1.0,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count,
                )
                key = (candidate.text, candidate.tape_pos)
                prior = expansions.get(key)
                if prior is None or candidate.score < prior.score:
                    expansions[key] = candidate
            for copy_score, chunk in copy_candidates(chunks_by_length, remaining):
                text = state.text + chunk
                if len(text) > target_len:
                    continue
                candidate = State(
                    text=text,
                    tape_pos=state.tape_pos,
                    score=state.score + copy_score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count + 1,
                )
                key = (candidate.text, candidate.tape_pos)
                prior = expansions.get(key)
                if prior is None or candidate.score < prior.score:
                    expansions[key] = candidate
        if not expansions:
            break
        ranked = sorted(expansions.values(), key=lambda item: item.score)
        beam = ranked[:BEAM_WIDTH]
        prefix_states = [state for state in beam if target.startswith(state.text)]
        if prefix_states:
            true_prefix_survives = True
            true_prefix_max_len = max(true_prefix_max_len, max(len(state.text) for state in prefix_states))
        if all(len(state.text) == target_len for state in beam):
            finished.extend(beam)
            break
    finished = sorted(finished, key=lambda item: item.score)
    top = finished[0] if finished else min(beam, key=lambda item: item.score)
    exact_rank = None
    for rank, state in enumerate(finished[:BEAM_WIDTH], start=1):
        if state.text == target:
            exact_rank = rank
            break
    return {
        "top1_exact": top.text == target,
        "exact_in_finished_beam": exact_rank is not None,
        "exact_rank": exact_rank,
        "true_prefix_survives": true_prefix_survives,
        "true_prefix_max_len": true_prefix_max_len,
        "true_prefix_max_fraction": true_prefix_max_len / target_len,
        "top_prefix_match_len": prefix_match_len(top.text, target),
        "top_prefix_match_fraction": prefix_match_len(top.text, target) / target_len,
        "top_tape_digits_consumed": top.tape_pos - tape_start,
        "top_op_count": top.op_count,
        "top_copy_count": top.copy_count,
    }


def evaluate_all(
    books: dict[int, str],
    tape: str,
    tape_starts: dict[int, int],
    chunks_by_book: dict[int, dict[int, list[tuple[float, str]]]],
) -> dict[str, Any]:
    rows = []
    for book in range(10, 70):
        row = decode_book(chunks_by_book[book], books[book], tape, tape_starts[book])
        row["book"] = book
        rows.append(row)
    return summarize_rows(rows)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "book_count": len(rows),
        "top1_exact_books": sum(1 for row in rows if row["top1_exact"]),
        "exact_in_finished_beam_books": sum(
            1 for row in rows if row["exact_in_finished_beam"]
        ),
        "true_prefix_survival_books": sum(
            1 for row in rows if row["true_prefix_survives"]
        ),
        "mean_true_prefix_max_fraction": mean(
            row["true_prefix_max_fraction"] for row in rows
        ),
        "mean_top_prefix_match_fraction": mean(
            row["top_prefix_match_fraction"] for row in rows
        ),
        "mean_top_tape_digits_consumed": mean(
            row["top_tape_digits_consumed"] for row in rows
        ),
        "sample_rows": rows[:12],
    }


def shuffled_controls(
    books: dict[int, str],
    tape: str,
    tape_starts: dict[int, int],
    chunks_by_book: dict[int, dict[int, list[tuple[float, str]]]],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    chars = list(tape)
    exact_counts = []
    survival_counts = []
    max_fractions = []
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        shuffled = "".join(chars)
        row = evaluate_all(books, shuffled, tape_starts, chunks_by_book)
        exact_counts.append(row["exact_in_finished_beam_books"])
        survival_counts.append(row["true_prefix_survival_books"])
        max_fractions.append(row["mean_true_prefix_max_fraction"])
    exact_counts.sort()
    survival_counts.sort()
    max_fractions.sort()
    return {
        "trials": RANDOM_TRIALS,
        "exact_in_finished_beam_mean": mean(exact_counts),
        "exact_in_finished_beam_p95": percentile(exact_counts, 0.95),
        "true_prefix_survival_mean": mean(survival_counts),
        "true_prefix_survival_p95": percentile(survival_counts, 0.95),
        "mean_true_prefix_max_fraction_mean": mean(max_fractions),
        "mean_true_prefix_max_fraction_p95": percentile(max_fractions, 0.95),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    replay = load_json(REPLAY_GATE)
    structure = load_json(STRUCTURE_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("innovation_tape_replay_gate", replay)
    assert_boundary("innovation_tape_structure_gate", structure)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape, starts, counts = canonical_tape_and_starts(ledger["canonical_ops_by_book"])
    chunks_by_book = {
        book: source_chunks("".join(books[index] for index in range(book)))
        for book in range(10, 70)
    }
    observed = evaluate_all(books, tape, starts, chunks_by_book)
    control = shuffled_controls(books, tape, starts, chunks_by_book)
    promotes = (
        observed["exact_in_finished_beam_books"] > control["exact_in_finished_beam_p95"]
        and observed["exact_in_finished_beam_books"] > 0
    )
    weak_survival_clue = (
        observed["true_prefix_survival_books"] > control["true_prefix_survival_p95"]
        or observed["mean_true_prefix_max_fraction"] > control["mean_true_prefix_max_fraction_p95"]
    )
    summary = {
        "literal_tape_digits": len(tape),
        "book_count": observed["book_count"],
        "beam_width": BEAM_WIDTH,
        "copy_candidate_limit": COPY_CANDIDATE_LIMIT,
        "top1_exact_books": observed["top1_exact_books"],
        "exact_in_finished_beam_books": observed["exact_in_finished_beam_books"],
        "exact_in_finished_beam_control_p95": control["exact_in_finished_beam_p95"],
        "true_prefix_survival_books": observed["true_prefix_survival_books"],
        "true_prefix_survival_control_p95": control["true_prefix_survival_p95"],
        "mean_true_prefix_max_fraction": observed["mean_true_prefix_max_fraction"],
        "mean_true_prefix_max_fraction_control_p95": control[
            "mean_true_prefix_max_fraction_p95"
        ],
        "mean_top_prefix_match_fraction": observed["mean_top_prefix_match_fraction"],
        "mean_top_tape_digits_consumed": observed["mean_top_tape_digits_consumed"],
        "promotes_tape_synchronized_generator": promotes,
        "weak_tape_synchronization_clue": weak_survival_clue,
        "interpretation": (
            "This gate tests the constructive synchronization hypothesis: with "
            "canonical tape positions, book lengths, and true prior material "
            "granted, can a closed-loop beam produce the books using only next "
            "tape digit emissions and copies from prior material?"
        ),
    }
    return {
        "schema": "tape_synchronized_closed_loop_gate_v1",
        "scope": "analysis_only_closed_loop_with_canonical_tape_position_and_true_prior_material",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "innovation_tape_replay_gate": rel(REPLAY_GATE),
            "innovation_tape_structure_gate": rel(STRUCTURE_GATE),
        },
        "model": {
            "book_length_granted": True,
            "canonical_tape_start_granted_per_book": True,
            "true_prior_material_granted": True,
            "within_book_target_stream_granted": False,
            "within_book_generated_prefix_as_copy_source": False,
            "literal_emission": "next canonical tape digit only",
            "copy_emission": "unique chunks from prior true material only",
        },
        "observed": observed,
        "shuffle_control": control,
        "literal_tape_digits_by_book": counts,
        "summary": summary,
        "classification": (
            "tape_synchronized_generator_promoted"
            if promotes
            else (
                "tape_synchronization_weak_clue"
                if weak_survival_clue
                else "tape_synchronized_closed_loop_rejected"
            )
        ),
        "decision": {
            "promotes_tape_synchronized_generator": promotes,
            "weak_tape_synchronization_clue": weak_survival_clue,
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
        "# Tape Synchronized Closed Loop Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the structured innovation tape can synchronize a closed-loop",
        "copy transducer. The decoder is granted book length, true prior material,",
        "and the canonical tape start for the book. It is not granted the target",
        "digits inside the book.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Books tested: `{s['book_count']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Copy candidate limit: `{s['copy_candidate_limit']}`.",
        f"- Top-1 exact books: `{s['top1_exact_books']}`.",
        f"- Exact books in finished beam: `{s['exact_in_finished_beam_books']}`.",
        f"- Exact-in-beam shuffled p95: `{s['exact_in_finished_beam_control_p95']}`.",
        f"- True-prefix survival books: `{s['true_prefix_survival_books']}`.",
        f"- True-prefix survival shuffled p95: `{s['true_prefix_survival_control_p95']}`.",
        f"- Mean true-prefix max fraction: `{s['mean_true_prefix_max_fraction']:.6f}`.",
        f"- Mean true-prefix max shuffled p95: `{s['mean_true_prefix_max_fraction_control_p95']:.6f}`.",
        f"- Mean top prefix-match fraction: `{s['mean_top_prefix_match_fraction']:.6f}`.",
        f"- Mean top tape digits consumed: `{s['mean_top_tape_digits_consumed']:.6f}`.",
        f"- Promotes tape-synchronized generator: `{s['promotes_tape_synchronized_generator']}`.",
        f"- Weak tape synchronization clue: `{s['weak_tape_synchronization_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Decision",
        "",
        "- A generator is promoted only if exact books survive above shuffled-tape controls.",
        "- A weak clue is recorded only if prefix survival beats controls.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
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
