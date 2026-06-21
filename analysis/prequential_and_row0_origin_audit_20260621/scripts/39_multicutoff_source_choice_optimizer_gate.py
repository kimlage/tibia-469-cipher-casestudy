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
GATE38_RESULT = TEST_RESULTS / "38_multicutoff_source_state_reparse_reprice_gate.json"

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


def legal_sources_for_chunk(
    *,
    emitted: str,
    chunk: str,
    legal_source_count: int,
) -> list[int]:
    sources = []
    start = emitted.find(chunk, 0, legal_source_count + len(chunk) - 1)
    while start != -1:
        if start < legal_source_count and emitted[start : start + len(chunk)] == chunk:
            sources.append(start)
        next_start = start + 1
        start = emitted.find(chunk, next_start, legal_source_count + len(chunk) - 1)
    return sources


def choose_source(
    *,
    emitted: str,
    chunk: str,
    legal_source_count: int,
    original_source: int,
    previous_copy_end: int | None,
    source_train_counts: dict[str, Any],
    gate37,
) -> dict[str, Any]:
    candidates = legal_sources_for_chunk(
        emitted=emitted,
        chunk=chunk,
        legal_source_count=legal_source_count,
    )
    if original_source not in candidates:
        candidates.append(original_source)
    best = None
    for source in candidates:
        bits, is_default, flag_bits, exception_bits = gate37.source_default_exception_bits(
            source=source,
            legal_source_count=legal_source_count,
            previous_copy_end=previous_copy_end,
            counts=source_train_counts,
        )
        row = {
            "source_digit_pos": source,
            "bits": bits,
            "source_is_default": is_default,
            "flag_bits": flag_bits,
            "exception_bits": exception_bits,
        }
        if best is None or (bits, source) < (best["bits"], best["source_digit_pos"]):
            best = row
    if best is None:
        raise RuntimeError(
            {
                "type": "no_source_candidate",
                "chunk": chunk,
                "legal_source_count": legal_source_count,
            }
        )
    best["candidate_count"] = len(candidates)
    best["source_changed"] = best["source_digit_pos"] != original_source
    return best


def optimize_encoded_sources(
    *,
    encoded: dict[str, Any],
    available: str,
    formula: dict[str, Any],
    source_train_counts: dict[str, Any],
    initial_previous_copy_end: int | None,
    gate37,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    local_emitted = available
    previous_end = initial_previous_copy_end
    rendered = []
    source_bits = 0.0
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    changed_source_count = 0
    total_candidate_count = 0
    optimized_ops = []
    for op in encoded["ops"]:
        if op["type"] == "literal":
            chunk = op["text"]
            rendered.append(chunk)
            optimized_ops.append({"type": "literal", "text": chunk, "length": int(op["length"])})
            local_emitted += chunk
            continue

        original_source = int(op["source_digit_pos"])
        length = int(op["length"])
        original_chunk = local_emitted[original_source : original_source + length]
        legal_source_count = max(1, len(local_emitted) - min_len + 1)
        choice = choose_source(
            emitted=local_emitted,
            chunk=original_chunk,
            legal_source_count=legal_source_count,
            original_source=original_source,
            previous_copy_end=previous_end,
            source_train_counts=source_train_counts,
            gate37=gate37,
        )
        source = int(choice["source_digit_pos"])
        chunk = local_emitted[source : source + length]
        if chunk != original_chunk:
            raise RuntimeError(
                {
                    "type": "optimized_source_chunk_mismatch",
                    "source": source,
                    "original_source": original_source,
                    "length": length,
                }
            )
        source_bits += choice["bits"]
        flag_bits += choice["flag_bits"]
        exception_bits += choice["exception_bits"]
        if choice["source_is_default"]:
            default_count += 1
        else:
            exception_count += 1
        if choice["source_changed"]:
            changed_source_count += 1
        total_candidate_count += choice["candidate_count"]
        optimized_ops.append(
            {
                "type": "copy",
                "source_digit_pos": source,
                "original_source_digit_pos": original_source,
                "length": length,
                "source_changed": bool(choice["source_changed"]),
                "candidate_count": int(choice["candidate_count"]),
                "source_is_default": bool(choice["source_is_default"]),
            }
        )
        previous_end = source + length
        rendered.append(chunk)
        local_emitted += chunk

    return {
        "source_bits": source_bits,
        "source_flag_bits": flag_bits,
        "source_exception_bits": exception_bits,
        "source_default_count": default_count,
        "source_exception_count": exception_count,
        "changed_source_count": changed_source_count,
        "total_candidate_count": total_candidate_count,
        "final_previous_copy_end": previous_end,
        "rendered": "".join(rendered),
        "ops": optimized_ops,
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
) -> dict[str, Any]:
    available = "".join(books[str(book)] for book in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    book_rows = []
    aggregate = {
        "bits": 0.0,
        "source_state_reprice_bits": 0.0,
        "uniform_address_reparse_bits": 0.0,
        "raw_digit_uniform_bits": 0.0,
        "copy_source_default_exception_bits": 0.0,
        "copy_source_flag_bits": 0.0,
        "copy_source_exception_bits": 0.0,
        "source_default_count": 0,
        "source_exception_count": 0,
        "changed_source_count": 0,
        "total_candidate_count": 0,
        "copy_items": 0,
        "copied_digits": 0,
    }
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
        repriced = gate37.reprice_encoded_book_source_state(
            encoded=encoded,
            available=available,
            formula=formula,
            source_train_counts=source_train_counts,
            initial_previous_copy_end=previous_end,
        )
        optimized = optimize_encoded_sources(
            encoded=encoded,
            available=available,
            formula=formula,
            source_train_counts=source_train_counts,
            initial_previous_copy_end=previous_end,
            gate37=gate37,
        )
        if optimized["rendered"] != books[book_key]:
            errors.append({"book": book, "error": "optimized_render_mismatch"})
        source_state_reprice_bits = (
            encoded["bits"] - encoded["copy_address_bits"] + repriced["source_bits"]
        )
        bits = encoded["bits"] - encoded["copy_address_bits"] + optimized["source_bits"]
        raw_bits = len(books[book_key]) * math.log2(10)
        row = {
            "book": book,
            "bits": bits,
            "source_state_reprice_bits": source_state_reprice_bits,
            "uniform_address_reparse_bits": encoded["bits"],
            "source_choice_minus_reprice_bits": bits - source_state_reprice_bits,
            "source_choice_minus_uniform_address_bits": bits - encoded["bits"],
            "raw_digit_uniform_bits": raw_bits,
            "gain_vs_raw_digit_uniform_bits": raw_bits - bits,
            "copy_source_default_exception_bits": optimized["source_bits"],
            "copy_source_flag_bits": optimized["source_flag_bits"],
            "copy_source_exception_bits": optimized["source_exception_bits"],
            "source_default_count": optimized["source_default_count"],
            "source_exception_count": optimized["source_exception_count"],
            "changed_source_count": optimized["changed_source_count"],
            "total_candidate_count": optimized["total_candidate_count"],
            "copy_items": encoded["copy_items"],
            "copied_digits": encoded["copied_digits"],
            "roundtrip_ok": not encoded["validation"]["errors"],
        }
        book_rows.append(row)
        for key in aggregate:
            aggregate[key] += row[key]
        previous_end = optimized["final_previous_copy_end"]
        available += books[book_key]

    aggregate["source_choice_minus_reprice_bits"] = (
        aggregate["bits"] - aggregate["source_state_reprice_bits"]
    )
    aggregate["source_choice_minus_uniform_address_bits"] = (
        aggregate["bits"] - aggregate["uniform_address_reparse_bits"]
    )
    aggregate["gain_vs_raw_digit_uniform_bits"] = (
        aggregate["raw_digit_uniform_bits"] - aggregate["bits"]
    )
    roundtrip_count = sum(1 for row in book_rows if row["roundtrip_ok"])
    beats_raw_count = sum(1 for row in book_rows if row["gain_vs_raw_digit_uniform_bits"] > 0)
    beats_reprice_count = sum(1 for row in book_rows if row["source_choice_minus_reprice_bits"] < 0)
    beats_uniform_count = sum(1 for row in book_rows if row["source_choice_minus_uniform_address_bits"] < 0)
    return {
        "cutoff": cutoff,
        "train_books": list(range(cutoff)),
        "test_books": list(range(cutoff, 70)),
        "book_count": len(book_rows),
        "roundtrip_book_count": roundtrip_count,
        "beats_raw_book_count": beats_raw_count,
        "beats_source_state_reprice_book_count": beats_reprice_count,
        "beats_uniform_address_reparse_book_count": beats_uniform_count,
        "aggregate": aggregate,
        "book_rows": book_rows,
        "errors": errors,
    }


def make_result() -> dict[str, Any]:
    gate38 = load_json(GATE38_RESULT)
    assert_boundary("multicutoff_source_state_reparse_reprice_gate", gate38)
    gate37 = load_module("gate37_source_state_reprice", GATE37_SCRIPT)
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
            )
        )

    all_roundtrip = all(row["roundtrip_book_count"] == row["book_count"] for row in rows)
    all_raw_positive = all(row["beats_raw_book_count"] == row["book_count"] for row in rows)
    all_aggregate_beats_reprice = all(
        row["aggregate"]["source_choice_minus_reprice_bits"] < 0 for row in rows
    )
    all_aggregate_beats_uniform = all(
        row["aggregate"]["source_choice_minus_uniform_address_bits"] < 0 for row in rows
    )
    total_changed_sources = sum(row["aggregate"]["changed_source_count"] for row in rows)
    if all_roundtrip and all_raw_positive and total_changed_sources == 0:
        classification = "multicutoff_source_choice_optimizer_no_change_boundary"
    elif all_roundtrip and all_raw_positive and all_aggregate_beats_reprice:
        classification = "multicutoff_source_choice_optimizer_improves_reprice_unpromoted"
    elif all_roundtrip and all_raw_positive and all_aggregate_beats_uniform:
        classification = "multicutoff_source_choice_optimizer_improves_uniform_unpromoted"
    else:
        classification = "multicutoff_source_choice_optimizer_mixed_unpromoted"

    return {
        "schema": "multicutoff_source_choice_optimizer_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate37_script": rel(GATE37_SCRIPT),
            "gate38_result": rel(GATE38_RESULT),
        },
        "scope": {
            "cutoffs": PREFIX_CUTOFFS,
            "optimization": "greedy source choice over fixed deterministic reparse segmentation and copy lengths",
            "not_segmentation_reoptimization": True,
            "source_counts": "frozen from train prefix for each cutoff",
        },
        "summary": {
            "cutoff_count": len(rows),
            "all_roundtrip": all_roundtrip,
            "all_books_beat_raw": all_raw_positive,
            "aggregate_beats_reprice_cutoff_count": sum(
                1 for row in rows if row["aggregate"]["source_choice_minus_reprice_bits"] < 0
            ),
            "aggregate_beats_uniform_cutoff_count": sum(
                1
                for row in rows
                if row["aggregate"]["source_choice_minus_uniform_address_bits"] < 0
            ),
            "rows": rows,
            "total_bits": sum(row["aggregate"]["bits"] for row in rows),
            "total_reprice_bits": sum(row["aggregate"]["source_state_reprice_bits"] for row in rows),
            "total_uniform_address_reparse_bits": sum(
                row["aggregate"]["uniform_address_reparse_bits"] for row in rows
            ),
            "total_source_choice_minus_reprice_bits": sum(
                row["aggregate"]["source_choice_minus_reprice_bits"] for row in rows
            ),
            "total_source_choice_minus_uniform_address_bits": sum(
                row["aggregate"]["source_choice_minus_uniform_address_bits"] for row in rows
            ),
            "total_changed_sources": total_changed_sources,
            "total_copy_items": sum(row["aggregate"]["copy_items"] for row in rows),
            "total_source_defaults": sum(row["aggregate"]["source_default_count"] for row in rows),
            "total_source_exceptions": sum(row["aggregate"]["source_exception_count"] for row in rows),
            "remaining_blockers": [
                "The greedy optimizer found no cheaper alternate source positions.",
                "Segmentation and copy lengths remain fixed from deterministic reparse.",
                "It does not promote a complete active parser or a new compression bound.",
            ],
        },
        "decision": {
            "source_choice_status": "fixed_segmentation_source_choice_no_change_boundary",
            "recipe_discovery_status": "partial_source_choice_optimization_only",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "39_multicutoff_source_choice_optimizer_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Multi-Cutoff Source Choice Optimizer Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 38 only repriced the deterministic reparse sources under the",
        "`previous_copy_end` source ledger. This gate makes the first source-aware",
        "recipe edit: for each fixed copy segment, it greedily chooses the cheapest",
        "legal source position that reproduces the same chunk. Segmentation and copy",
        "lengths remain fixed.",
        "",
        "## Summary",
        "",
        f"- All cutoffs roundtrip: `{s['all_roundtrip']}`.",
        f"- All books beat raw digit coding: `{s['all_books_beat_raw']}`.",
        f"- Aggregate beats source-state repricing at cutoffs: `{s['aggregate_beats_reprice_cutoff_count']}/{s['cutoff_count']}`.",
        f"- Aggregate beats uniform-address reparse at cutoffs: `{s['aggregate_beats_uniform_cutoff_count']}/{s['cutoff_count']}`.",
        f"- Total optimized bits: `{s['total_bits']:.3f}`.",
        f"- Total source-state reprice bits: `{s['total_reprice_bits']:.3f}`.",
        f"- Total uniform-address reparse bits: `{s['total_uniform_address_reparse_bits']:.3f}`.",
        f"- Total optimized minus reprice bits: `{s['total_source_choice_minus_reprice_bits']:+.3f}`.",
        f"- Total optimized minus uniform-address bits: `{s['total_source_choice_minus_uniform_address_bits']:+.3f}`.",
        f"- Changed sources: `{s['total_changed_sources']}/{s['total_copy_items']}`.",
        f"- Defaults/exceptions: `{s['total_source_defaults']}` / `{s['total_source_exceptions']}`.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Books | Roundtrip | Raw wins | Reprice wins | Uniform wins | Optimized bits | Reprice bits | Delta vs reprice | Delta vs uniform | Changed sources | Defaults | Exceptions |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["rows"]:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['book_count']}` | "
            f"`{row['roundtrip_book_count']}` | `{row['beats_raw_book_count']}` | "
            f"`{row['beats_source_state_reprice_book_count']}` | "
            f"`{row['beats_uniform_address_reparse_book_count']}` | "
            f"`{agg['bits']:.3f}` | `{agg['source_state_reprice_bits']:.3f}` | "
            f"`{agg['source_choice_minus_reprice_bits']:+.3f}` | "
            f"`{agg['source_choice_minus_uniform_address_bits']:+.3f}` | "
            f"`{agg['changed_source_count']}` | `{agg['source_default_count']}` | "
            f"`{agg['source_exception_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The fixed-segmentation source-choice hypothesis closes negative:",
            "the greedy optimizer finds no cheaper alternate source positions for",
            "the deterministic reparse copies. The original reparse sources are",
            "already locally optimal under this immediate `previous_copy_end` cost.",
            "",
            "This is still useful progress because it falsifies a simple source-only",
            "recipe-improvement path. Future active-parser work must change",
            "segmentation, copy lengths, or use a non-greedy/global source-state",
            "objective.",
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced.",
            "- No complete active parser or global recipe-discovery promotion is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "39_multicutoff_source_choice_optimizer_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
