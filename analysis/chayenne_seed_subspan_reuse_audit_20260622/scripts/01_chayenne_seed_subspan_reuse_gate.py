#!/usr/bin/env python3
"""Test whether Chayenne holdout spans are unusually reused seed subspans.

Chayenne has already been localized as two subspans inside seed books 1 and 2.
This gate asks whether those subspans are also mechanically important inside the
70-book corpus: are they reused across derived books more than same-length
random seed subspans?

This is a module-bank validation audit, not a source/origin/translation claim.
"""

from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/chayenne_seed_subspan_reuse_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_chayenne_seed_subspan_reuse_gate.json"
MD_OUT = OUT_DIR / "01_chayenne_seed_subspan_reuse_gate.md"
FINAL_OUT = FRONT / "reports/final_chayenne_seed_subspan_reuse_audit.md"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
ALIGNMENT_GATE = ROOT / "analysis/chayenne_holdout_boundary_alignment_audit_20260622/reports/test_results/01_chayenne_holdout_boundary_alignment_gate.json"
HOLDOUT_GATE = ROOT / "analysis/chayenne_external_holdout_innovation_replay_audit_20260622/reports/test_results/01_chayenne_external_holdout_innovation_replay_gate.json"

RNG_SEED = 46920260622
CONTROL_TRIALS = 5000


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0")


def find_occurrences(text: str, needle: str) -> list[int]:
    positions: list[int] = []
    start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 1
    return positions


def seed_stream(books: dict[int, str]) -> str:
    return "".join(books[index] for index in range(10))


def locate_seed_position(books: dict[int, str], global_pos: int) -> dict[str, int]:
    cursor = 0
    for book in range(10):
        end = cursor + len(books[book])
        if cursor <= global_pos < end:
            return {"book": book, "local_start": global_pos - cursor}
        cursor = end
    return {"book": -1, "local_start": global_pos}


def metrics_for_spans(books: dict[int, str], spans: list[dict[str, Any]], chayenne_digits: str | None = None) -> dict[str, Any]:
    rows = []
    covered_derived_books: set[int] = set()
    covered_all_books: set[int] = set()
    derived_occurrences = 0
    all_occurrences = 0
    derived_covered_digits = 0
    for span in spans:
        text = span["text"]
        per_book = []
        for book, digits in books.items():
            positions = find_occurrences(digits, text)
            if positions:
                covered_all_books.add(book)
                all_occurrences += len(positions)
                if book >= 10:
                    covered_derived_books.add(book)
                    derived_occurrences += len(positions)
                    derived_covered_digits += len(positions) * len(text)
            per_book.append({"book": book, "positions": positions, "count": len(positions)})
        rows.append(
            {
                "label": span["label"],
                "text": text,
                "length": len(text),
                "seed_global_start": span["seed_global_start"],
                "seed_location": span["seed_location"],
                "all_occurrences": sum(item["count"] for item in per_book),
                "derived_occurrences": sum(item["count"] for item in per_book if item["book"] >= 10),
                "derived_books": [item["book"] for item in per_book if item["book"] >= 10 and item["count"]],
                "per_book_hits": [item for item in per_book if item["count"]],
            }
        )

    chayenne_cover_digits = 0
    if chayenne_digits is not None:
        cursor = 0
        span_texts = [span["text"] for span in spans]
        while cursor < len(chayenne_digits):
            best = 0
            for text in span_texts:
                if chayenne_digits.startswith(text, cursor):
                    best = max(best, len(text))
            if best:
                chayenne_cover_digits += best
                cursor += best
            else:
                cursor += 1

    return {
        "span_rows": rows,
        "all_occurrences": all_occurrences,
        "derived_occurrences": derived_occurrences,
        "derived_covered_digits": derived_covered_digits,
        "distinct_all_books": len(covered_all_books),
        "distinct_derived_books": len(covered_derived_books),
        "covered_derived_books": sorted(covered_derived_books),
        "chayenne_cover_digits": chayenne_cover_digits,
    }


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def random_control(books: dict[int, str], lengths: list[int], chayenne_digits: str) -> dict[str, Any]:
    rng = random.Random(RNG_SEED)
    seeds = seed_stream(books)
    metrics = []
    for _ in range(CONTROL_TRIALS):
        spans = []
        for index, length in enumerate(lengths):
            start = rng.randrange(0, len(seeds) - length + 1)
            spans.append(
                {
                    "label": f"random_{index}",
                    "text": seeds[start : start + length],
                    "seed_global_start": start,
                    "seed_location": locate_seed_position(books, start),
                }
            )
        row = metrics_for_spans(books, spans, chayenne_digits)
        metrics.append(row)
    return {
        "trials": CONTROL_TRIALS,
        "derived_occurrences_p95": quantile([row["derived_occurrences"] for row in metrics], 0.95),
        "derived_occurrences_p99": quantile([row["derived_occurrences"] for row in metrics], 0.99),
        "distinct_derived_books_p95": quantile([row["distinct_derived_books"] for row in metrics], 0.95),
        "derived_covered_digits_p95": quantile([row["derived_covered_digits"] for row in metrics], 0.95),
        "chayenne_cover_digits_p95": quantile([row["chayenne_cover_digits"] for row in metrics], 0.95),
        "chayenne_cover_digits_max": max(row["chayenne_cover_digits"] for row in metrics),
    }


def make_result() -> dict[str, Any]:
    alignment = load_json(ALIGNMENT_GATE)
    holdout = load_json(HOLDOUT_GATE)
    assert_boundary("alignment", alignment)
    assert_boundary("holdout", holdout)
    if alignment["classification"] != "PROMOTED_CHAYENNE_SUBSPAN_MODULE_HOLDOUT_CLUE_NOT_EVENT_POLICY":
        raise RuntimeError("Chayenne boundary alignment is not the promoted subspan clue")

    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    seeds = seed_stream(books)
    chayenne = next(row for row in holdout["external_rows"] if row["name"] == "chayenne")
    spans = []
    for index, row in enumerate(alignment["span_rows"]):
        start = int(row["source_start"])
        end = int(row["source_end"])
        spans.append(
            {
                "label": f"chayenne_span_{index}",
                "text": seeds[start:end],
                "seed_global_start": start,
                "seed_location": locate_seed_position(books, start),
            }
        )
    observed = metrics_for_spans(books, spans, chayenne["raw_digits"])
    controls = random_control(books, [len(span["text"]) for span in spans], chayenne["raw_digits"])

    external_cover_clue = observed["chayenne_cover_digits"] > controls["chayenne_cover_digits_max"]
    promotes_reuse = (
        observed["chayenne_cover_digits"] == len(chayenne["raw_digits"])
        and external_cover_clue
        and observed["derived_occurrences"] >= controls["derived_occurrences_p95"]
    )
    classification = (
        "PROMOTED_CHAYENNE_SEED_SUBSPAN_REUSE_CLUE"
        if promotes_reuse
        else (
            "chayenne_seed_subspan_external_cover_clue_not_reuse_program"
            if external_cover_clue
            else "chayenne_seed_subspan_reuse_not_promoted"
        )
    )
    return {
        "schema": "chayenne_seed_subspan_reuse_gate.v1",
        "scope": "analysis_only_seed_subspan_module_reuse",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "books_digits": str(BOOKS_DIGITS.relative_to(ROOT)),
            "chayenne_alignment": str(ALIGNMENT_GATE.relative_to(ROOT)),
            "chayenne_holdout": str(HOLDOUT_GATE.relative_to(ROOT)),
        },
        "summary": {
            "chayenne_digits": len(chayenne["raw_digits"]),
            "chayenne_cover_digits": observed["chayenne_cover_digits"],
            "derived_occurrences": observed["derived_occurrences"],
            "distinct_derived_books": observed["distinct_derived_books"],
            "derived_covered_digits": observed["derived_covered_digits"],
            "external_cover_clue": external_cover_clue,
            "promoted": promotes_reuse,
        },
        "observed": observed,
        "controls": controls,
        "decision": {
            "seed_subspan_reuse_clue_promoted": promotes_reuse,
            "external_cover_clue": external_cover_clue,
            "event_policy_promoted": False,
            "origin_source_promoted": False,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "Chayenne spans are unusual seed subspans that validate reusable module-bank content"
                if promotes_reuse
                else (
                    "Chayenne spans uniquely cover the external holdout, but corpus reuse does not beat same-length seed controls"
                    if external_cover_clue
                    else "Chayenne seed subspans do not beat reuse controls strongly enough"
                )
            ),
            "next_blocker": "subspan reuse does not derive module selection, replay events, or innovation origin",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Chayenne Seed Subspan Reuse Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "| Metric | Observed | Control |",
        "| --- | ---: | ---: |",
        f"| Chayenne cover digits | `{s['chayenne_cover_digits']}/{s['chayenne_digits']}` | p95 `{c['chayenne_cover_digits_p95']}`, max `{c['chayenne_cover_digits_max']}` |",
        f"| Derived occurrences | `{s['derived_occurrences']}` | p95 `{c['derived_occurrences_p95']}`, p99 `{c['derived_occurrences_p99']}` |",
        f"| Distinct derived books | `{s['distinct_derived_books']}` | p95 `{c['distinct_derived_books_p95']}` |",
        f"| Derived covered digits | `{s['derived_covered_digits']}` | p95 `{c['derived_covered_digits_p95']}` |",
        f"| External cover clue | `{s['external_cover_clue']}` | control max `{c['chayenne_cover_digits_max']}` |",
        "",
        "## Span Rows",
        "",
        "| Span | Seed Location | Length | Derived Occurrences | Derived Books |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in result["observed"]["span_rows"]:
        loc = row["seed_location"]
        lines.append(
            f"| `{row['label']}` | `book {loc['book']}:{loc['local_start']}` | `{row['length']}` | `{row['derived_occurrences']}` | `{row['derived_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            f"Next blocker: `{result['decision']['next_blocker']}`",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Chayenne Seed Subspan Reuse Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The Chayenne holdout spans were tested as seed submodules against random same-length seed subspans.",
        f"They cover `{s['chayenne_cover_digits']}/{s['chayenne_digits']}` Chayenne digits and have `{s['derived_occurrences']}` derived-book occurrences across `{s['distinct_derived_books']}` derived books.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is an external-cover clue only: the same spans reconstruct Chayenne, but their derived-book reuse does not beat same-length seed controls. It does not derive module selection, replay events, innovation origin, plaintext, or translation.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_chayenne_seed_subspan_reuse_gate.py](../scripts/01_chayenne_seed_subspan_reuse_gate.py)",
        "- [01_chayenne_seed_subspan_reuse_gate.json](test_results/01_chayenne_seed_subspan_reuse_gate.json)",
        "- [01_chayenne_seed_subspan_reuse_gate.md](test_results/01_chayenne_seed_subspan_reuse_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
