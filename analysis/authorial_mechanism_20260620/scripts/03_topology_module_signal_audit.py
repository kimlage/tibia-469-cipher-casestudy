from __future__ import annotations

import csv
import json
import random
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"
TOPOLOGY = ROOT / "analysis/physical_topology_20260620/tables/hellgate_public_bookcase_manifest.csv"


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def p_ge(observed: float, controls: list[float]) -> float:
    return sum(1 for value in controls if value >= observed) / len(controls)


def adjacent_score(order: list[str], features: dict[str, set[str]]) -> float:
    return mean([jaccard(features[a], features[b]) for a, b in zip(order, order[1:]) if a in features and b in features])


def group_score(groups: dict[str, list[str]], features: dict[str, set[str]]) -> float:
    values = []
    for ids in groups.values():
        uniq = sorted(set(ids), key=int)
        for a, b in combinations(uniq, 2):
            if a in features and b in features:
                values.append(jaccard(features[a], features[b]))
    return mean(values)


def main() -> None:
    formula = json.loads(FORMULA.read_text(encoding="utf-8"))
    rows = [
        row
        for row in csv.DictReader(TOPOLOGY.open(encoding="utf-8"))
        if row["local_match_status"] == "resolved_unique"
    ]
    module_features = {}
    component_features = {}
    for book, recipe in formula["book_recipes"].items():
        module_features[book] = {item["id"] for item in recipe if item["type"] == "module_slice"}
        component_features[book] = {item["component_id"] for item in recipe if item["type"] == "module_slice"}
    public_order = [row["local_bookid"] for row in sorted(rows, key=lambda r: int(r["hg_public_entry"]))]
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(row["bookcase_public"], []).append(row["local_bookid"])
    group_sizes = [len(set(ids)) for ids in groups.values() if len(set(ids)) > 1]
    unique_books = sorted(set(public_order), key=int)
    rng = random.Random(46920260620)

    def control_adj(features: dict[str, set[str]]) -> list[float]:
        out = []
        for _ in range(2000):
            shuffled = public_order[:]
            rng.shuffle(shuffled)
            out.append(adjacent_score(shuffled, features))
        return out

    def control_group(features: dict[str, set[str]]) -> list[float]:
        out = []
        for _ in range(2000):
            shuffled = unique_books[:]
            rng.shuffle(shuffled)
            offset = 0
            control_groups = {}
            for idx, size in enumerate(group_sizes):
                control_groups[str(idx)] = shuffled[offset : offset + size]
                offset += size
            out.append(group_score(control_groups, features))
        return out

    module_adj = adjacent_score(public_order, module_features)
    module_adj_controls = control_adj(module_features)
    module_group = group_score(groups, module_features)
    module_group_controls = control_group(module_features)
    component_adj = adjacent_score(public_order, component_features)
    component_adj_controls = control_adj(component_features)
    component_group = group_score(groups, component_features)
    component_group_controls = control_group(component_features)

    metrics = {
        "module_adjacent": {
            "observed": module_adj,
            "control_mean": mean(module_adj_controls),
            "p_ge": p_ge(module_adj, module_adj_controls),
        },
        "module_bookcase_group": {
            "observed": module_group,
            "control_mean": mean(module_group_controls),
            "p_ge": p_ge(module_group, module_group_controls),
        },
        "component_adjacent": {
            "observed": component_adj,
            "control_mean": mean(component_adj_controls),
            "p_ge": p_ge(component_adj, component_adj_controls),
        },
        "component_bookcase_group": {
            "observed": component_group,
            "control_mean": mean(component_group_controls),
            "p_ge": p_ge(component_group, component_group_controls),
        },
    }
    best_p = min(row["p_ge"] for row in metrics.values())
    classification = "topology_module_signal_not_promoted" if best_p > 0.05 else "weak_topology_module_signal"
    result = {
        "schema": "topology_module_signal_audit.v1",
        "test": "03_topology_module_signal_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "resolved_topology_entries": len(public_order),
        "unique_books": len(unique_books),
        "metrics": metrics,
    }
    lines = [
        "# Topology Module Signal Audit",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This pass tests whether public Hellgate order/bookcase grouping predicts",
        "shared tape modules or tape components. It uses the partial public",
        "topology manifest and deterministic shuffles.",
        "",
        "| Metric | Observed | Control mean | p(control >= observed) |",
        "|---|---:|---:|---:|",
    ]
    for key, row in metrics.items():
        lines.append(f"| `{key}` | `{row['observed']:.6f}` | `{row['control_mean']:.6f}` | `{row['p_ge']:.4f}` |")
    lines += [
        "",
        "## Conclusion",
        "",
        "The current partial topology does not predict module/component sharing",
        "strongly enough to improve the generation model.",
    ]
    write_result("03_topology_module_signal_audit", result, lines)


if __name__ == "__main__":
    main()
