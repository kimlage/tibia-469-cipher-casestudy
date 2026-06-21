from __future__ import annotations

import importlib.util
import inspect
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
PARENT_RESULT = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("legacy_prequential_row0_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def pct(part: float, whole: float) -> float:
    return 100.0 * part / whole if whole else 0.0


def recipe_counts_for_books(formula: dict[str, Any], books: dict[str, str], selected: set[int]) -> dict[str, int]:
    counts = {
        "books": 0,
        "digits": 0,
        "ops": 0,
        "literal_runs": 0,
        "literal_payload_digits": 0,
        "copy_ops": 0,
        "copied_digits": 0,
        "copy_source_addresses_declared_by_recipe": 0,
        "item_type_decisions_declared_by_recipe": 0,
    }
    for book in formula["policy"]["book_order"]:
        book_id = int(book)
        if book_id not in selected:
            continue
        digits = books[str(book_id)]
        counts["books"] += 1
        counts["digits"] += len(digits)
        target = 0
        for op in formula["book_recipes"][str(book_id)]["ops"]:
            length = int(op["length"])
            counts["ops"] += 1
            counts["item_type_decisions_declared_by_recipe"] += 1
            if op["type"] == "literal":
                text = op["text"]
                if len(text) != length:
                    raise RuntimeError((book_id, op))
                counts["literal_runs"] += 1
                counts["literal_payload_digits"] += length
            elif op["type"] == "copy":
                if "source_digit_pos" not in op:
                    raise RuntimeError((book_id, op))
                counts["copy_ops"] += 1
                counts["copied_digits"] += length
                counts["copy_source_addresses_declared_by_recipe"] += 1
            else:
                raise RuntimeError((book_id, op))
            target += length
        if target != len(digits):
            raise RuntimeError((book_id, target, len(digits)))
    return counts


def component_accounting(legacy, formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    copy_module = legacy.load_module("copy_context", legacy.COPY_CONTEXT)
    payload_module = legacy.load_module("payload_context", legacy.PAYLOAD_CONTEXT)
    item_module = legacy.load_module("item_context", legacy.ITEM_CONTEXT)
    frontier = legacy.load_module("frontier", legacy.FRONTIER)
    midpoint = legacy.load_module("midpoint", legacy.MIDPOINT)

    legacy_score = midpoint.score_formula(formula, books, frontier, copy_module)
    if legacy_score["validation"]["errors"]:
        raise RuntimeError(legacy_score["validation"])

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    item_model = formula["policy"]["item_type_model"]
    copy_length_bits = legacy.score_copy_rows(
        copy_rows,
        {},
        int(formula["policy"]["copy_length_model"]["alpha"]),
        update=True,
    )
    literal_payload_bits = legacy.score_fixed_rows(
        payload_rows,
        {},
        alpha=float(formula["policy"]["literal_payload_model"]["alpha"]),
        alphabet=legacy.DIGITS,
        key_fn=legacy.payload_key,
        symbol_key="digit",
        update=True,
    )
    item_type_bits = legacy.score_fixed_rows(
        item_rows,
        {},
        alpha=float(item_model["alpha"]),
        alphabet=legacy.ITEM_TYPES,
        key_fn=legacy.item_key(item_model),
        symbol_key="item_type",
        update=True,
    )

    mdl = formula["mdl_estimate_rough"]
    active_total = float(mdl[legacy.CURRENT_TOTAL_KEY])
    scored_total = copy_length_bits + literal_payload_bits + item_type_bits
    fixed_recipe_total = (
        float(legacy_score["fixed_bits"])
        + float(legacy_score["literal_bits_no_payload"])
        + float(legacy_score["copy_address_bits"])
    )
    recomputed = scored_total + fixed_recipe_total
    if abs(recomputed - active_total) > 1e-6:
        raise RuntimeError((recomputed, active_total))

    return {
        "active_total_bits": active_total,
        "prequentially_scored_component_bits": scored_total,
        "fixed_recipe_or_nonlearned_bits": fixed_recipe_total,
        "prequentially_scored_component_share_pct": pct(scored_total, active_total),
        "fixed_recipe_or_nonlearned_share_pct": pct(fixed_recipe_total, active_total),
        "scored_components": {
            "copy_length_bits": copy_length_bits,
            "literal_payload_bits": literal_payload_bits,
            "item_type_bits": item_type_bits,
            "copy_length_events": len(copy_rows),
            "literal_payload_events": len(payload_rows),
            "item_type_events": len(item_rows),
        },
        "fixed_recipe_breakdown": {
            "fixed_bits_ledger": float(legacy_score["fixed_bits"]),
            "literal_structure_no_payload_bits": float(legacy_score["literal_bits_no_payload"]),
            "copy_address_bits": float(legacy_score["copy_address_bits"]),
        },
        "additional_formula_context": {
            "book_length_bits": mdl.get("book_length_bits"),
            "literal_length_code_bits": mdl.get("literal_length_code_bits"),
            "copy_items": mdl.get("copy_items"),
            "literal_runs": mdl.get("literal_runs"),
            "literal_digits": mdl.get("literal_digits"),
            "copied_digits": mdl.get("copied_digits"),
        },
    }


def split_recipe_disclosure(parent: dict[str, Any], formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    prefixes = []
    for row in parent["predictive_validation"]["prefix_future_suffix"]["rows"]:
        test_books = {int(book) for book in row["test_books"]}
        counts = recipe_counts_for_books(formula, books, test_books)
        prefixes.append(
            {
                "label": row["label"],
                "test_books": counts["books"],
                "test_digits": counts["digits"],
                "known_recipe_ops": counts["ops"],
                "known_copy_source_addresses": counts["copy_source_addresses_declared_by_recipe"],
                "known_literal_runs": counts["literal_runs"],
                "known_literal_payload_digits": counts["literal_payload_digits"],
                "known_copied_digits": counts["copied_digits"],
                "online_gain_vs_uniform_bits": row["aggregate"]["test_online_gain_vs_uniform_bits"],
                "frozen_gain_vs_uniform_bits": row["aggregate"]["test_frozen_gain_vs_uniform_bits"],
            }
        )

    family_failures = []
    for row in parent["predictive_validation"]["public_bookcase_family_holdouts"]["rows"]:
        if (
            row["aggregate"]["test_online_gain_vs_uniform_bits"] > 0
            and row["aggregate"]["test_frozen_gain_vs_uniform_bits"] > 0
        ):
            continue
        test_books = {int(book) for book in row["test_books"]}
        counts = recipe_counts_for_books(formula, books, test_books)
        family_failures.append(
            {
                "label": row["label"],
                "test_books": sorted(test_books),
                "known_recipe_ops": counts["ops"],
                "known_copy_source_addresses": counts["copy_source_addresses_declared_by_recipe"],
                "known_literal_runs": counts["literal_runs"],
                "known_literal_payload_digits": counts["literal_payload_digits"],
                "known_copied_digits": counts["copied_digits"],
                "online_gain_vs_uniform_bits": row["aggregate"]["test_online_gain_vs_uniform_bits"],
                "frozen_gain_vs_uniform_bits": row["aggregate"]["test_frozen_gain_vs_uniform_bits"],
            }
        )
    return {"prefix_future_suffix": prefixes, "family_failure_rows": family_failures}


def source_control(legacy) -> dict[str, Any]:
    source = inspect.getsource(legacy.predictive_split)
    script_text = LEGACY_SCRIPT.read_text(encoding="utf-8")
    return {
        "predictive_split_accepts_precomputed_rows": all(
            needle in source
            for needle in ("copy_rows", "payload_rows", "item_rows", "split_rows")
        ),
        "predictive_split_selects_or_searches_recipe_ops": any(
            needle in source
            for needle in ("book_recipes", "source_digit_pos", "target_start", "collect_copy_rows")
        ),
        "main_collects_rows_from_full_formula_before_splitting": all(
            needle in script_text
            for needle in (
                "copy_module.collect_copy_rows(formula, books)",
                "payload_module.collect_literal_digit_rows(formula, books)",
                "item_module.collect_item_rows(formula, books)",
                "prefix_splits = []",
            )
        ),
        "interpretation": (
            "The prequential function scores precomputed event rows after a train/test "
            "book filter. It does not discover literal/copy segmentation, copy source "
            "addresses, or held-out recipe operations."
        ),
    }


def make_result() -> dict[str, Any]:
    legacy = load_module(LEGACY_SCRIPT)
    parent = load_json(PARENT_RESULT)
    formula = load_json(legacy.FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    all_counts = recipe_counts_for_books(formula, books, set(range(70)))
    accounting = component_accounting(legacy, formula, books)

    return {
        "schema": "recipe_externality_audit.v1",
        "classification": "prequential_validation_is_conditional_on_full_recipe",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "sources": {
            "parent_audit": rel(PARENT_RESULT),
            "legacy_script": rel(LEGACY_SCRIPT),
            "formula": rel(legacy.FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "hypothesis_tested": {
            "hypothesis": (
                "The current prequential validation demonstrates a full held-out "
                "generation method for future books."
            ),
            "result": "rejected_as_full_generation_method",
            "reason": (
                "The holdout tests score learned copy-length, literal-payload, and "
                "item-type components, but the LZ recipe itself is read from the "
                "full-corpus formula before splitting."
            ),
        },
        "accounting": accounting,
        "recipe_inventory": all_counts,
        "split_recipe_disclosure": split_recipe_disclosure(parent, formula, books),
        "source_control": source_control(legacy),
        "decision": {
            "predictive_validation_status": "conditional_component_validation",
            "generation_method_status": "not_promoted",
            "row0_origin_changed": False,
            "compression_bound_changed": False,
            "translation_or_plaintext_status": "NONE",
            "next_valid_progress": (
                "A stronger generation claim would need train-only or online recipe "
                "discovery, not only frozen-parameter scoring of a full-corpus recipe."
            ),
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    acc = result["accounting"]
    inv = result["recipe_inventory"]
    lines = [
        "# Recipe Externality Audit",
        "",
        "Classification: `prequential_validation_is_conditional_on_full_recipe`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit quantifies the limitation already declared by the",
        "prequential/row0-origin report: the recipe of literal/copy operations is",
        "fixed from the full-corpus formula. The test is whether the current",
        "prequential evidence proves a full generation method. It does not.",
        "",
        "## Bit Accounting",
        "",
        "| Bucket | Bits | Share |",
        "|---|---:|---:|",
        f"| Active 8558.667-bit formula | `{acc['active_total_bits']:.3f}` | `100.000%` |",
        f"| Prequentially scored components | `{acc['prequentially_scored_component_bits']:.3f}` | `{acc['prequentially_scored_component_share_pct']:.3f}%` |",
        f"| Fixed recipe / non-learned ledger | `{acc['fixed_recipe_or_nonlearned_bits']:.3f}` | `{acc['fixed_recipe_or_nonlearned_share_pct']:.3f}%` |",
        "",
        "Scored components:",
        "",
        "| Component | Bits | Events |",
        "|---|---:|---:|",
        f"| Copy length | `{acc['scored_components']['copy_length_bits']:.3f}` | `{acc['scored_components']['copy_length_events']}` |",
        f"| Literal payload | `{acc['scored_components']['literal_payload_bits']:.3f}` | `{acc['scored_components']['literal_payload_events']}` |",
        f"| Item type | `{acc['scored_components']['item_type_bits']:.3f}` | `{acc['scored_components']['item_type_events']}` |",
        "",
        "Fixed/non-learned ledger:",
        "",
        "| Component | Bits |",
        "|---|---:|",
        f"| Fixed bits ledger | `{acc['fixed_recipe_breakdown']['fixed_bits_ledger']:.3f}` |",
        f"| Literal structure without payload | `{acc['fixed_recipe_breakdown']['literal_structure_no_payload_bits']:.3f}` |",
        f"| Copy address bits | `{acc['fixed_recipe_breakdown']['copy_address_bits']:.3f}` |",
        "",
        "## Recipe Inventory",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Books | `{inv['books']}` |",
        f"| Digits | `{inv['digits']}` |",
        f"| Recipe ops | `{inv['ops']}` |",
        f"| Literal runs | `{inv['literal_runs']}` |",
        f"| Literal payload digits | `{inv['literal_payload_digits']}` |",
        f"| Copy ops / source addresses | `{inv['copy_source_addresses_declared_by_recipe']}` |",
        f"| Copied digits | `{inv['copied_digits']}` |",
        "",
        "## Holdout Disclosure",
        "",
        "Every prefix holdout still receives the held-out recipe structure from the",
        "full formula before scoring the learned components.",
        "",
        "| Split | Test books | Test digits | Known ops | Known copy addresses | Known literal runs | Known copied digits | Online gain | Frozen gain |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["split_recipe_disclosure"]["prefix_future_suffix"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | `{row['test_digits']}` | "
            f"`{row['known_recipe_ops']}` | `{row['known_copy_source_addresses']}` | "
            f"`{row['known_literal_runs']}` | `{row['known_copied_digits']}` | "
            f"`{row['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['frozen_gain_vs_uniform_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "Family holdout failures under the same disclosure:",
            "",
            "| Family | Books | Known ops | Known copy addresses | Known literal runs | Known copied digits | Online gain | Frozen gain |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["split_recipe_disclosure"]["family_failure_rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['known_recipe_ops']}` | `{row['known_copy_source_addresses']}` | "
            f"`{row['known_literal_runs']}` | `{row['known_copied_digits']}` | "
            f"`{row['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['frozen_gain_vs_uniform_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Source Control",
            "",
            f"- Predictive split accepts precomputed rows: `{result['source_control']['predictive_split_accepts_precomputed_rows']}`",
            f"- Predictive split searches recipe ops: `{result['source_control']['predictive_split_selects_or_searches_recipe_ops']}`",
            f"- Main collects rows from the full formula before splitting: `{result['source_control']['main_collects_rows_from_full_formula_before_splitting']}`",
            "",
            "## Decision",
            "",
            "- The current prequential audit is retained as conditional component validation.",
            "- It is not promoted to a full generation method because recipe discovery is external to the test.",
            "- `row0` origin is unchanged and remains exogenous.",
            "- `translation_delta: NONE`; no plaintext or reopening claim is introduced.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "04_recipe_externality_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (TEST_RESULTS / "04_recipe_externality_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
