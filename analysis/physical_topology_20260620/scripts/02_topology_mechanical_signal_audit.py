from __future__ import annotations

import csv
import json
import random
import sqlite3
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TABLES = HERE / "tables"
REPORTS = HERE / "reports" / "test_results"
MANIFEST = TABLES / "hellgate_public_bookcase_manifest.csv"
DB = ROOT / "data/bonelord_operational.sqlite"


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_books() -> dict[str, dict]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return {
        row["bookid"]: dict(row)
        for row in conn.execute("select bookid, digits, digitslen, decodedbase from sheet__books")
    }


def bigram_jaccard(a: str, b: str) -> float:
    aa = {a[i : i + 2] for i in range(max(0, len(a) - 1))}
    bb = {b[i : i + 2] for i in range(max(0, len(b) - 1))}
    if not aa and not bb:
        return 1.0
    return len(aa & bb) / len(aa | bb)


def suffix_prefix_overlap(a: str, b: str, max_k: int = 80) -> int:
    cap = min(max_k, len(a), len(b))
    best = 0
    for k in range(1, cap + 1):
        if a[-k:] == b[:k]:
            best = k
    return best


def adjacent_scores(order: list[str], books: dict[str, dict]) -> list[float]:
    scores = []
    for left, right in zip(order, order[1:]):
        a = books[left]["decodedbase"]
        b = books[right]["decodedbase"]
        # Exact endpoint continuity is primary; bigram similarity keeps the
        # score from being all-zero on unrelated adjacent books.
        scores.append((suffix_prefix_overlap(a, b) / 80.0) + bigram_jaccard(a, b))
    return scores


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile_rank(observed: float, controls: list[float]) -> float:
    return sum(1 for value in controls if value >= observed) / len(controls)


def group_scores(groups: dict[str, list[str]], books: dict[str, dict]) -> list[float]:
    scores = []
    for ids in groups.values():
        uniq = sorted(set(ids), key=int)
        for a, b in combinations(uniq, 2):
            scores.append(bigram_jaccard(books[a]["decodedbase"], books[b]["decodedbase"]))
    return scores


def main() -> None:
    books = load_books()
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    resolved = [
        row
        for row in rows
        if row["local_match_status"] == "resolved_unique" and row["local_bookid"] in books
    ]
    resolved_order = [row["local_bookid"] for row in sorted(resolved, key=lambda r: int(r["hg_public_entry"]))]

    rng = random.Random(46920260620)
    observed_adjacent = mean(adjacent_scores(resolved_order, books))
    shuffle_adjacent = []
    for _ in range(2000):
        shuffled = resolved_order[:]
        rng.shuffle(shuffled)
        shuffle_adjacent.append(mean(adjacent_scores(shuffled, books)))
    adjacent_p_ge = percentile_rank(observed_adjacent, shuffle_adjacent)

    groups: dict[str, list[str]] = {}
    for row in resolved:
        groups.setdefault(row["bookcase_public"], []).append(row["local_bookid"])
    observed_group = mean(group_scores(groups, books))
    group_sizes = [len(set(ids)) for ids in groups.values() if len(set(ids)) > 1]
    unique_resolved = sorted(set(resolved_order), key=int)
    shuffle_group = []
    for _ in range(2000):
        shuffled = unique_resolved[:]
        rng.shuffle(shuffled)
        offset = 0
        control_groups = {}
        for idx, size in enumerate(group_sizes):
            control_groups[str(idx)] = shuffled[offset : offset + size]
            offset += size
        shuffle_group.append(mean(group_scores(control_groups, books)))
    group_p_ge = percentile_rank(observed_group, shuffle_group)

    isle_prefix = "6512889672"
    isle_candidates = [bid for bid, book in books.items() if book["digits"].startswith(isle_prefix)]
    hellgate_rows_for_isle = [
        row
        for row in rows
        if row["public_title_prefix"] == isle_prefix
    ]
    public_entry_for_isle = hellgate_rows_for_isle[0]["hg_public_entry"] if hellgate_rows_for_isle else None
    tibiasecrets_book35_claim_status = (
        "indexing_mismatch_under_fandom_overview_seed"
        if public_entry_for_isle and public_entry_for_isle != "35"
        else "not_tested"
    )

    classification = (
        "weak_topology_signal"
        if adjacent_p_ge <= 0.05 or group_p_ge <= 0.05
        else "no_promoted_topology_signal"
    )
    result = {
        "schema": "topology_mechanical_signal_audit.v1",
        "test": "02_topology_mechanical_signal_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "resolved_entries_used": len(resolved_order),
        "unique_resolved_books": len(set(resolved_order)),
        "public_order_adjacent_score": observed_adjacent,
        "public_order_shuffle_mean": mean(shuffle_adjacent),
        "public_order_p_ge": adjacent_p_ge,
        "bookcase_group_score": observed_group,
        "bookcase_group_shuffle_mean": mean(shuffle_group),
        "bookcase_group_p_ge": group_p_ge,
        "isle_6512889672_candidates": isle_candidates,
        "isle_6512889672_hellgate_public_entry": public_entry_for_isle,
        "tibiasecrets_book35_claim_status": tibiasecrets_book35_claim_status,
        "kharos_status": "blocked_until_exact_text_or_independent_index",
        "hypotheses": {
            "H-TOP1": "accepted_process_guard",
            "H-TOP2": "open_requires_coordinates",
            "H-TOP3": "weak_context_clue",
            "H-TOP4": "watchlist_only",
            "H-TOP5": "tested_no_promotion" if classification == "no_promoted_topology_signal" else "weak_mechanical_clue",
        },
    }

    lines = [
        "# Topology Mechanical Signal Audit",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the partial public Hellgate order or bookcase",
        "grouping predicts simple row0 mechanical similarity better than",
        "deterministic shuffles. It is not a translation test.",
        "",
        "## Public Order",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Resolved entries used | `{len(resolved_order)}` |",
        f"| Unique resolved books | `{len(set(resolved_order))}` |",
        f"| Public adjacent score | `{observed_adjacent:.6f}` |",
        f"| Shuffle mean | `{mean(shuffle_adjacent):.6f}` |",
        f"| p(control >= observed) | `{adjacent_p_ge:.4f}` |",
        "",
        "## Bookcase Grouping",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Bookcase group score | `{observed_group:.6f}` |",
        f"| Shuffle mean | `{mean(shuffle_group):.6f}` |",
        f"| p(control >= observed) | `{group_p_ge:.4f}` |",
        "",
        "## External Anchors",
        "",
        f"- Isle shelf 39 prefix `6512889672` maps to local candidates `{isle_candidates}`.",
        f"- Under the Fandom overview seed, the same prefix is Hellgate public entry `{public_entry_for_isle}`, not public entry `35`; the TibiaSecrets `Book 35` statement remains an indexing/numbering mismatch to audit, not an accepted rejection.",
        "- Kharos/Ferumbras remains blocked until exact text or an independent indexed source is available.",
        "",
        "## H-TOP Status",
        "",
        "| Hypothesis | Status |",
        "|---|---|",
    ]
    for key, status in result["hypotheses"].items():
        lines.append(f"| `{key}` | `{status}` |")
    lines += [
        "",
        "## Conclusion",
        "",
        "The public topology seed is useful for future graph/holdout work, but this",
        "simple signal test does not promote a physical-order mechanism or any",
        "semantic reading.",
    ]
    write_result("02_topology_mechanical_signal_audit", result, lines)


if __name__ == "__main__":
    main()
