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
GATE37_SCRIPT = HERE / "scripts" / "37_cutoff60_source_state_reparse_prototype_gate.py"
GATE73_SCRIPT = HERE / "scripts" / "73_book_local_source_length_parser_probe.py"
GATE72 = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"
GATE73 = TEST_RESULTS / "73_book_local_source_length_parser_probe.json"
GATE74 = TEST_RESULTS / "74_sparse_hard_book_source_length_parser_gate.json"
GATE75 = TEST_RESULTS / "75_post_parser_row0_compatibility_audit.json"

CUTOFF = 60
TARGET_BOOKS = list(range(60, 70))


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


def load_parser_context() -> dict[str, Any]:
    gate73 = load_module("gate73_book_local_parser_probe", GATE73_SCRIPT)
    context = gate73.load_parser_context()
    context["gate73"] = gate73
    context["gate37"] = load_module("gate37_source_state_reparse", GATE37_SCRIPT)
    return context


def same_policy_reprice_bits(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
) -> dict[str, Any]:
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    text = context["books"][str(book)]
    encoded = audit126.encode_book_frozen_reparse(
        book=str(book),
        text=text,
        available=available,
        formula=formula,
        train_counts=context["train_counts"],
    )
    repriced = gate37.reprice_encoded_book_source_state(
        encoded=encoded,
        available=available,
        formula=formula,
        source_train_counts=context["source_train_counts"],
        initial_previous_copy_end=initial_previous_copy_end,
    )
    bits = float(encoded["bits"]) - float(encoded["copy_address_bits"]) + float(
        repriced["source_bits"]
    )
    return {
        "bits": bits,
        "final_previous_copy_end": repriced["final_previous_copy_end"],
        "roundtrip_ok": repriced["rendered"] == text,
    }


def sparse_source_length_parse(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
) -> dict[str, Any]:
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    copy_prefixes = context["copy_prefixes"]
    text = context["books"][str(book)]
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

    start = (0, "BOS", initial_previous_copy_end)
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

    rendered_text = "".join(rendered)
    roundtrip_ok = rendered_text == text
    raw_bits = len(text) * math.log2(10)
    return {
        "book": book,
        "book_digits": len(text),
        "available_digits_before": len(available),
        "initial_previous_copy_end": initial_previous_copy_end,
        "final_previous_copy_end": final_state[2],
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


def run_suffix(context: dict[str, Any]) -> list[dict[str, Any]]:
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(CUTOFF))
    previous_end = gate37.previous_copy_end_before(formula, CUTOFF)
    rows = []
    for book in TARGET_BOOKS:
        same_policy = same_policy_reprice_bits(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        row = sparse_source_length_parse(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        row["same_policy_reprice_bits"] = same_policy["bits"]
        row["same_policy_roundtrip_ok"] = same_policy["roundtrip_ok"]
        row["same_policy_final_previous_copy_end"] = same_policy[
            "final_previous_copy_end"
        ]
        row["parser_minus_same_policy_reprice_bits"] = (
            row["parser_bits"] - same_policy["bits"]
        )
        rows.append(row)
        if not row["roundtrip_ok"]:
            raise RuntimeError({"book": book, "type": "roundtrip_failed"})
        available += books[str(book)]
        previous_end = row["final_previous_copy_end"]
    return rows


def make_result() -> dict[str, Any]:
    gate72 = load_json(GATE72)
    gate73 = load_json(GATE73)
    gate74 = load_json(GATE74)
    gate75 = load_json(GATE75)
    for name, data in [
        ("final_source_length_parser_feasibility", gate72),
        ("book_local_source_length_parser_probe", gate73),
        ("sparse_hard_book_source_length_parser", gate74),
        ("post_parser_row0_compatibility", gate75),
    ]:
        assert_boundary(name, data)

    context = load_parser_context()
    start = time.perf_counter()
    rows = run_suffix(context)
    elapsed = time.perf_counter() - start
    all_roundtrip = all(row["roundtrip_ok"] for row in rows)
    all_same_policy_roundtrip = all(row["same_policy_roundtrip_ok"] for row in rows)
    all_raw_positive = all(row["gain_vs_raw_digit_uniform_bits"] > 0 for row in rows)
    parser_better_count = sum(
        1 for row in rows if row["parser_minus_same_policy_reprice_bits"] < -1e-9
    )
    parser_tie_count = sum(
        1
        for row in rows
        if abs(row["parser_minus_same_policy_reprice_bits"]) <= 1e-9
    )
    parser_worse_count = sum(
        1 for row in rows if row["parser_minus_same_policy_reprice_bits"] > 1e-9
    )
    classification = (
        "cutoff60_sparse_suffix_source_length_parser_roundtrips"
        if all_roundtrip and all_same_policy_roundtrip
        else "cutoff60_sparse_suffix_source_length_parser_mixed"
    )
    return {
        "schema": "cutoff60_sparse_suffix_source_length_parser_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate37_parser_helpers": rel(GATE37_SCRIPT),
            "gate73_context_loader": rel(GATE73_SCRIPT),
            "gate72_feasibility": rel(GATE72),
            "gate73_book_local_probe": rel(GATE73),
            "gate74_sparse_hard_book": rel(GATE74),
            "gate75_row0_compatibility": rel(GATE75),
        },
        "scope": {
            "analysis_only": True,
            "cutoff": CUTOFF,
            "target_books": TARGET_BOOKS,
            "sequential_previous_end_carried_between_books": True,
            "train_counts_frozen_at_cutoff": CUTOFF,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "target_book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["roundtrip_ok"]),
            "same_policy_roundtrip_book_count": sum(
                1 for row in rows if row["same_policy_roundtrip_ok"]
            ),
            "raw_positive_book_count": sum(
                1 for row in rows if row["gain_vs_raw_digit_uniform_bits"] > 0
            ),
            "parser_better_than_same_policy_count": parser_better_count,
            "parser_tie_same_policy_count": parser_tie_count,
            "parser_worse_than_same_policy_count": parser_worse_count,
            "total_elapsed_seconds": elapsed,
            "total_book_elapsed_seconds": sum(row["elapsed_seconds"] for row in rows),
            "total_parser_bits": sum(row["parser_bits"] for row in rows),
            "total_same_policy_reprice_bits": sum(
                row["same_policy_reprice_bits"] for row in rows
            ),
            "total_parser_minus_same_policy_reprice_bits": sum(
                row["parser_minus_same_policy_reprice_bits"] for row in rows
            ),
            "total_raw_digit_uniform_bits": sum(
                row["raw_digit_uniform_bits"] for row in rows
            ),
            "total_gain_vs_raw_digit_uniform_bits": sum(
                row["gain_vs_raw_digit_uniform_bits"] for row in rows
            ),
            "total_transition_evaluations": sum(
                row["transition_evaluations"] for row in rows
            ),
            "total_visited_states": sum(row["visited_state_count"] for row in rows),
            "max_transition_book": max(rows, key=lambda row: row["transition_evaluations"])[
                "book"
            ],
            "max_transition_evaluations": max(
                row["transition_evaluations"] for row in rows
            ),
            "book_rows": rows,
            "interpretation": (
                "Sparse Dijkstra now executes the full cutoff-60 held-out suffix "
                "with previous-copy-end state carried between books. This is a "
                "real parser implementation step, but not a new compression bound "
                "or final authorial method because the train counts remain fixed "
                "at one cutoff and the result is still a local suffix gate."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "cutoff60_suffix_sparse_parser_executable",
            "generation_explanation_status": "parser_implementation_progress_not_corpus_wide_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "76_cutoff60_sparse_suffix_parser_gate.json"
    md_path = TEST_RESULTS / "76_cutoff60_sparse_suffix_parser_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Cutoff-60 Sparse Suffix Source/Length Parser Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 74 proved sparse Dijkstra on the cutoff-60 hard book `66`.",
        "This gate runs the same sparse source/length parser across the full",
        "cutoff-60 suffix, carrying `previous_copy_end` from each parsed book",
        "into the next book.",
        "",
        "## Summary",
        "",
        f"- Books parsed: `{s['target_book_count']}` (`{TARGET_BOOKS[0]}..{TARGET_BOOKS[-1]}`).",
        f"- Roundtrip books: `{s['roundtrip_book_count']}/{s['target_book_count']}`.",
        f"- Same-policy roundtrip books: `{s['same_policy_roundtrip_book_count']}/{s['target_book_count']}`.",
        f"- Books beating raw digit uniform: `{s['raw_positive_book_count']}/{s['target_book_count']}`.",
        f"- Total parser bits: `{s['total_parser_bits']:.6f}`.",
        f"- Total same-policy reprice bits: `{s['total_same_policy_reprice_bits']:.6f}`.",
        f"- Parser minus same-policy reprice: `{s['total_parser_minus_same_policy_reprice_bits']:+.6f}` bits.",
        f"- Total raw-uniform gain: `{s['total_gain_vs_raw_digit_uniform_bits']:.3f}` bits.",
        f"- Parser better/tie/worse than same policy: `{s['parser_better_than_same_policy_count']}` / `{s['parser_tie_same_policy_count']}` / `{s['parser_worse_than_same_policy_count']}`.",
        f"- Total transition evaluations: `{s['total_transition_evaluations']}`.",
        f"- Total visited states: `{s['total_visited_states']}`.",
        f"- Hardest parsed book by transitions: `{s['max_transition_book']}` (`{s['max_transition_evaluations']}` transitions).",
        f"- Elapsed wall time: `{s['total_elapsed_seconds']:.3f}` seconds.",
        "",
        "## Book Rows",
        "",
        "| Book | Digits | Parser bits | Same-policy | Delta | Raw gain | Ops | Copies | Literals | Transitions | States | Prev end in->out | Seconds |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in s["book_rows"]:
        lines.append(
            "| {book} | {book_digits} | {parser_bits:.3f} | {same_policy_reprice_bits:.3f} | {parser_minus_same_policy_reprice_bits:+.3f} | {gain_vs_raw_digit_uniform_bits:.3f} | {op_count} | {copy_items} | {literal_runs} | {transition_evaluations} | {visited_state_count} | `{initial_previous_copy_end}` -> `{final_previous_copy_end}` | {elapsed_seconds:.3f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No corpus-wide parser or recipe-discovery promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
