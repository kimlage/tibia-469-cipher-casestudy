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
GATE84 = TEST_RESULTS / "84_residual_literal_payload_neutralization_gate.json"
GATE85 = TEST_RESULTS / "85_book49_residual_split_cause_audit.json"

MODES = [
    "payload_uniform",
    "payload_uniform_no_literal_length",
    "payload_uniform_no_item_type",
    "payload_uniform_no_item_or_literal_length",
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


def mode_flags(mode: str) -> tuple[bool, bool]:
    no_literal_length = mode in {
        "payload_uniform_no_literal_length",
        "payload_uniform_no_item_or_literal_length",
    }
    no_item_type = mode in {
        "payload_uniform_no_item_type",
        "payload_uniform_no_item_or_literal_length",
    }
    return no_literal_length, no_item_type


def sparse_parse_mode(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
    mode: str,
) -> dict[str, Any]:
    gate82 = context["gate82"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    item_model = formula["policy"]["item_type_model"]
    n = len(text)
    no_literal_length, no_item_type = mode_flags(mode)

    matches = audit126.precompute_matches(text, available, min_len)
    copy_positions = {pos for pos, row in enumerate(matches) if row}
    literal_endpoints = sorted(copy_positions | {n})
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
        if no_item_type:
            return 0.0
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
        if no_literal_length:
            return 0.0
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
                add = item_bits(forced, "copy") + source_cost + math.log2(symbol_count)
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
        raise RuntimeError({"book": book, "mode": mode, "type": "no_parse"})

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
        "cost_mode": mode,
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


def run_cutoff(cutoff: int, gate77_module, gate82_module, *, mode: str) -> list[dict[str, Any]]:
    context = gate77_module.load_parser_context_for_cutoff(cutoff)
    context["gate82"] = gate82_module
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
            mode=mode,
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError({"cutoff": cutoff, "book": book, "mode": mode})
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


def summarize_mode(mode: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    book_rows = [summarize_book(book, by_book[book]) for book in sorted(by_book)]
    fully_tested = [row for row in book_rows if row["cutoff_count"] >= 2]
    stable_rows = [row for row in fully_tested if row["stable_exact_path"]]
    unstable_rows = [row for row in fully_tested if not row["stable_exact_path"]]
    return {
        "cost_mode": mode,
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
    gate84 = load_json(GATE84)
    gate85 = load_json(GATE85)
    assert_boundary("residual_literal_payload_neutralization", gate84)
    assert_boundary("book49_residual_split_cause", gate85)
    gate82_module = load_module("gate82_for_gate86", GATE82_SCRIPT)
    gate77_module = gate82_module.load_module(
        "gate77_for_gate86",
        gate82_module.GATE77_SCRIPT,
    )
    gate84_payload = gate84["summary"]["payload_mode_summary"]

    start = time.perf_counter()
    mode_summaries = []
    for mode in MODES:
        rows = []
        for cutoff in gate77_module.CUTOFFS:
            rows.extend(run_cutoff(cutoff, gate77_module, gate82_module, mode=mode))
        mode_summaries.append(summarize_mode(mode, rows))
    elapsed = time.perf_counter() - start

    baseline = next(row for row in mode_summaries if row["cost_mode"] == "payload_uniform")
    for row in mode_summaries:
        row["stable_book_delta_vs_payload"] = (
            row["stable_exact_path_book_count"] - baseline["stable_exact_path_book_count"]
        )
        row["total_parser_bits_delta_vs_payload"] = (
            row["total_parser_bits"] - baseline["total_parser_bits"]
        )
        row["raw_positive_delta_vs_payload"] = (
            row["raw_positive_book_evaluations"] - baseline["raw_positive_book_evaluations"]
        )

    best = max(
        mode_summaries,
        key=lambda row: (
            row["stable_exact_path_book_count"],
            -row["total_parser_bits"],
            row["cost_mode"],
        ),
    )
    promotes_global_control = (
        best["stable_exact_path_book_count"] == 50
        and best["raw_positive_book_evaluations"] == 175
    )
    classification = (
        "global_item_literal_control_closes_path_stability"
        if promotes_global_control
        else "global_item_literal_control_not_promoted"
    )
    return {
        "schema": "global_item_literal_length_control_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate84_payload_neutralization": rel(GATE84),
            "gate85_book49_local_cause": rel(GATE85),
            "gate82_replay_script": rel(GATE82_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "modes": MODES,
            "global_controls": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "gate84_payload_stable_exact_path_book_count": gate84_payload[
                "stable_exact_path_book_count"
            ],
            "mode_summaries": mode_summaries,
            "best_mode": best["cost_mode"],
            "best_stable_exact_path_book_count": best["stable_exact_path_book_count"],
            "best_parser_bits_delta_vs_payload": best["total_parser_bits_delta_vs_payload"],
            "promotes_global_control": promotes_global_control,
            "interpretation": (
                "The local book 49 controls are applied globally to test whether "
                "they close the residual without side effects. A global control "
                "is promotable only if it preserves roundtrip/raw-positive "
                "coverage and closes exact path stability across all multi-cutoff "
                "books."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": classification,
            "generation_explanation_status": "global_item_literal_controls_tested_after_book49_localization",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "86_global_item_literal_length_control_gate.json"
    md_path = TEST_RESULTS / "86_global_item_literal_length_control_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Global Item/Literal-Length Control Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 85 showed that local item-type or literal-length controls stabilize",
        "the sole book `49` residual. This gate applies those controls globally",
        "on top of the payload-neutralized parser.",
        "",
        "## Mode Scoreboard",
        "",
        "| Mode | Stable books | Unstable books | Stable delta | Raw-positive evals | Parser bits delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in s["mode_summaries"]:
        lines.append(
            "| {cost_mode} | {stable_exact_path_book_count}/50 | {unstable_exact_path_book_count}/50 | {stable_book_delta_vs_payload:+d} | {raw_positive_book_evaluations}/175 | {total_parser_bits_delta_vs_payload:+.6f} |".format(
                **row
            )
        )
    best = next(row for row in s["mode_summaries"] if row["cost_mode"] == s["best_mode"])
    lines.extend(
        [
            "",
            "## Best Mode",
            "",
            f"- Best mode: `{s['best_mode']}`.",
            f"- Best stable exact-path books: `{s['best_stable_exact_path_book_count']}/50`.",
            f"- Best parser-bit delta vs payload baseline: `{s['best_parser_bits_delta_vs_payload']:.6f}`.",
            f"- Best-mode unstable books: `{[row['book'] for row in best['unstable_books']]}`.",
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
