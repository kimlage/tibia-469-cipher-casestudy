#!/usr/bin/env python3
"""Context-only partition search for 469 homophone pair cells.

This is a focused follow-up to `pair_context_cluster_search.py`. Instead of
asking whether the observed same-symbol classes are context-compact, it asks a
harder question: can raw code-neighbourhood distances reconstruct any of the
observed homophone partition without seeing symbol labels?

The search is deliberately mechanical:

- target cluster sizes come from the observed homophone inventory only;
- clusters are built from pair-window context distances only;
- evaluation is label-free using pair co-clustering F1 and adjusted Rand index;
- controls compare against random partitions with the same cluster-size vector.

No plaintext or glossary is produced.
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.metrics import adjusted_rand_score


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import pair_context_cluster_search as context_search  # noqa: E402


OUT_JSON = HERE / "pair_context_partition_results.json"
OUT_MD = HERE / "pair_context_partition_report.md"

RANDOM_SEED = 46920260624
CONTROL_TRIALS = 20000


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def labels_to_ids(labels: list[str]) -> list[int]:
    mapping = {}
    out = []
    for label in labels:
        if label not in mapping:
            mapping[label] = len(mapping)
        out.append(mapping[label])
    return out


def pairwise_f1(true_ids: list[int], pred_ids: list[int]) -> dict:
    tp = fp = fn = 0
    for left in range(len(true_ids)):
        for right in range(left + 1, len(true_ids)):
            truth = true_ids[left] == true_ids[right]
            pred = pred_ids[left] == pred_ids[right]
            tp += int(truth and pred)
            fp += int((not truth) and pred)
            fn += int(truth and (not pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive_links": tp,
        "false_positive_links": fp,
        "false_negative_links": fn,
    }


def average_distance(cluster: list[int], matrix: list[list[float]]) -> float:
    if len(cluster) < 2:
        return 0.0
    total = 0.0
    count = 0
    for pos, left in enumerate(cluster):
        for right in cluster[pos + 1 :]:
            total += matrix[left][right]
            count += 1
    return total / count


def grow_cluster(remaining: set[int], size: int, matrix: list[list[float]], counts: list[int], mode: str) -> list[int]:
    best = None
    for seed in sorted(remaining):
        cluster = [seed]
        available = set(remaining)
        available.remove(seed)
        while len(cluster) < size:
            if mode == "average":
                key = lambda item: (sum(matrix[item][member] for member in cluster) / len(cluster), item)
            elif mode == "minimum":
                key = lambda item: (min(matrix[item][member] for member in cluster), item)
            elif mode == "weighted":
                key = lambda item: (
                    sum(matrix[item][member] * math.sqrt(counts[item] * counts[member]) for member in cluster)
                    / len(cluster),
                    item,
                )
            else:
                raise ValueError(mode)
            item = min(available, key=key)
            cluster.append(item)
            available.remove(item)
        score = average_distance(cluster, matrix)
        score_key = (score, sum(counts[index] for index in cluster), tuple(cluster))
        if best is None or score_key < best[0]:
            best = (score_key, cluster)
    return best[1]


def contextual_partition(sizes: list[int], matrix: list[list[float]], counts: list[int], size_order: str, mode: str) -> list[int]:
    ordered_sizes = sizes[:] if size_order == "desc" else list(reversed(sizes))
    remaining = set(range(len(matrix)))
    clusters = []
    for size in ordered_sizes:
        if size == 1:
            # Singletons carry no within-cluster distance. Put high-use cells
            # into singletons last/first deterministically based on the chosen
            # size order without consulting labels.
            cluster = [max(remaining, key=lambda index: (counts[index], -index))]
        else:
            cluster = grow_cluster(remaining, size, matrix, counts, mode)
        clusters.append(cluster)
        remaining -= set(cluster)
    pred = [-1] * len(matrix)
    for cluster_id, cluster in enumerate(clusters):
        for index in cluster:
            pred[index] = cluster_id
    return pred


def random_partition_from_sizes(sizes: list[int], rng: random.Random) -> list[int]:
    labels = []
    for cluster_id, size in enumerate(sizes):
        labels.extend([cluster_id] * size)
    rng.shuffle(labels)
    return labels


def score_partition(true_ids: list[int], pred_ids: list[int]) -> dict:
    return {
        "adjusted_rand": adjusted_rand_score(true_ids, pred_ids),
        **pairwise_f1(true_ids, pred_ids),
    }


def summarize(values: list[float], observed: float) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
    z = (observed - mean) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def cluster_table(pairs: list[str], true_labels: list[str], pred_ids: list[int]) -> list[dict]:
    by_cluster: dict[int, list[int]] = defaultdict(list)
    for index, cluster_id in enumerate(pred_ids):
        by_cluster[cluster_id].append(index)
    rows = []
    for cluster_id, indices in sorted(by_cluster.items()):
        symbol_counts = Counter(true_labels[index] for index in indices)
        rows.append(
            {
                "cluster_id": cluster_id,
                "size": len(indices),
                "pairs": [pairs[index] for index in indices],
                "observed_symbols": dict(sorted(symbol_counts.items())),
                "majority_symbol": symbol_counts.most_common(1)[0][0],
                "majority_count": symbol_counts.most_common(1)[0][1],
            }
        )
    rows.sort(key=lambda row: (-row["size"], row["cluster_id"]))
    return rows


def write_report(result: dict) -> None:
    lines = [
        "# Pair Context Partition Search",
        "",
        "Generated by `pair_context_partition_search.py`.",
        "",
        "This pass asks whether pair-window context distances can reconstruct",
        "the observed homophone partition without seeing symbol labels. It does",
        "not translate 469.",
        "",
        "## Algorithms",
        "",
        "| Algorithm | ARI | Pair F1 | TP links | Control p | Bonferroni p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["algorithm_rows"]:
        lines.append(
            f"| `{row['algorithm_id']}` | {row['adjusted_rand']:.4f} | {row['f1']:.4f} | "
            f"{row['true_positive_links']} | {row['control']['f1']['p_good_direction']:.5f} | "
            f"{row['bonferroni_p']:.5f} | `{row['verdict']}` |"
        )
    best = result["best"]
    lines += [
        "",
        "## Best Partition",
        "",
        f"Best algorithm: `{best['algorithm_id']}`.",
        "",
        "| Cluster | Size | Majority observed symbol | Pairs | Observed symbols |",
        "|---:|---:|---|---|---|",
    ]
    for row in result["best_clusters"]:
        lines.append(
            f"| {row['cluster_id']} | {row['size']} | `{row['majority_symbol']}` "
            f"({row['majority_count']}/{row['size']}) | `{', '.join(row['pairs'])}` | "
            f"`{row['observed_symbols']}` |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_context_partition":
        lines.append(
            "Context-only clustering recovers the homophone partition beyond the "
            "strict corrected gate. This is still mechanical and does not imply plaintext."
        )
    elif result["verdict"] == "not_promoted_context_partition_hint":
        lines.append(
            "Context-only clustering recovers more same-symbol links than random "
            "partitions, but not enough for strict promotion after algorithm/method "
            "correction. Treat as a weak mechanical hint."
        )
    else:
        lines.append(
            "Context-only clustering does not recover the homophone partition better "
            "than size-preserving random partitions."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = context_search.load_json(context_search.FORMULA_JSON)
    pairs = context_search.all_pairs()
    labels = [context_search.primary_pair_symbol(formula["pair_table"], pair) for pair in pairs]
    true_ids = labels_to_ids(labels)
    sizes = sorted(Counter(labels).values(), reverse=True)
    contexts, counts_by_pair = context_search.build_context_counters(pairs)
    matrix = context_search.distance_matrices(pairs, contexts)["pair_window"]
    counts = [counts_by_pair[pair] for pair in pairs]

    algorithm_specs = [
        ("desc_average", "desc", "average"),
        ("desc_minimum", "desc", "minimum"),
        ("desc_weighted", "desc", "weighted"),
        ("asc_average", "asc", "average"),
        ("asc_minimum", "asc", "minimum"),
        ("asc_weighted", "asc", "weighted"),
    ]

    rng = random.Random(RANDOM_SEED)
    random_scores = []
    for _trial in range(CONTROL_TRIALS):
        pred = random_partition_from_sizes(sizes, rng)
        random_scores.append(score_partition(true_ids, pred))

    rows = []
    for algorithm_id, size_order, mode in algorithm_specs:
        pred = contextual_partition(sizes, matrix, counts, size_order=size_order, mode=mode)
        scored = score_partition(true_ids, pred)
        ari_control = summarize([row["adjusted_rand"] for row in random_scores], scored["adjusted_rand"])
        f1_control = summarize([row["f1"] for row in random_scores], scored["f1"])
        row = {
            "algorithm_id": algorithm_id,
            "size_order": size_order,
            "mode": mode,
            **scored,
            "control": {"adjusted_rand": ari_control, "f1": f1_control},
            "predicted_ids": pred,
        }
        row["bonferroni_p"] = min(1.0, min(ari_control["p_good_direction"], f1_control["p_good_direction"]) * len(algorithm_specs) * 2)
        if row["bonferroni_p"] <= 0.01:
            row["verdict"] = "candidate"
        elif row["bonferroni_p"] <= 0.05:
            row["verdict"] = "not_promoted_hint"
        else:
            row["verdict"] = "rejected_control"
        rows.append(row)
    rows.sort(key=lambda row: (row["bonferroni_p"], -row["f1"]))
    best = rows[0]
    if best["bonferroni_p"] <= 0.01:
        verdict = "candidate_context_partition"
    elif best["bonferroni_p"] <= 0.05:
        verdict = "not_promoted_context_partition_hint"
    else:
        verdict = "rejected_control"

    public_rows = []
    for row in rows:
        clean = {key: value for key, value in row.items() if key != "predicted_ids"}
        public_rows.append(clean)

    result = {
        "schema": "pair_context_partition_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "cluster_sizes": sizes,
        "pair_count": len(pairs),
        "true_same_pair_links": sum(1 for left in range(len(true_ids)) for right in range(left + 1, len(true_ids)) if true_ids[left] == true_ids[right]),
        "algorithm_rows": public_rows,
        "best": {key: value for key, value in best.items() if key != "predicted_ids"},
        "best_clusters": cluster_table(pairs, labels, best["predicted_ids"]),
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best={best['algorithm_id']} "
        f"f1={best['f1']:.4f} ari={best['adjusted_rand']:.4f} "
        f"p={best['control']['f1']['p_good_direction']:.5f} "
        f"bonferroni={best['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
