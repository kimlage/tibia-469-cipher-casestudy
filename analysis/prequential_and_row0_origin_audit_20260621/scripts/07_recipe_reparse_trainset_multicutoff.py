from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
AUDIT_126_RESULT = AUTHORIAL / "reports" / "test_results" / "126_prequential_recipe_reparse_audit.json"

CONTROL_CUTOFFS = [35, 50, 60]
CONTROL_TRIALS = 4
RANDOM_SEED = 46920260621


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def summarize(values: list[float], observed: float) -> dict[str, float | int]:
    return {
        "trials": len(values),
        "min": min(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "max": max(values),
        "p_control_ge_observed": (1 + sum(value >= observed for value in values)) / (len(values) + 1),
    }


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    all_books = list(range(70))
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    source_126 = load_json(AUDIT_126_RESULT)
    observed_by_cutoff = {int(row["cutoff"]): row for row in source_126["rows"]}

    rows = []
    for cutoff in CONTROL_CUTOFFS:
        observed_row = observed_by_cutoff[cutoff]
        observed_gain = float(observed_row["reparse_gain_vs_raw_bits"])
        observed_bits = float(observed_row["deterministic_reparse_frozen_bits"])
        observed_test_books = list(range(cutoff, 70))

        rng = random.Random(RANDOM_SEED + cutoff)
        control_gains = []
        control_bits = []
        control_examples = []
        roundtrip_failures = 0
        for trial in range(CONTROL_TRIALS):
            train = set(rng.sample(all_books, cutoff))
            test = sorted(set(all_books) - train)
            train_counts = audit128.train_counts_for_books(
                audit126,
                train_books=train,
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
            )
            control = audit128.reparse_with_train_inventory(
                audit126,
                formula=formula,
                books=books,
                train_order=sorted(train),
                test_order=test,
                train_counts=train_counts,
            )
            control_gains.append(float(control["gain_vs_raw_bits"]))
            control_bits.append(float(control["bits"]))
            if control["validation"]["books_roundtrip_ok"] != control["validation"]["book_count"]:
                roundtrip_failures += 1
            if len(control_examples) < 3:
                control_examples.append(
                    {
                        "trial": trial,
                        "train_books": sorted(train),
                        "test_book_count": len(test),
                        "gain_vs_raw_bits": control["gain_vs_raw_bits"],
                        "bits": control["bits"],
                    }
                )

        control_summary = summarize(control_gains, observed_gain)
        row = {
            "cutoff": cutoff,
            "observed_prefix": {
                "train_books": list(range(cutoff)),
                "test_books": observed_test_books,
                "bits": observed_bits,
                "gain_vs_raw_bits": observed_gain,
                "reparse_minus_active_bits": observed_row["reparse_minus_active_bits"],
                "roundtrip_ok": observed_row["deterministic_reparse"]["validation"]["errors"] == [],
            },
            "random_train_set_control": control_summary,
            "random_train_bits_summary": summarize(control_bits, observed_bits),
            "random_train_roundtrip_failures": roundtrip_failures,
            "control_examples": control_examples,
            "numeric_prefix_beats_control_mean": observed_gain > float(control_summary["mean"]),
            "numeric_prefix_beats_control_max": observed_gain > float(control_summary["max"]),
            "numeric_prefix_is_unique_at_control_resolution": float(
                control_summary["p_control_ge_observed"]
            )
            <= 1 / (CONTROL_TRIALS + 1),
        }
        rows.append(row)

    mean_wins = sum(1 for row in rows if row["numeric_prefix_beats_control_mean"])
    max_wins = sum(1 for row in rows if row["numeric_prefix_beats_control_max"])
    unique_rows = sum(1 for row in rows if row["numeric_prefix_is_unique_at_control_resolution"])
    any_random_ge = any(
        row["random_train_set_control"]["p_control_ge_observed"] > 1 / (CONTROL_TRIALS + 1)
        for row in rows
    )
    classification = (
        "recipe_reparse_numeric_prefix_not_unique_multicutoff"
        if any_random_ge
        else "recipe_reparse_numeric_prefix_unique_at_control_resolution"
    )

    return {
        "schema": "recipe_reparse_trainset_multicutoff.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "prequential_recipe_reparse": rel(AUDIT_126_RESULT),
            "trainset_control_script": rel(AUDIT_128),
        },
        "control_cutoffs": CONTROL_CUTOFFS,
        "control_trials_per_cutoff": CONTROL_TRIALS,
        "random_seed": RANDOM_SEED,
        "rows": rows,
        "summary": {
            "numeric_prefix_beats_control_mean_cutoffs": mean_wins,
            "numeric_prefix_beats_control_max_cutoffs": max_wins,
            "numeric_prefix_unique_at_control_resolution_cutoffs": unique_rows,
            "all_roundtrip": all(row["random_train_roundtrip_failures"] == 0 for row in rows),
            "interpretation": (
                "Recipe reparsing is robustly predictive, but numeric-prefix "
                "training is not uniquely supported across same-size train inventories."
            ),
        },
        "decision": {
            "recipe_predictive_signal": "retained",
            "numeric_order_as_authorial_proof": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "07_recipe_reparse_trainset_multicutoff.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Recipe Reparse Train-Set Multi-Cutoff Control",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 128 tested random same-size train inventories only at cutoff `50`.",
        "This audit expands the same train/test contract to cutoffs",
        "`35/50/60`: train on a same-size inventory, reparse the complementary",
        "test set in numeric order, and compare gain versus raw digit coding.",
        "",
        "## Result",
        "",
        "| Cutoff | Observed gain | Random mean | Random max | p(random >= observed) | Mean win | Max win |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in result["rows"]:
        control = row["random_train_set_control"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix']['gain_vs_raw_bits']:.3f}` | "
            f"`{control['mean']:.3f}` | `{control['max']:.3f}` | "
            f"`{control['p_control_ge_observed']:.4f}` | "
            f"`{row['numeric_prefix_beats_control_mean']}` | "
            f"`{row['numeric_prefix_beats_control_max']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Numeric prefix beats random-train mean at `{result['summary']['numeric_prefix_beats_control_mean_cutoffs']}/{len(result['rows'])}` cutoffs.",
            f"- Numeric prefix beats random-train max at `{result['summary']['numeric_prefix_beats_control_max_cutoffs']}/{len(result['rows'])}` cutoffs.",
            f"- Unique at control resolution: `{result['summary']['numeric_prefix_unique_at_control_resolution_cutoffs']}/{len(result['rows'])}` cutoffs.",
            "- The recipe-reparse signal remains predictive, but numeric order is not promoted as final authorial proof.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "07_recipe_reparse_trainset_multicutoff.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
