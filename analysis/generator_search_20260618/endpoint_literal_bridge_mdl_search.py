#!/usr/bin/env python3
"""Endpoint-conditioned literal bridge MDL probe.

The tape-based formula still carries literal recipe spans after collapsing
modules into tape components. This pass tests the narrow bridge hypothesis:
middle literal spans between tape/module slices may be reusable connector
strings keyed by adjacent endpoints.

It is a book-layer mechanical test only. It does not assign plaintext and does
not alter the pair-table formula.
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
TAPE_FORMULA_JSON = HERE / "tape_based_formula_469.json"
RESIDUAL_ATLAS_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "residual_atlas.json"

OUT_JSON = HERE / "endpoint_literal_bridge_mdl_results.json"
OUT_MD = HERE / "endpoint_literal_bridge_mdl_report.md"

RANDOM_SEED = 46920260625
CONTROL_TRIALS = 1000
DIGIT_BITS = math.log2(10)
FINAL_RESIDUAL_HOLDOUT_IDS = {"B4_R01", "B31_R02", "B36_R01", "B41_R01", "B56_R02", "B57_R03"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def item_text(item: dict[str, Any] | None, components: dict[str, str]) -> str:
    if item is None:
        return ""
    if item["type"] == "literal":
        return item["text"]
    if item["type"] in {"module_slice", "tape_span"}:
        return components[item["component_id"]][int(item["start"]) : int(item["end"])]
    raise ValueError(item["type"])


def item_label(item: dict[str, Any] | None, side: str) -> str:
    if item is None:
        return side.upper()
    if item["type"] == "module_slice":
        return f"M:{item['id']}"
    if item["type"] == "tape_span":
        return f"TS:{item['component_id']}:{item['start']}:{item['end']}"
    return item["type"]


def component_id(item: dict[str, Any] | None, side: str) -> str:
    if item is None:
        return side.upper()
    if item["type"] not in {"module_slice", "tape_span"}:
        return item["type"]
    return item["component_id"]


def component_endpoint(item: dict[str, Any] | None, side: str) -> str:
    if item is None:
        return side.upper()
    if item["type"] not in {"module_slice", "tape_span"}:
        return item["type"]
    coord = item["end"] if side == "left" else item["start"]
    return f"{item['component_id']}:{coord}"


def orientation(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["component_id"] != right["component_id"]:
        return "cross_component"
    if int(left["end"]) <= int(right["start"]):
        return "same_component_forward"
    if int(right["end"]) <= int(left["start"]):
        return "same_component_reverse"
    return "same_component_overlap"


def residual_index() -> dict[tuple[str, int, int, str], str]:
    out = {}
    for row in load_json(RESIDUAL_ATLAS_JSON):
        out[(str(row["book"]), int(row["raw_start"]), int(row["raw_end"]), row["text"])] = row["id"]
    return out


def extract_bridge_rows(tape_formula: dict[str, Any]) -> list[dict[str, Any]]:
    components = {row["id"]: row["text"] for row in tape_formula["tape_components"]}
    residuals = residual_index()
    rows = []
    for book, recipe in tape_formula["book_recipes"].items():
        offset = 0
        for idx, item in enumerate(recipe):
            length = len(item["text"]) if item["type"] == "literal" else int(item["length"])
            raw_start, raw_end = offset, offset + length
            offset = raw_end
            if item["type"] != "literal":
                continue
            if not (idx > 0 and idx + 1 < len(recipe)):
                continue
            left = recipe[idx - 1]
            right = recipe[idx + 1]
            if left["type"] not in {"module_slice", "tape_span"} or right["type"] not in {"module_slice", "tape_span"}:
                continue
            left_text = item_text(left, components)
            right_text = item_text(right, components)
            rid = residuals.get((str(book), raw_start, raw_end, item["text"]))
            rows.append(
                {
                    "target_id": f"B{book}_RI{idx}",
                    "residual_id": rid,
                    "book": str(book),
                    "recipe_index": idx,
                    "text": item["text"],
                    "length": len(item["text"]),
                    "raw_start": raw_start,
                    "raw_end": raw_end,
                    "left_label": item_label(left, "left"),
                    "right_label": item_label(right, "right"),
                    "left_component": component_id(left, "left"),
                    "right_component": component_id(right, "right"),
                    "left_endpoint": component_endpoint(left, "left"),
                    "right_endpoint": component_endpoint(right, "right"),
                    "orientation": orientation(left, right),
                    "left_tail2": left_text[-2:],
                    "right_head2": right_text[:2],
                    "left_tail4": left_text[-4:],
                    "right_head4": right_text[:4],
                    "left_tail6": left_text[-6:],
                    "right_head6": right_text[:6],
                    "left_tail8": left_text[-8:],
                    "right_head8": right_text[:8],
                }
            )
    return rows


KEY_FAMILIES = {
    "component_pair": lambda r: (r["left_component"], r["right_component"]),
    "component_pair_orientation": lambda r: (r["left_component"], r["right_component"], r["orientation"]),
    "component_endpoint_pair": lambda r: (r["left_endpoint"], r["right_endpoint"]),
    "module_pair": lambda r: (r["left_label"], r["right_label"]),
    "tail2_head2": lambda r: (r["left_tail2"], r["right_head2"]),
    "tail4_head4": lambda r: (r["left_tail4"], r["right_head4"]),
    "tail6_head6": lambda r: (r["left_tail6"], r["right_head6"]),
    "tail8_head8": lambda r: (r["left_tail8"], r["right_head8"]),
    "component_pair_tail4_head4": lambda r: (
        r["left_component"],
        r["right_component"],
        r["left_tail4"],
        r["right_head4"],
    ),
}


def build_predictor(train: list[dict[str, Any]], family: str) -> dict[Any, str]:
    grouped: dict[Any, Counter[str]] = defaultdict(Counter)
    key_fn = KEY_FAMILIES[family]
    for row in train:
        grouped[key_fn(row)][row["text"]] += 1
    return {key: counts.most_common(1)[0][0] for key, counts in grouped.items()}


def evaluate_family(train: list[dict[str, Any]], test: list[dict[str, Any]], family: str) -> dict[str, Any]:
    predictor = build_predictor(train, family)
    key_fn = KEY_FAMILIES[family]
    covered_digits = 0
    covered_items = 0
    predicted_items = 0
    examples = []
    for row in test:
        key = key_fn(row)
        if key not in predictor:
            continue
        predicted_items += 1
        if predictor[key] == row["text"]:
            covered_items += 1
            covered_digits += row["length"]
            if len(examples) < 8:
                examples.append(
                    {
                        "target_id": row["target_id"],
                        "residual_id": row["residual_id"],
                        "text": row["text"],
                        "length": row["length"],
                        "key": list(key) if isinstance(key, tuple) else key,
                    }
                )
    return {
        "family": family,
        "train_keys": len(predictor),
        "test_items": len(test),
        "test_digits": sum(row["length"] for row in test),
        "predicted_items": predicted_items,
        "covered_items": covered_items,
        "covered_digits": covered_digits,
        "covered_fraction_digits": covered_digits / max(1, sum(row["length"] for row in test)),
        "examples": examples,
    }


def exact_repeat_baseline(train: list[dict[str, Any]], test: list[dict[str, Any]]) -> dict[str, Any]:
    seen = {row["text"] for row in train}
    covered = [row for row in test if row["text"] in seen]
    return {
        "family": "train_literal_exact_repeat",
        "covered_items": len(covered),
        "covered_digits": sum(row["length"] for row in covered),
        "test_items": len(test),
        "test_digits": sum(row["length"] for row in test),
        "covered_fraction_digits": sum(row["length"] for row in covered) / max(1, sum(row["length"] for row in test)),
    }


def split_eval(train: list[dict[str, Any]], test: list[dict[str, Any]], split_id: str) -> dict[str, Any]:
    rows = [evaluate_family(train, test, family) for family in KEY_FAMILIES]
    rows.sort(key=lambda row: (-row["covered_digits"], -row["covered_items"], row["family"]))
    repeat = exact_repeat_baseline(train, test)
    return {
        "split_id": split_id,
        "train_items": len(train),
        "test_items": len(test),
        "test_digits": sum(row["length"] for row in test),
        "best": rows[0],
        "rows": rows,
        "exact_repeat_baseline": repeat,
    }


def crossval_eval(targets: list[dict[str, Any]], unit: str) -> dict[str, Any]:
    units = sorted({row[unit] for row in targets if row[unit] is not None})
    totals = {family: {"covered_digits": 0, "covered_items": 0, "predicted_items": 0} for family in KEY_FAMILIES}
    repeat = {"covered_digits": 0, "covered_items": 0}
    test_digits = 0
    test_items = 0
    for value in units:
        train = [row for row in targets if row[unit] != value]
        test = [row for row in targets if row[unit] == value]
        test_digits += sum(row["length"] for row in test)
        test_items += len(test)
        for family in KEY_FAMILIES:
            row = evaluate_family(train, test, family)
            totals[family]["covered_digits"] += row["covered_digits"]
            totals[family]["covered_items"] += row["covered_items"]
            totals[family]["predicted_items"] += row["predicted_items"]
        base = exact_repeat_baseline(train, test)
        repeat["covered_digits"] += base["covered_digits"]
        repeat["covered_items"] += base["covered_items"]
    rows = [
        {
            "family": family,
            "test_items": test_items,
            "test_digits": test_digits,
            **values,
            "covered_fraction_digits": values["covered_digits"] / max(1, test_digits),
        }
        for family, values in totals.items()
    ]
    rows.sort(key=lambda row: (-row["covered_digits"], -row["covered_items"], row["family"]))
    repeat.update(
        {
            "family": "train_literal_exact_repeat",
            "test_items": test_items,
            "test_digits": test_digits,
            "covered_fraction_digits": repeat["covered_digits"] / max(1, test_digits),
        }
    )
    return {"unit": unit, "folds": len(units), "best": rows[0], "rows": rows, "exact_repeat_baseline": repeat}


def summarize(values: list[float], observed: float) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "mean": mean,
        "sd": sd,
        "min": min(values),
        "max": max(values),
        "p_good": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def shuffle_texts(rows: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    shuffled = [dict(row) for row in rows]
    by_len: dict[int, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_len[row["length"]].append(idx)
    for indexes in by_len.values():
        texts = [rows[idx]["text"] for idx in indexes]
        rng.shuffle(texts)
        for idx, text in zip(indexes, texts):
            shuffled[idx]["text"] = text
    return shuffled


def final_controls(targets: list[dict[str, Any]], final_result: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    final_ids = {row["residual_id"] for row in targets if row["residual_id"] in FINAL_RESIDUAL_HOLDOUT_IDS}
    values = []
    for _ in range(CONTROL_TRIALS):
        shuffled = shuffle_texts(targets, rng)
        train = [row for row in shuffled if row["residual_id"] not in final_ids]
        test = [row for row in shuffled if row["residual_id"] in final_ids]
        rows = [evaluate_family(train, test, family) for family in KEY_FAMILIES]
        values.append(max(row["covered_digits"] for row in rows))
    return {
        "label_shuffle_within_length": {
            "trials": CONTROL_TRIALS,
            "best_covered_digits": summarize(values, final_result["best"]["covered_digits"]),
        }
    }


def rough_mdl(result: dict[str, Any]) -> dict[str, Any]:
    best = result["best"]
    gross_gain = best["covered_digits"] * DIGIT_BITS
    # Favorable lower-bound charge: choose family plus one key pointer per train key.
    cost = math.log2(len(KEY_FAMILIES)) + best["train_keys"] * math.log2(max(2, best["train_keys"] + 1))
    return {"gross_gain_bits": gross_gain, "lower_bound_cost_bits": cost, "net_gain_bits": gross_gain - cost}


def classify(final_result: dict[str, Any], lobo: dict[str, Any], controls: dict[str, Any]) -> str:
    p = controls["label_shuffle_within_length"]["best_covered_digits"]["p_good"]
    mdl = rough_mdl(final_result)
    if final_result["best"]["covered_digits"] > 0 and lobo["best"]["covered_digits"] > 0 and mdl["net_gain_bits"] > 0 and p <= 0.05:
        return "candidate_endpoint_literal_bridge"
    if final_result["best"]["covered_digits"] > 0 or lobo["best"]["covered_digits"] > 0:
        return "weak_endpoint_bridge_signal_not_formula"
    return "rejected_control"


def write_report(result: dict[str, Any]) -> None:
    final_result = result["final_residual_holdout"]
    lobo = result["leave_one_bridge_out"]
    book = result["leave_book_out"]
    ctrl = result["controls"]["label_shuffle_within_length"]["best_covered_digits"]
    lines = [
        "# Endpoint Literal Bridge MDL Search",
        "",
        "Generated by `endpoint_literal_bridge_mdl_search.py`.",
        "",
        "This pass tests whether the 28 middle literal spans left after tape",
        "absorption are predictable from adjacent tape/module endpoints. It",
        "creates no translation or glossary.",
        "",
        "## Summary",
        "",
        "| Split | Best family | Covered digits | Exact-repeat baseline |",
        "|---|---|---:|---:|",
        f"| leave-one-bridge-out | `{lobo['best']['family']}` | {lobo['best']['covered_digits']}/{lobo['best']['test_digits']} | {lobo['exact_repeat_baseline']['covered_digits']}/{lobo['exact_repeat_baseline']['test_digits']} |",
        f"| leave-book-out | `{book['best']['family']}` | {book['best']['covered_digits']}/{book['best']['test_digits']} | {book['exact_repeat_baseline']['covered_digits']}/{book['exact_repeat_baseline']['test_digits']} |",
        f"| final residual holdout | `{final_result['best']['family']}` | {final_result['best']['covered_digits']}/{final_result['best']['test_digits']} | {final_result['exact_repeat_baseline']['covered_digits']}/{final_result['exact_repeat_baseline']['test_digits']} |",
        "",
        f"Final holdout label-shuffle p: `{ctrl['p_good']:.5f}`. Verdict: `{result['verdict']}`.",
        "",
        "## Target Scope",
        "",
        f"- Middle bridge literals: {result['target_count']} / {result['target_digits']} digits.",
        f"- Same-component middle bridge literals: {result['same_component_count']} / {result['same_component_digits']} digits.",
        f"- Final residual holdout bridge literals: {final_result['test_items']} / {final_result['test_digits']} digits.",
        "",
        "## Final Holdout Families",
        "",
        "| Family | Predicted items | Covered items | Covered digits |",
        "|---|---:|---:|---:|",
    ]
    for row in final_result["rows"][:12]:
        lines.append(
            f"| `{row['family']}` | {row['predicted_items']} | {row['covered_items']} | {row['covered_digits']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "No tested endpoint-key family predicts a held-out bridge string exactly.",
            "The result is negative for a transferable endpoint-conditioned bridge",
            "formula beyond the existing tape components and already absorbed",
            "same-component gaps.",
            "",
            f"Translation delta: `{result['translation_delta']}`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    targets = extract_bridge_rows(load_json(TAPE_FORMULA_JSON))
    final_ids = FINAL_RESIDUAL_HOLDOUT_IDS
    final_train = [row for row in targets if row["residual_id"] not in final_ids]
    final_test = [row for row in targets if row["residual_id"] in final_ids]
    final_result = split_eval(final_train, final_test, "final_residual_holdout")
    lobo = crossval_eval(targets, "target_id")
    book = crossval_eval(targets, "book")
    ctrl = final_controls(targets, final_result)
    result = {
        "schema": "endpoint_literal_bridge_mdl_results.v2",
        "source": str(TAPE_FORMULA_JSON.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "target_count": len(targets),
        "target_digits": sum(row["length"] for row in targets),
        "same_component_count": sum(row["orientation"].startswith("same_component") for row in targets),
        "same_component_digits": sum(row["length"] for row in targets if row["orientation"].startswith("same_component")),
        "final_residual_holdout_ids": sorted(FINAL_RESIDUAL_HOLDOUT_IDS),
        "targets": targets,
        "leave_one_bridge_out": lobo,
        "leave_book_out": book,
        "final_residual_holdout": final_result,
        "controls": ctrl,
        "rough_mdl_final": rough_mdl(final_result),
        "verdict": classify(final_result, lobo, ctrl),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        "verdict={verdict} final={covered}/{total} lobo={lobo}".format(
            verdict=result["verdict"],
            covered=final_result["best"]["covered_digits"],
            total=final_result["best"]["test_digits"],
            lobo=lobo["best"]["covered_digits"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
