from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

LEGACY_SCRIPT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "scripts"
    / "125_prequential_and_row0_origin_audit.py"
)

COMPONENTS = ("copy_length", "literal_payload", "item_type")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("legacy_prequential_row0_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def component_gain(row: dict[str, Any], component: str, mode: str) -> float:
    return (
        float(row["test_uniform_baseline_bits"][component])
        - float(row[f"test_{mode}_cost_bits"][component])
    )


def selected_bits(row: dict[str, Any], selectors: dict[str, bool], mode: str) -> float:
    total = 0.0
    for component, use_adaptive in selectors.items():
        if use_adaptive:
            total += float(row[f"test_{mode}_cost_bits"][component])
        else:
            total += float(row["test_uniform_baseline_bits"][component])
    return total


def oracle_selectors(row: dict[str, Any], mode: str) -> dict[str, bool]:
    return {
        component: component_gain(row, component, mode) > 0
        for component in COMPONENTS
    }


def train_cv_selectors(
    *,
    legacy,
    formula: dict[str, Any],
    copy_rows: list[dict[str, Any]],
    payload_rows: list[dict[str, Any]],
    item_rows: list[dict[str, Any]],
    families: dict[str, set[int]],
    all_books: set[int],
    outer_label: str,
    outer_test: set[int],
    mode: str,
) -> tuple[dict[str, bool], dict[str, float], int]:
    gains = {component: 0.0 for component in COMPONENTS}
    internal_count = 0
    for inner_label, inner_test in sorted(families.items()):
        if inner_label == outer_label or not inner_test.isdisjoint(outer_test):
            continue
        internal_count += 1
        inner_row = legacy.predictive_split(
            label=f"{outer_label}__inner_{inner_label}",
            split_type="train_cv_public_bookcase_family",
            train_books=all_books - outer_test - inner_test,
            test_books=inner_test,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        for component in COMPONENTS:
            gains[component] += component_gain(inner_row, component, mode)
    selectors = {component: gains[component] > 0 for component in COMPONENTS}
    return selectors, gains, internal_count


def make_result() -> dict[str, Any]:
    legacy = load_module(LEGACY_SCRIPT)
    copy_module = legacy.load_module("copy_context", legacy.COPY_CONTEXT)
    payload_module = legacy.load_module("payload_context", legacy.PAYLOAD_CONTEXT)
    item_module = legacy.load_module("item_context", legacy.ITEM_CONTEXT)

    formula = legacy.load_json(legacy.FORMULA)
    books = {str(key): value for key, value in legacy.load_json(legacy.BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    families = legacy.load_bookcase_families()
    all_books = set(range(70))
    rows = []
    for label, test_books in sorted(families.items()):
        target = legacy.predictive_split(
            label=label,
            split_type="public_bookcase_family_holdout",
            train_books=all_books - test_books,
            test_books=test_books,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        mode_rows = {}
        for mode in ("online", "frozen"):
            train_selectors, train_cv_gains, internal_count = train_cv_selectors(
                legacy=legacy,
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
                families=families,
                all_books=all_books,
                outer_label=label,
                outer_test=test_books,
                mode=mode,
            )
            oracle = oracle_selectors(target, mode)
            uniform_bits = float(target["aggregate"]["test_uniform_bits"])
            active_bits = float(target["aggregate"][f"test_{mode}_bits"])
            train_cv_bits = selected_bits(target, train_selectors, mode)
            oracle_bits = selected_bits(target, oracle, mode)
            mode_rows[mode] = {
                "active_bits": active_bits,
                "active_gain_vs_uniform_bits": uniform_bits - active_bits,
                "train_cv_selector_bits": train_cv_bits,
                "train_cv_selector_gain_vs_uniform_bits": uniform_bits - train_cv_bits,
                "oracle_component_selector_bits": oracle_bits,
                "oracle_component_selector_gain_vs_uniform_bits": uniform_bits - oracle_bits,
                "train_cv_selectors": train_selectors,
                "oracle_selectors": oracle,
                "train_cv_component_gains_bits": train_cv_gains,
                "internal_family_cv_count": internal_count,
                "train_cv_changes_active_components": any(not value for value in train_selectors.values()),
                "oracle_changes_active_components": any(not value for value in oracle.values()),
            }
        rows.append(
            {
                "label": label,
                "test_books": sorted(test_books),
                "event_counts": target["event_counts"],
                "online": mode_rows["online"],
                "frozen": mode_rows["frozen"],
            }
        )

    def mode_summary(mode: str) -> dict[str, Any]:
        active_gains = [row[mode]["active_gain_vs_uniform_bits"] for row in rows]
        train_gains = [row[mode]["train_cv_selector_gain_vs_uniform_bits"] for row in rows]
        oracle_gains = [row[mode]["oracle_component_selector_gain_vs_uniform_bits"] for row in rows]
        return {
            "active_failure_count": sum(gain <= 0 for gain in active_gains),
            "train_cv_selector_failure_count": sum(gain <= 0 for gain in train_gains),
            "oracle_selector_failure_count": sum(gain <= 0 for gain in oracle_gains),
            "active_total_gain_vs_uniform_bits": sum(active_gains),
            "train_cv_selector_total_gain_vs_uniform_bits": sum(train_gains),
            "oracle_selector_total_gain_vs_uniform_bits": sum(oracle_gains),
            "train_cv_changed_family_count": sum(
                row[mode]["train_cv_changes_active_components"] for row in rows
            ),
            "oracle_changed_family_count": sum(
                row[mode]["oracle_changes_active_components"] for row in rows
            ),
        }

    result = {
        "schema": "train_cv_component_selector_audit.v1",
        "classification": "train_cv_component_selector_does_not_rescue_family_holdouts",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "sources": {
            "legacy_script": rel(LEGACY_SCRIPT),
            "formula": rel(legacy.FORMULA),
        },
        "method": {
            "train_cv_selector": (
                "For each outer public-bookcase family holdout, use only the other "
                "public-bookcase families inside the training set. A component is "
                "kept adaptive only if its internal leave-family-out gain versus "
                "uniform is positive."
            ),
            "oracle_selector": (
                "Per-component heldout oracle included only as a ceiling. It sees "
                "the target family outcome and is therefore not promotable."
            ),
        },
        "summary": {
            "online": mode_summary("online"),
            "frozen": mode_summary("frozen"),
        },
        "decision": {
            "result": (
                "Train-only component selection chooses the active components for "
                "every public-bookcase family. It therefore leaves the same family "
                "failures in place. The only selector that rescues them is the "
                "heldout oracle, which is posthoc and not a generation rule."
            ),
            "promotion": "rejected_for_generation_method",
            "row0_origin_changed": False,
        },
        "rows": rows,
    }
    return result


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Train-CV Component Selector Audit",
        "",
        "Classification: `train_cv_component_selector_does_not_rescue_family_holdouts`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit tests whether the public-bookcase family failures can be fixed",
        "by a component selector learned from training families only. It is not a",
        "compression sweep: component choices are derived from inner family",
        "cross-validation and then applied to the held-out family.",
        "",
        "## Result",
        "",
        "| Mode | Active failures | Train-CV selector failures | Oracle failures | Active gain | Train-CV gain | Oracle gain | Train-CV changed families | Oracle changed families |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in ("online", "frozen"):
        row = result["summary"][mode]
        lines.append(
            f"| `{mode}` | `{row['active_failure_count']}` | "
            f"`{row['train_cv_selector_failure_count']}` | "
            f"`{row['oracle_selector_failure_count']}` | "
            f"`{row['active_total_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['train_cv_selector_total_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['oracle_selector_total_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['train_cv_changed_family_count']}` | "
            f"`{row['oracle_changed_family_count']}` |"
        )
    lines.extend(
        [
            "",
            "The train-CV selector keeps all active components for every family, because",
            "the other training families show positive aggregate gains for all three",
            "components. It therefore does not rescue `bookcase_33`, `bookcase_8`, or",
            "the frozen `bookcase_6` failure. The oracle selector does improve the",
            "ledger, but only by seeing the held-out family outcome.",
            "",
            "## Failure Rows",
            "",
            "| Family | Mode | Active gain | Train-CV gain | Oracle gain | Train-CV selectors | Oracle selectors |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in result["rows"]:
        for mode in ("online", "frozen"):
            data = row[mode]
            if (
                data["active_gain_vs_uniform_bits"] <= 0
                or data["train_cv_selector_gain_vs_uniform_bits"] <= 0
                or data["oracle_changes_active_components"]
            ):
                lines.append(
                    f"| `{row['label']}` | `{mode}` | "
                    f"`{data['active_gain_vs_uniform_bits']:.3f}` | "
                    f"`{data['train_cv_selector_gain_vs_uniform_bits']:.3f}` | "
                    f"`{data['oracle_component_selector_gain_vs_uniform_bits']:.3f}` | "
                    f"`{data['train_cv_selectors']}` | `{data['oracle_selectors']}` |"
                )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- No train-only component fallback is promoted.",
            "- Family failures remain evidence that the learned-component model is partial, not a final authorial generation method.",
            "- The oracle ceiling shows the failures are locally removable only with heldout information, so using that as a formula would be posthoc.",
            "- `row0` origin and semantics are unchanged; `translation_delta: NONE`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    result = make_result()
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "03_train_cv_component_selector_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (TEST_RESULTS / "03_train_cv_component_selector_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
