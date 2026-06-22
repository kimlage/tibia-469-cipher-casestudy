from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Callable


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
COPY_STATE_DIAGNOSTIC = TEST_RESULTS / "06_copy_state_rescue_diagnostic.json"

OUT_STEM = "07_copy_candidate_ranking_frontier"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
COPY_LENGTH_CHOICES = [5, 6, 7, 8, 10, 12, 15, 20, 30, 40, 60, 80, 120, 160]
TOP_K = 80
RANDOM_TRIALS = 500
RANDOM_SEED = 46920260622


Candidate = dict[str, Any]
PolicyKey = Callable[[Candidate, int], tuple[Any, ...]]


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


def sampled_books_for_cutoff(cutoff: int) -> list[int]:
    suffix_books = list(range(cutoff, 70))
    return sorted(
        {
            suffix_books[0],
            suffix_books[len(suffix_books) // 2],
            suffix_books[-1],
        }
    )


def build_candidates(available: str, lengths: list[int]) -> list[Candidate]:
    rows: dict[tuple[int, str], Candidate] = {}
    for length in lengths:
        if length > len(available):
            continue
        for source in range(0, len(available) - length + 1):
            chunk = available[source : source + length]
            key = (length, chunk)
            row = rows.get(key)
            if row is None:
                rows[key] = {
                    "length": length,
                    "chunk": chunk,
                    "min_source": source,
                    "max_source": source,
                    "count": 1,
                }
            else:
                row["max_source"] = source
                row["count"] += 1
    return list(rows.values())


def policy_keys() -> dict[str, PolicyKey]:
    return {
        "current_source_penalty": lambda c, _n: (
            0.05 * math.log2(max(1, int(c["min_source"]) + 1)),
            int(c["length"]),
            c["chunk"],
        ),
        "earliest_longest": lambda c, _n: (
            int(c["min_source"]),
            -int(c["length"]),
            c["chunk"],
        ),
        "recent_longest": lambda c, n: (
            n - (int(c["max_source"]) + int(c["length"])),
            -int(c["length"]),
            -int(c["count"]),
            c["chunk"],
        ),
        "longest_recent": lambda c, n: (
            -int(c["length"]),
            n - (int(c["max_source"]) + int(c["length"])),
            -int(c["count"]),
            c["chunk"],
        ),
        "frequent_longest": lambda c, n: (
            -int(c["count"]),
            -int(c["length"]),
            n - (int(c["max_source"]) + int(c["length"])),
            c["chunk"],
        ),
        "rare_longest": lambda c, n: (
            int(c["count"]),
            -int(c["length"]),
            n - (int(c["max_source"]) + int(c["length"])),
            c["chunk"],
        ),
    }


def evaluate_policy(
    candidates: list[Candidate],
    payload: str,
    policy: str,
    key_fn: PolicyKey,
    available_len: int,
) -> dict[str, Any]:
    top = sorted(candidates, key=lambda item: key_fn(item, available_len))[:TOP_K]
    hit_lengths = [
        int(item["length"])
        for item in top
        if payload[: int(item["length"])] == item["chunk"]
    ]
    best = max(hit_lengths) if hit_lengths else 0
    return {
        "policy": policy,
        "best_prefix_len": best,
        "hit": best > 0,
        "full_hit": best == len(payload),
    }


def random_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    hit_values = []
    digit_values = []
    for _trial in range(RANDOM_TRIALS):
        hits = 0
        digits = 0
        for row in rows:
            n = row["candidate_count"]
            correct_lengths = row["correct_candidate_lengths"]
            if not correct_lengths:
                continue
            if n <= TOP_K:
                best = max(correct_lengths)
            else:
                chosen = set(rng.sample(range(n), min(TOP_K, n)))
                best = 0
                for index, length in enumerate(correct_lengths):
                    if index in chosen:
                        best = max(best, length)
            if best:
                hits += 1
                digits += best
        hit_values.append(hits)
        digit_values.append(digits)
    hit_values.sort()
    digit_values.sort()
    p95_index = int(0.95 * (RANDOM_TRIALS - 1))
    return {
        "trials": RANDOM_TRIALS,
        "top_k": TOP_K,
        "hit_mean": mean(hit_values),
        "hit_p95": hit_values[p95_index],
        "digit_mean": mean(digit_values),
        "digit_p95": digit_values[p95_index],
    }


def summarize_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    total = len(rows)
    total_digits = sum(row["canonical_length"] for row in rows)
    hits = sum(1 for row in rows if row["policies"][policy]["hit"])
    full_hits = sum(1 for row in rows if row["policies"][policy]["full_hit"])
    prefix_digits = sum(row["policies"][policy]["best_prefix_len"] for row in rows)
    return {
        "policy": policy,
        "copy_ops": total,
        "hits": hits,
        "hit_fraction": hits / total if total else 0.0,
        "full_hits": full_hits,
        "prefix_digits": prefix_digits,
        "copy_digits": total_digits,
        "prefix_digit_fraction": prefix_digits / total_digits if total_digits else 0.0,
    }


def make_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    policy_fns = policy_keys()
    instance_rows: list[dict[str, Any]] = []
    unique_rows: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for cutoff in PREFIX_CUTOFFS:
        for book in sampled_books_for_cutoff(cutoff):
            target = books[book]
            emitted_base = "".join(books[index] for index in range(book))
            for op in ledger["canonical_ops_by_book"][str(book)]:
                if op["type"] != "copy":
                    continue
                start = int(op["target_start"])
                length = int(op["length"])
                available = emitted_base + target[:start]
                payload = target[start : start + length]
                allowed_lengths = [
                    copy_len
                    for copy_len in COPY_LENGTH_CHOICES
                    if copy_len <= length and copy_len <= len(available)
                ]
                candidates = build_candidates(available, allowed_lengths)
                correct_lengths = sorted(
                    {
                        int(candidate["length"])
                        for candidate in candidates
                        if payload[: int(candidate["length"])] == candidate["chunk"]
                    },
                    reverse=True,
                )
                row = {
                    "cutoff": cutoff,
                    "book": book,
                    "target_start": start,
                    "canonical_length": length,
                    "candidate_count": len(candidates),
                    "correct_candidate_lengths": correct_lengths,
                    "raw_inventory_best_prefix_len": max(correct_lengths)
                    if correct_lengths
                    else 0,
                    "policies": {
                        name: evaluate_policy(
                            candidates,
                            payload,
                            name,
                            fn,
                            len(available),
                        )
                        for name, fn in policy_fns.items()
                    },
                }
                instance_rows.append(row)
                key = (book, start)
                if key not in seen:
                    seen.add(key)
                    unique_rows.append(row)
    return instance_rows, unique_rows


def make_result() -> dict[str, Any]:
    copy_state = load_json(COPY_STATE_DIAGNOSTIC)
    assert_boundary("copy_state_rescue_diagnostic", copy_state)
    instance_rows, unique_rows = make_rows()
    policy_names = list(policy_keys())
    instance_summaries = {
        policy: summarize_policy(instance_rows, policy) for policy in policy_names
    }
    unique_summaries = {
        policy: summarize_policy(unique_rows, policy) for policy in policy_names
    }
    best_unique = max(
        unique_summaries.values(),
        key=lambda row: (row["prefix_digits"], row["hits"], row["full_hits"]),
    )
    random_unique = random_control(unique_rows)
    raw_inventory_digits = sum(row["raw_inventory_best_prefix_len"] for row in unique_rows)
    raw_copy_digits = sum(row["canonical_length"] for row in unique_rows)
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        rows = [row for row in instance_rows if row["cutoff"] == cutoff]
        cutoff_policy_summaries = {
            policy: summarize_policy(rows, policy) for policy in policy_names
        }
        best = max(
            cutoff_policy_summaries.values(),
            key=lambda row: (row["prefix_digits"], row["hits"], row["full_hits"]),
        )
        cutoff_rows.append(
            {
                "cutoff": cutoff,
                "sample_books": sampled_books_for_cutoff(cutoff),
                "copy_ops": len(rows),
                "best_policy": best["policy"],
                "best_hits": best["hits"],
                "best_prefix_digits": best["prefix_digits"],
                "best_prefix_digit_fraction": best["prefix_digit_fraction"],
                "current_hits": cutoff_policy_summaries["current_source_penalty"]["hits"],
                "current_prefix_digits": cutoff_policy_summaries[
                    "current_source_penalty"
                ]["prefix_digits"],
            }
        )
    promotes = (
        best_unique["prefix_digits"] > random_unique["digit_p95"]
        and best_unique["prefix_digit_fraction"] >= 0.25
    )
    return {
        "schema": "copy_candidate_ranking_frontier_v1",
        "scope": "analysis_only_target_free_chunk_ranking_frontier",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "copy_state_rescue_diagnostic": rel(COPY_STATE_DIAGNOSTIC),
        },
        "top_k": TOP_K,
        "length_choices": COPY_LENGTH_CHOICES,
        "policy_summaries_instance_weighted": instance_summaries,
        "policy_summaries_unique_ops": unique_summaries,
        "cutoff_rows": cutoff_rows,
        "random_control_unique_ops": random_unique,
        "summary": {
            "unique_copy_ops": len(unique_rows),
            "instance_copy_ops": len(instance_rows),
            "raw_inventory_prefix_digits": raw_inventory_digits,
            "raw_inventory_prefix_digit_fraction": raw_inventory_digits / raw_copy_digits,
            "raw_copy_digits": raw_copy_digits,
            "best_unique_policy": best_unique["policy"],
            "best_unique_hits": best_unique["hits"],
            "best_unique_prefix_digits": best_unique["prefix_digits"],
            "best_unique_prefix_digit_fraction": best_unique[
                "prefix_digit_fraction"
            ],
            "current_unique_hits": unique_summaries["current_source_penalty"]["hits"],
            "current_unique_prefix_digits": unique_summaries[
                "current_source_penalty"
            ]["prefix_digits"],
            "best_beats_random_digit_p95": best_unique["prefix_digits"]
            > random_unique["digit_p95"],
            "promotes_copy_ranking_rule": promotes,
        },
        "classification": "simple_copy_candidate_ranking_not_promoted",
        "interpretation": (
            "Target-free ranking policies can improve over the current source "
            "penalty pruning, with longest/recent and frequency-first variants "
            "providing weak signals, but the best policy still retains only a "
            "small fraction of canonical copy digits. "
            "This keeps copy candidate ranking open as a blocker, not as a solved "
            "generator component."
        ),
        "decision": {
            "promotes_generator": False,
            "promotes_copy_ranking_rule": promotes,
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
    random_unique = result["random_control_unique_ops"]
    lines = [
        "# Copy Candidate Ranking Frontier",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the copy-state blocker can be rescued by simple target-free",
        "chunk ranking policies at the same top-k budget used by the closed-loop",
        "candidate generator.",
        "",
        "## Summary",
        "",
        f"- Unique sampled copy ops: `{s['unique_copy_ops']}`.",
        f"- Instance-weighted sampled copy ops: `{s['instance_copy_ops']}`.",
        f"- Raw inventory prefix digits: `{s['raw_inventory_prefix_digits']}/{s['raw_copy_digits']}` (`{s['raw_inventory_prefix_digit_fraction']:.6f}`).",
        f"- Current source-penalty unique hits/digits: `{s['current_unique_hits']}` / `{s['current_unique_prefix_digits']}`.",
        f"- Best unique policy: `{s['best_unique_policy']}`.",
        f"- Best unique hits/digits: `{s['best_unique_hits']}` / `{s['best_unique_prefix_digits']}`.",
        f"- Best unique prefix digit fraction: `{s['best_unique_prefix_digit_fraction']:.6f}`.",
        f"- Random top-k digit p95: `{random_unique['digit_p95']}`.",
        f"- Best beats random digit p95: `{s['best_beats_random_digit_p95']}`.",
        f"- Promotes copy ranking rule: `{s['promotes_copy_ranking_rule']}`.",
        "",
        result["interpretation"],
        "",
        "## Unique-Op Policy Frontier",
        "",
        "| Policy | Hits | Full Hits | Prefix Digits | Prefix Digit Fraction |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for policy, row in result["policy_summaries_unique_ops"].items():
        lines.append(
            f"| `{policy}` | `{row['hits']}` | `{row['full_hits']}` | "
            f"`{row['prefix_digits']}` | `{row['prefix_digit_fraction']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Cutoff Rows",
            "",
            "| Cutoff | Books | Copy Ops | Best Policy | Best Hits | Best Prefix Digits | Current Prefix Digits |",
            "| ---: | ---: | ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['sample_books']}` | `{row['copy_ops']}` | "
            f"`{row['best_policy']}` | `{row['best_hits']}` | "
            f"`{row['best_prefix_digits']}` | `{row['current_prefix_digits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Simple target-free chunk ranking is not enough to rescue the closed-loop generator.",
            "- Longest/recent and frequency-first rankings are weak clues because they improve over current pruning, but coverage is too small for promotion.",
            "- The next constructive route must add a richer copy-control state or a paid copy hint stream.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "summary": result["summary"],
                "random_control_unique_ops": result["random_control_unique_ops"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
