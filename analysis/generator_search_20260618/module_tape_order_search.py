#!/usr/bin/env python3
"""Order-signal search for overlap-tape components.

The overlap-tape grammar is useful, but it could still be a compression
artifact. This pass asks whether the order of module slices inside each tape
is predicted by simple operational signals: module id, first book occurrence,
first offset, length, or reuse count.

Mechanical only. No plaintext is promoted.
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OVERLAP_JSON = HERE / "module_overlap_grammar_results.json"

OUT_JSON = HERE / "module_tape_order_results.json"
OUT_MD = HERE / "module_tape_order_report.md"

RANDOM_SEED = 46920260623
CONTROL_TRIALS = 20000


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def module_number(module_id: str) -> int:
    return int(module_id.removeprefix("M"))


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = (index + end - 1) / 2.0
        for pos in range(index, end):
            result[order[pos]] = rank
        index = end
    return result


def spearman(left: list[float], right: list[float]) -> float:
    if len(left) < 3:
        return 0.0
    a = ranks(left)
    b = ranks(right)
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denom_a = sum((x - mean_a) ** 2 for x in a)
    denom_b = sum((y - mean_b) ** 2 for y in b)
    denom = math.sqrt(denom_a * denom_b)
    return numerator / denom if denom else 0.0


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


def first_occurrence(module: dict) -> tuple[int, int]:
    return min((int(item["book"]), int(item["offset"])) for item in module["occurrences"])


def build_rows(formula: dict, overlap: dict) -> list[dict]:
    modules = {module["id"]: module for module in formula["modules"]}
    rows = []
    for item in overlap["best_overlap_tape_model"]["module_slices"]:
        module = modules[item["module_id"]]
        first_book, first_offset = first_occurrence(module)
        rows.append(
            {
                "component_id": item["component_id"],
                "module_id": item["module_id"],
                "start": item["start"],
                "end": item["end"],
                "module_number": module_number(item["module_id"]),
                "module_length": module["length"],
                "occurrence_count": len(module["occurrences"]),
                "first_book": first_book,
                "first_offset": first_offset,
                "first_occurrence_key": first_book * 1000 + first_offset,
            }
        )
    return rows


def component_correlations(rows: list[dict]) -> list[dict]:
    by_component: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_component[row["component_id"]].append(row)
    features = [
        "module_number",
        "module_length",
        "occurrence_count",
        "first_book",
        "first_offset",
        "first_occurrence_key",
    ]
    out = []
    for component_id, component_rows in sorted(by_component.items()):
        if len(component_rows) < 3:
            continue
        starts = [row["start"] for row in component_rows]
        for feature in features:
            values = [row[feature] for row in component_rows]
            rho = spearman(starts, values)
            out.append(
                {
                    "component_id": component_id,
                    "slice_count": len(component_rows),
                    "feature": feature,
                    "spearman": rho,
                    "abs_spearman": abs(rho),
                }
            )
    out.sort(key=lambda row: (-row["abs_spearman"], row["component_id"], row["feature"]))
    return out


def t00_control(rows: list[dict], observed_rows: list[dict]) -> dict:
    rng = random.Random(RANDOM_SEED)
    t00 = [row for row in rows if row["component_id"] == "T00"]
    starts = [row["start"] for row in t00]
    feature_names = sorted({row["feature"] for row in observed_rows})
    observed_by_feature = {
        row["feature"]: row for row in observed_rows if row["component_id"] == "T00"
    }
    controls: dict[str, list[float]] = {feature: [] for feature in feature_names}
    for _trial in range(CONTROL_TRIALS):
        for feature in feature_names:
            values = [row[feature] for row in t00]
            rng.shuffle(values)
            controls[feature].append(abs(spearman(starts, values)))
    rows_out = []
    for feature in feature_names:
        observed = observed_by_feature[feature]["abs_spearman"]
        summary = summarize(controls[feature], observed)
        rows_out.append(
            {
                "component_id": "T00",
                "feature": feature,
                **summary,
                "bonferroni_p": min(1.0, summary["p_good_direction"] * len(feature_names)),
            }
        )
    rows_out.sort(key=lambda row: row["bonferroni_p"])
    return {"feature_rows": rows_out, "best": rows_out[0]}


def write_report(result: dict) -> None:
    lines = [
        "# Module Tape Order Search",
        "",
        "Generated by `module_tape_order_search.py`.",
        "",
        "This pass tests whether the order of module slices inside overlap-tape",
        "components follows simple operational signals. It is mechanical only.",
        "",
        "## Strongest Correlations",
        "",
        "| Component | Slices | Feature | Spearman | Verdict |",
        "|---|---:|---|---:|---|",
    ]
    for row in result["component_correlation_rows"][:20]:
        verdict = "candidate" if row["component_id"] == "T00" and row["feature"] == result["t00_control"]["best"]["feature"] and result["t00_control"]["best"]["bonferroni_p"] <= 0.01 else "not_promoted"
        lines.append(
            f"| `{row['component_id']}` | {row['slice_count']} | `{row['feature']}` | "
            f"{row['spearman']:.3f} | `{verdict}` |"
        )
    lines += [
        "",
        "## T00 Permutation Control",
        "",
        "| Feature | Abs rho | Control mean | p | Bonferroni p |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["t00_control"]["feature_rows"]:
        lines.append(
            f"| `{row['feature']}` | {row['observed']:.3f} | {row['control_mean']:.3f} | "
            f"{row['p_good_direction']:.5f} | {row['bonferroni_p']:.5f} |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_tape_order_signal":
        lines.append("A simple ordering signal survived controls. Treat as mechanical only.")
    else:
        lines.append(
            "No simple module-id, first-occurrence, length, or reuse-count signal "
            "explains the internal order of `T00`. The large tape remains a useful "
            "overlap component, but not yet an independently recovered original order."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    overlap = load_json(OVERLAP_JSON)
    rows = build_rows(formula, overlap)
    correlation_rows = component_correlations(rows)
    control = t00_control(rows, correlation_rows)
    verdict = "candidate_tape_order_signal" if control["best"]["bonferroni_p"] <= 0.01 else "rejected_control"
    result = {
        "schema": "module_tape_order_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "component_correlation_rows": correlation_rows,
        "t00_control": control,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best_feature={control['best']['feature']} "
        f"rho={control['best']['observed']:.3f} bonferroni={control['best']['bonferroni_p']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
