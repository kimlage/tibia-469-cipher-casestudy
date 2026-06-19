#!/usr/bin/env python3
"""Joint zero/homophone transition origin probe.

This closes a narrow methodological gap: zero omission, previous-code
homophone selection, and orientation are individually real surface signals, but
do they jointly explain the origin of the 55-cell pair table?

The probe builds pair-level feature vectors from local rendered-code context in
training books only, without using the pair's true symbol as a feature. It then
tests whether those features reconstruct the observed homophone partition or
predict held-out pair labels better than inventory-preserving label shuffles.

Mechanical only. No plaintext, glossary, or semantic meaning is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
HOLDOUT_JSON = HERE / "generator_holdout_manifest.json"

OUT_JSON = HERE / "zero_homophone_transition_origin_probe_results.json"
OUT_MD = HERE / "zero_homophone_transition_origin_probe_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 500
CLUSTER_COUNT = 14


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def pair_key(code: str) -> str:
    return "".join(sorted(code))


def natural_pairs() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict[str, Any], key: str) -> str:
    row = pair_table[key]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def build_books_digits(formula: dict[str, Any]) -> dict[str, str]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    out = {}
    for book, recipe in formula["book_recipes"].items():
        out[str(book)] = "".join(
            modules[item["id"]] if item["type"] == "module" else item["text"]
            for item in recipe
        )
    return out


def token_rows(formula: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    occ = load_json(OCC_STREAMS)["occ"]
    books_digits = build_books_digits(formula)
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            by_book[str(row["book"])].append(
                {
                    "book": str(row["book"]),
                    "pos": int(row["pos"]),
                    "code": row["code"],
                    "pair": pair_key(row["code"]),
                    "symbol": symbol,
                    "novel": bool(row.get("novel", False)),
                    "xuniq": bool(row.get("xuniq", False)),
                }
            )

    aligned = {}
    for book, rows in by_book.items():
        raw = books_digits[book]
        offset = 0
        out = []
        for row in sorted(rows, key=lambda item: item["pos"]):
            code = row["code"]
            if raw.startswith(code, offset):
                raw_text = code
                omitted_zero = False
                start, end = offset, offset + 2
                offset += 2
            elif code.startswith("0") and offset < len(raw) and raw[offset] == code[1]:
                raw_text = code[1]
                omitted_zero = True
                start, end = offset, offset + 1
                offset += 1
            else:
                raise ValueError(f"cannot align book={book} pos={row['pos']} code={code} offset={offset}")
            out.append({**row, "raw_text": raw_text, "raw_start": start, "raw_end": end, "omitted_zero": omitted_zero})
        if offset != len(raw):
            raise ValueError(f"book {book}: consumed {offset}, expected {len(raw)}")
        aligned[book] = out
    return aligned


def holdout_books(formula: dict[str, Any]) -> set[str]:
    if HOLDOUT_JSON.exists():
        return set(load_json(HOLDOUT_JSON)["book_holdouts"])
    books = sorted(formula["book_recipes"], key=numeric_key)
    return {book for idx, book in enumerate(books) if idx % 7 == 0}


def add(counter: Counter[str], key: str, amount: float = 1.0) -> None:
    counter[key] += amount


def collect_pair_features(
    rows_by_book: dict[str, list[dict[str, Any]]],
    train_books: set[str],
    include_mode: str,
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    stats: dict[str, Counter[str]] = {pair: Counter() for pair in natural_pairs()}

    for book in sorted(train_books, key=numeric_key):
        rows = rows_by_book[book]
        for index, row in enumerate(rows):
            if include_mode == "novel_only" and not row["novel"]:
                continue
            if include_mode == "xuniq_only" and not row["xuniq"]:
                continue

            pair = row["pair"]
            code = row["code"]
            prev_row = rows[index - 1] if index > 0 else None
            next_row = rows[index + 1] if index + 1 < len(rows) else None

            add(stats[pair], "count")
            add(stats[pair], f"book_mod7:{int(book) % 7}")
            if row["omitted_zero"]:
                add(stats[pair], "current_zero_omitted")
            if code[0] < code[1]:
                add(stats[pair], "orientation_asc")
            elif code[0] > code[1]:
                add(stats[pair], "orientation_desc")
            else:
                add(stats[pair], "orientation_same")

            if prev_row is None:
                add(stats[pair], "prev_boundary")
            else:
                add(stats[pair], f"prev_pair:{prev_row['pair']}")
                add(stats[pair], f"prev_code:{prev_row['code']}")
                if prev_row["omitted_zero"]:
                    add(stats[pair], "prev_was_zero_omitted")

            if next_row is None:
                add(stats[pair], "next_boundary")
            else:
                add(stats[pair], f"next_pair:{next_row['pair']}")
                add(stats[pair], f"next_code:{next_row['code']}")
                if next_row["omitted_zero"]:
                    add(stats[pair], "causes_next_zero_omission")

    vectors = {}
    nonzero_pairs = 0
    for pair, raw in stats.items():
        count = raw["count"]
        vector: dict[str, float] = {}
        if count:
            nonzero_pairs += 1
            vector["log_count"] = math.log1p(count)
            for key, value in raw.items():
                if key == "count":
                    continue
                if key.startswith(("prev_pair:", "next_pair:", "prev_code:", "next_code:", "book_mod7:")):
                    vector[key] = value / count
                else:
                    vector[key] = value / count
        vectors[pair] = normalize(vector)

    meta = {
        "include_mode": include_mode,
        "train_books": sorted(train_books, key=numeric_key),
        "nonzero_pairs": nonzero_pairs,
        "feature_dimensions": len({key for vector in vectors.values() for key in vector}),
    }
    return vectors, meta


def normalize(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {key: value / norm for key, value in sorted(vector.items())}


def dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def cosine_distance(left: dict[str, float], right: dict[str, float]) -> float:
    return 1.0 - dot(left, right)


def average_vectors(vectors: list[dict[str, float]]) -> dict[str, float]:
    total = Counter()
    for vector in vectors:
        total.update(vector)
    if not vectors:
        return {}
    return normalize({key: value / len(vectors) for key, value in total.items()})


def agglomerative_clusters(vectors: dict[str, dict[str, float]], k: int) -> dict[str, int]:
    clusters = {idx: [pair] for idx, pair in enumerate(sorted(vectors))}
    centroids = {idx: vectors[pairs[0]] for idx, pairs in clusters.items()}
    next_id = len(clusters)
    while len(clusters) > k:
        ids = sorted(clusters)
        best = None
        for left_index, left in enumerate(ids):
            for right in ids[left_index + 1 :]:
                distance = cosine_distance(centroids[left], centroids[right])
                size_penalty = 0.002 * (len(clusters[left]) + len(clusters[right]))
                row = (distance + size_penalty, distance, left, right)
                if best is None or row < best:
                    best = row
        if best is None:
            break
        _, _, left, right = best
        merged = clusters.pop(left) + clusters.pop(right)
        centroids.pop(left)
        centroids.pop(right)
        clusters[next_id] = sorted(merged)
        centroids[next_id] = average_vectors([vectors[pair] for pair in merged])
        next_id += 1

    assignment = {}
    for cluster_idx, pairs in enumerate(sorted(clusters.values(), key=lambda items: (len(items), items[0]))):
        for pair in pairs:
            assignment[pair] = cluster_idx
    return assignment


def pair_link_scores(predicted: dict[str, int], labels: dict[str, str]) -> dict[str, float]:
    pairs = sorted(labels)
    tp = fp = fn = tn = 0
    for i, left in enumerate(pairs):
        for right in pairs[i + 1 :]:
            same_pred = predicted[left] == predicted[right]
            same_true = labels[left] == labels[right]
            if same_pred and same_true:
                tp += 1
            elif same_pred:
                fp += 1
            elif same_true:
                fn += 1
            else:
                tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1}


def nearest_centroid_leave_one_out(vectors: dict[str, dict[str, float]], labels: dict[str, str]) -> dict[str, Any]:
    sums: dict[str, Counter[str]] = defaultdict(Counter)
    counts = Counter(labels.values())
    for pair, label in labels.items():
        sums[label].update(vectors[pair])

    predictions = {}
    for held_pair in sorted(labels):
        centroids = {}
        held_label = labels[held_pair]
        for symbol in sorted(counts):
            count = counts[symbol] - (1 if symbol == held_label else 0)
            if count <= 0:
                continue
            raw = Counter(sums[symbol])
            if symbol == held_label:
                for key, value in vectors[held_pair].items():
                    raw[key] -= value
            centroids[symbol] = normalize({key: value / count for key, value in raw.items() if value})
        if not centroids:
            predictions[held_pair] = {"predicted": None, "distance": None}
            continue
        best_symbol, best_distance = min(
            ((symbol, cosine_distance(vectors[held_pair], centroid)) for symbol, centroid in centroids.items()),
            key=lambda item: (item[1], item[0]),
        )
        predictions[held_pair] = {"predicted": best_symbol, "distance": best_distance}
    correct = sum(1 for pair, row in predictions.items() if row["predicted"] == labels[pair])
    return {"accuracy": correct / len(labels), "correct": correct, "total": len(labels), "predictions": predictions}


def shuffled_labels(labels: dict[str, str], rng: random.Random) -> dict[str, str]:
    pairs = sorted(labels)
    values = [labels[pair] for pair in pairs]
    rng.shuffle(values)
    return dict(zip(pairs, values))


def summarize(values: list[float], observed: float, higher_is_better: bool = True) -> dict[str, float]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if higher_is_better:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {"observed": observed, "mean": mean, "sd": sd, "min": min(values), "max": max(values), "p": p, "z": z}


def evaluate_variant(vectors: dict[str, dict[str, float]], labels: dict[str, str], meta: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + hash(meta["include_mode"]) % 1000)
    clusters = agglomerative_clusters(vectors, CLUSTER_COUNT)
    cluster_scores = pair_link_scores(clusters, labels)
    centroid = nearest_centroid_leave_one_out(vectors, labels)

    cluster_controls = []
    centroid_controls = []
    for _ in range(CONTROL_TRIALS):
        ctrl_labels = shuffled_labels(labels, rng)
        cluster_controls.append(pair_link_scores(clusters, ctrl_labels)["f1"])
        centroid_controls.append(nearest_centroid_leave_one_out(vectors, ctrl_labels)["accuracy"])

    special_pairs = ["19", "39", "33", "66", "06", "09", "16", "36", "68", "89"]
    special = {}
    for pair in special_pairs:
        if pair in labels:
            special[pair] = {
                "true_label": labels[pair],
                "cluster": clusters[pair],
                "centroid_prediction": centroid["predictions"][pair],
            }

    return {
        "include_mode": meta["include_mode"],
        "meta": meta,
        "cluster_count": CLUSTER_COUNT,
        "cluster_pair_link": cluster_scores,
        "centroid_leave_one_pair_out": {
            key: value for key, value in centroid.items() if key != "predictions"
        },
        "controls": {
            "label_shuffle_preserving_inventory": {
                "cluster_f1": summarize(cluster_controls, cluster_scores["f1"], True),
                "centroid_accuracy": summarize(centroid_controls, centroid["accuracy"], True),
            }
        },
        "special_pairs": special,
        "sample_centroid_predictions": {
            pair: centroid["predictions"][pair] for pair in sorted(labels)[:20]
        },
    }


def verdict(variants: list[dict[str, Any]]) -> str:
    best_centroid = max(variants, key=lambda row: row["centroid_leave_one_pair_out"]["accuracy"])
    best_cluster = max(variants, key=lambda row: row["cluster_pair_link"]["f1"])
    centroid_p = best_centroid["controls"]["label_shuffle_preserving_inventory"]["centroid_accuracy"]["p"]
    cluster_p = best_cluster["controls"]["label_shuffle_preserving_inventory"]["cluster_f1"]["p"]
    centroid_acc = best_centroid["centroid_leave_one_pair_out"]["accuracy"]
    if centroid_acc >= 0.45 and centroid_p <= 0.01 and cluster_p <= 0.05:
        return "candidate_context_origin_signal"
    if centroid_p <= 0.05 or cluster_p <= 0.05:
        return "weak_context_signal_not_matrix_formula"
    return "rejected_context_origin_probe"


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# Zero/Homophone Transition Origin Probe",
        "",
        "Generated by `zero_homophone_transition_origin_probe.py`.",
        "",
        "This pass tests whether local rendering context, zero omission, and",
        "prev/next code transitions can reconstruct the 55-cell homophone",
        "partition. It does not use the true symbol as an input feature and",
        "does not promote plaintext.",
        "",
        "## Summary",
        "",
        "| Include mode | Nonzero pairs | Features | Cluster F1 | Cluster p | Centroid acc | Centroid p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["variants"]:
        ctrl = row["controls"]["label_shuffle_preserving_inventory"]
        lines.append(
            f"| `{row['include_mode']}` | {row['meta']['nonzero_pairs']} | {row['meta']['feature_dimensions']} | {row['cluster_pair_link']['f1']:.3f} | {ctrl['cluster_f1']['p']:.5f} | {row['centroid_leave_one_pair_out']['accuracy']:.3f} | {ctrl['centroid_accuracy']['p']:.5f} |"
        )
    lines += [
        "",
        f"Verdict: `{result['verdict']}`.",
        "",
        "## Special Pair Diagnostics",
        "",
        "| Mode | Pair | True label | Cluster | Centroid prediction | Distance |",
        "|---|---|---|---:|---|---:|",
    ]
    for row in result["variants"]:
        for pair, info in row["special_pairs"].items():
            pred = info["centroid_prediction"]
            distance = pred["distance"]
            distance_text = "" if distance is None else f"{distance:.3f}"
            lines.append(
                f"| `{row['include_mode']}` | `{pair}` | `{info['true_label']}` | {info['cluster']} | `{pred['predicted']}` | {distance_text} |"
            )
    lines += [
        "",
        "## Interpretation",
        "",
        "The probe is a closure test for a tempting explanation: maybe the pair",
        "table was chosen to create local render transitions. To change the",
        "matrix-origin verdict, the context-only features would need to predict",
        "held-out pair labels and recover same-symbol links better than",
        "inventory-preserving shuffles. Failing that, zero omission and",
        "prev-code homophone selection remain surface/rendering layers.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    rows_by_book = token_rows(formula)
    holdouts = holdout_books(formula)
    all_books = set(rows_by_book)
    train_books = all_books - holdouts
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in natural_pairs()}

    variants = []
    for include_mode in ["all_occurrences", "novel_only", "xuniq_only"]:
        vectors, meta = collect_pair_features(rows_by_book, train_books, include_mode)
        variants.append(evaluate_variant(vectors, labels, meta))

    result = {
        "schema": "zero_homophone_transition_origin_probe_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "occ_streams": str(OCC_STREAMS.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "book_holdouts": sorted(holdouts, key=numeric_key),
        "variants": variants,
        "verdict": verdict(variants),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    best = max(variants, key=lambda row: row["centroid_leave_one_pair_out"]["accuracy"])
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={result['verdict']} best_centroid={best['include_mode']} acc={best['centroid_leave_one_pair_out']['accuracy']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
