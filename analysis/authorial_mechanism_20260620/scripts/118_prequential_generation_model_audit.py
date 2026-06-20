from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
PAYLOAD_CONTEXT = HERE / "scripts/93_post_midpoint_alpha1_literal_payload_context_search.py"
ITEM_CONTEXT = HERE / "scripts/95_post_midpoint_alpha1_item_type_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits"
DIGITS = [str(i) for i in range(10)]
ITEM_TYPES = ["literal", "copy"]
TRAIN_CUTOFFS = [10, 20, 35, 50, 60]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_context(row: dict) -> str:
    return "first_half" if int(row["book_int"]) < 35 else "second_half"


def item_extra_context(model: dict, row: dict) -> str:
    family = model.get("extra_context_family", "global")
    book = int(row["book_int"])
    if family in ("global", "active_global", None):
        return "global"
    if family == "fixed_book_midpoint":
        return "first_half" if book < 35 else "second_half"
    if family == "fixed_book_quartile":
        return str(min(3, book // 18))
    if family == "fixed_book_decade":
        return str(book // 10)
    if family == "fixed_book_parity":
        return str(book % 2)
    if family == "op_index":
        return str(min(6, int(math.floor(math.log2(max(1, int(row["op_index"]) + 1))))))
    if family == "declared_remaining":
        return str(min(8, int(math.floor(math.log2(max(1, int(row["remaining"])))))))
    if family == "searched_single_book_split":
        return "before_split" if book < int(model["split_book"]) else "after_split"
    raise ValueError(family)


def copy_counts(rows: list[dict], alpha: int, update: bool = True) -> dict:
    counts: dict[str, dict[int, int]] = {}
    for row in rows:
        context = copy_context(row)
        bucket = counts.setdefault(context, {})
        if update:
            length_index = int(row["length_index"])
            bucket[length_index] = bucket.get(length_index, 0) + 1
    return counts


def score_copy_rows(rows: list[dict], counts: dict, alpha: int, update: bool) -> float:
    local_counts = copy.deepcopy(counts)
    bits = 0.0
    for row in rows:
        context = copy_context(row)
        bucket = local_counts.setdefault(context, {})
        symbol_count = int(row["symbol_count"])
        length_index = int(row["length_index"])
        legal_observations = sum(bucket.get(index, 0) for index in range(symbol_count))
        denominator = legal_observations + alpha * symbol_count
        numerator = bucket.get(length_index, 0) + alpha
        bits += -math.log2(numerator / denominator)
        if update:
            bucket[length_index] = bucket.get(length_index, 0) + 1
    return bits


def score_fixed_alphabet_rows(
    rows: list[dict],
    counts: dict,
    *,
    alpha: float,
    alphabet: list[str],
    context_key,
    symbol_key: str,
    update: bool,
) -> float:
    local_counts = copy.deepcopy(counts)
    bits = 0.0
    for row in rows:
        context = context_key(row)
        bucket = local_counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        total = sum(bucket.get(symbol, 0.0) for symbol in alphabet)
        symbol = row[symbol_key]
        probability = (bucket.get(symbol, 0.0) + alpha) / (total + len(alphabet) * alpha)
        bits += -math.log2(probability)
        if update:
            bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return bits


def fixed_alphabet_counts(rows: list[dict], *, alphabet: list[str], context_key, symbol_key: str) -> dict:
    counts = {}
    for row in rows:
        context = context_key(row)
        bucket = counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        symbol = row[symbol_key]
        bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return counts


def payload_context_key(row: dict) -> tuple[str, str]:
    return ("global", row["previous_digit_context"])


def item_context_key(model: dict):
    def key(row: dict) -> tuple[str, tuple[str, ...]]:
        return (item_extra_context(model, row), tuple(row["previous_item_context"]))

    return key


def component_summary(
    *,
    name: str,
    train_rows: list[dict],
    holdout_rows: list[dict],
    posthoc_bits: float,
    online_bits: float,
    frozen_bits: float,
    uniform_bits: float,
) -> dict:
    event_count = len(holdout_rows)
    return {
        "component": name,
        "train_events": len(train_rows),
        "holdout_events": event_count,
        "holdout_posthoc_adaptive_bits": posthoc_bits,
        "holdout_prefix_online_bits": online_bits,
        "holdout_prefix_frozen_bits": frozen_bits,
        "holdout_uniform_bits": uniform_bits,
        "online_vs_uniform_bits": online_bits - uniform_bits,
        "frozen_vs_uniform_bits": frozen_bits - uniform_bits,
        "online_excess_vs_posthoc_bits": online_bits - posthoc_bits,
        "frozen_excess_vs_posthoc_bits": frozen_bits - posthoc_bits,
        "online_bits_per_event": online_bits / event_count if event_count else None,
        "frozen_bits_per_event": frozen_bits / event_count if event_count else None,
        "uniform_bits_per_event": uniform_bits / event_count if event_count else None,
    }


def cutoff_audit(cutoff: int, formula: dict, copy_rows: list[dict], payload_rows: list[dict], item_rows: list[dict]) -> dict:
    copy_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    payload_alpha = float(formula["policy"]["literal_payload_model"]["alpha"])
    item_model = formula["policy"]["item_type_model"]
    item_alpha = float(item_model["alpha"])
    item_key = item_context_key(item_model)

    def split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
        return (
            [row for row in rows if int(row["book_int"]) < cutoff],
            [row for row in rows if int(row["book_int"]) >= cutoff],
        )

    train_copy, holdout_copy = split(copy_rows)
    train_payload, holdout_payload = split(payload_rows)
    train_item, holdout_item = split(item_rows)

    copy_train_counts = copy_counts(train_copy, copy_alpha)
    payload_train_counts = fixed_alphabet_counts(
        train_payload,
        alphabet=DIGITS,
        context_key=payload_context_key,
        symbol_key="digit",
    )
    item_train_counts = fixed_alphabet_counts(
        train_item,
        alphabet=ITEM_TYPES,
        context_key=item_key,
        symbol_key="item_type",
    )

    copy_posthoc = score_copy_rows(holdout_copy, {}, copy_alpha, update=True)
    copy_online = score_copy_rows(holdout_copy, copy_train_counts, copy_alpha, update=True)
    copy_frozen = score_copy_rows(holdout_copy, copy_train_counts, copy_alpha, update=False)
    copy_uniform = sum(math.log2(int(row["symbol_count"])) for row in holdout_copy)

    payload_posthoc = score_fixed_alphabet_rows(
        holdout_payload,
        {},
        alpha=payload_alpha,
        alphabet=DIGITS,
        context_key=payload_context_key,
        symbol_key="digit",
        update=True,
    )
    payload_online = score_fixed_alphabet_rows(
        holdout_payload,
        payload_train_counts,
        alpha=payload_alpha,
        alphabet=DIGITS,
        context_key=payload_context_key,
        symbol_key="digit",
        update=True,
    )
    payload_frozen = score_fixed_alphabet_rows(
        holdout_payload,
        payload_train_counts,
        alpha=payload_alpha,
        alphabet=DIGITS,
        context_key=payload_context_key,
        symbol_key="digit",
        update=False,
    )
    payload_uniform = len(holdout_payload) * math.log2(10)

    item_posthoc = score_fixed_alphabet_rows(
        holdout_item,
        {},
        alpha=item_alpha,
        alphabet=ITEM_TYPES,
        context_key=item_key,
        symbol_key="item_type",
        update=True,
    )
    item_online = score_fixed_alphabet_rows(
        holdout_item,
        item_train_counts,
        alpha=item_alpha,
        alphabet=ITEM_TYPES,
        context_key=item_key,
        symbol_key="item_type",
        update=True,
    )
    item_frozen = score_fixed_alphabet_rows(
        holdout_item,
        item_train_counts,
        alpha=item_alpha,
        alphabet=ITEM_TYPES,
        context_key=item_key,
        symbol_key="item_type",
        update=False,
    )
    item_uniform = len(holdout_item) * math.log2(2)

    components = [
        component_summary(
            name="copy_length",
            train_rows=train_copy,
            holdout_rows=holdout_copy,
            posthoc_bits=copy_posthoc,
            online_bits=copy_online,
            frozen_bits=copy_frozen,
            uniform_bits=copy_uniform,
        ),
        component_summary(
            name="literal_payload",
            train_rows=train_payload,
            holdout_rows=holdout_payload,
            posthoc_bits=payload_posthoc,
            online_bits=payload_online,
            frozen_bits=payload_frozen,
            uniform_bits=payload_uniform,
        ),
        component_summary(
            name="item_type",
            train_rows=train_item,
            holdout_rows=holdout_item,
            posthoc_bits=item_posthoc,
            online_bits=item_online,
            frozen_bits=item_frozen,
            uniform_bits=item_uniform,
        ),
    ]
    aggregate = {
        key: sum(component[key] for component in components)
        for key in [
            "holdout_posthoc_adaptive_bits",
            "holdout_prefix_online_bits",
            "holdout_prefix_frozen_bits",
            "holdout_uniform_bits",
            "online_vs_uniform_bits",
            "frozen_vs_uniform_bits",
            "online_excess_vs_posthoc_bits",
            "frozen_excess_vs_posthoc_bits",
        ]
    }
    return {
        "train_books": list(range(0, cutoff)),
        "holdout_books": list(range(cutoff, 70)),
        "components": components,
        "aggregate_learned_components": aggregate,
    }


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    payload = load_module("literal_payload_context", PAYLOAD_CONTEXT)
    item_context = load_module("item_type_context", ITEM_CONTEXT)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    copy_rows = context_module.collect_copy_rows(formula, books)
    payload_rows = payload.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_context.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    copy_active = score_copy_rows(copy_rows, {}, int(formula["policy"]["copy_length_model"]["alpha"]), update=True)
    payload_active = score_fixed_alphabet_rows(
        payload_rows,
        {},
        alpha=float(formula["policy"]["literal_payload_model"]["alpha"]),
        alphabet=DIGITS,
        context_key=payload_context_key,
        symbol_key="digit",
        update=True,
    )
    item_active = score_fixed_alphabet_rows(
        item_rows,
        {},
        alpha=float(formula["policy"]["item_type_model"]["alpha"]),
        alphabet=ITEM_TYPES,
        context_key=item_context_key(formula["policy"]["item_type_model"]),
        symbol_key="item_type",
        update=True,
    )
    expected = {
        "copy_length": current_score["copy_length_code_bits"],
        "literal_payload": current_score["literal_payload_bits"],
        "item_type": current_score["item_type_stream_bits"],
    }
    observed = {
        "copy_length": copy_active,
        "literal_payload": payload_active,
        "item_type": item_active,
    }
    for key, value in expected.items():
        if abs(float(value) - observed[key]) > 1e-6:
            raise RuntimeError((key, value, observed[key]))

    cutoffs = [cutoff_audit(cutoff, formula, copy_rows, payload_rows, item_rows) for cutoff in TRAIN_CUTOFFS]
    aggregate_online_wins = sum(
        1 for row in cutoffs if row["aggregate_learned_components"]["online_vs_uniform_bits"] < 0
    )
    aggregate_frozen_wins = sum(
        1 for row in cutoffs if row["aggregate_learned_components"]["frozen_vs_uniform_bits"] < 0
    )
    classification = (
        "prequential_generation_partial_not_final"
        if aggregate_online_wins and aggregate_frozen_wins
        else "prequential_generation_weak_or_posthoc"
    )

    result = {
        "schema": "prequential_generation_model_audit.v1",
        "test": "118_prequential_generation_model_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "compression_bound_bits": current_bits,
        "generation_explanation": {
            "status": classification,
            "interpretation": (
                "The active formula remains the compression_bound. Prequential "
                "component generalization is evidence about generation_explanation, "
                "not a new lower MDL bound or semantic reading."
            ),
            "row0_origin_status": "open_not_explained_by_lz_book_generator",
        },
        "current_score_audit": current_score,
        "active_component_reproduction": {
            "expected": expected,
            "observed": observed,
        },
        "event_counts": {
            "copy_length_rows": len(copy_rows),
            "literal_payload_rows": len(payload_rows),
            "item_type_rows": len(item_rows),
        },
        "train_cutoffs": cutoffs,
        "summary": {
            "aggregate_online_beats_uniform_cutoffs": aggregate_online_wins,
            "aggregate_frozen_beats_uniform_cutoffs": aggregate_frozen_wins,
            "cutoffs_tested": TRAIN_CUTOFFS,
            "micro_sweep_policy": (
                "Do not treat further small post-itemctx_param pair sweeps as "
                "mainline progress unless they introduce a structural mechanism, "
                "large gain, better holdout behavior, or simplification."
            ),
        },
        "boundary": formula["boundary"],
    }

    lines = [
        "# Prequential Generation Model Audit",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit separates the current `compression_bound` from a stronger",
        "`generation_explanation` claim. It freezes or pretrains the learned",
        "adaptive components on prefix books and scores later books without",
        "searching new parameters or changing the recipe.",
        "",
        "## Current Boundary",
        "",
        f"- Compression bound: `{current_bits:.3f}` bits",
        "- This is not promoted as the final authorial method.",
        "- The row0 / 10x10 table origin remains open.",
        "",
        "## Coverage",
        "",
        f"- Copy-length rows: `{len(copy_rows)}`",
        f"- Literal-payload rows: `{len(payload_rows)}`",
        f"- Item-type rows: `{len(item_rows)}`",
        "",
        "## Aggregate Learned-Component Holdouts",
        "",
        "| Train books | Holdout books | Posthoc bits | Prefix-online bits | Prefix-frozen bits | Uniform bits | Online vs uniform | Frozen vs uniform |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in cutoffs:
        agg = row["aggregate_learned_components"]
        lines.append(
            f"| `{len(row['train_books'])}` | `{len(row['holdout_books'])}` | "
            f"`{agg['holdout_posthoc_adaptive_bits']:.3f}` | "
            f"`{agg['holdout_prefix_online_bits']:.3f}` | "
            f"`{agg['holdout_prefix_frozen_bits']:.3f}` | "
            f"`{agg['holdout_uniform_bits']:.3f}` | "
            f"`{agg['online_vs_uniform_bits']:.3f}` | "
            f"`{agg['frozen_vs_uniform_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The learned components are evaluated as predictive structure, not as",
            "more post-hoc compression. Prefix-online scoring asks whether the same",
            "adaptive rules continue to compress future books after seeing a prefix;",
            "prefix-frozen scoring is stricter and asks whether prefix counts alone",
            "are enough without further adaptation.",
            "",
            "This audit therefore marks the current `8561.792` bit formula as the",
            "active compression bound and moves mainline progress criteria toward",
            "holdout behavior, structural mechanisms, simplification, or row0 origin",
            "evidence.",
            "",
            "## Boundary",
            "",
            "This is a mechanical validation audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("118_prequential_generation_model_audit", result, lines)


if __name__ == "__main__":
    main()
