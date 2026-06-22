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
BOUNDARY_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_gate.json"
)
HAZARD_GATE = TEST_RESULTS / "02_boundary_hazard_state_gate.json"
ENDPOINT_GATE = TEST_RESULTS / "03_boundary_hazard_endpoint_decoder_gate.json"

OUT_STEM = "04_combined_boundary_endpoint_decoder_gate"
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
MODEL_FAMILIES = [
    "age_only",
    "surprisal_bin_only",
    "age_plus_surprisal_bin_additive",
    "age_x_surprisal_bin_joint",
]


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


def prev2_context(prefix: str) -> tuple[str, str]:
    if not prefix:
        return ("BOS", "BOS")
    if len(prefix) == 1:
        return ("BOS", prefix[-1])
    return (prefix[-2], prefix[-1])


def train_prev2(
    books: dict[int, str],
    book_ids: list[int],
) -> tuple[dict[tuple[str, str], Counter[str]], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for book in book_ids:
        prefix = ""
        for digit in books[book]:
            counts[prev2_context(prefix)][digit] += 1
            prefix += digit
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    return counts, global_counts


def book_surprisals(books: dict[int, str], book: int) -> list[float]:
    train_ids = [candidate for candidate in sorted(books) if candidate < book]
    counts, global_counts = train_prev2(books, train_ids)
    prefix = ""
    values = []
    for digit in books[book]:
        counter = counts.get(prev2_context(prefix), global_counts)
        total = sum(counter.values())
        probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
        values.append(-math.log2(probability))
        prefix += digit
    return values


def boundary_flags(
    book: int,
    length: int,
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[int]:
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


def surprisal_bin(value: float) -> str:
    if value < 2.0:
        return "surp_lt_2"
    if value < 3.0:
        return "surp_2_3"
    if value < 4.0:
        return "surp_3_4"
    if value < 5.0:
        return "surp_4_5"
    return "surp_ge_5"


def logp(counter: Counter[int], flag: int) -> float:
    return math.log2(
        (counter[flag] + ALPHA) / (sum(counter.values()) + ALPHA * 2)
    )


def train_feature_counts(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
    cutoff: int,
) -> dict[str, Any]:
    age_counts: dict[str, Counter[int]] = defaultdict(Counter)
    surprisal_counts: dict[str, Counter[int]] = defaultdict(Counter)
    joint_counts: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    global_counts = Counter()
    for book in range(10, cutoff):
        flags = boundary_flags(book, len(books[book]), ops_by_book)
        surprisals = book_surprisals(books, book)
        last_boundary = 0
        for pos in range(1, len(flags)):
            age_key = age_bucket(pos - last_boundary)
            surp_key = surprisal_bin(surprisals[pos])
            flag = flags[pos]
            age_counts[age_key][flag] += 1
            surprisal_counts[surp_key][flag] += 1
            joint_counts[(age_key, surp_key)][flag] += 1
            global_counts[flag] += 1
            if flag:
                last_boundary = pos
    return {
        "age_counts": age_counts,
        "surprisal_counts": surprisal_counts,
        "joint_counts": joint_counts,
        "global_counts": global_counts,
    }


def score_flag(
    family: str,
    counts: dict[str, Any],
    age_key: str,
    surp_key: str,
    flag: int,
) -> float:
    global_counts = counts["global_counts"]
    if family == "age_only":
        return logp(counts["age_counts"].get(age_key, global_counts), flag)
    if family == "surprisal_bin_only":
        return logp(counts["surprisal_counts"].get(surp_key, global_counts), flag)
    if family == "age_plus_surprisal_bin_additive":
        return (
            logp(counts["age_counts"].get(age_key, global_counts), flag)
            + logp(counts["surprisal_counts"].get(surp_key, global_counts), flag)
            - logp(global_counts, flag)
        )
    if family == "age_x_surprisal_bin_joint":
        return logp(counts["joint_counts"].get((age_key, surp_key), global_counts), flag)
    raise KeyError(family)


def decode_exact_count(
    family: str,
    target: str,
    boundary_count: int,
    surprisals: list[float],
    counts: dict[str, Any],
) -> set[int]:
    if boundary_count == 0:
        return set()
    states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {
        (0, 1): (0.0, ())
    }
    for pos in range(1, len(target)):
        next_states: dict[tuple[int, int], tuple[float, tuple[int, ...]]] = {}
        surp_key = surprisal_bin(surprisals[pos])
        for (used, age), (score, path) in states.items():
            age_key = age_bucket(age)
            no_key = (used, age + 1)
            no_value = (
                score + score_flag(family, counts, age_key, surp_key, 0),
                path,
            )
            if no_key not in next_states or no_value[0] > next_states[no_key][0]:
                next_states[no_key] = no_value
            if used < boundary_count:
                yes_key = (used + 1, 1)
                yes_value = (
                    score + score_flag(family, counts, age_key, surp_key, 1),
                    path + (pos,),
                )
                if yes_key not in next_states or yes_value[0] > next_states[yes_key][0]:
                    next_states[yes_key] = yes_value
        states = next_states
    candidates = [value for key, value in states.items() if key[0] == boundary_count]
    if not candidates:
        return set()
    return set(max(candidates, key=lambda value: value[0])[1])


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


def make_result() -> dict[str, Any]:
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    boundary_gate = load_json(BOUNDARY_GATE)
    hazard_gate = load_json(HAZARD_GATE)
    endpoint_gate = load_json(ENDPOINT_GATE)
    for name, data in [
        ("copy_source_ledger", copy_ledger),
        ("target_digit_boundary_gate", boundary_gate),
        ("boundary_hazard_state_gate", hazard_gate),
        ("boundary_hazard_endpoint_decoder_gate", endpoint_gate),
    ]:
        assert_boundary(name, data)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ops_by_book = copy_ledger["canonical_ops_by_book"]
    surprisals_by_book = {
        book: book_surprisals(books, book)
        for book in range(10, 70)
    }
    actual_by_book = {
        book: {
            pos
            for pos, flag in enumerate(boundary_flags(book, len(books[book]), ops_by_book))
            if flag
        }
        for book in range(10, 70)
    }
    random_by_cutoff = {}
    rng = random.Random(RANDOM_SEED)
    for cutoff in PREFIX_CUTOFFS:
        book_ids = list(range(cutoff, 70))
        random_by_cutoff[cutoff] = random_control(books, actual_by_book, book_ids, rng)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        counts = train_feature_counts(books, ops_by_book, cutoff)
        book_ids = list(range(cutoff, 70))
        for family in MODEL_FAMILIES:
            hits = exact = nontrivial_exact = boundary_total = 0
            for book in book_ids:
                actual = actual_by_book[book]
                predicted = decode_exact_count(
                    family,
                    books[book],
                    len(actual),
                    surprisals_by_book[book],
                    counts,
                )
                hits += len(predicted & actual)
                exact += int(predicted == actual)
                nontrivial_exact += int(bool(actual) and predicted == actual)
                boundary_total += len(actual)
            control = random_by_cutoff[cutoff]
            rows.append(
                {
                    "cutoff": cutoff,
                    "family": family,
                    "test_books": len(book_ids),
                    "test_boundaries": boundary_total,
                    "hits": hits,
                    "exact_books": exact,
                    "nontrivial_exact_books": nontrivial_exact,
                    "random_hit_mean": control["hit_mean"],
                    "random_hit_p95": control["hit_p95"],
                    "random_hit_max": control["hit_max"],
                    "random_exact_p95": control["exact_p95"],
                    "random_nontrivial_exact_p95": control["nontrivial_exact_p95"],
                    "beats_random_hit_p95": hits > control["hit_p95"],
                }
            )
    family_summaries = []
    for family in MODEL_FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        family_summaries.append(
            {
                "family": family,
                "aggregate_hits": sum(row["hits"] for row in family_rows),
                "aggregate_boundaries": sum(row["test_boundaries"] for row in family_rows),
                "aggregate_exact_books": sum(row["exact_books"] for row in family_rows),
                "aggregate_nontrivial_exact_books": sum(
                    row["nontrivial_exact_books"] for row in family_rows
                ),
                "cells_beating_random_p95": sum(
                    1 for row in family_rows if row["beats_random_hit_p95"]
                ),
                "cutoff_count": len(family_rows),
            }
        )
    best = max(
        family_summaries,
        key=lambda row: (
            row["cells_beating_random_p95"],
            row["aggregate_nontrivial_exact_books"],
            row["aggregate_hits"],
        ),
    )
    promotes_endpoint_decoder = (
        best["cells_beating_random_p95"] == len(PREFIX_CUTOFFS)
        and best["aggregate_nontrivial_exact_books"] > 0
    )
    summary = {
        "family_count": len(MODEL_FAMILIES),
        "cutoff_count": len(PREFIX_CUTOFFS),
        "best_family": best["family"],
        "best_aggregate_hits": best["aggregate_hits"],
        "best_aggregate_boundaries": best["aggregate_boundaries"],
        "best_cells_beating_random_p95": best["cells_beating_random_p95"],
        "best_aggregate_exact_books": best["aggregate_exact_books"],
        "best_aggregate_nontrivial_exact_books": best[
            "aggregate_nontrivial_exact_books"
        ],
        "promotes_endpoint_decoder": promotes_endpoint_decoder,
        "interpretation": (
            "Combining the promoted digit-surprisal boundary clue with the "
            "promoted age hazard improves endpoint hit rate over age alone, but "
            "still does not yield a nontrivial exact endpoint decoder under "
            "prefix holdout. The combined features remain dependency clues, not "
            "a skeleton generator."
        ),
    }
    return {
        "schema": "combined_boundary_endpoint_decoder_gate_v1",
        "scope": "analysis_only_combined_promoted_boundary_clues_to_endpoint_decoder",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_boundary_gate": rel(BOUNDARY_GATE),
            "boundary_hazard_state_gate": rel(HAZARD_GATE),
            "boundary_hazard_endpoint_decoder_gate": rel(ENDPOINT_GATE),
        },
        "model_families": MODEL_FAMILIES,
        "cutoff_rows": rows,
        "family_summaries": family_summaries,
        "summary": summary,
        "classification": (
            "combined_boundary_endpoint_decoder_rejected"
            if not promotes_endpoint_decoder
            else "combined_boundary_endpoint_decoder_promoted"
        ),
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
        "# Combined Boundary Endpoint Decoder Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the promoted digit-surprisal boundary clue and the promoted",
        "`age_bucket` hazard become an exact endpoint selector when combined under",
        "prefix holdout and granted the true number of internal cutpoints.",
        "",
        "## Summary",
        "",
        f"- Model families tested: `{s['family_count']}`.",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Best family: `{s['best_family']}`.",
        f"- Best aggregate hits: `{s['best_aggregate_hits']}/{s['best_aggregate_boundaries']}`.",
        f"- Best cells beating random p95: `{s['best_cells_beating_random_p95']}/{s['cutoff_count']}`.",
        f"- Best aggregate exact books: `{s['best_aggregate_exact_books']}`.",
        f"- Best aggregate nontrivial exact books: `{s['best_aggregate_nontrivial_exact_books']}`.",
        f"- Promotes endpoint decoder: `{s['promotes_endpoint_decoder']}`.",
        "",
        s["interpretation"],
        "",
        "## Family Summary",
        "",
        "| Family | Hits | Cells > random p95 | Exact books | Nontrivial exact |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["family_summaries"]:
        lines.append(
            f"| `{row['family']}` | "
            f"`{row['aggregate_hits']}/{row['aggregate_boundaries']}` | "
            f"`{row['cells_beating_random_p95']}/{row['cutoff_count']}` | "
            f"`{row['aggregate_exact_books']}` | "
            f"`{row['aggregate_nontrivial_exact_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Cutoff Rows",
            "",
            "| Cutoff | Family | Boundaries | Hits | Random hit p95 | Exact books | Nontrivial exact |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['family']}` | "
            f"`{row['test_boundaries']}` | `{row['hits']}` | "
            f"`{row['random_hit_p95']:.3f}` | `{row['exact_books']}` | "
            f"`{row['nontrivial_exact_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Combined boundary endpoint decoding is rejected as a generator.",
            "- The tested features remain dependency clues only.",
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
