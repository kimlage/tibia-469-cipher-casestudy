#!/usr/bin/env python3
"""Small, controlled ML probes for the mechanical 469 generator question.

This is not a semantic decoder. The goal is to test whether simple models can
generalize out-of-sample on mechanical targets well enough to suggest a compact
human rule worth converting back into deterministic tests.

Targets:

1. pair-cell symbol from unordered 10x10 cell features;
2. homophone code choice from local/position context;
3. leading-zero omission from local rendering context.

The script writes a self-contained JSON result and Markdown report.
"""

from __future__ import annotations

import json
import math
import random
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

from sklearn.exceptions import ConvergenceWarning
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import GroupKFold, LeaveOneOut
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
HOLDOUT_MANIFEST = ROOT / "analysis" / "generator_search_20260618" / "generator_holdout_manifest.json"

OUT_JSON = HERE / "ml_formula_probe_results.json"
OUT_MD = HERE / "ml_formula_probe_report.md"

RANDOM_SEED = 46920260618
SKLEARN_RANDOM_SEED = RANDOM_SEED % (2**32 - 1)
CONTROL_TRIALS = 30
SIGMA = "*ABCEFILNORSTV"
MODEL_COMPLEXITY = {
    "dummy_most_frequent": 0,
    "linear_ridge": 1,
    "tree_depth3": 2,
    "tree_depth5": 3,
    "rf_small": 4,
}
FEATURE_COMPLEXITY = {
    "code_only": 0,
    "causal_local": 1,
    "local_context": 1,
    "with_next_symbol": 2,
    "module_context": 3,
}

warnings.filterwarnings("ignore", category=ConvergenceWarning)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    if not values:
        return {}
    mu = mean(values)
    sd = pstdev(values)
    if high_is_good:
        p = (sum(value >= observed for value in values) + 1) / (len(values) + 1)
        z = (observed - mu) / sd if sd else 0.0
    else:
        p = (sum(value <= observed for value in values) + 1) / (len(values) + 1)
        z = (mu - observed) / sd if sd else 0.0
    return {
        "observed": observed,
        "control_mean": mu,
        "control_sd": sd,
        "z_good_direction": z,
        "p_good_direction": p,
        "control_min": min(values),
        "control_max": max(values),
    }


def train_cv_selection_key(row: dict) -> tuple[float, float, int, int]:
    """Select candidates from train-only CV; read holdout only after selection."""
    return (
        row.get("cv_book_group_mean") or 0.0,
        -(row.get("cv_book_group_sd") or 0.0),
        -FEATURE_COMPLEXITY.get(row.get("feature_family"), 99),
        -MODEL_COMPLEXITY.get(row.get("model"), 99),
    )


def load_books_and_segments(formula: dict) -> tuple[dict[str, str], dict[str, list[dict]]]:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    books_digits: dict[str, str] = {}
    segments: dict[str, list[dict]] = {}
    for book, recipe in formula["book_recipes"].items():
        offset = 0
        text_parts = []
        segs = []
        for item_index, item in enumerate(recipe):
            if item["type"] == "module":
                text = modules[item["id"]]
                segment_id = item["id"]
            else:
                text = item["text"]
                segment_id = f"literal_{item_index}"
            text_parts.append(text)
            segs.append(
                {
                    "segment_id": segment_id,
                    "segment_type": item["type"],
                    "start": offset,
                    "end": offset + len(text),
                    "length": len(text),
                }
            )
            offset += len(text)
        books_digits[str(book)] = "".join(text_parts)
        segments[str(book)] = segs
    return books_digits, segments


def segment_for(segments: list[dict], raw_start: int) -> dict:
    for segment in segments:
        if segment["start"] <= raw_start < segment["end"]:
            return segment
    return {"segment_id": "unknown", "segment_type": "unknown", "start": 0, "end": 0, "length": 0}


def build_tokens(formula: dict) -> list[dict]:
    books_digits, segments = load_books_and_segments(formula)
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[dict]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            code = row["code"]
            by_book[str(row["book"])].append(
                {
                    "book": str(row["book"]),
                    "code_pos": int(row["pos"]),
                    "symbol": symbol,
                    "code": code,
                    "pair_key": "".join(sorted(code)),
                    "code_a": int(code[0]),
                    "code_b": int(code[1]),
                    "code_has_zero": "0" in code,
                    "code_starts_zero": code.startswith("0"),
                }
            )

    tokens: list[dict] = []
    global_seen = Counter()
    for book in sorted(by_book, key=numeric_key):
        rows = sorted(by_book[book], key=lambda item: item["code_pos"])
        raw = books_digits[book]
        offset = 0
        in_book_seen = Counter()
        aligned = []
        for idx, item in enumerate(rows):
            code = item["code"]
            if raw.startswith(code, offset):
                raw_text, start, end, omitted = code, offset, offset + 2, False
                offset += 2
            elif code.startswith("0") and offset < len(raw) and raw[offset] == code[1]:
                raw_text, start, end, omitted = code[1], offset, offset + 1, True
                offset += 1
            else:
                raise ValueError(f"cannot align book={book} code={code} offset={offset}")
            segment = segment_for(segments[book], start)
            aligned.append(
                {
                    **item,
                    "token_index": idx,
                    "token_count": len(rows),
                    "book_len": len(raw),
                    "raw_text": raw_text,
                    "raw_start": start,
                    "raw_end": end,
                    "omitted_zero": omitted,
                    "segment_id": segment["segment_id"],
                    "segment_type": segment["segment_type"],
                    "segment_offset": start - segment["start"],
                    "segment_len": segment["length"],
                    "symbol_seen_in_book": in_book_seen[item["symbol"]],
                    "symbol_seen_global": global_seen[item["symbol"]],
                }
            )
            in_book_seen[item["symbol"]] += 1
            global_seen[item["symbol"]] += 1
        if offset != len(raw):
            raise ValueError(f"book={book} consumed {offset}, expected {len(raw)}")
        for idx, item in enumerate(aligned):
            prev_item = aligned[idx - 1] if idx else None
            next_item = aligned[idx + 1] if idx + 1 < len(aligned) else None
            tokens.append(
                {
                    **item,
                    "prev_code": prev_item["code"] if prev_item else "<s>",
                    "prev_symbol": prev_item["symbol"] if prev_item else "<s>",
                    "prev_pair_key": prev_item["pair_key"] if prev_item else "<s>",
                    "next_symbol": next_item["symbol"] if next_item else "</s>",
                    "next_pair_key": next_item["pair_key"] if next_item else "</s>",
                }
            )
    return tokens


def pair_features(pair: str) -> dict:
    a = int(pair[0])
    b = int(pair[1])
    lo, hi = sorted((a, b))
    return {
        "lo": lo,
        "hi": hi,
        "sum": lo + hi,
        "diff": hi - lo,
        "product": lo * hi,
        "same": lo == hi,
        "has_0": lo == 0 or hi == 0,
        "has_1": lo == 1 or hi == 1,
        "has_4": lo == 4 or hi == 4,
        "has_6": lo == 6 or hi == 6,
        "has_9": lo == 9 or hi == 9,
        "min_mod3": lo % 3,
        "max_mod3": hi % 3,
        "sum_mod3": (lo + hi) % 3,
        "sum_mod5": (lo + hi) % 5,
        "product_mod7": (lo * hi) % 7,
        "border": lo in {0, 9} or hi in {0, 9},
        "centerish": lo in {4, 5} or hi in {4, 5},
        "triangular_index": hi * (hi + 1) // 2 + lo,
    }


def token_features(token: dict, family: str) -> dict:
    base = {
        "symbol": token["symbol"],
        "prev_code": token["prev_code"],
        "prev_symbol": token["prev_symbol"],
        "prev_pair_key": token["prev_pair_key"],
        "prev_same_symbol": token["prev_symbol"] == token["symbol"],
        "next_symbol": token["next_symbol"],
        "token_mod2": token["token_index"] % 2,
        "token_mod3": token["token_index"] % 3,
        "token_mod5": token["token_index"] % 5,
        "token_mod7": token["token_index"] % 7,
        "raw_mod2": token["raw_start"] % 2,
        "raw_mod3": token["raw_start"] % 3,
        "raw_mod5": token["raw_start"] % 5,
        "symbol_seen_book_mod2": token["symbol_seen_in_book"] % 2,
        "symbol_seen_book_mod3": token["symbol_seen_in_book"] % 3,
        "symbol_seen_book_mod5": token["symbol_seen_in_book"] % 5,
        "position_tenth": int(10 * token["token_index"] / max(1, token["token_count"])),
    }
    if family == "causal_local":
        return base
    if family == "with_next_symbol":
        return {**base, "next_pair_key": token["next_pair_key"]}
    if family == "module_context":
        return {
            **base,
            "segment_id": token["segment_id"],
            "segment_type": token["segment_type"],
            "segment_offset_mod2": token["segment_offset"] % 2,
            "segment_offset_mod3": token["segment_offset"] % 3,
            "segment_offset_mod5": token["segment_offset"] % 5,
            "segment_offset_mod7": token["segment_offset"] % 7,
            "segment_tenth": int(10 * token["segment_offset"] / max(1, token["segment_len"])),
        }
    raise ValueError(family)


def zero_features(token: dict, family: str) -> dict:
    base = {
        "code": token["code"],
        "symbol": token["symbol"],
        "prev_code": token["prev_code"],
        "prev_symbol": token["prev_symbol"],
        "next_symbol": token["next_symbol"],
        "token_mod2": token["token_index"] % 2,
        "token_mod3": token["token_index"] % 3,
        "raw_mod2": token["raw_start"] % 2,
        "raw_mod3": token["raw_start"] % 3,
        "raw_mod5": token["raw_start"] % 5,
        "position_tenth": int(10 * token["token_index"] / max(1, token["token_count"])),
    }
    if family == "code_only":
        return {"code": token["code"]}
    if family == "local_context":
        return base
    if family == "module_context":
        return {
            **base,
            "segment_id": token["segment_id"],
            "segment_type": token["segment_type"],
            "segment_offset_mod2": token["segment_offset"] % 2,
            "segment_offset_mod3": token["segment_offset"] % 3,
            "segment_offset_mod5": token["segment_offset"] % 5,
        }
    raise ValueError(family)


def model_factory(name: str):
    if name == "dummy_most_frequent":
        return make_pipeline(DictVectorizer(sparse=True), DummyClassifier(strategy="most_frequent"))
    if name == "linear_ridge":
        return make_pipeline(
            DictVectorizer(sparse=True),
            RidgeClassifier(alpha=1.0),
        )
    if name == "tree_depth3":
        return make_pipeline(
            DictVectorizer(sparse=False),
            DecisionTreeClassifier(max_depth=3, min_samples_leaf=8, random_state=SKLEARN_RANDOM_SEED),
        )
    if name == "tree_depth5":
        return make_pipeline(
            DictVectorizer(sparse=False),
            DecisionTreeClassifier(max_depth=5, min_samples_leaf=8, random_state=SKLEARN_RANDOM_SEED),
        )
    if name == "rf_small":
        return make_pipeline(
            DictVectorizer(sparse=False),
            RandomForestClassifier(
                n_estimators=80,
                max_depth=7,
                min_samples_leaf=5,
                random_state=SKLEARN_RANDOM_SEED,
                n_jobs=1,
            ),
        )
    raise ValueError(name)


def custom_symbol_top(train: list[dict], test: list[dict]) -> dict:
    counts = defaultdict(Counter)
    for row in train:
        counts[row["symbol"]][row["code"]] += 1
    top = {symbol: counter.most_common(1)[0][0] for symbol, counter in counts.items()}
    y = [row["code"] for row in test]
    pred = [top.get(row["symbol"], "<unk>") for row in test]
    return {"model": "symbol_top", "test_accuracy": accuracy_score(y, pred)}


def custom_prev_symbol_top(train: list[dict], test: list[dict]) -> dict:
    symbol_counts = defaultdict(Counter)
    prev_counts = defaultdict(Counter)
    for row in train:
        symbol_counts[row["symbol"]][row["code"]] += 1
        prev_counts[(row["prev_code"], row["symbol"])][row["code"]] += 1
    top = {symbol: counter.most_common(1)[0][0] for symbol, counter in symbol_counts.items()}
    prev_top = {key: counter.most_common(1)[0][0] for key, counter in prev_counts.items()}
    y = [row["code"] for row in test]
    pred = [prev_top.get((row["prev_code"], row["symbol"]), top.get(row["symbol"], "<unk>")) for row in test]
    return {"model": "prev_code_symbol_top", "test_accuracy": accuracy_score(y, pred)}


def make_homophone_dataset(tokens: list[dict], holdout_books: set[str]) -> dict:
    class_sizes = Counter(row["symbol"] for row in tokens)
    code_sets = defaultdict(set)
    for row in tokens:
        code_sets[row["symbol"]].add(row["code"])
    multi_symbols = {symbol for symbol, codes in code_sets.items() if len(codes) > 1}
    rows = [{**row, "is_multi_symbol": row["symbol"] in multi_symbols} for row in tokens]
    return {
        "train": [row for row in rows if row["book"] not in holdout_books],
        "test": [row for row in rows if row["book"] in holdout_books],
        "multi_symbols": sorted(multi_symbols),
        "class_sizes": dict(class_sizes),
    }


def evaluate_classifier(train_rows: list[dict], test_rows: list[dict], feature_family: str, feature_fn, model_name: str, metric: str) -> dict:
    train_x = [feature_fn(row, feature_family) for row in train_rows]
    train_y = [row["label"] for row in train_rows]
    test_x = [feature_fn(row, feature_family) for row in test_rows]
    test_y = [row["label"] for row in test_rows]
    model = model_factory(model_name)
    model.fit(train_x, train_y)
    train_pred = model.predict(train_x)
    test_pred = model.predict(test_x)
    if metric == "balanced_accuracy":
        train_score = balanced_accuracy_score(train_y, train_pred)
        test_score = balanced_accuracy_score(test_y, test_pred)
    else:
        train_score = accuracy_score(train_y, train_pred)
        test_score = accuracy_score(test_y, test_pred)
    return {
        "feature_family": feature_family,
        "model": model_name,
        "train_score": train_score,
        "test_score": test_score,
        "train_n": len(train_rows),
        "test_n": len(test_rows),
    }


def permute_labels_by(rows: list[dict], key_names: tuple[str, ...], label_name: str, rng: random.Random) -> list[dict]:
    groups: dict[tuple, list[int]] = defaultdict(list)
    out = [dict(row) for row in rows]
    for idx, row in enumerate(rows):
        groups[tuple(row[name] for name in key_names)].append(idx)
    for indices in groups.values():
        labels = [rows[idx][label_name] for idx in indices]
        rng.shuffle(labels)
        for idx, label in zip(indices, labels):
            out[idx][label_name] = label
    return out


def cv_by_book(rows: list[dict], feature_family: str, feature_fn, model_name: str, metric: str, eval_filter) -> dict:
    books = sorted({row["book"] for row in rows}, key=numeric_key)
    n_splits = min(5, len(books))
    if n_splits < 2:
        return {}
    groups = [row["book"] for row in rows]
    scores = []
    for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(rows, groups=groups):
        train = [rows[idx] for idx in train_idx]
        test = [rows[idx] for idx in test_idx if eval_filter(rows[idx])]
        if not test:
            continue
        result = evaluate_classifier(train, test, feature_family, feature_fn, model_name, metric)
        scores.append(result["test_score"])
    return {
        "cv_book_group_mean": mean(scores) if scores else None,
        "cv_book_group_sd": pstdev(scores) if len(scores) > 1 else 0.0,
        "cv_folds": len(scores),
    }


def homophone_probe(tokens: list[dict], holdout_books: set[str]) -> dict:
    dataset = make_homophone_dataset(tokens, holdout_books)
    train_all = [{**row, "label": row["code"]} for row in dataset["train"]]
    test_all = [{**row, "label": row["code"]} for row in dataset["test"]]
    test_multi = [row for row in test_all if row["is_multi_symbol"]]

    custom = []
    for scorer in [custom_symbol_top, custom_prev_symbol_top]:
        all_score = scorer(dataset["train"], dataset["test"])
        multi_score = scorer(dataset["train"], [row for row in dataset["test"] if row["is_multi_symbol"]])
        custom.append({**all_score, "test_multi_accuracy": multi_score["test_accuracy"]})
    prev_code_multi_observed = next(row["test_multi_accuracy"] for row in custom if row["model"] == "prev_code_symbol_top")

    rng = random.Random(RANDOM_SEED - 1)
    prev_code_controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled_train = permute_labels_by(train_all, ("symbol",), "label", rng)
        shuffled_train_for_custom = [{**row, "code": row["label"]} for row in shuffled_train]
        ctrl = custom_prev_symbol_top(shuffled_train_for_custom, [row for row in dataset["test"] if row["is_multi_symbol"]])
        prev_code_controls.append(ctrl["test_accuracy"])

    candidates = []
    for family in ["causal_local", "with_next_symbol", "module_context"]:
        for model_name in ["linear_ridge", "tree_depth3", "tree_depth5", "rf_small"]:
            result_all = evaluate_classifier(train_all, test_all, family, token_features, model_name, "accuracy")
            result_multi = evaluate_classifier(train_all, test_multi, family, token_features, model_name, "accuracy")
            cv = cv_by_book(train_all, family, token_features, model_name, "accuracy", lambda row: row["is_multi_symbol"])
            candidates.append(
                {
                    **result_all,
                    "test_multi_accuracy": result_multi["test_score"],
                    **cv,
                }
            )
    candidates.sort(key=train_cv_selection_key, reverse=True)
    selected = candidates[0]

    rng = random.Random(RANDOM_SEED)
    controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled_train = permute_labels_by(train_all, ("symbol",), "label", rng)
        ctrl = evaluate_classifier(
            shuffled_train,
            test_multi,
            selected["feature_family"],
            token_features,
            selected["model"],
            "accuracy",
        )
        controls.append(ctrl["test_score"])

    selected_summary = summarize(controls, selected["test_multi_accuracy"])
    prev_code_summary = summarize(prev_code_controls, prev_code_multi_observed)
    if prev_code_multi_observed >= selected["test_multi_accuracy"] and prev_code_summary.get("p_good_direction", 1.0) <= 0.05:
        verdict = "simple_prev_code_rule_confirmed_not_ml_upgrade"
    else:
        verdict = verdict_from_signal(
            selected["test_multi_accuracy"],
            max(row["test_multi_accuracy"] for row in custom),
            selected_summary.get("p_good_direction", 1.0),
            selected["feature_family"],
        )

    return {
        "target": "homophone_code_choice",
        "train_tokens": len(train_all),
        "test_tokens": len(test_all),
        "test_multi_tokens": len(test_multi),
        "multi_symbols": dataset["multi_symbols"],
        "custom_baselines": custom,
        "prev_code_symbol_top_vs_symbol_shuffle": prev_code_summary,
        "candidate_rows": candidates,
        "selected_by_train_book_cv": selected,
        "selected_test_multi_vs_symbol_shuffle": selected_summary,
        "verdict": verdict,
    }


def zero_probe(tokens: list[dict], holdout_books: set[str]) -> dict:
    zero_rows = [row for row in tokens if row["code_starts_zero"]]
    rows = [{**row, "label": bool(row["omitted_zero"])} for row in zero_rows]
    train = [row for row in rows if row["book"] not in holdout_books]
    test = [row for row in rows if row["book"] in holdout_books]

    candidates = []
    for family in ["code_only", "local_context", "module_context"]:
        for model_name in ["dummy_most_frequent", "linear_ridge", "tree_depth3", "tree_depth5", "rf_small"]:
            result = evaluate_classifier(train, test, family, zero_features, model_name, "balanced_accuracy")
            cv = cv_by_book(train, family, zero_features, model_name, "balanced_accuracy", lambda _row: True)
            candidates.append({**result, **cv})
    candidates.sort(key=train_cv_selection_key, reverse=True)
    selected = candidates[0]
    best_non_module = max(
        [row for row in candidates if row["feature_family"] != "module_context"],
        key=train_cv_selection_key,
    )

    rng = random.Random(RANDOM_SEED + 1)
    controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled_train = permute_labels_by(train, ("code",), "label", rng)
        ctrl = evaluate_classifier(
            shuffled_train,
            test,
            selected["feature_family"],
            zero_features,
            selected["model"],
            "balanced_accuracy",
        )
        controls.append(ctrl["test_score"])
    selected_summary = summarize(controls, selected["test_score"])

    rng = random.Random(RANDOM_SEED + 11)
    non_module_controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled_train = permute_labels_by(train, ("code",), "label", rng)
        ctrl = evaluate_classifier(
            shuffled_train,
            test,
            best_non_module["feature_family"],
            zero_features,
            best_non_module["model"],
            "balanced_accuracy",
        )
        non_module_controls.append(ctrl["test_score"])
    non_module_summary = summarize(non_module_controls, best_non_module["test_score"])
    code_only_baseline = max(row["test_score"] for row in candidates if row["feature_family"] == "code_only")
    non_module_verdict = verdict_from_signal(
        best_non_module["test_score"],
        code_only_baseline,
        non_module_summary.get("p_good_direction", 1.0),
        best_non_module["feature_family"],
    )

    return {
        "target": "leading_zero_omission",
        "train_examples": len(train),
        "test_examples": len(test),
        "train_positive_rate": sum(row["label"] for row in train) / len(train) if train else 0.0,
        "test_positive_rate": sum(row["label"] for row in test) / len(test) if test else 0.0,
        "candidate_rows": candidates,
        "selected_by_train_book_cv": selected,
        "selected_vs_code_preserving_shuffle": selected_summary,
        "best_non_module_by_train_book_cv": best_non_module,
        "best_non_module_vs_code_preserving_shuffle": non_module_summary,
        "verdict": non_module_verdict if non_module_verdict != "not_promoted" else verdict_from_signal(
            selected["test_score"],
            code_only_baseline,
            selected_summary.get("p_good_direction", 1.0),
            selected["feature_family"],
        ),
    }


def verdict_from_signal(score: float, baseline: float, p_value: float, feature_family: str) -> str:
    if feature_family == "module_context":
        if score > baseline + 0.03 and p_value <= 0.05:
            return "leaky_upper_bound_only"
        return "not_promoted"
    if score > baseline + 0.05 and p_value <= 0.05:
        return "candidate_mechanical_signal"
    if score > baseline + 0.02 and p_value <= 0.10:
        return "weak_signal"
    return "not_promoted"


def pair_cell_probe(formula: dict) -> dict:
    rows = []
    for pair, item in formula["pair_table"].items():
        if item["status"] != "pure":
            continue
        rows.append({"pair": pair, "label": item["symbol_if_pure"], "features": pair_features(pair)})

    models = ["dummy_most_frequent", "linear_ridge", "tree_depth3", "tree_depth5"]
    results = []
    for model_name in models:
        y_true = []
        y_pred = []
        loo = LeaveOneOut()
        indices = list(range(len(rows)))
        for train_idx, test_idx in loo.split(indices):
            train_x = [rows[idx]["features"] for idx in train_idx]
            train_y = [rows[idx]["label"] for idx in train_idx]
            test_x = [rows[idx]["features"] for idx in test_idx]
            test_y = [rows[idx]["label"] for idx in test_idx]
            model = model_factory(model_name)
            model.fit(train_x, train_y)
            y_true.extend(test_y)
            y_pred.extend(model.predict(test_x))
        results.append({"model": model_name, "leave_one_cell_out_accuracy": accuracy_score(y_true, y_pred)})

    best = max(results, key=lambda row: row["leave_one_cell_out_accuracy"])
    rng = random.Random(RANDOM_SEED + 2)
    controls = []
    labels = [row["label"] for row in rows]
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        shuffled_rows = [{**row, "label": label} for row, label in zip(rows, shuffled)]
        y_true = []
        y_pred = []
        for train_idx, test_idx in LeaveOneOut().split(range(len(shuffled_rows))):
            train_x = [shuffled_rows[idx]["features"] for idx in train_idx]
            train_y = [shuffled_rows[idx]["label"] for idx in train_idx]
            test_x = [shuffled_rows[idx]["features"] for idx in test_idx]
            test_y = [shuffled_rows[idx]["label"] for idx in test_idx]
            model = model_factory(best["model"])
            model.fit(train_x, train_y)
            y_true.extend(test_y)
            y_pred.extend(model.predict(test_x))
        controls.append(accuracy_score(y_true, y_pred))

    p_summary = summarize(controls, best["leave_one_cell_out_accuracy"])
    return {
        "target": "pair_cell_symbol_from_grid_features",
        "pure_pair_cells": len(rows),
        "candidate_rows": results,
        "best": best,
        "best_vs_label_shuffle": p_summary,
        "verdict": "candidate_mechanical_signal"
        if best["leave_one_cell_out_accuracy"] > 0.35 and p_summary.get("p_good_direction", 1.0) <= 0.05
        else "not_promoted",
    }


def write_report(result: dict) -> None:
    pair = result["pair_cell_probe"]
    homo = result["homophone_probe"]
    zero = result["zero_probe"]
    zero_display = zero.get("best_non_module_by_train_book_cv", zero["selected_by_train_book_cv"])
    zero_control = zero.get("best_non_module_vs_code_preserving_shuffle", zero["selected_vs_code_preserving_shuffle"])

    lines = [
        "# ML Formula Probe",
        "",
        "Generated by `ml_formula_probe.py`.",
        "",
        "This is a mechanical generalization probe, not a semantic decoder. Models",
        "are useful only if they beat simple baselines out-of-sample and pass label",
        "permutation controls.",
        "",
        "## Summary",
        "",
        "| Target | Selected / best | Out-of-sample score | Control p | Verdict |",
        "|---|---|---:|---:|---|",
        (
            f"| Pair-cell symbol | `{pair['best']['model']}` | "
            f"{pair['best']['leave_one_cell_out_accuracy']:.3f} | "
            f"{pair['best_vs_label_shuffle']['p_good_direction']:.3f} | `{pair['verdict']}` |"
        ),
        (
            f"| Homophone code choice | `{homo['selected_by_train_book_cv']['feature_family']} / "
            f"{homo['selected_by_train_book_cv']['model']}` | "
            f"{homo['selected_by_train_book_cv']['test_multi_accuracy']:.3f} | "
            f"{homo['selected_test_multi_vs_symbol_shuffle']['p_good_direction']:.3f} | `{homo['verdict']}` |"
        ),
        (
            f"| Leading-zero omission | `{zero_display['feature_family']} / "
            f"{zero_display['model']}` | "
            f"{zero_display['test_score']:.3f} | "
            f"{zero_control['p_good_direction']:.3f} | `{zero['verdict']}` |"
        ),
        "",
        "## Homophone Baselines",
        "",
        "| Baseline | Test all | Test multi-symbol only |",
        "|---|---:|---:|",
    ]
    for row in homo["custom_baselines"]:
        lines.append(f"| `{row['model']}` | {row['test_accuracy']:.3f} | {row['test_multi_accuracy']:.3f} |")
    lines += [
        "",
        (
            "`prev_code_symbol_top` vs symbol-preserving shuffle: "
            f"p={homo['prev_code_symbol_top_vs_symbol_shuffle']['p_good_direction']:.3f}, "
            f"control mean={homo['prev_code_symbol_top_vs_symbol_shuffle']['control_mean']:.3f}."
        ),
    ]

    lines += [
        "",
        "Top homophone ML rows:",
        "",
        "| Feature family | Model | CV mean | Test all | Test multi | Verdict note |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in homo["candidate_rows"][:8]:
        family = row["feature_family"]
        note = "upper-bound/leaky" if family == "module_context" else "candidate-input"
        lines.append(
            f"| `{family}` | `{row['model']}` | "
            f"{(row.get('cv_book_group_mean') or 0):.3f} | {row['test_score']:.3f} | "
            f"{row['test_multi_accuracy']:.3f} | {note} |"
        )

    lines += [
        "",
        "## Zero Omission Rows",
        "",
        "| Feature family | Model | CV balanced acc | Test balanced acc |",
        "|---|---|---:|---:|",
    ]
    for row in zero["candidate_rows"][:8]:
        lines.append(
            f"| `{row['feature_family']}` | `{row['model']}` | "
            f"{(row.get('cv_book_group_mean') or 0):.3f} | {row['test_score']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- A positive ML signal is only a generator hint if it survives book holdout",
        "  and label-shuffle controls without relying on `module_context`.",
        "- Homophone ML did not beat the simpler previous-code lookup baseline;",
        "  the useful signal is that previous rendered code is highly predictive.",
        "- Leading-zero omission has a non-module local-context signal; this is a",
        "  plausible rendering-rule target, not a translation channel.",
        "- `module_context` is reported as an upper bound because it can memorize",
        "  pre-rendered copied chunks.",
        "- No row promotes plaintext, a glossary, or number<->word meaning.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = load_json(FORMULA_JSON)
    manifest = load_json(HOLDOUT_MANIFEST)
    holdout_books = {str(book) for book in manifest["book_holdouts"]}
    tokens = build_tokens(formula)

    result = {
        "schema": "ml_formula_probe_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "holdout_books": sorted(holdout_books, key=numeric_key),
        "token_count": len(tokens),
        "pair_cell_probe": pair_cell_probe(formula),
        "homophone_probe": homophone_probe(tokens, holdout_books),
        "zero_probe": zero_probe(tokens, holdout_books),
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(
        "verdicts "
        f"pair={result['pair_cell_probe']['verdict']} "
        f"homophone={result['homophone_probe']['verdict']} "
        f"zero={result['zero_probe']['verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
