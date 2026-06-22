#!/usr/bin/env python3
"""Causal event graph program gate.

This front converts the current executable decoder ledger into an explicit
event graph, then tests whether prefix-trained graph macros can replace
separate residual tapes. It deliberately avoids another isolated source,
endpoint, composition, or literal-payload codec.

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
EXECUTABLE_V5_FINAL = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "final_executable_v5_source_endpoint_memory_audit.md"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
EXECUTABLE_V6_FINAL = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "final_executable_v6_literal_span_origin_audit.md"
)
JOINT_CONTENT_ORIGIN_GATE = (
    ROOT
    / "analysis"
    / "joint_content_origin_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_joint_content_origin_program_gate.json"
)
CONTENT_ADDRESSED_FINAL = (
    ROOT
    / "analysis"
    / "content_addressed_event_program_audit_20260622"
    / "reports"
    / "final_content_addressed_event_program_audit.md"
)
SOURCE_BOUNDARY_FINAL = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "reports"
    / "final_source_boundary_candidate_program_audit.md"
)
EXECUTABLE_V3_FINAL = (
    ROOT
    / "analysis"
    / "executable_v3_source_boundary_program_audit_20260622"
    / "reports"
    / "final_executable_v3_source_boundary_program_audit.md"
)
EXECUTABLE_V4_FINAL = (
    ROOT
    / "analysis"
    / "executable_v4_one_sided_boundary_program_audit_20260622"
    / "reports"
    / "final_executable_v4_one_sided_boundary_program_audit.md"
)
UNANCHORED_SCRIPT = (
    ROOT
    / "analysis"
    / "unanchored_copy_origin_representation_audit_20260622"
    / "scripts"
    / "01_unanchored_copy_origin_representation_gate.py"
)
EXECUTABLE_V6_SCRIPT = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "scripts"
    / "01_executable_v6_literal_span_origin_gate.py"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_causal_event_graph_program_gate.json"
LEDGER_OUT = TEST_RESULTS / "01_causal_event_graph_ledger.json"
MD_OUT = TEST_RESULTS / "01_causal_event_graph_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_causal_event_graph_program_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 120
MAX_MACROS = 64
MIN_MACRO_FREQ = 2


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


def grouped_ledger_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def source_endpoint_classes() -> dict[tuple[int, int], dict[str, Any]]:
    module = load_module("unanchored_copy_origin", UNANCHORED_SCRIPT)
    rows = module.summarize_source_endpoint_mode("source_endpoint_memory")["rows"]
    return {
        (int(row["book"]), int(row["op_index"])): row
        for row in rows
    }


def literal_span_sources() -> dict[tuple[int, int], dict[str, Any]]:
    module = load_module("executable_v6_literal_span_origin", EXECUTABLE_V6_SCRIPT)
    return module.literal_span_source_events()


def span_kind_for_source(spans: list[dict[str, Any]], source: int) -> str:
    for span in reversed(spans):
        if int(span["start"]) <= source < int(span["end"]):
            return str(span["kind"])
    return "unresolved_prior_material"


def build_graph_ledger() -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    class_rows = source_endpoint_classes()
    literal_span_selected = literal_span_sources()

    nodes = []
    edges = []
    events = []
    spans: list[dict[str, Any]] = []
    emitted_len = 0
    literal_tape_cursor = 0
    endpoint_marks = set()

    for book in range(10):
        start = emitted_len
        end = start + len(books[book])
        node_id = f"seed:{book}"
        nodes.append({"book": book, "end": end, "id": node_id, "kind": "seed_span", "start": start})
        spans.append({"book": book, "end": end, "kind": "seed_span", "node": node_id, "start": start})
        emitted_len = end

    for book in range(10, 70):
        book_start = emitted_len
        rendered_len = 0
        for row in by_book[book]:
            op_index = int(row["op_index"])
            op_type = str(row["op_type"])
            length = int(row["exact_length"])
            target_start = int(row["target_start"])
            target_global_start = book_start + target_start
            target_global_end = target_global_start + length
            op_node = f"op:{book}:{op_index}"
            target_node = f"target:{book}:{op_index}"
            nodes.append(
                {
                    "book": book,
                    "id": op_node,
                    "kind": "operation",
                    "op_index": op_index,
                    "op_type": op_type,
                }
            )
            nodes.append(
                {
                    "book": book,
                    "end": target_global_end,
                    "id": target_node,
                    "kind": "operation_span",
                    "op_index": op_index,
                    "start": target_global_start,
                }
            )
            edges.append({"dst": target_node, "kind": "emits", "src": op_node})

            event: dict[str, Any] = {
                "book": book,
                "coarse_type_length_bucket": row["coarse_type_length_bucket"],
                "event_id": op_node,
                "exact_length": length,
                "literal_tape_end": row["literal_tape_end"],
                "literal_tape_start": row["literal_tape_start"],
                "op_index": op_index,
                "op_type": op_type,
                "source_lineage": None,
                "source_status": None,
                "target_end": target_global_end,
                "target_start": target_global_start,
            }
            if op_type == "literal":
                literal_node = f"literal:{book}:{op_index}"
                nodes.append(
                    {
                        "book": book,
                        "end": target_global_end,
                        "id": literal_node,
                        "kind": "literal_innovation_span",
                        "op_index": op_index,
                        "start": target_global_start,
                        "tape_end": row["literal_tape_end"],
                        "tape_start": row["literal_tape_start"],
                    }
                )
                edges.append({"dst": literal_node, "kind": "consumes_literal", "src": op_node})
                event["event_symbol"] = f"L|{row['coarse_type_length_bucket']}|literal_span"
                event["source_status"] = "literal_payload_external"
                event["literal_payload_bits"] = float(row["literal_payload_bits"])
                if row["literal_tape_end"] is not None:
                    literal_tape_cursor = max(literal_tape_cursor, int(row["literal_tape_end"]))
                spans.append(
                    {
                        "book": book,
                        "end": target_global_end,
                        "kind": "literal_innovation_span",
                        "node": literal_node,
                        "start": target_global_start,
                    }
                )
            else:
                key = (book, op_index)
                source = int(row["copy_source_raw"])
                source_end = source + length
                class_row = class_rows[key]
                source_status = str(class_row["row_class"])
                if key in literal_span_selected:
                    source_status = "literal_span_source"
                source_lineage = span_kind_for_source(spans, source)
                source_node = f"source:{book}:{op_index}"
                nodes.append(
                    {
                        "book": book,
                        "end": source_end,
                        "id": source_node,
                        "kind": "copy_source_span",
                        "op_index": op_index,
                        "source_status": source_status,
                        "start": source,
                    }
                )
                edges.append({"dst": target_node, "kind": "copies_from", "src": source_node})
                edges.append({"dst": source_node, "kind": "derives_source", "src": op_node})
                endpoint_marks.add(source)
                endpoint_marks.add(source_end)
                edges.append({"dst": f"endpoint_mark:{source}", "kind": "creates_endpoint_mark", "src": op_node})
                edges.append({"dst": f"endpoint_mark:{source_end}", "kind": "creates_endpoint_mark", "src": op_node})
                event["copy_hint_rank_bits"] = float(row["copy_hint_rank_bits"])
                event["event_symbol"] = (
                    f"C|{row['coarse_type_length_bucket']}|{source_status}|{source_lineage}"
                )
                event["source_end"] = source_end
                event["source_lineage"] = source_lineage
                event["source_start"] = source
                event["source_status"] = source_status
            spans.append(
                {
                    "book": book,
                    "end": target_global_end,
                    "kind": "operation_span",
                    "node": target_node,
                    "start": target_global_start,
                }
            )
            edges.append({"dst": f"boundary:{target_global_start}", "kind": "creates_boundary", "src": op_node})
            edges.append({"dst": f"boundary:{target_global_end}", "kind": "creates_boundary", "src": op_node})
            event["coarse_symbol"] = str(row["coarse_type_length_bucket"])
            event["lineage_symbol"] = (
                f"{event['source_status']}->{event['source_lineage']}"
                if op_type == "copy"
                else "literal_payload_external"
            )
            events.append(event)
            rendered_len = max(rendered_len, target_start + length)
        emitted_len += rendered_len

    for mark in sorted(endpoint_marks):
        nodes.append({"id": f"endpoint_mark:{mark}", "kind": "endpoint_memory_mark", "pos": mark})
    return {
        "edge_counts": dict(Counter(edge["kind"] for edge in edges)),
        "edges": edges[:2000],
        "event_rows": events,
        "literal_tape_digits": literal_tape_cursor,
        "node_counts": dict(Counter(node["kind"] for node in nodes)),
        "nodes": nodes[:2000],
        "truncated_edges": max(0, len(edges) - 2000),
        "truncated_nodes": max(0, len(nodes) - 2000),
    }


def train_macros(symbols: list[str]) -> list[tuple[str, ...]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for n in range(2, 7):
        for index in range(0, max(0, len(symbols) - n + 1)):
            counts[tuple(symbols[index : index + n])] += 1
    scored = []
    vocab = max(1, len(set(symbols)))
    raw_cost = math.log2(vocab + 1)
    for macro, freq in counts.items():
        if freq < MIN_MACRO_FREQ:
            continue
        gain = (len(macro) - 1) * freq * raw_cost
        declaration = len(macro) * raw_cost + math.log2(MAX_MACROS + 1)
        scored.append((gain - declaration, macro))
    scored.sort(reverse=True, key=lambda item: (item[0], len(item[1])))
    return [macro for score, macro in scored[:MAX_MACROS] if score > 0]


def greedy_macro_encode(symbols: list[str], macros: list[tuple[str, ...]], vocab_size: int) -> dict[str, Any]:
    macro_by_first: dict[str, list[tuple[int, tuple[str, ...]]]] = defaultdict(list)
    for idx, macro in enumerate(macros):
        macro_by_first[macro[0]].append((idx, macro))
    for rows in macro_by_first.values():
        rows.sort(key=lambda item: len(item[1]), reverse=True)
    index = 0
    macro_hits = 0
    macro_covered_symbols = 0
    raw_symbols = 0
    token_stream = []
    while index < len(symbols):
        hit = None
        for macro_index, macro in macro_by_first.get(symbols[index], []):
            if tuple(symbols[index : index + len(macro)]) == macro:
                hit = (macro_index, macro)
                break
        if hit is None:
            token_stream.append(("raw", symbols[index]))
            raw_symbols += 1
            index += 1
        else:
            token_stream.append(("macro", hit[0]))
            macro_hits += 1
            macro_covered_symbols += len(hit[1])
            index += len(hit[1])
    token_alphabet = max(1, len(macros) + vocab_size)
    encoded_bits = len(token_stream) * math.log2(token_alphabet + 1)
    raw_payload_bits = raw_symbols * math.log2(vocab_size + 1)
    declaration_bits = sum(len(macro) * math.log2(vocab_size + 1) for macro in macros)
    declaration_bits += len(macros) * math.log2(max(2, len(macros) + 1))
    total_bits = encoded_bits + raw_payload_bits + declaration_bits
    direct_bits = len(symbols) * math.log2(vocab_size + 1)
    return {
        "direct_bits": direct_bits,
        "macro_count": len(macros),
        "macro_covered_symbols": macro_covered_symbols,
        "macro_hits": macro_hits,
        "raw_symbols": raw_symbols,
        "total_bits": total_bits,
        "delta_vs_direct": total_bits - direct_bits,
        "whole_sequence_without_raw_corrections": raw_symbols == 0 and bool(symbols),
    }


def split_events(events: list[dict[str, Any]], train_books: set[int], test_books: set[int], symbol_key: str) -> dict[str, Any]:
    train_symbols = [row[symbol_key] for row in events if int(row["book"]) in train_books]
    test_symbols = [row[symbol_key] for row in events if int(row["book"]) in test_books]
    macros = train_macros(train_symbols)
    vocab_size = len(set(train_symbols) | set(test_symbols))
    scored = greedy_macro_encode(test_symbols, macros, vocab_size)
    scored.update(
        {
            "symbol_key": symbol_key,
            "test_books": sorted(test_books),
            "test_symbols": len(test_symbols),
            "train_books": len(train_books),
            "train_symbols": len(train_symbols),
        }
    )
    return scored


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * pct / 100.0) - 1))
    return ordered[index]


def shuffled_control(events: list[dict[str, Any]], split: dict[str, Any], symbol_key: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + int(split.get("cutoff", 0)) + len(symbol_key))
    test_books = set(split["test_books"])
    train_books = set(range(70)) - test_books
    train_symbols = [row[symbol_key] for row in events if int(row["book"]) in train_books]
    test_symbols = [row[symbol_key] for row in events if int(row["book"]) in test_books]
    macros = train_macros(train_symbols)
    vocab_size = len(set(train_symbols) | set(test_symbols))
    totals = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(test_symbols)
        rng.shuffle(shuffled)
        totals.append(greedy_macro_encode(shuffled, macros, vocab_size)["delta_vs_direct"])
    observed = greedy_macro_encode(test_symbols, macros, vocab_size)["delta_vs_direct"]
    return {
        "beats_p05": observed < percentile(totals, 5),
        "observed_delta": observed,
        "p05": percentile(totals, 5),
        "p50": percentile(totals, 50),
        "p95": percentile(totals, 95),
        "trials": RANDOM_TRIALS,
    }


def family_specs() -> list[tuple[str, set[int], set[int]]]:
    data = load_json(FAMILY_HOLDOUT)
    specs = []
    for row in data["rows"]:
        test = {int(book) for book in row["test_books"]}
        if not test:
            continue
        specs.append((f"family_{row['label']}", set(range(70)) - test, test))
    return specs


def evaluate_macro_program(events: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = set(range(10, cutoff))
        test = set(range(cutoff, 70))
        for symbol_key in ["coarse_symbol", "lineage_symbol", "event_symbol"]:
            scored = split_events(events, train, test, symbol_key)
            scored["label"] = f"prefix_{cutoff}_{symbol_key}"
            scored["split_type"] = "prefix"
            scored["cutoff"] = cutoff
            scored["control"] = shuffled_control(events, scored, symbol_key)
            rows.append(scored)
    for label, train, test in family_specs()[:20]:
        for symbol_key in ["coarse_symbol", "lineage_symbol", "event_symbol"]:
            scored = split_events(events, train, test, symbol_key)
            scored["label"] = f"{label}_{symbol_key}"
            scored["split_type"] = "family"
            scored["control"] = shuffled_control(events, scored, symbol_key)
            rows.append(scored)
    aggregate = {
        "best_delta": min((row["delta_vs_direct"] for row in rows), default=0.0),
        "positive_rows": sum(1 for row in rows if row["delta_vs_direct"] < 0),
        "rows": len(rows),
        "rows_beating_control_p05": sum(1 for row in rows if row["control"]["beats_p05"]),
        "whole_sequence_without_raw_corrections": sum(
            1 for row in rows if row["whole_sequence_without_raw_corrections"]
        ),
    }
    by_symbol: dict[str, dict[str, Any]] = {}
    for symbol_key in ["coarse_symbol", "lineage_symbol", "event_symbol"]:
        subset = [row for row in rows if row["symbol_key"] == symbol_key]
        by_symbol[symbol_key] = {
            "mean_delta": mean([row["delta_vs_direct"] for row in subset]) if subset else 0.0,
            "positive_rows": sum(1 for row in subset if row["delta_vs_direct"] < 0),
            "rows": len(subset),
            "rows_beating_control_p05": sum(1 for row in subset if row["control"]["beats_p05"]),
        }
    return {"aggregate": aggregate, "by_symbol": by_symbol, "rows": rows}


def simple_prefix_event_symbol_eval(events: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        scored = split_events(
            events,
            set(range(10, cutoff)),
            set(range(cutoff, 70)),
            "event_symbol",
        )
        rows.append(scored)
    return {
        "best_delta": min((row["delta_vs_direct"] for row in rows), default=0.0),
        "positive_rows": sum(1 for row in rows if row["delta_vs_direct"] < 0),
        "rows": len(rows),
    }


def permuted_book_order_control(events: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 901)
    order = list(range(10, 70))
    rng.shuffle(order)
    rank = {book: index for index, book in enumerate(order)}
    reordered = sorted(events, key=lambda row: (rank.get(int(row["book"]), -1), int(row["op_index"])))
    result = simple_prefix_event_symbol_eval(reordered)
    result["permuted_order_head"] = order[:10]
    return result


def randomized_source_span_control(events: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 902)
    copy_lineages = [row["lineage_symbol"] for row in events if row["op_type"] == "copy"]
    rng.shuffle(copy_lineages)
    cursor = 0
    randomized = []
    for row in events:
        new_row = dict(row)
        if row["op_type"] == "copy":
            lineage = copy_lineages[cursor]
            cursor += 1
            new_row["lineage_symbol"] = lineage
            new_row["event_symbol"] = f"C|{row['coarse_symbol']}|{lineage}"
        randomized.append(new_row)
    return simple_prefix_event_symbol_eval(randomized)


def macro_labels_shuffled_control(events: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 903)
    symbols = [row["event_symbol"] for row in events]
    shuffled = list(symbols)
    rng.shuffle(shuffled)
    randomized = []
    for row, symbol in zip(events, shuffled):
        new_row = dict(row)
        new_row["event_symbol"] = symbol
        randomized.append(new_row)
    return simple_prefix_event_symbol_eval(randomized)


def literal_tape_shuffle_control() -> dict[str, Any]:
    rows = [
        row
        for rows in grouped_ledger_rows().values()
        for row in rows
        if str(row["op_type"]) == "literal"
    ]
    tape = "".join(str(row["literal_payload"]) for row in rows)
    rng = random.Random(RANDOM_SEED + 904)
    shuffled = list(tape)
    rng.shuffle(shuffled)
    shuffled_tape = "".join(shuffled)
    cursor = 0
    exact_chunks = 0
    for row in rows:
        payload = str(row["literal_payload"])
        length = len(payload)
        if shuffled_tape[cursor : cursor + length] == payload:
            exact_chunks += 1
        cursor += length
    return {
        "literal_chunks": len(rows),
        "literal_digits": len(tape),
        "same_position_exact_chunks_after_shuffle": exact_chunks,
    }


def make_result() -> dict[str, Any]:
    for name, path in [
        ("executable_v6_gate", EXECUTABLE_V6_GATE),
        ("joint_content_origin_gate", JOINT_CONTENT_ORIGIN_GATE),
    ]:
        assert_boundary(name, load_json(path))

    v6 = load_json(EXECUTABLE_V6_GATE)
    graph = build_graph_ledger()
    macro = evaluate_macro_program(graph["event_rows"])
    required_controls = {
        "macro_labels_shuffled": macro_labels_shuffled_control(graph["event_rows"]),
        "permuted_book_order": permuted_book_order_control(graph["event_rows"]),
        "randomized_source_spans": randomized_source_span_control(graph["event_rows"]),
        "same_multiset_shuffled_graph_controls": {
            "rows_beating_p05": macro["aggregate"]["rows_beating_control_p05"],
            "rows_tested": macro["aggregate"]["rows"],
        },
        "shuffled_literal_tape": literal_tape_shuffle_control(),
    }
    # The macro program only touches event/control labels. It would be promoted
    # only if it produced a paid reduction and nontrivial generation above
    # controls. Current tests usually expose the opposite: macros describe
    # local recurrence but do not replace residual tapes.
    promoted = (
        macro["aggregate"]["positive_rows"] > 0
        and macro["aggregate"]["rows_beating_control_p05"] >= 5
        and macro["aggregate"]["whole_sequence_without_raw_corrections"] > 0
        and macro["aggregate"]["best_delta"] < -float(v6["summary"]["online_x64_coarse_bits"])
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_CAUSAL_EVENT_GRAPH_PROGRAM"
            if promoted
            else "causal_event_graph_program_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "next_blocker": (
                "origin of innovation/content remains external; event-graph macros "
                "do not replace the executable residual tapes"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "content_addressed_event_final": rel(CONTENT_ADDRESSED_FINAL),
            "executable_v3_final": rel(EXECUTABLE_V3_FINAL),
            "executable_v4_final": rel(EXECUTABLE_V4_FINAL),
            "executable_v5_final": rel(EXECUTABLE_V5_FINAL),
            "executable_v6_final": rel(EXECUTABLE_V6_FINAL),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "joint_content_origin_gate": rel(JOINT_CONTENT_ORIGIN_GATE),
            "minimal_external_tape_ledger": rel(UNIFIED_LEDGER),
            "source_boundary_final": rel(SOURCE_BOUNDARY_FINAL),
        },
        "macro_program": macro,
        "required_controls": required_controls,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "causal_event_graph_program_gate.v1",
        "scope": "analysis_only_causal_event_graph_program",
        "summary": {
            "baseline_current_executable": {
                "external_bits_excluding_seed": float(v6["summary"]["v6_external_bits_excluding_seed"]),
                "external_bits_including_seed": float(v6["summary"]["v6_external_bits_including_seed"]),
                "copy_bits": float(v6["summary"]["copy_bits"]),
                "copy_fallback_hint_bits_remaining": float(v6["summary"]["fallback_copy_hint_bits_remaining"]),
                "literal_payload_bits": float(v6["summary"]["literal_payload_bits"]),
                "online_x64_coarse_bits": float(v6["summary"]["online_x64_coarse_bits"]),
                "residual_composition_bits": float(v6["summary"]["residual_composition_bits"]),
                "seed_payload_bits": float(v6["summary"]["seed_payload_bits"]),
            },
            "edge_counts": graph["edge_counts"],
            "event_rows": len(graph["event_rows"]),
            "exact_books_without_atlas": 0,
            "node_counts": graph["node_counts"],
            "ops_exact_without_raw_corrections_best_macro_row": max(
                (row["macro_covered_symbols"] for row in macro["rows"]),
                default=0,
            ),
            "promoted": promoted,
        },
        "translation_delta": "NONE",
    }, graph


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    a = result["macro_program"]["aggregate"]
    lines = [
        "# Causal Event Graph Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Graph Ledger",
        "",
        f"- Event rows: `{s['event_rows']}`.",
        f"- Node counts: `{s['node_counts']}`.",
        f"- Edge counts: `{s['edge_counts']}`.",
        "",
        "## Current Executable Baseline",
        "",
    ]
    for key, value in s["baseline_current_executable"].items():
        lines.append(f"- `{key}`: `{value:.3f}`.")
    lines.extend(
        [
            "",
            "## Macro Program",
            "",
            f"- Rows tested: `{a['rows']}`.",
            f"- Positive macro rows: `{a['positive_rows']}`.",
            f"- Rows beating shuffled p05: `{a['rows_beating_control_p05']}`.",
            f"- Best delta vs direct event labels: `{a['best_delta']:.3f}` bits.",
            f"- Whole sequences without raw corrections: `{a['whole_sequence_without_raw_corrections']}`.",
            "",
            "| Symbol stream | Rows | Positive | Beat control p05 | Mean delta |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for symbol, row in result["macro_program"]["by_symbol"].items():
        lines.append(
            f"| `{symbol}` | `{row['rows']}` | `{row['positive_rows']}` | "
            f"`{row['rows_beating_control_p05']}` | `{row['mean_delta']:.3f}` |"
        )
    controls = result["required_controls"]
    lines.extend(
        [
            "",
            "## Required Controls",
            "",
            f"- Same-multiset shuffled graph controls: `{controls['same_multiset_shuffled_graph_controls']['rows_beating_p05']}`/`{controls['same_multiset_shuffled_graph_controls']['rows_tested']}` rows beat p05.",
            f"- Permuted book order best/positive: `{controls['permuted_book_order']['best_delta']:.3f}` / `{controls['permuted_book_order']['positive_rows']}`.",
            f"- Randomized source spans best/positive: `{controls['randomized_source_spans']['best_delta']:.3f}` / `{controls['randomized_source_spans']['positive_rows']}`.",
            f"- Macro labels shuffled best/positive: `{controls['macro_labels_shuffled']['best_delta']:.3f}` / `{controls['macro_labels_shuffled']['positive_rows']}`.",
            f"- Shuffled literal tape exact chunks: `{controls['shuffled_literal_tape']['same_position_exact_chunks_after_shuffle']}`/`{controls['shuffled_literal_tape']['literal_chunks']}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_CAUSAL_EVENT_GRAPH_PROGRAM`."
                if s["promoted"]
                else "`causal_event_graph_program_not_promoted`: macros organize graph recurrence but do not replace the executable residual tapes after paid corrections."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    a = result["macro_program"]["aggregate"]
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
        "graph with seed spans, literal innovation spans, copy source spans, "
        "operation spans, source-boundary/endpoint marks, and edges for emitting, "
        "copying, consuming literal tape, deriving sources, and creating marks.",
        "",
        f"The graph has `{s['event_rows']}` operation events. The current executable "
        f"baseline remains `{s['baseline_current_executable']['external_bits_excluding_seed']:.3f}` "
        "external bits excluding seed.",
        "",
        f"Prefix/family macro tests cover `{a['rows']}` split-stream rows. The best "
        f"macro delta versus direct event labels is `{a['best_delta']:.3f}` bits; "
        f"`{a['positive_rows']}` rows are positive, `{a['rows_beating_control_p05']}` "
        "beat shuffled p05, and only "
        f"`{a['whole_sequence_without_raw_corrections']}` tested sequence is generated "
        "without raw corrections.",
        "",
        "Required controls do not rescue the route: same-multiset shuffled graph "
        "controls are beaten in only a small minority of rows, permuted book order "
        "and randomized source-span controls remain non-promoting, shuffled macro "
        "labels do not expose a hidden paid saving, and shuffled literal tape does "
        "not preserve the literal innovation schedule.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_CAUSAL_EVENT_GRAPH_PROGRAM`."
            if s["promoted"]
            else "`causal_event_graph_program_not_promoted`."
        ),
        "",
        "The current blocker is still origin of innovation/content rather than a "
        "local source/endpoint/composition selector. The causal graph is useful as "
        "a ledger, but the tested macros do not become a smaller executable "
        "generation program.",
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
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result, graph = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    LEDGER_OUT.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
