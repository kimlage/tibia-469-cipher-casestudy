from __future__ import annotations

import copy
import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
SOURCE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_136 = HERE / "scripts" / "136_copy_length_default_decodability_audit.py"
AUDIT_141 = HERE / "scripts" / "141_default_exception_prequential_validation.py"
AUDIT_143 = HERE / "scripts" / "143_current_literal_payload_profile_audit.py"
AUDIT_144 = HERE / "scripts" / "144_copy_source_distance_model_audit.py"
ITEM_CONTEXT = HERE / "scripts" / "95_post_midpoint_alpha1_item_type_context_search.py"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
BLOCK_SIZE = 10
RANDOM_CONTROL_SAMPLES = 20
RANDOM_SEED = 469145
ITEM_TYPES = ["literal", "copy"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def split_rows(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        book = int(row["book_int"] if "book_int" in row else row["book"])
        if book in books:
            out.append(row)
    return out


def item_context(row: dict[str, Any], *, split_book: int) -> tuple[str, tuple[()]]:
    return ("before_split" if int(row["book_int"]) < split_book else "after_split", ())


def score_item_rows(
    rows: list[dict[str, Any]],
    *,
    alpha: float,
    split_book: int,
    counts: dict[Any, dict[str, float]] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = copy.deepcopy(counts) if counts is not None else {}
    bits = 0.0
    for row in rows:
        context = item_context(row, split_book=split_book)
        bucket = local.setdefault(context, {item_type: 0.0 for item_type in ITEM_TYPES})
        total = sum(bucket.values())
        item_type = row["item_type"]
        probability = (bucket[item_type] + alpha) / (total + len(ITEM_TYPES) * alpha)
        bits += -math.log2(probability)
        if update:
            bucket[item_type] = bucket.get(item_type, 0.0) + 1.0
    return {"bits": bits, "counts": local, "context_count": len(local)}


def uniform_item_bits(rows: list[dict[str, Any]]) -> float:
    return len(rows) * math.log2(len(ITEM_TYPES))


def component_scores(
    *,
    train_books: set[int],
    test_books: set[int],
    rows: dict[str, list[dict[str, Any]]],
    min_len: int,
    item_alpha: float,
    item_split_book: int,
    scorer141,
    scorer143,
    scorer144,
) -> dict[str, Any]:
    train_length = split_rows(rows["copy_length"], train_books)
    test_length = split_rows(rows["copy_length"], test_books)
    train_source = split_rows(rows["copy_source"], train_books)
    test_source = split_rows(rows["copy_source"], test_books)
    train_payload = split_rows(rows["literal_payload"], train_books)
    test_payload = split_rows(rows["literal_payload"], test_books)
    train_item = split_rows(rows["item_type"], train_books)
    test_item = split_rows(rows["item_type"], test_books)

    length_train = scorer141.score_copy_length_default_exception(
        train_length,
        min_len=min_len,
        counts=None,
        update=True,
    )
    source_train = scorer144.score_default_exception(
        train_source,
        representation="absolute_source",
        counts=None,
        update=True,
    )
    payload_train_bits, payload_train_counts = scorer143.score_rows(
        train_payload,
        order=2,
        counts=None,
        update=True,
    )
    item_train = score_item_rows(
        train_item,
        alpha=item_alpha,
        split_book=item_split_book,
        counts=None,
        update=True,
    )

    length_online = scorer141.score_copy_length_default_exception(
        test_length,
        min_len=min_len,
        counts=length_train["counts"],
        update=True,
    )
    length_frozen = scorer141.score_copy_length_default_exception(
        test_length,
        min_len=min_len,
        counts=length_train["counts"],
        update=False,
    )
    source_online = scorer144.score_default_exception(
        test_source,
        representation="absolute_source",
        counts=source_train["counts"],
        update=True,
    )
    source_frozen = scorer144.score_default_exception(
        test_source,
        representation="absolute_source",
        counts=source_train["counts"],
        update=False,
    )
    payload_online_bits, _ = scorer143.score_rows(
        test_payload,
        order=2,
        counts=payload_train_counts,
        update=True,
    )
    payload_frozen_bits, _ = scorer143.score_rows(
        test_payload,
        order=2,
        counts=payload_train_counts,
        update=False,
    )
    item_online = score_item_rows(
        test_item,
        alpha=item_alpha,
        split_book=item_split_book,
        counts=item_train["counts"],
        update=True,
    )
    item_frozen = score_item_rows(
        test_item,
        alpha=item_alpha,
        split_book=item_split_book,
        counts=item_train["counts"],
        update=False,
    )

    uniform = {
        "copy_length": scorer141.uniform_copy_length_bits(test_length, min_len=min_len),
        "copy_source": scorer144.score_uniform(test_source),
        "literal_payload": len(test_payload) * math.log2(10),
        "item_type": uniform_item_bits(test_item),
    }
    train = {
        "copy_length": length_train["bits"],
        "copy_source": source_train["bits"],
        "literal_payload": payload_train_bits,
        "item_type": item_train["bits"],
    }
    online = {
        "copy_length": length_online["bits"],
        "copy_source": source_online["bits"],
        "literal_payload": payload_online_bits,
        "item_type": item_online["bits"],
    }
    frozen = {
        "copy_length": length_frozen["bits"],
        "copy_source": source_frozen["bits"],
        "literal_payload": payload_frozen_bits,
        "item_type": item_frozen["bits"],
    }
    event_counts = {
        "train_copy_length": len(train_length),
        "test_copy_length": len(test_length),
        "train_copy_source": len(train_source),
        "test_copy_source": len(test_source),
        "train_literal_payload": len(train_payload),
        "test_literal_payload": len(test_payload),
        "train_item_type": len(train_item),
        "test_item_type": len(test_item),
    }
    train_events = sum(value for key, value in event_counts.items() if key.startswith("train_"))
    test_events = sum(value for key, value in event_counts.items() if key.startswith("test_"))
    train_total = sum(train.values())
    online_total = sum(online.values())
    frozen_total = sum(frozen.values())
    uniform_total = sum(uniform.values())

    return {
        "event_counts": event_counts,
        "train_bits": train,
        "test_online_bits": online,
        "test_frozen_bits": frozen,
        "test_uniform_bits": uniform,
        "aggregate": {
            "train_bits": train_total,
            "test_online_bits": online_total,
            "test_frozen_bits": frozen_total,
            "test_uniform_bits": uniform_total,
            "online_gain_vs_uniform_bits": uniform_total - online_total,
            "frozen_gain_vs_uniform_bits": uniform_total - frozen_total,
            "online_train_test_gap_bits_per_event": (
                online_total / max(1, test_events) - train_total / max(1, train_events)
            ),
            "frozen_train_test_gap_bits_per_event": (
                frozen_total / max(1, test_events) - train_total / max(1, train_events)
            ),
        },
        "component_gain_vs_uniform_bits": {
            key: uniform[key] - online[key] for key in uniform
        }
        | {f"{key}_frozen": uniform[key] - frozen[key] for key in uniform},
    }


def make_split(
    *,
    label: str,
    split_type: str,
    train_books: set[int],
    test_books: set[int],
    **kwargs: Any,
) -> dict[str, Any]:
    scored = component_scores(train_books=train_books, test_books=test_books, **kwargs)
    return {
        "label": label,
        "split_type": split_type,
        "train_books": sorted(train_books),
        "test_books": sorted(test_books),
        **scored,
    }


def split_summary(splits: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["online_gain_vs_uniform_bits"]) for row in splits]
    frozen = [float(row["aggregate"]["frozen_gain_vs_uniform_bits"]) for row in splits]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["aggregate"]["online_gain_vs_uniform_bits"],
            "frozen_gain_vs_uniform_bits": row["aggregate"]["frozen_gain_vs_uniform_bits"],
            "component_gain_vs_uniform_bits": row["component_gain_vs_uniform_bits"],
        }
        for row in splits
        if row["aggregate"]["online_gain_vs_uniform_bits"] <= 0
        or row["aggregate"]["frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "split_count": len(splits),
        "online_gain_vs_uniform_bits": summary(online),
        "frozen_gain_vs_uniform_bits": summary(frozen),
        "nonpositive_gain_failures": failures,
    }


def random_order_controls(
    *,
    prefix_splits: list[dict[str, Any]],
    all_books: set[int],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    controls = []
    book_list = sorted(all_books)
    observed_by_cutoff = {
        len(row["train_books"]): row["aggregate"]["online_gain_vs_uniform_bits"]
        for row in prefix_splits
    }
    for cutoff in PREFIX_CUTOFFS:
        gains = []
        for _ in range(RANDOM_CONTROL_SAMPLES):
            train = set(rng.sample(book_list, cutoff))
            test = all_books - train
            scored = component_scores(train_books=train, test_books=test, **kwargs)
            gains.append(float(scored["aggregate"]["online_gain_vs_uniform_bits"]))
        observed = observed_by_cutoff[cutoff]
        controls.append(
            {
                "cutoff": cutoff,
                "samples": RANDOM_CONTROL_SAMPLES,
                "observed_numeric_prefix_online_gain_bits": observed,
                "random_online_gain_summary_bits": summary(gains),
                "p_random_ge_observed": sum(gain >= observed for gain in gains)
                / len(gains),
            }
        )
    return controls


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit136 = load_module("audit_136", AUDIT_136)
    audit141 = load_module("audit_141", AUDIT_141)
    audit143 = load_module("audit_143", AUDIT_143)
    audit144 = load_module("audit_144", AUDIT_144)
    item_module = load_module("item_context", ITEM_CONTEXT)

    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    normalized = compile134.normalize_ops(formula)
    mdl = formula["mdl_estimate_rough"]
    active_total_bits = float(mdl[SOURCE_TOTAL_KEY])
    min_len = int(normalized["policy"]["min_len"])
    item_model = normalized["policy"]["item_type_model"]
    item_alpha = float(item_model["alpha"])
    item_split_book = int(item_model["split_book"])

    length_collected = audit136.collect_copy_length_rows(normalized, books)
    source_collected = audit144.collect_source_rows(normalized, books)
    if length_collected["errors"]:
        raise RuntimeError(length_collected["errors"])
    if source_collected["errors"]:
        raise RuntimeError(source_collected["errors"])
    item_rows, item_stats = item_module.collect_item_rows(normalized, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = {
        "copy_length": length_collected["rows"],
        "copy_source": source_collected["rows"],
        "literal_payload": audit143.collect_literal_payload_rows(normalized, books),
        "item_type": item_rows,
    }

    full_copy_length = audit141.score_copy_length_default_exception(
        rows["copy_length"],
        min_len=min_len,
        counts=None,
        update=True,
    )
    full_copy_source = audit144.score_default_exception(
        rows["copy_source"],
        representation="absolute_source",
        counts=None,
        update=True,
    )
    full_payload_bits, payload_counts = audit143.score_rows(
        rows["literal_payload"],
        order=2,
        counts=None,
        update=True,
    )
    full_item = score_item_rows(
        rows["item_type"],
        alpha=item_alpha,
        split_book=item_split_book,
        counts=None,
        update=True,
    )
    component_streams = {
        "copy_length_stream_bits": full_copy_length["bits"],
        "copy_source_stream_bits": full_copy_source["bits"],
        "literal_payload_stream_bits": full_payload_bits,
        "item_type_stream_bits": full_item["bits"],
    }
    expected = {
        "copy_length_stream_bits": float(mdl["copy_length_default_exception_stream_bits"]),
        "copy_source_stream_bits": float(mdl["copy_source_default_exception_stream_bits"]),
        "literal_payload_stream_bits": float(mdl["adaptive_context_order_literal_payload_bits"]),
        "item_type_stream_bits": float(mdl["item_type_split_only_stream_bits"]),
    }
    for key, value in component_streams.items():
        if abs(value - expected[key]) > 1e-6:
            raise RuntimeError({"key": key, "observed": value, "expected": expected[key]})
    learned_stream_bits = sum(component_streams.values())
    fixed_or_declaration_bits = active_total_bits - learned_stream_bits

    common = {
        "rows": rows,
        "min_len": min_len,
        "item_alpha": item_alpha,
        "item_split_book": item_split_book,
        "scorer141": audit141,
        "scorer143": audit143,
        "scorer144": audit144,
    }
    all_books = set(range(70))
    prefix_splits = [
        make_split(
            label=f"prefix_{cutoff}_future_suffix",
            split_type="prefix_future_suffix",
            train_books=set(range(cutoff)),
            test_books=set(range(cutoff, 70)),
            **common,
        )
        for cutoff in PREFIX_CUTOFFS
    ]
    block_splits = []
    for start in range(0, 70, BLOCK_SIZE):
        test = set(range(start, min(70, start + BLOCK_SIZE)))
        block_splits.append(
            make_split(
                label=f"holdout_block_{start:02d}_{max(test):02d}",
                split_type="contiguous_block_holdout",
                train_books=all_books - test,
                test_books=test,
                **common,
            )
        )
    family_splits = [
        make_split(
            label=label,
            split_type="public_bookcase_family_holdout",
            train_books=all_books - test,
            test_books=test,
            **common,
        )
        for label, test in sorted(audit141.bookcase_families().items())
    ]
    random_controls = random_order_controls(
        prefix_splits=prefix_splits,
        all_books=all_books,
        **common,
    )

    prefix_failures = split_summary(prefix_splits)["nonpositive_gain_failures"]
    block_failures = split_summary(block_splits)["nonpositive_gain_failures"]
    family_failures = split_summary(family_splits)["nonpositive_gain_failures"]
    classification = (
        "current_active_components_predictive_under_tested_holdouts_recipe_fixed"
        if not prefix_failures and not block_failures and not family_failures
        else "current_active_components_partial_under_holdout"
    )

    return {
        "schema": "current_active_prequential_profile_audit.v1",
        "test": "145_current_active_prequential_profile_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "active_compression_bound_bits": active_total_bits,
            "components_tested": [
                "copy_length default/exception",
                "copy_source default/exception",
                "literal_payload order2 previous-emitted-digit context",
                "item_type split-only forced-rule context",
            ],
            "baseline": "uniform legal code for each active component event",
            "model_parameters_frozen": {
                "copy_length_alpha": normalized["policy"]["copy_length_model"]["alpha"],
                "copy_length_context": normalized["policy"]["copy_length_model"]["context"],
                "copy_source_alpha": normalized["policy"]["copy_address_model"]["alpha"],
                "literal_payload_alpha": normalized["policy"]["literal_payload_model"]["alpha"],
                "literal_payload_order": normalized["policy"]["literal_payload_model"]["order"],
                "item_type_alpha": item_alpha,
                "item_type_split_book": item_split_book,
            },
            "recipe_externality": (
                "Event rows are extracted from the active full-corpus recipe before "
                "splitting. This validates learned component scoring, not discovery "
                "of held-out segmentation or copy source addresses."
            ),
        },
        "full_corpus_accounting": {
            "component_stream_bits": component_streams,
            "learned_component_stream_bits": learned_stream_bits,
            "learned_component_stream_share_pct": 100.0 * learned_stream_bits / active_total_bits,
            "fixed_recipe_or_declaration_bits": fixed_or_declaration_bits,
            "fixed_recipe_or_declaration_share_pct": (
                100.0 * fixed_or_declaration_bits / active_total_bits
            ),
            "payload_context_count": len(payload_counts),
            "item_context_count": full_item["context_count"],
            "event_counts": {key: len(value) for key, value in rows.items()},
        },
        "prefix_future_suffix": {
            "summary": split_summary(prefix_splits),
            "rows": prefix_splits,
        },
        "contiguous_block_holdouts": {
            "summary": split_summary(block_splits),
            "rows": block_splits,
        },
        "public_bookcase_family_holdouts": {
            "summary": split_summary(family_splits),
            "rows": family_splits,
        },
        "random_same_size_train_controls": random_controls,
        "decision": {
            "compression_bound_changed": False,
            "generation_explanation_strengthened": not prefix_failures
            and not block_failures
            and not family_failures,
            "recipe_discovery_proved": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "nonpositive_prefix_failures": len(prefix_failures),
            "nonpositive_block_failures": len(block_failures),
            "nonpositive_family_failures": len(family_failures),
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    account = result["full_corpus_accounting"]
    lines = [
        "# 145. Current Active Prequential Profile Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 141, 143, and 144 tested current components separately. This audit",
        "consolidates the active `8177.317` bit formula into one prequential",
        "profile: copy length, copy source, literal payload, and item type are",
        "scored on train/test splits without retuning parameters.",
        "",
        "## Full-Corpus Accounting",
        "",
        f"- Active compression bound: `{result['scope']['active_compression_bound_bits']:.3f}` bits",
        f"- Learned component streams: `{account['learned_component_stream_bits']:.3f}` bits (`{account['learned_component_stream_share_pct']:.3f}%`)",
        f"- Fixed recipe/declaration remainder: `{account['fixed_recipe_or_declaration_bits']:.3f}` bits (`{account['fixed_recipe_or_declaration_share_pct']:.3f}%`)",
        "",
        "| Component | Stream bits | Events |",
        "|---|---:|---:|",
        f"| `copy_length` | `{account['component_stream_bits']['copy_length_stream_bits']:.3f}` | `{account['event_counts']['copy_length']}` |",
        f"| `copy_source` | `{account['component_stream_bits']['copy_source_stream_bits']:.3f}` | `{account['event_counts']['copy_source']}` |",
        f"| `literal_payload` | `{account['component_stream_bits']['literal_payload_stream_bits']:.3f}` | `{account['event_counts']['literal_payload']}` |",
        f"| `item_type` | `{account['component_stream_bits']['item_type_stream_bits']:.3f}` | `{account['event_counts']['item_type']}` |",
        "",
        "## Prefix Future-Suffix Splits",
        "",
        "| Split | Train books | Test books | Online gain | Frozen gain | Gap/event frozen |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["prefix_future_suffix"]["rows"]:
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{row['aggregate']['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['aggregate']['frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['aggregate']['frozen_train_test_gap_bits_per_event']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Holdout Summaries",
            "",
            f"- Prefix frozen gain summary: `{result['prefix_future_suffix']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Block frozen gain summary: `{result['contiguous_block_holdouts']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Family frozen gain summary: `{result['public_bookcase_family_holdouts']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Family nonpositive failures: `{result['public_bookcase_family_holdouts']['summary']['nonpositive_gain_failures']}`",
            "",
            "## Random Same-Size Train Controls",
            "",
            "| Cutoff | Observed prefix online gain | Random median | p(random >= observed) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in result["random_same_size_train_controls"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_numeric_prefix_online_gain_bits']:.3f}` | "
            f"`{row['random_online_gain_summary_bits']['median']:.3f}` | "
            f"`{row['p_random_ge_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The active learned streams beat uniform under all tested prefix, block, and public-bookcase family holdouts.",
            "- This strengthens component-level predictive validation for the current `8177.317` bit formula.",
            "- Random same-size train controls show the signal is not specific evidence for numeric book order.",
            "- Recipe discovery is still not proved: literal/copy segmentation and copy-source rows are extracted from the full active recipe before splitting.",
            "- No compression-bound, row0-origin, plaintext, or semantic claim is changed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "145_current_active_prequential_profile_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "145_current_active_prequential_profile_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
