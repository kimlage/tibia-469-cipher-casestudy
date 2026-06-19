#!/usr/bin/env python3
"""Directed 00..99 surface sequence-generator search.

Most matrix-origin tests work on the 55 unordered pair cells. The ordered
surface audit showed that the 99 present directed codes are nearly a mirror
rendering of the upper/unordered table. This pass asks a separate question:
could a human have generated the ordered 00..99 worksheet itself as a short
sequence, traversal, or periodic automaton?

The test is mechanical only. It assigns no plaintext and treats mirror
redundancy as a render layer, not as a recovered upper-table formula.
"""

from __future__ import annotations

import json
import math
import random
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
DIRECTED_SURFACE_JSON = HERE / "directed_pair_surface_results.json"

OUT_JSON = HERE / "directed_surface_sequence_generator_results.json"
OUT_MD = HERE / "directed_surface_sequence_generator_report.md"

RANDOM_SEED = 46920260623
TRIALS = 1500
MAX_PERIOD = 48


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def all_codes() -> list[str]:
    return [f"{a}{b}" for a in range(10) for b in range(10)]


def present(codes: list[str], code_to_symbol: dict[str, str]) -> list[str]:
    return [code for code in codes if code in code_to_symbol]


def spiral_coords() -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    top, left, bottom, right = 0, 0, 9, 9
    while top <= bottom and left <= right:
        for y in range(left, right + 1):
            coords.append((top, y))
        top += 1
        for x in range(top, bottom + 1):
            coords.append((x, right))
        right -= 1
        if top <= bottom:
            for y in range(right, left - 1, -1):
                coords.append((bottom, y))
            bottom -= 1
        if left <= right:
            for x in range(bottom, top - 1, -1):
                coords.append((x, left))
            left += 1
    return coords


def directed_orders(code_to_symbol: dict[str, str]) -> dict[str, dict[str, Any]]:
    row_major = all_codes()
    row_snake = [
        f"{a}{b}"
        for a in range(10)
        for b in (range(10) if a % 2 == 0 else range(9, -1, -1))
    ]
    col_major = [f"{a}{b}" for b in range(10) for a in range(10)]
    col_snake = [
        f"{a}{b}"
        for b in range(10)
        for a in (range(10) if b % 2 == 0 else range(9, -1, -1))
    ]
    diag_sum = sorted(all_codes(), key=lambda code: (int(code[0]) + int(code[1]), int(code[0]), int(code[1])))
    anti_diag = sorted(all_codes(), key=lambda code: (int(code[0]) - int(code[1]), int(code[0]), int(code[1])))
    spiral = [f"{a}{b}" for a, b in spiral_coords()]
    upper = [f"{a}{b}" for a in range(10) for b in range(a, 10)]
    lower = [f"{a}{b}" for a in range(10) for b in range(a)]
    mirror_interleave = []
    for a in range(10):
        for b in range(a, 10):
            mirror_interleave.append(f"{a}{b}")
            if a != b:
                mirror_interleave.append(f"{b}{a}")
    reverse_mirror_interleave = list(reversed(mirror_interleave))
    orders = {
        "directed_row_major": ("full_directed", row_major),
        "directed_row_major_rev": ("full_directed", list(reversed(row_major))),
        "directed_row_snake": ("full_directed", row_snake),
        "directed_col_major": ("full_directed", col_major),
        "directed_col_snake": ("full_directed", col_snake),
        "directed_diag_sum": ("full_directed", diag_sum),
        "directed_anti_diag": ("full_directed", anti_diag),
        "directed_spiral": ("full_directed", spiral),
        "mirror_pair_interleave": ("mirror_interleave", mirror_interleave),
        "mirror_pair_interleave_rev": ("mirror_interleave", reverse_mirror_interleave),
        "upper_then_lower": ("upper_lower", upper + lower),
        "lower_then_upper": ("upper_lower", lower + upper),
        "upper_only_row": ("upper_only", upper),
        "upper_only_row_rev": ("upper_only", list(reversed(upper))),
        "lower_only_row": ("lower_only", lower),
        "lower_only_row_rev": ("lower_only", list(reversed(lower))),
    }
    return {
        name: {"family": family, "codes": present(codes, code_to_symbol)}
        for name, (family, codes) in orders.items()
    }


def kt_bits(seq: list[str], order: int, alphabet: list[str]) -> float:
    contexts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    bits = 0.0
    for idx, symbol in enumerate(seq):
        context = tuple(seq[max(0, idx - order) : idx]) if order else ()
        counter = contexts[context]
        total = sum(counter.values())
        prob = (counter[symbol] + 0.5) / (total + 0.5 * len(alphabet))
        bits -= math.log2(prob)
        counter[symbol] += 1
    return bits + len(contexts) * math.log2(len(alphabet) + 1)


def transition_metrics(seq: list[str]) -> dict[str, Any]:
    transitions = list(zip(seq, seq[1:]))
    edges = Counter(transitions)
    out_degree: dict[str, set[str]] = defaultdict(set)
    for left, right in transitions:
        out_degree[left].add(right)
    repeated_edges = sum(count - 1 for count in edges.values() if count > 1)
    deterministic_steps = sum(1 for left, _right in transitions if len(out_degree[left]) == 1)
    return {
        "unique_edges": len(edges),
        "repeated_edge_excess": repeated_edges,
        "deterministic_step_fraction": deterministic_steps / len(transitions) if transitions else 0.0,
    }


def best_periodic_template(seq: list[str], alphabet: list[str]) -> dict[str, Any]:
    best = None
    for period in range(1, min(MAX_PERIOD, len(seq)) + 1):
        by_state: dict[int, Counter[str]] = defaultdict(Counter)
        for idx, symbol in enumerate(seq):
            by_state[idx % period][symbol] += 1
        template = {state: counts.most_common(1)[0][0] for state, counts in by_state.items()}
        predictions = [template[idx % period] for idx in range(len(seq))]
        correct = sum(pred == symbol for pred, symbol in zip(predictions, seq))
        exceptions = len(seq) - correct
        model_bits = math.log2(MAX_PERIOD) + period * math.log2(len(alphabet))
        exception_bits = exceptions * (math.log2(len(seq)) + math.log2(len(alphabet)))
        row = {
            "period": period,
            "correct": correct,
            "accuracy": correct / len(seq),
            "exceptions": exceptions,
            "mdl_bits_est": model_bits + exception_bits,
            "template": "".join(template[state] for state in range(period)),
        }
        if best is None or (row["accuracy"], -row["mdl_bits_est"], -row["period"]) > (
            best["accuracy"],
            -best["mdl_bits_est"],
            -best["period"],
        ):
            best = row
    return best


def sequence_metrics(seq: list[str], alphabet: list[str]) -> dict[str, Any]:
    kt0 = kt_bits(seq, 0, alphabet)
    kt1 = kt_bits(seq, 1, alphabet)
    kt2 = kt_bits(seq, 2, alphabet)
    return {
        "length": len(seq),
        "inventory": dict(Counter(seq)),
        "kt0_bits": kt0,
        "kt1_bits": kt1,
        "kt2_bits": kt2,
        "kt1_gain_vs_kt0": kt0 - kt1,
        "kt2_gain_vs_kt0": kt0 - kt2,
        "zlib_bytes": len(zlib.compress("".join(seq).encode("ascii"), level=9)),
        "transition": transition_metrics(seq),
        "best_periodic_template": best_periodic_template(seq, alphabet),
    }


def summarize(values: list[float], observed: float, high_is_good: bool) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mean) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mean - observed) / sd if sd else 0.0
    return {"observed": observed, "mean": mean, "sd": sd, "min": min(values), "max": max(values), "z_good": z, "p_good": p}


def analyze_sequence(seq: list[str], alphabet: list[str], rng: random.Random) -> dict[str, Any]:
    observed = sequence_metrics(seq, alphabet)
    control_values = {
        "kt1_gain_vs_kt0": [],
        "kt2_gain_vs_kt0": [],
        "zlib_bytes": [],
        "unique_edges": [],
        "repeated_edge_excess": [],
        "deterministic_step_fraction": [],
        "best_period_accuracy": [],
        "best_period_mdl_bits": [],
    }
    shuffled = seq[:]
    for _ in range(TRIALS):
        rng.shuffle(shuffled)
        current = sequence_metrics(shuffled, alphabet)
        control_values["kt1_gain_vs_kt0"].append(current["kt1_gain_vs_kt0"])
        control_values["kt2_gain_vs_kt0"].append(current["kt2_gain_vs_kt0"])
        control_values["zlib_bytes"].append(current["zlib_bytes"])
        control_values["unique_edges"].append(current["transition"]["unique_edges"])
        control_values["repeated_edge_excess"].append(current["transition"]["repeated_edge_excess"])
        control_values["deterministic_step_fraction"].append(current["transition"]["deterministic_step_fraction"])
        control_values["best_period_accuracy"].append(current["best_periodic_template"]["accuracy"])
        control_values["best_period_mdl_bits"].append(current["best_periodic_template"]["mdl_bits_est"])
    controls = {
        "kt1_gain_vs_kt0": summarize(control_values["kt1_gain_vs_kt0"], observed["kt1_gain_vs_kt0"], True),
        "kt2_gain_vs_kt0": summarize(control_values["kt2_gain_vs_kt0"], observed["kt2_gain_vs_kt0"], True),
        "zlib_bytes": summarize(control_values["zlib_bytes"], observed["zlib_bytes"], False),
        "unique_edges": summarize(control_values["unique_edges"], observed["transition"]["unique_edges"], False),
        "repeated_edge_excess": summarize(
            control_values["repeated_edge_excess"], observed["transition"]["repeated_edge_excess"], True
        ),
        "deterministic_step_fraction": summarize(
            control_values["deterministic_step_fraction"], observed["transition"]["deterministic_step_fraction"], True
        ),
        "best_period_accuracy": summarize(
            control_values["best_period_accuracy"], observed["best_periodic_template"]["accuracy"], True
        ),
        "best_period_mdl_bits": summarize(
            control_values["best_period_mdl_bits"], observed["best_periodic_template"]["mdl_bits_est"], False
        ),
    }
    return {"observed": observed, "controls": controls}


def best_metric_row(order_name: str, family: str, analysis: dict[str, Any]) -> dict[str, Any]:
    observed = analysis["observed"]
    metric_defs = {
        "kt1_gain_vs_kt0": (observed["kt1_gain_vs_kt0"], True),
        "kt2_gain_vs_kt0": (observed["kt2_gain_vs_kt0"], True),
        "zlib_bytes": (observed["zlib_bytes"], False),
        "unique_edges": (observed["transition"]["unique_edges"], False),
        "repeated_edge_excess": (observed["transition"]["repeated_edge_excess"], True),
        "deterministic_step_fraction": (observed["transition"]["deterministic_step_fraction"], True),
        "best_period_accuracy": (observed["best_periodic_template"]["accuracy"], True),
        "best_period_mdl_bits": (observed["best_periodic_template"]["mdl_bits_est"], False),
    }
    rows = []
    for metric, (value, high_is_good) in metric_defs.items():
        ctrl = analysis["controls"][metric]
        rows.append(
            {
                "order": order_name,
                "family": family,
                "metric": metric,
                "observed": value,
                "high_is_good": high_is_good,
                "p_good": ctrl["p_good"],
                "z_good": ctrl["z_good"],
                "control_mean": ctrl["mean"],
            }
        )
    rows.sort(key=lambda row: (row["p_good"], -row["z_good"]))
    return rows[0]


def inventory_bits(seq: list[str]) -> float:
    counts = Counter(seq)
    return math.lgamma(len(seq) + 1) / math.log(2) - sum(math.lgamma(count + 1) / math.log(2) for count in counts.values())


def classify(best: dict[str, Any], upper_best: dict[str, Any], mirror_best: dict[str, Any], periodic_mdl: dict[str, Any]) -> str:
    corrected_p = min(1.0, best["p_good"] * periodic_mdl["search_tests"])
    if (
        best["family"] == "upper_only"
        and corrected_p <= 0.01
        and periodic_mdl["best_period_gain_vs_inventory_bits"] > 0
    ):
        return "candidate_directed_sequence_formula"
    if mirror_best["p_good"] <= 0.01 and upper_best["p_good"] > 0.05:
        return "mirror_render_redundancy_not_origin_formula"
    if corrected_p <= 0.05:
        return "weak_directed_sequence_signal_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    best = result["best_metric"]
    upper = result["best_by_family"].get("upper_only")
    lower = result["best_by_family"].get("lower_only")
    mirror = result["best_by_family"].get("mirror_interleave")
    periodic = result["periodic_mdl"]
    lines = [
        "# Directed Surface Sequence Generator Search",
        "",
        "Generated by `directed_surface_sequence_generator_search.py`.",
        "",
        "This pass tests whether the ordered 00..99 code surface itself behaves",
        "like a generated sequence. It is separate from semantic decoding.",
        "",
        "## Summary",
        "",
        "| Best order | Family | Metric | Observed | Control mean | p | Corrected p | Verdict |",
        "|---|---|---|---:|---:|---:|---:|---|",
        f"| `{best['order']}` | `{best['family']}` | `{best['metric']}` | "
        f"{best['observed']:.3f} | {best['control_mean']:.3f} | "
        f"{best['p_good']:.5f} | {min(1.0, best['p_good'] * result['search_tests']):.5f} | "
        f"`{result['verdict']}` |",
        "",
        "## Family Best Rows",
        "",
        "| Family | Order | Metric | Observed | p | z |",
        "|---|---|---|---:|---:|---:|",
    ]
    for family, row in result["best_by_family"].items():
        lines.append(
            f"| `{family}` | `{row['order']}` | `{row['metric']}` | "
            f"{row['observed']:.3f} | {row['p_good']:.5f} | {row['z_good']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Periodic Template MDL",
            "",
            "| Order | Family | Period | Correct | Template MDL | Inventory bits | Gain |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["periodic_rows"][:12]:
        tmpl = row["best_periodic_template"]
        lines.append(
            f"| `{row['order']}` | `{row['family']}` | {tmpl['period']} | "
            f"{tmpl['correct']}/{row['length']} | {tmpl['mdl_bits_est']:.1f} | "
            f"{row['inventory_bits']:.1f} | {row['period_gain_vs_inventory_bits']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if mirror:
        lines.append(
            "The strongest full directed order is interpreted against the already-known mirror render layer. "
            f"Mirror-family best p is `{mirror['p_good']:.5f}`; upper-only best p is "
            f"`{upper['p_good']:.5f}`. A signal confined to mirror/full-directed orders does not derive the upper table."
        )
    if lower:
        lines.append(
            f"Lower-only best p is `{lower['p_good']:.5f}`; this reflects render redundancy unless it transfers to upper-only cells."
        )
    lines.extend(
        [
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    directed = load_json(DIRECTED_SURFACE_JSON)
    code_to_symbol = formula["code_to_symbol"]
    alphabet = sorted(set(code_to_symbol.values()))
    rng = random.Random(RANDOM_SEED)
    order_specs = directed_orders(code_to_symbol)
    order_results = []
    metric_rows = []
    periodic_rows = []
    for order_name, spec in order_specs.items():
        seq = [code_to_symbol[code] for code in spec["codes"]]
        analysis = analyze_sequence(seq, alphabet, rng)
        row = {
            "order": order_name,
            "family": spec["family"],
            "codes": spec["codes"],
            "length": len(seq),
            "analysis": analysis,
        }
        order_results.append(row)
        metric_rows.append(best_metric_row(order_name, spec["family"], analysis))
        period = analysis["observed"]["best_periodic_template"]
        inv_bits = inventory_bits(seq)
        periodic_rows.append(
            {
                "order": order_name,
                "family": spec["family"],
                "length": len(seq),
                "best_periodic_template": period,
                "inventory_bits": inv_bits,
                "period_gain_vs_inventory_bits": inv_bits - period["mdl_bits_est"],
            }
        )
    metric_rows.sort(key=lambda row: (row["p_good"], -row["z_good"]))
    best = metric_rows[0]
    best_by_family = {}
    for family in sorted({row["family"] for row in metric_rows}):
        rows = [row for row in metric_rows if row["family"] == family]
        rows.sort(key=lambda row: (row["p_good"], -row["z_good"]))
        best_by_family[family] = rows[0]
    periodic_rows.sort(key=lambda row: (-row["period_gain_vs_inventory_bits"], row["best_periodic_template"]["mdl_bits_est"]))
    periodic_mdl = {
        "best_period_gain_vs_inventory_bits": periodic_rows[0]["period_gain_vs_inventory_bits"],
        "best_period_order": periodic_rows[0]["order"],
        "best_period_family": periodic_rows[0]["family"],
        "search_tests": len(metric_rows) * 8,
    }
    result = {
        "schema": "directed_surface_sequence_generator_results.v1",
        "source": {
            "formula": str(FORMULA_JSON.relative_to(ROOT)),
            "directed_surface": str(DIRECTED_SURFACE_JSON.relative_to(ROOT)),
        },
        "random_seed": RANDOM_SEED,
        "control_trials": TRIALS,
        "search_tests": len(metric_rows) * 8,
        "target": {
            "ordered_present_codes": len(code_to_symbol),
            "missing_code": "39",
            "alphabet": alphabet,
            "directed_surface_classification": directed["conclusion"]["classification"],
        },
        "best_metric": best,
        "best_by_family": best_by_family,
        "metric_rows": metric_rows,
        "periodic_rows": periodic_rows,
        "periodic_mdl": periodic_mdl,
        "orders": order_results,
        "verdict": classify(
            best,
            best_by_family.get("upper_only", {"p_good": 1.0}),
            best_by_family.get("mirror_interleave", {"p_good": 1.0}),
            periodic_mdl,
        ),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "verdict={verdict} best={order}/{metric} p={p:.5f}".format(
            verdict=result["verdict"],
            order=best["order"],
            metric=best["metric"],
            p=best["p_good"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
