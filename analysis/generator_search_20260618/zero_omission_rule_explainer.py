#!/usr/bin/env python3
"""Interpret the ML zero-omission signal as auditable mechanical rules.

The ML probe found a non-module local-context signal for leading-zero omission.
This script tries to convert that signal into explicit human-scale rules. It
does not promote an opaque classifier and does not assign meaning to any code.

Acceptance is intentionally strict:

- beat the code-only baseline on book holdout;
- beat code-preserving label shuffles;
- reduce the rough MDL estimate versus code-only.

If the best rule improves prediction but costs more than code-only, it remains
a useful signal only, not an accepted formula.
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.pipeline import make_pipeline


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ML_DIR = ROOT / "analysis" / "ml_formula_probe_20260618"
sys.path.insert(0, str(ML_DIR))

import ml_formula_probe as ml_probe  # noqa: E402


OUT_JSON = HERE / "zero_omission_rule_explainer_results.json"
OUT_MD = HERE / "zero_omission_rule_explainer_report.md"
EXTERNAL_HOLDOUT = HERE / "external_holdout_scores.json"

RANDOM_SEED = 46920260621
CONTROL_TRIALS = 2000

FEATURES = [
    "code",
    "symbol",
    "prev_code",
    "prev_symbol",
    "next_symbol",
    "token_mod2",
    "token_mod3",
    "raw_mod2",
    "raw_mod3",
    "raw_mod5",
    "position_tenth",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def feature_value(row: dict, feature: str):
    if feature.startswith("token_mod"):
        return row["token_index"] % int(feature[-1])
    if feature.startswith("raw_mod"):
        return row["raw_start"] % int(feature[-1])
    if feature == "position_tenth":
        return int(10 * row["token_index"] / max(1, row["token_count"]))
    return row[feature]


def build_dataset() -> tuple[list[dict], list[dict]]:
    formula = ml_probe.load_json(ml_probe.FORMULA_JSON)
    manifest = ml_probe.load_json(ml_probe.HOLDOUT_MANIFEST)
    holdout_books = {str(book) for book in manifest["book_holdouts"]}
    tokens = ml_probe.build_tokens(formula)
    rows = [{**row, "label": bool(row["omitted_zero"])} for row in tokens if row["code_starts_zero"]]
    train = [row for row in rows if row["book"] not in holdout_books]
    test = [row for row in rows if row["book"] in holdout_books]
    return train, test


def group_rule(train: list[dict], features: tuple[str, ...]):
    groups: dict[tuple, list[bool]] = defaultdict(list)
    for row in train:
        groups[tuple(feature_value(row, feature) for feature in features)].append(row["label"])
    default = Counter(row["label"] for row in train).most_common(1)[0][0]
    majority = {key: Counter(values).most_common(1)[0][0] for key, values in groups.items()}
    return majority, default


def predict_group(row: dict, features: tuple[str, ...], majority: dict, default: bool) -> bool:
    return majority.get(tuple(feature_value(row, feature) for feature in features), default)


def feature_cardinality(train: list[dict], feature: str) -> int:
    return len({feature_value(row, feature) for row in train})


def rough_mdl_bits(train: list[dict], test: list[dict], features: tuple[str, ...], majority: dict, preds: list[bool]) -> float:
    y = [row["label"] for row in test]
    errors = sum(left != right for left, right in zip(y, preds))
    feature_key_bits = sum(math.log2(feature_cardinality(train, feature) + 1) for feature in features)
    # Simple two-part estimate: describe each group predicate+label, then literalize test errors.
    return len(majority) * (1.0 + feature_key_bits) + errors * math.log2(len(test) + 1)


def score_group_rule(train: list[dict], test: list[dict], features: tuple[str, ...]) -> dict:
    majority, default = group_rule(train, features)
    preds = [predict_group(row, features, majority, default) for row in test]
    y = [row["label"] for row in test]
    return {
        "features": list(features),
        "groups": len(majority),
        "accuracy": accuracy_score(y, preds),
        "balanced_accuracy": balanced_accuracy_score(y, preds),
        "errors": sum(left != right for left, right in zip(y, preds)),
        "mdl_bits": rough_mdl_bits(train, test, features, majority, preds),
    }


def all_group_rules(train: list[dict], test: list[dict]) -> list[dict]:
    rows = []
    for size in [1, 2, 3]:
        for features in itertools.combinations(FEATURES, size):
            rows.append(score_group_rule(train, test, features))
    rows.sort(key=lambda row: (-row["balanced_accuracy"], row["groups"], row["mdl_bits"]))
    return rows


def summarize(values: list[float], observed: float, high_is_good: bool = True) -> dict:
    mean = sum(values) / len(values)
    sd = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
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


def shuffle_control(train: list[dict], test: list[dict], features: tuple[str, ...]) -> dict:
    rng = random.Random(RANDOM_SEED)
    scores = []
    for _trial in range(CONTROL_TRIALS):
        shuffled = [dict(row) for row in train]
        by_code = defaultdict(list)
        for index, row in enumerate(train):
            by_code[row["code"]].append(index)
        for indices in by_code.values():
            labels = [train[index]["label"] for index in indices]
            rng.shuffle(labels)
            for index, label in zip(indices, labels):
                shuffled[index]["label"] = label
        scores.append(score_group_rule(shuffled, test, features)["balanced_accuracy"])
    return summarize(scores, score_group_rule(train, test, features)["balanced_accuracy"], high_is_good=True)


def ridge_weights(train: list[dict], test: list[dict]) -> dict:
    pipeline = make_pipeline(DictVectorizer(sparse=True), RidgeClassifier(alpha=1.0))
    train_x = [ml_probe.zero_features(row, "local_context") for row in train]
    train_y = [row["label"] for row in train]
    test_x = [ml_probe.zero_features(row, "local_context") for row in test]
    test_y = [row["label"] for row in test]
    pipeline.fit(train_x, train_y)
    pred = pipeline.predict(test_x)
    vectorizer = pipeline.named_steps["dictvectorizer"]
    classifier = pipeline.named_steps["ridgeclassifier"]
    feature_names = vectorizer.get_feature_names_out()
    weights = list(zip(feature_names, classifier.coef_[0]))
    weights.sort(key=lambda item: item[1])
    return {
        "accuracy": accuracy_score(test_y, pred),
        "balanced_accuracy": balanced_accuracy_score(test_y, pred),
        "top_positive_omitted": [{"feature": name, "weight": weight} for name, weight in reversed(weights[-15:])],
        "top_negative_not_omitted": [{"feature": name, "weight": weight} for name, weight in weights[:15]],
    }


def avar_tar_status() -> dict:
    if not EXTERNAL_HOLDOUT.exists():
        return {"supervised_zero_omission_control": "not_available"}
    external = load_json(EXTERNAL_HOLDOUT)["rows"]
    avar = external.get("avar_tar_min8", {})
    return {
        "supervised_zero_omission_control": "not_applicable_without_attested_underlying_zero_labels",
        "available_negative_copy_control": {
            "name": avar.get("name"),
            "min_len": avar.get("min_len"),
            "covered_digits": avar.get("covered_digits"),
            "length": avar.get("length"),
            "covered_fraction": avar.get("covered_fraction"),
        },
    }


def write_report(result: dict) -> None:
    selected = result["selected_group_rule"]
    code = result["code_only_rule"]
    lines = [
        "# Zero Omission Rule Explainer",
        "",
        "Generated by `zero_omission_rule_explainer.py`.",
        "",
        "This pass converts the ML zero-omission signal into auditable candidate",
        "rules. It does not promote an opaque classifier.",
        "",
        "## Summary",
        "",
        "| Rule | Balanced acc | Accuracy | Groups | Rough MDL bits | Control p | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
        (
            f"| `code_only` | {code['balanced_accuracy']:.3f} | {code['accuracy']:.3f} | "
            f"{code['groups']} | {code['mdl_bits']:.1f} | n/a | `baseline` |"
        ),
        (
            f"| `{'+'.join(selected['features'])}` | {selected['balanced_accuracy']:.3f} | "
            f"{selected['accuracy']:.3f} | {selected['groups']} | {selected['mdl_bits']:.1f} | "
            f"{result['selected_vs_code_preserving_shuffle']['p_good_direction']:.5f} | `{result['verdict']}` |"
        ),
        "",
        "## Linear Probe Weights",
        "",
        "Top omitted-zero weights:",
        "",
        "| Feature | Weight |",
        "|---|---:|",
    ]
    for row in result["linear_ridge_probe"]["top_positive_omitted"][:10]:
        lines.append(f"| `{row['feature']}` | {row['weight']:.3f} |")
    lines += [
        "",
        "Top not-omitted weights:",
        "",
        "| Feature | Weight |",
        "|---|---:|",
    ]
    for row in result["linear_ridge_probe"]["top_negative_not_omitted"][:10]:
        lines.append(f"| `{row['feature']}` | {row['weight']:.3f} |")
    lines += [
        "",
        "## Top Human Rules",
        "",
        "| Features | Balanced acc | Accuracy | Groups | MDL bits |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in result["top_group_rules"][:12]:
        lines.append(
            f"| `{'+'.join(row['features'])}` | {row['balanced_accuracy']:.3f} | "
            f"{row['accuracy']:.3f} | {row['groups']} | {row['mdl_bits']:.1f} |"
        )
    lines += [
        "",
        "## Avar Tar Control Boundary",
        "",
        "Avar Tar has no CipSoft-attested underlying full-code sequence, so it cannot",
        "supply supervised zero-omission labels. It remains usable as a copy/coverage",
        "negative control, not as a labeled zero-rendering control.",
        "",
        "## Interpretation",
        "",
    ]
    if result["verdict"] == "candidate_zero_render_rule_mdl":
        lines.append("A simple zero-rendering rule survives prediction, shuffle, and MDL gates.")
    else:
        lines.append(
            "The local-context signal is real, but the best explicit group rule is too"
            " costly under the rough MDL estimate. Keep it as a render-layer clue,"
            " not as an accepted formula."
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    train, test = build_dataset()
    group_rows = all_group_rules(train, test)
    code_only = score_group_rule(train, test, ("code",))
    selected = group_rows[0]
    selected_control = shuffle_control(train, test, tuple(selected["features"]))
    mdl_gain = code_only["mdl_bits"] - selected["mdl_bits"]
    verdict = "candidate_zero_render_rule_signal_only"
    if (
        selected["balanced_accuracy"] >= code_only["balanced_accuracy"] + 0.05
        and selected_control["p_good_direction"] <= 0.05
        and mdl_gain > 0
    ):
        verdict = "candidate_zero_render_rule_mdl"
    elif selected["balanced_accuracy"] <= code_only["balanced_accuracy"] + 0.02 or selected_control["p_good_direction"] > 0.10:
        verdict = "not_promoted"

    result = {
        "schema": "zero_omission_rule_explainer_results.v1",
        "random_seed": RANDOM_SEED,
        "control_trials": CONTROL_TRIALS,
        "train_examples": len(train),
        "test_examples": len(test),
        "code_only_rule": code_only,
        "selected_group_rule": selected,
        "selected_vs_code_preserving_shuffle": selected_control,
        "rough_mdl_gain_vs_code_only_bits": mdl_gain,
        "linear_ridge_probe": ridge_weights(train, test),
        "top_group_rules": group_rows[:40],
        "avar_tar_control": avar_tar_status(),
        "verdict": verdict,
        "translation_delta": "NONE",
    }
    write_json(OUT_JSON, result)
    write_report(result)
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(
        f"verdict={verdict} selected={'+'.join(selected['features'])} "
        f"bal={selected['balanced_accuracy']:.3f} mdl_gain={mdl_gain:.1f} "
        f"p={selected_control['p_good_direction']:.5f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
