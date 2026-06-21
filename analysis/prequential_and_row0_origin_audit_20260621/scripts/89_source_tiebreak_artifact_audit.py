from __future__ import annotations

import bisect
import hashlib
import heapq
import importlib.util
import json
import math
import time
from itertools import count
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE86_SCRIPT = HERE / "scripts" / "86_global_item_literal_length_control_gate.py"
GATE88 = TEST_RESULTS / "88_decoder_side_rule_coverage_audit.json"

MODE = "payload_uniform_no_item_or_literal_length"
TIE_POLICIES = [
    "earliest_source",
    "latest_source",
    "prefer_previous_end_then_earliest",
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


def source_tie_delta(
    *, policy: str, source: int, previous_end: int | None, legal_source_count: int
) -> int:
    if policy == "earliest_source":
        return source
    if policy == "latest_source":
        return legal_source_count - 1 - source
    if policy == "prefer_previous_end_then_earliest":
        if previous_end is not None and source == previous_end:
            return 0
        return legal_source_count + source + 1
    raise ValueError(policy)


def better(candidate: tuple[float, int], incumbent: tuple[float, int] | None) -> bool:
    if incumbent is None:
        return True
    if candidate[0] < incumbent[0] - 1e-12:
        return True
    return abs(candidate[0] - incumbent[0]) <= 1e-12 and candidate[1] < incumbent[1]


def sparse_parse_tiebreak(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
    gate82,
    policy: str,
) -> dict[str, Any]:
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    n = len(text)

    matches = audit126.precompute_matches(text, available, min_len)
    copy_positions = {pos for pos, row in enumerate(matches) if row}
    literal_endpoints = sorted(copy_positions | {n})
    source_cache: dict[tuple[int, int, int | None], tuple[float, bool, float, float]] = {}

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

    start = (0, "BOS", initial_previous_copy_end)
    serial = count()
    heap: list[tuple[float, int, int, tuple[int, str, int | None]]] = [
        (0.0, 0, next(serial), start)
    ]
    distance: dict[tuple[int, str, int | None], tuple[float, int]] = {start: (0.0, 0)}
    back: dict[
        tuple[int, str, int | None],
        tuple[tuple[int, str, int | None], tuple[Any, ...]],
    ] = {}
    transition_evaluations = 0
    final_state: tuple[int, str, int | None] | None = None

    while heap:
        cost, tie_score, _serial, state = heapq.heappop(heap)
        if (cost, tie_score) != distance.get(state):
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
                next_state = (next_pos, "literal", previous_end)
                candidate = (cost + add, tie_score)
                transition_evaluations += 1
                if better(candidate, distance.get(next_state)):
                    distance[next_state] = candidate
                    back[next_state] = (state, ("literal", length, literal_forced))
                    heapq.heappush(heap, (*candidate, next(serial), next_state))

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
                add = source_cost + math.log2(symbol_count)
                tie_add = source_tie_delta(
                    policy=policy,
                    source=source_pos,
                    previous_end=previous_end,
                    legal_source_count=legal_source_count,
                )
                next_state = (pos + length, "copy", source_pos + length)
                candidate = (cost + add, tie_score + tie_add)
                transition_evaluations += 1
                if better(candidate, distance.get(next_state)):
                    distance[next_state] = candidate
                    back[next_state] = (
                        state,
                        ("copy", source_pos, length, previous_item == "literal", is_default),
                    )
                    heapq.heappush(heap, (*candidate, next(serial), next_state))

    if final_state is None:
        raise RuntimeError({"book": book, "policy": policy, "type": "no_parse"})

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
    source_values: list[int] = []
    source_default_count = 0
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
            source_values.append(source_pos)
            source_default_count += 1 if is_default else 0
            position += length
            copy_items += 1
            copied_digits += length
        else:
            raise RuntimeError(op)

    primary_cost, tie_score = distance[final_state]
    return {
        "book": book,
        "policy": policy,
        "parser_bits": float(primary_cost),
        "tie_score": tie_score,
        "roundtrip_ok": "".join(rendered) == text,
        "final_previous_copy_end": final_state[2],
        "transition_evaluations": transition_evaluations,
        "visited_state_count": len(distance),
        "op_count": len(signature_ops),
        "copy_items": copy_items,
        "literal_runs": literal_runs,
        "copied_digits": copied_digits,
        "literal_digits": literal_digits,
        "source_sum": sum(source_values),
        "source_default_count": source_default_count,
        "raw_digit_uniform_bits": len(text) * math.log2(10),
        "signature": compact_signature(signature_ops),
        "signature_ops": signature_ops,
    }


def run_cutoff(cutoff: int, gate77, gate82, *, policy: str) -> list[dict[str, Any]]:
    context = gate77.load_parser_context_for_cutoff(cutoff)
    context["gate82"] = gate82
    gate37 = context["gate37"]
    formula = context["formula"]
    books = context["books"]
    available = "".join(books[str(index)] for index in range(cutoff))
    previous_end = gate37.previous_copy_end_before(formula, cutoff)
    rows = []
    for book in range(cutoff, 70):
        row = sparse_parse_tiebreak(
            context=context,
            book=book,
            available=available,
            initial_previous_copy_end=previous_end,
            gate82=gate82,
            policy=policy,
        )
        if not row["roundtrip_ok"]:
            raise RuntimeError({"cutoff": cutoff, "book": book, "policy": policy})
        row["cutoff"] = cutoff
        rows.append(row)
        available += books[str(book)]
        previous_end = row["final_previous_copy_end"]
    return rows


def summarize_policy(policy: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    book_rows = []
    for book in sorted(by_book):
        book_rows_for_book = sorted(by_book[book], key=lambda row: int(row["cutoff"]))
        signatures = sorted({row["signature"] for row in book_rows_for_book})
        book_rows.append(
            {
                "book": book,
                "cutoff_count": len(book_rows_for_book),
                "signature_count": len(signatures),
                "stable_exact_path": len(signatures) == 1,
                "copy_items": int(book_rows_for_book[0]["copy_items"]),
                "literal_runs": int(book_rows_for_book[0]["literal_runs"]),
                "source_sum": int(book_rows_for_book[0]["source_sum"]),
            }
        )
    multi = [row for row in book_rows if row["cutoff_count"] >= 2]
    unstable = [row for row in multi if not row["stable_exact_path"]]
    return {
        "policy": policy,
        "total_parser_evaluations": len(rows),
        "roundtrip_book_evaluations": sum(1 for row in rows if row["roundtrip_ok"]),
        "raw_positive_book_evaluations": sum(
            1 for row in rows if row["parser_bits"] < row["raw_digit_uniform_bits"]
        ),
        "book_count_with_multiple_cutoffs": len(multi),
        "stable_exact_path_book_count": len(multi) - len(unstable),
        "unstable_exact_path_book_count": len(unstable),
        "unstable_books": [row["book"] for row in unstable],
        "total_primary_parser_bits": sum(row["parser_bits"] for row in rows),
        "total_tie_score": sum(int(row["tie_score"]) for row in rows),
        "total_source_sum": sum(int(row["source_sum"]) for row in rows),
        "total_source_default_count": sum(int(row["source_default_count"]) for row in rows),
        "total_copy_items": sum(int(row["copy_items"]) for row in rows),
        "total_literal_runs": sum(int(row["literal_runs"]) for row in rows),
        "total_literal_digits": sum(int(row["literal_digits"]) for row in rows),
        "max_signature_count_per_book": max(row["signature_count"] for row in multi),
        "total_unique_book_signatures": sum(row["signature_count"] for row in multi),
        "book_rows": book_rows,
    }


def make_result() -> dict[str, Any]:
    gate88 = load_json(GATE88)
    assert_boundary("decoder_side_rule_coverage_audit", gate88)
    if gate88["classification"] != "decoder_side_rule_coverage_insufficient":
        raise RuntimeError("gate88 result changed")

    gate86 = load_module("gate86_for_gate89", GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate89", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate89", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    summaries = []
    for policy in TIE_POLICIES:
        rows = []
        for cutoff in gate77.CUTOFFS:
            rows.extend(run_cutoff(cutoff, gate77, gate82, policy=policy))
        summaries.append(summarize_policy(policy, rows))
    elapsed = time.perf_counter() - start

    primary_bits = {round(row["total_primary_parser_bits"], 9) for row in summaries}
    all_same_primary_cost = len(primary_bits) == 1
    all_stable = all(row["stable_exact_path_book_count"] == 50 for row in summaries)
    source_sums = {row["policy"]: row["total_source_sum"] for row in summaries}
    source_span = max(source_sums.values()) - min(source_sums.values())
    earliest_signal_artifact = (
        all_same_primary_cost and all_stable and source_span > 0
    )
    classification = (
        "source_canonicality_tiebreak_artifact"
        if earliest_signal_artifact
        else "source_canonicality_tiebreak_not_resolved"
    )

    return {
        "schema": "source_tiebreak_artifact_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate88": rel(GATE88),
            "gate86_script": rel(GATE86_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "base_cost_mode": MODE,
            "tie_policies": TIE_POLICIES,
            "primary_cost_unchanged_by_tie_policy": all_same_primary_cost,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "all_same_primary_cost": all_same_primary_cost,
            "all_policies_50_50_stable": all_stable,
            "source_sum_span": source_span,
            "earliest_signal_artifact": earliest_signal_artifact,
            "interpretation": (
                "If alternate source tie policies keep the same primary parser "
                "cost and 50/50 path stability while changing selected sources, "
                "then the 208/208 earliest-target-match observation is a parser "
                "tie-break artifact, not an independent source-origin rule."
            ),
        },
        "policy_summaries": summaries,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "source_canonicality_not_promoted",
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "89_source_tiebreak_artifact_audit.json"
    md_path = TEST_RESULTS / "89_source_tiebreak_artifact_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source Tie-Break Artifact Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 88 found that every projected copy source is the earliest target",
        "match. This audit tests whether that is mechanical evidence or a parser",
        "tie-break artifact by rerunning the stable no-item/no-literal-length",
        "projection with alternate source tie policies under the same primary cost.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Stable books | Unstable books | Primary bits | Source sum | Source defaults | Copy items |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["policy_summaries"]:
        lines.append(
            "| {policy} | {stable_exact_path_book_count}/50 | {unstable_exact_path_book_count}/50 | {total_primary_parser_bits:.6f} | {total_source_sum} | {total_source_default_count} | {total_copy_items} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Same primary cost across policies: `{s['all_same_primary_cost']}`.",
            f"- All policies stable at 50/50: `{s['all_policies_50_50_stable']}`.",
            f"- Source-sum span across policies: `{s['source_sum_span']}`.",
            f"- Earliest-source signal treated as artifact: `{s['earliest_signal_artifact']}`.",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
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
