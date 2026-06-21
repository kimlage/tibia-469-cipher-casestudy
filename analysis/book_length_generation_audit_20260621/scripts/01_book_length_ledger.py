from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
PREVIOUS_BOOK_LENGTH_LEDGER = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "33_book_length_ledger_search.json"
)

OUT_STEM = "01_book_length_ledger"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def signed_rice_bits(delta: int, k: int) -> int:
    return rice_bits(abs(delta) + 1, k) + (0 if delta == 0 else 1)


def make_result() -> dict[str, Any]:
    previous = load_json(PREVIOUS_BOOK_LENGTH_LEDGER)
    assert_boundary("previous_book_length_ledger", previous)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    lengths = [len(books[index]) for index in range(70)]
    counts = Counter(lengths)
    raw_gamma_bits = sum(gamma_bits(length + 1) for length in lengths)
    anchor = int(previous["best_model"]["parameters"]["anchor"])
    k = int(previous["best_model"]["parameters"]["k"])
    active_rice_bits = gamma_bits(anchor + 1) + gamma_bits(k + 1) + sum(
        signed_rice_bits(length - anchor, k) for length in lengths
    )
    repeated_rows = sum(count for count in counts.values() if count > 1)
    summary = {
        "book_count": len(lengths),
        "length_min": min(lengths),
        "length_max": max(lengths),
        "unique_lengths": len(counts),
        "repeated_length_rows": repeated_rows,
        "most_common_lengths": counts.most_common(10),
        "raw_gamma_length_bits": raw_gamma_bits,
        "active_anchor": anchor,
        "active_k": k,
        "active_signed_rice_length_bits": active_rice_bits,
        "active_gain_vs_raw_gamma": raw_gamma_bits - active_rice_bits,
        "exact_lengths_remain_declared": True,
        "interpretation": (
            "Book lengths are clustered enough for a compact residual ledger, "
            "but the active Rice model still declares per-book residuals. It is "
            "not a generator for the length sequence."
        ),
    }
    return {
        "schema": "book_length_ledger.v1",
        "classification": "book_length_ledger_audit_only",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "previous_book_length_ledger": rel(PREVIOUS_BOOK_LENGTH_LEDGER),
        },
        "scope": {
            "analysis_only": True,
            "book_lengths_mapped": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "length_rows": [
            {"book": index, "length": length} for index, length in enumerate(lengths)
        ],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "book_length_residual_ledger_only",
            "book_length_status": "external_declared_residuals",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Book Length Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Map the 70 declared book lengths and separate residual compression",
        "from a source-free generator.",
        "",
        "## Summary",
        "",
        f"- Book count: `{s['book_count']}`.",
        f"- Length range: `{s['length_min']}..{s['length_max']}`.",
        f"- Unique lengths: `{s['unique_lengths']}`.",
        f"- Repeated length rows: `{s['repeated_length_rows']}`.",
        f"- Raw gamma length bits: `{s['raw_gamma_length_bits']}`.",
        f"- Active signed-Rice ledger: `anchor={s['active_anchor']}`, `k={s['active_k']}`, `{s['active_signed_rice_length_bits']}` bits.",
        f"- Active gain vs raw gamma: `{s['active_gain_vs_raw_gamma']}` bits.",
        "",
        "## Decision",
        "",
        f"- {s['interpretation']}",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
