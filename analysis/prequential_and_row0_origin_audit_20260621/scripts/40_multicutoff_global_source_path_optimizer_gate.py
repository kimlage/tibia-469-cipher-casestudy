from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_137 = AUTHORIAL / "scripts" / "137_copy_source_default_decodability_audit.py"
GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE39_SCRIPT = HERE / "scripts" / "39_multicutoff_source_choice_optimizer_gate.py"
GATE39_RESULT = TEST_RESULTS / "39_multicutoff_source_choice_optimizer_gate.json"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
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
    if decision.get("row0_origin_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced plaintext status")


def build_fixed_copy_events(
    *,
    cutoff: int,
    formula: dict[str, Any],
    books: dict[str, str],
    train_counts: dict[str, Any],
    audit126,
    gate39,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    available = "".join(books[str(book)] for book in range(cutoff))
    events = []
    book_rows = []
    non_source_bits = 0.0
    uniform_address_bits = 0.0
    raw_digit_bits = 0.0
    errors = []
    for book in range(cutoff, 70):
        book_key = str(book)
        encoded = audit126.encode_book_frozen_reparse(
            book=book_key,
            text=books[book_key],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )
        if encoded["validation"]["errors"]:
            errors.extend(
                {"book": book, "error": error}
                for error in encoded["validation"]["errors"]
            )
        local_emitted = available
        rendered = []
        book_copy_count = 0
        book_candidate_count = 0
        for op_index, op in enumerate(encoded["ops"]):
            if op["type"] == "literal":
                chunk = op["text"]
                local_emitted += chunk
                rendered.append(chunk)
                continue

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = local_emitted[source : source + length]
            legal_source_count = max(1, len(local_emitted) - min_len + 1)
            candidates = gate39.legal_sources_for_chunk(
                emitted=local_emitted,
                chunk=chunk,
                legal_source_count=legal_source_count,
            )
            if source not in candidates:
                candidates.append(source)
            candidates = sorted(set(candidates))
            events.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "length": length,
                    "original_source": source,
                    "legal_source_count": legal_source_count,
                    "candidates": candidates,
                }
            )
            book_copy_count += 1
            book_candidate_count += len(candidates)
            local_emitted += chunk
            rendered.append(chunk)
        if "".join(rendered) != books[book_key]:
            errors.append({"book": book, "error": "event_render_mismatch"})
        non_source_bits += encoded["bits"] - encoded["copy_address_bits"]
        uniform_address_bits += encoded["bits"]
        raw_digit_bits += len(books[book_key]) * math.log2(10)
        book_rows.append(
            {
                "book": book,
                "copy_items": book_copy_count,
                "candidate_count": book_candidate_count,
                "uniform_address_reparse_bits": encoded["bits"],
                "non_source_bits": encoded["bits"] - encoded["copy_address_bits"],
                "raw_digit_uniform_bits": len(books[book_key]) * math.log2(10),
                "roundtrip_ok": not encoded["validation"]["errors"],
            }
        )
        available += books[book_key]
    return {
        "events": events,
        "book_rows": book_rows,
        "non_source_bits": non_source_bits,
        "uniform_address_reparse_bits": uniform_address_bits,
        "raw_digit_uniform_bits": raw_digit_bits,
        "errors": errors,
    }


def optimize_source_path(
    *,
    events: list[dict[str, Any]],
    initial_previous_end: int | None,
    source_train_counts: dict[str, Any],
    gate37,
) -> dict[str, Any]:
    states: dict[int | None, float] = {initial_previous_end: 0.0}
    backpointers: list[dict[int, tuple[int | None, int, bool, float, float, float]]] = []
    max_state_count = 1
    transition_count = 0
    for event in events:
        next_states: dict[int, float] = {}
        back: dict[int, tuple[int | None, int, bool, float, float, float]] = {}
        for previous_end, previous_bits in states.items():
            for source in event["candidates"]:
                bits, is_default, flag_bits, exception_bits = (
                    gate37.source_default_exception_bits(
                        source=source,
                        legal_source_count=int(event["legal_source_count"]),
                        previous_copy_end=previous_end,
                        counts=source_train_counts,
                    )
                )
                if not math.isfinite(bits):
                    continue
                transition_count += 1
                next_end = int(source) + int(event["length"])
                total = previous_bits + bits
                if next_end not in next_states or total < next_states[next_end]:
                    next_states[next_end] = total
                    back[next_end] = (
                        previous_end,
                        int(source),
                        bool(is_default),
                        float(bits),
                        float(flag_bits),
                        float(exception_bits),
                    )
        if not next_states:
            raise RuntimeError({"type": "no_next_states", "event": event})
        backpointers.append(back)
        states = next_states
        max_state_count = max(max_state_count, len(states))

    final_end, source_bits = min(states.items(), key=lambda item: item[1])
    choices = []
    current_end: int | None = final_end
    for index in range(len(events) - 1, -1, -1):
        previous_end, source, is_default, bits, flag_bits, exception_bits = backpointers[index][
            int(current_end)
        ]
        event = events[index]
        choices.append(
            {
                "event_index": index,
                "book": event["book"],
                "op_index": event["op_index"],
                "source_digit_pos": source,
                "original_source_digit_pos": event["original_source"],
                "source_changed": source != event["original_source"],
                "length": event["length"],
                "candidate_count": len(event["candidates"]),
                "source_is_default": is_default,
                "bits": bits,
                "flag_bits": flag_bits,
                "exception_bits": exception_bits,
            }
        )
        current_end = previous_end
    choices.reverse()
    return {
        "source_bits": source_bits,
        "final_previous_end": final_end,
        "choices": choices,
        "max_state_count": max_state_count,
        "transition_count": transition_count,
    }


def original_reprice_for_events(
    *,
    events: list[dict[str, Any]],
    initial_previous_end: int | None,
    source_train_counts: dict[str, Any],
    gate37,
) -> dict[str, Any]:
    previous_end = initial_previous_end
    source_bits = flag_bits = exception_bits = 0.0
    defaults = exceptions = 0
    for event in events:
        source = int(event["original_source"])
        bits, is_default, flag, exception = gate37.source_default_exception_bits(
            source=source,
            legal_source_count=int(event["legal_source_count"]),
            previous_copy_end=previous_end,
            counts=source_train_counts,
        )
        source_bits += bits
        flag_bits += flag
        exception_bits += exception
        if is_default:
            defaults += 1
        else:
            exceptions += 1
        previous_end = source + int(event["length"])
    return {
        "source_bits": source_bits,
        "source_flag_bits": flag_bits,
        "source_exception_bits": exception_bits,
        "source_default_count": defaults,
        "source_exception_count": exceptions,
        "final_previous_end": previous_end,
    }


def cutoff_optimize(
    *,
    cutoff: int,
    formula: dict[str, Any],
    books: dict[str, str],
    train_counts: dict[str, Any],
    source_train_counts: dict[str, Any],
    audit126,
    gate37,
    gate39,
) -> dict[str, Any]:
    event_data = build_fixed_copy_events(
        cutoff=cutoff,
        formula=formula,
        books=books,
        train_counts=train_counts,
        audit126=audit126,
        gate39=gate39,
    )
    initial_previous_end = gate37.previous_copy_end_before(formula, cutoff)
    original = original_reprice_for_events(
        events=event_data["events"],
        initial_previous_end=initial_previous_end,
        source_train_counts=source_train_counts,
        gate37=gate37,
    )
    optimized = optimize_source_path(
        events=event_data["events"],
        initial_previous_end=initial_previous_end,
        source_train_counts=source_train_counts,
        gate37=gate37,
    )
    changed_sources = sum(1 for choice in optimized["choices"] if choice["source_changed"])
    default_count = sum(1 for choice in optimized["choices"] if choice["source_is_default"])
    exception_count = len(optimized["choices"]) - default_count
    optimized_bits = event_data["non_source_bits"] + optimized["source_bits"]
    original_bits = event_data["non_source_bits"] + original["source_bits"]
    uniform_bits = event_data["uniform_address_reparse_bits"]
    raw_bits = event_data["raw_digit_uniform_bits"]
    return {
        "cutoff": cutoff,
        "train_books": list(range(cutoff)),
        "test_books": list(range(cutoff, 70)),
        "book_count": len(event_data["book_rows"]),
        "roundtrip_book_count": sum(1 for row in event_data["book_rows"] if row["roundtrip_ok"]),
        "copy_event_count": len(event_data["events"]),
        "candidate_count": sum(len(event["candidates"]) for event in event_data["events"]),
        "changed_source_count": changed_sources,
        "source_default_count": default_count,
        "source_exception_count": exception_count,
        "max_state_count": optimized["max_state_count"],
        "transition_count": optimized["transition_count"],
        "aggregate": {
            "bits": optimized_bits,
            "source_state_reprice_bits": original_bits,
            "uniform_address_reparse_bits": uniform_bits,
            "raw_digit_uniform_bits": raw_bits,
            "source_bits": optimized["source_bits"],
            "source_state_reprice_source_bits": original["source_bits"],
            "source_path_minus_reprice_bits": optimized_bits - original_bits,
            "source_path_minus_uniform_address_bits": optimized_bits - uniform_bits,
            "gain_vs_raw_digit_uniform_bits": raw_bits - optimized_bits,
        },
        "book_rows": event_data["book_rows"],
        "sample_changed_sources": [
            choice for choice in optimized["choices"] if choice["source_changed"]
        ][:10],
        "errors": event_data["errors"],
    }


def make_result() -> dict[str, Any]:
    gate39_result = load_json(GATE39_RESULT)
    assert_boundary("multicutoff_source_choice_optimizer_gate", gate39_result)
    gate37 = load_module("gate37_source_state_reprice", GATE37_SCRIPT)
    gate39 = load_module("gate39_source_choice", GATE39_SCRIPT)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = load_module("audit126", AUDIT_126)
    audit137 = load_module("audit137", AUDIT_137)
    payload_module = load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])
    source_rows = audit137.collect_source_rows(formula, books)
    if source_rows["errors"]:
        raise RuntimeError(source_rows["errors"])
    max_source_count = sum(len(text) for text in books.values()) + 1

    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_counts = audit126.train_counts_for_cutoff(
            cutoff=cutoff,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        source_train_counts = gate37.source_counts(
            [row for row in source_rows["rows"] if int(row["book"]) < cutoff],
            max_source_count=max_source_count,
        )
        rows.append(
            cutoff_optimize(
                cutoff=cutoff,
                formula=formula,
                books=books,
                train_counts=train_counts,
                source_train_counts=source_train_counts,
                audit126=audit126,
                gate37=gate37,
                gate39=gate39,
            )
        )

    all_roundtrip = all(row["roundtrip_book_count"] == row["book_count"] for row in rows)
    all_raw_positive = all(row["aggregate"]["gain_vs_raw_digit_uniform_bits"] > 0 for row in rows)
    aggregate_beats_reprice = [
        row for row in rows if row["aggregate"]["source_path_minus_reprice_bits"] < 0
    ]
    total_delta = sum(row["aggregate"]["source_path_minus_reprice_bits"] for row in rows)
    total_changed = sum(row["changed_source_count"] for row in rows)
    if all_roundtrip and all_raw_positive and total_delta < 0:
        classification = "global_source_path_optimizer_improves_fixed_segmentation_unpromoted"
    elif all_roundtrip and all_raw_positive and total_changed == 0:
        classification = "global_source_path_optimizer_no_change_boundary"
    else:
        classification = "global_source_path_optimizer_mixed_unpromoted"

    return {
        "schema": "multicutoff_global_source_path_optimizer_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate37_script": rel(GATE37_SCRIPT),
            "gate39_script": rel(GATE39_SCRIPT),
            "gate39_result": rel(GATE39_RESULT),
        },
        "scope": {
            "cutoffs": PREFIX_CUTOFFS,
            "optimization": "exact DP over copy-source choices with fixed deterministic reparse segmentation and copy lengths",
            "not_segmentation_reoptimization": True,
            "source_counts": "frozen from train prefix for each cutoff",
        },
        "summary": {
            "cutoff_count": len(rows),
            "all_roundtrip": all_roundtrip,
            "all_books_beat_raw": all_raw_positive,
            "aggregate_beats_reprice_cutoff_count": len(aggregate_beats_reprice),
            "rows": rows,
            "total_bits": sum(row["aggregate"]["bits"] for row in rows),
            "total_reprice_bits": sum(row["aggregate"]["source_state_reprice_bits"] for row in rows),
            "total_uniform_address_reparse_bits": sum(
                row["aggregate"]["uniform_address_reparse_bits"] for row in rows
            ),
            "total_source_path_minus_reprice_bits": total_delta,
            "total_source_path_minus_uniform_address_bits": sum(
                row["aggregate"]["source_path_minus_uniform_address_bits"] for row in rows
            ),
            "total_changed_sources": total_changed,
            "total_copy_events": sum(row["copy_event_count"] for row in rows),
            "total_candidate_count": sum(row["candidate_count"] for row in rows),
            "total_source_defaults": sum(row["source_default_count"] for row in rows),
            "total_source_exceptions": sum(row["source_exception_count"] for row in rows),
            "max_state_count": max(row["max_state_count"] for row in rows),
            "total_transition_count": sum(row["transition_count"] for row in rows),
            "remaining_blockers": [
                "Segmentation and copy lengths remain fixed from deterministic reparse.",
                "Source counts are frozen from train prefixes; no adaptive source-count update over the test suffix is modeled.",
                "This does not promote a complete active parser or a new compression bound.",
            ],
        },
        "decision": {
            "source_path_status": "global_fixed_segmentation_source_path_tested",
            "recipe_discovery_status": "source_path_optimized_but_segmentation_lengths_fixed",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "40_multicutoff_global_source_path_optimizer_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Multi-Cutoff Global Source Path Optimizer Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 39 showed that greedy local source substitution changes no sources.",
        "This gate tests the next stronger fixed-segmentation hypothesis: an exact",
        "dynamic program over copy-source choices, where a locally expensive source",
        "may be chosen if its `previous_copy_end` state makes later sources cheaper.",
        "Segmentation and copy lengths remain fixed.",
        "",
        "## Summary",
        "",
        f"- All cutoffs roundtrip: `{s['all_roundtrip']}`.",
        f"- All books beat raw digit coding: `{s['all_books_beat_raw']}`.",
        f"- Aggregate beats repricing at cutoffs: `{s['aggregate_beats_reprice_cutoff_count']}/{s['cutoff_count']}`.",
        f"- Total optimized bits: `{s['total_bits']:.3f}`.",
        f"- Total repriced bits: `{s['total_reprice_bits']:.3f}`.",
        f"- Total optimized minus repriced bits: `{s['total_source_path_minus_reprice_bits']:+.3f}`.",
        f"- Total optimized minus uniform-address bits: `{s['total_source_path_minus_uniform_address_bits']:+.3f}`.",
        f"- Changed sources: `{s['total_changed_sources']}/{s['total_copy_events']}`.",
        f"- Defaults/exceptions: `{s['total_source_defaults']}` / `{s['total_source_exceptions']}`.",
        f"- Max DP state count: `{s['max_state_count']}`.",
        f"- Total DP transitions: `{s['total_transition_count']}`.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Copy events | Candidates | Changed | States max | Optimized bits | Reprice bits | Delta vs reprice | Delta vs uniform | Defaults | Exceptions |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["rows"]:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['book_count']}` | "
            f"`{row['copy_event_count']}` | `{row['candidate_count']}` | "
            f"`{row['changed_source_count']}` | `{row['max_state_count']}` | "
            f"`{agg['bits']:.3f}` | `{agg['source_state_reprice_bits']:.3f}` | "
            f"`{agg['source_path_minus_reprice_bits']:+.3f}` | "
            f"`{agg['source_path_minus_uniform_address_bits']:+.3f}` | "
            f"`{row['source_default_count']}` | `{row['source_exception_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is the first global source-path test under `previous_copy_end`.",
            "It determines whether fixed deterministic copy events can be improved",
            "by choosing sources for future state value rather than immediate cost.",
            "",
            "It remains a partial parser: copy/literal segmentation and copy lengths",
            "are fixed from deterministic reparse, and no compression bound is",
            "promoted.",
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced.",
            "- No complete active parser or global recipe-discovery promotion is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "40_multicutoff_global_source_path_optimizer_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
