from __future__ import annotations

import csv
import json
import math
import random
import statistics
import time
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SKELETON_LEDGER = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "99_exact_skeleton_dependency_ledger.json"
)
BOOKCASE_MANIFEST = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "tables"
    / "hellgate_public_bookcase_manifest.csv"
)

MIN_COPY_LEN = 5
SEED_SIZES = [5, 10, 15, 20]
RANDOM_SAMPLES_PER_K = 100
PERMUTED_PREFIX_SAMPLES_PER_K = 100
RNG_SEED = 46920260621
DIGITS = [str(i) for i in range(10)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def log2_comb(n: int, k: int) -> float:
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


def entropy(text: str) -> float:
    if not text:
        return 0.0
    return -sum(
        (text.count(digit) / len(text)) * math.log2(text.count(digit) / len(text))
        for digit in DIGITS
        if digit in text
    )


def repeated_ngram_fraction(text: str, n: int = MIN_COPY_LEN) -> float:
    if len(text) < n:
        return 0.0
    grams = [text[i : i + n] for i in range(len(text) - n + 1)]
    return 1.0 - (len(set(grams)) / len(grams))


def build_source_index(source: str) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos in range(0, len(source) - MIN_COPY_LEN + 1):
        index.setdefault(source[pos : pos + MIN_COPY_LEN], []).append(pos)
    return index


def source_target_maxlens(source: str, target: str) -> list[int]:
    index = build_source_index(source)
    maxlens = [0] * len(target)
    for tpos in range(0, max(0, len(target) - MIN_COPY_LEN + 1)):
        key = target[tpos : tpos + MIN_COPY_LEN]
        best = 0
        for spos in index.get(key, []):
            length = MIN_COPY_LEN
            max_len = min(len(source) - spos, len(target) - tpos)
            while length < max_len and source[spos + length] == target[tpos + length]:
                length += 1
            if length > best:
                best = length
        maxlens[tpos] = best
    return maxlens


def precompute_source_target_maxlens(books: dict[int, str]) -> dict[int, dict[int, list[int]]]:
    rows: dict[int, dict[int, list[int]]] = {}
    for target_book, target in books.items():
        target_rows: dict[int, list[int]] = {}
        for source_book, source in books.items():
            if source_book == target_book:
                continue
            target_rows[source_book] = source_target_maxlens(source, target)
        rows[target_book] = target_rows
    return rows


def better(candidate: tuple[int, int, int, int], incumbent: tuple[int, int, int, int] | None) -> bool:
    return incumbent is None or candidate < incumbent


def parse_target(maxlens: list[int]) -> dict[str, Any]:
    n = len(maxlens)
    # State key is (position, previous_was_literal). Cost is ordered so the DP
    # first minimizes literal digits, then dependency fields/copy items.
    dist: dict[tuple[int, bool], tuple[int, int, int, int]] = {(0, False): (0, 0, 0, 0)}
    back: dict[tuple[int, bool], tuple[tuple[int, bool], tuple[str, int]]] = {}
    for pos in range(n + 1):
        for previous_literal in (False, True):
            state = (pos, previous_literal)
            cost = dist.get(state)
            if cost is None or pos >= n:
                continue

            literal_cost = (
                cost[0] + 1,
                cost[1],
                cost[2] + (0 if previous_literal else 1),
                cost[3] + (0 if previous_literal else 1),
            )
            literal_state = (pos + 1, True)
            if better(literal_cost, dist.get(literal_state)):
                dist[literal_state] = literal_cost
                back[literal_state] = (state, ("literal", 1))

            length = maxlens[pos]
            if length >= MIN_COPY_LEN:
                copy_state = (pos + length, False)
                copy_cost = (cost[0], cost[1] + 1, cost[2], cost[3] + 1)
                if better(copy_cost, dist.get(copy_state)):
                    dist[copy_state] = copy_cost
                    back[copy_state] = (state, ("copy", length))

    end_state = min(((n, False), (n, True)), key=lambda state: dist.get(state, (10**9, 10**9, 10**9, 10**9)))
    literal_digits, copy_items, literal_runs, op_count = dist[end_state]
    ops = []
    state = end_state
    while state != (0, False):
        previous, op = back[state]
        ops.append((previous[0], op[0], op[1]))
        state = previous
    ops.reverse()
    copied_mask = [False] * n
    copied_digits = 0
    for start, kind, length in ops:
        if kind == "copy":
            copied_digits += length
            for offset in range(start, start + length):
                copied_mask[offset] = True
    return {
        "literal_digits": literal_digits,
        "copy_items": copy_items,
        "literal_runs": literal_runs,
        "op_count": op_count,
        "copied_digits": copied_digits,
        "copied_mask": copied_mask,
    }


def bookcase_order() -> list[int]:
    if not BOOKCASE_MANIFEST.exists():
        return []
    rows = []
    with BOOKCASE_MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("local_match_status") != "resolved_unique" or not row.get("local_bookid"):
                continue
            rows.append((int(row["hg_public_entry"]), int(row["local_bookid"])))
    seen = set()
    ordered = []
    for _entry, book in sorted(rows):
        if book not in seen:
            seen.add(book)
            ordered.append(book)
    return ordered


def bookcase_groups() -> dict[str, list[int]]:
    if not BOOKCASE_MANIFEST.exists():
        return {}
    groups: dict[str, list[int]] = {}
    with BOOKCASE_MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("local_match_status") != "resolved_unique" or not row.get("local_bookid"):
                continue
            label = f"hellgate_public_bookcase_{row['bookcase_public']}"
            groups.setdefault(label, []).append(int(row["local_bookid"]))
    return {label: sorted(set(books)) for label, books in groups.items()}


def mean(values: list[float]) -> float:
    return float(statistics.mean(values)) if values else 0.0


def median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def summarize_book_stats(books: dict[int, str], book_ids: list[int]) -> dict[str, float]:
    if not book_ids:
        return {
            "book_count": 0,
            "mean_length": 0.0,
            "mean_entropy": 0.0,
            "mean_repeated_5gram_fraction": 0.0,
        }
    return {
        "book_count": len(book_ids),
        "mean_length": mean([len(books[book]) for book in book_ids]),
        "mean_entropy": mean([entropy(books[book]) for book in book_ids]),
        "mean_repeated_5gram_fraction": mean(
            [repeated_ngram_fraction(books[book]) for book in book_ids]
        ),
    }


def main() -> None:
    start = time.perf_counter()
    books_raw = load_json(BOOKS_DIGITS)
    books = {int(book): text for book, text in books_raw.items()}
    all_books = sorted(books)
    total_digits = sum(len(text) for text in books.values())
    skeleton_ledger = load_json(SKELETON_LEDGER)
    if skeleton_ledger.get("translation_delta") != "NONE":
        raise RuntimeError("input skeleton ledger changed translation boundary")

    maxlens_by_target_source = precompute_source_target_maxlens(books)

    @lru_cache(maxsize=None)
    def evaluate_seed(seed_tuple: tuple[int, ...]) -> dict[str, Any]:
        seed = set(seed_tuple)
        target_books = [book for book in all_books if book not in seed]
        totals = {
            "target_digits": 0,
            "copied_digits_explained": 0,
            "literal_digits_required": 0,
            "copy_items_required": 0,
            "literal_runs_required": 0,
            "op_count": 0,
            "low_book_target_digits": 0,
            "low_book_copied_digits": 0,
            "high_book_target_digits": 0,
            "high_book_copied_digits": 0,
        }
        copied_rates = []
        for target_book in target_books:
            n = len(books[target_book])
            combined = [0] * n
            for source_book in seed_tuple:
                source_lens = maxlens_by_target_source[target_book].get(source_book)
                if source_lens is None:
                    continue
                for pos, length in enumerate(source_lens):
                    if length > combined[pos]:
                        combined[pos] = length
            parsed = parse_target(combined)
            copied = int(parsed["copied_digits"])
            totals["target_digits"] += n
            totals["copied_digits_explained"] += copied
            totals["literal_digits_required"] += int(parsed["literal_digits"])
            totals["copy_items_required"] += int(parsed["copy_items"])
            totals["literal_runs_required"] += int(parsed["literal_runs"])
            totals["op_count"] += int(parsed["op_count"])
            copied_rates.append(copied / n if n else 0.0)
            if target_book < 35:
                totals["low_book_target_digits"] += n
                totals["low_book_copied_digits"] += copied
            else:
                totals["high_book_target_digits"] += n
                totals["high_book_copied_digits"] += copied

        k = len(seed_tuple)
        seed_digits = sum(len(books[book]) for book in seed_tuple)
        copied = totals["copied_digits_explained"]
        declaration_bits = log2_comb(len(all_books), k)
        low_rate = (
            totals["low_book_copied_digits"] / totals["low_book_target_digits"]
            if totals["low_book_target_digits"]
            else 0.0
        )
        high_rate = (
            totals["high_book_copied_digits"] / totals["high_book_target_digits"]
            if totals["high_book_target_digits"]
            else 0.0
        )
        return {
            "seed_books": list(seed_tuple),
            "seed_book_count": k,
            "seed_digits": seed_digits,
            "target_book_count": len(target_books),
            "target_digits": totals["target_digits"],
            "copied_digits_explained": copied,
            "literal_digits_required": totals["literal_digits_required"],
            "copy_items_required": totals["copy_items_required"],
            "literal_runs_required": totals["literal_runs_required"],
            "op_count": totals["op_count"],
            "coverage_rate": copied / totals["target_digits"] if totals["target_digits"] else 0.0,
            "median_book_coverage_rate": median(copied_rates),
            "low_book_coverage_rate": low_rate,
            "high_book_coverage_rate": high_rate,
            "prefix_holdout_gap_abs": abs(low_rate - high_rate),
            "seed_declaration_bits": declaration_bits,
            "payload_gain_before_declaration_bits": copied * math.log2(10),
            "payload_gain_after_declaration_bits": copied * math.log2(10) - declaration_bits,
            "source_dependency_remaining": totals["copy_items_required"],
            "copy_items_per_1000_copied_digits": (
                totals["copy_items_required"] * 1000 / copied if copied else 0.0
            ),
            "seed_stats": summarize_book_stats(books, list(seed_tuple)),
            "derived_stats": summarize_book_stats(books, target_books),
        }

    singleton_scores = [
        (evaluate_seed((book,))["copied_digits_explained"], book) for book in all_books
    ]
    singleton_ranked = [book for _score, book in sorted(singleton_scores, reverse=True)]

    def greedy_seed(k: int) -> list[int]:
        chosen: list[int] = []
        remaining = set(all_books)
        for _ in range(k):
            best_book = None
            best_score = None
            for book in sorted(remaining):
                candidate = tuple(sorted(chosen + [book]))
                candidate_row = evaluate_seed(candidate)
                score = (
                    candidate_row["copied_digits_explained"],
                    -candidate_row["literal_digits_required"],
                    -candidate_row["copy_items_required"],
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_book = book
            assert best_book is not None
            chosen.append(best_book)
            remaining.remove(best_book)
        return sorted(chosen)

    bookcase_prefix = bookcase_order()
    rng = random.Random(RNG_SEED)

    candidate_rows = []
    random_summaries = []
    permuted_summaries = []
    greedy_sets: dict[int, list[int]] = {}
    for k in SEED_SIZES:
        fixed_candidates: list[tuple[str, str, list[int]]] = []
        fixed_candidates.append(("canonical_prefix", "zero_search_prefix", list(range(k))))
        if k == 10:
            fixed_candidates.append(("operational_0_9", "current_operational_seed", list(range(10))))
        fixed_candidates.append(
            ("singleton_centrality_top", "posthoc_single_book_coverage_top_k", sorted(singleton_ranked[:k]))
        )
        greedy_sets[k] = greedy_seed(k)
        fixed_candidates.append(("greedy_coverage", "posthoc_greedy_coverage", greedy_sets[k]))
        if bookcase_prefix:
            seeds = list(bookcase_prefix[:k])
            for book in all_books:
                if len(seeds) >= k:
                    break
                if book not in seeds:
                    seeds.append(book)
            fixed_candidates.append(
                ("public_bookcase_order_prefix", "metadata_public_bookcase_then_canonical_fill", sorted(seeds))
            )

        seen_fixed: set[tuple[int, ...]] = set()
        for label, search_class, seed_books in fixed_candidates:
            seed_tuple = tuple(sorted(seed_books))
            if seed_tuple in seen_fixed and label != "operational_0_9":
                continue
            seen_fixed.add(seed_tuple)
            row = evaluate_seed(seed_tuple).copy()
            row.update({"label": label, "search_class": search_class})
            candidate_rows.append(row)

        random_rows = []
        for index in range(RANDOM_SAMPLES_PER_K):
            seed_tuple = tuple(sorted(rng.sample(all_books, k)))
            row = evaluate_seed(seed_tuple)
            random_rows.append(row)
        random_summaries.append(summarize_distribution("random_seed_sets", k, random_rows))

        permuted_rows = []
        for index in range(PERMUTED_PREFIX_SAMPLES_PER_K):
            permuted = all_books[:]
            rng.shuffle(permuted)
            row = evaluate_seed(tuple(sorted(permuted[:k])))
            permuted_rows.append(row)
        permuted_summaries.append(summarize_distribution("permuted_order_prefixes", k, permuted_rows))

    rows_by_k: dict[int, list[dict[str, Any]]] = {}
    for row in candidate_rows:
        rows_by_k.setdefault(int(row["seed_book_count"]), []).append(row)

    controls_by_key = {
        ("random_seed_sets", row["seed_book_count"]): row for row in random_summaries
    }
    controls_by_key.update(
        {("permuted_order_prefixes", row["seed_book_count"]): row for row in permuted_summaries}
    )
    for row in candidate_rows:
        k = int(row["seed_book_count"])
        random_control = controls_by_key[("random_seed_sets", k)]
        row["random_control_percentile_copied_digits"] = percentile(
            row["copied_digits_explained"],
            random_control["copied_digits_samples"],
        )
        row["gain_vs_random_median_copied_digits"] = (
            row["copied_digits_explained"] - random_control["copied_digits_median"]
        )
        row["gain_vs_random_median_after_declaration_bits"] = (
            row["payload_gain_after_declaration_bits"]
            - random_control["payload_gain_after_declaration_bits_median"]
        )

    family_holdouts = []
    for label, heldout in sorted(bookcase_groups().items()):
        seed_books = tuple(book for book in all_books if book not in heldout)
        row = evaluate_seed(seed_books)
        family_holdouts.append(
            {
                "label": label,
                "heldout_books": heldout,
                "seed_book_count": len(seed_books),
                "heldout_target_digits": sum(len(books[book]) for book in heldout),
                "coverage_rate_all_nonseed_targets": row["coverage_rate"],
                "literal_digits_required_all_nonseed_targets": row["literal_digits_required"],
                "copied_digits_explained_all_nonseed_targets": row["copied_digits_explained"],
                "classification": "family_holdout_control_only",
            }
        )

    best_by_k = []
    for k in SEED_SIZES:
        candidates = rows_by_k[k]
        best = max(
            candidates,
            key=lambda row: (
                row["copied_digits_explained"],
                row["payload_gain_after_declaration_bits"],
                -row["copy_items_required"],
            ),
        )
        best_by_k.append(best)

    operational = next(
        row for row in candidate_rows if row["label"] == "operational_0_9" and row["seed_book_count"] == 10
    )
    best_k10 = max(
        rows_by_k[10],
        key=lambda row: (
            row["copied_digits_explained"],
            row["payload_gain_after_declaration_bits"],
            -row["copy_items_required"],
        ),
    )
    operational_random = controls_by_key[("random_seed_sets", 10)]
    k10_special = (
        operational["copied_digits_explained"] > operational_random["copied_digits_p95"]
        and operational["copied_digits_explained"] >= best_k10["copied_digits_explained"]
    )
    alternative_better_than_operational = best_k10["copied_digits_explained"] > operational["copied_digits_explained"]
    final_category = (
        "PROMOTED_MECHANICAL_SEED_CLUE"
        if k10_special and not alternative_better_than_operational
        else "WEAK_SEED_CLUE"
        if operational["copied_digits_explained"] > operational_random["copied_digits_median"]
        else "AUDIT_ONLY_COMPRESSION"
    )
    if alternative_better_than_operational:
        final_category = "AUDIT_ONLY_COMPRESSION"

    result = {
        "schema": "seed_primacy_coverage_audit.v1",
        "classification": final_category,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "skeleton_dependency_ledger": rel(SKELETON_LEDGER),
            "bookcase_manifest": rel(BOOKCASE_MANIFEST) if BOOKCASE_MANIFEST.exists() else None,
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "does_not_search_plaintext": True,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "min_copy_len": MIN_COPY_LEN,
            "parse_policy": "dynamic_programming_over_longest_available_copy_at_each_position",
            "copy_crosses_seed_book_boundaries": False,
            "target_self_copy_allowed": False,
            "derived_to_derived_copy_allowed": False,
            "random_samples_per_k": RANDOM_SAMPLES_PER_K,
            "permuted_prefix_samples_per_k": PERMUTED_PREFIX_SAMPLES_PER_K,
            "rng_seed": RNG_SEED,
        },
        "skeleton_context": {
            "operational_seed_books": skeleton_ledger["residual_dependencies"]["seed_books_external"],
            "operational_skeleton_records": skeleton_ledger["exact_skeleton_dependency_counts"][
                "atlas_operation_skeleton_records"
            ],
            "operational_copy_source_fields": skeleton_ledger["exact_skeleton_dependency_counts"][
                "external_copy_source_fields"
            ],
            "operational_literal_payload_digits": skeleton_ledger["exact_skeleton_dependency_counts"][
                "external_literal_payload_digits"
            ],
            "operational_copied_digits": skeleton_ledger["residual_dependencies"]["copied_digits"],
            "note": "Seed-only parses are compared to the existing source-free skeleton ledger, not promoted as a replacement generator.",
        },
        "summary": {
            "elapsed_seconds": time.perf_counter() - start,
            "book_count": len(all_books),
            "total_digits": total_digits,
            "seed_sizes": SEED_SIZES,
            "operational_0_9": compact_row(operational),
            "best_k10_candidate": compact_row(best_k10),
            "alternative_better_than_operational": alternative_better_than_operational,
            "operational_above_random_median": operational["copied_digits_explained"]
            > operational_random["copied_digits_median"],
            "operational_above_random_p95": operational["copied_digits_explained"]
            > operational_random["copied_digits_p95"],
            "final_category": final_category,
            "interpretation": (
                "This is a seed-only substring coverage audit. It can identify "
                "small high-coverage subsets, but source choice, literal payload, "
                "and seed-set selection remain external; therefore coverage gains "
                "are mechanical/compression clues only unless they beat controls "
                "after declaration cost and survive non-posthoc constraints."
            ),
        },
        "candidate_rows": sorted(
            candidate_rows,
            key=lambda row: (row["seed_book_count"], -row["copied_digits_explained"], row["label"]),
        ),
        "best_by_k": [compact_row(row) for row in best_by_k],
        "random_control_summaries": drop_samples(random_summaries),
        "permuted_prefix_control_summaries": drop_samples(permuted_summaries),
        "family_holdout_controls": family_holdouts,
        "decision": {
            "books_0_9_special_as_seed": bool(k10_special),
            "alternative_seed_better_for_k10": bool(alternative_better_than_operational),
            "best_alternative_k10_seed": best_k10["seed_books"],
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "seed_primacy_not_promoted_posthoc_coverage_only",
            "gain_over_random_survives_declaration_cost": bool(
                operational["gain_vs_random_median_after_declaration_bits"] > 0
            ),
            "mechanical_primary_core_signal": (
                "not_promoted_posthoc_alternatives_exist"
                if alternative_better_than_operational
                else "weak_seed_clue"
                if final_category == "WEAK_SEED_CLUE"
                else "promoted_mechanical_clue"
                if final_category == "PROMOTED_MECHANICAL_SEED_CLUE"
                else "audit_only_compression"
            ),
            "authorial_seed_claim": "BLOCKED_NEEDS_EXTERNAL_SOURCE",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "row0_status": "unchanged_exogenous",
        },
    }

    write_outputs(result)


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "label",
        "search_class",
        "seed_books",
        "seed_book_count",
        "seed_digits",
        "target_digits",
        "copied_digits_explained",
        "literal_digits_required",
        "copy_items_required",
        "literal_runs_required",
        "coverage_rate",
        "median_book_coverage_rate",
        "prefix_holdout_gap_abs",
        "seed_declaration_bits",
        "payload_gain_after_declaration_bits",
        "gain_vs_random_median_copied_digits",
        "gain_vs_random_median_after_declaration_bits",
        "random_control_percentile_copied_digits",
    ]
    return {key: row[key] for key in keys if key in row}


def summarize_distribution(label: str, k: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    copied = sorted(int(row["copied_digits_explained"]) for row in rows)
    after = sorted(float(row["payload_gain_after_declaration_bits"]) for row in rows)
    coverage = sorted(float(row["coverage_rate"]) for row in rows)
    return {
        "label": label,
        "seed_book_count": k,
        "sample_count": len(rows),
        "copied_digits_samples": copied,
        "copied_digits_min": copied[0],
        "copied_digits_median": median(copied),
        "copied_digits_mean": mean([float(v) for v in copied]),
        "copied_digits_p95": copied[int(0.95 * (len(copied) - 1))],
        "copied_digits_max": copied[-1],
        "coverage_rate_median": median(coverage),
        "coverage_rate_p95": coverage[int(0.95 * (len(coverage) - 1))],
        "payload_gain_after_declaration_bits_median": median(after),
        "payload_gain_after_declaration_bits_p95": after[int(0.95 * (len(after) - 1))],
    }


def percentile(value: float, samples: list[int]) -> float:
    if not samples:
        return 0.0
    return sum(1 for sample in samples if sample <= value) / len(samples)


def drop_samples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if key != "copied_digits_samples"} for row in rows]


def write_outputs(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "01_seed_coverage_audit.json"
    md_path = TEST_RESULTS / "01_seed_coverage_audit.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = result["summary"]
    op = summary["operational_0_9"]
    best = summary["best_k10_candidate"]
    lines = [
        "# Seed Coverage Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Scope",
        "",
        f"- Minimum copy length: `{result['scope']['min_copy_len']}`.",
        f"- Parse policy: `{result['scope']['parse_policy']}`.",
        "- Copy source is restricted to declared seed books only.",
        "- Copies cannot cross seed-book boundaries.",
        "- Target self-copy and derived-to-derived copy are disabled.",
        f"- Random controls per k: `{result['scope']['random_samples_per_k']}`.",
        f"- Permuted-prefix controls per k: `{result['scope']['permuted_prefix_samples_per_k']}`.",
        "",
        "## Operational 0-9",
        "",
        f"- Seed books: `{op['seed_books']}`.",
        f"- Copied digits explained: `{op['copied_digits_explained']}` / `{op['target_digits']}`.",
        f"- Literal digits required: `{op['literal_digits_required']}`.",
        f"- Copy items required: `{op['copy_items_required']}`.",
        f"- Coverage rate: `{op['coverage_rate']:.6f}`.",
        f"- Random copied-digit percentile: `{op['random_control_percentile_copied_digits']:.6f}`.",
        f"- Gain vs random median after declaration: `{op['gain_vs_random_median_after_declaration_bits']:.3f}` bits.",
        "",
        "## Best k=10 Candidate",
        "",
        f"- Label: `{best['label']}`.",
        f"- Seed books: `{best['seed_books']}`.",
        f"- Copied digits explained: `{best['copied_digits_explained']}`.",
        f"- Literal digits required: `{best['literal_digits_required']}`.",
        f"- Coverage rate: `{best['coverage_rate']:.6f}`.",
        f"- Alternative better than operational: `{summary['alternative_better_than_operational']}`.",
        "",
        "## Best By k",
        "",
        "| k | label | copied | literal | copies | coverage | seed books |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in result["best_by_k"]:
        lines.append(
            f"| {row['seed_book_count']} | `{row['label']}` | {row['copied_digits_explained']} | "
            f"{row['literal_digits_required']} | {row['copy_items_required']} | "
            f"{row['coverage_rate']:.6f} | `{row['seed_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Books 0-9 special as seed: `{result['decision']['books_0_9_special_as_seed']}`.",
            f"- Alternative k=10 seed better: `{result['decision']['alternative_seed_better_for_k10']}`.",
            f"- Gain over random survives declaration cost: `{result['decision']['gain_over_random_survives_declaration_cost']}`.",
            f"- Mechanical primary core signal: `{result['decision']['mechanical_primary_core_signal']}`.",
            f"- Authorial seed claim: `{result['decision']['authorial_seed_claim']}`.",
            "- Row0 remains unchanged and exogenous.",
            "- Translation/plaintext status remains `NONE`.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
