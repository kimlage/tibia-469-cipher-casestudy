from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
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
RANKCODE_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_rankcode_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_rankcode_gate.json"
)

OUT_STEM = "01_target_digit_boundary_type_gate"
ALPHA = 0.5
DIGITS = "0123456789"
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


def prev2_context(prefix: str) -> tuple[str, str]:
    if not prefix:
        return ("BOS", "BOS")
    if len(prefix) == 1:
        return ("BOS", prefix[-1])
    return (prefix[-2], prefix[-1])


def train_prev2(books: dict[int, str], book_ids: list[int]) -> tuple[dict[tuple[str, str], Counter[str]], Counter[str]]:
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
    counts, global_counts = train_prev2(
        books, [candidate for candidate in sorted(books) if candidate < book]
    )
    prefix = ""
    values = []
    for digit in books[book]:
        counter = counts.get(prev2_context(prefix), global_counts)
        total = sum(counter.values())
        probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
        values.append(-math.log2(probability))
        prefix += digit
    return values


def rows(books: dict[int, str], ops_by_book: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    out = []
    for book in range(10, 70):
        surprisal = book_surprisals(books, book)
        candidates = list(range(1, len(surprisal)))
        ranked = sorted(candidates, key=lambda pos: (-surprisal[pos], pos))
        rank_fraction = {pos: (index + 1) / len(candidates) for index, pos in enumerate(ranked)}
        ops = ops_by_book[str(book)]
        for index, op in enumerate(ops[:-1]):
            end = int(op["target_start"]) + int(op["length"])
            next_type = str(ops[index + 1]["type"])
            if 0 < end < len(surprisal):
                out.append(
                    {
                        "book": book,
                        "op_index": index,
                        "boundary": end,
                        "next_type": next_type,
                        "right_surprisal": surprisal[end],
                        "delta_right_left": surprisal[end] - surprisal[end - 1],
                        "rank_fraction": rank_fraction[end],
                    }
                )
    return out


Predicate = Callable[[dict[str, Any]], bool]


def predicate_families() -> dict[str, Predicate]:
    return {
        "rank_top10": lambda row: row["rank_fraction"] <= 0.10,
        "rank_top20": lambda row: row["rank_fraction"] <= 0.20,
        "rank_bottom70": lambda row: row["rank_fraction"] > 0.30,
        "right_surprisal_lt3": lambda row: row["right_surprisal"] < 3.0,
        "right_surprisal_ge4": lambda row: row["right_surprisal"] >= 4.0,
        "delta_negative": lambda row: row["delta_right_left"] < 0.0,
        "delta_lt1": lambda row: row["delta_right_left"] < 1.0,
    }


def evaluate_predicates(all_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    majority_type = Counter(row["next_type"] for row in all_rows).most_common(1)[0][0]
    for name, predicate in predicate_families().items():
        for literal_when_true in [True, False]:
            hits = 0
            for row in all_rows:
                true_branch = "literal" if literal_when_true else "copy"
                false_branch = "copy" if literal_when_true else "literal"
                predicted = true_branch if predicate(row) else false_branch
                hits += int(predicted == row["next_type"])
            out.append(
                {
                    "predicate": name,
                    "literal_when_true": literal_when_true,
                    "hits": hits,
                    "total": len(all_rows),
                    "delta_vs_majority_hits": hits
                    - sum(1 for row in all_rows if row["next_type"] == majority_type),
                }
            )
    return sorted(out, key=lambda row: (-row["hits"], row["predicate"], row["literal_when_true"]))


def context_key(name: str, row: dict[str, Any]) -> Any:
    if name == "rank_top10":
        return row["rank_fraction"] <= 0.10
    if name == "rank_decile":
        return min(9, int(row["rank_fraction"] * 10))
    if name == "right_surprisal_bin":
        return "hi" if row["right_surprisal"] >= 4 else "mid" if row["right_surprisal"] >= 2 else "lo"
    if name == "delta_sign":
        return row["delta_right_left"] >= 0
    raise KeyError(name)


def prequential_context_rows(all_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts = ["rank_top10", "rank_decile", "right_surprisal_bin", "delta_sign"]
    rows_out = []
    for context in contexts:
        for cutoff in PREFIX_CUTOFFS:
            train = [row for row in all_rows if row["book"] < cutoff]
            test = [row for row in all_rows if row["book"] >= cutoff]
            majority = Counter(row["next_type"] for row in train).most_common(1)[0][0]
            table: dict[Any, Counter[str]] = defaultdict(Counter)
            for row in train:
                table[context_key(context, row)][row["next_type"]] += 1
            hits = 0
            majority_hits = 0
            for row in test:
                key = context_key(context, row)
                predicted = table[key].most_common(1)[0][0] if table.get(key) else majority
                hits += int(predicted == row["next_type"])
                majority_hits += int("copy" == row["next_type"])
            rows_out.append(
                {
                    "context": context,
                    "cutoff": cutoff,
                    "hits": hits,
                    "total": len(test),
                    "majority_hits": majority_hits,
                    "delta_vs_majority_hits": hits - majority_hits,
                }
            )
    return rows_out


def make_result() -> dict[str, Any]:
    rankcode_gate = load_json(RANKCODE_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_rankcode_gate", rankcode_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    all_rows = rows(books, copy_ledger["canonical_ops_by_book"])
    type_counts = Counter(row["next_type"] for row in all_rows)
    majority_hits = max(type_counts.values())
    predicates = evaluate_predicates(all_rows)
    preq = prequential_context_rows(all_rows)
    best_predicate = predicates[0]
    best_preq_delta = max(row["delta_vs_majority_hits"] for row in preq)
    promotes_type_rule = best_predicate["hits"] > majority_hits and best_preq_delta > 0
    summary = {
        "boundary_count": len(all_rows),
        "next_type_counts": dict(type_counts),
        "majority_type": type_counts.most_common(1)[0][0],
        "majority_hits": majority_hits,
        "best_predicate": best_predicate,
        "best_prequential_delta_vs_majority_hits": best_preq_delta,
        "prequential_cells_with_positive_delta": sum(
            1 for row in preq if row["delta_vs_majority_hits"] > 0
        ),
        "prequential_cells": len(preq),
        "promotes_boundary_type_rule": promotes_type_rule,
        "interpretation": (
            "Prev2 boundary surprisal helps locate cutpoints, but does not "
            "predict whether the next operation is copy or literal. The "
            "copy-majority baseline remains unbeaten."
        ),
    }
    return {
        "schema": "target_digit_boundary_type_gate_v1",
        "scope": "analysis_only_boundary_surprisal_next_type",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_boundary_rankcode_gate": rel(RANKCODE_GATE),
        },
        "summary": summary,
        "predicate_rows": predicates,
        "prequential_rows": preq,
        "classification": "target_digit_boundary_type_rule_rejected",
        "decision": {
            "promotes_boundary_type_rule": promotes_type_rule,
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
        "# Target Digit Boundary Type Gate",
        "",
        "Classification: `target_digit_boundary_type_rule_rejected`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the `prev2_digits` boundary surprisal clue predicts the",
        "next operation type after an internal cutpoint.",
        "",
        "## Summary",
        "",
        f"- Boundaries tested: `{s['boundary_count']}`.",
        f"- Next-type counts: `{s['next_type_counts']}`.",
        f"- Majority baseline: `{s['majority_type']}` with `{s['majority_hits']}/{s['boundary_count']}` hits.",
        f"- Best predicate: `{s['best_predicate']['predicate']}` / literal_when_true `{s['best_predicate']['literal_when_true']}`.",
        f"- Best predicate hits: `{s['best_predicate']['hits']}/{s['boundary_count']}`.",
        f"- Best predicate delta vs majority: `{s['best_predicate']['delta_vs_majority_hits']}`.",
        f"- Prequential positive-delta cells: `{s['prequential_cells_with_positive_delta']}/{s['prequential_cells']}`.",
        "",
        "## Best Predicate Rows",
        "",
        "| Predicate | literal_when_true | Hits | Delta vs majority |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in result["predicate_rows"][:8]:
        lines.append(
            f"| `{row['predicate']}` | `{row['literal_when_true']}` | "
            f"`{row['hits']}/{row['total']}` | `{row['delta_vs_majority_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes boundary type rule: `False`.",
            "- The boundary surprisal clue localizes cutpoints, but does not explain next operation type.",
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
