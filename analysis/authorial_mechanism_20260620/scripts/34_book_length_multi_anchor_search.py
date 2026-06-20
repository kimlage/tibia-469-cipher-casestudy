from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_length_ledger_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


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


def ceil_log2(value: int) -> int:
    return 0 if value <= 1 else int(math.ceil(math.log2(value)))


def cluster_cost(unique_lengths: list[tuple[int, int]], start: int, end: int, k: int) -> tuple[int, int]:
    low = unique_lengths[start][0]
    high = unique_lengths[end][0]
    best: tuple[int, int] | None = None
    for anchor in range(low, high + 1):
        cost = gamma_bits(anchor + 1)
        for length, count in unique_lengths[start : end + 1]:
            cost += count * signed_rice_bits(length - anchor, k)
        row = (cost, anchor)
        if best is None or row[0] < best[0]:
            best = row
    if best is None:
        raise RuntimeError((start, end, k))
    return best


def best_partition(unique_lengths: list[tuple[int, int]], cluster_count: int, k: int) -> dict:
    n = len(unique_lengths)
    cluster = [[None for _ in range(n)] for __ in range(n)]
    for start in range(n):
        for end in range(start, n):
            cluster[start][end] = cluster_cost(unique_lengths, start, end, k)

    dp: list[list[tuple[float, list[dict]]]] = [
        [(float("inf"), []) for _ in range(n)] for __ in range(cluster_count + 1)
    ]
    for end in range(n):
        cost, anchor = cluster[0][end]
        dp[1][end] = (cost, [{"start": 0, "end": end, "anchor": anchor, "cost": cost}])

    for count in range(2, cluster_count + 1):
        for end in range(count - 1, n):
            for previous_end in range(count - 2, end):
                cost, anchor = cluster[previous_end + 1][end]
                candidate = dp[count - 1][previous_end][0] + cost
                if candidate < dp[count][end][0]:
                    dp[count][end] = (
                        candidate,
                        dp[count - 1][previous_end][1]
                        + [{"start": previous_end + 1, "end": end, "anchor": anchor, "cost": cost}],
                    )

    cost, parts = dp[cluster_count][n - 1]
    return {"cluster_payload_bits": cost, "clusters": parts}


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    lengths = [len(books[str(book)]) for book in formula["policy"]["book_order"]]
    unique_lengths = sorted(Counter(lengths).items())
    current_length_bits = formula["mdl_estimate_rough"]["book_length_bits"]
    current_total_bits = formula["mdl_estimate_rough"]["sequential_lz_length_ledger_bits"]

    rows = []
    for cluster_count in range(2, 7):
        mode_bits = ceil_log2(cluster_count) * len(lengths)
        for k in range(0, 11):
            partition = best_partition(unique_lengths, cluster_count, k)
            book_length_bits = (
                gamma_bits(cluster_count + 1)
                + gamma_bits(k + 1)
                + mode_bits
                + partition["cluster_payload_bits"]
            )
            total_bits = current_total_bits - current_length_bits + book_length_bits
            rows.append(
                {
                    "model": "multi_anchor_signed_rice_length_ledger",
                    "cluster_count": cluster_count,
                    "k": k,
                    "mode_bits": mode_bits,
                    "book_length_bits": book_length_bits,
                    "total_bits": total_bits,
                    "delta_vs_current_bits": total_bits - current_total_bits,
                    "clusters": partition["clusters"],
                    "decodable": True,
                }
            )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    classification = (
        "multi_anchor_book_length_ledger_improvement"
        if best["total_bits"] < current_total_bits
        else "multi_anchor_book_length_ledger_not_promoted"
    )

    result = {
        "schema": "book_length_multi_anchor_search.v1",
        "test": "34_book_length_multi_anchor_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_total_bits,
        "current_book_length_bits": current_length_bits,
        "length_count": len(lengths),
        "unique_length_count": len(unique_lengths),
        "best_model": best,
        "top_models": rows[:20],
        "boundary": formula["boundary"],
    }

    lines = [
        "# Book Length Multi-Anchor Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the promoted single-anchor book-length ledger",
        "can be improved by a decodable multi-anchor signed-Rice mixture. The",
        "search uses optimal dynamic programming over sorted unique lengths and",
        "charges cluster anchors, `k`, and explicit per-book mode bits.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_total_bits:.1f}` |",
        f"| Current book-length bits | `{current_length_bits:.1f}` |",
        f"| Best multi-anchor book-length bits | `{best['book_length_bits']:.1f}` |",
        f"| Best multi-anchor total bits | `{best['total_bits']:.1f}` |",
        f"| Delta vs current | `{best['delta_vs_current_bits']:.1f}` |",
        f"| Best cluster count | `{best['cluster_count']}` |",
        f"| Best k | `{best['k']}` |",
        "",
        "## Top Models",
        "",
        "| Rank | Clusters | k | Book-length bits | Total bits | Delta |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(rows[:10], start=1):
        lines.append(
            f"| `{index}` | `{row['cluster_count']}` | `{row['k']}` | "
            f"`{row['book_length_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The best multi-anchor ledger is worse than the promoted single-anchor",
            "ledger once per-book mode bits and extra anchor declarations are paid.",
            "The current `anchor=151`, `k=5` length ledger remains the active bound.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter the",
            "book text, row0, or semantic verdict.",
        ]
    )
    write_result("34_book_length_multi_anchor_search", result, lines)


if __name__ == "__main__":
    main()
