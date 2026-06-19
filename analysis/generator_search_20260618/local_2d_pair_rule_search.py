#!/usr/bin/env python3
"""Local 2D/CA-style rule search for the 469 unordered pair table.

This pass asks whether the 55 labels in the triangular 10x10 unordered-pair
table can be predicted from already-filled local neighbors under plausible fill
orders. It is mechanical only: no plaintext, glossary, or translation is
promoted.
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

OUT_JSON = HERE / "local_2d_pair_rule_results.json"
OUT_MD = HERE / "local_2d_pair_rule_report.md"

SIGMA = "*ABCEFILNORSTV"
RANDOM_SEED = 46920260619
CONTROL_TRIALS = 300

LORE_DIGIT_SETS = {
    "469": {4, 6, 9},
    "3478": {3, 4, 7, 8},
    "43153": {1, 3, 4, 5},
    "honeminas": {1, 3, 4, 5, 7, 8},
    "missing39": {3, 9},
    "conflict19": {1, 9},
    "tape_edges_33_66": {3, 6},
}

DIRECTIONS = {
    "W": (0, -1),
    "N": (-1, 0),
    "NW": (-1, -1),
    "NE": (-1, 1),
    "E": (0, 1),
    "S": (1, 0),
    "SW": (1, -1),
    "SE": (1, 1),
}

COPY_PRIORITY = ("W", "N", "NW", "NE", "E", "S", "SW", "SE")


MODEL_DEFS = [
    {
        "name": "copy_left",
        "kind": "copy",
        "direction": "W",
        "complexity_bits": 8.0,
        "description": "Copy filled left neighbor, else prefix majority.",
    },
    {
        "name": "copy_up",
        "kind": "copy",
        "direction": "N",
        "complexity_bits": 8.0,
        "description": "Copy filled upper neighbor, else prefix majority.",
    },
    {
        "name": "copy_diag",
        "kind": "copy",
        "direction": "NW",
        "complexity_bits": 8.0,
        "description": "Copy filled upper-left diagonal neighbor, else prefix majority.",
    },
    {
        "name": "copy_previous_cell",
        "kind": "copy_previous",
        "complexity_bits": 7.0,
        "description": "Copy previous cell in the candidate fill order.",
    },
    {
        "name": "copy_first_local_neighbor",
        "kind": "copy_first",
        "directions": COPY_PRIORITY,
        "complexity_bits": 11.0,
        "description": "Copy first available local neighbor in W/N/NW/NE/E/S/SW/SE priority.",
    },
    {
        "name": "neighbor_majority",
        "kind": "neighbor_majority",
        "complexity_bits": 10.0,
        "description": "Predict the majority label among already-filled 8-neighbors.",
    },
    {
        "name": "majority_by_neighbor_signature",
        "kind": "signature_backoff",
        "signatures": ["neighbor_signature"],
        "complexity_bits": 16.0,
        "description": "Online majority keyed by direction-labeled filled-neighbor signature.",
    },
    {
        "name": "majority_by_neighbor_multiset",
        "kind": "signature_backoff",
        "signatures": ["neighbor_multiset", "neighbor_majority"],
        "complexity_bits": 14.0,
        "description": "Online majority keyed by unordered filled-neighbor label multiset.",
    },
    {
        "name": "left_up_diag_backoff",
        "kind": "signature_backoff",
        "signatures": ["left_up_diag", "core_signature", "neighbor_majority"],
        "complexity_bits": 18.0,
        "description": "Back off from W/N/NW label template to local majority.",
    },
    {
        "name": "row_col_digit_neighbor_backoff",
        "kind": "signature_backoff",
        "signatures": [
            "geom_neighbor_core",
            "shape_neighbor_core",
            "row_bucket_neighbor",
            "digit_neighbor_core",
            "shape_coarse",
            "neighbor_majority",
        ],
        "complexity_bits": 24.0,
        "description": "Row/column/digit geometry plus already-filled neighbor labels.",
    },
    {
        "name": "lore_seed_neighbor_backoff",
        "kind": "signature_backoff",
        "signatures": [
            "seed_469_neighbor",
            "seed_3478_neighbor",
            "seed_honeminas_neighbor",
            "seed_missing39_neighbor",
            "neighbor_multiset",
        ],
        "complexity_bits": 24.0,
        "description": "Lore-seed geometry classes plus local neighbor labels.",
    },
    {
        "name": "small_decision_list_local_template",
        "kind": "decision_list",
        "max_rules": 3,
        "complexity_bits": 28.0,
        "description": "Online greedy decision list over local templates, with majority fallback.",
    },
]

PREDICATE_FEATURES = [
    "diag",
    "border",
    "edge_distance",
    "center_bin",
    "row_bucket",
    "col_bucket",
    "diff_bucket",
    "sum_mod3",
    "diff_mod3",
    "parity_pair",
    "dir_W",
    "dir_N",
    "dir_NW",
    "dir_NE",
    "dir_E",
    "dir_S",
    "dir_SW",
    "dir_SE",
    "neighbor_count_bucket",
    "neighbor_majority",
    "neighbor_multiset",
    "core_signature",
    "left_up_diag",
    "prev_label",
    "shape_coarse",
    "geom_neighbor_core",
    "shape_neighbor_core",
    "digit_neighbor_core",
    "seed_469_class",
    "seed_3478_class",
    "seed_honeminas_class",
    "seed_missing39_class",
    "seed_conflict19_class",
    "seed_469_neighbor",
    "seed_3478_neighbor",
    "seed_honeminas_neighbor",
    "seed_missing39_neighbor",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def natural_pairs() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(i, 10)]


def parse_pair(pair: str) -> tuple[int, int]:
    return int(pair[0]), int(pair[1])


def pair_id(a: int, b: int) -> str:
    return f"{a}{b}"


def valid_pair(a: int, b: int) -> bool:
    return 0 <= a <= b <= 9


def primary_pair_symbol(pair_table: dict[str, dict], pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def acceptable_pair_symbols(pair_table: dict[str, dict], pair: str) -> set[str]:
    return set(pair_table[pair]["symbols"])


def sigma_index(symbol: str) -> int:
    try:
        return SIGMA.index(symbol)
    except ValueError:
        return len(SIGMA)


def mode(values: list[str], default: str) -> str:
    if not values:
        return default
    counts = Counter(values)
    return max(counts, key=lambda item: (counts[item], -sigma_index(item), item))


def counter_mode(counter: Counter[str], default: str) -> str:
    if not counter:
        return default
    return max(counter, key=lambda item: (counter[item], -sigma_index(item), item))


def row_bucket(value: int) -> str:
    if value <= 2:
        return "low"
    if value <= 6:
        return "mid"
    return "high"


def diff_bucket(value: int) -> str:
    if value == 0:
        return "diag"
    if value <= 2:
        return "near"
    if value <= 5:
        return "mid"
    return "far"


def center_bin(a: int, b: int) -> str:
    score = abs(a - 4.5) + abs(b - 4.5)
    if score <= 3.0:
        return "center"
    if score <= 6.0:
        return "middle"
    return "outer"


def edge_distance(a: int, b: int) -> int:
    return min(a, 9 - b, b - a)


def seed_class(a: int, b: int, digits: set[int]) -> str:
    left = a in digits
    right = b in digits
    if left and right:
        return "both"
    if left or right:
        return "one"
    return "none"


def seed_distance(a: int, b: int, digits: set[int]) -> int:
    return min(abs(a - digit) + abs(b - digit) for digit in digits)


def unique_order(sequence: list[str]) -> list[str]:
    expected = set(natural_pairs())
    got = set(sequence)
    if got != expected or len(sequence) != len(expected):
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        raise ValueError(f"bad order missing={missing} extra={extra} len={len(sequence)}")
    return sequence


def build_orders() -> dict[str, list[str]]:
    pairs = natural_pairs()
    orders: dict[str, list[str]] = {
        "row_major": pairs,
        "row_major_reverse": list(reversed(pairs)),
        "col_major": [f"{i}{j}" for j in range(10) for i in range(j + 1)],
        "col_major_reverse": list(reversed([f"{i}{j}" for j in range(10) for i in range(j + 1)])),
        "sum": sorted(pairs, key=lambda p: (sum(parse_pair(p)), parse_pair(p)[0], parse_pair(p)[1])),
        "sum_reverse": sorted(pairs, key=lambda p: (sum(parse_pair(p)), parse_pair(p)[0], parse_pair(p)[1]), reverse=True),
        "diff": sorted(pairs, key=lambda p: (parse_pair(p)[1] - parse_pair(p)[0], parse_pair(p)[0], parse_pair(p)[1])),
        "diff_reverse": sorted(pairs, key=lambda p: (parse_pair(p)[1] - parse_pair(p)[0], parse_pair(p)[0], parse_pair(p)[1]), reverse=True),
        "diagonal_first": [f"{i}{i}" for i in range(10)]
        + [p for p in sorted(pairs, key=lambda p: (parse_pair(p)[1] - parse_pair(p)[0], parse_pair(p)[0], parse_pair(p)[1])) if p[0] != p[1]],
        "diagonal_last": [p for p in pairs if p[0] != p[1]] + [f"{i}{i}" for i in range(10)],
        "center_first": sorted(
            pairs,
            key=lambda p: (
                abs(parse_pair(p)[0] - 4.5) + abs(parse_pair(p)[1] - 4.5),
                edge_distance(*parse_pair(p)),
                parse_pair(p)[1] - parse_pair(p)[0],
                p,
            ),
        ),
        "border_first": sorted(
            pairs,
            key=lambda p: (
                edge_distance(*parse_pair(p)),
                abs(parse_pair(p)[0] - 4.5) + abs(parse_pair(p)[1] - 4.5),
                p,
            ),
        ),
    }
    for name, digits in LORE_DIGIT_SETS.items():
        orders[f"lore_seed_{name}"] = sorted(
            pairs,
            key=lambda p, ds=digits: (
                {"both": 0, "one": 1, "none": 2}[seed_class(*parse_pair(p), ds)],
                seed_distance(*parse_pair(p), ds),
                parse_pair(p)[1] - parse_pair(p)[0],
                sum(parse_pair(p)),
                p,
            ),
        )
    return {name: unique_order(order) for name, order in orders.items()}


def neighbor_labels(pair: str, filled: set[str], labels_by_pair: dict[str, str]) -> dict[str, str]:
    a, b = parse_pair(pair)
    out = {}
    for name, (da, db) in DIRECTIONS.items():
        na, nb = a + da, b + db
        if valid_pair(na, nb):
            neighbor = pair_id(na, nb)
            out[name] = labels_by_pair[neighbor] if neighbor in filled else "."
        else:
            out[name] = "#"
    return out


def feature_dict(pair: str, filled: set[str], prior_pairs: list[str], labels_by_pair: dict[str, str]) -> dict[str, Any]:
    a, b = parse_pair(pair)
    neighbors = neighbor_labels(pair, filled, labels_by_pair)
    filled_neighbor_labels = [label for label in neighbors.values() if label not in {".", "#"}]
    neighbor_count = len(filled_neighbor_labels)
    neigh_majority = mode(filled_neighbor_labels, ".")
    neigh_multiset = "".join(sorted(filled_neighbor_labels, key=lambda item: (sigma_index(item), item))) or "."
    neigh_signature = "|".join(
        f"{direction}:{neighbors[direction]}" for direction in DIRECTIONS if neighbors[direction] not in {".", "#"}
    ) or "."
    edge = edge_distance(a, b)
    features: dict[str, Any] = {
        "row": a,
        "col": b,
        "diff": b - a,
        "sum": a + b,
        "diag": a == b,
        "border": edge == 0,
        "edge_distance": edge,
        "center_bin": center_bin(a, b),
        "row_bucket": row_bucket(a),
        "col_bucket": row_bucket(b),
        "diff_bucket": diff_bucket(b - a),
        "sum_mod2": (a + b) % 2,
        "sum_mod3": (a + b) % 3,
        "diff_mod2": (b - a) % 2,
        "diff_mod3": (b - a) % 3,
        "parity_pair": (a % 2, b % 2),
        "neighbor_count": neighbor_count,
        "neighbor_count_bucket": "none" if neighbor_count == 0 else "one" if neighbor_count == 1 else "many",
        "neighbor_majority": neigh_majority,
        "neighbor_multiset": neigh_multiset,
        "neighbor_signature": neigh_signature,
        "prev_label": labels_by_pair[prior_pairs[-1]] if prior_pairs else ".",
        "prev2_label": labels_by_pair[prior_pairs[-2]] if len(prior_pairs) >= 2 else ".",
    }
    for direction in DIRECTIONS:
        features[f"dir_{direction}"] = neighbors[direction]
    features["core_signature"] = (features["dir_W"], features["dir_N"], features["dir_NW"], features["dir_NE"])
    features["left_up_diag"] = (features["dir_W"], features["dir_N"], features["dir_NW"])
    features["shape_coarse"] = (
        features["diff_bucket"],
        features["edge_distance"],
        features["center_bin"],
        features["sum_mod3"],
    )
    features["geom_neighbor_core"] = (
        features["row_bucket"],
        features["col_bucket"],
        features["diff_bucket"],
        features["edge_distance"],
        features["dir_W"],
        features["dir_N"],
        features["dir_NW"],
    )
    features["shape_neighbor_core"] = (
        features["shape_coarse"],
        features["neighbor_count_bucket"],
        features["neighbor_majority"],
        features["dir_W"],
        features["dir_N"],
    )
    features["row_bucket_neighbor"] = (
        features["row_bucket"],
        features["col_bucket"],
        features["neighbor_multiset"],
    )
    features["digit_neighbor_core"] = (
        features["parity_pair"],
        features["sum_mod3"],
        features["diff_mod3"],
        features["neighbor_majority"],
        features["prev_label"],
    )
    for seed_name, digits in LORE_DIGIT_SETS.items():
        klass = seed_class(a, b, digits)
        features[f"seed_{seed_name}_class"] = klass
        features[f"seed_{seed_name}_neighbor"] = (klass, features["neighbor_majority"], features["neighbor_multiset"])
    return features


def fallback_label(train_obs: list[dict], inventory_default: str) -> str:
    return mode([obs["label"] for obs in train_obs], inventory_default)


def predict_signature_backoff(
    train_obs: list[dict],
    current_features: dict[str, Any],
    signatures: list[str],
    inventory_default: str,
) -> str:
    fallback = fallback_label(train_obs, inventory_default)
    for signature in signatures:
        table: dict[Any, Counter[str]] = defaultdict(Counter)
        for obs in train_obs:
            table[obs["features"][signature]][obs["label"]] += 1
        key = current_features[signature]
        if key in table:
            return counter_mode(table[key], fallback)
    return fallback


def candidate_tests(train_obs: list[dict]) -> list[tuple[str, Any, int]]:
    tests = []
    for feature in PREDICATE_FEATURES:
        buckets: dict[Any, int] = defaultdict(int)
        for obs in train_obs:
            buckets[obs["features"][feature]] += 1
        for value, count in buckets.items():
            if count < 2 or count == len(train_obs):
                continue
            tests.append((feature, value, count))
    tests.sort(key=lambda item: (item[0], str(item[1])))
    return tests


def train_decision_list(train_obs: list[dict], max_rules: int, inventory_default: str) -> dict[str, Any]:
    if not train_obs:
        return {"rules": [], "default": inventory_default}
    labels = [obs["label"] for obs in train_obs]
    remaining = set(range(len(train_obs)))
    assigned_hits = 0
    default = mode(labels, inventory_default)
    current_hits = sum(label == default for label in labels)
    rules = []
    tests = candidate_tests(train_obs)
    for _step in range(max_rules):
        best = None
        for feature, value, cover_size_hint in tests:
            cover = [idx for idx in remaining if train_obs[idx]["features"][feature] == value]
            if len(cover) < 2:
                continue
            new_remaining = remaining - set(cover)
            remaining_labels = [labels[idx] for idx in sorted(new_remaining)]
            new_default = mode(remaining_labels, default)
            default_hits = sum(labels[idx] == new_default for idx in new_remaining)
            for symbol in SIGMA:
                rule_hits = sum(labels[idx] == symbol for idx in cover)
                false_hits = len(cover) - rule_hits
                total_hits = assigned_hits + rule_hits + default_hits
                gain = total_hits - current_hits
                rank = (gain, rule_hits, -false_hits, -cover_size_hint, -sigma_index(symbol), feature, str(value))
                if best is None or rank > best["rank"]:
                    best = {
                        "rank": rank,
                        "feature": feature,
                        "value": value,
                        "symbol": symbol,
                        "cover": cover,
                        "hits": rule_hits,
                        "false_hits": false_hits,
                        "default": new_default,
                        "total_hits": total_hits,
                    }
        if best is None or best["rank"][0] <= 0:
            break
        rules.append(
            {
                "feature": best["feature"],
                "value": best["value"],
                "symbol": best["symbol"],
                "cover_size": len(best["cover"]),
                "train_hits": best["hits"],
                "train_false_hits": best["false_hits"],
            }
        )
        remaining -= set(best["cover"])
        assigned_hits += best["hits"]
        default = best["default"]
        current_hits = best["total_hits"]
    return {"rules": rules, "default": default}


def predict_decision_list(train_obs: list[dict], current_features: dict[str, Any], model: dict, inventory_default: str) -> tuple[str, dict]:
    trained = train_decision_list(train_obs, model["max_rules"], inventory_default)
    for rule in trained["rules"]:
        if current_features[rule["feature"]] == rule["value"]:
            return rule["symbol"], {"rule_count": len(trained["rules"]), "matched_rule": rule["feature"]}
    return trained["default"], {"rule_count": len(trained["rules"]), "matched_rule": "default"}


def predict_model(
    model: dict,
    train_obs: list[dict],
    current_features: dict[str, Any],
    inventory_default: str,
) -> tuple[str, dict]:
    fallback = fallback_label(train_obs, inventory_default)
    kind = model["kind"]
    if kind == "copy":
        label = current_features[f"dir_{model['direction']}"]
        return (label if label not in {".", "#"} else fallback), {}
    if kind == "copy_previous":
        label = current_features["prev_label"]
        return (label if label != "." else fallback), {}
    if kind == "copy_first":
        for direction in model["directions"]:
            label = current_features[f"dir_{direction}"]
            if label not in {".", "#"}:
                return label, {"direction": direction}
        return fallback, {"direction": "fallback"}
    if kind == "neighbor_majority":
        label = current_features["neighbor_majority"]
        return (label if label != "." else fallback), {}
    if kind == "signature_backoff":
        return predict_signature_backoff(train_obs, current_features, model["signatures"], inventory_default), {}
    if kind == "decision_list":
        return predict_decision_list(train_obs, current_features, model, inventory_default)
    raise ValueError(f"unknown model kind: {kind}")


def json_safe(value: Any) -> Any:
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    return value


def evaluate_order_model(
    order_name: str,
    order: list[str],
    model: dict,
    labels_by_pair: dict[str, str],
    acceptable_by_pair: dict[str, set[str]],
    inventory_default: str,
    order_bits: float,
    model_bits: float,
    keep_details: bool,
) -> dict[str, Any]:
    filled: set[str] = set()
    prior_pairs: list[str] = []
    train_obs: list[dict] = []
    predictions = []
    aux_counter = Counter()
    for pair in order:
        features = feature_dict(pair, filled, prior_pairs, labels_by_pair)
        prediction, aux = predict_model(model, train_obs, features, inventory_default)
        predictions.append(prediction)
        if "rule_count" in aux:
            aux_counter["decision_list_steps"] += 1
            aux_counter["decision_list_rule_count_sum"] += aux["rule_count"]
            aux_counter[f"matched_{aux.get('matched_rule', 'unknown')}"] += 1
        train_obs.append({"pair": pair, "label": labels_by_pair[pair], "features": features})
        filled.add(pair)
        prior_pairs.append(pair)

    actual = [labels_by_pair[pair] for pair in order]
    primary_hits = sum(pred == label for pred, label in zip(predictions, actual))
    acceptable_hits = sum(pred in acceptable_by_pair[pair] for pred, pair in zip(predictions, order))
    n = len(order)
    lookup_bits = n * math.log2(len(SIGMA))
    exception_unit_bits = math.log2(n) + math.log2(len(SIGMA))
    rough_model_bits = order_bits + model_bits
    primary_misses = n - primary_hits
    acceptable_misses = n - acceptable_hits
    primary_mdl = rough_model_bits + primary_misses * exception_unit_bits
    acceptable_mdl = rough_model_bits + acceptable_misses * exception_unit_bits
    row: dict[str, Any] = {
        "order": order_name,
        "model": model["name"],
        "model_kind": model["kind"],
        "primary_hits": primary_hits,
        "primary_accuracy": primary_hits / n,
        "acceptable_hits": acceptable_hits,
        "acceptable_accuracy": acceptable_hits / n,
        "primary_misses": primary_misses,
        "acceptable_misses": acceptable_misses,
        "lookup_cost_bits": lookup_bits,
        "rough_model_bits": rough_model_bits,
        "primary_mdl_cost_bits": primary_mdl,
        "primary_mdl_gain_vs_lookup_bits": lookup_bits - primary_mdl,
        "primary_lookup_cost_ratio": primary_mdl / lookup_bits,
        "acceptable_mdl_cost_bits": acceptable_mdl,
        "acceptable_mdl_gain_vs_lookup_bits": lookup_bits - acceptable_mdl,
        "acceptable_lookup_cost_ratio": acceptable_mdl / lookup_bits,
        "target_sequence": "".join(actual),
        "prediction_sequence": "".join(predictions),
    }
    if aux_counter["decision_list_steps"]:
        row["mean_dynamic_rule_count"] = aux_counter["decision_list_rule_count_sum"] / aux_counter["decision_list_steps"]
    if keep_details:
        row["misses"] = [
            {"pair": pair, "actual": label, "predicted": pred}
            for pair, label, pred in zip(order, actual, predictions)
            if label != pred
        ]
        row["acceptable_misses_detail"] = [
            {
                "pair": pair,
                "acceptable": sorted(acceptable_by_pair[pair], key=lambda item: (sigma_index(item), item)),
                "predicted": pred,
            }
            for pair, pred in zip(order, predictions)
            if pred not in acceptable_by_pair[pair]
        ]
    return row


def best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        rows,
        key=lambda row: (
            row["primary_hits"],
            row["primary_mdl_gain_vs_lookup_bits"],
            row["acceptable_hits"],
            -row["primary_mdl_cost_bits"],
            row["order"],
            row["model"],
        ),
    )


def run_search(
    orders: dict[str, list[str]],
    labels_by_pair: dict[str, str],
    acceptable_by_pair: dict[str, set[str]],
    keep_details: bool,
    models: list[dict[str, Any]] | None = None,
    model_count_for_bits: int | None = None,
) -> dict[str, Any]:
    if models is None:
        models = MODEL_DEFS
    inventory_default = mode(list(labels_by_pair.values()), "E")
    order_bits = math.log2(len(orders))
    search_rows = []
    model_search_bits = math.log2(model_count_for_bits if model_count_for_bits is not None else len(models))
    for order_name, order in orders.items():
        for model in models:
            row = evaluate_order_model(
                order_name,
                order,
                model,
                labels_by_pair,
                acceptable_by_pair,
                inventory_default,
                order_bits,
                model["complexity_bits"] + model_search_bits,
                keep_details=keep_details,
            )
            search_rows.append(row)
    sorted_rows = sorted(
        search_rows,
        key=lambda row: (
            -row["primary_hits"],
            -row["primary_mdl_gain_vs_lookup_bits"],
            -row["acceptable_hits"],
            row["primary_mdl_cost_bits"],
            row["order"],
            row["model"],
        ),
    )
    per_order = {}
    for order_name in orders:
        order_rows = [row for row in sorted_rows if row["order"] == order_name]
        per_order[order_name] = best_row(order_rows)
    return {
        "best": sorted_rows[0],
        "top_rows": sorted_rows[:25],
        "rows": sorted_rows if keep_details else [],
        "per_order_best": per_order if keep_details else {},
    }


def summarize_high(values: list[float], observed: float) -> dict[str, Any]:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5 if len(values) > 1 else 0.0
    return {
        "observed": observed,
        "control_mean": mean,
        "control_sd": sd,
        "control_min": min(values),
        "control_max": max(values),
        "z_good_direction": (observed - mean) / sd if sd else 0.0,
        "p_ge": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def control_search(
    orders: dict[str, list[str]],
    observed_best: dict[str, Any],
    observed_labels: dict[str, str],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    pairs = natural_pairs()
    labels = [observed_labels[pair] for pair in pairs]
    best_hits = []
    best_mdl_gain = []
    best_accuracy = []
    best_lookup_ratio = []
    best_rows = []
    control_models = [model for model in MODEL_DEFS if model["kind"] != "decision_list"]
    excluded_models = [model["name"] for model in MODEL_DEFS if model["kind"] == "decision_list"]
    current = labels[:]
    for _trial in range(CONTROL_TRIALS):
        rng.shuffle(current)
        shuffled_labels = dict(zip(pairs, current))
        shuffled_acceptables = {pair: {label} for pair, label in shuffled_labels.items()}
        trial = run_search(
            orders,
            shuffled_labels,
            shuffled_acceptables,
            keep_details=False,
            models=control_models,
            model_count_for_bits=len(MODEL_DEFS),
        )["best"]
        best_hits.append(trial["primary_hits"])
        best_mdl_gain.append(trial["primary_mdl_gain_vs_lookup_bits"])
        best_accuracy.append(trial["primary_accuracy"])
        best_lookup_ratio.append(trial["primary_lookup_cost_ratio"])
        best_rows.append(
            {
                "order": trial["order"],
                "model": trial["model"],
                "primary_hits": trial["primary_hits"],
                "primary_mdl_gain_vs_lookup_bits": trial["primary_mdl_gain_vs_lookup_bits"],
                "primary_lookup_cost_ratio": trial["primary_lookup_cost_ratio"],
            }
        )
    model_counter = Counter(row["model"] for row in best_rows)
    order_counter = Counter(row["order"] for row in best_rows)
    return {
        "trials": CONTROL_TRIALS,
        "scope": {
            "included_models": [model["name"] for model in control_models],
            "excluded_models": excluded_models,
            "exclusion_reason": (
                "Observed decision-list runs were noncompetitive and non-compressive; "
                "shuffle controls cover the local copy/signature/backoff surface used by the best observed run."
            ),
        },
        "primary_hits": summarize_high(best_hits, observed_best["primary_hits"]),
        "primary_accuracy": summarize_high(best_accuracy, observed_best["primary_accuracy"]),
        "primary_mdl_gain_vs_lookup_bits": summarize_high(
            best_mdl_gain,
            observed_best["primary_mdl_gain_vs_lookup_bits"],
        ),
        "negative_lookup_ratio": summarize_high([-value for value in best_lookup_ratio], -observed_best["primary_lookup_cost_ratio"]),
        "best_control_examples": sorted(
            best_rows,
            key=lambda row: (-row["primary_hits"], -row["primary_mdl_gain_vs_lookup_bits"], row["order"], row["model"]),
        )[:10],
        "best_model_frequency": model_counter.most_common(),
        "best_order_frequency": order_counter.most_common(),
    }


def verdict(best: dict[str, Any], control: dict[str, Any]) -> str:
    compressive = best["primary_mdl_gain_vs_lookup_bits"] > 0 and best["primary_lookup_cost_ratio"] < 1.0
    strong_control = (
        control["primary_hits"]["p_ge"] <= 0.01
        and control["primary_mdl_gain_vs_lookup_bits"]["p_ge"] <= 0.01
    )
    if compressive and strong_control:
        return "candidate_local_2d_rule"
    if not compressive:
        return "lookup_disguise"
    return "rejected_control"


def report_table_row(row: dict[str, Any]) -> str:
    return (
        f"| `{row['order']}` | `{row['model']}` | "
        f"{row['primary_hits']}/55 | {row['acceptable_hits']}/55 | "
        f"{row['primary_lookup_cost_ratio']:.3f} | "
        f"{row['primary_mdl_gain_vs_lookup_bits']:.1f} |"
    )


def write_report(result: dict[str, Any]) -> None:
    best = result["observed"]["best"]
    control = result["control"]
    lines = [
        "# Local 2D Pair-Rule Search",
        "",
        "Generated by `local_2d_pair_rule_search.py`.",
        "",
        "This pass treats the 10x10 unordered pair table as a triangular grid",
        "and tests whether cell labels can be predicted from already-filled",
        "neighbors under plausible fill orders. It is mechanical only and does",
        "not promote plaintext, glossary entries, or translations.",
        "",
        "## Summary",
        "",
        "| Orders | Models | Control trials | Best hits | MDL/lookup | Control p(hit) | Control p(MDL gain) | Verdict |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
        f"| {len(result['orders'])} | {len(result['models'])} | {control['trials']} | "
        f"{best['primary_hits']}/55 | {best['primary_lookup_cost_ratio']:.3f} | "
        f"{control['primary_hits']['p_ge']:.4f} | "
        f"{control['primary_mdl_gain_vs_lookup_bits']['p_ge']:.4f} | `{result['verdict']}` |",
        "",
        "Best observed model:",
        "",
        "| Order | Model | Primary hits | Acceptable hits | MDL/lookup | MDL gain bits |",
        "|---|---|---:|---:|---:|---:|",
        report_table_row(best),
        "",
        "## Top Observed Runs",
        "",
        "| Order | Model | Primary hits | Acceptable hits | MDL/lookup | MDL gain bits |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in result["observed"]["top_rows"][:15]:
        lines.append(report_table_row(row))
    lines.extend(
        [
            "",
            "## Control Gate",
            "",
            "| Metric | Observed | Control mean | Control max | z | p_ge |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for metric in ["primary_hits", "primary_accuracy", "primary_mdl_gain_vs_lookup_bits"]:
        row = control[metric]
        lines.append(
            f"| `{metric}` | {row['observed']:.3f} | {row['control_mean']:.3f} | "
            f"{row['control_max']:.3f} | {row['z_good_direction']:.2f} | {row['p_ge']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Best control examples preserve the exact label inventory and rerun the",
            "same order/model search over the copy/signature/backoff surface.",
            "The observed decision-list runs are reported above but excluded from",
            "shuffle controls because they were noncompetitive and non-compressive.",
            "",
            "| Order | Model | Hits | MDL gain bits | MDL/lookup |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in control["best_control_examples"][:8]:
        lines.append(
            f"| `{row['order']}` | `{row['model']}` | {row['primary_hits']}/55 | "
            f"{row['primary_mdl_gain_vs_lookup_bits']:.1f} | {row['primary_lookup_cost_ratio']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Best Run Misses",
            "",
            "| Pair | Actual primary | Predicted |",
            "|---|---|---|",
        ]
    )
    for miss in best.get("misses", [])[:40]:
        lines.append(f"| `{miss['pair']}` | `{miss['actual']}` | `{miss['predicted']}` |")
    if len(best.get("misses", [])) > 40:
        lines.append(f"| ... | ... | ... |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["verdict"] == "candidate_local_2d_rule":
        lines.extend(
            [
                "The best local 2D rule is both compressive under the rough MDL check and",
                "stronger than inventory-preserving label shuffles. Treat this only as a",
                "mechanical pair-table candidate.",
            ]
        )
    elif result["verdict"] == "lookup_disguise":
        lines.extend(
            [
                "The best local 2D rule does not beat a direct label lookup under the rough",
                "MDL check. It is classified as `lookup_disguise`, not as a generator.",
            ]
        )
    else:
        lines.extend(
            [
                "The best local 2D rule is not strong enough against inventory-preserving",
                "controls. It is classified as `rejected_control`, not as a generator.",
            ]
        )
    lines.extend(["", f"Translation delta: `{result['translation_delta']}`.", ""])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    pairs = natural_pairs()
    orders = build_orders()
    labels_by_pair = {pair: primary_pair_symbol(pair_table, pair) for pair in pairs}
    acceptable_by_pair = {pair: acceptable_pair_symbols(pair_table, pair) for pair in pairs}
    observed = run_search(orders, labels_by_pair, acceptable_by_pair, keep_details=True)
    control = control_search(orders, observed["best"], labels_by_pair)
    result_verdict = verdict(observed["best"], control)
    inventory = Counter(labels_by_pair.values())
    result = {
        "schema": "local_2d_pair_rule_results.v1",
        "source_formula": str(FORMULA_JSON.relative_to(ROOT)),
        "translation_delta": "NONE",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "target": {
            "cell_count": len(pairs),
            "alphabet": list(SIGMA),
            "alphabet_size": len(SIGMA),
            "label_inventory": dict(sorted(inventory.items(), key=lambda item: (sigma_index(item[0]), item[0]))),
            "conflict_cells": [
                pair for pair in pairs if len(acceptable_by_pair[pair]) > 1
            ],
            "lookup_cost_bits": len(pairs) * math.log2(len(SIGMA)),
        },
        "orders": {name: order for name, order in orders.items()},
        "models": [
            {
                "name": model["name"],
                "kind": model["kind"],
                "description": model["description"],
                "complexity_bits": model["complexity_bits"],
            }
            for model in MODEL_DEFS
        ],
        "observed": json_safe(observed),
        "control": json_safe(control),
        "verdict": result_verdict,
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "best order={} model={} hits={}/55 acceptable={}/55 mdl_ratio={:.3f} "
        "p_hit={:.4f} p_mdl={:.4f} verdict={}".format(
            observed["best"]["order"],
            observed["best"]["model"],
            observed["best"]["primary_hits"],
            observed["best"]["acceptable_hits"],
            observed["best"]["primary_lookup_cost_ratio"],
            control["primary_hits"]["p_ge"],
            control["primary_mdl_gain_vs_lookup_bits"]["p_ge"],
            result_verdict,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
