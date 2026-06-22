from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
BEAM_GATE_SCRIPT = HERE / "scripts" / "01_latent_transducer_beam_gate.py"
BEAM_GATE = TEST_RESULTS / "01_latent_transducer_beam_gate.json"

OUT_STEM = "03_closed_loop_digit_survival_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BEAM_WIDTH = 250
COPY_CANDIDATE_LIMIT = 80
COPY_LENGTH_CHOICES = [5, 6, 7, 8, 10, 12, 15, 20, 30, 40, 60, 80, 120, 160]


@dataclass(frozen=True)
class State:
    text: str
    score: float
    op_count: int
    copy_count: int


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def prefix_match_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index
    return limit


def copy_chunks(
    module,
    available: str,
    remaining: int,
    params: dict[str, Any],
) -> list[tuple[float, str]]:
    by_chunk: dict[str, float] = {}
    for length in COPY_LENGTH_CHOICES:
        if length > remaining or length > len(available):
            continue
        op_cost = module.op_prior_cost("copy", length, params)
        for source in range(0, len(available) - length + 1):
            chunk = available[source : source + length]
            # Copy emits content without digit likelihood; source is still paid weakly
            # to avoid making far-address choices free.
            score = op_cost + 0.05 * math.log2(max(1, source + 1))
            prior = by_chunk.get(chunk)
            if prior is None or score < prior:
                by_chunk[chunk] = score
    return sorted((score, chunk) for chunk, score in by_chunk.items())[:COPY_CANDIDATE_LIMIT]


def literal_digit_score(module, digit: str, prefix: str, params: dict[str, Any]) -> float:
    return (
        module.op_prior_cost("literal", 1, params)
        + module.digit_cost(
            digit,
            prefix,
            params["digit_counts"],
            params["global_digit_counts"],
        )
    )


def decode_book(
    module,
    emitted_base: str,
    target: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    target_len = len(target)
    beam = [State(text="", score=0.0, op_count=0, copy_count=0)]
    finished: list[State] = []
    copy_cache: dict[int, list[tuple[float, str]]] = {}
    true_prefix_best_rank: int | None = 1
    true_prefix_max_len = 0
    true_prefix_survives_all_steps = True
    for _step in range(target_len):
        expansions: dict[str, State] = {}
        for state in beam:
            if len(state.text) == target_len:
                finished.append(state)
                continue
            remaining = target_len - len(state.text)
            for digit in "0123456789":
                text = state.text + digit
                score = state.score + literal_digit_score(module, digit, state.text, params)
                candidate = State(
                    text=text,
                    score=score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count,
                )
                prior = expansions.get(text)
                if prior is None or candidate.score < prior.score:
                    expansions[text] = candidate
            if remaining not in copy_cache:
                copy_cache[remaining] = copy_chunks(module, emitted_base, remaining, params)
            for copy_score, chunk in copy_cache[remaining]:
                text = state.text + chunk
                if len(text) > target_len:
                    continue
                candidate = State(
                    text=text,
                    score=state.score + copy_score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count + 1,
                )
                prior = expansions.get(text)
                if prior is None or candidate.score < prior.score:
                    expansions[text] = candidate
        if not expansions:
            break
        ranked = sorted(expansions.values(), key=lambda item: item.score)
        beam = ranked[:BEAM_WIDTH]
        true_prefix_states = [
            (rank, state)
            for rank, state in enumerate(beam, start=1)
            if target.startswith(state.text)
        ]
        if true_prefix_states:
            rank, state = min(true_prefix_states, key=lambda item: item[0])
            true_prefix_best_rank = rank
            true_prefix_max_len = max(true_prefix_max_len, len(state.text))
        else:
            true_prefix_survives_all_steps = False
            break
        if all(len(state.text) == target_len for state in beam):
            finished.extend(beam)
            break
    if not finished:
        finished.extend(state for state in beam if len(state.text) == target_len)
    finished = sorted(finished, key=lambda item: item.score)
    top = finished[0] if finished else min(beam, key=lambda item: item.score)
    exact_in_finished_rank = None
    for rank, state in enumerate(finished[:BEAM_WIDTH], start=1):
        if state.text == target:
            exact_in_finished_rank = rank
            break
    return {
        "top1_exact": top.text == target,
        "exact_in_finished_beam": exact_in_finished_rank is not None,
        "exact_in_finished_rank": exact_in_finished_rank,
        "true_prefix_survives_all_steps": true_prefix_survives_all_steps,
        "true_prefix_best_rank_last": true_prefix_best_rank,
        "true_prefix_max_len": true_prefix_max_len,
        "target_len": target_len,
        "top_prefix_match_len": prefix_match_len(top.text, target),
        "top_score": top.score,
        "top_op_count": top.op_count,
        "top_copy_count": top.copy_count,
    }


def evaluate_cutoff(
    module,
    books: dict[int, str],
    cutoff: int,
) -> dict[str, Any]:
    # Training is prefix-only; per-book decoding still grants true previous
    # material to avoid a cascade where one generated book poisons all later
    # source availability.
    params = module.train_parameters(
        books,
        load_json(module.COPY_SOURCE_LEDGER)["canonical_ops_by_book"],
        cutoff,
    )
    rows = []
    for book in range(cutoff, 70):
        emitted_base = "".join(books[index] for index in range(book))
        row = decode_book(module, emitted_base, books[book], params)
        row["book"] = book
        rows.append(row)
    return {
        "cutoff": cutoff,
        "test_books": len(rows),
        "top1_exact_books": sum(1 for row in rows if row["top1_exact"]),
        "exact_in_finished_beam_books": sum(
            1 for row in rows if row["exact_in_finished_beam"]
        ),
        "true_prefix_survival_books": sum(
            1 for row in rows if row["true_prefix_survives_all_steps"]
        ),
        "mean_true_prefix_max_fraction": sum(
            row["true_prefix_max_len"] / row["target_len"] for row in rows
        )
        / len(rows),
        "mean_top_prefix_match_fraction": sum(
            row["top_prefix_match_len"] / row["target_len"] for row in rows
        )
        / len(rows),
        "mean_top_copy_count": sum(row["top_copy_count"] for row in rows) / len(rows),
        "sample_book_rows": rows[:12],
    }


def make_result() -> dict[str, Any]:
    module = load_module("latent_transducer_beam_gate_for_closed_loop", BEAM_GATE_SCRIPT)
    beam_gate = load_json(BEAM_GATE)
    assert_boundary("latent_transducer_beam_gate", beam_gate)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    cutoff_rows = [evaluate_cutoff(module, books, cutoff) for cutoff in PREFIX_CUTOFFS]
    top1_exact = sum(row["top1_exact_books"] for row in cutoff_rows)
    exact_in_beam = sum(row["exact_in_finished_beam_books"] for row in cutoff_rows)
    prefix_survival = sum(row["true_prefix_survival_books"] for row in cutoff_rows)
    tested = sum(row["test_books"] for row in cutoff_rows)
    promotes_closed_loop = top1_exact > 0 or exact_in_beam >= tested // 2
    summary = {
        "cutoff_count": len(PREFIX_CUTOFFS),
        "beam_width": BEAM_WIDTH,
        "copy_candidate_limit": COPY_CANDIDATE_LIMIT,
        "tested_book_instances": tested,
        "top1_exact_books": top1_exact,
        "exact_in_finished_beam_books": exact_in_beam,
        "true_prefix_survival_books": prefix_survival,
        "mean_true_prefix_max_fraction": sum(
            row["mean_true_prefix_max_fraction"] * row["test_books"]
            for row in cutoff_rows
        )
        / tested,
        "mean_top_prefix_match_fraction": sum(
            row["mean_top_prefix_match_fraction"] * row["test_books"]
            for row in cutoff_rows
        )
        / tested,
        "promotes_closed_loop_digit_generator": promotes_closed_loop,
        "interpretation": (
            "The gate removes within-book target teacher forcing and asks whether "
            "the real digit stream survives a closed-loop beam when book length "
            "and true prior material are granted. This is a generous survival "
            "test, not a complete corpus generator."
        ),
    }
    return {
        "schema": "closed_loop_digit_survival_gate_v1",
        "scope": "analysis_only_closed_loop_digit_survival_with_true_prior_material",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "latent_transducer_beam_gate": rel(BEAM_GATE),
        },
        "model": {
            "book_length_granted": True,
            "true_prior_material_granted": True,
            "within_book_target_stream_granted": False,
            "literal_digit_branching": "all_10_digits",
            "copy_branching": (
                "unique chunks from true prior material only, "
                f"limited to {COPY_CANDIDATE_LIMIT} cheapest chunks"
            ),
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": (
            "closed_loop_digit_generator_promoted"
            if promotes_closed_loop
            else "closed_loop_digit_survival_rejected"
        ),
        "decision": {
            "promotes_closed_loop_digit_generator": promotes_closed_loop,
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
        "# Closed Loop Digit Survival Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Remove within-book target teacher forcing from the latent transducer route.",
        "The decoder knows the target book length and true prior material, then",
        "generates candidate digit prefixes by literal digit emissions or copied",
        "chunks. The test asks whether the real book is top-1 or survives in the",
        "beam.",
        "",
        "## Summary",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Copy candidate limit: `{s['copy_candidate_limit']}`.",
        f"- Tested book instances: `{s['tested_book_instances']}`.",
        f"- Top-1 exact books: `{s['top1_exact_books']}`.",
        f"- Exact books surviving finished beam: `{s['exact_in_finished_beam_books']}`.",
        f"- True-prefix survival books: `{s['true_prefix_survival_books']}`.",
        f"- Mean true-prefix max fraction: `{s['mean_true_prefix_max_fraction']:.6f}`.",
        f"- Mean top prefix-match fraction: `{s['mean_top_prefix_match_fraction']:.6f}`.",
        f"- Promotes closed-loop digit generator: `{s['promotes_closed_loop_digit_generator']}`.",
        "",
        s["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Top-1 exact | Exact in beam | True-prefix survival | Mean true-prefix max | Mean top prefix-match |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['top1_exact_books']}/{row['test_books']}` | "
            f"`{row['exact_in_finished_beam_books']}/{row['test_books']}` | "
            f"`{row['true_prefix_survival_books']}/{row['test_books']}` | "
            f"`{row['mean_true_prefix_max_fraction']:.6f}` | "
            f"`{row['mean_top_prefix_match_fraction']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Closed-loop digit generation is rejected unless the JSON summary says otherwise.",
            "- The result does not touch row0, plaintext, or translation.",
            "- Compression bound is unchanged.",
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
