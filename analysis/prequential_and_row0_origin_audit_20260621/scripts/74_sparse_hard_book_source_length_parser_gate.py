from __future__ import annotations

import bisect
import heapq
import importlib.util
import json
import math
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
GATE73_SCRIPT = HERE / "scripts" / "73_book_local_source_length_parser_probe.py"
GATE72 = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"
GATE73 = TEST_RESULTS / "73_book_local_source_length_parser_probe.json"

HARD_BOOK = 66
CUTOFF = 60


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
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
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def sparse_source_length_parse(
    *,
    context: dict[str, Any],
    book: int,
) -> dict[str, Any]:
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    books = context["books"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    copy_prefixes = context["copy_prefixes"]
    text = books[str(book)]
    available = "".join(books[str(index)] for index in range(book))
    initial_previous_end = gate37.previous_copy_end_before(formula, book)
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    payload_model = formula["policy"]["literal_payload_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]
    n = len(text)

    matches = audit126.precompute_matches(text, available, min_len)
    copy_positions = {pos for pos, row in enumerate(matches) if row}
    literal_endpoints = sorted(copy_positions | {n})
    payload_prefix = audit126.literal_payload_prefix_costs(
        text=text,
        emitted_before_book=available,
        payload_counts=train_counts["payload"],
        order=int(payload_model["order"]),
        alpha=float(payload_model["alpha"]),
    )
    copy_context = audit126.copy_context_key(book)

    source_cache: dict[tuple[int, int, int | None], tuple[float, bool, float, float]] = {}
    length_cache: dict[tuple[int, int], float] = {}
    item_cache: dict[tuple[bool, str], float] = {}
    literal_length_cache: dict[int, float] = {}

    def source_bits(
        source: int,
        legal_source_count: int,
        previous_end: int | None,
    ) -> tuple[float, bool, float, float]:
        key = (source, legal_source_count, previous_end)
        if key not in source_cache:
            source_cache[key] = gate37.source_default_exception_bits(
                source=source,
                legal_source_count=legal_source_count,
                previous_copy_end=previous_end,
                counts=source_train_counts,
            )
        return source_cache[key]

    def copy_length_bits(length_index: int, symbol_count: int) -> float:
        key = (length_index, symbol_count)
        if key not in length_cache:
            length_cache[key] = gate37.fast_copy_length_bits(
                counts=train_counts["copy"],
                prefixes=copy_prefixes,
                context=copy_context,
                length_index=length_index,
                symbol_count=symbol_count,
                alpha=int(copy_model["alpha"]),
            )
        return length_cache[key]

    def item_bits(forced: bool, item_type: str) -> float:
        key = (forced, item_type)
        if key not in item_cache:
            item_cache[key] = audit126.item_bits_for_choice(
                forced=forced,
                item_type=item_type,
                book_int=book,
                item_model=item_model,
                item_counts=train_counts["item"],
            )
        return item_cache[key]

    def literal_length_bits(length: int) -> float:
        if length not in literal_length_cache:
            literal_length_cache[length] = audit126.length_bits(
                length + 1,
                literal_length_model,
            )
        return literal_length_cache[length]

    start = (0, "BOS", initial_previous_end)
    heap: list[tuple[float, tuple[int, str, int | None]]] = [(0.0, start)]
    distance: dict[tuple[int, str, int | None], float] = {start: 0.0}
    back: dict[
        tuple[int, str, int | None],
        tuple[tuple[int, str, int | None], tuple[Any, ...]],
    ] = {}
    heap_pops = 0
    heap_pushes = 0
    transition_evaluations = 0
    stale_pops = 0
    start_time = time.perf_counter()
    final_state: tuple[int, str, int | None] | None = None

    while heap:
        cost, state = heapq.heappop(heap)
        heap_pops += 1
        if cost != distance.get(state):
            stale_pops += 1
            continue
        pos, previous_item, previous_end = state
        if pos == n:
            final_state = state
            break

        remaining = n - pos
        if previous_item != "literal":
            literal_forced = remaining < min_len
            if literal_forced:
                literal_lengths = [remaining]
            else:
                index = bisect.bisect_right(literal_endpoints, pos)
                literal_lengths = [end - pos for end in literal_endpoints[index:]]
            for length in literal_lengths:
                if length <= 0:
                    continue
                next_pos = pos + length
                add = payload_prefix[next_pos] - payload_prefix[pos]
                if not literal_forced:
                    add += item_bits(False, "literal") + literal_length_bits(length)
                next_state = (next_pos, "literal", previous_end)
                next_cost = cost + add
                transition_evaluations += 1
                if next_cost < distance.get(next_state, float("inf")):
                    distance[next_state] = next_cost
                    back[next_state] = (state, ("literal", length, literal_forced))
                    heapq.heappush(heap, (next_cost, next_state))
                    heap_pushes += 1

        if remaining >= min_len:
            for source_pos, length, length_index in matches[pos]:
                target_digit_global = len(available) + pos
                legal_source_count = max(1, target_digit_global - min_len + 1)
                if source_pos >= legal_source_count:
                    continue
                max_length = min(remaining, target_digit_global - source_pos)
                symbol_count = max_length - min_len + 1
                if symbol_count <= 0 or length_index >= symbol_count:
                    continue
                source_cost, is_default, flag_bits, exception_bits = source_bits(
                    source_pos,
                    legal_source_count,
                    previous_end,
                )
                if not math.isfinite(source_cost):
                    continue
                forced = previous_item == "literal"
                add = (
                    item_bits(forced, "copy")
                    + source_cost
                    + copy_length_bits(length_index, symbol_count)
                )
                next_state = (pos + length, "copy", source_pos + length)
                next_cost = cost + add
                transition_evaluations += 1
                if next_cost < distance.get(next_state, float("inf")):
                    distance[next_state] = next_cost
                    back[next_state] = (
                        state,
                        (
                            "copy",
                            source_pos,
                            length,
                            forced,
                            is_default,
                            flag_bits,
                            exception_bits,
                        ),
                    )
                    heapq.heappush(heap, (next_cost, next_state))
                    heap_pushes += 1

    elapsed = time.perf_counter() - start_time
    if final_state is None:
        raise RuntimeError({"book": book, "type": "no_sparse_parse"})

    ops: list[tuple[Any, ...]] = []
    state = final_state
    while state != start:
        previous_state, op = back[state]
        ops.append(op)
        state = previous_state
    ops.reverse()

    rendered: list[str] = []
    local_emitted = available
    position = 0
    totals = {
        "literal_runs": 0,
        "literal_digits": 0,
        "copy_items": 0,
        "copied_digits": 0,
        "source_default_count": 0,
        "source_exception_count": 0,
    }
    for op in ops:
        if op[0] == "literal":
            _kind, length, _forced = op
            chunk = text[position : position + length]
            rendered.append(chunk)
            local_emitted += chunk
            position += length
            totals["literal_runs"] += 1
            totals["literal_digits"] += length
        elif op[0] == "copy":
            _kind, source_pos, length, _forced, is_default, _flag_bits, _exception_bits = op
            chunk = local_emitted[source_pos : source_pos + length]
            rendered.append(chunk)
            local_emitted += chunk
            position += length
            totals["copy_items"] += 1
            totals["copied_digits"] += length
            if is_default:
                totals["source_default_count"] += 1
            else:
                totals["source_exception_count"] += 1
        else:
            raise RuntimeError(op)
    roundtrip_ok = "".join(rendered) == text
    raw_bits = len(text) * math.log2(10)
    return {
        "book": book,
        "book_digits": len(text),
        "elapsed_seconds": elapsed,
        "parser_bits": float(distance[final_state]),
        "raw_digit_uniform_bits": raw_bits,
        "gain_vs_raw_digit_uniform_bits": raw_bits - float(distance[final_state]),
        "roundtrip_ok": roundtrip_ok,
        "op_count": len(ops),
        "heap_pops": heap_pops,
        "stale_heap_pops": stale_pops,
        "heap_pushes": heap_pushes,
        "visited_state_count": len(distance),
        "transition_evaluations": transition_evaluations,
        "source_cache_entries": len(source_cache),
        "copy_length_cache_entries": len(length_cache),
        "item_cache_entries": len(item_cache),
        "literal_length_cache_entries": len(literal_length_cache),
        **totals,
    }


def make_result() -> dict[str, Any]:
    gate72 = load_json(GATE72)
    gate73 = load_json(GATE73)
    assert_boundary("final_source_length_parser_feasibility_audit", gate72)
    assert_boundary("book_local_source_length_parser_probe", gate73)
    gate73_module = load_module("gate73_book_local_parser_probe", GATE73_SCRIPT)
    context = gate73_module.load_parser_context()
    row = sparse_source_length_parse(context=context, book=HARD_BOOK)
    hard_proxy = next(
        item
        for item in gate72["book_rows_by_cutoff"][str(CUTOFF)]
        if int(item["book"]) == HARD_BOOK
    )
    transition_reduction_factor = (
        hard_proxy["copy_transition_proxy"] / row["transition_evaluations"]
    )
    classification = (
        "sparse_hard_book_source_length_parser_roundtrips"
        if row["roundtrip_ok"]
        else "sparse_hard_book_source_length_parser_failed"
    )
    return {
        "schema": "sparse_hard_book_source_length_parser_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate72_feasibility": rel(GATE72),
            "gate73_book_local_probe": rel(GATE73),
            "gate73_context_loader": rel(GATE73_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "cutoff": CUTOFF,
            "hard_book": HARD_BOOK,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_row": row,
            "gate72_transition_proxy": hard_proxy["copy_transition_proxy"],
            "gate72_end_state_proxy": hard_proxy["end_state_proxy"],
            "transition_reduction_factor_vs_proxy": transition_reduction_factor,
            "raw_positive": row["gain_vs_raw_digit_uniform_bits"] > 0,
            "interpretation": (
                "Sparse Dijkstra over reachable states turns the cutoff-60 hard "
                "book from a transition-proxy blocker into an executable exact "
                "book-local parser. This is implementation progress for the "
                "source/length parser, not a formula promotion."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "hard_book_66_sparse_parser_executable",
            "generation_explanation_status": "parser_implementation_progress_not_bound_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "74_sparse_hard_book_source_length_parser_gate.json"
    md_path = TEST_RESULTS / "74_sparse_hard_book_source_length_parser_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    row = s["book_row"]
    lines = [
        "# Sparse Hard-Book Source/Length Parser Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 73 left book `66` as the immediate cutoff-60 hard case. This gate",
        "switches the parser from dense dynamic programming over the full",
        "previous-end domain to sparse Dijkstra over actually reachable states,",
        "with source and length costs cached.",
        "",
        "## Result",
        "",
        f"- Book: `{row['book']}`.",
        f"- Digits: `{row['book_digits']}`.",
        f"- Roundtrip: `{row['roundtrip_ok']}`.",
        f"- Parser bits: `{row['parser_bits']:.6f}`.",
        f"- Gain versus raw digit uniform: `{row['gain_vs_raw_digit_uniform_bits']:.3f}` bits.",
        f"- Ops: `{row['op_count']}`.",
        f"- Copy/literal ops: `{row['copy_items']}` / `{row['literal_runs']}`.",
        f"- Transition evaluations: `{row['transition_evaluations']}`.",
        f"- Gate-72 transition proxy: `{s['gate72_transition_proxy']}`.",
        f"- Transition reduction vs proxy: `{s['transition_reduction_factor_vs_proxy']:.1f}x`.",
        f"- Visited states: `{row['visited_state_count']}`.",
        f"- Heap pops/pushes: `{row['heap_pops']}` / `{row['heap_pushes']}`.",
        f"- Cache entries source/length/item/literal-length: `{row['source_cache_entries']}` / `{row['copy_length_cache_entries']}` / `{row['item_cache_entries']}` / `{row['literal_length_cache_entries']}`.",
        f"- Elapsed: `{row['elapsed_seconds']:.3f}` seconds.",
        "",
        "## Decision",
        "",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No parser or recipe-discovery promotion is introduced.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
