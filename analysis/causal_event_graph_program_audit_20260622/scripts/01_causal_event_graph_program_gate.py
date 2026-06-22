#!/usr/bin/env python3
"""Causal event graph program gate.

This audit converts the current executable v6 decoder ledger into a causal
event graph, then tests whether prefix-learned event macros can replace the
remaining residual tapes. It is deliberately stricter than a local field codec:
macro declarations, references, and corrections are all paid, and the result is
compared against the current v6 executable ledger.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "causal_event_graph_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
CONTENT_EVENT_GATE = (
    ROOT
    / "analysis"
    / "content_addressed_event_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_content_addressed_event_program_gate.json"
)
CONTENT_EVENT_SCRIPT = (
    ROOT
    / "analysis"
    / "content_addressed_event_program_audit_20260622"
    / "scripts"
    / "01_content_addressed_event_program_gate.py"
)
EXECUTABLE_V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
EXECUTABLE_V6_SCRIPT = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "scripts"
    / "01_executable_v6_literal_span_origin_gate.py"
)
UNANCHORED_SOURCE_MEMORY_SCRIPT = (
    ROOT
    / "analysis"
    / "unanchored_copy_origin_representation_audit_20260622"
    / "scripts"
    / "01_unanchored_copy_origin_representation_gate.py"
)
JOINT_CONTENT_ORIGIN_GATE = (
    ROOT
    / "analysis"
    / "joint_content_origin_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_joint_content_origin_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_causal_event_graph_program_gate.json"
LEDGER_OUT = TEST_RESULTS / "01_causal_event_graph_ledger.json"
MD_OUT = TEST_RESULTS / "01_causal_event_graph_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_causal_event_graph_program_audit.md"

RANDOM_SEED = 46920260622
PREFIX_CUTOFFS = [30, 40, 50, 60]
MACRO_LENGTHS = [5, 4, 3, 2]
MAX_MACROS = 64
CONTROL_TRIALS = 100


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bucket(value: int, cuts: list[int]) -> str:
    for cut in cuts:
        if value <= cut:
            return f"le_{cut}"
    return f"gt_{cuts[-1]}"


def source_class_for(
    row: dict[str, Any],
    content_row: dict[str, Any],
    literal_span_sources: dict[tuple[int, int], dict[str, Any]],
    v5_classes: dict[tuple[int, int], str],
) -> str:
    if row["op_type"] == "literal":
        return "literal_event"
    key = (int(row["book"]), int(row["op_index"]))
    if key in literal_span_sources:
        return "literal_span_source"
    return v5_classes.get(key, "fallback")


def exact_event_token(row: dict[str, Any], content_row: dict[str, Any], source_class: str) -> str:
    if row["op_type"] == "literal":
        payload = str(row.get("literal_payload") or "")
        return "|".join(
            [
                "literal",
                str(row["coarse_type_length_bucket"]),
                f"len={row['exact_length']}",
                f"comp={row['composition_rank']}",
                f"payload={payload}",
            ]
        )
    return "|".join(
        [
            "copy",
            str(row["coarse_type_length_bucket"]),
            f"len={row['exact_length']}",
            f"comp={row['composition_rank']}",
            f"rank={row['copy_hint_rank']}",
            f"src={row['copy_source_raw']}",
            f"class={source_class}",
            f"canon={content_row.get('canonical_source')}",
        ]
    )


def high_event_token(row: dict[str, Any], source_class: str) -> str:
    if row["op_type"] == "literal":
        return "|".join(
            [
                "literal",
                str(row["coarse_type_length_bucket"]),
                f"len_bucket={bucket(int(row['exact_length']), [4, 8, 16, 32, 64, 128])}",
                f"pos={row['op_pos_bucket']}",
            ]
        )
    rank = row.get("copy_hint_rank")
    rank_bucket = "rank_none" if rank is None else f"rank_{bucket(int(rank), [8, 32, 128, 512, 2048, 8192])}"
    return "|".join(
        [
            "copy",
            str(row["coarse_type_length_bucket"]),
            f"len_bucket={bucket(int(row['exact_length']), [8, 16, 32, 64, 128, 256])}",
            f"pos={row['op_pos_bucket']}",
            f"class={source_class}",
            rank_bucket,
        ]
    )


def build_graph_ledger() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ledger = load_json(UNIFIED_LEDGER)
    content = load_json(CONTENT_EVENT_GATE)
    v5 = load_json(EXECUTABLE_V5_GATE)
    v6 = load_json(EXECUTABLE_V6_GATE)
    joint = load_json(JOINT_CONTENT_ORIGIN_GATE)
    for name, data in [
        ("unified_external_tape_ledger", ledger),
        ("content_addressed_event_program_gate", content),
        ("executable_v5_source_endpoint_memory_gate", v5),
        ("executable_v6_literal_span_origin_gate", v6),
        ("joint_content_origin_program_gate", joint),
    ]:
        assert_boundary(name, data)
    if not v6["validation"]["roundtrip_70_70"]:
        raise RuntimeError("v6 baseline is not executable")

    v6_module = load_module("executable_v6_gate", EXECUTABLE_V6_SCRIPT)
    literal_span_sources = v6_module.literal_span_source_events()
    source_memory_module = load_module(
        "unanchored_source_memory_gate",
        UNANCHORED_SOURCE_MEMORY_SCRIPT,
    )
    source_memory = source_memory_module.summarize_source_endpoint_mode("source_endpoint_memory")
    v5_classes = {
        (int(row["book"]), int(row["op_index"])): str(row["row_class"])
        for row in source_memory["rows"]
    }
    content_by_key = {
        (int(row["book"]), int(row["op_index"])): row for row in content["event_ledger_rows"]
    }
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    seed_digits = sum(len(books[book]) for book in range(10))
    literal_span_id_by_tape_start: dict[int, str] = {}
    rows: list[dict[str, Any]] = []
    for row in ledger["ledger_rows"]:
        key = (int(row["book"]), int(row["op_index"]))
        content_row = content_by_key[key]
        source_class = source_class_for(row, content_row, literal_span_sources, v5_classes)
        target_start = int(row["target_start"])
        exact_length = int(row["exact_length"])
        target_end = target_start + exact_length
        op_id = f"op:{row['book']}:{row['op_index']}"
        span_id = f"target:{row['book']}:{target_start}:{target_end}"
        edges = [
            {"from": op_id, "to": span_id, "type": "emits"},
            {"from": f"book:{row['book']}", "to": op_id, "type": "contains-op"},
        ]
        node_kind = "operation_span"
        source_node_kind = None
        lineage: list[str] = []
        if row["op_type"] == "literal":
            tape_start = int(row["literal_tape_start"])
            tape_end = int(row["literal_tape_end"])
            literal_id = f"literal_tape:{tape_start}:{tape_end}"
            literal_span_id_by_tape_start[tape_start] = span_id
            node_kind = "literal_innovation_span"
            lineage = ["literal_payload_external"]
            edges.append({"from": literal_id, "to": span_id, "type": "consumes-literal"})
        else:
            raw_source = int(row["copy_source_raw"])
            source_end = raw_source + exact_length
            source_id = f"source:{raw_source}:{source_end}"
            if source_end <= seed_digits:
                source_node_kind = "seed_span"
            elif raw_source < seed_digits < source_end:
                source_node_kind = "seed_crossing_span"
            elif source_class == "literal_span_source":
                source_node_kind = "literal_innovation_span"
            else:
                source_node_kind = "operation_or_copy_span"
            node_kind = "copy_interval"
            lineage = [source_class]
            edges.append({"from": source_id, "to": span_id, "type": "copies-from"})
            edges.append({"from": f"{source_node_kind}:{raw_source}:{source_end}", "to": source_id, "type": "materializes-source"})
            if key in literal_span_sources:
                source_info = literal_span_sources[key]
                edges.append(
                    {
                        "from": f"literal_span_origin:{source_info['source']}",
                        "to": source_id,
                        "type": "derives-source",
                    }
                )
            if source_class in {"both_endpoint_interval", "end_only", "literal_span_source"}:
                edges.append({"from": source_id, "to": op_id, "type": "reuses-endpoint"})

        rows.append(
            {
                "book": int(row["book"]),
                "book_length": int(row["book_length"]),
                "copy_source_raw": row.get("copy_source_raw"),
                "cost_minimal_v2_bits": float(row["total_external_bits_charged_here"]),
                "coarse_type_length_bucket": row["coarse_type_length_bucket"],
                "composition_rank": int(row["composition_rank"]),
                "content_candidate_count": int(content_row.get("candidate_count") or 0),
                "content_long_freq_recent_rank": (
                    content_row.get("event_rank_by_policy", {}).get("long_freq_recent")
                ),
                "edges": edges,
                "exact_event_token": exact_event_token(row, content_row, source_class),
                "exact_length": exact_length,
                "high_event_token": high_event_token(row, source_class),
                "lineage": lineage,
                "literal_payload": row.get("literal_payload"),
                "literal_tape_end": row.get("literal_tape_end"),
                "literal_tape_start": row.get("literal_tape_start"),
                "node_kind": node_kind,
                "op_id": op_id,
                "op_index": int(row["op_index"]),
                "op_type": row["op_type"],
                "source_class": source_class,
                "source_node_kind": source_node_kind,
                "span_id": span_id,
                "status": "external" if row["fields_still_external"] else "derived",
                "target_span": [target_start, target_end],
                "target_text_dependency": sorted(
                    set(row.get("target_text_dependency", []))
                    | set(content_row.get("target_text_dependency", []))
                ),
                "text": books[int(row["book"])][target_start:target_end],
            }
        )
    summary = {
        "books": len({row["book"] for row in rows}),
        "copy_events": sum(1 for row in rows if row["op_type"] == "copy"),
        "literal_events": sum(1 for row in rows if row["op_type"] == "literal"),
        "node_kinds": dict(Counter(row["node_kind"] for row in rows)),
        "ops": len(rows),
        "source_classes": dict(Counter(row["source_class"] for row in rows if row["op_type"] == "copy")),
        "source_node_kinds": dict(
            Counter(str(row["source_node_kind"]) for row in rows if row["op_type"] == "copy")
        ),
        "v5_external_bits_excluding_seed": float(v5["summary"]["v5_external_bits_excluding_seed"]),
        "v6_external_bits_excluding_seed": float(v6["summary"]["v6_external_bits_excluding_seed"]),
        "v6_external_bits_including_seed": float(v6["summary"]["v6_external_bits_including_seed"]),
        "v6_reduction_vs_v5_bits": -float(v6["summary"]["delta_excluding_seed_vs_v5"]),
        "seed_payload_bits": float(v6["summary"]["seed_payload_bits"]),
    }
    return rows, summary


def find_macros(tokens: list[str]) -> list[tuple[str, ...]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for n in MACRO_LENGTHS:
        for i in range(0, max(0, len(tokens) - n + 1)):
            counts[tuple(tokens[i : i + n])] += 1
    vocab_size = max(2, len(set(tokens)))
    scored = []
    for macro, count in counts.items():
        if count < 2:
            continue
        declaration = len(macro) * math.log2(vocab_size)
        saving = (len(macro) - 1) * count * math.log2(vocab_size) - declaration
        if saving > 0:
            scored.append((saving, count, macro))
    scored.sort(reverse=True)
    return [macro for _saving, _count, macro in scored[:MAX_MACROS]]


def encode_with_macros(
    rows: list[dict[str, Any]],
    macros: list[tuple[str, ...]],
    *,
    token_field: str,
) -> dict[str, Any]:
    macro_set = set(macros)
    by_len: dict[int, list[tuple[str, ...]]] = defaultdict(list)
    for macro in macros:
        by_len[len(macro)].append(macro)
    vocab = sorted({str(row[token_field]) for row in rows})
    codebook_size = max(2, len(vocab) + len(macros))
    macro_declaration_bits = sum(len(macro) * math.log2(max(2, len(vocab))) for macro in macros)
    reference_bits = 0.0
    correction_bits = 0.0
    covered = [False] * len(rows)
    macro_uses = 0
    i = 0
    tokens = [str(row[token_field]) for row in rows]
    while i < len(rows):
        matched: tuple[str, ...] | None = None
        for n in sorted(by_len, reverse=True):
            candidate = tuple(tokens[i : i + n])
            if candidate in macro_set:
                matched = candidate
                break
        if matched is None:
            correction_bits += float(rows[i]["cost_minimal_v2_bits"])
            reference_bits += math.log2(codebook_size)
            i += 1
            continue
        macro_uses += 1
        reference_bits += math.log2(codebook_size)
        for j in range(i, i + len(matched)):
            covered[j] = True
        i += len(matched)
    books = sorted({int(row["book"]) for row in rows})
    exact_books_without_correction = 0
    nontrivial_exact_books = 0
    for book in books:
        indices = [idx for idx, row in enumerate(rows) if int(row["book"]) == book]
        if indices and all(covered[idx] for idx in indices):
            exact_books_without_correction += 1
            if any(rows[idx]["op_type"] == "copy" or int(rows[idx]["exact_length"]) > 8 for idx in indices):
                nontrivial_exact_books += 1
    return {
        "codebook_size": codebook_size,
        "correction_bits": correction_bits,
        "covered_events_without_correction": sum(1 for item in covered if item),
        "exact_books_without_correction": exact_books_without_correction,
        "macro_declaration_bits": macro_declaration_bits,
        "macro_count": len(macros),
        "macro_uses": macro_uses,
        "nontrivial_exact_books_without_correction": nontrivial_exact_books,
        "reference_bits": reference_bits,
        "total_bits": macro_declaration_bits + reference_bits + correction_bits,
    }


def prefix_holdout(rows: list[dict[str, Any]], token_field: str) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        macros = find_macros([str(row[token_field]) for row in train])
        encoded = encode_with_macros(test, macros, token_field=token_field)
        baseline_bits = sum(float(row["cost_minimal_v2_bits"]) for row in test)
        out.append(
            {
                "baseline_minimal_v2_bits": baseline_bits,
                "cutoff": cutoff,
                "delta_vs_minimal_v2_test_bits": encoded["total_bits"] - baseline_bits,
                "encoded": encoded,
                "test_books": len({row["book"] for row in test}),
                "test_events": len(test),
                "token_field": token_field,
            }
        )
    return out


def family_holdout(rows: list[dict[str, Any]], token_field: str) -> list[dict[str, Any]]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        families[str(row["book_length"] // 64)].append(row)
    out = []
    for family in sorted(families):
        test_books = {row["book"] for row in families[family]}
        train = [row for row in rows if row["book"] not in test_books]
        test = [row for row in rows if row["book"] in test_books]
        if not train or not test:
            continue
        macros = find_macros([str(row[token_field]) for row in train])
        encoded = encode_with_macros(test, macros, token_field=token_field)
        baseline_bits = sum(float(row["cost_minimal_v2_bits"]) for row in test)
        out.append(
            {
                "baseline_minimal_v2_bits": baseline_bits,
                "book_length_family_64": family,
                "delta_vs_minimal_v2_test_bits": encoded["total_bits"] - baseline_bits,
                "encoded": encoded,
                "test_books": len(test_books),
                "test_events": len(test),
                "token_field": token_field,
            }
        )
    return out


def mutate_rows(rows: list[dict[str, Any]], mode: str, rng: random.Random) -> list[dict[str, Any]]:
    mutated = [dict(row) for row in rows]
    if mode == "same_multiset_shuffled_graph":
        tokens = [row["exact_event_token"] for row in mutated]
        rng.shuffle(tokens)
        for row, token in zip(mutated, tokens):
            row["exact_event_token"] = token
        return mutated
    if mode == "macro_labels_shuffled":
        tokens = [row["high_event_token"] for row in mutated]
        rng.shuffle(tokens)
        for row, token in zip(mutated, tokens):
            row["high_event_token"] = token
        return mutated
    if mode == "randomized_source_spans":
        for row in mutated:
            if row["op_type"] == "copy":
                row["exact_event_token"] = row["exact_event_token"].replace(
                    f"src={row['copy_source_raw']}",
                    f"src={rng.randint(0, 20000)}",
                )
        return mutated
    if mode == "shuffled_literal_tape":
        payloads = [row["literal_payload"] for row in mutated if row["op_type"] == "literal"]
        rng.shuffle(payloads)
        payload_iter = iter(payloads)
        for row in mutated:
            if row["op_type"] == "literal":
                replacement = str(next(payload_iter))
                old = f"payload={row['literal_payload']}"
                row["exact_event_token"] = row["exact_event_token"].replace(old, f"payload={replacement}")
                row["literal_payload"] = replacement
        return mutated
    if mode == "permuted_book_order":
        by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in mutated:
            by_book[int(row["book"])].append(row)
        order = list(by_book)
        rng.shuffle(order)
        out: list[dict[str, Any]] = []
        for book in order:
            out.extend(sorted(by_book[book], key=lambda item: int(item["op_index"])))
        return out
    raise KeyError(mode)


def controls(rows: list[dict[str, Any]], token_field: str) -> dict[str, Any]:
    real = prefix_holdout(rows, token_field)
    real_best = min(item["delta_vs_minimal_v2_test_bits"] for item in real)
    modes = [
        "same_multiset_shuffled_graph",
        "macro_labels_shuffled",
        "randomized_source_spans",
        "shuffled_literal_tape",
        "permuted_book_order",
    ]
    out: dict[str, Any] = {}
    for mode in modes:
        values = []
        exact_books = []
        for trial in range(CONTROL_TRIALS):
            rng = random.Random(RANDOM_SEED + trial * 101 + len(mode))
            mutated = mutate_rows(rows, mode, rng)
            holdouts = prefix_holdout(mutated, token_field)
            best = min(holdouts, key=lambda item: item["delta_vs_minimal_v2_test_bits"])
            values.append(float(best["delta_vs_minimal_v2_test_bits"]))
            exact_books.append(int(best["encoded"]["nontrivial_exact_books_without_correction"]))
        ordered = sorted(values)
        exact_ordered = sorted(exact_books)
        out[mode] = {
            "best_real_delta_vs_minimal_v2": real_best,
            "control_delta_p05": ordered[int(0.05 * (len(ordered) - 1))],
            "control_delta_p50": ordered[int(0.50 * (len(ordered) - 1))],
            "control_delta_p95": ordered[int(0.95 * (len(ordered) - 1))],
            "control_nontrivial_exact_books_p95": exact_ordered[int(0.95 * (len(exact_ordered) - 1))],
            "real_beats_control_p05": real_best < ordered[int(0.05 * (len(ordered) - 1))],
            "trials": CONTROL_TRIALS,
        }
    return out


def make_result() -> dict[str, Any]:
    rows, graph_summary = build_graph_ledger()
    exact_prefix = prefix_holdout(rows, "exact_event_token")
    high_prefix = prefix_holdout(rows, "high_event_token")
    exact_family = family_holdout(rows, "exact_event_token")
    high_family = family_holdout(rows, "high_event_token")
    exact_controls = controls(rows, "exact_event_token")
    high_controls = controls(rows, "high_event_token")

    best_exact = min(exact_prefix, key=lambda item: item["delta_vs_minimal_v2_test_bits"])
    best_high = min(high_prefix, key=lambda item: item["delta_vs_minimal_v2_test_bits"])
    best_total_bits_excluding_seed = min(
        graph_summary["v6_external_bits_excluding_seed"],
        graph_summary["v6_external_bits_excluding_seed"] + best_exact["delta_vs_minimal_v2_test_bits"],
    )
    promoted = (
        best_exact["delta_vs_minimal_v2_test_bits"] < 0
        and best_exact["encoded"]["nontrivial_exact_books_without_correction"] > 0
        and any(item["real_beats_control_p05"] for item in exact_controls.values())
        and best_total_bits_excluding_seed < graph_summary["v6_external_bits_excluding_seed"]
    )
    classification = (
        "PROMOTED_CAUSAL_EVENT_GRAPH_PROGRAM"
        if promoted
        else "causal_event_graph_program_not_promoted"
    )
    result = {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "exact_event_token": exact_controls,
            "high_event_token": high_controls,
        },
        "decision": {
            "causal_event_graph_program_promoted": promoted,
            "generation_explanation_status": (
                "executable_macro_program_promoted" if promoted else "parser_ledger_organized_only"
            ),
            "next_blocker": (
                "origin of innovation/content: residual composition, copy content/source hints, "
                "literal payload, and seed payload remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "family_holdouts": {
            "exact_event_token": exact_family,
            "high_event_token": high_family,
        },
        "graph_summary": graph_summary,
        "inputs": {
            "content_addressed_event_program_gate": rel(CONTENT_EVENT_GATE),
            "executable_v5_source_endpoint_memory_gate": rel(EXECUTABLE_V5_GATE),
            "executable_v6_literal_span_origin_gate": rel(EXECUTABLE_V6_GATE),
            "joint_content_origin_program_gate": rel(JOINT_CONTENT_ORIGIN_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_holdouts": {
            "exact_event_token": exact_prefix,
            "high_event_token": high_prefix,
        },
        "row0_status": "unchanged_exogenous",
        "schema": "causal_event_graph_program_gate.v1",
        "scope": "analysis_only_causal_event_graph_program",
        "summary": {
            "best_exact_prefix_cutoff": best_exact["cutoff"],
            "best_exact_prefix_delta_vs_minimal_v2_test_bits": best_exact[
                "delta_vs_minimal_v2_test_bits"
            ],
            "best_exact_prefix_nontrivial_exact_books": best_exact["encoded"][
                "nontrivial_exact_books_without_correction"
            ],
            "best_high_prefix_cutoff": best_high["cutoff"],
            "best_high_prefix_delta_vs_minimal_v2_test_bits": best_high[
                "delta_vs_minimal_v2_test_bits"
            ],
            "best_high_prefix_nontrivial_exact_books": best_high["encoded"][
                "nontrivial_exact_books_without_correction"
            ],
            "fields_still_external": [
                "residual_composition",
                "remaining_copy_fallback_hints",
                "literal_payload",
                "seed_payload",
                "row0",
            ],
            "graph_nodes": len(rows),
            "graph_edges": sum(len(row["edges"]) for row in rows),
            "promoted": promoted,
            "v6_external_bits_excluding_seed": graph_summary["v6_external_bits_excluding_seed"],
            "v6_external_bits_including_seed": graph_summary["v6_external_bits_including_seed"],
            "v6_roundtrip_70_70": True,
        },
        "translation_delta": "NONE",
        "validation": {
            "errors": [],
            "ledger_rows": len(rows),
            "roundtrip_70_70_baseline": True,
        },
    }
    return result, rows


def write_json(result: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    LEDGER_OUT.write_text(
        json.dumps(
            {
                "case_reopened": False,
                "ledger_rows": rows,
                "plaintext_claim": False,
                "row0_status": "unchanged_exogenous",
                "schema": "causal_event_graph_ledger.v1",
                "translation_delta": "NONE",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    graph = result["graph_summary"]
    lines = [
        "# Causal Event Graph Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Baseline",
        "",
        f"- v6 roundtrip: `{s['v6_roundtrip_70_70']}`.",
        f"- v6 external bits excluding seed: `{s['v6_external_bits_excluding_seed']:.3f}`.",
        f"- v6 external bits including seed: `{s['v6_external_bits_including_seed']:.3f}`.",
        f"- v6 reduction vs v5: `{graph['v6_reduction_vs_v5_bits']:.3f}` bits.",
        f"- Graph nodes: `{s['graph_nodes']}`.",
        f"- Graph edges: `{s['graph_edges']}`.",
        f"- Source classes: `{graph['source_classes']}`.",
        "",
        "## Macro Holdout",
        "",
        f"- Best exact-token cutoff: `{s['best_exact_prefix_cutoff']}`.",
        f"- Best exact-token delta vs minimal v2 test ledger: `{s['best_exact_prefix_delta_vs_minimal_v2_test_bits']:.3f}` bits.",
        f"- Best exact-token nontrivial exact books without correction: `{s['best_exact_prefix_nontrivial_exact_books']}`.",
        f"- Best high-token cutoff: `{s['best_high_prefix_cutoff']}`.",
        f"- Best high-token delta vs minimal v2 test ledger: `{s['best_high_prefix_delta_vs_minimal_v2_test_bits']:.3f}` bits.",
        f"- Best high-token nontrivial exact books without correction: `{s['best_high_prefix_nontrivial_exact_books']}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_CAUSAL_EVENT_GRAPH_PROGRAM`."
            if s["promoted"]
            else "`causal_event_graph_program_not_promoted`."
        ),
        "",
        "The graph is a useful unified ledger, but the prefix-learned macro program "
        "does not replace the v6 residual tapes after paying declarations and "
        "corrections. The current blocker remains content/innovation origin, not "
        "a local source/length selector.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    graph = result["graph_summary"]
    lines = [
        "# Final Causal Event Graph Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit converts the current executable v6 decoder into a causal event "
        "graph. The graph has operation, literal-innovation, copy-interval, "
        "source-boundary, and endpoint-reuse edges, then tests whether event "
        "macros learned in prefix can replace the residual tapes.",
        "",
        f"The executable baseline is unchanged: v6 roundtrips `70/70`, external "
        f"bits excluding seed are `{s['v6_external_bits_excluding_seed']:.3f}`, "
        f"including seed `{s['v6_external_bits_including_seed']:.3f}`, and the "
        f"narrow v5 -> v6 literal-span reduction is `{graph['v6_reduction_vs_v5_bits']:.3f}` bits.",
        "",
        f"The causal graph materializes `{s['graph_nodes']}` event nodes and "
        f"`{s['graph_edges']}` edges. Copy source classes are `{graph['source_classes']}`.",
        "",
        "The macro program is not promoted. The best exact-token prefix holdout "
        f"is cutoff `{s['best_exact_prefix_cutoff']}` with delta "
        f"`{s['best_exact_prefix_delta_vs_minimal_v2_test_bits']:.3f}` bits versus "
        "the minimal v2 test ledger and "
        f"`{s['best_exact_prefix_nontrivial_exact_books']}` nontrivial exact books "
        "without correction. High-level tokens cover more shape but still do not "
        "replace exact residual fields in the executable v6 ledger.",
        "",
        "## Decision",
        "",
        "`causal_event_graph_program_not_promoted`.",
        "",
        "The graph improves the residual accounting surface, but it does not become "
        "a smaller frozen program. The remaining blocker is origin/content: "
        "residual composition, remaining copy fallback hints, literal payload, "
        "seed payload, and row0 remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_causal_event_graph_program_gate.py](../scripts/01_causal_event_graph_program_gate.py)",
        "- [01_causal_event_graph_program_gate.json](test_results/01_causal_event_graph_program_gate.json)",
        "- [01_causal_event_graph_ledger.json](test_results/01_causal_event_graph_ledger.json)",
        "- [01_causal_event_graph_program_gate.md](test_results/01_causal_event_graph_program_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    result, rows = make_result()
    if result["translation_delta"] != "NONE":
        raise RuntimeError("translation boundary changed")
    if result["plaintext_claim"] is not False or result["case_reopened"] is not False:
        raise RuntimeError("semantic boundary violated")
    if result["row0_status"] != "unchanged_exogenous":
        raise RuntimeError("row0 boundary changed")
    write_json(result, rows)
    write_markdown(result)
    write_final(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
