from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
BEAM_GATE_SCRIPT = HERE / "scripts" / "01_latent_transducer_beam_gate.py"
CLOSED_LOOP_SCRIPT = HERE / "scripts" / "03_closed_loop_digit_survival_gate.py"
BEAM_GATE = TEST_RESULTS / "01_latent_transducer_beam_gate.json"
CLOSED_LOOP_GATE = TEST_RESULTS / "03_closed_loop_digit_survival_gate.json"

OUT_STEM = "04_closed_loop_rescue_ledger"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BEAM_WIDTH = 250
COPY_CANDIDATE_LIMIT = 80
COPY_LENGTH_CHOICES = [5, 6, 7, 8, 10, 12, 15, 20, 30, 40, 60, 80, 120, 160]
SAMPLE_BOOKS_PER_CUTOFF = 3
DIGIT_BITS = math.log2(10)


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


def decode_book_with_rescue(
    beam_module,
    closed_loop_module,
    emitted_base: str,
    target: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    beam = [closed_loop_module.State(text="", score=0.0, op_count=0, copy_count=0)]
    chunk_inventory = precompute_copy_chunks(beam_module, emitted_base, params)
    copy_cache: dict[int, list[tuple[float, str]]] = {}
    rescue_events = 0
    rescue_bits = 0.0
    max_true_rank = 1
    rank_sum = 0.0
    rank_observations = 0
    first_rescue_len: int | None = None
    true_prefix_max_len = 0
    unreachable = False
    final_true_score: float | None = None
    for _step in range(len(target) + 1):
        exact_states = [state for state in beam if state.text == target]
        if exact_states:
            final_true_score = min(state.score for state in exact_states)
            break
        expansions: dict[str, Any] = {}
        for state in beam:
            if len(state.text) >= len(target):
                continue
            remaining = len(target) - len(state.text)
            for digit in "0123456789":
                text = state.text + digit
                score = state.score + closed_loop_module.literal_digit_score(
                    beam_module, digit, state.text, params
                )
                candidate = closed_loop_module.State(
                    text=text,
                    score=score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count,
                )
                prior = expansions.get(text)
                if prior is None or candidate.score < prior.score:
                    expansions[text] = candidate
            if remaining not in copy_cache:
                copy_cache[remaining] = copy_candidates(chunk_inventory, remaining)
            for copy_score, chunk in copy_cache[remaining]:
                text = state.text + chunk
                if len(text) > len(target):
                    continue
                candidate = closed_loop_module.State(
                    text=text,
                    score=state.score + copy_score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count + 1,
                )
                prior = expansions.get(text)
                if prior is None or candidate.score < prior.score:
                    expansions[text] = candidate
        if not expansions:
            unreachable = True
            break
        ranked = sorted(expansions.values(), key=lambda item: item.score)
        true_prefix_candidates = [
            (rank, state)
            for rank, state in enumerate(ranked, start=1)
            if target.startswith(state.text)
        ]
        if not true_prefix_candidates:
            unreachable = True
            break
        true_rank, true_state = min(true_prefix_candidates, key=lambda item: item[0])
        max_true_rank = max(max_true_rank, true_rank)
        rank_sum += true_rank
        rank_observations += 1
        true_prefix_max_len = max(true_prefix_max_len, len(true_state.text))
        if true_rank > BEAM_WIDTH:
            rescue_events += 1
            rescue_bits += math.log2(true_rank)
            if first_rescue_len is None:
                first_rescue_len = len(true_state.text)
            beam = ranked[: BEAM_WIDTH - 1] + [true_state]
        else:
            beam = ranked[:BEAM_WIDTH]
    raw_digit_bits = len(target) * DIGIT_BITS
    return {
        "forced_exact": final_true_score is not None,
        "unreachable": unreachable,
        "target_len": len(target),
        "true_prefix_max_len": true_prefix_max_len,
        "true_prefix_max_fraction": true_prefix_max_len / len(target),
        "rescue_events": rescue_events,
        "rescue_bits": rescue_bits,
        "rescue_bits_per_digit": rescue_bits / len(target),
        "raw_digit_bits": raw_digit_bits,
        "rescue_bits_fraction_of_raw": rescue_bits / raw_digit_bits,
        "max_true_rank": max_true_rank,
        "mean_true_rank": rank_sum / rank_observations if rank_observations else None,
        "first_rescue_fraction": (
            first_rescue_len / len(target) if first_rescue_len is not None else None
        ),
        "final_true_score": final_true_score,
    }


def precompute_copy_chunks(
    beam_module,
    available: str,
    params: dict[str, Any],
) -> dict[int, list[tuple[float, str]]]:
    by_length: dict[int, dict[str, float]] = {}
    for length in COPY_LENGTH_CHOICES:
        if length > len(available):
            continue
        op_cost = beam_module.op_prior_cost("copy", length, params)
        best: dict[str, float] = {}
        for source in range(0, len(available) - length + 1):
            chunk = available[source : source + length]
            score = op_cost + 0.05 * math.log2(max(1, source + 1))
            prior = best.get(chunk)
            if prior is None or score < prior:
                best[chunk] = score
        by_length[length] = sorted((score, chunk) for chunk, score in best.items())
    return by_length


def copy_candidates(
    inventory: dict[int, list[tuple[float, str]]],
    remaining: int,
) -> list[tuple[float, str]]:
    rows = []
    for length, candidates in inventory.items():
        if length <= remaining:
            rows.extend(candidates[: max(1, COPY_CANDIDATE_LIMIT // 8)])
    rows.sort(key=lambda item: item[0])
    return rows[:COPY_CANDIDATE_LIMIT]


def evaluate_cutoff(
    beam_module,
    closed_loop_module,
    books: dict[int, str],
    cutoff: int,
) -> dict[str, Any]:
    params = beam_module.train_parameters(
        books,
        load_json(beam_module.COPY_SOURCE_LEDGER)["canonical_ops_by_book"],
        cutoff,
    )
    suffix_books = list(range(cutoff, 70))
    sample_books = sorted(
        {
            suffix_books[0],
            suffix_books[len(suffix_books) // 2],
            suffix_books[-1],
        }
    )
    rows = []
    for book in sample_books:
        emitted_base = "".join(books[index] for index in range(book))
        row = decode_book_with_rescue(
            beam_module, closed_loop_module, emitted_base, books[book], params
        )
        row["book"] = book
        rows.append(row)
    total_books = len(rows)
    total_rescue_bits = sum(row["rescue_bits"] for row in rows)
    total_raw_bits = sum(row["raw_digit_bits"] for row in rows)
    first_rescue_values = [
        row["first_rescue_fraction"]
        for row in rows
        if row["first_rescue_fraction"] is not None
    ]
    return {
        "cutoff": cutoff,
        "suffix_books": len(suffix_books),
        "sample_books": sample_books,
        "test_books": total_books,
        "forced_exact_books": sum(1 for row in rows if row["forced_exact"]),
        "unreachable_books": sum(1 for row in rows if row["unreachable"]),
        "books_without_rescue": sum(1 for row in rows if row["rescue_events"] == 0),
        "total_rescue_events": sum(row["rescue_events"] for row in rows),
        "total_rescue_bits": total_rescue_bits,
        "total_raw_digit_bits": total_raw_bits,
        "rescue_bits_fraction_of_raw": total_rescue_bits / total_raw_bits,
        "mean_rescue_events_per_book": sum(row["rescue_events"] for row in rows)
        / total_books,
        "mean_rescue_bits_per_book": total_rescue_bits / total_books,
        "max_true_rank": max(row["max_true_rank"] for row in rows),
        "mean_first_rescue_fraction": (
            sum(first_rescue_values) / len(first_rescue_values)
            if first_rescue_values
            else None
        ),
        "sample_book_rows": rows[:12],
    }


def make_result() -> dict[str, Any]:
    beam_module = load_module("latent_transducer_beam_gate_for_rescue", BEAM_GATE_SCRIPT)
    closed_loop_module = load_module("closed_loop_digit_survival_for_rescue", CLOSED_LOOP_SCRIPT)
    beam_gate = load_json(BEAM_GATE)
    closed_loop = load_json(CLOSED_LOOP_GATE)
    assert_boundary("latent_transducer_beam_gate", beam_gate)
    assert_boundary("closed_loop_digit_survival_gate", closed_loop)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    cutoff_rows = [
        evaluate_cutoff(beam_module, closed_loop_module, books, cutoff)
        for cutoff in PREFIX_CUTOFFS
    ]
    tested_books = sum(row["test_books"] for row in cutoff_rows)
    total_rescue_events = sum(row["total_rescue_events"] for row in cutoff_rows)
    total_rescue_bits = sum(row["total_rescue_bits"] for row in cutoff_rows)
    total_raw_bits = sum(row["total_raw_digit_bits"] for row in cutoff_rows)
    forced_exact_books = sum(row["forced_exact_books"] for row in cutoff_rows)
    no_rescue_books = sum(row["books_without_rescue"] for row in cutoff_rows)
    mean_first_values = [
        row["mean_first_rescue_fraction"]
        for row in cutoff_rows
        if row["mean_first_rescue_fraction"] is not None
    ]
    low_external_control = (
        forced_exact_books == tested_books
        and total_rescue_bits / total_raw_bits < 0.10
        and total_rescue_events <= tested_books
    )
    summary = {
        "cutoff_count": len(PREFIX_CUTOFFS),
        "beam_width": BEAM_WIDTH,
        "sample_books_per_cutoff": SAMPLE_BOOKS_PER_CUTOFF,
        "tested_book_instances": tested_books,
        "forced_exact_books": forced_exact_books,
        "books_without_rescue": no_rescue_books,
        "total_rescue_events": total_rescue_events,
        "mean_rescue_events_per_book": total_rescue_events / tested_books,
        "total_rescue_bits": total_rescue_bits,
        "total_raw_digit_bits": total_raw_bits,
        "rescue_bits_fraction_of_raw": total_rescue_bits / total_raw_bits,
        "max_true_rank": max(row["max_true_rank"] for row in cutoff_rows),
        "mean_first_rescue_fraction": (
            sum(mean_first_values) / len(mean_first_values)
            if mean_first_values
            else None
        ),
        "low_external_control_regime": low_external_control,
        "interpretation": (
            "This sampled ledger turns closed-loop failure into a steering-cost measure. "
            "Whenever the true prefix falls outside the beam, an oracle rescue "
            "injects it back and charges log2(rank). A small rescue ledger would "
            "suggest a missing compact latent state; a large ledger means the "
            "closed-loop route still needs substantial external guidance."
        ),
    }
    return {
        "schema": "closed_loop_rescue_ledger_v1",
        "scope": "analysis_only_closed_loop_missing_state_cost",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "latent_transducer_beam_gate": rel(BEAM_GATE),
            "closed_loop_digit_survival_gate": rel(CLOSED_LOOP_GATE),
        },
        "model": {
            "book_length_granted": True,
            "true_prior_material_granted": True,
            "within_book_target_stream_granted": False,
            "oracle_rescue": "inject best true-prefix state when rank exceeds beam width",
            "rescue_cost_bits": "log2(true_prefix_rank)",
            "sampling": "first/middle/last suffix book per prefix cutoff",
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": (
            "closed_loop_rescue_low_external_control_clue"
            if low_external_control
            else "closed_loop_rescue_high_external_control"
        ),
        "decision": {
            "promotes_closed_loop_generator": False,
            "low_external_control_regime": low_external_control,
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
        "# Closed Loop Rescue Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Measure how much external steering the closed-loop latent transducer needs",
        "after target teacher forcing is removed. When the true prefix falls",
        "outside the beam, the best true-prefix state is injected back and charged",
        "`log2(rank)` bits. This is a fixed first/middle/last suffix-book sample",
        "per cutoff, not a full-corpus rescue total.",
        "",
        "## Summary",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Sample books per cutoff: `{s['sample_books_per_cutoff']}`.",
        f"- Tested book instances: `{s['tested_book_instances']}`.",
        f"- Forced exact books with rescue: `{s['forced_exact_books']}`.",
        f"- Books needing no rescue: `{s['books_without_rescue']}`.",
        f"- Total rescue events: `{s['total_rescue_events']}`.",
        f"- Mean rescue events per book: `{s['mean_rescue_events_per_book']:.3f}`.",
        f"- Total rescue bits: `{s['total_rescue_bits']:.3f}`.",
        f"- Total raw digit bits: `{s['total_raw_digit_bits']:.3f}`.",
        f"- Rescue bits / raw digit bits: `{s['rescue_bits_fraction_of_raw']:.6f}`.",
        f"- Max true-prefix rank: `{s['max_true_rank']}`.",
        f"- Mean first rescue fraction: `{s['mean_first_rescue_fraction']:.6f}`.",
        f"- Low external-control regime: `{s['low_external_control_regime']}`.",
        "",
        s["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Sample Books | Forced Exact | No Rescue | Rescue Events | Rescue Bits | Rescue/Raw | Max Rank | Mean First Rescue |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        first = row["mean_first_rescue_fraction"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['sample_books']}` | "
            f"`{row['forced_exact_books']}` | `{row['books_without_rescue']}` | "
            f"`{row['total_rescue_events']}` | `{row['total_rescue_bits']:.3f}` | "
            f"`{row['rescue_bits_fraction_of_raw']:.6f}` | "
            f"`{row['max_true_rank']}` | "
            f"`{first:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This is an oracle rescue ledger, not a generator.",
            "- Promotion would require a low external-control regime and a concrete decoder-visible state that predicts the rescues.",
            "- The current closed-loop transducer remains unpromoted.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)


if __name__ == "__main__":
    main()
