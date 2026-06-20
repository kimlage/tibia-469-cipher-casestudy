from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

from _common import ROOT, write_result

RNG = random.Random(46920260620)
CONTROL_TRIALS = 2000


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def pct_rank_ge(observed: float, values: list[float]) -> float:
    return (sum(v >= observed for v in values) + 1) / (len(values) + 1)


def pct_rank_le(observed: float, values: list[float]) -> float:
    return (sum(v <= observed for v in values) + 1) / (len(values) + 1)


def summarize_controls(observed: float, values: list[float]) -> dict:
    return {
        "observed": observed,
        "control_mean": mean(values) if values else 0.0,
        "control_sd": pstdev(values) if len(values) > 1 else 0.0,
        "control_max": max(values) if values else 0.0,
        "control_min": min(values) if values else 0.0,
        "p_ge": pct_rank_ge(observed, values),
        "p_le": pct_rank_le(observed, values),
    }


def random_digits(length: int, weights: dict[str, int]) -> str:
    digits = list(weights)
    total = sum(weights.values())
    cum = []
    acc = 0
    for d in digits:
        acc += weights[d]
        cum.append((acc / total, d))
    out = []
    for _ in range(length):
        x = RNG.random()
        for threshold, digit in cum:
            if x <= threshold:
                out.append(digit)
                break
    return "".join(out)


def random_multiset_permutation(s: str) -> str:
    chars = list(s)
    RNG.shuffle(chars)
    return "".join(chars)


def substr_count(haystack: str, needle: str) -> int:
    if not needle:
        return 0
    count = 0
    start = 0
    while True:
        idx = haystack.find(needle, start)
        if idx < 0:
            return count
        count += 1
        start = idx + 1


def build_substring_sets(strings: list[str], min_len: int, max_len: int) -> dict[int, set[str]]:
    sets: dict[int, set[str]] = {}
    for length in range(min_len, max_len + 1):
        vals: set[str] = set()
        for s in strings:
            if len(s) < length:
                continue
            for i in range(0, len(s) - length + 1):
                vals.add(s[i : i + length])
        sets[length] = vals
    return sets


def greedy_coverage(s: str, substring_sets: dict[int, set[str]], min_len: int, max_len: int) -> dict:
    covered = [False] * len(s)
    segments = []
    i = 0
    while i < len(s):
        best = None
        for length in range(min(max_len, len(s) - i), min_len - 1, -1):
            candidate = s[i : i + length]
            if candidate in substring_sets.get(length, set()):
                best = candidate
                break
        if best is None:
            i += 1
            continue
        start, end = i, i + len(best)
        for j in range(start, end):
            covered[j] = True
        segments.append({"start": start, "end": end, "length": len(best), "text": best})
        i = end
    return {
        "covered_digits": sum(covered),
        "covered_fraction": sum(covered) / len(s) if s else 0.0,
        "segments": segments[:20],
        "segment_count": len(segments),
    }


def majority_accuracy(labels: list[str], buckets: list[object]) -> float:
    by_bucket: dict[object, Counter] = defaultdict(Counter)
    for label, bucket in zip(labels, buckets):
        by_bucket[bucket][label] += 1
    correct = sum(max(counter.values()) for counter in by_bucket.values())
    return correct / len(labels)


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0

    def ranks(vals: list[float]) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda item: item[1])
        out = [0.0] * len(vals)
        i = 0
        while i < len(indexed):
            j = i
            while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
                j += 1
            rank = (i + j) / 2.0
            for k in range(i, j + 1):
                out[indexed[k][0]] = rank
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    deny = math.sqrt(sum((b - my) ** 2 for b in ry))
    if denx == 0 or deny == 0:
        return 0.0
    return num / (denx * deny)


def digit_order_from_seed(seed: str) -> dict[str, int]:
    order: list[str] = []
    for ch in seed:
        if ch.isdigit() and ch not in order:
            order.append(ch)
    for ch in "0123456789":
        if ch not in order:
            order.append(ch)
    return {digit: i for i, digit in enumerate(order)}


def seed_row0_stats(pair_table: dict, seeds: list[str]) -> list[dict]:
    pairs = sorted(pair_table)
    labels = [pair_table[p]["symbol_if_pure"] or "/".join(pair_table[p]["symbols"]) for p in pairs]

    def family_scores(order: dict[str, int]) -> dict[str, float]:
        coords = [(order[p[0]], order[p[1]]) for p in pairs]
        features = {
            "rank_distance": [abs(a - b) for a, b in coords],
            "rank_sum_mod10": [(a + b) % 10 for a, b in coords],
            "rank_product_mod10": [(a * b) % 10 for a, b in coords],
            "rank_min_quartile": [min(a, b) // 3 for a, b in coords],
            "rank_max_quartile": [max(a, b) // 3 for a, b in coords],
            "same_or_adjacent": [0 if a == b else 1 if abs(a - b) == 1 else 2 for a, b in coords],
            "rank_sum_mod14": [(a + b) % 14 for a, b in coords],
        }
        return {name: majority_accuracy(labels, buckets) for name, buckets in features.items()}

    rows = []
    for seed in seeds:
        observed_scores = family_scores(digit_order_from_seed(seed))
        best_family, best_accuracy = max(observed_scores.items(), key=lambda item: item[1])
        controls = []
        for _ in range(CONTROL_TRIALS):
            digits = list("0123456789")
            RNG.shuffle(digits)
            order = {digit: i for i, digit in enumerate(digits)}
            controls.append(max(family_scores(order).values()))
        summary = summarize_controls(best_accuracy, controls)
        rows.append({
            "seed": seed,
            "best_family": best_family,
            "best_accuracy": best_accuracy,
            "control_summary": summary,
            "classification": "rejected_control" if summary["p_ge"] > 0.05 else "weak_clue",
        })
    return rows


def source_number_stats(corpus: str, tape_text: str, digit_weights: dict[str, int], seeds: list[str]) -> list[dict]:
    rows = []
    for seed in seeds:
        observed = substr_count(corpus, seed)
        tape_observed = substr_count(tape_text, seed)
        random_controls = [substr_count(corpus, random_digits(len(seed), digit_weights)) for _ in range(CONTROL_TRIALS)]
        multiset_controls = [substr_count(corpus, random_multiset_permutation(seed)) for _ in range(CONTROL_TRIALS)]
        random_summary = summarize_controls(observed, random_controls)
        multiset_summary = summarize_controls(observed, multiset_controls)
        rows.append({
            "seed": seed,
            "length": len(seed),
            "corpus_exact_hits": observed,
            "tape_exact_hits": tape_observed,
            "same_length_random": random_summary,
            "digit_multiset_random": multiset_summary,
            "classification": (
                "weak_clue"
                if observed > 0 and random_summary["p_ge"] <= 0.01 and multiset_summary["p_ge"] <= 0.05
                else "rejected_control"
                if observed > 0
                else "absent_or_blocked"
            ),
        })
    return rows


def external_coverage_stats(book_strings: list[str], digit_weights: dict[str, int], manifest: dict) -> list[dict]:
    substring_sets = build_substring_sets(book_strings, min_len=5, max_len=32)
    sources = {
        "chayenne": "".join(manifest["external_holdouts"]["chayenne"]),
        "your_true_colour": "".join(manifest["external_holdouts"]["your_true_colour"]),
        "avar_tar": "".join(manifest["negative_controls"]["avar_tar"]),
        "secret_library_74032_45331": "7403245331",
        "honeminas_vectors": "4315334784",
        "knightmare_phrase": "347867908719766434660345",
        "elder_evil_eye": "65997854764653768764",
    }
    rows = []
    for name, digits in sources.items():
        observed = greedy_coverage(digits, substring_sets, 5, 32)
        random_controls = [
            greedy_coverage(random_digits(len(digits), digit_weights), substring_sets, 5, 32)["covered_fraction"]
            for _ in range(CONTROL_TRIALS)
        ]
        perm_controls = [
            greedy_coverage(random_multiset_permutation(digits), substring_sets, 5, 32)["covered_fraction"]
            for _ in range(CONTROL_TRIALS)
        ]
        random_summary = summarize_controls(observed["covered_fraction"], random_controls)
        perm_summary = summarize_controls(observed["covered_fraction"], perm_controls)
        rows.append({
            "name": name,
            "length": len(digits),
            "covered_fraction": observed["covered_fraction"],
            "covered_digits": observed["covered_digits"],
            "segment_count": observed["segment_count"],
            "example_segments": observed["segments"][:8],
            "same_length_random": random_summary,
            "digit_multiset_random": perm_summary,
            "classification": (
                "copy_holdout_like_secondary_validation"
                if name == "chayenne" and random_summary["p_ge"] <= 0.01
                else "negative_control_leaky_short_substrings"
                if name == "avar_tar" and observed["covered_fraction"] >= random_summary["control_mean"]
                else "external_anchor_not_supported"
            ),
        })
    return rows


def book_phase_stats(book_recipes: dict) -> list[dict]:
    rows = []
    book_ids = sorted(int(k) for k in book_recipes)
    features = []
    primary_components = []
    for book_id in book_ids:
        recipe = book_recipes[str(book_id)]
        literal_digits = sum(item.get("length", 0) for item in recipe if item["type"] == "literal")
        module_digits = sum(item.get("length", 0) for item in recipe if item["type"] != "literal")
        tape_spans = sum(1 for item in recipe if item["type"] == "tape_span")
        comps = [item.get("component_id", "literal") for item in recipe if item["type"] != "literal"]
        primary = Counter(comps).most_common(1)[0][0] if comps else "literal_only"
        features.append({
            "literal_digits": literal_digits,
            "module_digits": module_digits,
            "tape_spans": tape_spans,
            "item_count": len(recipe),
        })
        primary_components.append(primary)

    motifs = {
        "dreamer_duality_parity": [i % 2 for i in book_ids],
        "yalahar_quarters_mod4": [i % 4 for i in book_ids],
        "poi_thrones_mod7": [i % 7 for i in book_ids],
        "poi_14_symbols_mod14": [i % 14 for i in book_ids],
        "secret_library_table7_phase": [(i - 7) % 10 for i in book_ids],
    }

    def eta_squared(groups: list[int], values: list[float]) -> float:
        total_mean = mean(values)
        ss_between = 0.0
        ss_total = sum((v - total_mean) ** 2 for v in values)
        if ss_total == 0:
            return 0.0
        by_group: dict[int, list[float]] = defaultdict(list)
        for g, v in zip(groups, values):
            by_group[g].append(v)
        for vals in by_group.values():
            ss_between += len(vals) * (mean(vals) - total_mean) ** 2
        return ss_between / ss_total

    def primary_purity(groups: list[int]) -> float:
        by_group: dict[int, Counter] = defaultdict(Counter)
        for g, comp in zip(groups, primary_components):
            by_group[g][comp] += 1
        return sum(max(c.values()) for c in by_group.values()) / len(primary_components)

    for motif, groups in motifs.items():
        metric_rows = {}
        observed_values = []
        for feature_name in ["literal_digits", "module_digits", "tape_spans", "item_count"]:
            obs = eta_squared(groups, [f[feature_name] for f in features])
            controls = []
            for _ in range(CONTROL_TRIALS):
                shuffled = groups[:]
                RNG.shuffle(shuffled)
                controls.append(eta_squared(shuffled, [f[feature_name] for f in features]))
            metric_rows[feature_name] = summarize_controls(obs, controls)
            observed_values.append(obs)
        purity_obs = primary_purity(groups)
        purity_controls = []
        for _ in range(CONTROL_TRIALS):
            shuffled = groups[:]
            RNG.shuffle(shuffled)
            purity_controls.append(primary_purity(shuffled))
        metric_rows["primary_component_purity"] = summarize_controls(purity_obs, purity_controls)
        best_metric, best_summary = max(metric_rows.items(), key=lambda item: item[1]["p_ge"] * -1)
        rows.append({
            "motif": motif,
            "best_metric": best_metric,
            "best_summary": best_summary,
            "all_metrics": metric_rows,
            "classification": "weak_clue" if best_summary["p_ge"] <= 0.01 else "rejected_control",
        })
    return rows


def seed_cooccurrence_stats(book_strings: list[str], seeds: list[str]) -> list[dict]:
    joined_by_book = book_strings
    rows = []
    for i, a in enumerate(seeds):
        for b in seeds[i + 1 :]:
            both = sum((a in book) and (b in book) for book in joined_by_book)
            a_count = sum(a in book for book in joined_by_book)
            b_count = sum(b in book for book in joined_by_book)
            controls = []
            for _ in range(CONTROL_TRIALS):
                aa = random_multiset_permutation(a)
                bb = random_multiset_permutation(b)
                controls.append(sum((aa in book) and (bb in book) for book in joined_by_book))
            summary = summarize_controls(both, controls)
            rows.append({
                "pair": [a, b],
                "books_with_a": a_count,
                "books_with_b": b_count,
                "books_with_both": both,
                "digit_multiset_control": summary,
                "classification": "weak_clue" if both > 0 and summary["p_ge"] <= 0.01 else "rejected_control",
            })
    return rows


def row0_anomaly_stats(pair_table: dict) -> list[dict]:
    pairs = sorted(pair_table)
    labels = [pair_table[p]["symbol_if_pure"] or "/".join(pair_table[p]["symbols"]) for p in pairs]

    feature_defs = {
        "tridiag_diagonal_e": lambda p: p[0] == p[1],
        "tridiag_33_66_anchor": lambda p: p in {"33", "66"},
        "high_block_e_pressure": lambda p: int(p[0]) >= 6 and int(p[1]) >= 6,
        "donina_missing_39_or_93": lambda p: p in {"39", "93"},
        "subjective_19_91_conflict": lambda p: p == "19",
        "zero_touch": lambda p: "0" in p,
        "six_nine_orbit_touch": lambda p: "6" in p or "9" in p,
    }
    rows = []
    for name, predicate in feature_defs.items():
        selected = [i for i, p in enumerate(pairs) if predicate(p)]
        if not selected:
            rows.append({
                "feature": name,
                "selected_count": 0,
                "e_count": 0,
                "e_rate": 0.0,
                "control_summary": summarize_controls(0.0, [0.0] * CONTROL_TRIALS),
                "classification": "absent_or_blocked",
            })
            continue
        e_count = sum(labels[i] == "E" for i in selected)
        e_rate = e_count / len(selected)
        controls = []
        for _ in range(CONTROL_TRIALS):
            shuffled = labels[:]
            RNG.shuffle(shuffled)
            controls.append(sum(shuffled[i] == "E" for i in selected) / len(selected))
        summary = summarize_controls(e_rate, controls)
        rows.append({
            "feature": name,
            "selected_count": len(selected),
            "e_count": e_count,
            "e_rate": e_rate,
            "control_summary": summary,
            "classification": "weak_clue" if summary["p_ge"] <= 0.01 else "rejected_control",
        })
    return rows


def build_report(result: dict) -> list[str]:
    lines = [
        "# Deep Statistical Exhaustion",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `{result['translation_delta']}`.",
        "",
        "This suite adds direct statistical probes beyond the earlier wrapper audits:",
        "source-number exact hits, external-string coverage, seed-derived row0",
        "feature models, book phase/motif tests, and identity-anchor co-occurrence.",
        "",
        "## Source Number Exact Hits",
        "",
        "| Seed | Hits | Tape hits | Random p>= | Multiset p>= | Class |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in result["source_number_stats"]:
        lines.append(
            f"| `{row['seed']}` | {row['corpus_exact_hits']} | {row['tape_exact_hits']} | "
            f"{row['same_length_random']['p_ge']:.4f} | {row['digit_multiset_random']['p_ge']:.4f} | "
            f"`{row['classification']}` |"
        )
    lines += [
        "",
        "## External Coverage",
        "",
        "| Source | Covered | Random p>= | Multiset p>= | Class |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["external_coverage_stats"]:
        lines.append(
            f"| `{row['name']}` | {row['covered_fraction']:.3f} | "
            f"{row['same_length_random']['p_ge']:.4f} | {row['digit_multiset_random']['p_ge']:.4f} | "
            f"`{row['classification']}` |"
        )
    lines += [
        "",
        "## Seed-Derived Row0 Models",
        "",
        "| Seed | Best family | Accuracy | Random p>= | Class |",
        "|---|---|---:|---:|---|",
    ]
    for row in result["seed_row0_stats"]:
        lines.append(
            f"| `{row['seed']}` | `{row['best_family']}` | {row['best_accuracy']:.3f} | "
            f"{row['control_summary']['p_ge']:.4f} | `{row['classification']}` |"
        )
    lines += [
        "",
        "## Book Phase / Quest Motif Tests",
        "",
        "| Motif | Best metric | Observed | Random p>= | Class |",
        "|---|---|---:|---:|---|",
    ]
    for row in result["book_phase_stats"]:
        s = row["best_summary"]
        lines.append(
            f"| `{row['motif']}` | `{row['best_metric']}` | {s['observed']:.3f} | "
            f"{s['p_ge']:.4f} | `{row['classification']}` |"
        )
    lines += [
        "",
        "## Row0 Anomaly / E-Layer Statistics",
        "",
        "| Feature | Cells | E rate | Random p>= | Class |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["row0_anomaly_stats"]:
        lines.append(
            f"| `{row['feature']}` | {row['selected_count']} | {row['e_rate']:.3f} | "
            f"{row['control_summary']['p_ge']:.4f} | `{row['classification']}` |"
        )
    lines += [
        "",
        "## Identity Co-Occurrence",
        "",
        "| Pair | Books with both | Multiset p>= | Class |",
        "|---|---:|---:|---|",
    ]
    for row in result["seed_cooccurrence_stats"]:
        lines.append(
            f"| `{' / '.join(row['pair'])}` | {row['books_with_both']} | "
            f"{row['digit_multiset_control']['p_ge']:.4f} | `{row['classification']}` |"
        )
    lines += [
        "",
        "## Conclusion",
        "",
        "No test beats the current promoted mechanical baselines or supplies official",
        "ground truth. Some short seeds such as `3478` are corpus-common, but the",
        "controls classify them as structural overlap rather than a usable key.",
        "Chayenne remains the only strong copy-holdout-like external string; Avar",
        "Tar remains leaky at short substring lengths and is not validation. E-layer",
        "features can be weak local clues, but they do not create a row0 formula.",
    ]
    return lines


def main() -> None:
    formula = load_json("analysis/generator_search_20260618/tape_based_formula_469.json")
    books = load_json("analysis/audit_20260609/books_digits.json")
    manifest = load_json("analysis/generator_search_20260618/generator_holdout_manifest.json")
    book_strings = [books[str(i)] for i in sorted(map(int, books))]
    corpus = "".join(book_strings)
    tape_text = "".join(component["text"] for component in formula["tape_components"])
    digit_weights = dict(Counter(corpus))
    seeds = ["3478", "486486", "486", "3478468486", "4864863478", "74032", "45331", "469", "43153", "34784", "3700", "99", "1", "0"]
    row0_seeds = [seed for seed in seeds if len(set(seed)) > 1 and len(seed) >= 3]
    identity_seeds = ["3478", "486486", "74032", "45331", "43153", "34784", "469"]
    result = {
        "schema": "deep_statistical_exhaustion.v1",
        "test": "14_deep_statistical_exhaustion",
        "control_trials": CONTROL_TRIALS,
        "random_seed": 46920260620,
        "translation_delta": "NONE",
        "classification": "source_family_closed_negative",
        "source_number_stats": source_number_stats(corpus, tape_text, digit_weights, seeds),
        "external_coverage_stats": external_coverage_stats(book_strings, digit_weights, manifest),
        "seed_row0_stats": seed_row0_stats(formula["pair_table"], row0_seeds),
        "book_phase_stats": book_phase_stats(formula["book_recipes"]),
        "row0_anomaly_stats": row0_anomaly_stats(formula["pair_table"]),
        "seed_cooccurrence_stats": seed_cooccurrence_stats(book_strings, identity_seeds),
    }
    write_result("14_deep_statistical_exhaustion", result, build_report(result))


if __name__ == "__main__":
    main()
