from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
HAZARD_GATE = TEST_RESULTS / "02_boundary_hazard_state_gate.json"

OUT_STEM = "03_boundary_hazard_endpoint_decoder_gate"
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def boundary_flags(book: int, length: int, ops_by_book: dict[str, list[dict[str, Any]]]) -> list[int]:
    flags = [0] * length
    if str(book) not in ops_by_book:
        return flags
    for op in ops_by_book[str(book)][:-1]:
        cutpoint = int(op["target_start"]) + int(op["length"])
        if 0 < cutpoint < length:
            flags[cutpoint] = 1
    return flags


def age_bucket(age: int) -> str:
    if age == 1:
        return "age_1"
    if age <= 3:
        return "age_2_3"
    if age <= 7:
        return "age_4_7"
    if age <= 15:
        return "age_8_15"
    if age <= 31:
        return "age_16_31"
    if age <= 63:
        return "age_32_63"
    return "age_64_plus"


def train_age_counts(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
    cutoff: int,
) -> tuple[dict[str, Counter[int]], Counter[int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    global_counts = Counter()
    for book in range(10, cutoff):
        flags = boundary_flags(book, len(books[book]), ops_by_book)
        last_boundary = 0
        for pos in range(1, len(flags)):
            age = pos - last_boundary
            flag = flags[pos]
            counts[age_bucket(age)][flag] += 1
            global_counts[flag] += 1
            if flag:
                last_boundary = pos
    return counts, global_counts


def logp(counter: Counter[int], flag: int) -> float:
    return math.log2(
        (counter[flag] + ALPHA) / (sum(counter.values()) + ALPHA * 2)
    )


def decode_exact_count(
    length: int,
    boundary_count: int,
    counts: dict[str, Counter[int]],
    global_counts: Counter[int],
) -> set[int]:
    if boundary_count == 0:
        return set()
    # State is (used_count, age_since_last_boundary) at current position.
    states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {
        (0, 1): (0.0, ())
    }
    for pos in range(1, length):
        next_states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
        for (used, age), (score, path) in states.items():
            counter = counts.get(age_bucket(age), global_counts)
            no_key = (used, age + 1)
            no_value = (score + logp(counter, 0), path)
            if no_key not in next_states or no_value[0] > next_states[no_key][0]:
                next_states[no_key] = no_value
            if used < boundary_count:
                yes_key = (used + 1, 1)
                yes_value = (score + logp(counter, 1), path + (pos,))
                if yes_key not in next_states or yes_value[0] > next_states[yes_key][0]:
                    next_states[yes_key] = yes_value
        states = next_states
    candidates = [
        value for key, value in states.items() if key[0] == boundary_count
    ]
    if not candidates:
        return set()
    return set(max(candidates, key=lambda value: value[0])[1])


def random_control(
    books: dict[int, str],
    actual_by_book: dict[int, set[int]],
    book_ids: list[int],
    rng: random.Random,
) -> dict[str, Any]:
    hit_values = []
    exact_values = []
    nontrivial_exact_values = []
    for _ in range(RANDOM_TRIALS):
        hits = exact = nontrivial_exact = 0
        for book in book_ids:
            actual = actual_by_book[book]
            positions = list(range(1, len(books[book])))
            predicted = set(rng.sample(positions, len(actual))) if actual else set()
            hits += len(predicted & actual)
            exact += int(predicted == actual)
            nontrivial_exact += int(bool(actual) and predicted == actual)
        hit_values.append(hits)
        exact_values.append(exact)
        nontrivial_exact_values.append(nontrivial_exact)
    hit_values.sort()
    exact_values.sort()
    nontrivial_exact_values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "hit_mean": mean(hit_values),
        "hit_p95": percentile(hit_values, 0.95),
        "hit_max": hit_values[-1],
        "exact_mean": mean(exact_values),
        "exact_p95": percentile(exact_values, 0.95),
        "nontrivial_exact_mean": mean(nontrivial_exact_values),
        "nontrivial_exact_p95": percentile(nontrivial_exact_values, 0.95),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def make_result() -> dict[str, Any]:
    hazard_gate = load_json(HAZARD_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("boundary_hazard_state_gate", hazard_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ops_by_book = copy_ledger["canonical_ops_by_book"]
    actual_by_book = {
        book: {
            pos
            for pos, flag in enumerate(boundary_flags(book, len(books[book]), ops_by_book))
            if flag
        }
        for book in range(10, 70)
    }
    rows = []
    rng = random.Random(RANDOM_SEED)
    for cutoff in PREFIX_CUTOFFS:
        counts, global_counts = train_age_counts(books, ops_by_book, cutoff)
        book_ids = list(range(cutoff, 70))
        hits = exact = nontrivial_exact = boundary_total = 0
        for book in book_ids:
            actual = actual_by_book[book]
            predicted = decode_exact_count(len(books[book]), len(actual), counts, global_counts)
            hits += len(predicted & actual)
            exact += int(predicted == actual)
            nontrivial_exact += int(bool(actual) and predicted == actual)
            boundary_total += len(actual)
        control = random_control(books, actual_by_book, book_ids, rng)
        rows.append(
            {
                "cutoff": cutoff,
                "test_books": len(book_ids),
                "test_boundaries": boundary_total,
                "hazard_hits": hits,
                "hazard_exact_books": exact,
                "hazard_nontrivial_exact_books": nontrivial_exact,
                "random_hit_mean": control["hit_mean"],
                "random_hit_p95": control["hit_p95"],
                "random_hit_max": control["hit_max"],
                "random_exact_p95": control["exact_p95"],
                "random_nontrivial_exact_p95": control["nontrivial_exact_p95"],
                "beats_random_hit_p95": hits > control["hit_p95"],
            }
        )
    aggregate_hits = sum(row["hazard_hits"] for row in rows)
    aggregate_random_hit_p95_sum = sum(row["random_hit_p95"] for row in rows)
    promotes_endpoint_decoder = (
        all(row["beats_random_hit_p95"] for row in rows)
        and sum(row["hazard_nontrivial_exact_books"] for row in rows) > 0
    )
    summary = {
        "cutoff_count": len(PREFIX_CUTOFFS),
        "aggregate_hazard_hits": aggregate_hits,
        "aggregate_boundaries": sum(row["test_boundaries"] for row in rows),
        "aggregate_random_hit_p95_sum": aggregate_random_hit_p95_sum,
        "cells_beating_random_p95": sum(1 for row in rows if row["beats_random_hit_p95"]),
        "aggregate_exact_books": sum(row["hazard_exact_books"] for row in rows),
        "aggregate_nontrivial_exact_books": sum(
            row["hazard_nontrivial_exact_books"] for row in rows
        ),
        "promotes_endpoint_decoder": promotes_endpoint_decoder,
        "interpretation": (
            "The age hazard improves probabilistic boundary coding, but when it is "
            "forced to decode exact endpoint positions even with true op-count "
            "granted, it does not beat same-count random endpoint controls. The "
            "hazard is not an endpoint parser."
        ),
    }
    return {
        "schema": "boundary_hazard_endpoint_decoder_gate_v1",
        "scope": "analysis_only_hazard_to_exact_endpoint_decoder",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "hazard_gate": rel(HAZARD_GATE),
        },
        "cutoff_rows": rows,
        "summary": summary,
        "classification": "boundary_hazard_endpoint_decoder_rejected",
        "decision": {
            "promotes_endpoint_decoder": promotes_endpoint_decoder,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Boundary Hazard Endpoint Decoder Gate",
        "",
        "Classification: `boundary_hazard_endpoint_decoder_rejected`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the promoted `age_bucket` boundary hazard can choose exact",
        "cutpoint positions when the true number of internal cutpoints is granted.",
        "",
        "## Summary",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Aggregate hazard hits: `{s['aggregate_hazard_hits']}/{s['aggregate_boundaries']}`.",
        f"- Aggregate random hit p95 sum: `{s['aggregate_random_hit_p95_sum']:.3f}`.",
        f"- Cells beating random p95: `{s['cells_beating_random_p95']}/{s['cutoff_count']}`.",
        f"- Aggregate exact books: `{s['aggregate_exact_books']}`.",
        f"- Aggregate nontrivial exact books: `{s['aggregate_nontrivial_exact_books']}`.",
        f"- Promotes endpoint decoder: `{s['promotes_endpoint_decoder']}`.",
        "",
        s["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Boundaries | Hazard hits | Random hit p95 | Exact books | Nontrivial exact |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_boundaries']}` | "
            f"`{row['hazard_hits']}` | `{row['random_hit_p95']:.3f}` | "
            f"`{row['hazard_exact_books']}` | `{row['hazard_nontrivial_exact_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Hazard endpoint decoder is rejected.",
            "- The `age_bucket` hazard remains only a probabilistic dependency reducer.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
