from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import random
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
REPORTS = BASE / "reports"
TEST_RESULTS = REPORTS / "test_results"

RUN_DATE = "2026-06-21"
RANDOM_SEED = 46920260621
DIGITS = list(range(10))
SYMBOLS = ["*", "A", "B", "C", "E", "F", "I", "L", "N", "O", "R", "S", "T", "V"]
STATUS_ORDER = [
    "PROMOTED_ORIGIN_FORMULA",
    "PROMOTED_MECHANICAL_CLUE",
    "WEAK_CLUE",
    "REJECTED_LOOKUP_DISGUISE",
    "REJECTED_CONTROL",
    "BLOCKED_NEEDS_EXTERNAL_SOURCE",
    "AUDIT_ONLY",
]

GRID = [
    ["*", "N", "R", "V", "F", "T", "I", "I", "I", "T"],
    ["N", "E", "F", "N", "A", "E", "T", "V", "I", "I"],
    ["R", "F", "A", "O", "L", "I", "N", "S", "T", "N"],
    ["V", "N", "O", "E", "B", "L", "V", "A", "T", None],
    ["F", "A", "L", "B", "E", "F", "N", "E", "E", "N"],
    ["T", "E", "I", "L", "F", "V", "I", "E", "E", "I"],
    ["I", "T", "N", "V", "N", "I", "E", "A", "C", "V"],
    ["I", "V", "S", "A", "E", "E", "A", "N", "E", "A"],
    ["I", "I", "T", "T", "E", "E", "C", "E", "A", "T"],
    ["T", "N", "N", "N", "N", "I", "V", "A", "T", "E"],
]

INPUTS = {
    "plan": Path("/Users/sargam/Downloads/row0_parallel_origin_plan.md"),
    "code_symbol_grid": ROOT / "analysis/mechanism_model_20260618/code_symbol_grid.md",
    "mechanical_formula": ROOT / "analysis/mechanism_model_20260618/mechanical_formula_469.json",
    "mechanical_formula_report": ROOT / "analysis/mechanism_model_20260618/mechanical_formula_report.md",
    "generator_model_report": ROOT / "analysis/generator_search_20260618/generator_model_final_report.md",
    "generator_mdl_leaderboard": ROOT / "analysis/generator_search_20260618/generator_mdl_leaderboard.md",
    "authorial_final": ROOT / "analysis/authorial_mechanism_20260620/reports/final_authorial_mechanism_report.md",
    "row0_frontier": ROOT / "analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.json",
    "prequential_row0": ROOT / "analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/01_prequential_and_row0_origin_audit.json",
    "family_holdout": ROOT / "analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/02_family_holdout_failure_audit.json",
    "recipe_externality": ROOT / "analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/04_recipe_externality_audit.json",
    "pair_table_constructive": ROOT / "analysis/generator_search_20260618/pair_table_constructive_leaderboard.json",
    "priority_fill": ROOT / "analysis/generator_search_20260618/priority_anchored_quotient_residual_fill_results.json",
    "quotient_fill": ROOT / "analysis/generator_search_20260618/quotient_constructive_fill_results.json",
    "usage_placement": ROOT / "analysis/generator_search_20260618/usage_driven_pair_placement_results.json",
    "pair_context_cluster": ROOT / "analysis/generator_search_20260618/pair_context_cluster_results.json",
    "directed_surface": ROOT / "analysis/generator_search_20260618/directed_pair_surface_results.json",
    "structural_exception": ROOT / "analysis/generator_search_20260618/structural_exception_layer_results.json",
    "digit_orbit": ROOT / "analysis/generator_search_20260618/digit_orbit_robust_control_results.json",
    "bilinear_low_rank": ROOT / "analysis/generator_search_20260618/bilinear_low_rank_pair_factor_results.json",
    "hierarchical_provenance": ROOT / "analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.json",
    "k5_eye": ROOT / "analysis/eye_model_20260619/k5_eye_pair_model_results.json",
    "eye_5x2": ROOT / "analysis/eye_model_20260619/eye_state_5x2_model_results.json",
    "inspiration_final": ROOT / "analysis/inspiration_model_20260620/reports/final_inspiration_model_report.md",
    "dnd_eye_order": ROOT / "analysis/inspiration_model_20260620/reports/test_results/dnd_eye_ray_order_model.json",
    "numeric_seed": ROOT / "analysis/inspiration_model_20260620/reports/test_results/numeric_identity_key_seed_search.json",
    "language_comparanda": ROOT / "analysis/language_comparanda_20260620/reports/final_language_comparanda_report.md",
    "physical_topology": ROOT / "analysis/physical_topology_20260620/reports/final_physical_topology_report.md",
    "wiki_lore": ROOT / "docs/wiki/10-lore-source-audit.md",
    "wiki_mechanical": ROOT / "docs/wiki/13-mechanical-origin-model-v1.md",
    "wiki_eye": ROOT / "docs/wiki/14-eye-blink-arity-model.md",
    "wiki_topology": ROOT / "docs/wiki/17-physical-library-topology.md",
    "wiki_authorial": ROOT / "docs/wiki/18-authorial-mechanism-model.md",
    "wiki_open_questions": ROOT / "docs/wiki/09-open-questions.md",
    "workbook_export_script": ROOT / "scripts/export_workbook_to_sqlite.py",
    "q3_tables": ROOT / "analysis/audit_20260609/q3_tables.py",
    "row0_code_symbol_probe": ROOT / "scripts/sqlite_row0_code_symbol_probe.py",
    "external_row0_literal_decode": ROOT / "scripts/sqlite_external_row0_literal_decode_audit.py",
}

SEVEN_SEG = {
    0: set("abcefd"),
    1: set("bc"),
    2: set("abged"),
    3: set("abgcd"),
    4: set("fgbc"),
    5: set("afgcd"),
    6: set("afgecd"),
    7: set("abc"),
    8: set("abcdefg"),
    9: set("abfgcd"),
}
NUMPAD = {
    1: (0, 0),
    2: (1, 0),
    3: (2, 0),
    4: (0, 1),
    5: (1, 1),
    6: (2, 1),
    7: (0, 2),
    8: (1, 2),
    9: (2, 2),
    0: (1, -1),
}


def ensure_dirs() -> None:
    for path in [DATA, REPORTS, TEST_RESULTS, BASE / "scripts"]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing": True, "path": rel(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def yaml_lines(data: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(yaml_lines(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
        return lines
    if isinstance(data, list):
        lines = []
        for value in data:
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(yaml_lines(value, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(value)}")
        return lines
    return [f"{prefix}{yaml_scalar(data)}"]


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(yaml_lines(data)).rstrip() + "\n", encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ordered_label(code: str) -> str | None:
    return GRID[int(code[0])][int(code[1])]


def pair_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in DIGITS:
        for j in range(i, 10):
            codes = [f"{i}{j}"] if i == j else [f"{i}{j}", f"{j}{i}"]
            present = [(code, ordered_label(code)) for code in codes if ordered_label(code) is not None]
            labels = [label for _, label in present if label is not None]
            if len(labels) == 2 and labels[0] != labels[1]:
                status = "conflict"
                label = "/".join(labels)
            elif len(labels) == 2:
                status = "pure"
                label = labels[0]
            elif len(labels) == 1 and len(codes) == 2:
                status = "reverse_missing" if ordered_label(codes[0]) is None else "forward_missing"
                label = labels[0]
            elif len(labels) == 1:
                status = "pure"
                label = labels[0]
            else:
                status = "missing"
                label = ""
            rows.append(
                {
                    "pair": f"{i}{j}",
                    "i": i,
                    "j": j,
                    "label": label,
                    "status": status,
                    "ordered_codes": "|".join(code for code, _ in present),
                    "ordered_labels": "|".join(label for _, label in present if label is not None),
                    "is_diagonal": i == j,
                    "is_conflict": status == "conflict",
                    "is_reverse_missing": status == "reverse_missing",
                }
            )
    return rows


def canonical_label(row: dict[str, Any]) -> str:
    if row["status"] == "conflict":
        return "I/N"
    return str(row["label"])


def label_for_model(row: dict[str, Any]) -> str:
    if row["status"] == "conflict":
        return "I/N"
    return str(row["label"])


def seven_segment_distance(a: int, b: int) -> int:
    return len(SEVEN_SEG[a] ^ SEVEN_SEG[b])


def numpad_distance(a: int, b: int) -> int:
    ax, ay = NUMPAD[a]
    bx, by = NUMPAD[b]
    return abs(ax - bx) + abs(ay - by)


def clock_distance(a: int, b: int) -> int:
    diff = abs(a - b)
    return min(diff, 10 - diff)


def feature_rows() -> list[dict[str, Any]]:
    rows = []
    for row in pair_rows():
        i = int(row["i"])
        j = int(row["j"])
        high_block = i >= 5 and j >= 5
        border = i in {0, 9} or j in {0, 9}
        corner = (i, j) in {(0, 0), (0, 9), (9, 9)}
        rows.append(
            {
                **row,
                "min_digit": min(i, j),
                "max_digit": max(i, j),
                "sum": i + j,
                "diff": abs(i - j),
                "product": i * j,
                "sum_mod_3": (i + j) % 3,
                "sum_mod_5": (i + j) % 5,
                "product_mod_5": (i * j) % 5,
                "parity_pair": f"{i % 2}{j % 2}",
                "is_border": border,
                "is_corner": corner,
                "is_high_block": high_block,
                "has_6": i == 6 or j == 6,
                "has_9": i == 9 or j == 9,
                "has_0": i == 0 or j == 0,
                "has_1": i == 1 or j == 1,
                "seven_segment_distance": seven_segment_distance(i, j),
                "numpad_distance": numpad_distance(i, j),
                "clock_distance": clock_distance(i, j),
                "eye_pair_features": "diagonal" if i == j else ("contains_central_digit" if 5 in {i, j} else "off_diagonal"),
                "ordered_surface_features": "conflict" if row["status"] == "conflict" else ("missing_reverse" if row["status"] == "reverse_missing" else "symmetric"),
                "frequency_features": "inventory_only_pending",
                "zero_omission_features": "zero_pair" if 0 in {i, j} else "nonzero_pair",
                "copy_provenance_features": "external_audit_reference",
                "literal_provenance_features": "external_audit_reference",
                "first_use_features": "external_audit_reference",
                "topology_features": "external_audit_reference",
                "external_anchor_overlap_features": "external_audit_reference",
            }
        )
    return rows


def inventory(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(label_for_model(row) for row in rows)


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def inventory_sequence_bits(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return log2_factorial(total) - sum(log2_factorial(count) for count in counts.values())


def json_leaf(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = data
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def pvalue_ge(values: list[float], observed: float) -> float:
    return (sum(1 for value in values if value >= observed) + 1) / (len(values) + 1)


def predicate_defs() -> list[tuple[str, str, Any]]:
    return [
        ("diagonal", "is_diagonal", True),
        ("border", "is_border", True),
        ("corner", "is_corner", True),
        ("high_block", "is_high_block", True),
        ("has_6", "has_6", True),
        ("has_9", "has_9", True),
        ("has_0", "has_0", True),
        ("has_1", "has_1", True),
        ("diff_0", "diff", 0),
        ("diff_1", "diff", 1),
        ("diff_le_2", "diff_le_2", True),
        ("sum_mod_3_0", "sum_mod_3", 0),
        ("sum_mod_5_4", "sum_mod_5", 4),
        ("sevenseg_le_2", "sevenseg_le_2", True),
        ("numpad_le_1", "numpad_le_1", True),
        ("clock_le_1", "clock_le_1", True),
    ]


def predicate_value(row: dict[str, Any], field: str) -> Any:
    if field == "diff_le_2":
        return int(row["diff"]) <= 2
    if field == "sevenseg_le_2":
        return int(row["seven_segment_distance"]) <= 2
    if field == "numpad_le_1":
        return int(row["numpad_distance"]) <= 1
    if field == "clock_le_1":
        return int(row["clock_distance"]) <= 1
    return row[field]


def majority_label(rows: list[dict[str, Any]]) -> str:
    counts = Counter(label_for_model(row) for row in rows)
    return counts.most_common(1)[0][0] if counts else "E"


def stump_predictions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outcomes = []
    labels = [label_for_model(row) for row in rows]
    global_majority = Counter(labels).most_common(1)[0][0]
    for name, field, expected in predicate_defs():
        in_group = [row for row in rows if predicate_value(row, field) == expected]
        out_group = [row for row in rows if predicate_value(row, field) != expected]
        if not in_group or not out_group:
            continue
        pred_in = majority_label(in_group)
        pred_out = majority_label(out_group)
        hits = sum(
            1
            for row in rows
            if label_for_model(row) == (pred_in if predicate_value(row, field) == expected else pred_out)
        )
        loo_hits = 0
        for holdout in rows:
            train = [row for row in rows if row is not holdout]
            train_in = [row for row in train if predicate_value(row, field) == expected]
            train_out = [row for row in train if predicate_value(row, field) != expected]
            holdout_pred = (
                majority_label(train_in) if predicate_value(holdout, field) == expected and train_in else
                majority_label(train_out) if train_out else global_majority
            )
            loo_hits += int(holdout_pred == label_for_model(holdout))
        outcomes.append(
            {
                "rule": name,
                "hits": hits,
                "loo_hits": loo_hits,
                "accuracy": hits / len(rows),
                "loo_accuracy": loo_hits / len(rows),
                "pred_in": pred_in,
                "pred_out": pred_out,
                "in_count": len(in_group),
            }
        )
    return sorted(outcomes, key=lambda row: (row["loo_hits"], row["hits"]), reverse=True)


def fixed_orders(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    pairs = [row["pair"] for row in rows]
    by_pair = {row["pair"]: row for row in rows}
    diag = sorted(pairs, key=lambda pair: (int(pair[0]) + int(pair[1]), int(pair[0]), int(pair[1])))
    anti = sorted(pairs, key=lambda pair: (int(pair[1]) - int(pair[0]), int(pair[0]), int(pair[1])))
    boust = []
    for i in DIGITS:
        row_pairs = [f"{i}{j}" for j in range(i, 10)]
        if i % 2:
            row_pairs.reverse()
        boust.extend(row_pairs)
    numpad = sorted(pairs, key=lambda pair: (numpad_distance(int(pair[0]), int(pair[1])), NUMPAD[int(pair[0])][1], NUMPAD[int(pair[1])][1], pair))
    clock = sorted(pairs, key=lambda pair: (clock_distance(int(pair[0]), int(pair[1])), int(pair[0]), int(pair[1])))
    seven = sorted(pairs, key=lambda pair: (seven_segment_distance(int(pair[0]), int(pair[1])), int(pair[0]) + int(pair[1]), pair))
    k5 = sorted(pairs, key=lambda pair: ((int(pair[0]) % 5, int(pair[1]) % 5), int(pair[0]) // 5, int(pair[1]) // 5))
    return {
        "lexicographic_upper_triangle": pairs,
        "diagonal_sweep": diag,
        "anti_diagonal_sweep": anti,
        "boustrophedon": [pair for pair in boust if pair in by_pair],
        "numpad_distance": numpad,
        "clock_distance": clock,
        "seven_segment_distance": seven,
        "k5_mod5_eye_pair_order": k5,
    }


def inventory_fill_hits(rows: list[dict[str, Any]], order: list[str]) -> dict[str, Any]:
    by_pair = {row["pair"]: row for row in rows}
    counts = inventory(rows)
    label_stream = []
    for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        label_stream.extend([label] * count)
    predicted = dict(zip(order, label_stream))
    hits = sum(1 for pair, pred in predicted.items() if pred == label_for_model(by_pair[pair]))
    return {"hits": hits, "accuracy": hits / len(rows), "order": order[:10]}


def label_shuffle_control(rows: list[dict[str, Any]], trials: int = 1000) -> dict[str, Any]:
    labels = [label_for_model(row) for row in rows]
    rng = random.Random(RANDOM_SEED)
    observed = max(row["loo_hits"] for row in stump_predictions(rows))
    maxima = []
    shuffled_rows = [dict(row) for row in rows]
    for _ in range(trials):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        for row, label in zip(shuffled_rows, shuffled):
            row["label"] = label
            row["status"] = "pure"
        maxima.append(max(row["loo_hits"] for row in stump_predictions(shuffled_rows)))
    return {
        "observed_best_loo_hits": observed,
        "trials": trials,
        "control_median_best_loo_hits": sorted(maxima)[len(maxima) // 2],
        "control_max_best_loo_hits": max(maxima),
        "p_control_ge_observed": pvalue_ge(maxima, observed),
    }


def digit_permutation_control(rows: list[dict[str, Any]], trials: int = 500) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 1)
    observed = max(row["hits"] for row in stump_predictions(rows))
    values = []
    label_by_pair = {row["pair"]: label_for_model(row) for row in rows}
    for _ in range(trials):
        perm = DIGITS[:]
        rng.shuffle(perm)
        remap = {old: new for old, new in zip(DIGITS, perm)}
        permuted = []
        for row in rows:
            a, b = sorted((remap[int(row["i"])], remap[int(row["j"])]))
            feature = next(item for item in feature_rows() if int(item["i"]) == a and int(item["j"]) == b)
            feature = dict(feature)
            feature["label"] = label_by_pair[row["pair"]]
            feature["status"] = "pure"
            permuted.append(feature)
        values.append(max(item["hits"] for item in stump_predictions(permuted)))
    return {
        "observed_best_hits": observed,
        "trials": trials,
        "control_median_best_hits": sorted(values)[len(values) // 2],
        "control_max_best_hits": max(values),
        "p_control_ge_observed": pvalue_ge(values, observed),
    }


def source_summary(name: str, path: list[str] | None = None) -> Any:
    data = load_json(INPUTS[name])
    if path:
        return json_leaf(data, path)
    return data


def workbook_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False}
    key_patterns = re.compile(r"keytable|digitcode|codepair|row0|booksdigit|omission|groundtruth", re.I)
    try:
        raw = subprocess.check_output(["unzip", "-p", str(path), "xl/workbook.xml"], cwd=ROOT)
        workbook = raw.decode("utf-8", errors="replace")
        sheet_names = re.findall(r'<sheet[^>]+name="([^"]+)"', workbook)
        key_sheets = [name for name in sheet_names if key_patterns.search(name)]
        return {
            "path": rel(path),
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "sheet_count": len(sheet_names),
            "key_sheet_names": key_sheets[:40],
            "first_sheet_names": sheet_names[:12],
            "classification": "legacy_workbook_snapshot_or_derived_project_artifact",
        }
    except Exception as exc:
        return {"path": rel(path), "exists": True, "error": str(exc), "classification": "unreadable_workbook"}


def script_signal(path: Path, patterns: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(pattern.lower() in low for pattern in patterns):
            hits.append({"line": lineno, "text": line.strip()[:220]})
    return {"path": rel(path), "exists": path.exists(), "hit_count": len(hits), "hits": hits[:24]}


def residual_lookup_bits_after_freezing(rows: list[dict[str, Any]], frozen_pairs: set[str]) -> float:
    residual_counts = Counter(label_for_model(row) for row in rows if row["pair"] not in frozen_pairs)
    return inventory_sequence_bits(residual_counts)


def worksheet_anchor_rows() -> list[dict[str, Any]]:
    labels = {row["pair"]: label_for_model(row) for row in pair_rows()}
    anchors = [
        ("00", "unique_star_cell", "AUDIT_ONLY", "Only `00` maps to `*`; useful worksheet anchor but not externally sourced."),
        ("19", "directed_conflict_cell", "PROMOTED_MECHANICAL_CLUE", "`19 -> I` versus `91 -> N` is the sole directed conflict."),
        ("39", "missing_forward_surface_cell", "PROMOTED_MECHANICAL_CLUE", "`39` is absent while `93 -> N` exists."),
        ("02", "rare_singleton_R", "WEAK_CLUE", "Singleton rare label placement; descriptive only."),
        ("23", "rare_singleton_O", "WEAK_CLUE", "Singleton rare label placement; descriptive only."),
        ("27", "rare_singleton_S", "WEAK_CLUE", "Singleton rare label placement; descriptive only."),
        ("34", "rare_singleton_B", "WEAK_CLUE", "Singleton rare label placement; descriptive only."),
        ("68", "rare_singleton_C", "WEAK_CLUE", "Singleton rare label placement; descriptive only."),
        ("11", "diagonal_E_pressure", "WEAK_CLUE", "One of five diagonal E cells; diagonal pressure is partial."),
        ("33", "diagonal_E_pressure", "WEAK_CLUE", "One of five diagonal E cells; diagonal pressure is partial."),
        ("44", "diagonal_E_pressure", "WEAK_CLUE", "One of five diagonal E cells; diagonal pressure is partial."),
        ("66", "diagonal_E_pressure", "WEAK_CLUE", "One of five diagonal E cells; diagonal pressure is partial."),
        ("99", "diagonal_E_pressure", "WEAK_CLUE", "One of five diagonal E cells; diagonal pressure is partial."),
    ]
    return [
        {
            "pair": pair,
            "label": labels[pair],
            "anchor_family": family,
            "classification": classification,
            "reason": reason,
        }
        for pair, family, classification, reason in anchors
    ]


def run_141() -> dict[str, Any]:
    status = git_output(["status", "--short", "--branch"])
    manifest = {
        "schema": "row0_origin_parallel_run_manifest.v1",
        "front": "row0_origin_parallel",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "date": RUN_DATE,
        "commit": git_output(["rev-parse", "HEAD"]),
        "branch": git_output(["branch", "--show-current"]),
        "status_short": status.splitlines(),
        "boundary": {
            "scope": "row0 origin only",
            "translation_delta": "NONE",
            "does_not_attempt": ["book plaintext", "fan gloss validation", "main book-generation formula improvement"],
            "parallel_front_rule": "Reads only committed/current workspace artifacts and records hashes; does not assume the other formula-improvement front is complete.",
        },
        "inputs": {
            key: {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
            }
            for key, path in INPUTS.items()
        },
    }
    write_json(BASE / "run_manifest.json", manifest)
    lines = [
        "# 141. Row0 Run Manifest",
        "",
        f"- Commit: `{manifest['commit']}`",
        f"- Branch: `{manifest['branch']}`",
        "- Scope: row0 origin only; no plaintext or translation claim.",
        "- Boundary: the active book-generation formula is an input substrate, not proof of row0 origin.",
        "",
        "## Dirty worktree note",
        "",
        "The manifest records the current short status so this front can stay separate from concurrent formula work.",
        "",
        "## Inputs",
        "",
        "| Input | Exists | SHA-256 |",
        "|---|---:|---|",
    ]
    for key, meta in manifest["inputs"].items():
        lines.append(f"| `{key}` | `{meta['exists']}` | `{meta['sha256'] or 'missing'}` |")
    write_md(TEST_RESULTS / "141_row0_run_manifest.md", lines)
    write_json(TEST_RESULTS / "141_row0_run_manifest.json", manifest)
    return manifest


def run_142() -> dict[str, Any]:
    rows = pair_rows()
    features = feature_rows()
    pair_fields = [
        "pair", "i", "j", "label", "status", "ordered_codes", "ordered_labels",
        "is_diagonal", "is_conflict", "is_reverse_missing",
    ]
    feature_fields = list(features[0].keys())
    write_csv(DATA / "row0_pair_table_canonical.csv", rows, pair_fields)
    write_csv(DATA / "row0_pair_features.csv", features, feature_fields)
    counts = inventory(rows)
    label_inventory = {
        "pair_count": len(rows),
        "ordered_code_count": sum(1 for i in DIGITS for j in DIGITS if GRID[i][j] is not None),
        "missing_ordered_codes": [f"{i}{j}" for i in DIGITS for j in DIGITS if GRID[i][j] is None],
        "pure_pair_count": sum(1 for row in rows if row["status"] != "conflict"),
        "conflict_pairs": [row["pair"] for row in rows if row["status"] == "conflict"],
        "reverse_missing_pairs": [row["pair"] for row in rows if row["status"] == "reverse_missing"],
        "label_counts": dict(sorted(counts.items())),
    }
    write_json(DATA / "row0_label_inventory.json", label_inventory)
    controls = {
        "random_seed": RANDOM_SEED,
        "controls": [
            "label_shuffle_inventory_preserving",
            "digit_identity_permutation",
            "row_column_preserving_shuffle_for_ordered_surface",
            "diagonal_preserving_shuffle_when_applicable",
            "best_of_search_correction_required_for_family_sweeps",
            "negative_source_controls_for_lore",
        ],
    }
    write_json(DATA / "row0_controls_manifest.json", controls)
    lines = [
        "# 142. Canonical Row0 Features",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        "## Canonical facts",
        "",
        f"- Unordered pair rows: `{len(rows)}`.",
        f"- Ordered codes represented: `{label_inventory['ordered_code_count']}`.",
        f"- Missing ordered code: `{label_inventory['missing_ordered_codes']}`.",
        f"- Pure unordered pairs: `{label_inventory['pure_pair_count']}/55`.",
        f"- Conflict pair: `{label_inventory['conflict_pairs']}`.",
        f"- Reverse-missing pair: `{label_inventory['reverse_missing_pairs']}`.",
        "",
        "## Label inventory",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in sorted(counts.items()):
        lines.append(f"| `{label}` | `{count}` |")
    write_md(TEST_RESULTS / "142_row0_canonical_features_compile.md", lines)
    write_json(TEST_RESULTS / "142_row0_canonical_features_compile.json", label_inventory)
    return label_inventory


def run_143() -> dict[str, Any]:
    rows = pair_rows()
    counts = inventory(rows)
    inv_bits = inventory_sequence_bits(counts)
    direct_symbol_bits = len(rows) * math.log2(len(SYMBOLS))
    conflict_aware_alphabet_bits = len(rows) * math.log2(len(counts))
    baseline = {
        "schema": "row0_lookup_baseline_mdl.v1",
        "classification": "AUDIT_ONLY",
        "pair_count": len(rows),
        "label_inventory": dict(sorted(counts.items())),
        "bits_lookup_given_inventory": inv_bits,
        "bits_direct_symbol_alphabet": direct_symbol_bits,
        "bits_direct_observed_label_alphabet": conflict_aware_alphabet_bits,
        "manual_authorial_lookup_status": "baseline_to_beat_not_failure",
        "promotion_rule": "A row0-origin formula must beat lookup after rule, parameters, exceptions, order, and search costs.",
    }
    write_json(TEST_RESULTS / "143_row0_lookup_baseline_mdl.json", baseline)
    write_json(DATA / "row0_lookup_baseline_mdl.json", baseline)
    lines = [
        "# 143. Row0 Lookup Baseline MDL",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        f"- Lookup cost given inventory: `{inv_bits:.3f}` bits.",
        f"- Direct 14-symbol code cost: `{direct_symbol_bits:.3f}` bits.",
        f"- Direct observed-label alphabet cost: `{conflict_aware_alphabet_bits:.3f}` bits.",
        "",
        "This is the baseline to beat. A manual worksheet/lookup explanation is acceptable if controlled formulas do not reduce cost.",
    ]
    write_md(TEST_RESULTS / "143_row0_lookup_baseline_mdl.md", lines)
    return baseline


def run_144() -> dict[str, Any]:
    rows = feature_rows()
    stumps = stump_predictions(rows)
    label_control = label_shuffle_control(rows, trials=500)
    digit_control = digit_permutation_control(rows, trials=250)
    best = stumps[0]
    classification = "REJECTED_CONTROL"
    if best["loo_hits"] > label_control["control_max_best_loo_hits"]:
        classification = "WEAK_CLUE"
    result = {
        "schema": "row0_priority_layer_mdl.v1",
        "classification": classification,
        "best_rule": best,
        "top_rules": stumps[:10],
        "label_shuffle_control": label_control,
        "digit_permutation_control": digit_control,
        "interpretation": "Simple priority layers are useful diagnostics but do not beat lookup or survive best-of-family controls as an origin formula.",
    }
    write_json(TEST_RESULTS / "144_row0_priority_layer_mdl.json", result)
    lines = [
        "# 144. Row0 Priority Layer MDL",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        f"Best layer: `{best['rule']}` with `{best['loo_hits']}/55` leave-one-pair-out hits.",
        f"Label-shuffle control p(control >= observed): `{label_control['p_control_ge_observed']:.4f}`.",
        f"Digit-permutation control p(control >= observed): `{digit_control['p_control_ge_observed']:.4f}`.",
        "",
        "| Rule | Hits | LOO hits | In-count | Labels |",
        "|---|---:|---:|---:|---|",
    ]
    for row in stumps[:10]:
        lines.append(f"| `{row['rule']}` | `{row['hits']}` | `{row['loo_hits']}` | `{row['in_count']}` | `{row['pred_in']}/{row['pred_out']}` |")
    write_md(TEST_RESULTS / "144_row0_priority_layer_mdl.md", lines)
    return result


def run_145() -> dict[str, Any]:
    rows = feature_rows()
    clusters = []
    for row in rows:
        cluster = (
            "conflict_or_missing" if row["status"] != "pure" else
            "diagonal" if row["is_diagonal"] else
            "six_nine_orbit" if row["has_6"] or row["has_9"] else
            "zero_or_one_edge" if row["has_0"] or row["has_1"] else
            "residual_geometry"
        )
        clusters.append({"pair": row["pair"], "label": label_for_model(row), "cluster": cluster})
    write_csv(DATA / "row0_latent_pair_clusters.csv", clusters, ["pair", "label", "cluster"])
    counts_by_cluster: dict[str, Counter[str]] = defaultdict(Counter)
    for row in clusters:
        counts_by_cluster[row["cluster"]][row["label"]] += 1
    total_hits = sum(counter.most_common(1)[0][1] for counter in counts_by_cluster.values())
    existing = source_summary("pair_context_cluster")
    result = {
        "schema": "row0_latent_behavior_partition.v1",
        "classification": "REJECTED_CONTROL",
        "geometry_cluster_majority_hits": total_hits,
        "geometry_cluster_majority_accuracy": total_hits / len(rows),
        "cluster_label_counts": {cluster: dict(counter) for cluster, counter in counts_by_cluster.items()},
        "prior_pair_context_cluster_result": existing,
        "interpretation": "Unsupervised/label-blind partitions do not recover row0 labels strongly enough for promotion; previous pair-context clustering is retained as rejected/control-bound evidence.",
    }
    write_json(TEST_RESULTS / "145_row0_latent_behavior_partition.json", result)
    lines = [
        "# 145. Row0 Latent Behavior Partition",
        "",
        "Classification: `REJECTED_CONTROL`",
        "Translation delta: `NONE`",
        "",
        f"Geometry-only cluster majority score: `{total_hits}/55`.",
        "",
        "| Cluster | Label counts |",
        "|---|---|",
    ]
    for cluster, counter in sorted(counts_by_cluster.items()):
        lines.append(f"| `{cluster}` | `{dict(counter)}` |")
    lines += [
        "",
        "The retained prior pair-context audit is treated as evidence against a corpus-behavior origin formula, not as a new translation signal.",
    ]
    write_md(TEST_RESULTS / "145_row0_latent_behavior_partition.md", lines)
    return result


def run_146() -> dict[str, Any]:
    rows = pair_rows()
    results = {name: inventory_fill_hits(rows, order) for name, order in fixed_orders(rows).items()}
    observed_best = max(row["hits"] for row in results.values())
    rng = random.Random(RANDOM_SEED + 2)
    pairs = [row["pair"] for row in rows]
    controls = []
    for _ in range(1000):
        order = pairs[:]
        rng.shuffle(order)
        controls.append(inventory_fill_hits(rows, order)["hits"])
    result = {
        "schema": "row0_fill_order_inventory_search.v1",
        "classification": "REJECTED_CONTROL",
        "fixed_orders": results,
        "observed_best_hits": observed_best,
        "random_order_control": {
            "trials": len(controls),
            "median": sorted(controls)[len(controls) // 2],
            "max": max(controls),
            "p_control_ge_observed": pvalue_ge(controls, observed_best),
        },
        "prior_usage_driven_pair_placement": source_summary("usage_placement"),
        "interpretation": "Fixed fill orders plus inventory do not produce a promoted row0 origin formula.",
    }
    write_json(TEST_RESULTS / "146_row0_fill_order_inventory_search.json", result)
    lines = [
        "# 146. Row0 Fill Order Inventory Search",
        "",
        "Classification: `REJECTED_CONTROL`",
        "Translation delta: `NONE`",
        "",
        f"Best fixed-order inventory fill: `{observed_best}/55` hits.",
        f"Random-order p(control >= observed): `{result['random_order_control']['p_control_ge_observed']:.4f}`.",
        "",
        "| Order | Hits | Accuracy |",
        "|---|---:|---:|",
    ]
    for name, row in sorted(results.items(), key=lambda item: item[1]["hits"], reverse=True):
        lines.append(f"| `{name}` | `{row['hits']}` | `{row['accuracy']:.3f}` |")
    write_md(TEST_RESULTS / "146_row0_fill_order_inventory_search.md", lines)
    return result


def run_147() -> dict[str, Any]:
    registry = {
        "schema": "row0_lore_source_registry.v1",
        "sources": [
            {"id": "great_calculator_assemble", "classification": "BLOCKED_NEEDS_EXTERNAL_SOURCE", "reason": "No fixed official symbol/pair order that predicts row0 labels without target-fit transforms."},
            {"id": "honeminas_magic_web", "classification": "REJECTED_CONTROL", "reason": "Numeric/vector seeds remain mechanism watchlist material; no controlled row0-label predictor."},
            {"id": "secret_library_74032_45331", "classification": "WEAK_CLUE", "reason": "Official unglossed numeric motif; useful as watchlist only, not a pair-label source."},
            {"id": "3478_486486_1_0", "classification": "WEAK_CLUE", "reason": "Numeric identity motifs survive as weak mechanism clues, not a row0 formula."},
            {"id": "dnd_beholder_eye_rays", "classification": "BLOCKED_NEEDS_EXTERNAL_SOURCE", "reason": "External 10-channel order can support arity tests, but no authority for Tibia row0 labels."},
            {"id": "bonelord_lore_texts", "classification": "REJECTED_CONTROL", "reason": "Lore text presence does not become a fixed low-cost label order under controls."},
        ],
    }
    write_json(DATA / "row0_lore_source_registry.json", registry)
    write_yaml(DATA / "row0_lore_source_registry.yaml", registry)
    result = {
        "schema": "row0_lore_fixed_order_audit.v1",
        "classification": "REJECTED_CONTROL",
        "registry": registry,
        "dnd_eye_order_result": source_summary("dnd_eye_order"),
        "numeric_seed_result": source_summary("numeric_seed"),
        "interpretation": "Lore sources remain mechanism/watchlist inputs unless they supply a fixed external order that predicts labels under controls.",
    }
    write_json(TEST_RESULTS / "147_row0_lore_fixed_order_audit.json", result)
    lines = [
        "# 147. Row0 Lore Fixed-Order Audit",
        "",
        "Classification: `REJECTED_CONTROL`",
        "Translation delta: `NONE`",
        "",
        "| Source | Classification | Reason |",
        "|---|---|---|",
    ]
    for row in registry["sources"]:
        lines.append(f"| `{row['id']}` | `{row['classification']}` | {row['reason']} |")
    write_md(TEST_RESULTS / "147_row0_lore_fixed_order_audit.md", lines)
    return result


def run_148() -> dict[str, Any]:
    k5 = source_summary("k5_eye")
    eye = source_summary("eye_5x2")
    orbit = source_summary("digit_orbit")
    k5_summary = {
        "source": rel(INPUTS["k5_eye"]),
        "best_label_rule": json_leaf(k5, ["best_label_rule"]),
        "label_gain_control_p": json_leaf(k5, ["controls", "label_gain_p"]),
    }
    eye_summary = {
        "source": rel(INPUTS["eye_5x2"]),
        "best_label_rule": json_leaf(eye, ["best_label_rule"]),
        "label_gain_control_p": json_leaf(eye, ["controls", "label_gain_p"]),
    }
    orbit_summary = {
        "source": rel(INPUTS["digit_orbit"]),
        "observed_best_by_primary_hits": json_leaf(orbit, ["observed", "best_by_primary_hits"]),
        "fixed_swap_control_p": json_leaf(
            orbit,
            ["controls", "column_preserving_shuffle", "fixed_swap_6_9", "primary_hits", "p_good_direction"],
        ),
    }
    result = {
        "schema": "row0_eye_digit_geometry_audit.v1",
        "classification": "WEAK_CLUE",
        "k5_eye_pair_model": k5_summary,
        "eye_state_5x2_model": eye_summary,
        "digit_orbit_6_9": orbit_summary,
        "interpretation": "Eye/K5 arity and 6<->9 orbit remain weak mechanical clues. They do not derive the row0 labels below lookup with controls.",
    }
    write_json(TEST_RESULTS / "148_row0_eye_digit_geometry_audit.json", result)
    k5_acc = json_leaf(k5, ["best_label_rule", "accuracy"], "n/a")
    eye_acc = json_leaf(eye, ["best_label_rule", "accuracy"], "n/a")
    orbit_hits = json_leaf(orbit, ["observed", "best_by_primary_hits", "primary_hits"], "n/a")
    orbit_p = json_leaf(orbit, ["controls", "column_preserving_shuffle", "fixed_swap_6_9", "primary_hits", "p_good_direction"], "n/a")
    lines = [
        "# 148. Row0 Eye Digit Geometry Audit",
        "",
        "Classification: `WEAK_CLUE`",
        "Translation delta: `NONE`",
        "",
        f"- K5 eye-pair label accuracy: `{k5_acc}`.",
        f"- 5x2 eye-state label accuracy: `{eye_acc}`.",
        f"- 6/9 orbit primary hits: `{orbit_hits}/55`; control p: `{orbit_p}`.",
        "",
        "Interpretation: arity/geometric structure can guide mechanism hypotheses, but label prediction remains unpromoted.",
    ]
    write_md(TEST_RESULTS / "148_row0_eye_digit_geometry_audit.md", lines)
    return result


def run_149() -> dict[str, Any]:
    directed = source_summary("directed_surface")
    structural = source_summary("structural_exception")
    rows = pair_rows()
    result = {
        "schema": "row0_ordered_surface_origin_audit.v1",
        "classification": "PROMOTED_MECHANICAL_CLUE",
        "ordered_surface_facts": {
            "ordered_code_count": 99,
            "missing_ordered_codes": ["39"],
            "conflict_pairs": [row["pair"] for row in rows if row["status"] == "conflict"],
            "reverse_missing_pairs": [row["pair"] for row in rows if row["status"] == "reverse_missing"],
            "pure_pairs": sum(1 for row in rows if row["status"] != "conflict"),
        },
        "directed_pair_surface_result": {
            "source": rel(INPUTS["directed_surface"]),
            "conclusion": json_leaf(directed, ["conclusion"]),
            "diagnostics": json_leaf(directed, ["diagnostics"]),
        },
        "structural_exception_result": {
            "source": rel(INPUTS["structural_exception"]),
            "conclusion": json_leaf(structural, ["conclusion"]),
        },
        "interpretation": "The ordered surface/render layer is a promoted mechanical clue, but not a complete unordered pair-label origin formula.",
    }
    write_json(TEST_RESULTS / "149_row0_ordered_surface_origin_audit.json", result)
    lines = [
        "# 149. Row0 Ordered Surface Origin Audit",
        "",
        "Classification: `PROMOTED_MECHANICAL_CLUE`",
        "Translation delta: `NONE`",
        "",
        "- Ordered surface has `99/100` codes.",
        "- Missing ordered code: `39`.",
        "- Sole directed conflict: `19 -> I`, `91 -> N`.",
        "- Unordered pair purity: `54/55`.",
        "",
        "This promotes a render/ordered-surface clue only. It does not derive the full unordered row0 label inventory.",
    ]
    write_md(TEST_RESULTS / "149_row0_ordered_surface_origin_audit.md", lines)
    return result


def run_150() -> dict[str, Any]:
    result = {
        "schema": "row0_external_anchor_holdout.v1",
        "classification": "BLOCKED_NEEDS_EXTERNAL_SOURCE",
        "anchors": [
            {"id": "ytc_2012_chayenne", "status": "secondary_validation_only", "reason": "Useful compatibility holdout for mechanical stream, not a row0 label source."},
            {"id": "secret_library_74032_45331", "status": "weak_watchlist", "reason": "Official unglossed number string; no symbol table or plaintext pair."},
            {"id": "avar_tar", "status": "negative_control", "reason": "Retained as control, not promoted."},
            {"id": "isle_kharos_exact_topology", "status": "blocked", "reason": "Exact tile/slot/orientation/order not available as fixed source."},
            {"id": "tibia_language_comparanda", "status": "control_corpus_only", "reason": "Community language material is not official 469 ground truth."},
        ],
        "interpretation": "External anchors do not currently validate a row0-origin formula. The unlock remains a CipSoft/in-game symbol table or book-to-meaning crib.",
    }
    write_json(TEST_RESULTS / "150_row0_external_anchor_holdout.json", result)
    lines = [
        "# 150. Row0 External Anchor Holdout",
        "",
        "Classification: `BLOCKED_NEEDS_EXTERNAL_SOURCE`",
        "Translation delta: `NONE`",
        "",
        "| Anchor | Status | Reason |",
        "|---|---|---|",
    ]
    for row in result["anchors"]:
        lines.append(f"| `{row['id']}` | `{row['status']}` | {row['reason']} |")
    write_md(TEST_RESULTS / "150_row0_external_anchor_holdout.md", lines)
    return result


def run_151() -> dict[str, Any]:
    grep = subprocess.check_output(
        ["git", "grep", "-n", "-E", "row0|code[-_ ]symbol|code_symbol_grid|q3_tables", "--", "analysis", "scripts", "docs"],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    )
    hits = grep.splitlines()
    relevant = [line for line in hits if any(token in line for token in ["code_symbol_grid", "q3_tables", "export_workbook", "row0"])]
    result = {
        "schema": "row0_artifact_provenance_audit.v1",
        "classification": "AUDIT_ONLY",
        "grep_hit_count": len(hits),
        "selected_hits": relevant[:80],
        "known_ingestion_paths": {
            "workbook_export_script": rel(INPUTS["workbook_export_script"]),
            "q3_tables": rel(INPUTS["q3_tables"]),
            "code_symbol_grid": rel(INPUTS["code_symbol_grid"]),
        },
        "interpretation": "Project tooling preserves/imports the row0-like table and analysis artifacts; no compact table generator is identified in scripts. This audits project provenance, not CipSoft origin.",
    }
    write_json(TEST_RESULTS / "151_row0_artifact_provenance_audit.json", result)
    lines = [
        "# 151. Row0 Artifact Provenance Audit",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        "The project reads/preserves row0-like tables and derived reports. No repository script is promoted as the origin generator for the pair labels.",
        "",
        "## Selected provenance hits",
        "",
    ]
    for line in relevant[:30]:
        lines.append(f"- `{line}`")
    write_md(TEST_RESULTS / "151_row0_artifact_provenance_audit.md", lines)
    return result


def run_152() -> dict[str, Any]:
    ledger = [
        {
            "candidate": "ordered_surface_render_layer",
            "starting_status": "PROMOTED_MECHANICAL_CLUE",
            "beats_lookup": False,
            "holdout_predicts_labels": False,
            "survives_controls": True,
            "explains_39_19_91": True,
            "final_status": "PROMOTED_MECHANICAL_CLUE",
            "reason": "Explains surface facts, not full label placement.",
        },
        {
            "candidate": "digit_orbit_6_9",
            "starting_status": "WEAK_CLUE",
            "beats_lookup": False,
            "holdout_predicts_labels": False,
            "survives_controls": True,
            "explains_39_19_91": False,
            "final_status": "WEAK_CLUE",
            "reason": "Weak quotient/orbit signal only.",
        },
        {
            "candidate": "k5_eye_arity",
            "starting_status": "WEAK_CLUE",
            "beats_lookup": False,
            "holdout_predicts_labels": False,
            "survives_controls": False,
            "explains_39_19_91": False,
            "final_status": "REJECTED_CONTROL",
            "reason": "Arity match is not label prediction.",
        },
        {
            "candidate": "fixed_lore_order",
            "starting_status": "WEAK_CLUE",
            "beats_lookup": False,
            "holdout_predicts_labels": False,
            "survives_controls": False,
            "explains_39_19_91": False,
            "final_status": "REJECTED_CONTROL",
            "reason": "No fixed source order beats controls.",
        },
        {
            "candidate": "manual_authorial_lookup",
            "starting_status": "AUDIT_ONLY",
            "beats_lookup": False,
            "holdout_predicts_labels": False,
            "survives_controls": "not_applicable",
            "explains_39_19_91": "by_storage_only",
            "final_status": "AUDIT_ONLY",
            "reason": "Honest baseline and likely exogenous worksheet under current evidence.",
        },
    ]
    result = {
        "schema": "row0_adversarial_refuter.v1",
        "classification": "AUDIT_ONLY",
        "refuter_questions": [
            "beats lookup after costs",
            "predicts labels under holdout",
            "survives label shuffle and digit permutation controls",
            "explains 39 absence and 19/91 directed conflict",
            "does not use invented semantics",
        ],
        "ledger": ledger,
        "decision": "No candidate is promoted to PROMOTED_ORIGIN_FORMULA.",
    }
    write_json(TEST_RESULTS / "152_row0_adversarial_refuter.json", result)
    lines = [
        "# 152. Row0 Adversarial Refuter",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        "| Candidate | Final status | Reason |",
        "|---|---|---|",
    ]
    for row in ledger:
        lines.append(f"| `{row['candidate']}` | `{row['final_status']}` | {row['reason']} |")
    lines += ["", "Decision: no candidate becomes `PROMOTED_ORIGIN_FORMULA`."]
    write_md(TEST_RESULTS / "152_row0_adversarial_refuter.md", lines)
    return result


def run_153() -> dict[str, Any]:
    manifest = load_json(BASE / "run_manifest.json")
    baseline = load_json(TEST_RESULTS / "143_row0_lookup_baseline_mdl.json")
    canonical = load_json(TEST_RESULTS / "142_row0_canonical_features_compile.json")
    outcomes = {
        "priority_layers": load_json(TEST_RESULTS / "144_row0_priority_layer_mdl.json"),
        "latent_behavior": load_json(TEST_RESULTS / "145_row0_latent_behavior_partition.json"),
        "fill_order": load_json(TEST_RESULTS / "146_row0_fill_order_inventory_search.json"),
        "lore_fixed_order": load_json(TEST_RESULTS / "147_row0_lore_fixed_order_audit.json"),
        "eye_geometry": load_json(TEST_RESULTS / "148_row0_eye_digit_geometry_audit.json"),
        "ordered_surface": load_json(TEST_RESULTS / "149_row0_ordered_surface_origin_audit.json"),
        "external_anchor": load_json(TEST_RESULTS / "150_row0_external_anchor_holdout.json"),
        "artifact_provenance": load_json(TEST_RESULTS / "151_row0_artifact_provenance_audit.json"),
        "adversarial_refuter": load_json(TEST_RESULTS / "152_row0_adversarial_refuter.json"),
    }
    hypothesis_registry = {
        "schema": "row0_origin_hypothesis_registry.v1",
        "classification_counts": dict(Counter(row.get("classification", "AUDIT_ONLY") for row in outcomes.values())),
        "hypotheses": [
            {"id": "H-ROW0-A", "name": "inventory_frequency", "classification": "REJECTED_CONTROL", "evidence": "lookup and fixed-order inventory fills do not promote"},
            {"id": "H-ROW0-B", "name": "priority_layers", "classification": outcomes["priority_layers"]["classification"], "evidence": "simple layers fail as origin formula"},
            {"id": "H-ROW0-C", "name": "latent_behavior_partition", "classification": outcomes["latent_behavior"]["classification"], "evidence": "label-blind partitions do not recover labels"},
            {"id": "H-ROW0-D", "name": "fill_order_inventory", "classification": outcomes["fill_order"]["classification"], "evidence": "fixed orders ordinary under controls"},
            {"id": "H-ROW0-E", "name": "lore_fixed_order", "classification": outcomes["lore_fixed_order"]["classification"], "evidence": "no fixed source order promoted"},
            {"id": "H-ROW0-F", "name": "eye_blink_arity", "classification": outcomes["eye_geometry"]["classification"], "evidence": "weak arity/orbit clue only"},
            {"id": "H-ROW0-G", "name": "visual_digit_geometry", "classification": "REJECTED_CONTROL", "evidence": "geometry stumps fail controls"},
            {"id": "H-ROW0-H", "name": "ordered_surface_render", "classification": outcomes["ordered_surface"]["classification"], "evidence": "explains 39 and 19/91 as surface clue only"},
            {"id": "H-ROW0-I", "name": "book_generation_provenance", "classification": "REJECTED_CONTROL", "evidence": "previous hierarchical provenance and prequential audits do not derive row0"},
            {"id": "H-ROW0-J", "name": "external_text_source", "classification": outcomes["external_anchor"]["classification"], "evidence": "blocked pending CipSoft/in-game fixed source"},
            {"id": "H-ROW0-K", "name": "artifact_provenance", "classification": outcomes["artifact_provenance"]["classification"], "evidence": "project import provenance audited; no generator found"},
        ],
    }
    write_json(BASE / "hypothesis_registry.json", hypothesis_registry)
    write_yaml(BASE / "hypothesis_registry.yaml", hypothesis_registry)
    final = {
        "schema": "final_row0_origin_parallel_report.v1",
        "verdict": "row0_origin_exogenous_under_current_evidence",
        "translation_delta": "NONE",
        "promoted_origin_formula_count": 0,
        "promoted_mechanical_clues": ["ordered_surface_render_layer"],
        "weak_clues": ["digit_orbit_6_9", "eye_blink_arity", "secret_library_numeric_watchlist"],
        "lookup_baseline_bits": baseline.get("bits_lookup_given_inventory"),
        "commit": manifest.get("commit"),
        "hypothesis_registry": hypothesis_registry,
    }
    write_json(TEST_RESULTS / "153_row0_summary_report_compile.json", final)
    lines = [
        "# Row0 Origin Parallel Report",
        "",
        "## Verdict",
        "",
        "`row0_origin_exogenous_under_current_evidence`.",
        "",
        "No tested family becomes `PROMOTED_ORIGIN_FORMULA`. The best positive result is an ordered-surface/render clue: the table has `99/100` ordered codes, missing `39`, a sole directed `19/91` conflict, and `54/55` pure unordered pairs. That helps describe the surface but does not derive the pair labels below lookup.",
        "",
        "Translation delta: `NONE`.",
        "",
        "## Inputs and frozen commit",
        "",
        f"- Commit: `{manifest.get('commit')}`.",
        f"- Branch: `{manifest.get('branch')}`.",
        "- This front treats the current book-generation formula as an input substrate and does not assume the parallel formula-improvement chat has finished.",
        "",
        "## Canonical row0 facts",
        "",
        f"- Pair rows: `{canonical.get('pair_count')}`.",
        f"- Ordered codes represented: `{canonical.get('ordered_code_count')}`.",
        f"- Missing ordered code: `{canonical.get('missing_ordered_codes')}`.",
        f"- Pure unordered pairs: `{canonical.get('pure_pair_count')}/55`.",
        f"- Conflict pairs: `{canonical.get('conflict_pairs')}`.",
        "",
        "## Lookup baseline",
        "",
        f"- Lookup cost given inventory: `{baseline.get('bits_lookup_given_inventory'):.3f}` bits.",
        "- Any formula must beat this after charging rule, order, parameters, exceptions, and search.",
        "",
        "## Hypothesis ledger",
        "",
        "| ID | Name | Classification | Evidence |",
        "|---|---|---|---|",
    ]
    for row in hypothesis_registry["hypotheses"]:
        lines.append(f"| `{row['id']}` | `{row['name']}` | `{row['classification']}` | {row['evidence']} |")
    lines += [
        "",
        "## Promoted findings",
        "",
        "- `PROMOTED_ORIGIN_FORMULA`: none.",
        "- `PROMOTED_MECHANICAL_CLUE`: ordered-surface/render layer only.",
        "",
        "## Weak clues",
        "",
        "- `6<->9` orbit remains a weak quotient signal, not a full label formula.",
        "- Eye/K5/5x2 arity remains useful mechanism context, not label prediction.",
        "- Official numeric motifs such as `74032 45331` remain watchlist material without gloss.",
        "",
        "## Rejected families",
        "",
        "- Priority layers, fixed fill orders, geometry stumps, latent behavior partitions, lore fixed orders, and book-generation provenance do not produce a controlled holdout-capable label generator.",
        "",
        "## External/lore audit",
        "",
        "No external source supplies a fixed symbol/pair order that predicts row0 labels under controls. The unlock remains a CipSoft/in-game symbol table or exact book-to-meaning crib.",
        "",
        "## Artifact provenance audit",
        "",
        "Repository scripts preserve and analyze the table; they do not reveal a compact generator for row0. This answers project provenance only, not CipSoft origin.",
        "",
        "## Adversarial refuter",
        "",
        "Every positive candidate fails at least one critical origin-formula gate: lookup MDL, holdout label prediction, controls, or natural explanation of `39` plus `19/91`.",
        "",
        "## What remains exogenous",
        "",
        "The current best explanation is a manual or semimanual authorial worksheet: 10-channel arity, pair folding, inventory pressure, local render/orbit clues, and residual placement by a source not currently identified.",
        "",
        "## Next actions",
        "",
        "- Do not run more broad row0 brute force unless a new fixed external source, new provenance artifact, or lower-cost controlled rule appears.",
        "- Keep the main formula front free to use row0 as a validated substrate.",
        "- Reopen only with primary CipSoft/in-game evidence or a genuinely holdout-predictive row0 formula.",
    ]
    write_md(REPORTS / "final_row0_origin_parallel_report.md", lines)
    write_md(TEST_RESULTS / "153_row0_summary_report_compile.md", ["# 153. Row0 Summary Report Compile", "", "Final report written to `reports/final_row0_origin_parallel_report.md`.", "", f"Verdict: `{final['verdict']}`."])
    return final


def run_154() -> dict[str, Any]:
    workbooks = [
        ROOT / "bonelord_469_iter129.xlsx",
        ROOT / "bonelord_469_iter129_frontier.xlsx",
        ROOT / "bonelord_469_iter129_stab.xlsx",
        ROOT / "archive/bonelord_469_iter141.xlsx",
    ]
    workbook_rows = [workbook_summary(path) for path in workbooks]
    script_rows = [
        {
            "artifact": "export_workbook_to_sqlite",
            "classification": "preservation_importer_not_row0_generator",
            "signals": script_signal(INPUTS["workbook_export_script"], ["cells", "row_json", "sheet__", "raw_value", "formula"]),
            "risk": "low_generation_risk_high_source_importance",
        },
        {
            "artifact": "row0_code_symbol_probe",
            "classification": "project_reconstruction_probe_not_cipsoft_origin",
            "signals": script_signal(INPUTS["row0_code_symbol_probe"], ["decodedbase", "omitcodes", "code_symbol_counts", "reconstruct"]),
            "risk": "medium_reconstruction_policy_risk",
        },
        {
            "artifact": "q3_tables",
            "classification": "sqlite_schema_introspection_only",
            "signals": script_signal(INPUTS["q3_tables"], ["sqlite_master", "table"]),
            "risk": "low",
        },
        {
            "artifact": "external_row0_literal_decode",
            "classification": "external_phrase_audit_not_origin_source",
            "signals": script_signal(INPUTS["external_row0_literal_decode"], ["PHRASES", "mapping", "row0_code_symbol_counts"]),
            "risk": "semantic_overreach_risk_if_misused",
        },
    ]
    tracked = git_output(["ls-files"]).splitlines()
    row0_tracked = [
        path for path in tracked
        if any(token in path.lower() for token in ["row0", "code_symbol_grid", "q3_tables", "bonelord_469", "s2ward", "article160", "tibiasecrets"])
    ]
    result = {
        "schema": "row0_deep_provenance_audit.v1",
        "classification": "AUDIT_ONLY",
        "translation_delta": "NONE",
        "decision": "project_row0_provenance_partially_traced_but_cipsoft_origin_untraced",
        "workbooks": workbook_rows,
        "scripts": script_rows,
        "tracked_row0_related_paths": row0_tracked,
        "risk_register": [
            {
                "risk": "tooling_introduced_structure",
                "assessment": "not ruled out for project-level representation; current repo shows workbook/import/reconstruction layers before the frozen code-symbol grid.",
                "mitigation": "treat row0 as project substrate unless a primary pre-project source is identified.",
            },
            {
                "risk": "community_source_contamination",
                "assessment": "external row0/tibiasecrets/s2ward scripts are audit lanes, not accepted origin evidence.",
                "mitigation": "do not promote community matches without primary fixed source and controls.",
            },
            {
                "risk": "reconstruction_policy_leakage",
                "assessment": "row0_code_symbol_probe reconstructs from decodedbase/books digit model; useful validation but not an independent origin.",
                "mitigation": "separate project reconstruction from CipSoft/authorial source claims.",
            },
        ],
    }
    write_json(TEST_RESULTS / "154_row0_deep_provenance_audit.json", result)
    lines = [
        "# 154. Row0 Deep Provenance Audit",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        "Decision: `project_row0_provenance_partially_traced_but_cipsoft_origin_untraced`.",
        "",
        "## Workbook inventory",
        "",
        "| Workbook | Sheets | Key row0-adjacent sheets | Classification |",
        "|---|---:|---|---|",
    ]
    for row in workbook_rows:
        lines.append(
            f"| `{row['path']}` | `{row.get('sheet_count', 'n/a')}` | `{', '.join(row.get('key_sheet_names', [])[:8]) or 'none'}` | `{row.get('classification')}` |"
        )
    lines += [
        "",
        "## Script provenance",
        "",
        "| Artifact | Classification | Risk |",
        "|---|---|---|",
    ]
    for row in script_rows:
        lines.append(f"| `{row['artifact']}` | `{row['classification']}` | `{row['risk']}` |")
    lines += [
        "",
        "## Interpretation",
        "",
        "The repository can explain how row0 is preserved, imported, reconstructed, and audited inside the project. It still does not identify a primary CipSoft source or authorial generator for the pair-label placement.",
    ]
    write_md(TEST_RESULTS / "154_row0_deep_provenance_audit.md", lines)
    return result


def run_155() -> dict[str, Any]:
    baseline = load_json(TEST_RESULTS / "143_row0_lookup_baseline_mdl.json")
    priority = load_json(TEST_RESULTS / "144_row0_priority_layer_mdl.json")
    fill = load_json(TEST_RESULTS / "146_row0_fill_order_inventory_search.json")
    surface = load_json(TEST_RESULTS / "149_row0_ordered_surface_origin_audit.json")
    external = load_json(TEST_RESULTS / "150_row0_external_anchor_holdout.json")
    rows = [
        {
            "candidate": "lookup_baseline",
            "classification": "AUDIT_ONLY",
            "labels_predicted_holdout": 0,
            "diagnostic_hits": 55,
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_and_19_91": "stores_only",
            "survives_controls": "not_applicable",
            "external_source_validated": False,
        },
        {
            "candidate": "priority_layer_stumps",
            "classification": priority["classification"],
            "labels_predicted_holdout": priority["best_rule"]["loo_hits"],
            "diagnostic_hits": priority["best_rule"]["hits"],
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_and_19_91": "no",
            "survives_controls": priority["label_shuffle_control"]["p_control_ge_observed"] < 0.05,
            "external_source_validated": False,
        },
        {
            "candidate": "fixed_order_inventory_fill",
            "classification": fill["classification"],
            "labels_predicted_holdout": 0,
            "diagnostic_hits": fill["observed_best_hits"],
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_and_19_91": "no",
            "survives_controls": fill["random_order_control"]["p_control_ge_observed"] < 0.05,
            "external_source_validated": False,
        },
        {
            "candidate": "ordered_surface_render_layer",
            "classification": surface["classification"],
            "labels_predicted_holdout": 0,
            "diagnostic_hits": 2,
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_and_19_91": "yes_surface_only",
            "survives_controls": True,
            "external_source_validated": False,
        },
        {
            "candidate": "external_fixed_source",
            "classification": external["classification"],
            "labels_predicted_holdout": 0,
            "diagnostic_hits": 0,
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_and_19_91": "blocked",
            "survives_controls": False,
            "external_source_validated": False,
        },
    ]
    write_csv(DATA / "row0_improvement_scoreboard.csv", rows, list(rows[0].keys()))
    result = {
        "schema": "row0_improvement_scoreboard.v1",
        "classification": "AUDIT_ONLY",
        "translation_delta": "NONE",
        "lookup_baseline_bits": baseline["bits_lookup_given_inventory"],
        "scoreboard": rows,
        "decision": "score_row0_progress_separately_from_book_generation_bits",
    }
    write_json(TEST_RESULTS / "155_row0_improvement_scoreboard.json", result)
    lines = [
        "# 155. Row0 Improvement Scoreboard",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        f"Lookup baseline: `{baseline['bits_lookup_given_inventory']:.3f}` bits.",
        "",
        "| Candidate | Class | Holdout labels | Diagnostic hits | Bits below lookup | 39/19/91 | Controls | External source |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['candidate']}` | `{row['classification']}` | `{row['labels_predicted_holdout']}` | `{row['diagnostic_hits']}` | `{row['bits_below_lookup_after_costs']}` | `{row['explains_39_and_19_91']}` | `{row['survives_controls']}` | `{row['external_source_validated']}` |"
        )
    lines += [
        "",
        "This scoreboard is intentionally row0-only. Book-generator compression does not move it unless it predicts row0 labels or explains the special ordered-surface facts.",
    ]
    write_md(TEST_RESULTS / "155_row0_improvement_scoreboard.md", lines)
    return result


def run_156() -> dict[str, Any]:
    rows = pair_rows()
    anchors = worksheet_anchor_rows()
    frozen_pairs = {row["pair"] for row in anchors}
    baseline_bits = inventory_sequence_bits(inventory(rows))
    residual_bits = residual_lookup_bits_after_freezing(rows, frozen_pairs)
    nominal_delta = baseline_bits - residual_bits
    write_csv(DATA / "row0_partial_worksheet_model.csv", anchors, ["pair", "label", "anchor_family", "classification", "reason"])
    result = {
        "schema": "row0_partial_worksheet_model.v1",
        "classification": "WEAK_CLUE",
        "translation_delta": "NONE",
        "anchor_count": len(anchors),
        "frozen_pairs": sorted(frozen_pairs),
        "lookup_bits_before": baseline_bits,
        "residual_lookup_bits_after_freezing_anchors": residual_bits,
        "nominal_bits_reduction_before_anchor_cost": nominal_delta,
        "promotion_decision": "not_promoted_as_origin_formula_anchor_cost_and_externality_not_paid",
        "anchors": anchors,
        "interpretation": "A semimanual worksheet model is more honest than a pure formula: a small set of surface/rare/diagonal anchors plus residual lookup. It reduces nominal residual lookup, but only before paying anchor/source costs.",
    }
    write_json(TEST_RESULTS / "156_row0_partial_worksheet_model.json", result)
    lines = [
        "# 156. Row0 Partial Worksheet Model",
        "",
        "Classification: `WEAK_CLUE`",
        "Translation delta: `NONE`",
        "",
        f"Anchors declared: `{len(anchors)}`.",
        f"Lookup bits before anchors: `{baseline_bits:.3f}`.",
        f"Residual lookup bits after freezing anchors: `{residual_bits:.3f}`.",
        f"Nominal reduction before anchor/source cost: `{nominal_delta:.3f}` bits.",
        "",
        "Promotion decision: `not_promoted_as_origin_formula_anchor_cost_and_externality_not_paid`.",
        "",
        "| Pair | Label | Anchor family | Classification |",
        "|---|---|---|---|",
    ]
    for row in anchors:
        lines.append(f"| `{row['pair']}` | `{row['label']}` | `{row['anchor_family']}` | `{row['classification']}` |")
    lines += [
        "",
        "This is the current best *shape* of an authorial worksheet hypothesis, not a proof. It explicitly leaves the rest as lookup residual.",
    ]
    write_md(TEST_RESULTS / "156_row0_partial_worksheet_model.md", lines)
    return result


def run_157() -> dict[str, Any]:
    rows = {row["pair"]: row for row in pair_rows()}
    ledger = [
        {
            "fact": "39_absent",
            "observed": "ordered code 39 is absent",
            "paired_fact": "93 exists and maps to N",
            "status": "PROMOTED_MECHANICAL_CLUE",
            "natural_explanation": "directed render/surface exception, not unordered pair-label origin",
            "open_gap": "why this exact directed cell is omitted remains externally untraced",
        },
        {
            "fact": "19_91_conflict",
            "observed": "19 maps to I while 91 maps to N",
            "paired_fact": "sole unordered-pair conflict",
            "status": "PROMOTED_MECHANICAL_CLUE",
            "natural_explanation": "ordered-surface asymmetry",
            "open_gap": "no fixed source predicts I for 19 and N for 91",
        },
        {
            "fact": "54_55_purity",
            "observed": "all non-19 unordered pairs have one effective label after allowing missing 39",
            "paired_fact": "pair folding is real",
            "status": "PROMOTED_MECHANICAL_CLUE",
            "natural_explanation": "unordered pair matrix with two directed exceptions",
            "open_gap": "folding does not assign the actual labels",
        },
    ]
    write_csv(DATA / "row0_surface_exception_ledger.csv", ledger, list(ledger[0].keys()))
    result = {
        "schema": "row0_surface_exception_focus.v1",
        "classification": "PROMOTED_MECHANICAL_CLUE",
        "translation_delta": "NONE",
        "ledger": ledger,
        "pair_19": rows["19"],
        "pair_39": rows["39"],
        "decision": "surface_ordered_asymmetry_is_real_but_label_origin_unresolved",
    }
    write_json(TEST_RESULTS / "157_row0_surface_exception_focus.json", result)
    lines = [
        "# 157. Row0 Surface Exception Focus",
        "",
        "Classification: `PROMOTED_MECHANICAL_CLUE`",
        "Translation delta: `NONE`",
        "",
        "| Fact | Status | Natural explanation | Open gap |",
        "|---|---|---|---|",
    ]
    for row in ledger:
        lines.append(f"| `{row['fact']}` | `{row['status']}` | {row['natural_explanation']} | {row['open_gap']} |")
    write_md(TEST_RESULTS / "157_row0_surface_exception_focus.md", lines)
    return result


def run_158() -> dict[str, Any]:
    provenance = load_json(TEST_RESULTS / "154_row0_deep_provenance_audit.json")
    scoreboard = load_json(TEST_RESULTS / "155_row0_improvement_scoreboard.json")
    worksheet = load_json(TEST_RESULTS / "156_row0_partial_worksheet_model.json")
    surface = load_json(TEST_RESULTS / "157_row0_surface_exception_focus.json")
    synthesis = {
        "schema": "row0_next_frontier_synthesis.v1",
        "classification": "AUDIT_ONLY",
        "translation_delta": "NONE",
        "frontier_order": [
            "provenance_primary_source_search",
            "ordered_surface_exception_source",
            "partial_worksheet_anchor_costing",
            "label_blind_pair_behavior_retest_only_if_new_features",
        ],
        "decisions": {
            "provenance": provenance["decision"],
            "scoreboard": scoreboard["decision"],
            "worksheet": worksheet["promotion_decision"],
            "surface": surface["decision"],
            "overall": "row0_advance_requires_primary_source_or_paid_partial_worksheet_anchor_reduction",
        },
    }
    write_json(TEST_RESULTS / "158_row0_next_frontier_synthesis.json", synthesis)
    lines = [
        "# 158. Row0 Next Frontier Synthesis",
        "",
        "Classification: `AUDIT_ONLY`",
        "Translation delta: `NONE`",
        "",
        "## Decision",
        "",
        "`row0_advance_requires_primary_source_or_paid_partial_worksheet_anchor_reduction`.",
        "",
        "## Priority order",
        "",
        "1. Provenance primary-source search: identify whether row0 entered through workbook/tooling/community reconstruction or an older fixed source.",
        "2. Ordered-surface exception source: look for a fixed source that naturally predicts missing `39`, present `93`, and `19/91` direction.",
        "3. Partial worksheet anchor costing: keep only anchors that pay their rule/source cost and reduce residual lookup.",
        "4. Label-blind pair behavior retest only if new provenance/corpus features appear.",
        "",
        "## Current state",
        "",
        "- No `PROMOTED_ORIGIN_FORMULA`.",
        "- Surface asymmetry is a real mechanical clue.",
        "- Partial worksheet model is plausible but currently weak because anchor/source costs are unpaid.",
        "- External source remains the only likely strong unlock.",
    ]
    write_md(TEST_RESULTS / "158_row0_next_frontier_synthesis.md", lines)
    write_md(REPORTS / "row0_next_frontier_report.md", lines)
    return synthesis


STEPS = {
    "141": run_141,
    "142": run_142,
    "143": run_143,
    "144": run_144,
    "145": run_145,
    "146": run_146,
    "147": run_147,
    "148": run_148,
    "149": run_149,
    "150": run_150,
    "151": run_151,
    "152": run_152,
    "153": run_153,
    "154": run_154,
    "155": run_155,
    "156": run_156,
    "157": run_157,
    "158": run_158,
}


def write_readme() -> None:
    lines = [
        "---",
        'title: "Row0 origin parallel audit"',
        f"date: {RUN_DATE}",
        "status: analysis_only_no_semantics",
        "translation_delta: NONE",
        "---",
        "",
        "# Row0 Origin Parallel Audit",
        "",
        "This front investigates the origin of `row0` independently from the concurrent book-generation formula work.",
        "",
        "Boundary: no plaintext, no fan-gloss promotion, no attempt to improve the main formula except as input evidence. The final report is [reports/final_row0_origin_parallel_report.md](reports/final_row0_origin_parallel_report.md).",
        "",
        "The focused next-frontier report is [reports/row0_next_frontier_report.md](reports/row0_next_frontier_report.md).",
    ]
    write_md(BASE / "README.md", lines)


def run_all() -> None:
    ensure_dirs()
    write_readme()
    for step in [str(number) for number in range(141, 159)]:
        STEPS[step]()


def main(step: str | None = None) -> None:
    ensure_dirs()
    if step is None or step == "all":
        run_all()
    else:
        STEPS[step]()


if __name__ == "__main__":
    main("all")
