#!/usr/bin/env python3
"""Nine-identity base matrix plus 6/9 renderer search.

The existing `6<->9` quotient has 46 orbits because `66/99` collapse together
but `69` remains a fixed cross-pair.  This pass tests the stricter authoring
hypothesis suggested by the current evidence:

    build a 45-cell base matrix over identities
    0,1,2,3,4,5,Q,7,8, then render Q as 6/9.

It charges the base labels, the Q-render split metadata, and the residual
secondary labels.  This is a mechanical authoring/process model, not a
plaintext decoder.
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
QUOTIENT_JSON = HERE / "digit_orbit_quotient_results.json"

OUT_JSON = HERE / "nine_identity_render_split_results.json"
OUT_MD = HERE / "nine_identity_render_split_report.md"

SIGMA = "*ABCEFILNORSTV"
SYMBOL_BITS = math.log2(len(SIGMA))
RAW_LOOKUP_BITS = 55 * SYMBOL_BITS
TRANSFORM_BITS = math.log2(45) + math.log2(8)
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 5000

IDENTITIES = ["0", "1", "2", "3", "4", "5", "Q", "7", "8"]
IDENTITY_INDEX = {value: index for index, value in enumerate(IDENTITIES)}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return math.log2(math.comb(n, k))


def symbol_key(symbol: str) -> int:
    return SIGMA.index(symbol)


def pair_key(pair: tuple[int, int]) -> str:
    return f"{pair[0]}{pair[1]}"


def natural_pairs() -> list[tuple[int, int]]:
    return [(a, b) for a in range(10) for b in range(a, 10)]


def primary_pair_symbol(pair_table: dict[str, dict[str, Any]], pair: tuple[int, int]) -> str:
    cell = pair_table[pair_key(pair)]
    if cell["status"] == "pure":
        return cell["symbol_if_pure"]
    return min(cell["symbols"], key=symbol_key)


def identity_of_digit(digit: int) -> str:
    return "Q" if digit in {6, 9} else str(digit)


def identity_pair(pair: tuple[int, int]) -> tuple[str, str]:
    left, right = identity_of_digit(pair[0]), identity_of_digit(pair[1])
    return (left, right) if IDENTITY_INDEX[left] <= IDENTITY_INDEX[right] else (right, left)


def identity_pair_key(pair: tuple[str, str]) -> str:
    return "".join(pair)


def base_identity_pairs() -> list[tuple[str, str]]:
    return [(left, right) for i, left in enumerate(IDENTITIES) for right in IDENTITIES[i:]]


def majority_symbol(labels: list[str]) -> str:
    counts = Counter(labels)
    return min(counts, key=lambda symbol: (-counts[symbol], symbol_key(symbol)))


def build_groups(labels: dict[tuple[int, int], str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for pair in natural_pairs():
        grouped[identity_pair(pair)].append(pair)
    rows = []
    for ident_pair in base_identity_pairs():
        pairs = sorted(grouped[ident_pair])
        pair_labels = [labels[pair] for pair in pairs]
        base_label = majority_symbol(pair_labels)
        residuals = [
            {"pair": pair_key(pair), "label": labels[pair]}
            for pair in pairs
            if labels[pair] != base_label
        ]
        rows.append(
            {
                "identity_pair": identity_pair_key(ident_pair),
                "left": ident_pair[0],
                "right": ident_pair[1],
                "original_pairs": [pair_key(pair) for pair in pairs],
                "labels": pair_labels,
                "base_label": base_label,
                "is_expandable": len(pairs) > 1,
                "is_xq": "Q" in ident_pair and ident_pair != ("Q", "Q"),
                "is_qq": ident_pair == ("Q", "Q"),
                "is_mixed": len(set(pair_labels)) > 1,
                "residuals": residuals,
            }
        )
    return rows


def generic_bits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expandable = [row for row in rows if row["is_expandable"]]
    mixed = [row for row in expandable if row["is_mixed"]]
    residual_count = sum(len(row["residuals"]) for row in rows)
    label_slots = len(rows) + residual_count
    selector_bits = log2_comb(len(expandable), len(mixed))
    position_bits = 0.0
    for row in mixed:
        position_bits += log2_comb(len(row["original_pairs"]), len(row["residuals"]))
    total = TRANSFORM_BITS + selector_bits + position_bits + label_slots * SYMBOL_BITS
    return {
        "id": "generic_45_base_plus_expandable_split_metadata",
        "base_cell_count": len(rows),
        "expandable_group_count": len(expandable),
        "mixed_group_count": len(mixed),
        "residual_label_count": residual_count,
        "label_slots": label_slots,
        "selector_bits": selector_bits,
        "position_bits": position_bits,
        "transform_bits": TRANSFORM_BITS,
        "total_bits": total,
        "lookup_ratio": total / RAW_LOOKUP_BITS,
        "gain_vs_raw_lookup_bits": RAW_LOOKUP_BITS - total,
    }


def renderer_aware_bits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    xq = [row for row in rows if row["is_xq"]]
    mixed_xq = [row for row in xq if row["is_mixed"]]
    qq = next(row for row in rows if row["is_qq"])
    residual_count = sum(len(row["residuals"]) for row in rows)
    label_slots = len(rows) + residual_count
    xq_selector_bits = log2_comb(len(xq), len(mixed_xq))
    # In xQ groups, a mixed two-cell expansion needs one side bit.
    xq_side_bits = sum(len(row["residuals"]) for row in mixed_xq)
    # The QQ group has a structural cross-pair slot 69; charge a small marker
    # if that group is mixed, but do not charge a full position among all cells.
    qq_cross_marker_bits = 1.0 if qq["is_mixed"] else 0.0
    total = TRANSFORM_BITS + xq_selector_bits + xq_side_bits + qq_cross_marker_bits + label_slots * SYMBOL_BITS
    return {
        "id": "renderer_aware_45_base_Q_to_6_9_split",
        "base_cell_count": len(rows),
        "xq_group_count": len(xq),
        "mixed_xq_group_count": len(mixed_xq),
        "qq_is_mixed": qq["is_mixed"],
        "residual_label_count": residual_count,
        "label_slots": label_slots,
        "xq_selector_bits": xq_selector_bits,
        "xq_side_bits": xq_side_bits,
        "qq_cross_marker_bits": qq_cross_marker_bits,
        "transform_bits": TRANSFORM_BITS,
        "total_bits": total,
        "lookup_ratio": total / RAW_LOOKUP_BITS,
        "gain_vs_raw_lookup_bits": RAW_LOOKUP_BITS - total,
    }


def evaluate(labels: dict[tuple[int, int], str]) -> dict[str, Any]:
    rows = build_groups(labels)
    return {
        "groups": rows,
        "generic": generic_bits(rows),
        "renderer_aware": renderer_aware_bits(rows),
    }


def shuffle_labels(labels: dict[tuple[int, int], str], rng: random.Random) -> dict[tuple[int, int], str]:
    pairs = natural_pairs()
    values = [labels[pair] for pair in pairs]
    rng.shuffle(values)
    return dict(zip(pairs, values))


def summarize(values: list[float], observed: float, higher_is_better: bool) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    if higher_is_better:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good_direction": p,
        "z_good_direction": z,
    }


def controls(labels: dict[tuple[int, int], str], observed: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    generic_gain = []
    renderer_gain = []
    generic_bits_values = []
    renderer_bits_values = []
    renderer_mixed_xq = []
    renderer_residuals = []
    for _ in range(CONTROL_TRIALS):
        ctrl = evaluate(shuffle_labels(labels, rng))
        generic_gain.append(ctrl["generic"]["gain_vs_raw_lookup_bits"])
        renderer_gain.append(ctrl["renderer_aware"]["gain_vs_raw_lookup_bits"])
        generic_bits_values.append(ctrl["generic"]["total_bits"])
        renderer_bits_values.append(ctrl["renderer_aware"]["total_bits"])
        renderer_mixed_xq.append(ctrl["renderer_aware"]["mixed_xq_group_count"])
        renderer_residuals.append(ctrl["renderer_aware"]["residual_label_count"])
    return {
        "trials": CONTROL_TRIALS,
        "global_inventory_shuffle": {
            "generic_gain_vs_raw_lookup_bits": summarize(generic_gain, observed["generic"]["gain_vs_raw_lookup_bits"], True),
            "renderer_gain_vs_raw_lookup_bits": summarize(renderer_gain, observed["renderer_aware"]["gain_vs_raw_lookup_bits"], True),
            "generic_total_bits": summarize(generic_bits_values, observed["generic"]["total_bits"], False),
            "renderer_total_bits": summarize(renderer_bits_values, observed["renderer_aware"]["total_bits"], False),
            "renderer_mixed_xq_group_count": summarize(renderer_mixed_xq, observed["renderer_aware"]["mixed_xq_group_count"], False),
            "renderer_residual_label_count": summarize(renderer_residuals, observed["renderer_aware"]["residual_label_count"], False),
        },
    }


def verdict(result: dict[str, Any]) -> str:
    renderer = result["observed"]["renderer_aware"]
    quotient_gain = result["baselines"]["quotient_46_split_gain_bits"]
    p = result["controls"]["global_inventory_shuffle"]["renderer_gain_vs_raw_lookup_bits"]["p_good_direction"]
    if renderer["gain_vs_raw_lookup_bits"] > quotient_gain and p <= 0.05:
        return "candidate_45_base_renderer_beats_46_quotient"
    if renderer["gain_vs_raw_lookup_bits"] > 0 and p <= 0.05:
        return "weak_45_base_renderer_compression"
    if renderer["gain_vs_raw_lookup_bits"] > 0:
        return "base45_renderer_positive_but_control_sensitive"
    return "base45_renderer_not_promoted"


def write_report(result: dict[str, Any]) -> None:
    obs = result["observed"]
    generic = obs["generic"]
    renderer = obs["renderer_aware"]
    ctrl = result["controls"]["global_inventory_shuffle"]
    lines = [
        "# Nine-Identity Render Split Search",
        "",
        "Generated by `nine_identity_render_split_search.py`.",
        "",
        "This pass tests a stricter authoring model than the 46-orbit quotient:",
        "a 45-cell base matrix over `0,1,2,3,4,5,Q,7,8`, rendered by expanding",
        "`Q` to `6/9`. It assigns no plaintext.",
        "",
        "## Summary",
        "",
        "| Model | Base cells | Label slots | Mixed groups | Bits | Lookup ratio | Gain vs raw |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| generic expandable split | {generic['base_cell_count']} | {generic['label_slots']} | {generic['mixed_group_count']} | {generic['total_bits']:.2f} | {generic['lookup_ratio']:.3f} | {generic['gain_vs_raw_lookup_bits']:.2f} |",
        f"| renderer-aware Q split | {renderer['base_cell_count']} | {renderer['label_slots']} | {renderer['mixed_xq_group_count']} xQ + QQ={str(renderer['qq_is_mixed']).lower()} | {renderer['total_bits']:.2f} | {renderer['lookup_ratio']:.3f} | {renderer['gain_vs_raw_lookup_bits']:.2f} |",
        "",
        f"Raw 55-cell lookup baseline: `{result['baselines']['raw_lookup_bits']:.2f}` bits.",
        f"Prior 46-orbit `6<->9` split gain: `{result['baselines']['quotient_46_split_gain_bits']:.2f}` bits.",
        "",
        "## Expanded Q Groups",
        "",
        "| Base cell | Original pairs | Labels | Base label | Residuals |",
        "|---|---|---|---|---|",
    ]
    for row in obs["groups"]:
        if row["is_expandable"]:
            residuals = ", ".join(f"{item['pair']}:{item['label']}" for item in row["residuals"]) or "-"
            lines.append(
                f"| `{row['identity_pair']}` | `{', '.join(row['original_pairs'])}` | `{''.join(row['labels'])}` | `{row['base_label']}` | `{residuals}` |"
            )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Metric | Observed | Mean | Max/Min | p(good) |",
            "|---|---:|---:|---:|---:|",
            f"| renderer gain vs raw lookup | {ctrl['renderer_gain_vs_raw_lookup_bits']['observed']:.2f} | {ctrl['renderer_gain_vs_raw_lookup_bits']['mean']:.2f} | {ctrl['renderer_gain_vs_raw_lookup_bits']['max']:.2f} | {ctrl['renderer_gain_vs_raw_lookup_bits']['p_good_direction']:.5f} |",
            f"| renderer total bits | {ctrl['renderer_total_bits']['observed']:.2f} | {ctrl['renderer_total_bits']['mean']:.2f} | {ctrl['renderer_total_bits']['min']:.2f} | {ctrl['renderer_total_bits']['p_good_direction']:.5f} |",
            f"| renderer mixed xQ groups | {ctrl['renderer_mixed_xq_group_count']['observed']:.0f} | {ctrl['renderer_mixed_xq_group_count']['mean']:.2f} | {ctrl['renderer_mixed_xq_group_count']['min']:.0f} | {ctrl['renderer_mixed_xq_group_count']['p_good_direction']:.5f} |",
            f"| renderer residual labels | {ctrl['renderer_residual_label_count']['observed']:.0f} | {ctrl['renderer_residual_label_count']['mean']:.2f} | {ctrl['renderer_residual_label_count']['min']:.0f} | {ctrl['renderer_residual_label_count']['p_good_direction']:.5f} |",
            "",
            "## Interpretation",
            "",
            "The 45-cell base matrix closes the formal gap between a 9-identity",
            "authoring worksheet and the previous 46-orbit quotient. It does not",
            "improve on the 46-orbit model: the `QQ -> 66/69/99` cross-pair adds",
            "metadata that consumes the apparent one-cell saving. The result is an",
            "audited negative for the pure 45-base renderer hypothesis.",
            "",
            f"Verdict: `{result['verdict']}`.",
            "",
            "Translation delta: `NONE`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    labels = {pair: primary_pair_symbol(formula["pair_table"], pair) for pair in natural_pairs()}
    observed = evaluate(labels)
    quotient_gain = 0.0
    if QUOTIENT_JSON.exists():
        quotient = load_json(QUOTIENT_JSON)
        quotient_gain = quotient["swap_6_9"]["split_mdl_gain_vs_lookup_bits"]
    result = {
        "schema": "nine_identity_render_split_results.v1",
        "translation_delta": "NONE",
        "baselines": {
            "raw_lookup_bits": RAW_LOOKUP_BITS,
            "quotient_46_split_gain_bits": quotient_gain,
            "transform_bits": TRANSFORM_BITS,
            "symbol_bits": SYMBOL_BITS,
        },
        "observed": observed,
    }
    result["controls"] = controls(labels, observed)
    result["verdict"] = verdict(result)
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "verdict={verdict} renderer_gain={gain:.2f} quotient_gain={qgain:.2f}".format(
            verdict=result["verdict"],
            gain=observed["renderer_aware"]["gain_vs_raw_lookup_bits"],
            qgain=quotient_gain,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
