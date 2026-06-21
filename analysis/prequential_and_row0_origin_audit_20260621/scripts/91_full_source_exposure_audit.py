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
GATE89_SCRIPT = HERE / "scripts" / "89_source_tiebreak_artifact_audit.py"
GATE89 = TEST_RESULTS / "89_source_tiebreak_artifact_audit.json"
GATE90 = TEST_RESULTS / "90_source_candidate_collapse_audit.json"

MODE = "payload_uniform_no_item_or_literal_length"
TEST_CUTOFFS = [60]
TIE_POLICIES = ["earliest_source", "latest_source", "prefer_previous_end_then_earliest"]


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


def all_match_candidates(
    *, text: str, pos: int, available: str, index: dict[str, list[int]], min_len: int
) -> list[tuple[int, int, int]]:
    if pos + min_len > len(text):
        return []
    key = text[pos : pos + min_len]
    rows: list[tuple[int, int, int]] = []
    max_len = len(text) - pos
    for source_pos in index.get(key, []):
        length = min_len
        while length < max_len:
            source_next = source_pos + length
            if source_next >= len(available) or available[source_next] != text[pos + length]:
                break
            length += 1
        for candidate_len in range(min_len, length + 1):
            rows.append((source_pos, candidate_len, candidate_len - min_len))
    return sorted(rows, key=lambda row: (row[1], row[0]))


def precompute_all_source_matches(audit126, text: str, available: str, min_len: int):
    local_available = available
    local_index = audit126.build_index(local_available, min_len)
    rows = []
    total_candidates = 0
    collapsed_candidate_count = 0
    max_candidates_at_position = 0
    positions_with_hidden_sources = 0
    for pos in range(len(text)):
        all_rows = all_match_candidates(
            text=text,
            pos=pos,
            available=local_available,
            index=local_index,
            min_len=min_len,
        )
        collapsed_rows = audit126.match_candidates(
            text=text,
            pos=pos,
            available=local_available,
            index=local_index,
            min_len=min_len,
        )
        rows.append(all_rows)
        total_candidates += len(all_rows)
        collapsed_candidate_count += len(collapsed_rows)
        max_candidates_at_position = max(max_candidates_at_position, len(all_rows))
        if len(all_rows) > len(collapsed_rows):
            positions_with_hidden_sources += 1
        previous_len = len(local_available)
        local_available += text[pos]
        audit126.add_index_entries(local_available, local_index, min_len, previous_len)
    return rows, {
        "total_all_source_candidates": total_candidates,
        "total_collapsed_candidates": collapsed_candidate_count,
        "hidden_candidate_count": total_candidates - collapsed_candidate_count,
        "positions_with_hidden_sources": positions_with_hidden_sources,
        "max_candidates_at_position": max_candidates_at_position,
    }


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


def sparse_parse_all_sources(
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
    source_train_counts = context["source_train_counts"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    n = len(text)

    matches, candidate_stats = precompute_all_source_matches(
        audit126,
        text,
        available,
        min_len,
    )
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
    non_earliest_sources = 0
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
            if len(chunk) != length:
                raise RuntimeError({"book": book, "type": "short_copy"})
            target_chunk = text[position : position + length]
            if chunk != target_chunk:
                raise RuntimeError({"book": book, "type": "copy_mismatch"})
            earliest = local_emitted.find(target_chunk)
            non_earliest_sources += 1 if earliest != source_pos else 0
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
        "non_earliest_source_count": non_earliest_sources,
        "raw_digit_uniform_bits": len(text) * math.log2(10),
        "signature": compact_signature(signature_ops),
        "candidate_stats": candidate_stats,
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
        row = sparse_parse_all_sources(
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
            }
        )
    evaluated = book_rows
    unstable = [row for row in evaluated if not row["stable_exact_path"]]
    stats = [row["candidate_stats"] for row in rows if "candidate_stats" in row]
    return {
        "policy": policy,
        "total_parser_evaluations": len(rows),
        "roundtrip_book_evaluations": sum(1 for row in rows if row["roundtrip_ok"]),
        "raw_positive_book_evaluations": sum(
            1 for row in rows if row["parser_bits"] < row["raw_digit_uniform_bits"]
        ),
        "target_book_count": len(evaluated),
        "book_count_with_multiple_cutoffs": sum(
            1 for row in evaluated if row["cutoff_count"] >= 2
        ),
        "stable_exact_path_book_count": len(evaluated) - len(unstable),
        "unstable_exact_path_book_count": len(unstable),
        "unstable_books": [row["book"] for row in unstable],
        "total_primary_parser_bits": sum(row["parser_bits"] for row in rows),
        "total_source_sum": sum(int(row["source_sum"]) for row in rows),
        "total_non_earliest_source_count": sum(
            int(row.get("non_earliest_source_count", 0)) for row in rows
        ),
        "total_copy_items": sum(int(row["copy_items"]) for row in rows),
        "total_literal_runs": sum(int(row["literal_runs"]) for row in rows),
        "total_literal_digits": sum(int(row["literal_digits"]) for row in rows),
        "total_transition_evaluations": sum(int(row["transition_evaluations"]) for row in rows),
        "total_all_source_candidates": sum(
            int(row["total_all_source_candidates"]) for row in stats
        ),
        "total_collapsed_candidates": sum(
            int(row["total_collapsed_candidates"]) for row in stats
        ),
        "hidden_candidate_count": sum(int(row["hidden_candidate_count"]) for row in stats),
        "positions_with_hidden_sources": sum(
            int(row["positions_with_hidden_sources"]) for row in stats
        ),
        "max_candidates_at_position": max(
            [int(row["max_candidates_at_position"]) for row in stats] or [0]
        ),
        "max_signature_count_per_book": max(row["signature_count"] for row in evaluated),
        "book_rows": book_rows,
    }


def make_result() -> dict[str, Any]:
    gate89 = load_json(GATE89)
    gate90 = load_json(GATE90)
    assert_boundary("source_tiebreak_artifact_audit", gate89)
    assert_boundary("source_candidate_collapse_audit", gate90)
    gate86 = load_module("gate86_for_gate91", GATE86_SCRIPT)
    gate89_module = load_module("gate89_for_gate91", GATE89_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate91", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate91", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    summaries = []
    collapsed_summaries = []
    for policy in TIE_POLICIES:
        rows = []
        collapsed_rows = []
        for cutoff in TEST_CUTOFFS:
            rows.extend(run_cutoff(cutoff, gate77, gate82, policy=policy))
            collapsed_rows.extend(
                gate89_module.run_cutoff(cutoff, gate77, gate82, policy=policy)
            )
        summaries.append(summarize_policy(policy, rows))
        collapsed_summaries.append(summarize_policy(policy, collapsed_rows))
    elapsed = time.perf_counter() - start

    collapsed = {row["policy"]: row for row in collapsed_summaries}
    comparisons = []
    for row in summaries:
        base = collapsed[row["policy"]]
        comparisons.append(
            {
                "policy": row["policy"],
                "stable_delta_vs_collapsed": row["stable_exact_path_book_count"]
                - base["stable_exact_path_book_count"],
                "primary_bits_delta_vs_collapsed": row["total_primary_parser_bits"]
                - base["total_primary_parser_bits"],
                "source_sum_delta_vs_collapsed": row["total_source_sum"]
                - base["total_source_sum"],
                "copy_item_delta_vs_collapsed": row["total_copy_items"]
                - base["total_copy_items"],
                "literal_digit_delta_vs_collapsed": row["total_literal_digits"]
                - base["total_literal_digits"],
            }
        )
    all_roundtrip = all(
        row["roundtrip_book_evaluations"] == row["target_book_count"]
        for row in summaries
    )
    all_stable = all(
        row["stable_exact_path_book_count"] == row["target_book_count"]
        for row in summaries
    )
    any_non_earliest = any(row["total_non_earliest_source_count"] > 0 for row in summaries)
    classification = (
        "full_source_exposure_preserves_stability_with_non_earliest_sources"
        if all_roundtrip and all_stable and any_non_earliest
        else "full_source_exposure_changes_parser_frontier"
    )

    return {
        "schema": "full_source_exposure_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate89_collapsed_tiebreak": rel(GATE89),
            "gate89_script": rel(GATE89_SCRIPT),
            "gate90_candidate_collapse": rel(GATE90),
            "gate86_script": rel(GATE86_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "base_cost_mode": MODE,
            "all_same_length_sources_exposed": True,
            "tested_cutoffs": TEST_CUTOFFS,
            "full_multicutoff_exposure": False,
            "tie_policies": TIE_POLICIES,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "all_roundtrip": all_roundtrip,
            "all_policies_stable_on_tested_cutoffs": all_stable,
            "any_non_earliest_sources_selected": any_non_earliest,
            "interpretation": (
                "This audit exposes every same-length source candidate suppressed "
                "by precompute_matches. It tests whether the stable parser "
                "frontier survives without the earliest-only candidate collapse."
            ),
        },
        "policy_summaries": summaries,
        "collapsed_policy_summaries": collapsed_summaries,
        "comparisons_vs_collapsed_gate89": comparisons,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "full_source_exposure_tested_no_formula_promotion",
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "91_full_source_exposure_audit.json"
    md_path = TEST_RESULTS / "91_full_source_exposure_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    comparisons = {row["policy"]: row for row in result["comparisons_vs_collapsed_gate89"]}
    lines = [
        "# Full Source Exposure Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 90 showed that `precompute_matches` collapses source candidates to",
        "the earliest source per length. This audit reruns the cutoff-60 stable",
        "projection while exposing every same-length source candidate, then",
        "compares the result with the collapsed gate 89 frontier.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Stable books | Primary bits | Non-earliest sources | Hidden candidates | Delta bits vs collapsed | Delta source sum |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["policy_summaries"]:
        comp = comparisons[row["policy"]]
        render_row = {**row, **{k: v for k, v in comp.items() if k != "policy"}}
        lines.append(
            "| {policy} | {stable_exact_path_book_count}/{target_book_count} | {total_primary_parser_bits:.6f} | {total_non_earliest_source_count} | {hidden_candidate_count} | {primary_bits_delta_vs_collapsed:+.6f} | {source_sum_delta_vs_collapsed:+d} |".format(
                **render_row,
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- All policies roundtrip: `{s['all_roundtrip']}`.",
            f"- All policies stable on tested cutoffs: `{s['all_policies_stable_on_tested_cutoffs']}`.",
            f"- Any non-earliest sources selected: `{s['any_non_earliest_sources_selected']}`.",
            f"- Tested cutoffs: `{TEST_CUTOFFS}`.",
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
