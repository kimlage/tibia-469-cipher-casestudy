#!/usr/bin/env python3
"""Explain the residual after deterministic homophone apportionment.

The deterministic apportionment pass gets close to the observed extra-slot
inventory but misses by L1=12. This script asks whether that remaining
six-slot transfer can be explained by a small mechanical bias over already
frozen corpus features.

The correction family is deliberately constrained:

- compute symbol-level features from corpus usage, module/literal placement,
  zero rendering, and apportionment quota remainders;
- generate small balanced corrections: add one slot to the top/bottom k symbols
  by a feature and remove one slot from the opposite side;
- optionally compose two such corrections;
- compare the best residual fit to shuffled residual controls.

Mechanical only. No plaintext or glossary is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
APPORTIONMENT_JSON = HERE / "deterministic_apportionment_inventory_results.json"

OUT_JSON = HERE / "inventory_residual_explainer_results.json"
OUT_MD = HERE / "inventory_residual_explainer_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260621
CONTROL_TRIALS = 50000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    out = 0.0
    for count in counter.values():
        if count:
            p = count / total
            out -= p * math.log2(p)
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if not dx or not dy:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def reconstruct_books(formula: dict) -> tuple[dict[str, str], dict[str, list[dict]]]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    books = {}
    segments = {}
    for book, recipe in formula["book_recipes"].items():
        offset = 0
        raw_parts = []
        book_segments = []
        for item in recipe:
            if item["type"] == "module":
                text = modules[item["id"]]
                segment = {"start": offset, "end": offset + len(text), "type": "module", "id": item["id"]}
            else:
                text = item["text"]
                segment = {"start": offset, "end": offset + len(text), "type": "literal", "id": None}
            raw_parts.append(text)
            book_segments.append(segment)
            offset += len(text)
        books[book] = "".join(raw_parts)
        segments[book] = book_segments
    return books, segments


def load_token_maps(formula: dict, books: dict[str, str]) -> dict[str, list[dict]]:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[dict]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            by_book[str(row["book"])].append(
                {
                    "book": str(row["book"]),
                    "code_pos": int(row["pos"]),
                    "symbol": symbol,
                    "code": row["code"],
                }
            )

    token_maps = {}
    for book, rows in by_book.items():
        rows = sorted(rows, key=lambda item: item["code_pos"])
        raw = books[book]
        offset = 0
        out = []
        for item in rows:
            code = item["code"]
            if raw.startswith(code, offset):
                raw_text, start, end, omitted = code, offset, offset + 2, False
                offset += 2
            elif code.startswith("0") and offset < len(raw) and raw[offset] == code[1]:
                raw_text, start, end, omitted = code[1], offset, offset + 1, True
                offset += 1
            else:
                raise ValueError(f"cannot align book={book} code={code} offset={offset}")
            out.append({**item, "raw_text": raw_text, "raw_start": start, "raw_end": end, "omitted_zero": omitted})
        if offset != len(raw):
            raise ValueError(f"book {book}: consumed {offset}, expected {len(raw)}")
        token_maps[book] = out
    return token_maps


def segment_type_at(segments: list[dict], pos: int) -> str:
    for segment in segments:
        if segment["start"] <= pos < segment["end"]:
            return segment["type"]
    raise ValueError(pos)


def symbol_features(formula: dict, apportionment: dict) -> dict[str, dict[str, float]]:
    books, segments = reconstruct_books(formula)
    token_maps = load_token_maps(formula, books)
    book_order = {book: idx for idx, book in enumerate(sorted(books, key=numeric_key))}
    cumulative = {}
    running = 0
    for book in sorted(books, key=numeric_key):
        cumulative[book] = running
        running += len(books[book])

    totals = Counter()
    module_counts = Counter()
    literal_counts = Counter()
    zero_code_counts = Counter()
    omitted_zero_counts = Counter()
    code_counters: dict[str, Counter[str]] = defaultdict(Counter)
    book_sets: dict[str, set[str]] = defaultdict(set)
    global_positions: dict[str, list[int]] = defaultdict(list)
    raw_lengths = Counter()

    for book, toks in token_maps.items():
        for tok in toks:
            symbol = tok["symbol"]
            totals[symbol] += 1
            if segment_type_at(segments[book], tok["raw_start"]) == "module":
                module_counts[symbol] += 1
            else:
                literal_counts[symbol] += 1
            if "0" in tok["code"]:
                zero_code_counts[symbol] += 1
            if tok["omitted_zero"]:
                omitted_zero_counts[symbol] += 1
            code_counters[symbol][tok["code"]] += 1
            book_sets[symbol].add(book)
            global_positions[symbol].append(cumulative[book] + tok["raw_start"])
            raw_lengths[symbol] += len(tok["raw_text"])

    best = apportionment["best"]
    observed = apportionment["observed_extra_counts"]
    predicted = best["prediction"]
    total_corpus = sum(totals.values())
    total_raw = sum(len(text) for text in books.values())
    features = {}
    for symbol in SIGMA:
        total = totals[symbol]
        expected_extra = 41 * total / total_corpus
        floor_extra = math.floor(expected_extra)
        code_counter = code_counters[symbol]
        top_count = code_counter.most_common(1)[0][1] if code_counter else 0
        positions = global_positions[symbol]
        features[symbol] = {
            "corpus_count": total,
            "corpus_share": total / total_corpus,
            "expected_extra": expected_extra,
            "quota_remainder": expected_extra - floor_extra,
            "base_predicted_extra": predicted[symbol],
            "observed_extra": observed[symbol],
            "residual": observed[symbol] - predicted[symbol],
            "module_fraction": module_counts[symbol] / total if total else 0.0,
            "literal_fraction": literal_counts[symbol] / total if total else 0.0,
            "book_presence_fraction": len(book_sets[symbol]) / len(books),
            "first_global_position_fraction": min(positions) / total_raw if positions else 1.0,
            "mean_global_position_fraction": (sum(positions) / len(positions)) / total_raw if positions else 1.0,
            "zero_code_fraction": zero_code_counts[symbol] / total if total else 0.0,
            "omitted_zero_fraction": omitted_zero_counts[symbol] / total if total else 0.0,
            "mean_raw_digits_per_token": raw_lengths[symbol] / total if total else 0.0,
            "code_entropy": entropy(code_counter),
            "top_code_share": top_count / total if total else 0.0,
            "book_entropy": entropy(Counter(book for book in book_sets[symbol])),
            "book_presence_count": len(book_sets[symbol]),
        }
    return features


def l1_residual(residual: dict[str, int], correction: dict[str, int]) -> int:
    return sum(abs(residual[symbol] - correction.get(symbol, 0)) for symbol in SIGMA)


def make_single_corrections(features: dict[str, dict[str, float]], base_prediction: dict[str, int]) -> list[dict]:
    feature_names = [
        "quota_remainder",
        "module_fraction",
        "literal_fraction",
        "book_presence_fraction",
        "first_global_position_fraction",
        "mean_global_position_fraction",
        "zero_code_fraction",
        "omitted_zero_fraction",
        "mean_raw_digits_per_token",
        "code_entropy",
        "top_code_share",
        "corpus_share",
    ]
    corrections = []
    for feature in feature_names:
        values = {symbol: features[symbol][feature] for symbol in SIGMA}
        for high_receives in [True, False]:
            ordered = sorted(SIGMA, key=lambda symbol: (values[symbol], symbol))
            receivers_order = list(reversed(ordered)) if high_receives else ordered
            donors_order = ordered if high_receives else list(reversed(ordered))
            for k in range(1, 7):
                receivers = receivers_order[:k]
                donors = donors_order[:k]
                if set(receivers) & set(donors):
                    continue
                correction = {symbol: 0 for symbol in SIGMA}
                valid = True
                for symbol in receivers:
                    correction[symbol] += 1
                for symbol in donors:
                    correction[symbol] -= 1
                    if base_prediction[symbol] + correction[symbol] < 0:
                        valid = False
                if not valid:
                    continue
                corrections.append(
                    {
                        "kind": "single_feature_transfer",
                        "features": [feature],
                        "high_receives": high_receives,
                        "k": k,
                        "correction": correction,
                        "description": (
                            f"{'high' if high_receives else 'low'} `{feature}` receives one slot from "
                            f"{'low' if high_receives else 'high'} `{feature}`, k={k}"
                        ),
                    }
                )
    return corrections


def combine_corrections(singles: list[dict], base_prediction: dict[str, int]) -> list[dict]:
    out = list(singles)
    seen = {tuple(item["correction"][symbol] for symbol in SIGMA) for item in out}
    for idx, left in enumerate(singles):
        if left["k"] > 3:
            continue
        for right in singles[idx + 1 :]:
            if right["k"] > 3:
                continue
            correction = {symbol: left["correction"][symbol] + right["correction"][symbol] for symbol in SIGMA}
            if any(base_prediction[symbol] + correction[symbol] < 0 for symbol in SIGMA):
                continue
            key = tuple(correction[symbol] for symbol in SIGMA)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "kind": "two_feature_transfer",
                    "features": left["features"] + right["features"],
                    "k": left["k"] + right["k"],
                    "correction": correction,
                    "description": left["description"] + " + " + right["description"],
                }
            )
    out.append({"kind": "null", "features": [], "k": 0, "correction": {symbol: 0 for symbol in SIGMA}, "description": "no correction"})
    return out


def score_corrections(corrections: list[dict], residual: dict[str, int], base_prediction: dict[str, int]) -> list[dict]:
    rows = []
    baseline_l1 = l1_residual(residual, {symbol: 0 for symbol in SIGMA})
    for item in corrections:
        correction = item["correction"]
        current_l1 = l1_residual(residual, correction)
        corrected_prediction = {symbol: base_prediction[symbol] + correction[symbol] for symbol in SIGMA}
        rows.append(
            {
                "kind": item["kind"],
                "features": item["features"],
                "k": item["k"],
                "description": item["description"],
                "correction": correction,
                "corrected_prediction": corrected_prediction,
                "l1": current_l1,
                "gain_vs_null": baseline_l1 - current_l1,
                "exact_residual_symbols": sum(residual[symbol] == correction[symbol] for symbol in SIGMA),
            }
        )
    rows.sort(key=lambda row: (row["l1"], -row["gain_vs_null"], row["kind"], row["description"]))
    return rows


def summarize(values: list[float], observed: float, low_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if low_is_good:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
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


def controls(corrections: list[dict], residual: dict[str, int]) -> dict:
    rng = random.Random(RANDOM_SEED)
    residual_values = [residual[symbol] for symbol in SIGMA]
    best_l1_values = []
    best_gain_values = []
    exact_symbol_values = []
    baseline_l1 = sum(abs(value) for value in residual_values)
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(residual_values)
        shuffled = {symbol: residual_values[idx] for idx, symbol in enumerate(SIGMA)}
        rows = score_corrections(corrections, shuffled, {symbol: 100 for symbol in SIGMA})
        best = rows[0]
        best_l1_values.append(best["l1"])
        best_gain_values.append(baseline_l1 - best["l1"])
        exact_symbol_values.append(best["exact_residual_symbols"])
    return {
        "best_l1": best_l1_values,
        "gain_vs_null": best_gain_values,
        "exact_residual_symbols": exact_symbol_values,
    }


def verdict(best: dict, l1_summary: dict, gain_summary: dict) -> str:
    if best["l1"] == 0 and l1_summary["p_good_direction"] <= 0.01:
        return "candidate_generator_residual_rule"
    if best["l1"] <= 4 and gain_summary["p_good_direction"] <= 0.05:
        return "weak_candidate_residual_rule"
    if best["gain_vs_null"] > 0 and gain_summary["p_good_direction"] <= 0.05:
        return "secondary_support_not_exact"
    return "rejected_control"


def write_report(result: dict) -> None:
    best = result["best"]
    lines = [
        "# Inventory Residual Explainer",
        "",
        "Generated by `inventory_residual_explainer.py`.",
        "",
        "This pass tests whether the L1=12 residual left by deterministic",
        "apportionment can be explained by a small corpus/mechanical bias.",
        "",
        "## Best Correction",
        "",
        "| Kind | L1 | Gain | Exact residual symbols | Features | Control p(gain) | Verdict |",
        "|---|---:|---:|---:|---|---:|---|",
        (
            f"| `{best['kind']}` | {best['l1']} | {best['gain_vs_null']} | "
            f"{best['exact_residual_symbols']}/14 | {', '.join('`'+f+'`' for f in best['features']) or '`none`'} | "
            f"{result['controls']['gain_vs_null']['p_good_direction']:.5f} | `{result['verdict']}` |"
        ),
        "",
        best["description"],
        "",
        "Correction vector:",
        "",
        "```json",
        json.dumps(best["correction"], indent=2, sort_keys=True),
        "```",
        "",
        "## Feature/Residual Table",
        "",
        "| Symbol | Observed extra | Base pred | Residual | Module frac | Zero-code frac | Quota remainder |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, row in result["feature_table"].items():
        lines.append(
            f"| `{symbol}` | {row['observed_extra']} | {row['base_predicted_extra']} | {row['residual']} | "
            f"{row['module_fraction']:.3f} | {row['zero_code_fraction']:.3f} | {row['quota_remainder']:.3f} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
    ]
    if result["verdict"] == "rejected_control":
        lines += [
            "The best small correction does not beat shuffled-residual controls enough",
            "to explain the remaining inventory error. The frequency-weighted",
            "inventory remains useful, but the residual still looks like manual",
            "choice, unmodeled randomness, or a rule not covered by these features.",
            "",
        ]
    else:
        lines += [
            "A small correction beats shuffled-residual controls. Treat this as a",
            "mechanical generator clue only; it is not a plaintext mapping.",
            "",
        ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    apportionment = load_json(APPORTIONMENT_JSON)
    features = symbol_features(formula, apportionment)
    residual = {symbol: int(features[symbol]["residual"]) for symbol in SIGMA}
    base_prediction = {symbol: int(features[symbol]["base_predicted_extra"]) for symbol in SIGMA}
    singles = make_single_corrections(features, base_prediction)
    corrections = combine_corrections(singles, base_prediction)
    rows = score_corrections(corrections, residual, base_prediction)
    best = rows[0]
    ctrl = controls(corrections, residual)
    baseline_l1 = sum(abs(value) for value in residual.values())
    l1_summary = summarize(ctrl["best_l1"], best["l1"], low_is_good=True)
    gain_summary = summarize(ctrl["gain_vs_null"], best["gain_vs_null"], low_is_good=False)
    exact_summary = summarize(ctrl["exact_residual_symbols"], best["exact_residual_symbols"], low_is_good=False)
    result = {
        "schema": "inventory_residual_explainer_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "baseline_residual_l1": baseline_l1,
        "candidate_count": len(corrections),
        "single_candidate_count": len(singles),
        "feature_table": features,
        "best": best,
        "top_rows": rows[:50],
        "controls": {
            "best_l1": l1_summary,
            "gain_vs_null": gain_summary,
            "exact_residual_symbols": exact_summary,
        },
        "residual_vs_features_pearson": {
            feature: pearson([features[symbol]["residual"] for symbol in SIGMA], [features[symbol][feature] for symbol in SIGMA])
            for feature in [
                "quota_remainder",
                "module_fraction",
                "literal_fraction",
                "book_presence_fraction",
                "first_global_position_fraction",
                "mean_global_position_fraction",
                "zero_code_fraction",
                "omitted_zero_fraction",
                "mean_raw_digits_per_token",
                "code_entropy",
                "top_code_share",
                "corpus_share",
            ]
        },
        "verdict": verdict(best, l1_summary, gain_summary),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={result['verdict']} best_l1={best['l1']} gain={best['gain_vs_null']} "
        f"p_gain={gain_summary['p_good_direction']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
