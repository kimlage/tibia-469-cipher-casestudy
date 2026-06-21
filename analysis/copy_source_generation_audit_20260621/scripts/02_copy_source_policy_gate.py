from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_copy_source_ledger.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

OUT_STEM = "02_copy_source_policy_gate"
SEED_BOOKS = list(range(10))


Row = dict[str, Any]
PolicyFn = Callable[[Row], int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def clamp_source(source: int, legal_source_count: int) -> int:
    return max(0, min(source, legal_source_count - 1))


def matching_sources(emitted: str, chunk: str) -> list[int]:
    length = len(chunk)
    return [
        source
        for source in range(0, len(emitted) - length + 1)
        if emitted[source : source + length] == chunk
    ]


def policy_specs() -> dict[str, dict[str, Any]]:
    def earliest_legal(row: Row) -> int:
        return 0

    def latest_legal(row: Row) -> int:
        return int(row["legal_source_count"]) - 1

    def previous_source_else_earliest(row: Row) -> int:
        previous = row.get("previous_source")
        return 0 if previous is None else clamp_source(int(previous), int(row["legal_source_count"]))

    def previous_end_else_earliest(row: Row) -> int:
        previous = row.get("previous_end")
        return 0 if previous is None else clamp_source(int(previous), int(row["legal_source_count"]))

    def previous_end_minus_length_else_earliest(row: Row) -> int:
        previous = row.get("previous_end")
        if previous is None:
            return 0
        return clamp_source(int(previous) - int(row["length"]), int(row["legal_source_count"]))

    def same_target_start_else_latest(row: Row) -> int:
        return clamp_source(int(row["target_start"]), int(row["legal_source_count"]))

    def same_op_index_else_earliest(row: Row) -> int:
        return clamp_source(int(row["op_index"]), int(row["legal_source_count"]))

    def earliest_matching_oracle(row: Row) -> int:
        return int(row["earliest_matching_source"])

    def latest_matching_oracle(row: Row) -> int:
        return int(row["latest_matching_source"])

    def previous_end_matching_or_earliest_oracle(row: Row) -> int:
        previous = row.get("previous_end")
        if previous is not None and int(previous) in row["matching_sources"]:
            return int(previous)
        return int(row["earliest_matching_source"])

    return {
        "earliest_legal": {"fn": earliest_legal, "target_aware": False},
        "latest_legal": {"fn": latest_legal, "target_aware": False},
        "previous_source_else_earliest": {
            "fn": previous_source_else_earliest,
            "target_aware": False,
        },
        "previous_end_else_earliest": {
            "fn": previous_end_else_earliest,
            "target_aware": False,
        },
        "previous_end_minus_length_else_earliest": {
            "fn": previous_end_minus_length_else_earliest,
            "target_aware": False,
        },
        "same_target_start_else_latest": {
            "fn": same_target_start_else_latest,
            "target_aware": False,
        },
        "same_op_index_else_earliest": {
            "fn": same_op_index_else_earliest,
            "target_aware": False,
        },
        "earliest_matching_oracle": {"fn": earliest_matching_oracle, "target_aware": True},
        "latest_matching_oracle": {"fn": latest_matching_oracle, "target_aware": True},
        "previous_end_matching_or_earliest_oracle": {
            "fn": previous_end_matching_or_earliest_oracle,
            "target_aware": True,
        },
    }


def enrich_rows(rows: list[Row]) -> list[Row]:
    enriched = []
    for row in rows:
        copy = dict(row)
        copy["matching_sources"] = [int(source) for source in row["matching_sources"]]
        enriched.append(copy)
    return enriched


def evaluate_rows(rows: list[Row], policy_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    fn: PolicyFn = spec["fn"]
    scored = []
    for row in rows:
        source = fn(row)
        legal = 0 <= source < int(row["legal_source_count"])
        source_exact = legal and source == int(row["canonical_source"])
        chunk_hit = legal and source in row["matching_sources"]
        scored.append(
            {
                "book": row["book"],
                "op_index": row["op_index"],
                "predicted_source": source,
                "legal": legal,
                "source_exact": source_exact,
                "chunk_hit": chunk_hit,
            }
        )
    return {
        "policy": policy_name,
        "target_aware": bool(spec["target_aware"]),
        "copy_events": len(scored),
        "legal_predictions": sum(1 for row in scored if row["legal"]),
        "source_exact_events": sum(1 for row in scored if row["source_exact"]),
        "chunk_hit_events": sum(1 for row in scored if row["chunk_hit"]),
        "rows": scored,
    }


def select_source(policy_name: str, spec: dict[str, Any], row: Row) -> int:
    return spec["fn"](row)


def render_policy(
    policy_name: str,
    spec: dict[str, Any],
    ops_by_book: dict[str, list[dict[str, Any]]],
    books: dict[int, str],
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    previous_source: int | None = None
    previous_end: int | None = None
    exact_books = []
    book_rows = []
    copy_events = 0
    chunk_hits = 0
    exact_digits = 0
    total_digits = 0
    for book_text in sorted(ops_by_book, key=lambda value: int(value)):
        book = int(book_text)
        target = books[book]
        rendered = []
        for op_index, op in enumerate(ops_by_book[book_text]):
            start = int(op["target_start"])
            length = int(op["length"])
            total_digits += length
            if op["type"] == "literal":
                chunk = op["payload"]
                rendered.append(chunk)
                emitted += chunk
                exact_digits += length
                continue
            target_chunk = target[start : start + length]
            matches = matching_sources(emitted, target_chunk)
            ledger_like_row = {
                "book": book,
                "op_index": op_index,
                "target_start": start,
                "length": length,
                "legal_source_count": len(emitted) - length + 1,
                "canonical_source": int(op["source"]),
                "earliest_matching_source": matches[0] if matches else -1,
                "latest_matching_source": matches[-1] if matches else -1,
                "previous_source": previous_source,
                "previous_end": previous_end,
                "source_is_previous_end": previous_end is not None
                and emitted[previous_end : previous_end + length] == target_chunk,
                "matching_sources": matches,
            }
            source = select_source(policy_name, spec, ledger_like_row)
            copy_events += 1
            if 0 <= source < len(emitted) - length + 1:
                chunk = emitted[source : source + length]
            else:
                chunk = "?" * length
            if chunk == target_chunk:
                chunk_hits += 1
                exact_digits += length
            rendered.append(chunk)
            emitted += chunk
            previous_source = source if 0 <= source < len(emitted) else None
            previous_end = None if previous_source is None else previous_source + length
        rendered_book = "".join(rendered)
        exact = rendered_book == target
        if exact:
            exact_books.append(book)
        else:
            exact_digits_for_book = sum(
                1 for left, right in zip(rendered_book, target) if left == right
            )
            book_rows.append(
                {
                    "book": book,
                    "exact": False,
                    "exact_digits": exact_digits_for_book,
                    "book_digits": len(target),
                }
            )
    return {
        "policy": policy_name,
        "target_aware": bool(spec["target_aware"]),
        "exact_books": len(exact_books),
        "book_total": len(ops_by_book),
        "copy_chunk_hits_sequential": chunk_hits,
        "copy_events": copy_events,
        "exact_digits_sequential": exact_digits,
        "digit_total": total_digits,
        "failed_book_rows": book_rows[:10],
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    rows = enrich_rows(list(ledger["copy_rows"]))
    specs = policy_specs()
    row_scores = [evaluate_rows(rows, name, spec) for name, spec in specs.items()]
    row_scores.sort(
        key=lambda row: (
            row["target_aware"],
            row["chunk_hit_events"],
            row["source_exact_events"],
            row["policy"],
        ),
        reverse=True,
    )
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    render_scores = [
        render_policy(name, spec, ledger["canonical_ops_by_book"], books)
        for name, spec in specs.items()
    ]
    decoder_visible = [row for row in row_scores if not row["target_aware"]]
    target_aware = [row for row in row_scores if row["target_aware"]]
    best_decoder = max(
        decoder_visible,
        key=lambda row: (row["chunk_hit_events"], row["source_exact_events"], row["policy"]),
    )
    best_oracle = max(
        target_aware,
        key=lambda row: (row["chunk_hit_events"], row["source_exact_events"], row["policy"]),
    )
    render_by_policy = {row["policy"]: row for row in render_scores}
    best_decoder_render = render_by_policy[best_decoder["policy"]]
    promoted = (
        best_decoder["chunk_hit_events"] == best_decoder["copy_events"]
        and best_decoder_render["exact_books"] == best_decoder_render["book_total"]
    )
    classification = (
        "copy_source_decoder_policy_promoted"
        if promoted
        else "copy_source_decoder_policy_rejected"
    )
    return {
        "schema": "copy_source_policy_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {"copy_source_ledger": str(LEDGER.relative_to(ROOT))},
        "scope": {
            "analysis_only": True,
            "exact_skeleton_granted": True,
            "literal_payload_granted": True,
            "decoder_visible_policies_do_not_use_target_matching": True,
            "target_aware_controls_separated": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "policy_count": len(specs),
            "decoder_visible_policy_count": len(decoder_visible),
            "target_aware_control_count": len(target_aware),
            "copy_events": len(rows),
            "best_decoder_policy": best_decoder["policy"],
            "best_decoder_chunk_hits": best_decoder["chunk_hit_events"],
            "best_decoder_source_exact": best_decoder["source_exact_events"],
            "best_decoder_exact_books_sequential": best_decoder_render["exact_books"],
            "best_decoder_book_total": best_decoder_render["book_total"],
            "best_oracle_policy": best_oracle["policy"],
            "best_oracle_chunk_hits": best_oracle["chunk_hit_events"],
            "best_oracle_source_exact": best_oracle["source_exact_events"],
            "promotes_copy_source_generator": promoted,
            "interpretation": (
                "Decoder-visible source policies do not remove the source field. "
                "Target-aware matching controls can copy correctly, but they use "
                "the target chunk and are therefore parser/oracle controls, not "
                "generation rules."
            ),
        },
        "row_policy_scoreboard": [
            {key: value for key, value in row.items() if key != "rows"} for row in row_scores
        ],
        "sequential_render_scoreboard": render_scores,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "copy_source_status": "external_after_policy_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Copy Source Policy Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Grant the exact skeleton and literal payload, then test whether simple",
        "decoder-visible source policies can replace the declared copy-source",
        "fields. Target-aware matching policies are kept only as oracle controls.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_events']}`.",
        f"- Decoder-visible policies: `{s['decoder_visible_policy_count']}`.",
        f"- Target-aware controls: `{s['target_aware_control_count']}`.",
        f"- Best decoder-visible policy: `{s['best_decoder_policy']}`.",
        f"- Best decoder-visible chunk hits: `{s['best_decoder_chunk_hits']}/{s['copy_events']}`.",
        f"- Best decoder-visible exact sources: `{s['best_decoder_source_exact']}/{s['copy_events']}`.",
        f"- Best decoder-visible sequential exact books: `{s['best_decoder_exact_books_sequential']}/{s['best_decoder_book_total']}`.",
        f"- Best oracle control: `{s['best_oracle_policy']}`.",
        f"- Best oracle chunk hits: `{s['best_oracle_chunk_hits']}/{s['copy_events']}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Target-aware | Chunk hits | Source exact |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["row_policy_scoreboard"]:
        lines.append(
            f"| `{row['policy']}` | `{row['target_aware']}` | "
            f"`{row['chunk_hit_events']}/{row['copy_events']}` | "
            f"`{row['source_exact_events']}/{row['copy_events']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes copy-source generator: `{s['promotes_copy_source_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
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
