from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import Counter
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
BEAM_GATE_SCRIPT = HERE / "scripts" / "01_latent_transducer_beam_gate.py"
CLOSED_LOOP_SCRIPT = HERE / "scripts" / "03_closed_loop_digit_survival_gate.py"
RESCUE_LEDGER_SCRIPT = HERE / "scripts" / "04_closed_loop_rescue_ledger.py"
RESCUE_LEDGER = TEST_RESULTS / "04_closed_loop_rescue_ledger.json"

OUT_STEM = "05_closed_loop_rescue_surface_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BEAM_WIDTH = 250


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


def op_surface(
    ops_by_book: dict[str, list[dict[str, Any]]],
    book: int,
    prefix_len: int,
    book_len: int,
) -> dict[str, Any]:
    ops = ops_by_book[str(book)]
    starts = {int(op["target_start"]) for op in ops}
    cutpoints = {
        int(op["target_start"]) + int(op["length"])
        for op in ops[:-1]
    }
    near_cutpoint = any(abs(prefix_len - cutpoint) <= 1 for cutpoint in cutpoints)
    if prefix_len <= 0:
        containing = "book_start"
    elif prefix_len >= book_len:
        containing = "book_end"
    else:
        containing = "unknown"
        pos = prefix_len - 1
        for op in ops:
            start = int(op["target_start"])
            end = start + int(op["length"])
            if start <= pos < end:
                containing = op["type"]
                break
    return {
        "at_op_start": prefix_len in starts,
        "at_internal_cutpoint": prefix_len in cutpoints,
        "near_internal_cutpoint": near_cutpoint,
        "surface": containing,
    }


def decode_book_with_event_surface(
    beam_module,
    closed_loop_module,
    rescue_module,
    emitted_base: str,
    target: str,
    params: dict[str, Any],
    ops_by_book: dict[str, list[dict[str, Any]]],
    book: int,
) -> dict[str, Any]:
    beam = [closed_loop_module.State(text="", score=0.0, op_count=0, copy_count=0)]
    chunk_inventory = rescue_module.precompute_copy_chunks(beam_module, emitted_base, params)
    copy_cache: dict[int, list[tuple[float, str]]] = {}
    events = []
    for _step in range(len(target) + 1):
        if any(state.text == target for state in beam):
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
                copy_cache[remaining] = rescue_module.copy_candidates(
                    chunk_inventory, remaining
                )
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
            break
        ranked = sorted(expansions.values(), key=lambda item: item.score)
        true_prefix_candidates = [
            (rank, state)
            for rank, state in enumerate(ranked, start=1)
            if target.startswith(state.text)
        ]
        if not true_prefix_candidates:
            break
        true_rank, true_state = min(true_prefix_candidates, key=lambda item: item[0])
        if true_rank > BEAM_WIDTH:
            prefix_len = len(true_state.text)
            surface = op_surface(ops_by_book, book, prefix_len, len(target))
            events.append(
                {
                    "book": book,
                    "prefix_len": prefix_len,
                    "prefix_fraction": prefix_len / len(target),
                    "rank": true_rank,
                    "rank_bits": math.log2(true_rank),
                    **surface,
                }
            )
            beam = ranked[: BEAM_WIDTH - 1] + [true_state]
        else:
            beam = ranked[:BEAM_WIDTH]
    return {
        "book": book,
        "target_len": len(target),
        "event_count": len(events),
        "events": events,
    }


def sampled_books_for_cutoff(cutoff: int) -> list[int]:
    suffix_books = list(range(cutoff, 70))
    return sorted(
        {
            suffix_books[0],
            suffix_books[len(suffix_books) // 2],
            suffix_books[-1],
        }
    )


def make_result() -> dict[str, Any]:
    beam_module = load_module("latent_transducer_beam_gate_for_surface", BEAM_GATE_SCRIPT)
    closed_loop_module = load_module(
        "closed_loop_digit_survival_gate_for_surface",
        CLOSED_LOOP_SCRIPT,
    )
    rescue_module = load_module("closed_loop_rescue_ledger_for_surface", RESCUE_LEDGER_SCRIPT)
    rescue_ledger = load_json(RESCUE_LEDGER)
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("closed_loop_rescue_ledger", rescue_ledger)
    assert_boundary("copy_source_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows = []
    all_events = []
    for cutoff in PREFIX_CUTOFFS:
        params = beam_module.train_parameters(
            books,
            ledger["canonical_ops_by_book"],
            cutoff,
        )
        sample_books = sampled_books_for_cutoff(cutoff)
        cutoff_events = []
        for book in sample_books:
            emitted_base = "".join(books[index] for index in range(book))
            row = decode_book_with_event_surface(
                beam_module,
                closed_loop_module,
                rescue_module,
                emitted_base,
                books[book],
                params,
                ledger["canonical_ops_by_book"],
                book,
            )
            cutoff_events.extend(row["events"])
        all_events.extend(cutoff_events)
        rows.append(
            summarize_events(
                {
                    "cutoff": cutoff,
                    "sample_books": sample_books,
                    "events": cutoff_events,
                }
            )
        )
    summary = summarize_events({"cutoff": "all", "sample_books": [], "events": all_events})
    summary.update(
        {
            "cutoff_count": len(PREFIX_CUTOFFS),
            "sample_book_instances": len(PREFIX_CUTOFFS) * 3,
            "promotes_rescue_surface": False,
            "interpretation": (
                "This audit classifies oracle rescue events from the sampled "
                "closed-loop rescue ledger against the canonical skeleton. It "
                "does not use the skeleton for generation; it asks whether the "
                "missing closed-loop state has an obvious surface such as "
                "operation boundaries or literal interiors."
            ),
        }
    )
    return {
        "schema": "closed_loop_rescue_surface_audit_v1",
        "scope": "analysis_only_missing_state_surface_classification",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "closed_loop_rescue_ledger": rel(RESCUE_LEDGER),
        },
        "cutoff_rows": rows,
        "summary": summary,
        "classification": "closed_loop_rescue_surface_audit_only",
        "decision": {
            "promotes_rescue_surface": False,
            "generator_status": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def summarize_events(row: dict[str, Any]) -> dict[str, Any]:
    events = row["events"]
    surface_counts = Counter(event["surface"] for event in events)
    total = len(events)
    early_5 = sum(1 for event in events if event["prefix_fraction"] <= 0.05)
    early_20 = sum(1 for event in events if event["prefix_fraction"] <= 0.20)
    at_cutpoint = sum(1 for event in events if event["at_internal_cutpoint"])
    near_cutpoint = sum(1 for event in events if event["near_internal_cutpoint"])
    at_op_start = sum(1 for event in events if event["at_op_start"])
    return {
        "cutoff": row["cutoff"],
        "sample_books": row["sample_books"],
        "event_count": total,
        "surface_counts": dict(sorted(surface_counts.items())),
        "copy_surface_fraction": (
            surface_counts.get("copy", 0) / total if total else 0.0
        ),
        "literal_surface_fraction": (
            surface_counts.get("literal", 0) / total if total else 0.0
        ),
        "at_internal_cutpoint": at_cutpoint,
        "near_internal_cutpoint": near_cutpoint,
        "at_op_start": at_op_start,
        "at_internal_cutpoint_fraction": at_cutpoint / total if total else 0.0,
        "near_internal_cutpoint_fraction": near_cutpoint / total if total else 0.0,
        "at_op_start_fraction": at_op_start / total if total else 0.0,
        "early_5pct_events": early_5,
        "early_20pct_events": early_20,
        "early_5pct_fraction": early_5 / total if total else 0.0,
        "early_20pct_fraction": early_20 / total if total else 0.0,
        "mean_rank_bits": (
            sum(event["rank_bits"] for event in events) / total if total else 0.0
        ),
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Closed Loop Rescue Surface Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Classify where sampled closed-loop oracle rescues occur relative to the",
        "canonical skeleton. This is a missing-state surface audit, not a",
        "generator: the skeleton is used only after decoding to label events.",
        "",
        "## Summary",
        "",
        f"- Sample book instances: `{s['sample_book_instances']}`.",
        f"- Rescue events classified: `{s['event_count']}`.",
        f"- Surface counts: `{s['surface_counts']}`.",
        f"- Copy/literal surface fraction: `{s['copy_surface_fraction']:.6f}` / `{s['literal_surface_fraction']:.6f}`.",
        f"- Exact internal cutpoint events: `{s['at_internal_cutpoint']}` (`{s['at_internal_cutpoint_fraction']:.6f}`).",
        f"- Near internal cutpoint events: `{s['near_internal_cutpoint']}` (`{s['near_internal_cutpoint_fraction']:.6f}`).",
        f"- Operation-start events: `{s['at_op_start']}` (`{s['at_op_start_fraction']:.6f}`).",
        f"- Early <=5% events: `{s['early_5pct_events']}` (`{s['early_5pct_fraction']:.6f}`).",
        f"- Early <=20% events: `{s['early_20pct_events']}` (`{s['early_20pct_fraction']:.6f}`).",
        f"- Mean rescue rank bits: `{s['mean_rank_bits']:.3f}`.",
        f"- Promotes rescue surface: `{s['promotes_rescue_surface']}`.",
        "",
        s["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Events | Surface Counts | Exact Cutpoint | Near Cutpoint | Op Start | Early <=20% | Mean Rank Bits |",
        "| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['sample_books']}` | "
            f"`{row['event_count']}` | `{row['surface_counts']}` | "
            f"`{row['at_internal_cutpoint_fraction']:.3f}` | "
            f"`{row['near_internal_cutpoint_fraction']:.3f}` | "
            f"`{row['at_op_start_fraction']:.3f}` | "
            f"`{row['early_20pct_fraction']:.3f}` | "
            f"`{row['mean_rank_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Rescue events are diagnostic labels for the missing state, not generator outputs.",
            "- A promotable next step would require a decoder-visible state that predicts these rescue surfaces without the canonical skeleton.",
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
