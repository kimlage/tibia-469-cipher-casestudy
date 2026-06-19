#!/usr/bin/env python3
"""Overlap-grammar search for the 469 module inventory.

The frozen mechanical model stores 62 long numeric modules literally. This pass
asks whether those modules look like slices of a smaller generating tape:
suffix/prefix overlaps, containments, or repeated internal motifs.

The test is mechanical only. It never assigns plaintext.
"""

from __future__ import annotations

import heapq
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"

OUT_JSON = HERE / "module_overlap_grammar_results.json"
OUT_MD = HERE / "module_overlap_grammar_report.md"

RANDOM_SEED = 46920260622
CONTROL_TRIALS = 200
THRESHOLDS = [8, 12, 16, 20, 32]
SUBSTRING_LENGTHS = [8, 12, 16, 20, 32]
LOG2_10 = math.log2(10)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ceil_log2(value: int) -> int:
    return max(1, math.ceil(math.log2(max(2, value))))


def suffix_prefix_overlap(left: str, right: str) -> int:
    """Longest suffix of left that is also a prefix of right."""
    max_len = min(len(left), len(right))
    if max_len == 0:
        return 0
    hay = right[:max_len] + "#" + left[-max_len:]
    pi = [0] * len(hay)
    for index in range(1, len(hay)):
        candidate = pi[index - 1]
        while candidate and hay[index] != hay[candidate]:
            candidate = pi[candidate - 1]
        if hay[index] == hay[candidate]:
            candidate += 1
        pi[index] = candidate
    return min(pi[-1], max_len)


def best_pair_edges(left_id: int, left: str, right_id: int, right: str) -> list[tuple[int, str, int, int]]:
    edges: list[tuple[int, str, int, int]] = []
    if right in left:
        edges.append((len(right), "contain_left", left_id, right_id))
    if left in right:
        edges.append((len(left), "contain_right", left_id, right_id))
    lr = suffix_prefix_overlap(left, right)
    if lr:
        edges.append((lr, "overlap_lr", left_id, right_id))
    rl = suffix_prefix_overlap(right, left)
    if rl:
        edges.append((rl, "overlap_rl", left_id, right_id))
    return edges


def merged_text(kind: str, left: str, right: str, saving: int) -> str:
    if kind == "contain_left":
        return left
    if kind == "contain_right":
        return right
    if kind == "overlap_lr":
        return left + right[saving:]
    if kind == "overlap_rl":
        return right + left[saving:]
    raise ValueError(kind)


def locate_modules(component_texts: list[str], texts: list[str]) -> list[dict]:
    slices = []
    for index, text in enumerate(texts):
        hits = []
        for component_index, component_text in enumerate(component_texts):
            start = component_text.find(text)
            if start >= 0:
                hits.append(
                    {
                        "module_index": index,
                        "component_id": f"T{component_index:02d}",
                        "start": start,
                        "end": start + len(text),
                    }
                )
        if not hits:
            raise ValueError(f"module index {index} is not contained in the overlap components")
        slices.append(hits[0])
    return slices


def greedy_overlap_grammar(texts: list[str], min_overlap: int, include_components: bool = False) -> dict:
    """Greedy shortest-common-superstring approximation with a minimum overlap."""
    active: dict[int, str] = {index: text for index, text in enumerate(texts)}
    next_id = len(active)
    heap: list[tuple[int, int, str, int, int]] = []
    tie = 0

    def push_edges(new_id: int) -> None:
        nonlocal tie
        new_text = active[new_id]
        for other_id, other_text in active.items():
            if other_id == new_id:
                continue
            left_id, right_id = sorted((new_id, other_id))
            left, right = active[left_id], active[right_id]
            for saving, kind, edge_left, edge_right in best_pair_edges(left_id, left, right_id, right):
                if saving >= min_overlap:
                    heapq.heappush(heap, (-saving, tie, kind, edge_left, edge_right))
                    tie += 1

    ids = sorted(active)
    for pos, left_id in enumerate(ids):
        for right_id in ids[pos + 1 :]:
            for saving, kind, edge_left, edge_right in best_pair_edges(left_id, active[left_id], right_id, active[right_id]):
                if saving >= min_overlap:
                    heapq.heappush(heap, (-saving, tie, kind, edge_left, edge_right))
                    tie += 1

    operations = []
    while heap:
        neg_saving, _tie, kind, left_id, right_id = heapq.heappop(heap)
        saving = -neg_saving
        if saving < min_overlap:
            break
        if left_id not in active or right_id not in active:
            continue
        left, right = active[left_id], active[right_id]
        current_edges = best_pair_edges(left_id, left, right_id, right)
        valid = [edge for edge in current_edges if edge[0] == saving and edge[1] == kind]
        if not valid:
            continue
        text = merged_text(kind, left, right, saving)
        operations.append({"left_id": left_id, "right_id": right_id, "kind": kind, "saving": saving, "merged_length": len(text)})
        del active[left_id]
        del active[right_id]
        active[next_id] = text
        push_edges(next_id)
        next_id += 1

    component_texts = sorted(active.values(), key=lambda text: (-len(text), text))
    component_lengths = [len(text) for text in component_texts]
    total_digits = sum(len(text) for text in texts)
    tape_digits = sum(component_lengths)
    max_component_len = max(component_lengths) if component_lengths else 0
    max_module_len = max(len(text) for text in texts) if texts else 0
    baseline_bits = total_digits * LOG2_10
    address_bits = len(texts) * (
        ceil_log2(len(component_lengths)) + ceil_log2(max_component_len + 1) + ceil_log2(max_module_len + 1)
    )
    grammar_bits = tape_digits * LOG2_10 + address_bits
    result = {
        "min_overlap": min_overlap,
        "total_digits": total_digits,
        "tape_digits": tape_digits,
        "gross_savings_digits": total_digits - tape_digits,
        "baseline_bits": baseline_bits,
        "grammar_bits": grammar_bits,
        "address_bits": address_bits,
        "rough_mdl_gain_bits": baseline_bits - grammar_bits,
        "component_count": len(component_lengths),
        "component_lengths_top10": component_lengths[:10],
        "merge_count": len(operations),
        "operations_top20": operations[:20],
    }
    if include_components:
        result["component_texts"] = [
            {"component_id": f"T{index:02d}", "length": len(text), "text": text}
            for index, text in enumerate(component_texts)
        ]
        result["module_slices"] = locate_modules(component_texts, texts)
    return result


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
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
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def shuffled_modules(texts: list[str], rng: random.Random) -> list[str]:
    out = []
    for text in texts:
        chars = list(text)
        rng.shuffle(chars)
        out.append("".join(chars))
    return out


def resampled_modules(texts: list[str], rng: random.Random) -> list[str]:
    counts = Counter("".join(texts))
    digits = sorted(counts)
    weights = [counts[digit] for digit in digits]
    return ["".join(rng.choices(digits, weights=weights, k=len(text))) for text in texts]


def pairwise_top_edges(module_rows: list[dict], min_overlap: int = 8) -> list[dict]:
    out = []
    for i, left in enumerate(module_rows):
        for j, right in enumerate(module_rows):
            if i == j:
                continue
            saving = suffix_prefix_overlap(left["text"], right["text"])
            if saving >= min_overlap:
                out.append(
                    {
                        "from": left["id"],
                        "to": right["id"],
                        "overlap": saving,
                        "from_length": len(left["text"]),
                        "to_length": len(right["text"]),
                    }
                )
    out.sort(key=lambda row: (-row["overlap"], row["from"], row["to"]))
    return out[:25]


def shared_substring_stats(module_rows: list[dict], lengths: list[int] = SUBSTRING_LENGTHS) -> list[dict]:
    rows = []
    for length in lengths:
        by_sub: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for module in module_rows:
            text = module["text"]
            for pos in range(0, len(text) - length + 1):
                by_sub[text[pos : pos + length]].append((module["id"], pos))
        reused = []
        for sub, hits in by_sub.items():
            module_ids = {module_id for module_id, _pos in hits}
            if len(module_ids) >= 2:
                reused.append((sub, hits, module_ids))
        rows.append(
            {
                "length": length,
                "reused_unique": len(reused),
                "reused_occurrences": sum(len(hits) for _sub, hits, _module_ids in reused),
                "max_occurrences": max((len(hits) for _sub, hits, _module_ids in reused), default=0),
                "max_module_span": max((len(module_ids) for _sub, _hits, module_ids in reused), default=0),
                "examples": [
                    {
                        "substring": sub,
                        "occurrences": len(hits),
                        "modules": sorted(module_ids)[:10],
                    }
                    for sub, hits, module_ids in sorted(reused, key=lambda item: (-len(item[1]), item[0]))[:10]
                ],
            }
        )
    return rows


def control_rows(texts: list[str], thresholds: list[int], observed_by_threshold: dict[int, dict]) -> dict:
    rng = random.Random(RANDOM_SEED)
    controls = {
        "per_module_digit_shuffle": {threshold: {"gross": [], "mdl": []} for threshold in thresholds},
        "global_digit_resample": {threshold: {"gross": [], "mdl": []} for threshold in thresholds},
    }
    for _trial in range(CONTROL_TRIALS):
        for control_name, control_texts in {
            "per_module_digit_shuffle": shuffled_modules(texts, rng),
            "global_digit_resample": resampled_modules(texts, rng),
        }.items():
            for threshold in thresholds:
                result = greedy_overlap_grammar(control_texts, threshold)
                controls[control_name][threshold]["gross"].append(result["gross_savings_digits"])
                controls[control_name][threshold]["mdl"].append(result["rough_mdl_gain_bits"])

    rows = {}
    for threshold in thresholds:
        rows[threshold] = {}
        observed = observed_by_threshold[threshold]
        for control_name in controls:
            rows[threshold][control_name] = {
                "gross_savings_digits": summarize(
                    controls[control_name][threshold]["gross"],
                    observed["gross_savings_digits"],
                    high_is_good=True,
                ),
                "rough_mdl_gain_bits": summarize(
                    controls[control_name][threshold]["mdl"],
                    observed["rough_mdl_gain_bits"],
                    high_is_good=True,
                ),
            }
    return rows


def shared_substring_controls(texts: list[str], observed_rows: list[dict]) -> list[dict]:
    rng = random.Random(RANDOM_SEED + 1)
    values = {row["length"]: [] for row in observed_rows}
    for _trial in range(CONTROL_TRIALS):
        modules = [{"id": f"C{idx:02d}", "text": text} for idx, text in enumerate(shuffled_modules(texts, rng))]
        for row in shared_substring_stats(modules):
            values[row["length"]].append(row["reused_unique"])
    out = []
    observed_by_length = {row["length"]: row for row in observed_rows}
    for length, vals in values.items():
        observed = observed_by_length[length]["reused_unique"]
        out.append({"length": length, **summarize(vals, observed, high_is_good=True)})
    return out


def write_report(result: dict) -> None:
    lines = [
        "# Module Overlap Grammar Search",
        "",
        "Generated by `module_overlap_grammar_search.py`.",
        "",
        "This pass tests whether the 62 stored numeric modules can be replaced by",
        "a smaller overlap tape/grammar. It is mechanical only and promotes no",
        "plaintext.",
        "",
        "## Overlap Superstring",
        "",
        "| Min overlap | Gross saved digits | Components | Rough MDL gain bits | Shuffle p(MDL) | Resample p(MDL) | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["threshold_rows"]:
        lines.append(
            f"| {row['min_overlap']} | {row['gross_savings_digits']} | {row['component_count']} | "
            f"{row['rough_mdl_gain_bits']:.1f} | "
            f"{row['controls']['per_module_digit_shuffle']['rough_mdl_gain_bits']['p_good_direction']:.5f} | "
            f"{row['controls']['global_digit_resample']['rough_mdl_gain_bits']['p_good_direction']:.5f} | "
            f"`{row['verdict']}` |"
        )
    lines += [
        "",
        "The MDL estimate charges one common tape plus component/start/length",
        "addresses for each original module. Gross overlap alone is therefore not",
        "accepted as a generator.",
        "",
        "## Top Suffix-Prefix Edges",
        "",
        "| From | To | Overlap digits |",
        "|---|---|---:|",
    ]
    for edge in result["top_suffix_prefix_edges"]:
        lines.append(f"| `{edge['from']}` | `{edge['to']}` | {edge['overlap']} |")
    lines += [
        "",
        "## Internal Reused Motifs",
        "",
        "| Length | Reused unique substrings | Occurrences | Max occurrences | Shuffle p |",
        "|---:|---:|---:|---:|---:|",
    ]
    controls_by_length = {row["length"]: row for row in result["shared_substring_controls"]}
    for row in result["shared_substring_rows"]:
        control = controls_by_length[row["length"]]
        lines.append(
            f"| {row['length']} | {row['reused_unique']} | {row['reused_occurrences']} | "
            f"{row['max_occurrences']} | {control['p_good_direction']:.5f} |"
        )
    lines += ["", "## Verdict", ""]
    if result["verdict"] == "candidate_overlap_tape":
        lines.append(
            "A module overlap tape gives positive rough MDL and beats digit-shuffle controls. "
            "It remains a mechanical generator candidate, not a translation."
        )
    else:
        lines.append(
            "The modules contain real copied substructure, but the tested overlap-tape "
            "grammar does not beat the literal module table after address cost and "
            "controls. The stronger interpretation remains copied/pre-rendered "
            "numeric chunks plus shorter exact repeats, not a compact module formula."
        )
    lines += ["", f"Translation delta: `{result['translation_delta']}`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    module_rows = [{"id": module["id"], "text": module["text"]} for module in formula["modules"]]
    texts = [module["text"] for module in module_rows]
    observed_by_threshold = {
        threshold: greedy_overlap_grammar(texts, threshold, include_components=True) for threshold in THRESHOLDS
    }
    controls = control_rows(texts, THRESHOLDS, observed_by_threshold)
    threshold_rows = []
    for threshold in THRESHOLDS:
        row = {**observed_by_threshold[threshold], "controls": controls[threshold]}
        mdl = row["rough_mdl_gain_bits"]
        p_shuffle = row["controls"]["per_module_digit_shuffle"]["rough_mdl_gain_bits"]["p_good_direction"]
        p_resample = row["controls"]["global_digit_resample"]["rough_mdl_gain_bits"]["p_good_direction"]
        row["verdict"] = "candidate" if mdl > 0 and p_shuffle <= 0.01 and p_resample <= 0.01 else "not_promoted"
        threshold_rows.append(row)
    threshold_rows.sort(key=lambda row: (-row["rough_mdl_gain_bits"], row["min_overlap"]))
    shared_rows = shared_substring_stats(module_rows)
    shared_controls = shared_substring_controls(texts, shared_rows)
    best = threshold_rows[0]
    verdict = "candidate_overlap_tape" if best["verdict"] == "candidate" else "not_promoted"
    module_slice_model = []
    for item in best["module_slices"]:
        module = module_rows[item["module_index"]]
        module_slice_model.append(
            {
                "module_id": module["id"],
                "length": len(module["text"]),
                "component_id": item["component_id"],
                "start": item["start"],
                "end": item["end"],
            }
        )
    result = {
        "schema": "module_overlap_grammar_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "module_count": len(module_rows),
        "total_module_digits": sum(len(text) for text in texts),
        "threshold_rows": threshold_rows,
        "best_threshold": best,
        "best_overlap_tape_model": {
            "min_overlap": best["min_overlap"],
            "component_count": best["component_count"],
            "tape_digits": best["tape_digits"],
            "components": best["component_texts"],
            "module_slices": module_slice_model,
        },
        "top_suffix_prefix_edges": pairwise_top_edges(module_rows),
        "shared_substring_rows": shared_rows,
        "shared_substring_controls": shared_controls,
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} best_threshold={best['min_overlap']} "
        f"mdl_gain_bits={best['rough_mdl_gain_bits']:.1f} gross_saved={best['gross_savings_digits']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
