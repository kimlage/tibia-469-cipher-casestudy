#!/usr/bin/env python3
"""Priority-masked E layer search.

This is a narrow follow-up to `e_layer_predicate_search.py`.

Hypothesis:
  A few non-E cells inside the high digit block are claimed first, then
  `both_in_4578` can fill the remaining off-diagonal E cells. Add the selected
  E diagonals and `prod_eq_5` for `15`.

This tests whether the E clue is the start of a priority-layer construction or
only a local descriptive fit. It assigns no plaintext.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OUT_JSON = HERE / "priority_masked_e_layer_results.json"
OUT_MD = HERE / "priority_masked_e_layer_report.md"

RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000
SYMBOLS = "*ABCEFILNORSTV"
PAIRS = [f"{a}{b}" for a in range(10) for b in range(a, 10)]
PAIR_INDEX = {pair: idx for idx, pair in enumerate(PAIRS)}
SYMBOL_BITS = math.log2(len(SYMBOLS))
CELL_BITS = math.log2(len(PAIRS))
LABEL_EXCEPTION_BITS = CELL_BITS + SYMBOL_BITS


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pair_symbol(pair_table: dict[str, Any], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return "+".join(sorted(row["symbols"]))


def labels_from_formula() -> list[str]:
    formula = load_json(FORMULA_JSON)
    return [pair_symbol(formula["pair_table"], pair) for pair in PAIRS]


def log2_multinomial(labels: list[str]) -> float:
    counts = Counter(labels)
    out = math.lgamma(len(labels) + 1) / math.log(2)
    for count in counts.values():
        out -= math.lgamma(count + 1) / math.log(2)
    return out


def rule_claims() -> list[dict[str, Any]]:
    blockers = {
        "45": "F",
        "55": "V",
        "77": "N",
        "88": "A",
    }
    diag_e = {"11", "33", "44", "66", "99"}
    claims: dict[str, dict[str, Any]] = {}

    for pair, symbol in blockers.items():
        claims[pair] = {"pair": pair, "symbol": symbol, "rule": "priority_blocker"}
    for pair in diag_e:
        claims[pair] = {"pair": pair, "symbol": "E", "rule": "selected_e_diagonal"}
    for pair in PAIRS:
        a, b = int(pair[0]), int(pair[1])
        if a * b == 5:
            claims.setdefault(pair, {"pair": pair, "symbol": "E", "rule": "prod_eq_5"})
        if a in {4, 5, 7, 8} and b in {4, 5, 7, 8} and pair not in blockers:
            claims.setdefault(pair, {"pair": pair, "symbol": "E", "rule": "both_in_4578_after_blockers"})
    return [claims[pair] for pair in PAIRS if pair in claims]


def model_cost_bits() -> dict[str, float]:
    blocker_bits = 4 * (CELL_BITS + SYMBOL_BITS)
    diag_set_bits = 4.0 + 5 * math.log2(10)
    prod_eq_bits = 5.0
    high_set_bits = 3.0 + 4 * math.log2(10)
    priority_bits = 4.0
    total = blocker_bits + diag_set_bits + prod_eq_bits + high_set_bits + priority_bits
    return {
        "priority_blockers_bits": blocker_bits,
        "selected_diagonal_set_bits": diag_set_bits,
        "prod_eq_5_bits": prod_eq_bits,
        "both_in_4578_bits": high_set_bits,
        "priority_order_bits": priority_bits,
        "total_model_bits": total,
    }


def evaluate(labels: list[str], claims: list[dict[str, Any]], costs: dict[str, float]) -> dict[str, Any]:
    predictions: list[str | None] = [None] * len(labels)
    claim_rows = []
    for claim in claims:
        idx = PAIR_INDEX[claim["pair"]]
        predictions[idx] = claim["symbol"]
        claim_rows.append(
            {
                **claim,
                "actual": labels[idx],
                "hit": labels[idx] == claim["symbol"],
            }
        )

    remaining_indexes = [idx for idx, pred in enumerate(predictions) if pred is None]
    default_symbol = Counter(labels[idx] for idx in remaining_indexes).most_common(1)[0][0]
    for idx in remaining_indexes:
        predictions[idx] = default_symbol

    claim_hits = sum(1 for row in claim_rows if row["hit"])
    total_hits = sum(1 for pred, actual in zip(predictions, labels) if pred == actual)
    errors = len(labels) - total_hits
    inventory_bits = log2_multinomial(labels)
    raw_bits = len(labels) * SYMBOL_BITS
    mdl_bits = costs["total_model_bits"] + SYMBOL_BITS + errors * LABEL_EXCEPTION_BITS
    return {
        "claims": claim_rows,
        "claim_count": len(claim_rows),
        "claim_hits": claim_hits,
        "claim_accuracy": claim_hits / len(claim_rows),
        "default_symbol": default_symbol,
        "total_hits": total_hits,
        "total_accuracy": total_hits / len(labels),
        "errors_after_default": errors,
        "model_cost_bits": costs["total_model_bits"] + SYMBOL_BITS,
        "mdl_bits": mdl_bits,
        "inventory_lookup_bits": inventory_bits,
        "raw_lookup_bits": raw_bits,
        "gain_vs_inventory_lookup_bits": inventory_bits - mdl_bits,
        "mdl_ratio_vs_inventory_lookup": mdl_bits / inventory_bits,
        "predicted": "".join(predictions),
    }


def controls(labels: list[str], claims: list[dict[str, Any]], costs: dict[str, float], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    claim_hits = []
    total_hits = []
    gains = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        row = evaluate(shuffled, claims, costs)
        claim_hits.append(row["claim_hits"])
        total_hits.append(row["total_hits"])
        gains.append(row["gain_vs_inventory_lookup_bits"])

    def summarize(values: list[float], observed_value: float) -> dict[str, float]:
        mean = sum(values) / len(values)
        sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
        return {
            "observed": observed_value,
            "mean": mean,
            "sd": sd,
            "min": min(values),
            "max": max(values),
            "p_good_direction": (sum(value >= observed_value for value in values) + 1) / (len(values) + 1),
            "z_good_direction": (observed_value - mean) / sd if sd else 0.0,
        }

    return {
        "trials": CONTROL_TRIALS,
        "claim_hits": summarize(claim_hits, observed["claim_hits"]),
        "total_hits": summarize(total_hits, observed["total_hits"]),
        "gain_vs_inventory_lookup_bits": summarize(gains, observed["gain_vs_inventory_lookup_bits"]),
    }


def classify(observed: dict[str, Any], ctrl: dict[str, Any]) -> str:
    if observed["gain_vs_inventory_lookup_bits"] > 0 and ctrl["gain_vs_inventory_lookup_bits"]["p_good_direction"] <= 0.05:
        return "candidate_priority_masked_e_formula"
    if observed["claim_accuracy"] == 1.0 and ctrl["claim_hits"]["p_good_direction"] <= 0.01:
        return "exact_local_e_priority_layer_not_global_formula"
    return "priority_masked_e_layer_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    obs = result["observed"]
    ctrl = result["controls"]
    lines = [
        "# Priority-Masked E Layer Search",
        "",
        "Generated by `priority_masked_e_layer_search.py`.",
        "",
        "This pass tests a narrow priority model suggested by the E residual:",
        "claim four non-E blockers inside the high block first, then let",
        "`both_in_4578`, `prod_eq_5`, and selected diagonal cells fill E.",
        "",
        "## Summary",
        "",
        "| Claim hits | Total hits with default | MDL/inventory | Gain vs inventory | Claim-hit control p | MDL control p | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---|",
        f"| {obs['claim_hits']}/{obs['claim_count']} | {obs['total_hits']}/55 | {obs['mdl_ratio_vs_inventory_lookup']:.3f} | {obs['gain_vs_inventory_lookup_bits']:.1f} | {ctrl['claim_hits']['p_good_direction']:.5f} | {ctrl['gain_vs_inventory_lookup_bits']['p_good_direction']:.5f} | `{result['verdict']}` |",
        "",
        "## Claims",
        "",
        "| Pair | Predicted | Actual | Rule | Hit |",
        "|---|---|---|---|---|",
    ]
    for row in obs["claims"]:
        hit = "yes" if row["hit"] else "no"
        lines.append(f"| `{row['pair']}` | `{row['symbol']}` | `{row['actual']}` | `{row['rule']}` | {hit} |")
    lines += [
        "",
        "## Cost Model",
        "",
    ]
    for key, value in result["costs"].items():
        lines.append(f"- `{key}`: `{value:.1f}` bits.")
    lines += [
        "",
        "## Controls",
        "",
        f"- Claim-hit control p: `{ctrl['claim_hits']['p_good_direction']:.5f}`.",
        f"- Total-hit control p: `{ctrl['total_hits']['p_good_direction']:.5f}`.",
        f"- MDL-gain control p: `{ctrl['gain_vs_inventory_lookup_bits']['p_good_direction']:.5f}`.",
        "",
        "## Interpretation",
        "",
        "The priority layer is meaningful only if it beats an inventory lookup after",
        "charging the blockers, selected diagonal set, high-block set, and residual",
        "exceptions. Exact local claims alone are not enough, because the blockers",
        "are hand-selected cells.",
        "",
        f"Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    labels = labels_from_formula()
    claims = rule_claims()
    costs = model_cost_bits()
    observed = evaluate(labels, claims, costs)
    ctrl = controls(labels, claims, costs, observed)
    result = {
        "schema": "priority_masked_e_layer_results.v1",
        "source": str(FORMULA_JSON.relative_to(ROOT)),
        "claims": claims,
        "costs": costs,
        "observed": observed,
        "controls": ctrl,
        "verdict": classify(observed, ctrl),
        "translation_delta": "NONE",
        "new_plaintext": False,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "claims={claim_hits}/{claim_count} total={total}/55 gain={gain:.1f} p={p:.5f} verdict={verdict}".format(
            claim_hits=observed["claim_hits"],
            claim_count=observed["claim_count"],
            total=observed["total_hits"],
            gain=observed["gain_vs_inventory_lookup_bits"],
            p=ctrl["gain_vs_inventory_lookup_bits"]["p_good_direction"],
            verdict=result["verdict"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
