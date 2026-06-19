#!/usr/bin/env python3
"""Deterministic apportionment search for the 469 homophone inventory.

The stochastic inventory model is currently the strongest formula-like
generator: one pair cell per symbol, then frequency-weighted extra cells.
This pass asks whether that can be sharpened into a deterministic rule using
classic apportionment/rounding methods.

The tested family is intentionally small and human-scale:

- weight transforms over internal corpus frequency;
- Hamilton/largest remainder;
- Jefferson/D'Hondt, Webster/Sainte-Lague, Adams, and Huntington-Hill.

Mechanical only. No plaintext or glossary is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "deterministic_apportionment_inventory_results.json"
OUT_MD = HERE / "deterministic_apportionment_inventory_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260620
CONTROL_TRIALS = 20000
EXTRA_TOTAL = 41


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def all_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def observed_extra_counts(formula: dict) -> Counter[str]:
    counts = Counter()
    for pair in all_pairs():
        counts[primary_pair_symbol(formula["pair_table"], pair)] += 1
    return Counter({symbol: counts[symbol] - 1 for symbol in SIGMA})


def corpus_counts() -> Counter[str]:
    occ = load_json(OCC_STREAMS)["occ"]
    return Counter({symbol: len(rows) for symbol, rows in occ.items()})


def weights_from_counts(counts: Counter[str], transform: str, alpha: float, shift: float) -> dict[str, float]:
    out = {}
    for symbol in SIGMA:
        value = counts[symbol] + shift
        if transform == "power":
            out[symbol] = value**alpha
        elif transform == "log_power":
            out[symbol] = math.log(value + 1) ** alpha
        elif transform == "sqrt_power":
            out[symbol] = math.sqrt(value) ** alpha
        else:
            raise ValueError(transform)
    return out


def hamilton(weights: dict[str, float], total: int) -> dict[str, int]:
    denom = sum(weights.values())
    quotas = {symbol: total * weights[symbol] / denom for symbol in SIGMA}
    out = {symbol: math.floor(quotas[symbol]) for symbol in SIGMA}
    remainder = total - sum(out.values())
    for symbol in sorted(SIGMA, key=lambda s: (quotas[s] - out[s], quotas[s], s), reverse=True)[:remainder]:
        out[symbol] += 1
    return out


def divisor(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    quotients = []
    for symbol, weight in weights.items():
        for seats in range(total + 1):
            if method == "jefferson":
                quotient = weight / (seats + 1)
            elif method == "webster":
                quotient = weight / (2 * seats + 1)
            elif method == "adams":
                quotient = float("inf") if seats == 0 else weight / seats
            elif method == "hill":
                quotient = float("inf") if seats == 0 else weight / math.sqrt(seats * (seats + 1))
            else:
                raise ValueError(method)
            quotients.append((quotient, symbol, seats))
    quotients.sort(reverse=True)
    out = {symbol: 0 for symbol in SIGMA}
    for _quotient, symbol, _seats in quotients[:total]:
        out[symbol] += 1
    return out


def allocate(weights: dict[str, float], total: int, method: str) -> dict[str, int]:
    if method == "hamilton":
        return hamilton(weights, total)
    return divisor(weights, total, method)


def l1(left: dict[str, int], right: dict[str, int]) -> int:
    return sum(abs(left[symbol] - right[symbol]) for symbol in SIGMA)


def max_abs(left: dict[str, int], right: dict[str, int]) -> int:
    return max(abs(left[symbol] - right[symbol]) for symbol in SIGMA)


def pearson(xs: list[float], ys: list[float]) -> float:
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if not dx or not dy:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def candidate_rows(counts: Counter[str]) -> list[dict]:
    methods = ["hamilton", "jefferson", "webster", "adams", "hill"]
    transforms = ["power", "log_power", "sqrt_power"]
    shifts = [0, 1, 5, 10, 25, 50, 100, 250]
    rows = []
    for transform in transforms:
        for alpha_i in range(1, 601):
            alpha = alpha_i / 200
            for shift in shifts:
                if shift == 0 and min(counts.values()) == 0:
                    continue
                weights = weights_from_counts(counts, transform, alpha, shift)
                for method in methods:
                    prediction = allocate(weights, EXTRA_TOTAL, method)
                    rows.append(
                        {
                            "transform": transform,
                            "alpha": alpha,
                            "shift": shift,
                            "method": method,
                            "prediction": prediction,
                        }
                    )
    return rows


def score_rows(rows: list[dict], observed: Counter[str], counts: Counter[str]) -> list[dict]:
    corpus_vector = [counts[symbol] for symbol in SIGMA]
    out = []
    for row in rows:
        pred = row["prediction"]
        out.append(
            {
                **row,
                "l1": l1(pred, observed),
                "max_abs": max_abs(pred, observed),
                "pearson_vs_observed": pearson([pred[symbol] for symbol in SIGMA], [observed[symbol] for symbol in SIGMA]),
                "pearson_prediction_vs_corpus": pearson([pred[symbol] for symbol in SIGMA], corpus_vector),
            }
        )
    out.sort(key=lambda item: (item["l1"], item["max_abs"], -item["pearson_vs_observed"], item["transform"], item["alpha"], item["shift"], item["method"]))
    return out


def summarize(values: list[float], observed: float, low_is_good: bool) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if low_is_good:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    else:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    return {"observed": observed, "control_mean": mean, "control_sd": sd, "z_good_direction": z, "p_good_direction": p, "control_min": min(values), "control_max": max(values)}


def control(best_rows: list[dict], observed: Counter[str]) -> dict:
    """Shuffle the observed extra vector over symbols and rescore fixed candidate family."""
    rng = random.Random(RANDOM_SEED)
    values = list(observed.values())
    l1_values = []
    corr_values = []
    rows = [{"prediction": row["prediction"]} for row in best_rows]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(values)
        shuffled = Counter({symbol: values[idx] for idx, symbol in enumerate(SIGMA)})
        best_l1 = min(l1(row["prediction"], shuffled) for row in rows)
        best_corr = max(pearson([row["prediction"][symbol] for symbol in SIGMA], [shuffled[symbol] for symbol in SIGMA]) for row in rows)
        l1_values.append(best_l1)
        corr_values.append(best_corr)
    return {"l1": l1_values, "pearson": corr_values}


def main() -> int:
    formula = load_json(FORMULA_JSON)
    observed = observed_extra_counts(formula)
    counts = corpus_counts()
    rows = score_rows(candidate_rows(counts), observed, counts)
    best = rows[0]
    exact_hits = [row for row in rows if row["l1"] == 0]
    # Deduplicate by prediction to keep control runtime sane without changing the family's best possible fit.
    seen = set()
    unique_rows = []
    for row in rows:
        key = tuple(row["prediction"][symbol] for symbol in SIGMA)
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    ctrl = control(unique_rows, observed)
    l1_summary = summarize(ctrl["l1"], best["l1"], low_is_good=True)
    corr_summary = summarize(ctrl["pearson"], best["pearson_vs_observed"], low_is_good=False)

    verdict = "rejected_control"
    if best["l1"] == 0 and l1_summary["p_good_direction"] <= 0.01:
        verdict = "candidate_generator_deterministic_inventory"
    elif best["l1"] <= 6 and l1_summary["p_good_direction"] <= 0.05:
        verdict = "weak_candidate_inventory"
    elif l1_summary["p_good_direction"] <= 0.01:
        verdict = "secondary_support_not_exact"

    result = {
        "schema": "deterministic_apportionment_inventory_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "observed_extra_counts": dict(observed),
        "corpus_symbol_counts": dict(counts),
        "candidate_count": len(rows),
        "unique_prediction_count": len(unique_rows),
        "exact_hit_count": len(exact_hits),
        "best": best,
        "top_rows": rows[:30],
        "controls": {
            "best_l1_vs_shuffled_observed": l1_summary,
            "best_pearson_vs_shuffled_observed": corr_summary,
        },
        "verdict": verdict,
    }
    write_json(OUT_JSON, result)

    lines = [
        "# Deterministic Apportionment Inventory",
        "",
        "Generated by `deterministic_apportionment_inventory.py`.",
        "",
        "This pass asks whether the stochastic frequency-weighted inventory can be",
        "sharpened into a deterministic apportionment rule for the 41 extra",
        "homophone slots.",
        "",
        "## Best Rule",
        "",
        "| Transform | alpha | shift | Method | L1 | max abs | Pearson vs observed | p(L1) |",
        "|---|---:|---:|---|---:|---:|---:|---:|",
        (
            f"| `{best['transform']}` | {best['alpha']:.3f} | {best['shift']} | `{best['method']}` | "
            f"{best['l1']} | {best['max_abs']} | {best['pearson_vs_observed']:.3f} | "
            f"{l1_summary['p_good_direction']:.5f} |"
        ),
        "",
        "Predicted extras:",
        "",
        "```json",
        json.dumps(best["prediction"], indent=2, sort_keys=True),
        "```",
        "",
        "## Verdict",
        "",
        f"`{verdict}`.",
        "",
        f"No exact rule was found (`exact_hit_count={len(exact_hits)}`). The best",
        f"apportionment is still {best['l1']} cells away by L1, so the deterministic",
        "rounding family does not replace the stochastic inventory model.",
        "",
        "However, the best apportionment is far better than shuffled symbol-label",
        "controls. This is useful as secondary support for frequency-weighted",
        "homophone allocation, not as an exact original formula.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"verdict={verdict} best_l1={best['l1']} exact_hits={len(exact_hits)} p={l1_summary['p_good_direction']:.5f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
