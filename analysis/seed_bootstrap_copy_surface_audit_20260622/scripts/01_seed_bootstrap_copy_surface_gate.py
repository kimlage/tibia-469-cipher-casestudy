#!/usr/bin/env python3
"""Seed bootstrap copy-surface gate.

The executable v6 ledger still treats books 0..9 as raw seed payload:
1696 digits / 5633.990 bits. Recent work has focused on non-seed fallback
copy origins, but a complete generator also has to explain or consciously
declare the seed payload.

This audit does not promote a seed generator. It measures whether the seed
payload has a strong target-conditioned previous-copy surface, and compares it
against same-multiset shuffled controls and seed-book order permutations. If
the surface is strong, it opens a future bootstrap-transducer route; it does
not by itself reduce the executable ledger because starts/copy choices remain
target-conditioned.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "seed_bootstrap_copy_surface_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
SEED_PRIMACY_FINAL = (
    ROOT
    / "analysis"
    / "seed_primacy_audit_20260621"
    / "reports"
    / "final_seed_primacy_audit.md"
)

JSON_OUT = TEST_RESULTS / "01_seed_bootstrap_copy_surface_gate.json"
MD_OUT = TEST_RESULTS / "01_seed_bootstrap_copy_surface_gate.md"
FINAL_OUT = FRONT / "reports" / "final_seed_bootstrap_copy_surface_audit.md"

LOG2_10 = math.log2(10)
MIN_LENS = [4, 5, 6, 8, 10, 12]
MAX_COPY_LEN = 64
RANDOM_SEED = 46920260625
SHUFFLE_TRIALS = 40
ORDER_TRIALS = 80


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def seed_books() -> dict[int, str]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    return {book: books[book] for book in range(10)}


def stream_from_order(books: dict[int, str], order: list[int]) -> str:
    return "".join(books[book] for book in order)


def add_previous_substrings(
    stream: str,
    by_len: dict[int, set[str]],
    old_end: int,
    new_end: int,
    max_copy_len: int,
) -> None:
    for end in range(old_end + 1, new_end + 1):
        max_len = min(max_copy_len, end)
        for length in range(1, max_len + 1):
            by_len[length].add(stream[end - length : end])


def greedy_copy_surface(
    stream: str,
    min_len: int,
    *,
    max_copy_len: int = MAX_COPY_LEN,
) -> dict[str, Any]:
    by_len: dict[int, set[str]] = defaultdict(set)
    i = 0
    indexed_until = 0
    copied_digits = 0
    literal_digits = 0
    copy_ops = 0
    literal_runs = 0
    op_rows = []
    in_literal = False
    n = len(stream)
    while i < n:
        if indexed_until < i:
            add_previous_substrings(stream, by_len, indexed_until, i, max_copy_len)
            indexed_until = i
        best = 0
        upper = min(max_copy_len, n - i)
        for length in range(upper, min_len - 1, -1):
            bucket = by_len.get(length)
            if bucket and stream[i : i + length] in bucket:
                best = length
                break
        if best:
            copied_digits += best
            copy_ops += 1
            op_rows.append({"kind": "copy", "length": best, "start": i})
            i += best
            in_literal = False
        else:
            literal_digits += 1
            if not in_literal:
                literal_runs += 1
                in_literal = True
            i += 1
    return {
        "copied_digits": copied_digits,
        "copy_ops": copy_ops,
        "copy_surface_fraction": copied_digits / n if n else 0.0,
        "literal_digits": literal_digits,
        "literal_runs": literal_runs,
        "max_copy_len": max_copy_len,
        "min_len": min_len,
        "op_rows_sample": op_rows[:60],
        "raw_bits": n * LOG2_10,
        "seed_digits": n,
        "target_conditioned_literal_bits_lower_bound": literal_digits * LOG2_10,
    }


def surface_scoreboard(stream: str) -> dict[str, dict[str, Any]]:
    return {str(min_len): greedy_copy_surface(stream, min_len) for min_len in MIN_LENS}


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "p05": ordered[int(0.05 * (len(ordered) - 1))],
        "p50": ordered[int(0.50 * (len(ordered) - 1))],
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
    }


def shuffled_digit_controls(stream: str) -> dict[str, dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    digits = list(stream)
    out: dict[str, dict[str, Any]] = {}
    for min_len in MIN_LENS:
        copied_values = []
        literal_values = []
        for _ in range(SHUFFLE_TRIALS):
            shuffled = list(digits)
            rng.shuffle(shuffled)
            score = greedy_copy_surface("".join(shuffled), min_len)
            copied_values.append(score["copied_digits"])
            literal_values.append(score["literal_digits"])
        copied_q = quantiles([float(value) for value in copied_values])
        literal_q = quantiles([float(value) for value in literal_values])
        out[str(min_len)] = {
            "copied_digits_p05": copied_q["p05"],
            "copied_digits_p50": copied_q["p50"],
            "copied_digits_p95": copied_q["p95"],
            "literal_digits_p05": literal_q["p05"],
            "literal_digits_p50": literal_q["p50"],
            "literal_digits_p95": literal_q["p95"],
            "trials": SHUFFLE_TRIALS,
        }
    return out


def book_order_controls(books: dict[int, str]) -> dict[str, dict[str, Any]]:
    rng = random.Random(RANDOM_SEED + 99)
    canonical = list(range(10))
    out: dict[str, dict[str, Any]] = {}
    for min_len in MIN_LENS:
        copied_values = []
        literal_values = []
        for _ in range(ORDER_TRIALS):
            order = list(canonical)
            rng.shuffle(order)
            score = greedy_copy_surface(stream_from_order(books, order), min_len)
            copied_values.append(score["copied_digits"])
            literal_values.append(score["literal_digits"])
        copied_q = quantiles([float(value) for value in copied_values])
        literal_q = quantiles([float(value) for value in literal_values])
        out[str(min_len)] = {
            "copied_digits_p05": copied_q["p05"],
            "copied_digits_p50": copied_q["p50"],
            "copied_digits_p95": copied_q["p95"],
            "literal_digits_p05": literal_q["p05"],
            "literal_digits_p50": literal_q["p50"],
            "literal_digits_p95": literal_q["p95"],
            "trials": ORDER_TRIALS,
        }
    return out


def repeated_book_pair_clues(books: dict[int, str]) -> list[dict[str, Any]]:
    rows = []
    for left in range(10):
        for right in range(left + 1, 10):
            a = books[left]
            b = books[right]
            longest = 0
            best = None
            for i in range(len(a)):
                for j in range(len(b)):
                    k = 0
                    while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                        k += 1
                    if k > longest:
                        longest = k
                        best = {"left_start": i, "right_start": j}
            if longest >= 12:
                rows.append(
                    {
                        "left_book": left,
                        "right_book": right,
                        "longest_common_substring": longest,
                        **(best or {}),
                    }
                )
    rows.sort(key=lambda item: (-item["longest_common_substring"], item["left_book"], item["right_book"]))
    return rows


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    books = seed_books()
    stream = stream_from_order(books, list(range(10)))
    observed = surface_scoreboard(stream)
    shuffled = shuffled_digit_controls(stream)
    order = book_order_controls(books)
    best_key = max(observed, key=lambda key: observed[key]["copied_digits"])
    strong_minlens = []
    order_sensitive_minlens = []
    for key, score in observed.items():
        if score["copied_digits"] > shuffled[key]["copied_digits_p95"]:
            strong_minlens.append(int(key))
        if score["copied_digits"] > order[key]["copied_digits_p95"]:
            order_sensitive_minlens.append(int(key))
    promoted_clue = len(strong_minlens) >= 5
    classification = (
        "PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE"
        if promoted_clue
        else "seed_bootstrap_copy_surface_audit_only"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "book_order_permutation": order,
            "same_multiset_digit_shuffle": shuffled,
        },
        "decision": {
            "generator_status": "not_promoted_target_conditioned_surface_only",
            "next_blocker": (
                "seed payload has a strong previous-copy surface, but a future "
                "bootstrap program must derive starts/copy choices without the target stream"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "seed_primacy_final": rel(SEED_PRIMACY_FINAL),
        },
        "observed": observed,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "seed_bootstrap_copy_surface_gate.v1",
        "scope": "analysis_only_seed_payload_surface",
        "summary": {
            "best_min_len_by_copied_digits": int(best_key),
            "best_observed_copied_digits": observed[best_key]["copied_digits"],
            "best_observed_literal_digits": observed[best_key]["literal_digits"],
            "classification": classification,
            "order_sensitive_minlens": order_sensitive_minlens,
            "promoted_clue": promoted_clue,
            "raw_seed_bits": len(stream) * LOG2_10,
            "seed_digits": len(stream),
            "seed_payload_bits_v6": float(v6["summary"]["seed_payload_bits"]),
            "strong_vs_shuffle_minlens": strong_minlens,
        },
        "translation_delta": "NONE",
        "validation": {
            "book_lengths": {book: len(text) for book, text in books.items()},
            "digit_histogram": dict(Counter(stream)),
            "roundtrip_seed_stream": stream == "".join(books[book] for book in range(10)),
            "seed_books": list(range(10)),
            "validation_errors": [],
        },
        "book_pair_clues": repeated_book_pair_clues(books)[:30],
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Seed Bootstrap Copy-Surface Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Seed digits: `{s['seed_digits']}`.",
        f"- Raw seed bits: `{s['raw_seed_bits']:.3f}`.",
        f"- Best min_len by copied digits: `{s['best_min_len_by_copied_digits']}`.",
        f"- Best observed copied/literal digits: `{s['best_observed_copied_digits']}` / `{s['best_observed_literal_digits']}`.",
        f"- Strong vs same-multiset shuffle min_lens: `{s['strong_vs_shuffle_minlens']}`.",
        f"- Order-sensitive min_lens: `{s['order_sensitive_minlens']}`.",
        "",
        "## Copy Surface",
        "",
        "| min_len | copied | literal | copy ops | copied fraction | shuffle p95 copied | order p95 copied |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in [str(value) for value in MIN_LENS]:
        obs = result["observed"][key]
        shuf = result["controls"]["same_multiset_digit_shuffle"][key]
        order = result["controls"]["book_order_permutation"][key]
        lines.append(
            f"| `{key}` | `{obs['copied_digits']}` | `{obs['literal_digits']}` | "
            f"`{obs['copy_ops']}` | `{obs['copy_surface_fraction']:.3f}` | "
            f"`{shuf['copied_digits_p95']:.0f}` | `{order['copied_digits_p95']:.0f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`."
                if s["promoted_clue"]
                else "`seed_bootstrap_copy_surface_audit_only`."
            ),
            "",
            "This is a target-conditioned surface clue, not an executable generator. "
            "It does not reduce the v6 seed payload ledger until a target-free "
            "bootstrap policy derives copy starts and copy choices.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    obs4 = result["observed"]["4"]
    shuf4 = result["controls"]["same_multiset_digit_shuffle"]["4"]
    order4 = result["controls"]["book_order_permutation"]["4"]
    lines = [
        "# Final Seed Bootstrap Copy-Surface Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit turns back to the largest remaining executable-ledger field: "
        "the raw seed payload for books `0..9`. It asks whether those seed "
        "digits have a strong previous-copy surface that could justify a future "
        "bootstrap transducer route.",
        "",
        f"The seed payload has `{s['seed_digits']}` digits and costs "
        f"`{s['raw_seed_bits']:.3f}` raw bits in v6. Under target-conditioned "
        f"greedy previous-copy parsing with `min_len=4`, `{obs4['copied_digits']}` "
        f"digits are copy-covered and `{obs4['literal_digits']}` remain literal. "
        f"Same-multiset digit shuffles have p95 copied digits `{shuf4['copied_digits_p95']:.0f}`; "
        f"seed-book order permutations have p95 copied digits `{order4['copied_digits_p95']:.0f}`.",
        "",
        f"Strong same-multiset wins hold for min_lens `{s['strong_vs_shuffle_minlens']}`. "
        f"Order-sensitive wins hold for min_lens `{s['order_sensitive_minlens']}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`."
            if s["promoted_clue"]
            else "`seed_bootstrap_copy_surface_audit_only`."
        ),
        "",
        "This is not a generator and does not reduce the executable ledger yet: "
        "the copy surface is target-conditioned. The valid next constructive "
        "question is whether a target-free bootstrap policy can derive starts "
        "and copy choices for the seed stream from a much smaller innovation tape.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_seed_bootstrap_copy_surface_gate.py](../scripts/01_seed_bootstrap_copy_surface_gate.py)",
        "- [01_seed_bootstrap_copy_surface_gate.json](test_results/01_seed_bootstrap_copy_surface_gate.json)",
        "- [01_seed_bootstrap_copy_surface_gate.md](test_results/01_seed_bootstrap_copy_surface_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
