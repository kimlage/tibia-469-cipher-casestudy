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

GATE77_SCRIPT = HERE / "scripts" / "77_multi_cutoff_sparse_suffix_parser_validation.py"
GATE78 = TEST_RESULTS / "78_multi_cutoff_parser_path_stability_audit.json"
GATE81 = TEST_RESULTS / "81_boundary_instability_cost_decomposition_gate.json"

COST_MODES = [
    "active_learned",
    "uniform_copy_length",
    "uniform_source_exception",
    "uniform_copy_length_and_source_exception",
    "uniform_copy_length_and_full_source",
]


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


def uniform_source_bits(
    *,
    source: int,
    legal_source_count: int,
    previous_copy_end: int | None,
    counts: dict[str, Any],
    uniform_flag: bool,
) -> tuple[float, bool, float, float]:
    default = (
        previous_copy_end
        if previous_copy_end is not None and previous_copy_end < legal_source_count
        else 0
    )
    is_default = source == default
    if uniform_flag:
        flag_bits = 1.0
    else:
        flag_bucket = counts["flag"]
        flag_probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits = -math.log2(flag_probability)
    if is_default:
        return flag_bits, True, flag_bits, 0.0
    if not 0 <= source < legal_source_count:
        return float("inf"), False, flag_bits, float("inf")
    alphabet_size = legal_source_count - (
        1 if 0 <= default < legal_source_count else 0
    )
    if alphabet_size <= 0:
        return float("inf"), False, flag_bits, float("inf")
    return flag_bits + math.log2(alphabet_size), False, flag_bits, math.log2(alphabet_size)


def sparse_parse_mode(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
    cost_mode: str,
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

    neutralize_source_exception = cost_mode in {
        "uniform_source_exception",
        "uniform_copy_length_and_source_exception",
        "uniform_copy_length_and_full_source",
    }
    neutralize_source_flag = cost_mode == "uniform_copy_length_and_full_source"
    neutralize_copy_length = cost_mode in {
        "uniform_copy_length",
        "uniform_copy_length_and_source_exception",
        "uniform_copy_length_and_full_source",
    }

    def source_bits(
        source: int,
        legal_source_count: int,
        previous_end: int | None,
    ) -> tuple[float, bool, float, float]:
        key = (source, legal_source_count, previous_end)
        if key not in source_cache:
            if neutralize_source_exception or neutralize_source_flag:
                source_cache[key] = uniform_source_bits(
                    source=source,
                    legal_source_count=legal_source_count,
                    previous_copy_end=previous_end,
                    counts=source_train_counts,
                    uniform_flag=neutralize_source_flag,
                )
            else:
                source_cache[key] = gate37.source_default_exception_bits(
                    source=source,
                    legal_source_count=legal_source_count,
                    previous_copy_end=previous_end,
                    counts=source_train_counts,
                )
        return source_cache[key]

    def copy_length_bits(length_index: int, symbol_count: int) -> float:
        if neutralize_copy_length:
            return math.log2(symbol_count)
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

    if final_state is None:
        raise RuntimeError(
            {"book": book, "cost_mode": cost_mode, "type": "no_sparse_parse"}
        )

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
        "cost_mode": cost_mode,
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


def run_cutoff(cutoff: int, gate77_module, *, cost_mode: str) -> list[dict[str, Any]]:
    context = gate77_module.load_parser_context_for_cutoff(cutoff)
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    rows = []
    for book in range(cutoff, 70):
        row = sparse_parse_mode(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
            cost_mode=cost_mode,
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError(
                {"cutoff": cutoff, "book": book, "cost_mode": cost_mode}
            )
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
            },
        )
        signatures[sig]["cutoffs"].append(row["cutoff"])
    variants = sorted(
        signatures.values(),
        key=lambda item: (-len(item["cutoffs"]), item["cutoffs"][0], item["signature"]),
    )
    all_cutoffs = sorted(row["cutoff"] for row in rows)
    return {
        "book": book,
        "cutoffs_tested": all_cutoffs,
        "cutoff_count": len(all_cutoffs),
        "signature_count": len(variants),
        "stable_exact_path": len(variants) == 1,
        "variant_cutoffs": [variant["cutoffs"] for variant in variants],
    }


def summarize_mode(cost_mode: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    book_rows = [summarize_book(book, by_book[book]) for book in sorted(by_book)]
    fully_tested = [row for row in book_rows if row["cutoff_count"] >= 2]
    stable_rows = [row for row in fully_tested if row["stable_exact_path"]]
    unstable_rows = [row for row in fully_tested if not row["stable_exact_path"]]
    return {
        "cost_mode": cost_mode,
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


def make_result() -> dict[str, Any]:
    gate78 = load_json(GATE78)
    gate81 = load_json(GATE81)
    assert_boundary("multi_cutoff_parser_path_stability", gate78)
    assert_boundary("boundary_instability_cost_decomposition", gate81)
    gate77_module = load_module("gate77_multi_cutoff_validation", GATE77_SCRIPT)

    start = time.perf_counter()
    mode_rows = {}
    mode_summaries = []
    for cost_mode in COST_MODES:
        rows = []
        for cutoff in gate77_module.CUTOFFS:
            rows.extend(run_cutoff(cutoff, gate77_module, cost_mode=cost_mode))
        mode_rows[cost_mode] = rows
        mode_summaries.append(summarize_mode(cost_mode, rows))
    elapsed = time.perf_counter() - start

    active = next(row for row in mode_summaries if row["cost_mode"] == "active_learned")
    for row in mode_summaries:
        row["stable_book_delta_vs_active"] = (
            row["stable_exact_path_book_count"]
            - active["stable_exact_path_book_count"]
        )
        row["total_parser_bits_delta_vs_active"] = (
            row["total_parser_bits"] - active["total_parser_bits"]
        )
        row["raw_positive_delta_vs_active"] = (
            row["raw_positive_book_evaluations"]
            - active["raw_positive_book_evaluations"]
        )

    best_stability = max(
        mode_summaries,
        key=lambda row: (
            row["stable_exact_path_book_count"],
            -row["total_parser_bits"],
            row["cost_mode"],
        ),
    )
    improves_stability = (
        best_stability["stable_exact_path_book_count"]
        > active["stable_exact_path_book_count"]
    )
    classification = (
        "component_neutralization_improves_path_stability"
        if improves_stability
        else "component_neutralization_does_not_improve_path_stability"
    )
    return {
        "schema": "component_neutralized_path_stability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate78_path_stability": rel(GATE78),
            "gate81_cost_decomposition": rel(GATE81),
            "gate77_context_loader": rel(GATE77_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "cutoffs": gate77_module.CUTOFFS,
            "cost_modes": COST_MODES,
            "component_neutralization_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "active_stable_exact_path_book_count": active[
                "stable_exact_path_book_count"
            ],
            "best_stability_mode": best_stability["cost_mode"],
            "best_stability_book_count": best_stability[
                "stable_exact_path_book_count"
            ],
            "best_stability_delta_vs_active": best_stability[
                "stable_book_delta_vs_active"
            ],
            "mode_summaries": mode_summaries,
            "interpretation": (
                "Uniformizing the learned copy-length/source-exception cost "
                "components tests whether path instability is an artifact of "
                "overfit component priors. A mode can be structurally "
                "interesting only if it improves exact multi-cutoff path "
                "stability without being treated as a compression-bound "
                "promotion."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": classification,
            "generation_explanation_status": "component_neutralization_tested_for_path_stability",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "82_component_neutralized_path_stability_gate.json"
    md_path = TEST_RESULTS / "82_component_neutralized_path_stability_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Component-Neutralized Path Stability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 81 localized boundary instability mainly to learned copy-length",
        "and source-exception costs. This gate neutralizes those components",
        "with uniform decodable costs and reruns multi-cutoff path stability.",
        "",
        "## Summary",
        "",
        f"- Active stable exact-path books: `{s['active_stable_exact_path_book_count']}`.",
        f"- Best stability mode: `{s['best_stability_mode']}`.",
        f"- Best stable exact-path books: `{s['best_stability_book_count']}`.",
        f"- Best stability delta vs active: `{s['best_stability_delta_vs_active']}`.",
        "",
        "## Mode Scoreboard",
        "",
        "| Mode | Stable books | Unstable books | Stable delta | Raw-positive evals | Parser bits delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in s["mode_summaries"]:
        lines.append(
            "| {cost_mode} | {stable_exact_path_book_count}/50 | {unstable_exact_path_book_count}/50 | {stable_book_delta_vs_active:+d} | {raw_positive_book_evaluations}/175 | {total_parser_bits_delta_vs_active:+.6f} |".format(
                **row
            )
        )
    best = next(
        row
        for row in s["mode_summaries"]
        if row["cost_mode"] == s["best_stability_mode"]
    )
    lines.extend(
        [
            "",
            "## Best-Mode Residual Instability",
            "",
            f"- Best mode parser-bit delta vs active: `{best['total_parser_bits_delta_vs_active']:.6f}`.",
            f"- Remaining unstable books: `{[row['book'] for row in best['unstable_books']]}`.",
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
