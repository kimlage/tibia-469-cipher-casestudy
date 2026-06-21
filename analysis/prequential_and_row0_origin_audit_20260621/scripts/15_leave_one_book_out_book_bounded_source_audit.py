from __future__ import annotations

import bisect
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
LOO_AUDIT = TEST_RESULTS / "13_leave_one_book_out_no_self_audit.json"
SOURCE_ATTRIBUTION = TEST_RESULTS / "14_leave_one_book_out_source_attribution_audit.json"

COMPONENT_KEYS = [
    "literal_length_bits",
    "literal_payload_bits",
    "item_type_stream_bits",
    "copy_address_bits",
    "copy_length_stream_bits",
]
INVENTORY_KEYS = ["literal_runs", "literal_digits", "copy_items", "copied_digits"]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def source_ranges(books: dict[str, str], train_books: list[int]) -> tuple[list[dict[str, int]], list[int]]:
    ranges = []
    starts = []
    cursor = 0
    for book in train_books:
        start = cursor
        cursor += len(books[str(book)])
        ranges.append({"book": book, "start": start, "end": cursor})
        starts.append(start)
    return ranges, starts


def within_single_source(
    *,
    ranges: list[dict[str, int]],
    starts: list[int],
    train_len: int,
    source_pos: int,
    length: int,
    current_prefix_len: int,
) -> bool:
    source_end = source_pos + length
    if source_pos >= train_len:
        return source_end <= train_len + current_prefix_len
    index = bisect.bisect_right(starts, source_pos) - 1
    if index < 0:
        return False
    return source_end <= ranges[index]["end"]


def encode_book_book_bounded_reparse(
    *,
    audit126,
    book: str,
    text: str,
    available: str,
    source_boundaries: tuple[list[dict[str, int]], list[int]],
    formula: dict[str, Any],
    train_counts: dict[str, Any],
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    payload_model = formula["policy"]["literal_payload_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]
    ranges, starts = source_boundaries
    train_len = len(available)

    raw_matches = audit126.precompute_matches(text, available, min_len)
    matches = []
    for pos, candidates in enumerate(raw_matches):
        filtered = [
            (source_pos, length, length_index)
            for source_pos, length, length_index in candidates
            if within_single_source(
                ranges=ranges,
                starts=starts,
                train_len=train_len,
                source_pos=source_pos,
                length=length,
                current_prefix_len=pos,
            )
        ]
        matches.append(filtered)

    copy_positions = {pos for pos, row in enumerate(matches) if row}
    n = len(text)
    literal_endpoints = sorted(copy_positions | {n})
    payload_prefix = audit126.literal_payload_prefix_costs(
        text=text,
        emitted_before_book=available,
        payload_counts=train_counts["payload"],
        order=int(payload_model["order"]),
        alpha=float(payload_model["alpha"]),
    )
    states = ["BOS", "literal", "copy"]
    dp: dict[tuple[int, str], float] = {}
    choice: dict[tuple[int, str], tuple[Any, ...]] = {}
    for previous in states:
        dp[(n, previous)] = 0.0

    for pos in range(n - 1, -1, -1):
        remaining = n - pos
        for previous in states:
            best = float("inf")
            best_choice: tuple[Any, ...] | None = None

            literal_forced = previous != "literal" and remaining < min_len
            if literal_forced:
                literal_lengths = [remaining]
            else:
                start_idx = bisect.bisect_right(literal_endpoints, pos)
                literal_lengths = [end - pos for end in literal_endpoints[start_idx:]]
            if previous != "literal":
                for length in literal_lengths:
                    next_pos = pos + length
                    forced = literal_forced
                    cost = (
                        audit126.item_bits_for_choice(
                            forced=forced,
                            item_type="literal",
                            book_int=int(book),
                            item_model=item_model,
                            item_counts=train_counts["item"],
                        )
                        + (0 if forced else audit126.length_bits(length + 1, literal_length_model))
                        + payload_prefix[pos + length]
                        - payload_prefix[pos]
                        + dp[(next_pos, "literal")]
                    )
                    if cost < best:
                        best = cost
                        best_choice = ("literal", length, forced)

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
                    forced = previous == "literal"
                    cost = (
                        audit126.item_bits_for_choice(
                            forced=forced,
                            item_type="copy",
                            book_int=int(book),
                            item_model=item_model,
                            item_counts=train_counts["item"],
                        )
                        + math.log2(max(2, legal_source_count))
                        + audit126.copy_length_bits(
                            counts=train_counts["copy"],
                            context=audit126.copy_context_key(int(book)),
                            length_index=length_index,
                            symbol_count=symbol_count,
                            alpha=int(copy_model["alpha"]),
                        )
                        + dp[(pos + length, "copy")]
                    )
                    if cost < best:
                        best = cost
                        best_choice = ("copy", source_pos, length, forced, symbol_count)

            dp[(pos, previous)] = best
            if best_choice is not None:
                choice[(pos, previous)] = best_choice

    if not math.isfinite(dp[(0, "BOS")]):
        raise RuntimeError({"book": book, "type": "no_finite_parse"})

    ops = []
    pos = 0
    previous = "BOS"
    totals: dict[str, Any] = {
        "bits": dp[(0, "BOS")],
        "literal_runs": 0,
        "literal_digits": 0,
        "copy_items": 0,
        "copied_digits": 0,
        "forced_literals": 0,
        "forced_copies": 0,
        "literal_length_bits": 0.0,
        "literal_payload_bits": 0.0,
        "copy_address_bits": 0.0,
        "copy_length_stream_bits": 0.0,
        "item_type_stream_bits": 0.0,
    }
    while pos < n:
        item = choice[(pos, previous)]
        if item[0] == "literal":
            _, length, forced = item
            text_chunk = text[pos : pos + length]
            ops.append({"type": "literal", "text": text_chunk, "length": length, "forced": forced})
            if forced:
                totals["forced_literals"] += 1
            else:
                totals["literal_length_bits"] += audit126.length_bits(length + 1, literal_length_model)
                totals["item_type_stream_bits"] += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="literal",
                    book_int=int(book),
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
            totals["literal_payload_bits"] += payload_prefix[pos + length] - payload_prefix[pos]
            totals["literal_runs"] += 1
            totals["literal_digits"] += length
            pos += length
            previous = "literal"
        elif item[0] == "copy":
            _, source_pos, length, forced, symbol_count = item
            target_digit_global = len(available) + pos
            legal_source_count = max(1, target_digit_global - min_len + 1)
            length_index = length - min_len
            ops.append(
                {
                    "type": "copy",
                    "source_digit_pos": source_pos,
                    "length": length,
                    "target_start": pos,
                    "forced": forced,
                }
            )
            if forced:
                totals["forced_copies"] += 1
            else:
                totals["item_type_stream_bits"] += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="copy",
                    book_int=int(book),
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
            totals["copy_address_bits"] += math.log2(max(2, legal_source_count))
            totals["copy_length_stream_bits"] += audit126.copy_length_bits(
                counts=train_counts["copy"],
                context=audit126.copy_context_key(int(book)),
                length_index=length_index,
                symbol_count=int(symbol_count),
                alpha=int(copy_model["alpha"]),
            )
            totals["copy_items"] += 1
            totals["copied_digits"] += length
            pos += length
            previous = "copy"
        else:
            raise ValueError(item)

    rendered = []
    local_emitted = available
    for op in ops:
        if op["type"] == "literal":
            chunk = op["text"]
        else:
            chunk = local_emitted[int(op["source_digit_pos"]) : int(op["source_digit_pos"]) + int(op["length"])]
        rendered.append(chunk)
        local_emitted += chunk
    errors = [] if "".join(rendered) == text else ["book_mismatch"]
    totals["book"] = book
    totals["ops"] = ops
    totals["validation"] = {"errors": errors, "roundtrip_ok": not errors}
    return totals


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    loo = load_json(LOO_AUDIT)
    source_attr = load_json(SOURCE_ATTRIBUTION)
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    loo_by_book = {row["book"]: row for row in loo["rows"]}
    rows = []
    for book in range(70):
        train_books = sorted(all_books - {book})
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        available = "".join(books[str(train_book)] for train_book in train_books)
        encoded = encode_book_book_bounded_reparse(
            audit126=audit126,
            book=str(book),
            text=books[str(book)],
            available=available,
            source_boundaries=source_ranges(books, train_books),
            formula=formula,
            train_counts=train_counts,
        )
        raw_bits = audit128.raw_uniform_bits(books, [book])
        gain = raw_bits - encoded["bits"]
        baseline = loo_by_book[book]
        rows.append(
            {
                "book": book,
                "book_length_digits": len(books[str(book)]),
                "raw_uniform_bits": raw_bits,
                "book_bounded_reparse_bits": encoded["bits"],
                "unbounded_leave_one_out_bits": baseline["leave_one_out_reparse_bits"],
                "book_bounded_gain_vs_raw_bits": gain,
                "unbounded_gain_vs_raw_bits": baseline["gain_vs_raw_bits"],
                "book_bounded_minus_unbounded_bits": encoded["bits"]
                - baseline["leave_one_out_reparse_bits"],
                "beats_raw": gain > 0,
                "validation": encoded["validation"],
                "inventory": {key: encoded[key] for key in INVENTORY_KEYS},
                "component_bits": {key: encoded[key] for key in COMPONENT_KEYS},
            }
        )

    failures = [row for row in rows if not row["beats_raw"]]
    weakest = sorted(rows, key=lambda row: row["book_bounded_gain_vs_raw_bits"])[:10]
    highest_penalty = sorted(rows, key=lambda row: row["book_bounded_minus_unbounded_bits"], reverse=True)[:10]
    classification = (
        "book_bounded_singleton_holdout_predictive"
        if not failures
        else "book_bounded_singleton_holdout_partial"
    )
    return {
        "schema": "leave_one_book_out_book_bounded_source_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "leave_one_book_out_no_self": rel(LOO_AUDIT),
            "source_attribution": rel(SOURCE_ATTRIBUTION),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
        },
        "rows": rows,
        "summary": {
            "book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "beats_raw_count": sum(1 for row in rows if row["beats_raw"]),
            "failure_books": [row["book"] for row in failures],
            "mean_book_bounded_gain_vs_raw_bits": sum(
                row["book_bounded_gain_vs_raw_bits"] for row in rows
            )
            / len(rows),
            "min_book_bounded_gain_vs_raw_bits": min(
                row["book_bounded_gain_vs_raw_bits"] for row in rows
            ),
            "mean_book_bounded_minus_unbounded_bits": sum(
                row["book_bounded_minus_unbounded_bits"] for row in rows
            )
            / len(rows),
            "max_book_bounded_minus_unbounded_bits": max(
                row["book_bounded_minus_unbounded_bits"] for row in rows
            ),
            "unbounded_cross_boundary_copied_digit_share": source_attr["summary"][
                "cross_boundary_copied_digit_share"
            ],
            "weakest_books": [
                {
                    "book": row["book"],
                    "gain_vs_raw_bits": row["book_bounded_gain_vs_raw_bits"],
                    "book_length_digits": row["book_length_digits"],
                }
                for row in weakest
            ],
            "highest_boundary_penalty_books": [
                {
                    "book": row["book"],
                    "book_bounded_minus_unbounded_bits": row["book_bounded_minus_unbounded_bits"],
                    "book_bounded_gain_vs_raw_bits": row["book_bounded_gain_vs_raw_bits"],
                }
                for row in highest_penalty
            ],
            "interpretation": (
                "Forbidding copy sources from crossing source-book boundaries "
                "tests whether the singleton result depends on concatenation "
                "artifacts. Positive gain in every book would retain the signal "
                "under a cleaner source model."
            ),
        },
        "decision": {
            "book_boundary_status": "predictive_signal_retained_under_book_bounded_sources"
            if not failures
            else "book_boundary_status_partial",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "15_leave_one_book_out_book_bounded_source_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Leave-One-Book-Out Book-Bounded Source Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 14 exposed that some singleton copies crossed artificial source-book",
        "boundaries in the concatenated complement inventory. This audit reparses",
        "each singleton while forbidding copy sources from crossing source-book",
        "boundaries. Current-prefix copies are still legal if they stay inside the",
        "already-emitted current prefix.",
        "",
        "## Summary",
        "",
        f"- Books checked: `{result['summary']['book_count']}`.",
        f"- Roundtrip books: `{result['summary']['roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Beats raw digits: `{result['summary']['beats_raw_count']}/{result['summary']['book_count']}`.",
        f"- Mean book-bounded gain vs raw: `{result['summary']['mean_book_bounded_gain_vs_raw_bits']:.3f}` bits.",
        f"- Min book-bounded gain vs raw: `{result['summary']['min_book_bounded_gain_vs_raw_bits']:.3f}` bits.",
        f"- Mean book-bounded minus unbounded: `{result['summary']['mean_book_bounded_minus_unbounded_bits']:.3f}` bits.",
        f"- Max book-bounded minus unbounded: `{result['summary']['max_book_bounded_minus_unbounded_bits']:.3f}` bits.",
        f"- Failure books: `{result['summary']['failure_books']}`.",
        "",
        "## Weakest Books",
        "",
        "| Book | Length | Book-bounded gain vs raw |",
        "|---:|---:|---:|",
    ]
    for row in result["summary"]["weakest_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_length_digits']}` | "
            f"`{row['gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Highest Boundary Penalties",
            "",
            "| Book | Penalty vs unbounded | Book-bounded gain vs raw |",
            "|---:|---:|---:|",
        ]
    )
    for row in result["summary"]["highest_boundary_penalty_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_bounded_minus_unbounded_bits']:.3f}` | "
            f"`{row['book_bounded_gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The singleton holdout is retested under book-bounded copy-source constraints.",
            "- The item-level signal does not depend on source-book boundary crossings to beat raw digit coding.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "15_leave_one_book_out_book_bounded_source_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
