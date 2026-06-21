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

GATE82_SCRIPT = HERE / "scripts" / "82_component_neutralized_path_stability_gate.py"
GATE82 = TEST_RESULTS / "82_component_neutralized_path_stability_gate.json"
GATE83 = TEST_RESULTS / "83_component_neutralized_residual_tradeoff_audit.json"

BASE_MODE = "uniform_copy_length_and_source_exception"
PAYLOAD_MODE = "uniform_copy_length_source_exception_and_literal_payload"


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


def sparse_parse_literal_payload_uniform(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
) -> dict[str, Any]:
    gate82 = context["gate82"]
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    copy_prefixes = context["copy_prefixes"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]
    n = len(text)

    matches = audit126.precompute_matches(text, available, min_len)
    copy_positions = {pos for pos, row in enumerate(matches) if row}
    literal_endpoints = sorted(copy_positions | {n})
    copy_context = audit126.copy_context_key(book)

    source_cache: dict[tuple[int, int, int | None], tuple[float, bool, float, float]] = {}
    item_cache: dict[tuple[bool, str], float] = {}
    literal_length_cache: dict[int, float] = {}

    def source_bits(
        source: int,
        legal_source_count: int,
        previous_end: int | None,
    ) -> tuple[float, bool, float, float]:
        key = (source, legal_source_count, previous_end)
        if key not in source_cache:
            source_cache[key] = gate82.uniform_source_bits(
                source=source,
                legal_source_count=legal_source_count,
                previous_copy_end=previous_end,
                counts=source_train_counts,
                uniform_flag=False,
            )
        return source_cache[key]

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
                add = length * math.log2(10)
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
                    + math.log2(symbol_count)
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

    if final_state is None:
        raise RuntimeError({"book": book, "type": "no_literal_payload_uniform_parse"})

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
        "cost_mode": PAYLOAD_MODE,
        "parser_bits": float(distance[final_state]),
        "roundtrip_ok": "".join(rendered) == text,
        "final_previous_copy_end": final_state[2],
        "transition_evaluations": transition_evaluations,
        "visited_state_count": len(distance),
        "op_count": len(signature_ops),
        "copy_items": copy_items,
        "literal_runs": literal_runs,
        "copied_digits": copied_digits,
        "literal_digits": literal_digits,
        "raw_digit_uniform_bits": len(text) * math.log2(10),
        "signature": compact_signature(signature_ops),
        "signature_ops": signature_ops,
    }


def run_cutoff(cutoff: int, gate77_module, gate82_module) -> list[dict[str, Any]]:
    context = gate77_module.load_parser_context_for_cutoff(cutoff)
    context["gate82"] = gate82_module
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    rows = []
    for book in range(cutoff, 70):
        row = sparse_parse_literal_payload_uniform(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError({"cutoff": cutoff, "book": book})
        row["cutoff"] = cutoff
        rows.append(row)
        available += books[str(book)]
        previous_end = row["final_previous_copy_end"]
    return rows


def summarize_book(book: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    signatures: dict[str, dict[str, Any]] = {}
    for row in rows:
        signatures.setdefault(row["signature"], {"cutoffs": [], "signature": row["signature"]})
        signatures[row["signature"]]["cutoffs"].append(int(row["cutoff"]))
    variants = sorted(
        signatures.values(),
        key=lambda item: (-len(item["cutoffs"]), item["cutoffs"][0], item["signature"]),
    )
    return {
        "book": book,
        "cutoff_count": len(rows),
        "signature_count": len(variants),
        "stable_exact_path": len(variants) == 1,
        "variant_cutoffs": [variant["cutoffs"] for variant in variants],
    }


def summarize_payload_mode(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    book_rows = [summarize_book(book, by_book[book]) for book in sorted(by_book)]
    fully_tested = [row for row in book_rows if row["cutoff_count"] >= 2]
    stable_rows = [row for row in fully_tested if row["stable_exact_path"]]
    unstable_rows = [row for row in fully_tested if not row["stable_exact_path"]]
    return {
        "cost_mode": PAYLOAD_MODE,
        "total_parser_evaluations": len(rows),
        "roundtrip_book_evaluations": sum(1 for row in rows if row["roundtrip_ok"]),
        "raw_positive_book_evaluations": sum(
            1 for row in rows if row["parser_bits"] < row["raw_digit_uniform_bits"]
        ),
        "book_count_with_multiple_cutoffs": len(fully_tested),
        "stable_exact_path_book_count": len(stable_rows),
        "unstable_exact_path_book_count": len(unstable_rows),
        "stable_exact_path_fraction": len(stable_rows) / len(fully_tested),
        "max_signature_count_per_book": max(row["signature_count"] for row in fully_tested),
        "total_unique_book_signatures": sum(row["signature_count"] for row in fully_tested),
        "total_parser_bits": sum(row["parser_bits"] for row in rows),
        "total_raw_digit_uniform_bits": sum(row["raw_digit_uniform_bits"] for row in rows),
        "total_transition_evaluations": sum(row["transition_evaluations"] for row in rows),
        "unstable_books": [
            {
                "book": row["book"],
                "signature_count": row["signature_count"],
                "variant_cutoffs": row["variant_cutoffs"],
            }
            for row in unstable_rows
        ],
        "book_rows": book_rows,
    }


def mode_summary(gate82: dict[str, Any], mode: str) -> dict[str, Any]:
    return next(row for row in gate82["summary"]["mode_summaries"] if row["cost_mode"] == mode)


def make_result() -> dict[str, Any]:
    gate82 = load_json(GATE82)
    gate83 = load_json(GATE83)
    assert_boundary("component_neutralized_path_stability", gate82)
    assert_boundary("component_neutralized_residual_tradeoff", gate83)
    gate82_module = load_module("gate82_component_neutralized", GATE82_SCRIPT)
    gate77_module = gate82_module.load_module(
        "gate77_multi_cutoff_validation_for_gate84",
        gate82_module.GATE77_SCRIPT,
    )

    start = time.perf_counter()
    rows = []
    for cutoff in gate77_module.CUTOFFS:
        rows.extend(run_cutoff(cutoff, gate77_module, gate82_module))
    elapsed = time.perf_counter() - start

    active = mode_summary(gate82, "active_learned")
    base = mode_summary(gate82, BASE_MODE)
    payload = summarize_payload_mode(rows)
    payload["stable_book_delta_vs_base"] = (
        payload["stable_exact_path_book_count"] - base["stable_exact_path_book_count"]
    )
    payload["total_parser_bits_delta_vs_base"] = (
        payload["total_parser_bits"] - base["total_parser_bits"]
    )
    payload["total_parser_bits_delta_vs_active"] = (
        payload["total_parser_bits"] - active["total_parser_bits"]
    )
    payload["raw_positive_delta_vs_base"] = (
        payload["raw_positive_book_evaluations"] - base["raw_positive_book_evaluations"]
    )
    base_unstable = {int(row["book"]) for row in base["unstable_books"]}
    payload_unstable = {int(row["book"]) for row in payload["unstable_books"]}
    resolved_vs_base = sorted(base_unstable - payload_unstable)
    introduced_vs_base = sorted(payload_unstable - base_unstable)
    persistent_vs_base = sorted(base_unstable & payload_unstable)
    improves_stability = payload["stable_exact_path_book_count"] > base[
        "stable_exact_path_book_count"
    ]
    classification = (
        "literal_payload_neutralization_improves_residual_stability"
        if improves_stability
        else "literal_payload_neutralization_not_promoted"
    )
    return {
        "schema": "residual_literal_payload_neutralization_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate82_component_neutralized_path_stability": rel(GATE82),
            "gate83_residual_tradeoff": rel(GATE83),
            "gate82_replay_script": rel(GATE82_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "base_mode": BASE_MODE,
            "payload_mode": PAYLOAD_MODE,
            "uniform_literal_payload_cost": "digit_uniform_log2_10",
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "base_stable_exact_path_book_count": base["stable_exact_path_book_count"],
            "base_unstable_books": sorted(base_unstable),
            "payload_mode_summary": payload,
            "resolved_vs_base_books": resolved_vs_base,
            "persistent_vs_base_books": persistent_vs_base,
            "introduced_vs_base_books": introduced_vs_base,
            "interpretation": (
                "Uniform literal-payload cost tests whether the remaining "
                "neutralized-parser residuals are caused by learned payload "
                "pressure. Promotion would require improved global path "
                "stability without introducing a worse residual frontier."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": classification,
            "generation_explanation_status": "literal_payload_neutralization_tested_for_residuals",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "84_residual_literal_payload_neutralization_gate.json"
    md_path = TEST_RESULTS / "84_residual_literal_payload_neutralization_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    payload = s["payload_mode_summary"]
    lines = [
        "# Residual Literal-Payload Neutralization Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 83 localized the best neutralized parser residuals to books `26`",
        "and `34`. This gate adds uniform literal-payload cost on top of the",
        "uniform copy-length/source-exception mode to test whether learned",
        "payload pressure is the remaining instability driver.",
        "",
        "## Summary",
        "",
        f"- Base stable exact-path books: `{s['base_stable_exact_path_book_count']}`.",
        f"- Payload-neutralized stable exact-path books: `{payload['stable_exact_path_book_count']}`.",
        f"- Stable delta vs base: `{payload['stable_book_delta_vs_base']}`.",
        f"- Payload-mode unstable books: `{[row['book'] for row in payload['unstable_books']]}`.",
        f"- Resolved vs base: `{s['resolved_vs_base_books']}`.",
        f"- Persistent vs base: `{s['persistent_vs_base_books']}`.",
        f"- Introduced vs base: `{s['introduced_vs_base_books']}`.",
        f"- Parser-bit delta vs base: `{payload['total_parser_bits_delta_vs_base']:.6f}`.",
        f"- Raw-positive evaluations: `{payload['raw_positive_book_evaluations']}/175`.",
        "",
        "## Decision",
        "",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No corpus-wide formula promotion is introduced.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
