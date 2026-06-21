from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE100 = PREQ / "reports" / "test_results" / "100_skeleton_rule_coverage_audit.json"
GATE111 = PREQ / "reports" / "test_results" / "111_decoder_length_candidate_ambiguity_audit.json"
GATE112 = PREQ / "reports" / "test_results" / "112_decoder_length_policy_audit.json"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

OUT_STEM = "01_segmentation_decision_trace"
MIN_COPY_LEN = 5
SEED_BOOKS = list(range(10))
MAX_PAIR_SAMPLE = 80


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


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def max_match(emitted: str, target: str, source: int, target_start: int) -> int:
    limit = min(len(emitted) - source, len(target) - target_start)
    length = 0
    while length < limit and emitted[source + length] == target[target_start + length]:
        length += 1
    return length


def candidate_sources_with_max(
    emitted: str, target: str, target_start: int, min_len: int = MIN_COPY_LEN
) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    if len(target) - target_start < min_len:
        return rows
    needle = target[target_start : target_start + min_len]
    start = emitted.find(needle)
    while start != -1:
        match_len = max_match(emitted, target, start, target_start)
        if match_len >= min_len:
            rows.append({"source": start, "max_length": match_len})
        start = emitted.find(needle, start + 1)
    return rows


def copy_pair_count(source_rows: list[dict[str, int]], min_len: int = MIN_COPY_LEN) -> int:
    return sum(row["max_length"] - min_len + 1 for row in source_rows)


def sample_pairs(
    source_rows: list[dict[str, int]], declared_source: int, declared_length: int
) -> tuple[list[dict[str, int]], bool]:
    pairs: list[dict[str, int]] = []
    total = copy_pair_count(source_rows)
    include_all = total <= MAX_PAIR_SAMPLE
    if include_all:
        for row in source_rows:
            for length in range(MIN_COPY_LEN, row["max_length"] + 1):
                pairs.append({"source": row["source"], "length": length})
        return pairs, True

    selected: set[tuple[int, int]] = set()
    for row in source_rows[:10] + source_rows[-10:]:
        for length in (MIN_COPY_LEN, row["max_length"]):
            selected.add((row["source"], length))
    max_source_rows = sorted(
        source_rows, key=lambda row: (-row["max_length"], row["source"])
    )[:20]
    for row in max_source_rows:
        midpoint = (MIN_COPY_LEN + row["max_length"]) // 2
        for length in (MIN_COPY_LEN, midpoint, row["max_length"]):
            selected.add((row["source"], length))
    selected.add((declared_source, declared_length))
    for length in (MIN_COPY_LEN, declared_length, max(r["max_length"] for r in source_rows)):
        if MIN_COPY_LEN <= length <= next(
            row["max_length"] for row in source_rows if row["source"] == declared_source
        ):
            selected.add((declared_source, length))
    for source, length in sorted(selected)[:MAX_PAIR_SAMPLE]:
        pairs.append({"source": source, "length": length})
    return pairs, False


def op_intervals_for_book(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    for book_rows in by_book.values():
        book_rows.sort(key=lambda row: int(row["op_index"]))
    return by_book


def projected_ops_from_copy_rows(
    copy_rows: list[dict[str, Any]], books: dict[int, str]
) -> list[dict[str, Any]]:
    """Rebuild the stable projection used by gate 111.

    Gate 100's skeleton rows are a dependency ledger, but its copy op_index values
    do not always align with the stable-projection copy rows used by gates 111/112.
    For a source/length trace we need the latter, so literals are inferred as gaps
    between stable copy intervals.
    """
    copies_by_book: dict[int, list[dict[str, Any]]] = {}
    for row in copy_rows:
        copies_by_book.setdefault(int(row["book"]), []).append(row)
    for rows in copies_by_book.values():
        rows.sort(key=lambda row: (int(row["book_pos"]), int(row["op_index"])))

    ops: list[dict[str, Any]] = []
    for book in range(10, 70):
        target = books[book]
        pos = 0
        op_index = 0
        for copy in copies_by_book.get(book, []):
            copy_start = int(copy["book_pos"])
            if copy_start < pos:
                raise RuntimeError(
                    {
                        "type": "overlapping_stable_copy_rows",
                        "book": book,
                        "copy_start": copy_start,
                        "pos": pos,
                    }
                )
            if copy_start > pos:
                ops.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "projection_copy_index": None,
                        "type": "literal",
                        "target_start": pos,
                        "length": copy_start - pos,
                        "source": None,
                        "global_target_pos": None,
                    }
                )
                op_index += 1
            length = int(copy["length"])
            ops.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "projection_copy_index": int(copy["op_index"]),
                    "type": "copy",
                    "target_start": copy_start,
                    "length": length,
                    "source": int(copy["source"]),
                    "global_target_pos": int(copy["global_target_pos"]),
                }
            )
            pos = copy_start + length
            op_index += 1
        if pos < len(target):
            ops.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "projection_copy_index": None,
                    "type": "literal",
                    "target_start": pos,
                    "length": len(target) - pos,
                    "source": None,
                    "global_target_pos": None,
                }
            )
    return ops


def boundary_copy_pair_count(emitted: str, target: str, target_start: int) -> int:
    return copy_pair_count(candidate_sources_with_max(emitted, target, target_start))


def make_trace() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    gate111 = load_json(GATE111)
    gate112 = load_json(GATE112)
    for name, data in [
        ("skeleton_rule_coverage", gate100),
        ("decoder_length_candidate_ambiguity", gate111),
        ("decoder_length_policy", gate112),
    ]:
        assert_boundary(name, data)
    if gate112["classification"] != "simple_length_candidate_policies_not_promoted":
        raise RuntimeError("gate112 no longer rejects simple length policies")

    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    gate111_module = load_module("gate111_for_segmentation_trace", GATE111_SCRIPT)
    stable_copy_rows = gate111_module.make_copy_rows()
    projected_ops = projected_ops_from_copy_rows(stable_copy_rows, books)
    if sum(1 for row in projected_ops if row["type"] == "copy") != gate100["summary"]["copy_count"]:
        raise RuntimeError("projected copy count differs from gate100")
    by_book = op_intervals_for_book(projected_ops)

    emitted = "".join(books[book] for book in SEED_BOOKS)
    copy_trace_rows: list[dict[str, Any]] = []
    operation_trace_rows: list[dict[str, Any]] = []
    previous_length_by_book: dict[int, int] = {}

    for skeleton in projected_ops:
        book = int(skeleton["book"])
        op_index = int(skeleton["op_index"])
        op_type = skeleton["type"]
        target = books[book]
        target_start = int(skeleton["target_start"])
        declared_length = int(skeleton["length"])
        remaining = len(target) - target_start
        previous_length = previous_length_by_book.get(book)
        future_rows = [
            row for row in by_book[book] if int(row["op_index"]) > op_index
        ]
        next_row = future_rows[0] if future_rows else None

        operation_trace_rows.append(
            {
                "book": book,
                "op_index": op_index,
                "op_type": op_type,
                "projection_copy_index": skeleton["projection_copy_index"],
                "target_start": target_start,
                "declared_length": declared_length,
                "remaining_book_digits": remaining,
                "previous_in_book_length": previous_length,
            }
        )

        if op_type == "literal":
            payload = target[target_start : target_start + declared_length]
            if payload != target[target_start : target_start + declared_length]:
                raise RuntimeError({"book": book, "op_index": op_index})
            emitted += payload
            previous_length_by_book[book] = declared_length
            continue

        if op_type != "copy":
            raise RuntimeError({"book": book, "op_index": op_index, "op_type": op_type})

        declared_source = int(skeleton["source"])
        source_rows = candidate_sources_with_max(emitted, target, target_start)
        source_by_pos = {row["source"]: row for row in source_rows}
        if declared_source not in source_by_pos:
            raise RuntimeError(
                {
                    "type": "declared_source_missing_from_candidates",
                    "book": book,
                    "op_index": op_index,
                    "declared_source": declared_source,
                }
            )
        decoder_max = source_by_pos[declared_source]["max_length"]
        if not (MIN_COPY_LEN <= declared_length <= decoder_max):
            raise RuntimeError(
                {
                    "type": "declared_length_outside_source_max",
                    "book": book,
                    "op_index": op_index,
                    "declared_length": declared_length,
                    "decoder_max": decoder_max,
                }
            )

        boundary_after_declared = target_start + declared_length
        boundary_after_max = target_start + decoder_max
        if boundary_after_declared < len(target):
            declared_boundary_sources = candidate_sources_with_max(
                emitted + target[target_start:boundary_after_declared],
                target,
                boundary_after_declared,
            )
        else:
            declared_boundary_sources = []
        if boundary_after_max < len(target):
            max_boundary_sources = candidate_sources_with_max(
                emitted + target[target_start:boundary_after_max],
                target,
                boundary_after_max,
            )
        else:
            max_boundary_sources = []

        extension_digits = decoder_max - declared_length
        extension_span = (boundary_after_declared, boundary_after_max)
        overlapped_future_ops = []
        overlapped_literal_digits = 0
        overlapped_copy_digits = 0
        if extension_digits > 0:
            ext_start, ext_end = extension_span
            for future in future_rows:
                f_start = int(future["target_start"])
                f_end = f_start + int(future["length"])
                overlap = max(0, min(ext_end, f_end) - max(ext_start, f_start))
                if overlap <= 0:
                    continue
                overlapped_future_ops.append(
                    {
                        "op_index": int(future["op_index"]),
                        "op_type": future["type"],
                        "overlap_digits": overlap,
                    }
                )
                if future["type"] == "literal":
                    overlapped_literal_digits += overlap
                else:
                    overlapped_copy_digits += overlap

        normalized = (
            0.0
            if decoder_max == MIN_COPY_LEN
            else (declared_length - MIN_COPY_LEN) / (decoder_max - MIN_COPY_LEN)
        )
        pair_sample, sample_is_exhaustive = sample_pairs(
            source_rows, declared_source, declared_length
        )
        all_source_max = max(row["max_length"] for row in source_rows)
        all_pair_count = copy_pair_count(source_rows)
        max_length_sources = [
            row["source"] for row in source_rows if row["max_length"] == all_source_max
        ]
        max_length_sources_sorted = sorted(max_length_sources)
        declared_source_rank = sorted(source_by_pos).index(declared_source) + 1
        declared_source_rank_among_global_max = (
            max_length_sources_sorted.index(declared_source) + 1
            if declared_source in max_length_sources_sorted
            else None
        )
        trace = {
            "book": book,
            "op_index": op_index,
            "projection_copy_index": skeleton["projection_copy_index"],
            "target_start": target_start,
            "global_target_pos": int(skeleton["global_target_pos"]),
            "declared_source": declared_source,
            "declared_length": declared_length,
            "remaining_book_digits": remaining,
            "candidate_pair_count": all_pair_count,
            "candidate_source_count": len(source_rows),
            "candidate_pair_sample_exhaustive": sample_is_exhaustive,
            "candidate_pair_sample": pair_sample,
            "decoder_max": decoder_max,
            "all_source_max_length": all_source_max,
            "declared_source_rank_by_position": declared_source_rank,
            "declared_source_is_earliest": declared_source_rank == 1,
            "declared_source_is_latest": declared_source_rank == len(source_rows),
            "declared_pair_is_global_max_length": declared_length == all_source_max
            and declared_source in max_length_sources,
            "global_max_length_source_count": len(max_length_sources_sorted),
            "global_max_earliest_source": max_length_sources_sorted[0],
            "global_max_latest_source": max_length_sources_sorted[-1],
            "global_max_length_sources_sample": max_length_sources_sorted[:40],
            "declared_source_rank_among_global_max": declared_source_rank_among_global_max,
            "declared_source_is_unique_global_max": len(max_length_sources_sorted) == 1
            and declared_source in max_length_sources_sorted,
            "declared_source_is_earliest_global_max": declared_source
            == max_length_sources_sorted[0],
            "declared_source_is_latest_global_max": declared_source
            == max_length_sources_sorted[-1],
            "normalized_declared_length_position": normalized,
            "declared_is_min": declared_length == MIN_COPY_LEN,
            "declared_is_max": declared_length == decoder_max,
            "declared_is_median": declared_length
            == round((MIN_COPY_LEN + decoder_max) / 2),
            "declared_is_previous_length": previous_length == declared_length,
            "previous_in_book_length": previous_length,
            "extend_to_max_extra_digits": extension_digits,
            "extend_to_max_invades_next_operation": extension_digits > 0,
            "extend_to_max_overlapped_future_ops": overlapped_future_ops,
            "extend_to_max_overlapped_literal_digits": overlapped_literal_digits,
            "extend_to_max_overlapped_copy_digits": overlapped_copy_digits,
            "extend_to_max_changes_literal_payload": overlapped_literal_digits > 0,
            "next_operation_type": None if next_row is None else next_row["type"],
            "next_operation_declared_length": None
            if next_row is None
            else int(next_row["length"]),
            "declared_boundary_candidate_pair_count": copy_pair_count(
                declared_boundary_sources
            ),
            "declared_boundary_candidate_source_count": len(declared_boundary_sources),
            "max_boundary_candidate_pair_count": copy_pair_count(max_boundary_sources),
            "max_boundary_candidate_source_count": len(max_boundary_sources),
            "extend_to_max_creates_or_destroys_future_copy_opportunity": copy_pair_count(
                declared_boundary_sources
            )
            != copy_pair_count(max_boundary_sources),
            "preserves_recurrent_boundary": copy_pair_count(declared_boundary_sources)
            > 0,
        }
        copy_trace_rows.append(trace)

        emitted_chunk = emitted[declared_source : declared_source + declared_length]
        target_chunk = target[target_start : target_start + declared_length]
        if emitted_chunk != target_chunk:
            raise RuntimeError({"type": "copy_mismatch", "book": book, "op_index": op_index})
        emitted += target_chunk
        previous_length_by_book[book] = declared_length

    candidate_counts = [row["candidate_pair_count"] for row in copy_trace_rows]
    source_counts = [row["candidate_source_count"] for row in copy_trace_rows]
    extension_digits = [row["extend_to_max_extra_digits"] for row in copy_trace_rows]
    hard_rows = sorted(
        copy_trace_rows,
        key=lambda row: (
            row["candidate_pair_count"],
            row["extend_to_max_extra_digits"],
            row["book"],
            row["op_index"],
        ),
        reverse=True,
    )[:25]
    max_failures = [
        row
        for row in copy_trace_rows
        if row["extend_to_max_extra_digits"] > 0
    ]

    return {
        "schema": "segmentation_decision_trace.v1",
        "classification": "segmentation_decision_trace_audit_only",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "skeleton_rule_coverage": rel(GATE100),
            "decoder_length_candidate_ambiguity": rel(GATE111),
            "decoder_length_policy": rel(GATE112),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "new_plaintext_or_translation": False,
            "candidate_pair_sample_limit": MAX_PAIR_SAMPLE,
            "seed_books_are_operational_context_only": SEED_BOOKS,
        },
        "summary": {
            "reference_skeleton_operation_count": gate100["summary"]["op_count"],
            "reference_skeleton_literal_count": gate100["summary"]["literal_count"],
            "stable_projection_operation_count": len(operation_trace_rows),
            "stable_projection_literal_gap_count": sum(
                1 for row in projected_ops if row["type"] == "literal"
            ),
            "stable_projection_literal_digit_count": sum(
                int(row["length"]) for row in projected_ops if row["type"] == "literal"
            ),
            "copy_count": len(copy_trace_rows),
            "candidate_pair_count_summary": summarize([float(v) for v in candidate_counts]),
            "candidate_source_count_summary": summarize([float(v) for v in source_counts]),
            "extend_to_max_extra_digits_summary": summarize(
                [float(v) for v in extension_digits]
            ),
            "declared_is_max_count": sum(1 for row in copy_trace_rows if row["declared_is_max"]),
            "declared_is_min_count": sum(1 for row in copy_trace_rows if row["declared_is_min"]),
            "declared_is_median_count": sum(
                1 for row in copy_trace_rows if row["declared_is_median"]
            ),
            "declared_is_previous_length_count": sum(
                1 for row in copy_trace_rows if row["declared_is_previous_length"]
            ),
            "extend_to_max_failure_count": len(max_failures),
            "extend_to_max_changes_literal_payload_count": sum(
                1 for row in copy_trace_rows if row["extend_to_max_changes_literal_payload"]
            ),
            "preserves_recurrent_boundary_count": sum(
                1 for row in copy_trace_rows if row["preserves_recurrent_boundary"]
            ),
            "hard_case_books": sorted({row["book"] for row in hard_rows}),
        },
        "copy_trace_rows": copy_trace_rows,
        "hard_case_rows": hard_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "trace_built_no_rule_promoted",
            "source_length_dependency_status": "retained_pending_structural_tests",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    pair = s["candidate_pair_count_summary"]
    ext = s["extend_to_max_extra_digits_summary"]
    lines = [
        "# Segmentation Decision Trace",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This trace converts the retained `(source,length)` dependency into a",
        "per-copy decision ledger. It is analysis-only: it does not emit a",
        "new formula and it does not alter row0, plaintext, translation, or the",
        "compression bound.",
        "",
        "## Summary",
        "",
        f"- Stable-projection operations traced: `{s['stable_projection_operation_count']}`.",
        f"- Reference skeleton operations: `{s['reference_skeleton_operation_count']}`.",
        f"- Copy decisions traced: `{s['copy_count']}`.",
        f"- Candidate pair count median: `{pair['median']:.3f}`; max: `{pair['max']}`.",
        f"- Extra digits if extending declared source to max median: `{ext['median']:.3f}`; max: `{ext['max']}`.",
        f"- Declared length is max for `{s['declared_is_max_count']}/{s['copy_count']}` copies.",
        f"- Declared length is min for `{s['declared_is_min_count']}/{s['copy_count']}` copies.",
        f"- Declared length equals previous in-book length for `{s['declared_is_previous_length_count']}/{s['copy_count']}` copies.",
        f"- Extending to max would change literal payload in `{s['extend_to_max_changes_literal_payload_count']}` copy decisions.",
        f"- Declared boundary preserves a recurrent copy opportunity in `{s['preserves_recurrent_boundary_count']}` copy decisions.",
        f"- Hard-case books by candidate-pair pressure: `{s['hard_case_books']}`.",
        "",
        "## Hard Cases",
        "",
        "| Book | Op | Declared source | Declared length | Decoder max | Candidate pairs | Extend extra | Declared boundary pairs | Max boundary pairs |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["hard_case_rows"][:12]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['declared_source']}` | "
            f"`{row['declared_length']}` | `{row['decoder_max']}` | "
            f"`{row['candidate_pair_count']}` | `{row['extend_to_max_extra_digits']}` | "
            f"`{row['declared_boundary_candidate_pair_count']}` | "
            f"`{row['max_boundary_candidate_pair_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This gate builds the required trace but promotes no segmentation rule.",
            "- Structural hypotheses are tested in the next gate against this trace.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_trace()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
