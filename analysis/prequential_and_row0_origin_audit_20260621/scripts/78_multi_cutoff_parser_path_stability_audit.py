from __future__ import annotations

import bisect
import hashlib
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

GATE76_SCRIPT = HERE / "scripts" / "76_cutoff60_sparse_suffix_parser_gate.py"
GATE77_SCRIPT = HERE / "scripts" / "77_multi_cutoff_sparse_suffix_parser_validation.py"
GATE77 = TEST_RESULTS / "77_multi_cutoff_sparse_suffix_parser_validation.json"

CUTOFFS = [10, 20, 35, 50, 60]


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


def compact_signature(ops: list[dict[str, Any]]) -> str:
    encoded = json.dumps(ops, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def sparse_parse_with_signature(
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
    transition_evaluations = 0
    start_time = time.perf_counter()
    final_state: tuple[int, str, int | None] | None = None

    while heap:
        cost, state = heapq.heappop(heap)
        if cost != distance.get(state):
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
                source_cost, is_default, _flag_bits, _exception_bits = source_bits(
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
                        ("copy", source_pos, length, forced, is_default),
                    )
                    heapq.heappush(heap, (next_cost, next_state))

    elapsed = time.perf_counter() - start_time
    if final_state is None:
        raise RuntimeError({"book": book, "type": "no_sparse_parse"})

    path: list[tuple[Any, ...]] = []
    state = final_state
    while state != start:
        previous_state, op = back[state]
        path.append(op)
        state = previous_state
    path.reverse()

    rendered: list[str] = []
    local_emitted = available
    position = 0
    signature_ops: list[dict[str, Any]] = []
    literal_runs = 0
    literal_digits = 0
    copy_items = 0
    copied_digits = 0
    for op in path:
        if op[0] == "literal":
            _kind, length, forced = op
            chunk = text[position : position + length]
            rendered.append(chunk)
            local_emitted += chunk
            signature_ops.append(
                {
                    "type": "literal",
                    "target_start": position,
                    "length": length,
                    "forced": bool(forced),
                }
            )
            position += length
            literal_runs += 1
            literal_digits += length
        elif op[0] == "copy":
            _kind, source_pos, length, forced, is_default = op
            chunk = local_emitted[source_pos : source_pos + length]
            rendered.append(chunk)
            local_emitted += chunk
            signature_ops.append(
                {
                    "type": "copy",
                    "target_start": position,
                    "source": source_pos,
                    "length": length,
                    "forced": bool(forced),
                    "source_default": bool(is_default),
                }
            )
            position += length
            copy_items += 1
            copied_digits += length
        else:
            raise RuntimeError(op)

    return {
        "book": book,
        "parser_bits": float(distance[final_state]),
        "roundtrip_ok": "".join(rendered) == text,
        "final_previous_copy_end": final_state[2],
        "transition_evaluations": transition_evaluations,
        "visited_state_count": len(distance),
        "elapsed_seconds": elapsed,
        "op_count": len(signature_ops),
        "copy_items": copy_items,
        "literal_runs": literal_runs,
        "copied_digits": copied_digits,
        "literal_digits": literal_digits,
        "signature": compact_signature(signature_ops),
        "signature_ops": signature_ops,
    }


def run_cutoff(cutoff: int, gate77_module) -> list[dict[str, Any]]:
    context = gate77_module.load_parser_context_for_cutoff(cutoff)
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    rows = []
    for book in range(cutoff, 70):
        row = sparse_parse_with_signature(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError({"cutoff": cutoff, "book": book, "type": "roundtrip"})
        row["cutoff"] = cutoff
        rows.append(row)
        available += books[str(book)]
        previous_end = row["final_previous_copy_end"]
    return rows


def summarize_book(book: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    signatures: dict[str, dict[str, Any]] = {}
    for row in rows:
        sig = row["signature"]
        signatures.setdefault(
            sig,
            {
                "signature": sig,
                "cutoffs": [],
                "op_count": row["op_count"],
                "copy_items": row["copy_items"],
                "literal_runs": row["literal_runs"],
                "copied_digits": row["copied_digits"],
                "literal_digits": row["literal_digits"],
                "parser_bits_by_cutoff": {},
                "example_ops": row["signature_ops"],
            },
        )
        signatures[sig]["cutoffs"].append(row["cutoff"])
        signatures[sig]["parser_bits_by_cutoff"][str(row["cutoff"])] = row[
            "parser_bits"
        ]
    variants = sorted(
        signatures.values(),
        key=lambda item: (-len(item["cutoffs"]), item["cutoffs"][0], item["signature"]),
    )
    all_cutoffs = sorted(row["cutoff"] for row in rows)
    stable = len(variants) == 1
    return {
        "book": book,
        "cutoffs_tested": all_cutoffs,
        "cutoff_count": len(all_cutoffs),
        "signature_count": len(variants),
        "stable_exact_path": stable,
        "dominant_signature_cutoff_count": len(variants[0]["cutoffs"]),
        "dominant_signature": variants[0]["signature"],
        "variant_summaries": [
            {
                "signature": item["signature"],
                "cutoffs": item["cutoffs"],
                "op_count": item["op_count"],
                "copy_items": item["copy_items"],
                "literal_runs": item["literal_runs"],
                "copied_digits": item["copied_digits"],
                "literal_digits": item["literal_digits"],
                "parser_bits_by_cutoff": item["parser_bits_by_cutoff"],
                "example_ops": item["example_ops"][:12],
                "example_ops_truncated": len(item["example_ops"]) > 12,
            }
            for item in variants
        ],
    }


def make_result() -> dict[str, Any]:
    gate77 = load_json(GATE77)
    assert_boundary("multi_cutoff_sparse_suffix_parser_validation", gate77)
    gate77_module = load_module("gate77_multi_cutoff_validation", GATE77_SCRIPT)
    start = time.perf_counter()
    rows = []
    for cutoff in CUTOFFS:
        rows.extend(run_cutoff(cutoff, gate77_module))
    elapsed = time.perf_counter() - start

    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(row["book"], []).append(row)
    book_rows = [summarize_book(book, by_book[book]) for book in sorted(by_book)]

    fully_tested = [row for row in book_rows if row["cutoff_count"] >= 2]
    stable_rows = [row for row in fully_tested if row["stable_exact_path"]]
    unstable_rows = [row for row in fully_tested if not row["stable_exact_path"]]
    max_signature_count = max(row["signature_count"] for row in fully_tested)
    most_unstable = sorted(
        unstable_rows,
        key=lambda row: (-row["signature_count"], row["book"]),
    )[:10]
    total_evaluations = len(rows)
    classification = (
        "multi_cutoff_parser_paths_partially_stable"
        if stable_rows and unstable_rows
        else (
            "multi_cutoff_parser_paths_fully_stable"
            if stable_rows
            else "multi_cutoff_parser_paths_unstable"
        )
    )
    return {
        "schema": "multi_cutoff_parser_path_stability_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate77_validation": rel(GATE77),
            "gate77_context_loader": rel(GATE77_SCRIPT),
            "gate76_sparse_parser_reference": rel(GATE76_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "cutoffs": CUTOFFS,
            "exact_path_signature_fields": [
                "type",
                "target_start",
                "source",
                "length",
                "forced",
                "source_default",
            ],
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "total_parser_evaluations": total_evaluations,
            "book_count_with_multiple_cutoffs": len(fully_tested),
            "stable_exact_path_book_count": len(stable_rows),
            "unstable_exact_path_book_count": len(unstable_rows),
            "stable_exact_path_fraction": len(stable_rows) / len(fully_tested),
            "max_signature_count_per_book": max_signature_count,
            "total_unique_book_signatures": sum(row["signature_count"] for row in fully_tested),
            "total_transition_evaluations": sum(
                row["transition_evaluations"] for row in rows
            ),
            "total_visited_states": sum(row["visited_state_count"] for row in rows),
            "elapsed_seconds": elapsed,
            "most_unstable_books": [
                {
                    "book": row["book"],
                    "cutoffs_tested": row["cutoffs_tested"],
                    "signature_count": row["signature_count"],
                    "dominant_signature_cutoffs": row["variant_summaries"][0][
                        "cutoffs"
                    ],
                    "variant_cutoffs": [
                        item["cutoffs"] for item in row["variant_summaries"]
                    ],
                }
                for row in most_unstable
            ],
            "book_rows": book_rows,
            "interpretation": (
                "The sparse parser is executable and predictive across cutoffs, "
                "but exact operation paths are only partially stable under "
                "different frozen prefixes. Stable books support a reusable "
                "mechanism; unstable books identify where the current objective "
                "still depends on learned stream weights and tie-breaking rather "
                "than a prefix-invariant authorial recipe."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "path_stability_partial_not_final",
            "generation_explanation_status": "parser_mechanism_supported_but_path_instability_remains",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "78_multi_cutoff_parser_path_stability_audit.json"
    md_path = TEST_RESULTS / "78_multi_cutoff_parser_path_stability_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Multi-Cutoff Parser Path Stability Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 77 showed that sparse source/length parsing roundtrips every",
        "tested suffix across cutoffs. This gate asks whether the exact parser",
        "paths are stable for the same book when the frozen training prefix",
        "changes.",
        "",
        "## Summary",
        "",
        f"- Parser evaluations replayed: `{s['total_parser_evaluations']}`.",
        f"- Books with multiple cutoff views: `{s['book_count_with_multiple_cutoffs']}`.",
        f"- Stable exact-path books: `{s['stable_exact_path_book_count']}`.",
        f"- Unstable exact-path books: `{s['unstable_exact_path_book_count']}`.",
        f"- Stable exact-path fraction: `{s['stable_exact_path_fraction']:.3f}`.",
        f"- Max signatures for one book: `{s['max_signature_count_per_book']}`.",
        f"- Unique book signatures across tested books: `{s['total_unique_book_signatures']}`.",
        f"- Total transition evaluations: `{s['total_transition_evaluations']}`.",
        f"- Total visited states: `{s['total_visited_states']}`.",
        f"- Elapsed wall time: `{s['elapsed_seconds']:.3f}` seconds.",
        "",
        "## Most Unstable Books",
        "",
        "| Book | Cutoffs | Signatures | Dominant cutoffs | Variant cutoffs |",
        "|---:|---|---:|---|---|",
    ]
    for row in s["most_unstable_books"]:
        lines.append(
            "| {book} | `{cutoffs_tested}` | {signature_count} | `{dominant_signature_cutoffs}` | `{variant_cutoffs}` |".format(
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
            "- No corpus-wide formula promotion is introduced.",
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
