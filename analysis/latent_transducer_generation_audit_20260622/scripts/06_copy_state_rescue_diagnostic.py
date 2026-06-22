from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
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
BEAM_GATE_SCRIPT = HERE / "scripts" / "01_latent_transducer_beam_gate.py"
CLOSED_LOOP_SCRIPT = HERE / "scripts" / "03_closed_loop_digit_survival_gate.py"
RESCUE_LEDGER_SCRIPT = HERE / "scripts" / "04_closed_loop_rescue_ledger.py"
RESCUE_SURFACE = TEST_RESULTS / "05_closed_loop_rescue_surface_audit.json"

OUT_STEM = "06_copy_state_rescue_diagnostic"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
BEAM_WIDTH = 250


@dataclass(frozen=True)
class TraceState:
    text: str
    score: float
    op_count: int
    copy_count: int
    last_kind: str
    last_len: int


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


def sampled_books_for_cutoff(cutoff: int) -> list[int]:
    suffix_books = list(range(cutoff, 70))
    return sorted(
        {
            suffix_books[0],
            suffix_books[len(suffix_books) // 2],
            suffix_books[-1],
        }
    )


def containing_op(
    ops_by_book: dict[str, list[dict[str, Any]]],
    book: int,
    prefix_len: int,
) -> dict[str, Any] | None:
    if prefix_len <= 0:
        return None
    pos = prefix_len - 1
    for op in ops_by_book[str(book)]:
        start = int(op["target_start"])
        end = start + int(op["length"])
        if start <= pos < end:
            return op
    return None


def trace_rescue_events(
    beam_module,
    closed_loop_module,
    rescue_module,
    emitted_base: str,
    target: str,
    params: dict[str, Any],
    ops_by_book: dict[str, list[dict[str, Any]]],
    book: int,
) -> list[dict[str, Any]]:
    beam = [
        TraceState(
            text="",
            score=0.0,
            op_count=0,
            copy_count=0,
            last_kind="start",
            last_len=0,
        )
    ]
    chunk_inventory = rescue_module.precompute_copy_chunks(beam_module, emitted_base, params)
    copy_cache: dict[int, list[tuple[float, str]]] = {}
    events: list[dict[str, Any]] = []
    for _step in range(len(target) + 1):
        if any(state.text == target for state in beam):
            break
        expansions: dict[str, TraceState] = {}
        for state in beam:
            if len(state.text) >= len(target):
                continue
            remaining = len(target) - len(state.text)
            for digit in "0123456789":
                text = state.text + digit
                score = state.score + closed_loop_module.literal_digit_score(
                    beam_module, digit, state.text, params
                )
                candidate = TraceState(
                    text=text,
                    score=score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count,
                    last_kind="literal",
                    last_len=1,
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
                candidate = TraceState(
                    text=text,
                    score=state.score + copy_score,
                    op_count=state.op_count + 1,
                    copy_count=state.copy_count + 1,
                    last_kind="copy",
                    last_len=len(chunk),
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
            op = containing_op(ops_by_book, book, len(true_state.text))
            surface = "book_end" if len(true_state.text) >= len(target) else "unknown"
            if op is not None and surface != "book_end":
                surface = op["type"]
            row: dict[str, Any] = {
                "book": book,
                "prefix_len": len(true_state.text),
                "prefix_fraction": len(true_state.text) / len(target),
                "rank": true_rank,
                "rank_bits": math.log2(true_rank),
                "last_kind": true_state.last_kind,
                "last_len": true_state.last_len,
                "surface": surface,
            }
            if op is not None:
                start = int(op["target_start"])
                length = int(op["length"])
                row.update(
                    {
                        "canonical_op_type": op["type"],
                        "canonical_op_start": start,
                        "canonical_op_length": length,
                        "canonical_offset_end": len(true_state.text) - start,
                        "canonical_remaining_after_prefix": start
                        + length
                        - len(true_state.text),
                    }
                )
            events.append(row)
            beam = ranked[: BEAM_WIDTH - 1] + [true_state]
        else:
            beam = ranked[:BEAM_WIDTH]
    return events


def candidate_prefix_diagnostic(
    rescue_module,
    beam_module,
    emitted_base: str,
    target: str,
    params: dict[str, Any],
    op: dict[str, Any],
) -> dict[str, Any]:
    start = int(op["target_start"])
    length = int(op["length"])
    source = int(op["source"])
    available = emitted_base + target[:start]
    payload = target[start : start + length]
    source_payload = available[source : source + length]
    source_matches = source_payload == payload
    inventory = rescue_module.precompute_copy_chunks(beam_module, available, params)
    pruned = rescue_module.copy_candidates(inventory, len(target) - start)
    pruned_chunks = {chunk: rank for rank, (_score, chunk) in enumerate(pruned, start=1)}
    allowed = [
        copy_len
        for copy_len in rescue_module.COPY_LENGTH_CHOICES
        if copy_len <= length and copy_len <= len(target) - start
    ]
    max_inventory_prefix = 0
    max_pruned_prefix = 0
    best_inventory_rank = None
    best_pruned_rank = None
    for copy_len in allowed:
        prefix = payload[:copy_len]
        by_length = inventory.get(copy_len, [])
        rank_by_length = next(
            (
                rank
                for rank, (_score, chunk) in enumerate(by_length, start=1)
                if chunk == prefix
            ),
            None,
        )
        if rank_by_length is not None:
            max_inventory_prefix = max(max_inventory_prefix, copy_len)
            best_inventory_rank = (
                rank_by_length
                if best_inventory_rank is None
                else min(best_inventory_rank, rank_by_length)
            )
        rank_pruned = pruned_chunks.get(prefix)
        if rank_pruned is not None:
            max_pruned_prefix = max(max_pruned_prefix, copy_len)
            best_pruned_rank = (
                rank_pruned if best_pruned_rank is None else min(best_pruned_rank, rank_pruned)
            )
    return {
        "source_matches_target": source_matches,
        "canonical_length": length,
        "full_length_allowed": length in rescue_module.COPY_LENGTH_CHOICES,
        "allowed_prefix_lengths": allowed,
        "max_inventory_prefix_len": max_inventory_prefix,
        "max_pruned_prefix_len": max_pruned_prefix,
        "max_inventory_prefix_fraction": max_inventory_prefix / length,
        "max_pruned_prefix_fraction": max_pruned_prefix / length,
        "best_inventory_rank": best_inventory_rank,
        "best_pruned_rank": best_pruned_rank,
        "has_any_inventory_prefix": max_inventory_prefix > 0,
        "has_any_pruned_prefix": max_pruned_prefix > 0,
        "has_full_inventory_chunk": max_inventory_prefix == length,
        "has_full_pruned_chunk": max_pruned_prefix == length,
    }


def summarize_event_rows(events: list[dict[str, Any]]) -> dict[str, Any]:
    copy_surface = [event for event in events if event.get("surface") == "copy"]
    last_kind_counts = Counter(event["last_kind"] for event in events)
    copy_last_kind_counts = Counter(event["last_kind"] for event in copy_surface)
    return {
        "event_count": len(events),
        "copy_surface_event_count": len(copy_surface),
        "last_kind_counts": dict(sorted(last_kind_counts.items())),
        "copy_surface_last_kind_counts": dict(sorted(copy_last_kind_counts.items())),
        "copy_surface_true_copy_event_fraction": (
            copy_last_kind_counts.get("copy", 0) / len(copy_surface)
            if copy_surface
            else 0.0
        ),
        "copy_surface_true_literal_event_fraction": (
            copy_last_kind_counts.get("literal", 0) / len(copy_surface)
            if copy_surface
            else 0.0
        ),
        "mean_copy_surface_rank_bits": (
            mean(event["rank_bits"] for event in copy_surface) if copy_surface else 0.0
        ),
        "mean_copy_surface_last_len": (
            mean(event["last_len"] for event in copy_surface) if copy_surface else 0.0
        ),
        "copy_surface_event_length_counts": dict(
            sorted(Counter(event["last_len"] for event in copy_surface).items())
        ),
    }


def summarize_copy_ops(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    total_digits = sum(row["canonical_length"] for row in rows)
    pruned_digits = sum(row["max_pruned_prefix_len"] for row in rows)
    inventory_digits = sum(row["max_inventory_prefix_len"] for row in rows)
    return {
        "copy_ops_tested": total,
        "copy_digits_tested": total_digits,
        "source_match_ops": sum(1 for row in rows if row["source_matches_target"]),
        "source_match_fraction": (
            sum(1 for row in rows if row["source_matches_target"]) / total if total else 0.0
        ),
        "ops_with_any_inventory_prefix": sum(
            1 for row in rows if row["has_any_inventory_prefix"]
        ),
        "ops_with_any_pruned_prefix": sum(1 for row in rows if row["has_any_pruned_prefix"]),
        "ops_with_full_length_allowed": sum(1 for row in rows if row["full_length_allowed"]),
        "ops_with_full_inventory_chunk": sum(1 for row in rows if row["has_full_inventory_chunk"]),
        "ops_with_full_pruned_chunk": sum(1 for row in rows if row["has_full_pruned_chunk"]),
        "inventory_prefix_digits": inventory_digits,
        "pruned_prefix_digits": pruned_digits,
        "inventory_prefix_digit_fraction": inventory_digits / total_digits
        if total_digits
        else 0.0,
        "pruned_prefix_digit_fraction": pruned_digits / total_digits if total_digits else 0.0,
        "mean_inventory_prefix_fraction": (
            mean(row["max_inventory_prefix_fraction"] for row in rows) if rows else 0.0
        ),
        "mean_pruned_prefix_fraction": (
            mean(row["max_pruned_prefix_fraction"] for row in rows) if rows else 0.0
        ),
        "canonical_length_counts": dict(
            sorted(Counter(row["canonical_length"] for row in rows).items())
        ),
    }


def make_result() -> dict[str, Any]:
    beam_module = load_module("latent_transducer_beam_gate_for_copy_diag", BEAM_GATE_SCRIPT)
    closed_loop_module = load_module(
        "closed_loop_digit_survival_gate_for_copy_diag",
        CLOSED_LOOP_SCRIPT,
    )
    rescue_module = load_module("closed_loop_rescue_ledger_for_copy_diag", RESCUE_LEDGER_SCRIPT)
    rescue_surface = load_json(RESCUE_SURFACE)
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("closed_loop_rescue_surface_audit", rescue_surface)
    assert_boundary("copy_source_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    all_events: list[dict[str, Any]] = []
    all_copy_rows: list[dict[str, Any]] = []
    cutoff_rows = []
    seen_copy_ops: set[tuple[int, int]] = set()
    for cutoff in PREFIX_CUTOFFS:
        params = beam_module.train_parameters(
            books,
            ledger["canonical_ops_by_book"],
            cutoff,
        )
        sample_books = sampled_books_for_cutoff(cutoff)
        cutoff_events: list[dict[str, Any]] = []
        cutoff_copy_rows: list[dict[str, Any]] = []
        for book in sample_books:
            emitted_base = "".join(books[index] for index in range(book))
            events = trace_rescue_events(
                beam_module,
                closed_loop_module,
                rescue_module,
                emitted_base,
                books[book],
                params,
                ledger["canonical_ops_by_book"],
                book,
            )
            cutoff_events.extend(events)
            for op in ledger["canonical_ops_by_book"][str(book)]:
                if op["type"] != "copy":
                    continue
                key = (book, int(op["target_start"]))
                if key in seen_copy_ops:
                    continue
                seen_copy_ops.add(key)
                row = candidate_prefix_diagnostic(
                    rescue_module,
                    beam_module,
                    emitted_base,
                    books[book],
                    params,
                    op,
                )
                row.update(
                    {
                        "book": book,
                        "target_start": int(op["target_start"]),
                    }
                )
                cutoff_copy_rows.append(row)
        all_events.extend(cutoff_events)
        all_copy_rows.extend(cutoff_copy_rows)
        event_summary = summarize_event_rows(cutoff_events)
        copy_summary = summarize_copy_ops(cutoff_copy_rows)
        cutoff_rows.append(
            {
                "cutoff": cutoff,
                "sample_books": sample_books,
                **event_summary,
                "copy_ops_tested": copy_summary["copy_ops_tested"],
                "ops_with_any_pruned_prefix": copy_summary["ops_with_any_pruned_prefix"],
                "pruned_prefix_digit_fraction": copy_summary["pruned_prefix_digit_fraction"],
                "mean_pruned_prefix_fraction": copy_summary["mean_pruned_prefix_fraction"],
            }
        )
    event_summary = summarize_event_rows(all_events)
    copy_summary = summarize_copy_ops(all_copy_rows)
    return {
        "schema": "copy_state_rescue_diagnostic_v1",
        "scope": "analysis_only_copy_state_failure_surface",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "closed_loop_rescue_surface_audit": rel(RESCUE_SURFACE),
        },
        "cutoff_rows": cutoff_rows,
        "event_summary": event_summary,
        "copy_op_summary": copy_summary,
        "classification": "copy_state_control_blocker_mapped",
        "interpretation": (
            "This diagnostic asks whether copy-span rescue failures are mostly "
            "missing inventory or low-rank control. It uses canonical copy spans "
            "only for post-hoc labeling and coverage accounting, not for decoding."
        ),
        "decision": {
            "promotes_generator": False,
            "promotes_copy_state_rule": False,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    e = result["event_summary"]
    c = result["copy_op_summary"]
    lines = [
        "# Copy State Rescue Diagnostic",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Diagnose the copy-span failure exposed by the closed-loop rescue surface",
        "audit. This does not promote a generator; it separates missing copy",
        "inventory from low-rank copy-state/control failure.",
        "",
        "## Event Summary",
        "",
        f"- Rescue events traced: `{e['event_count']}`.",
        f"- Copy-surface rescue events: `{e['copy_surface_event_count']}`.",
        f"- Last-kind counts: `{e['last_kind_counts']}`.",
        f"- Copy-surface last-kind counts: `{e['copy_surface_last_kind_counts']}`.",
        f"- Copy-surface true-copy event fraction: `{e['copy_surface_true_copy_event_fraction']:.6f}`.",
        f"- Copy-surface true-literal event fraction: `{e['copy_surface_true_literal_event_fraction']:.6f}`.",
        f"- Mean copy-surface rescue rank bits: `{e['mean_copy_surface_rank_bits']:.3f}`.",
        f"- Mean copy-surface last emitted length: `{e['mean_copy_surface_last_len']:.3f}`.",
        "",
        "## Canonical Copy Prefix Coverage",
        "",
        f"- Copy ops tested: `{c['copy_ops_tested']}`.",
        f"- Copy digits tested: `{c['copy_digits_tested']}`.",
        f"- Source-match ops: `{c['source_match_ops']}` (`{c['source_match_fraction']:.6f}`).",
        f"- Ops with any inventory prefix: `{c['ops_with_any_inventory_prefix']}`.",
        f"- Ops with any pruned prefix: `{c['ops_with_any_pruned_prefix']}`.",
        f"- Ops with full length allowed: `{c['ops_with_full_length_allowed']}`.",
        f"- Ops with full inventory chunk: `{c['ops_with_full_inventory_chunk']}`.",
        f"- Ops with full pruned chunk: `{c['ops_with_full_pruned_chunk']}`.",
        f"- Inventory prefix digit fraction: `{c['inventory_prefix_digit_fraction']:.6f}`.",
        f"- Pruned prefix digit fraction: `{c['pruned_prefix_digit_fraction']:.6f}`.",
        f"- Mean inventory/pruned prefix fraction: `{c['mean_inventory_prefix_fraction']:.6f}` / `{c['mean_pruned_prefix_fraction']:.6f}`.",
        "",
        result["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Events | Copy Events | Copy Last-Kind | Copy Ops | Any Pruned Prefix | Pruned Prefix Digits |",
        "| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['sample_books']}` | "
            f"`{row['event_count']}` | `{row['copy_surface_event_count']}` | "
            f"`{row['copy_surface_last_kind_counts']}` | "
            f"`{row['copy_ops_tested']}` | `{row['ops_with_any_pruned_prefix']}` | "
            f"`{row['pruned_prefix_digit_fraction']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This maps the next blocker to copy-state/content control.",
            "- It does not produce a decoder-visible source/length rule.",
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
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "event_summary": result["event_summary"],
                "copy_op_summary": result["copy_op_summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
