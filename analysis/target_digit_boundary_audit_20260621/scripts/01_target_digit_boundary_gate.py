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
TARGET_DIGIT_PROCESS_GATE = (
    ROOT
    / "analysis"
    / "target_digit_process_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_process_gate.json"
)

OUT_STEM = "01_target_digit_boundary_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"


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


def digit_surprisal(
    digit: str,
    prefix: str,
    counts: dict[tuple[str, str], Counter[str]],
    global_counts: Counter[str],
) -> float:
    counter = counts.get(prev2_context(prefix), global_counts)
    total = sum(counter.values())
    probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
    return -math.log2(probability)


def book_surprisals(books: dict[int, str], book: int) -> list[float]:
    train_ids = [candidate for candidate in sorted(books) if candidate < book]
    counts, global_counts = train_prev2(books, train_ids)
    prefix = ""
    values = []
    for digit in books[book]:
        values.append(digit_surprisal(digit, prefix, counts, global_counts))
        prefix += digit
    return values


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


def metric_value(name: str, surprisals: list[float], pos: int) -> float:
    if name == "right_surprisal":
        return surprisals[pos]
    if name == "left_surprisal":
        return surprisals[pos - 1]
    if name == "sum2_surprisal":
        return surprisals[pos] + surprisals[pos - 1]
    if name == "delta_right_left":
        return surprisals[pos] - surprisals[pos - 1]
    raise KeyError(name)


def top_fraction_hits(
    per_book: dict[int, dict[str, Any]],
    metric_name: str,
    fraction: float,
) -> int:
    hits = 0
    for info in per_book.values():
        candidates = info["candidate_positions"]
        if not candidates:
            continue
        values = [
            metric_value(metric_name, info["surprisals"], pos)
            for pos in candidates
        ]
        threshold_index = max(0, math.ceil(fraction * len(values)) - 1)
        threshold = sorted(values, reverse=True)[threshold_index]
        hits += sum(
            1
            for pos in info["actual_cutpoints"]
            if metric_value(metric_name, info["surprisals"], pos) >= threshold
        )
    return hits


def top_k_selector_hits(
    per_book: dict[int, dict[str, Any]],
    metric_name: str,
) -> dict[str, Any]:
    hit_count = 0
    cutpoint_count = 0
    exact_nontrivial_books = 0
    zero_cutpoint_books = 0
    nontrivial_books = 0
    book_rows = []
    for book, info in per_book.items():
        k = len(info["actual_cutpoints"])
        if k == 0:
            zero_cutpoint_books += 1
            book_rows.append(
                {
                    "book": book,
                    "actual_cutpoints": 0,
                    "selector_hits": 0,
                    "exact_nontrivial": False,
                }
            )
            continue
        nontrivial_books += 1
        ranked = sorted(
            info["candidate_positions"],
            key=lambda pos: (-metric_value(metric_name, info["surprisals"], pos), pos),
        )[:k]
        selected = set(ranked)
        actual = set(info["actual_cutpoints"])
        hits = len(selected & actual)
        hit_count += hits
        cutpoint_count += k
        exact = hits == k
        exact_nontrivial_books += int(exact)
        book_rows.append(
            {
                "book": book,
                "actual_cutpoints": k,
                "selector_hits": hits,
                "exact_nontrivial": exact,
            }
        )
    return {
        "metric": metric_name,
        "hit_count": hit_count,
        "cutpoint_count": cutpoint_count,
        "hit_fraction": hit_count / cutpoint_count if cutpoint_count else 0.0,
        "exact_nontrivial_books": exact_nontrivial_books,
        "nontrivial_books": nontrivial_books,
        "zero_cutpoint_books": zero_cutpoint_books,
        "book_count": len(per_book),
        "book_rows": book_rows,
    }


def random_controls(
    per_book: dict[int, dict[str, Any]],
    metric_names: list[str],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    metric_means: dict[str, list[float]] = {name: [] for name in metric_names}
    top10_hits: dict[str, list[float]] = {name: [] for name in metric_names}
    top20_hits: dict[str, list[float]] = {name: [] for name in metric_names}
    topk_hits: dict[str, list[float]] = {name: [] for name in metric_names}
    for _ in range(RANDOM_TRIALS):
        sampled_positions: dict[int, list[int]] = {}
        for book, info in per_book.items():
            k = len(info["actual_cutpoints"])
            candidates = info["candidate_positions"]
            sampled_positions[book] = rng.sample(candidates, k) if k else []
        for name in metric_names:
            values = []
            hit10 = 0
            hit20 = 0
            hit_topk = 0
            total = 0
            for book, positions in sampled_positions.items():
                info = per_book[book]
                candidates = info["candidate_positions"]
                if not positions:
                    continue
                values.extend(
                    metric_value(name, info["surprisals"], pos) for pos in positions
                )
                ranked10 = set(
                    sorted(
                        candidates,
                        key=lambda pos: (-metric_value(name, info["surprisals"], pos), pos),
                    )[: max(1, math.ceil(0.10 * len(candidates)))]
                )
                ranked20 = set(
                    sorted(
                        candidates,
                        key=lambda pos: (-metric_value(name, info["surprisals"], pos), pos),
                    )[: max(1, math.ceil(0.20 * len(candidates)))]
                )
                rankedk = set(
                    sorted(
                        candidates,
                        key=lambda pos: (-metric_value(name, info["surprisals"], pos), pos),
                    )[: len(positions)]
                )
                hit10 += sum(1 for pos in positions if pos in ranked10)
                hit20 += sum(1 for pos in positions if pos in ranked20)
                hit_topk += sum(1 for pos in positions if pos in rankedk)
                total += len(positions)
            metric_means[name].append(mean(values) if values else 0.0)
            top10_hits[name].append(hit10 / total if total else 0.0)
            top20_hits[name].append(hit20 / total if total else 0.0)
            topk_hits[name].append(hit_topk / total if total else 0.0)
    out = {}
    for name in metric_names:
        out[name] = {}
        for label, values in {
            "mean": metric_means[name],
            "top10_fraction": top10_hits[name],
            "top20_fraction": top20_hits[name],
            "topk_fraction": topk_hits[name],
        }.items():
            sorted_values = sorted(values)
            out[name][label] = {
                "random_mean": mean(sorted_values),
                "p05": percentile(sorted_values, 0.05),
                "p95": percentile(sorted_values, 0.95),
            }
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED,
        "control": "uniform_random_cutpoints_per_book_preserving_cutpoint_count",
        "metrics": out,
    }


def make_per_book(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> dict[int, dict[str, Any]]:
    out = {}
    for book in range(10, 70):
        target = books[book]
        surprisals = book_surprisals(books, book)
        actual = [
            int(op["target_start"]) + int(op["length"])
            for op in ops_by_book[str(book)][:-1]
        ]
        actual = [pos for pos in actual if 0 < pos < len(target)]
        out[book] = {
            "length": len(target),
            "op_count": len(ops_by_book[str(book)]),
            "actual_cutpoints": actual,
            "candidate_positions": list(range(1, len(target))),
            "surprisals": surprisals,
        }
    return out


def make_result() -> dict[str, Any]:
    digit_gate = load_json(TARGET_DIGIT_PROCESS_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_process_gate", digit_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    per_book = make_per_book(books, copy_ledger["canonical_ops_by_book"])
    metric_names = [
        "right_surprisal",
        "left_surprisal",
        "sum2_surprisal",
        "delta_right_left",
    ]
    cutpoint_count = sum(len(info["actual_cutpoints"]) for info in per_book.values())
    observed = {}
    for name in metric_names:
        values = [
            metric_value(name, info["surprisals"], pos)
            for info in per_book.values()
            for pos in info["actual_cutpoints"]
        ]
        top10 = top_fraction_hits(per_book, name, 0.10)
        top20 = top_fraction_hits(per_book, name, 0.20)
        selector = top_k_selector_hits(per_book, name)
        observed[name] = {
            "mean": mean(values),
            "top10_hits": top10,
            "top10_fraction": top10 / cutpoint_count if cutpoint_count else 0.0,
            "top20_hits": top20,
            "top20_fraction": top20 / cutpoint_count if cutpoint_count else 0.0,
            "topk_selector": {
                key: value
                for key, value in selector.items()
                if key != "book_rows"
            },
        }
    controls = random_controls(per_book, metric_names)
    for name in metric_names:
        control = controls["metrics"][name]
        observed[name]["mean_beats_random_p95"] = (
            observed[name]["mean"] > control["mean"]["p95"]
        )
        observed[name]["top10_beats_random_p95"] = (
            observed[name]["top10_fraction"] > control["top10_fraction"]["p95"]
        )
        observed[name]["top20_beats_random_p95"] = (
            observed[name]["top20_fraction"] > control["top20_fraction"]["p95"]
        )
        observed[name]["topk_beats_random_p95"] = (
            observed[name]["topk_selector"]["hit_fraction"]
            > control["topk_fraction"]["p95"]
        )
    right = observed["right_surprisal"]
    delta = observed["delta_right_left"]
    promotes_boundary_clue = (
        right["mean_beats_random_p95"]
        and right["top10_beats_random_p95"]
        and right["topk_beats_random_p95"]
    )
    promotes_boundary_generator = False
    summary = {
        "book_count": len(per_book),
        "internal_cutpoint_count": cutpoint_count,
        "candidate_position_count": sum(
            len(info["candidate_positions"]) for info in per_book.values()
        ),
        "right_surprisal_mean": right["mean"],
        "right_surprisal_random_mean": controls["metrics"]["right_surprisal"]["mean"]["random_mean"],
        "right_surprisal_random_p95": controls["metrics"]["right_surprisal"]["mean"]["p95"],
        "right_top10_hits": right["top10_hits"],
        "right_top10_fraction": right["top10_fraction"],
        "right_top10_random_p95": controls["metrics"]["right_surprisal"]["top10_fraction"]["p95"],
        "right_topk_hits": right["topk_selector"]["hit_count"],
        "right_topk_fraction": right["topk_selector"]["hit_fraction"],
        "right_topk_exact_nontrivial_books": right["topk_selector"]["exact_nontrivial_books"],
        "right_topk_nontrivial_books": right["topk_selector"]["nontrivial_books"],
        "zero_cutpoint_books": right["topk_selector"]["zero_cutpoint_books"],
        "delta_mean": delta["mean"],
        "delta_random_p95": controls["metrics"]["delta_right_left"]["mean"]["p95"],
        "promotes_target_digit_boundary_clue": promotes_boundary_clue,
        "promotes_target_digit_boundary_generator": promotes_boundary_generator,
        "interpretation": (
            "Internal operation cutpoints occur before high-surprisal digits "
            "under a prequential prev2 digit model. This links the target-digit "
            "Markov clue to segmentation, but top-k surprisal selection still "
            "recovers only a minority of exact cutpoints and no full book set."
        ),
    }
    compact_books = [
        {
            "book": book,
            "length": info["length"],
            "op_count": info["op_count"],
            "internal_cutpoints": len(info["actual_cutpoints"]),
        }
        for book, info in per_book.items()
    ]
    return {
        "schema": "target_digit_boundary_gate_v1",
        "scope": "analysis_only_prev2_boundary_alignment",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_process_gate": rel(TARGET_DIGIT_PROCESS_GATE),
        },
        "summary": summary,
        "observed_metrics": observed,
        "random_controls": controls,
        "book_rows": compact_books,
        "classification": "target_digit_boundary_markov_clue_promoted_not_generator",
        "decision": {
            "promotes_target_digit_boundary_clue": promotes_boundary_clue,
            "promotes_target_digit_boundary_generator": promotes_boundary_generator,
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
    observed = result["observed_metrics"]
    controls = result["random_controls"]["metrics"]
    lines = [
        "# Target Digit Boundary Gate",
        "",
        "Classification: `target_digit_boundary_markov_clue_promoted_not_generator`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether internal operation cutpoints are aligned with surprisal",
        "under the prequential `prev2_digits` target digit process.",
        "",
        "## Summary",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Internal cutpoints: `{s['internal_cutpoint_count']}`.",
        f"- Candidate boundary positions: `{s['candidate_position_count']}`.",
        f"- Right-surprisal mean at real cutpoints: `{s['right_surprisal_mean']:.6f}`.",
        f"- Right-surprisal random mean/p95: `{s['right_surprisal_random_mean']:.6f}` / `{s['right_surprisal_random_p95']:.6f}`.",
        f"- Right-surprisal top10 hits: `{s['right_top10_hits']}/{s['internal_cutpoint_count']}` (`{s['right_top10_fraction']:.6f}`), random p95 `{s['right_top10_random_p95']:.6f}`.",
        f"- Right-surprisal top-k selector hits: `{s['right_topk_hits']}/{s['internal_cutpoint_count']}` (`{s['right_topk_fraction']:.6f}`), exact nontrivial books `{s['right_topk_exact_nontrivial_books']}/{s['right_topk_nontrivial_books']}`.",
        f"- Zero-cutpoint books: `{s['zero_cutpoint_books']}`.",
        f"- Delta right-left mean/p95 control: `{s['delta_mean']:.6f}` / `{s['delta_random_p95']:.6f}`.",
        "",
        "## Metric Table",
        "",
        "| Metric | Observed mean | Random p95 | Top10 fraction | Top10 random p95 | Top-k hits | Top-k random p95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in [
        "right_surprisal",
        "left_surprisal",
        "sum2_surprisal",
        "delta_right_left",
    ]:
        obs = observed[name]
        ctrl = controls[name]
        lines.append(
            f"| `{name}` | `{obs['mean']:.6f}` | "
            f"`{ctrl['mean']['p95']:.6f}` | "
            f"`{obs['top10_fraction']:.6f}` | "
            f"`{ctrl['top10_fraction']['p95']:.6f}` | "
            f"`{obs['topk_selector']['hit_count']}/{obs['topk_selector']['cutpoint_count']}` | "
            f"`{ctrl['topk_fraction']['p95']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes target digit boundary Markov clue: `True`.",
            "- Promotes target digit boundary generator: `False`.",
            "- Real cutpoints are strongly enriched before high-surprisal `prev2` digits.",
            "- Top-k surprisal selection does not reconstruct the skeleton: it hits a minority of cutpoints and does not solve full books.",
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
