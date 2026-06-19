#!/usr/bin/env python3
"""Per-symbol predicate/DNF search for the 469 pair table.

Several earlier passes tested global decision lists, block covers, graph
motifs, and coordinate formulas. This pass asks a slightly different question:

    does any individual symbol have a short human-readable predicate formula,
    and can those per-symbol formulas combine into a compact table generator?

The search deliberately excludes exact pair predicates. It allows only reusable
digit, line, modular, geometry, and lore-shaped sets, then tries single
predicates or small OR rules per symbol. The resulting rule set is scored as a
mechanical model against the 55-cell lookup and against inventory-preserving
label shuffles.

No plaintext, glossary entry, or number<->word mapping is produced.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "symbol_predicate_dnf_results.json"
OUT_MD = HERE / "symbol_predicate_dnf_report.md"

SIGMA = tuple("*ABCEFILNORSTV")
PAIR_COUNT = 55
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 300
TOP_PREDICATES_PER_SYMBOL = 48
MAX_RULE_TERMS = 2

LORE_SETS = {
    "digits_469": {4, 6, 9},
    "digits_3478": {3, 4, 7, 8},
    "digits_43153": {1, 3, 4, 5},
    "digits_34784": {3, 4, 7, 8},
    "digits_74032": {0, 2, 3, 4, 7},
    "digits_45331": {1, 3, 4, 5},
    "digits_19": {1, 9},
    "digits_39": {3, 9},
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_pairs() -> list[str]:
    return [f"{left}{right}" for left in range(10) for right in range(left, 10)]


PAIRS = all_pairs()


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def pair_features(pair: str) -> dict:
    a, b = int(pair[0]), int(pair[1])
    return {
        "a": a,
        "b": b,
        "sum": a + b,
        "diff": b - a,
        "prod": a * b,
        "min": a,
        "max": b,
        "diag": a == b,
        "edge": a in {0, 9} or b in {0, 9},
        "center": a in {4, 5} or b in {4, 5},
        "contains_0": a == 0 or b == 0,
        "contains_1": a == 1 or b == 1,
        "contains_3": a == 3 or b == 3,
        "contains_4": a == 4 or b == 4,
        "contains_6": a == 6 or b == 6,
        "contains_9": a == 9 or b == 9,
        "contains_6_or_9": a in {6, 9} or b in {6, 9},
        "both_6_9_class": a in {6, 9} and b in {6, 9},
        "cross_69": pair == "69",
        "same_parity": (a % 2) == (b % 2),
        "both_prime": a in {2, 3, 5, 7} and b in {2, 3, 5, 7},
        "both_square": a in {0, 1, 4, 9} and b in {0, 1, 4, 9},
        "row": a,
        "col": b,
        "anti_sum": a + b,
        "diag_diff": b - a,
    }


def mask_for(fn) -> int:
    mask = 0
    for idx, pair in enumerate(PAIRS):
        if fn(pair_features(pair)):
            mask |= 1 << idx
    return mask


def popcount(mask: int) -> int:
    return mask.bit_count()


def predicate_library() -> list[dict]:
    rows: list[dict] = []

    def add(name: str, family: str, cost: float, fn) -> None:
        mask = mask_for(fn)
        if mask == 0 or mask == (1 << PAIR_COUNT) - 1:
            return
        rows.append({"name": name, "family": family, "cost": cost, "mask": mask})

    for field in ["a", "b", "sum", "diff", "prod", "anti_sum", "diag_diff"]:
        values = sorted({pair_features(pair)[field] for pair in PAIRS})
        for value in values:
            add(f"{field}_eq_{value}", "numeric_eq", 1.8, lambda feat, f=field, v=value: feat[f] == v)
            add(f"{field}_le_{value}", "numeric_range", 1.5, lambda feat, f=field, v=value: feat[f] <= v)
            add(f"{field}_ge_{value}", "numeric_range", 1.5, lambda feat, f=field, v=value: feat[f] >= v)
        for modulus in range(2, 7):
            for residue in range(modulus):
                add(
                    f"{field}_mod_{modulus}_{residue}",
                    "numeric_mod",
                    2.1,
                    lambda feat, f=field, m=modulus, r=residue: feat[f] % m == r,
                )

    for digit in range(10):
        add(f"contains_digit_{digit}", "digit_incidence", 1.4, lambda feat, d=digit: feat["a"] == d or feat["b"] == d)
        add(f"row_digit_{digit}", "row", 1.9, lambda feat, d=digit: feat["a"] == d)
        add(f"col_digit_{digit}", "col", 1.9, lambda feat, d=digit: feat["b"] == d)

    for field in [
        "diag",
        "edge",
        "center",
        "contains_0",
        "contains_1",
        "contains_3",
        "contains_4",
        "contains_6",
        "contains_9",
        "contains_6_or_9",
        "both_6_9_class",
        "cross_69",
        "same_parity",
        "both_prime",
        "both_square",
    ]:
        add(field, "geometry_bool", 1.3, lambda feat, f=field: bool(feat[f]))

    for name, digits in LORE_SETS.items():
        add(f"any_{name}", "lore_digit_set", 1.9, lambda feat, ds=digits: feat["a"] in ds or feat["b"] in ds)
        add(f"both_{name}", "lore_digit_set", 2.1, lambda feat, ds=digits: feat["a"] in ds and feat["b"] in ds)
        add(f"exactly_one_{name}", "lore_digit_set", 2.2, lambda feat, ds=digits: (feat["a"] in ds) ^ (feat["b"] in ds))

    # Pairwise conjunctions among compact base predicates. This is still not a
    # pair lookup because no predicate can name a full pair; repeated masks are
    # deduplicated by cheapest expression.
    base = [row for row in rows if row["cost"] <= 1.9]
    for left, right in itertools.combinations(base, 2):
        mask = left["mask"] & right["mask"]
        if mask and mask != left["mask"] and mask != right["mask"]:
            rows.append(
                {
                    "name": f"and({left['name']},{right['name']})",
                    "family": "compound_and",
                    "cost": left["cost"] + right["cost"] + 0.8,
                    "mask": mask,
                }
            )

    dedup: dict[int, dict] = {}
    for row in rows:
        old = dedup.get(row["mask"])
        if old is None or row["cost"] < old["cost"]:
            dedup[row["mask"]] = row
    return sorted(dedup.values(), key=lambda item: (item["cost"], item["name"]))


def labels_to_masks(labels: dict[str, str]) -> dict[str, int]:
    masks = {symbol: 0 for symbol in SIGMA}
    for idx, pair in enumerate(PAIRS):
        masks[labels[pair]] |= 1 << idx
    return masks


def symbol_rule_score(mask: int, target: int, term_cost: float) -> dict:
    tp = popcount(mask & target)
    fp = popcount(mask & ~target)
    fn = popcount(target & ~mask)
    tn = PAIR_COUNT - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    # Negative because sort ascending. False positives are more damaging when
    # composing multi-symbol predictions.
    objective = -(2.2 * tp - 1.7 * fp - 1.2 * fn - 0.6 * term_cost)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "term_cost": term_cost,
        "objective": objective,
    }


def best_rule_for_symbol(symbol: str, target: int, predicates: list[dict]) -> dict:
    singles = []
    for pred in predicates:
        scored = symbol_rule_score(pred["mask"], target, pred["cost"])
        singles.append({**scored, "symbol": symbol, "rule_type": "single", "terms": [pred["name"]], "mask": pred["mask"]})
    singles.sort(key=lambda row: (row["objective"], -row["f1"], row["term_cost"], row["terms"]))
    candidates = singles[:TOP_PREDICATES_PER_SYMBOL]
    if MAX_RULE_TERMS >= 2:
        for left, right in itertools.combinations(singles[:TOP_PREDICATES_PER_SYMBOL], 2):
            mask = left["mask"] | right["mask"]
            term_cost = left["term_cost"] + right["term_cost"] + 0.8
            scored = symbol_rule_score(mask, target, term_cost)
            candidates.append(
                {
                    **scored,
                    "symbol": symbol,
                    "rule_type": "or2",
                    "terms": sorted(left["terms"] + right["terms"]),
                    "mask": mask,
                }
            )
    candidates.sort(key=lambda row: (row["objective"], -row["f1"], row["term_cost"], row["terms"]))
    return candidates[0]


def build_rules(labels: dict[str, str], predicates: list[dict]) -> dict:
    masks = labels_to_masks(labels)
    rules = {symbol: best_rule_for_symbol(symbol, masks[symbol], predicates) for symbol in SIGMA}
    # Prediction priority: high precision first, then rule support, then common
    # symbols. This is intentionally fixed from learned rule summaries rather
    # than tuned cell-by-cell.
    inventory = Counter(labels.values())
    priority = sorted(
        SIGMA,
        key=lambda symbol: (
            -rules[symbol]["precision"],
            -rules[symbol]["tp"],
            -inventory[symbol],
            rules[symbol]["term_cost"],
            symbol,
        ),
    )
    fallback = inventory.most_common(1)[0][0]
    predictions = {}
    detail = []
    for idx, pair in enumerate(PAIRS):
        bit = 1 << idx
        hits = [symbol for symbol in priority if rules[symbol]["mask"] & bit]
        predicted = hits[0] if hits else fallback
        predictions[pair] = predicted
        detail.append(
            {
                "pair": pair,
                "actual": labels[pair],
                "predicted": predicted,
                "matched_symbols": hits,
                "hit": predicted == labels[pair],
            }
        )
    hit_count = sum(1 for pair in PAIRS if predictions[pair] == labels[pair])
    total_rule_cost = sum(rules[symbol]["term_cost"] for symbol in SIGMA)
    model_bits = total_rule_cost * math.log2(len(predicates) + 1)
    exception_bits = (PAIR_COUNT - hit_count) * (math.log2(PAIR_COUNT) + math.log2(len(SIGMA)))
    lookup_bits = PAIR_COUNT * math.log2(len(SIGMA))
    mdl_bits = model_bits + exception_bits
    return {
        "rules": {
            symbol: {key: value for key, value in rule.items() if key not in {"mask", "objective"}}
            for symbol, rule in rules.items()
        },
        "priority": priority,
        "fallback": fallback,
        "hit_count": hit_count,
        "accuracy": hit_count / PAIR_COUNT,
        "predictions": detail,
        "total_rule_cost": total_rule_cost,
        "model_bits": model_bits,
        "exception_bits": exception_bits,
        "mdl_bits": mdl_bits,
        "lookup_bits": lookup_bits,
        "mdl_gain_vs_lookup_bits": lookup_bits - mdl_bits,
        "lookup_cost_ratio": mdl_bits / lookup_bits,
    }


def summarize(values: list[float], observed: float, high_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "z_good_direction": z,
        "p_good_direction": p,
    }


def control(labels: dict[str, str], predicates: list[dict], observed: dict) -> dict:
    rng = random.Random(RANDOM_SEED)
    label_values = [labels[pair] for pair in PAIRS]
    hits = []
    mdl_gains = []
    best_symbol_f1 = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = label_values[:]
        rng.shuffle(shuffled)
        ctrl_labels = dict(zip(PAIRS, shuffled))
        row = build_rules(ctrl_labels, predicates)
        hits.append(row["hit_count"])
        mdl_gains.append(row["mdl_gain_vs_lookup_bits"])
        best_symbol_f1.append(max(rule["f1"] for rule in row["rules"].values()))
    return {
        "trials": CONTROL_TRIALS,
        "hit_count": summarize(hits, observed["hit_count"], high_is_good=True),
        "mdl_gain_vs_lookup_bits": summarize(mdl_gains, observed["mdl_gain_vs_lookup_bits"], high_is_good=True),
        "best_symbol_f1": summarize(
            best_symbol_f1,
            max(rule["f1"] for rule in observed["rules"].values()),
            high_is_good=True,
        ),
    }


def verdict(observed: dict, ctrl: dict) -> str:
    p = max(
        ctrl["hit_count"]["p_good_direction"],
        ctrl["mdl_gain_vs_lookup_bits"]["p_good_direction"],
    )
    if observed["mdl_gain_vs_lookup_bits"] > 0 and p <= 0.01:
        return "candidate_symbol_predicate_dnf_generator"
    if observed["accuracy"] >= 0.65 and p <= 0.05:
        if observed["lookup_cost_ratio"] >= 1.0:
            return "weak_symbol_predicate_signal_not_compressed"
        return "weak_symbol_predicate_signal"
    if observed["lookup_cost_ratio"] >= 1.0:
        return "lookup_disguise"
    return "rejected_control"


def write_report(result: dict) -> None:
    observed = result["observed"]
    ctrl = result["control"]
    lines = [
        "# Symbol Predicate DNF Search",
        "",
        "Generated by `symbol_predicate_dnf_search.py`.",
        "",
        "This pass searches for short per-symbol digit predicates over the 55",
        "unordered pair cells. It excludes exact pair predicates and assigns no",
        "plaintext.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Summary",
        "",
        "| Hits | Accuracy | MDL/lookup | Gain bits | Control p(hit) | Control p(MDL) | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| {observed['hit_count']}/55 | {observed['accuracy']:.3f} | "
            f"{observed['lookup_cost_ratio']:.3f} | {observed['mdl_gain_vs_lookup_bits']:.1f} | "
            f"{ctrl['hit_count']['p_good_direction']:.4f} | "
            f"{ctrl['mdl_gain_vs_lookup_bits']['p_good_direction']:.4f} | "
            f"`{result['verdict']}` |"
        ),
        "",
        "## Per-Symbol Rules",
        "",
        "| Symbol | Rule | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, rule in sorted(observed["rules"].items(), key=lambda item: (-item[1]["f1"], item[0])):
        lines.append(
            f"| `{symbol}` | `{' OR '.join(rule['terms'])}` | {rule['precision']:.3f} | "
            f"{rule['recall']:.3f} | {rule['f1']:.3f} | {rule['tp']} | {rule['fp']} | {rule['fn']} |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Metric | Observed | Control mean | Control max | p(good) |",
            "|---|---:|---:|---:|---:|",
            (
                f"| hit count | {ctrl['hit_count']['observed']:.0f} | "
                f"{ctrl['hit_count']['control_mean']:.2f} | "
                f"{ctrl['hit_count']['control_max']:.0f} | "
                f"{ctrl['hit_count']['p_good_direction']:.4f} |"
            ),
            (
                f"| MDL gain bits | {ctrl['mdl_gain_vs_lookup_bits']['observed']:.1f} | "
                f"{ctrl['mdl_gain_vs_lookup_bits']['control_mean']:.1f} | "
                f"{ctrl['mdl_gain_vs_lookup_bits']['control_max']:.1f} | "
                f"{ctrl['mdl_gain_vs_lookup_bits']['p_good_direction']:.4f} |"
            ),
            (
                f"| best symbol F1 | {ctrl['best_symbol_f1']['observed']:.3f} | "
                f"{ctrl['best_symbol_f1']['control_mean']:.3f} | "
                f"{ctrl['best_symbol_f1']['control_max']:.3f} | "
                f"{ctrl['best_symbol_f1']['p_good_direction']:.4f} |"
            ),
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["verdict"].startswith("candidate"):
        lines.append("A compact per-symbol predicate generator passed controls. This is mechanical only.")
    elif result["verdict"].startswith("weak"):
        lines.append(
            "Some symbol predicates are nonrandom, but the combined model does not compress enough to recover the original table formula."
        )
    else:
        lines.append(
            "The best per-symbol predicate/DNF model is lookup-like or ordinary under shuffles. This closes another human-readable rule family without changing the semantic verdict."
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in PAIRS}
    predicates = predicate_library()
    observed = build_rules(labels, predicates)
    ctrl = control(labels, predicates, observed)
    result = {
        "schema": "symbol_predicate_dnf_results.v1",
        "created_at": "2026-06-19",
        "translation_delta": "NONE",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "predicate_count": len(predicates),
        "control": ctrl,
        "observed": observed,
        "verdict": verdict(observed, ctrl),
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "best={hits}/55 ratio={ratio:.3f} verdict={verdict}".format(
            hits=observed["hit_count"],
            ratio=observed["lookup_cost_ratio"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
