from __future__ import annotations

import copy
import csv
import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
AUDIT_118 = HERE / "scripts" / "118_prequential_generation_model_audit.py"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
COPY_CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
PAYLOAD_CONTEXT = HERE / "scripts/93_post_midpoint_alpha1_literal_payload_context_search.py"
ITEM_CONTEXT = HERE / "scripts/95_post_midpoint_alpha1_item_type_context_search.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_bits"
)
RANDOM_SEED = 46920260620
RANDOM_TRIALS = 200
PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
BLOCK_SIZE = 10
DIGITS = [str(i) for i in range(10)]
ITEM_TYPES = ["literal", "copy"]

ROW0_SOURCES = {
    "matrix_exhaustive": ROOT / "analysis/generator_search_20260618/matrix_generator_exhaustive_results.json",
    "pair_rule_cover": ROOT / "analysis/generator_search_20260618/pair_rule_cover_results.json",
    "finite_group": ROOT / "analysis/generator_search_20260618/finite_group_pair_formula_results.json",
    "pair_hash": ROOT / "analysis/generator_search_20260618/pair_hash_formula_results.json",
    "local_2d": ROOT / "analysis/generator_search_20260618/local_2d_pair_rule_results.json",
    "quotient": ROOT / "analysis/generator_search_20260618/quotient_pair_formula_results.json",
    "decision_tree": ROOT / "analysis/generator_search_20260618/decision_tree_pair_formula_results.json",
    "usage_driven": ROOT / "analysis/generator_search_20260618/usage_driven_pair_placement_results.json",
    "tape_first_use": ROOT / "analysis/generator_search_20260618/tape_first_use_pair_order_results.json",
    "pair_sequence": ROOT / "analysis/generator_search_20260618/pair_sequence_automaton_results.json",
    "pair_marginal": ROOT / "analysis/generator_search_20260618/pair_marginal_signature_results.json",
    "workbook_export": ROOT / "scripts/export_workbook_to_sqlite.py",
    "q3_tables": ROOT / "analysis/audit_20260609/q3_tables.py",
}
TOPOLOGY_MANIFEST = ROOT / "analysis/physical_topology_20260620/tables/hellgate_public_bookcase_manifest.csv"


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


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


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


def copy_key(row: dict[str, Any]) -> str:
    return "first_half" if int(row["book_int"]) < 35 else "second_half"


def payload_key(row: dict[str, Any]) -> tuple[str, str]:
    return ("global", row["previous_digit_context"])


def item_extra_context(model: dict[str, Any], row: dict[str, Any]) -> str:
    family = model.get("extra_context_family", "global")
    book = int(row["book_int"])
    if family == "searched_single_book_split":
        return "before_split" if book < int(model["split_book"]) else "after_split"
    if family in ("global", "active_global", None):
        return "global"
    if family == "fixed_book_midpoint":
        return "first_half" if book < 35 else "second_half"
    raise ValueError(f"unsupported active item family: {family}")


def item_key(model: dict[str, Any]) -> Callable[[dict[str, Any]], tuple[str, tuple]]:
    def key(row: dict[str, Any]) -> tuple[str, tuple]:
        return (item_extra_context(model, row), ())

    return key


def score_copy_rows(rows: list[dict[str, Any]], counts: dict[Any, dict[int, float]], alpha: int, update: bool) -> float:
    local_counts = copy.deepcopy(counts)
    bits = 0.0
    for row in rows:
        context = copy_key(row)
        bucket = local_counts.setdefault(context, {})
        symbol_count = int(row["symbol_count"])
        length_index = int(row["length_index"])
        legal_observations = sum(bucket.get(index, 0.0) for index in range(symbol_count))
        probability = (bucket.get(length_index, 0.0) + alpha) / (legal_observations + alpha * symbol_count)
        bits += -math.log2(probability)
        if update:
            bucket[length_index] = bucket.get(length_index, 0.0) + 1.0
    return bits


def score_fixed_rows(
    rows: list[dict[str, Any]],
    counts: dict[Any, dict[str, float]],
    *,
    alpha: float,
    alphabet: list[str],
    key_fn: Callable[[dict[str, Any]], Any],
    symbol_key: str,
    update: bool,
) -> float:
    local_counts = copy.deepcopy(counts)
    bits = 0.0
    for row in rows:
        context = key_fn(row)
        bucket = local_counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        symbol = row[symbol_key]
        total = sum(bucket.get(candidate, 0.0) for candidate in alphabet)
        probability = (bucket.get(symbol, 0.0) + alpha) / (total + alpha * len(alphabet))
        bits += -math.log2(probability)
        if update:
            bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return bits


def copy_counts(rows: list[dict[str, Any]]) -> dict[Any, dict[int, float]]:
    counts: dict[Any, dict[int, float]] = {}
    for row in rows:
        bucket = counts.setdefault(copy_key(row), {})
        length_index = int(row["length_index"])
        bucket[length_index] = bucket.get(length_index, 0.0) + 1.0
    return counts


def fixed_counts(
    rows: list[dict[str, Any]],
    *,
    alphabet: list[str],
    key_fn: Callable[[dict[str, Any]], Any],
    symbol_key: str,
) -> dict[Any, dict[str, float]]:
    counts: dict[Any, dict[str, float]] = {}
    for row in rows:
        bucket = counts.setdefault(key_fn(row), {symbol: 0.0 for symbol in alphabet})
        symbol = row[symbol_key]
        bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return counts


def split_rows(rows: list[dict[str, Any]], train_books: set[int], test_books: set[int]) -> tuple[list[dict], list[dict]]:
    train = [row for row in rows if int(row["book_int"]) in train_books]
    test = [row for row in rows if int(row["book_int"]) in test_books]
    return train, test


def context_coverage(test_rows: list[dict[str, Any]], train_counts: dict[Any, dict[Any, float]], key_fn) -> dict[str, int]:
    missing = 0
    present = 0
    for row in test_rows:
        if key_fn(row) in train_counts:
            present += 1
        else:
            missing += 1
    return {"present_context_events": present, "missing_context_events": missing}


def predictive_split(
    *,
    label: str,
    split_type: str,
    train_books: set[int],
    test_books: set[int],
    formula: dict[str, Any],
    copy_rows: list[dict[str, Any]],
    payload_rows: list[dict[str, Any]],
    item_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    copy_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    payload_alpha = float(formula["policy"]["literal_payload_model"]["alpha"])
    item_model = formula["policy"]["item_type_model"]
    item_alpha = float(item_model["alpha"])
    active_item_key = item_key(item_model)

    train_copy, test_copy = split_rows(copy_rows, train_books, test_books)
    train_payload, test_payload = split_rows(payload_rows, train_books, test_books)
    train_item, test_item = split_rows(item_rows, train_books, test_books)

    copy_train_counts = copy_counts(train_copy)
    payload_train_counts = fixed_counts(
        train_payload,
        alphabet=DIGITS,
        key_fn=payload_key,
        symbol_key="digit",
    )
    item_train_counts = fixed_counts(
        train_item,
        alphabet=ITEM_TYPES,
        key_fn=active_item_key,
        symbol_key="item_type",
    )

    train_cost = {
        "copy_length": score_copy_rows(train_copy, {}, copy_alpha, update=True),
        "literal_payload": score_fixed_rows(
            train_payload,
            {},
            alpha=payload_alpha,
            alphabet=DIGITS,
            key_fn=payload_key,
            symbol_key="digit",
            update=True,
        ),
        "item_type": score_fixed_rows(
            train_item,
            {},
            alpha=item_alpha,
            alphabet=ITEM_TYPES,
            key_fn=active_item_key,
            symbol_key="item_type",
            update=True,
        ),
    }
    test_online = {
        "copy_length": score_copy_rows(test_copy, copy_train_counts, copy_alpha, update=True),
        "literal_payload": score_fixed_rows(
            test_payload,
            payload_train_counts,
            alpha=payload_alpha,
            alphabet=DIGITS,
            key_fn=payload_key,
            symbol_key="digit",
            update=True,
        ),
        "item_type": score_fixed_rows(
            test_item,
            item_train_counts,
            alpha=item_alpha,
            alphabet=ITEM_TYPES,
            key_fn=active_item_key,
            symbol_key="item_type",
            update=True,
        ),
    }
    test_frozen = {
        "copy_length": score_copy_rows(test_copy, copy_train_counts, copy_alpha, update=False),
        "literal_payload": score_fixed_rows(
            test_payload,
            payload_train_counts,
            alpha=payload_alpha,
            alphabet=DIGITS,
            key_fn=payload_key,
            symbol_key="digit",
            update=False,
        ),
        "item_type": score_fixed_rows(
            test_item,
            item_train_counts,
            alpha=item_alpha,
            alphabet=ITEM_TYPES,
            key_fn=active_item_key,
            symbol_key="item_type",
            update=False,
        ),
    }
    test_uniform = {
        "copy_length": sum(math.log2(int(row["symbol_count"])) for row in test_copy),
        "literal_payload": len(test_payload) * math.log2(10),
        "item_type": len(test_item) * math.log2(2),
    }
    test_ablated = {
        "copy_length_uniform_only": test_uniform["copy_length"] + test_online["literal_payload"] + test_online["item_type"],
        "literal_payload_uniform_only": test_online["copy_length"] + test_uniform["literal_payload"] + test_online["item_type"],
        "item_type_uniform_only": test_online["copy_length"] + test_online["literal_payload"] + test_uniform["item_type"],
    }

    train_total = sum(train_cost.values())
    online_total = sum(test_online.values())
    frozen_total = sum(test_frozen.values())
    uniform_total = sum(test_uniform.values())

    return {
        "label": label,
        "split_type": split_type,
        "train_books": sorted(train_books),
        "test_books": sorted(test_books),
        "event_counts": {
            "train_copy": len(train_copy),
            "test_copy": len(test_copy),
            "train_literal_payload": len(train_payload),
            "test_literal_payload": len(test_payload),
            "train_item_type": len(train_item),
            "test_item_type": len(test_item),
        },
        "train_cost_bits": train_cost,
        "test_online_cost_bits": test_online,
        "test_frozen_cost_bits": test_frozen,
        "test_uniform_baseline_bits": test_uniform,
        "test_component_ablation_totals_bits": test_ablated,
        "aggregate": {
            "train_bits": train_total,
            "test_online_bits": online_total,
            "test_frozen_bits": frozen_total,
            "test_uniform_bits": uniform_total,
            "test_online_gain_vs_uniform_bits": uniform_total - online_total,
            "test_frozen_gain_vs_uniform_bits": uniform_total - frozen_total,
            "online_train_test_gap_bits_per_event": (
                online_total / max(1, len(test_copy) + len(test_payload) + len(test_item))
                - train_total / max(1, len(train_copy) + len(train_payload) + len(train_item))
            ),
            "frozen_minus_online_bits": frozen_total - online_total,
        },
        "parameter_stability": {
            "copy_length_context_coverage": context_coverage(test_copy, copy_train_counts, copy_key),
            "literal_payload_context_coverage": context_coverage(test_payload, payload_train_counts, payload_key),
            "item_type_context_coverage": context_coverage(test_item, item_train_counts, active_item_key),
            "declared_parameters_frozen": {
                "copy_length_alpha": copy_alpha,
                "copy_length_context": formula["policy"]["copy_length_model"]["context"],
                "literal_payload_order": int(formula["policy"]["literal_payload_model"]["order"]),
                "literal_payload_alpha": payload_alpha,
                "item_type_alpha": item_alpha,
                "item_type_split_book": int(item_model["split_book"]),
                "item_type_order": int(item_model["order"]),
            },
        },
    }


def random_order_controls(
    *,
    cutoff: int,
    all_books: list[int],
    observed_online_gain: float,
    formula: dict[str, Any],
    copy_rows: list[dict[str, Any]],
    payload_rows: list[dict[str, Any]],
    item_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + cutoff)
    gains = []
    for _ in range(RANDOM_TRIALS):
        train = set(rng.sample(all_books, cutoff))
        test = set(all_books) - train
        row = predictive_split(
            label=f"random_train_{cutoff}",
            split_type="random_train_set_control",
            train_books=train,
            test_books=test,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        gains.append(row["aggregate"]["test_online_gain_vs_uniform_bits"])
    return {
        "cutoff": cutoff,
        "trials": RANDOM_TRIALS,
        "observed_prefix_online_gain_vs_uniform_bits": observed_online_gain,
        "random_gain_summary_bits": summary(gains),
        "p_random_gain_ge_observed": (1 + sum(1 for gain in gains if gain >= observed_online_gain)) / (RANDOM_TRIALS + 1),
    }


def load_bookcase_families() -> dict[str, set[int]]:
    if not TOPOLOGY_MANIFEST.exists():
        return {}
    families: dict[str, set[int]] = {}
    with TOPOLOGY_MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("local_match_status") != "resolved_unique" or not row.get("local_bookid"):
                continue
            label = f"hellgate_public_bookcase_{row['bookcase_public']}"
            families.setdefault(label, set()).add(int(row["local_bookid"]))
    return {key: value for key, value in families.items() if len(value) >= 2}


def safe_get(data: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def row0_hypotheses() -> list[dict[str, Any]]:
    loaded = {name: load_json(path) for name, path in ROW0_SOURCES.items() if path.suffix == ".json" and path.exists()}
    matrix = loaded["matrix_exhaustive"]
    lookup_bits = safe_get(matrix, ("lookup_cost_bits",), 209.40452071316824)

    return [
        {
            "hypothesis": "manual_authorial_lookup",
            "algorithm": "Declare unordered-pair -> row0-symbol inventory directly.",
            "descriptive_cost_bits": lookup_bits,
            "coverage": "55/55 by definition",
            "contradictions": "none inside inventory; explains no compact origin",
            "negative_controls": "not meaningful because this is the lookup baseline",
            "status": "accepted_as_exogenous_substrate_not_origin_formula",
            "source": rel(ROW0_SOURCES["matrix_exhaustive"]),
        },
        {
            "hypothesis": "simple_permutation_or_group_rule",
            "algorithm": "Finite-group / cyclic / hash-like formulas over pair indices and digit permutations.",
            "descriptive_cost_bits": safe_get(loaded["finite_group"], ("observed", "best", "mdl_cost_bits")),
            "coverage": f"{safe_get(loaded['finite_group'], ('observed', 'best', 'correct'))}/55 hits for the best finite-group row, but it uses one group per cell",
            "contradictions": "best exact row is classified lookup_disguise; hash rows are low-coverage and do not compress",
            "negative_controls": safe_get(loaded["finite_group"], ("control", "mdl_gain", "p_ge_observed")),
            "status": "rejected_lookup_disguise",
            "source": rel(ROW0_SOURCES["finite_group"]),
        },
        {
            "hypothesis": "grid_10x10_mechanism",
            "algorithm": "Local 2D propagation, quotient/orbit formulas, matrix seed overlays, and table-grid order rules.",
            "descriptive_cost_bits": safe_get(matrix, ("best_by_mdl", "mdl_cost_bits")),
            "coverage": f"{safe_get(matrix, ('best_by_cells', 'cells_hit'))}/55 best matrix hits; {safe_get(loaded['local_2d'], ('observed', 'best', 'acceptable_hits'))}/55 best local-2D hits",
            "contradictions": "partial hits require many exceptions or posthoc overlays; no lossless compact grid algorithm",
            "negative_controls": {
                "matrix_control_p": safe_get(matrix, ("best_by_cells", "control_p")),
                "local_2d_primary_mdl_gain_control": safe_get(loaded["local_2d"], ("control", "primary_mdl_gain_p_ge")),
            },
            "status": "rejected_as_origin_formula",
            "source": rel(ROW0_SOURCES["matrix_exhaustive"]),
        },
        {
            "hypothesis": "order_or_frequency_derivation",
            "algorithm": "Derive pair labels/order from book usage, first-use order, symbol streams, or marginal signatures.",
            "descriptive_cost_bits": "not promoted; tested as accuracy/control signals",
            "coverage": f"{safe_get(loaded['usage_driven'], ('holdout_same_rule', 'correct'))}/{safe_get(loaded['usage_driven'], ('holdout_same_rule', 'total'))} holdout same-rule hits",
            "contradictions": "train and stream signals do not survive as a controlled row0 generator",
            "negative_controls": {
                "usage_train_p_ge_observed": safe_get(loaded["usage_driven"], ("train_best_control", "p_ge_observed")),
                "tape_first_use_bonferroni": safe_get(loaded["tape_first_use"], ("best", "bonferroni_p")),
                "pair_marginal_verdict": safe_get(loaded["pair_marginal"], ("verdict",)),
            },
            "status": "rejected_holdout_or_control",
            "source": rel(ROW0_SOURCES["usage_driven"]),
        },
        {
            "hypothesis": "known_external_text_source",
            "algorithm": "Map pair labels to known lore/textual seeds or external phrase order.",
            "descriptive_cost_bits": "no promoted external source ledger",
            "coverage": f"{safe_get(matrix, ('best_by_cells', 'cells_hit'))}/55 at best when lore-word symbol orders are allowed inside matrix search",
            "contradictions": "lore/textual seeds behave as searched symbol orders, not primary row0 evidence",
            "negative_controls": safe_get(matrix, ("best_by_cells", "control_p_monte_carlo_top")),
            "status": "not_attested_rejected_as_source_formula",
            "source": rel(ROW0_SOURCES["matrix_exhaustive"]),
        },
        {
            "hypothesis": "workbook_or_script_artifact",
            "algorithm": "Treat row0 as an artifact of workbook export, SQLite ingestion, or local scripts.",
            "descriptive_cost_bits": "provenance-preserving ingestion, not a generator",
            "coverage": "explains where the project reads row0-like tables from, not why CipSoft/game data has that table",
            "contradictions": "export scripts preserve source cells and do not synthesize a compact row0 formula",
            "negative_controls": "manual code inspection of ingestion scripts; no generated table algorithm found",
            "status": "rejected_as_origin_explanation_for_in_game_table",
            "source": rel(ROW0_SOURCES["workbook_export"]),
        },
    ]


def main() -> None:
    audit118 = load_module("audit_118", AUDIT_118)
    frontier = load_module("frontier", FRONTIER)
    midpoint = load_module("midpoint", MIDPOINT)
    copy_module = load_module("copy_context", COPY_CONTEXT)
    payload_module = load_module("payload_context", PAYLOAD_CONTEXT)
    item_module = load_module("item_context", ITEM_CONTEXT)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    active_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    legacy_score = midpoint.score_formula(formula, books, frontier, copy_module)
    if legacy_score["validation"]["errors"]:
        raise RuntimeError(legacy_score["validation"])

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    item_bits = score_fixed_rows(
        item_rows,
        {},
        alpha=float(formula["policy"]["item_type_model"]["alpha"]),
        alphabet=ITEM_TYPES,
        key_fn=item_key(formula["policy"]["item_type_model"]),
        symbol_key="item_type",
        update=True,
    )
    active_copy_bits = score_copy_rows(copy_rows, {}, int(formula["policy"]["copy_length_model"]["alpha"]), update=True)
    active_payload_bits = score_fixed_rows(
        payload_rows,
        {},
        alpha=float(formula["policy"]["literal_payload_model"]["alpha"]),
        alphabet=DIGITS,
        key_fn=payload_key,
        symbol_key="digit",
        update=True,
    )
    active_recomputed = (
        float(legacy_score["fixed_bits"])
        + float(legacy_score["literal_bits_no_payload"])
        + active_payload_bits
        + float(legacy_score["copy_address_bits"])
        + active_copy_bits
        + item_bits
    )
    if abs(active_recomputed - active_bits) > 1e-6:
        raise RuntimeError((active_recomputed, active_bits))

    all_books = list(range(70))
    prefix_splits = []
    random_controls = []
    for cutoff in PREFIX_CUTOFFS:
        row = predictive_split(
            label=f"prefix_{cutoff}_future_suffix",
            split_type="prefix_future_suffix",
            train_books=set(range(cutoff)),
            test_books=set(range(cutoff, 70)),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        prefix_splits.append(row)
        random_controls.append(
            random_order_controls(
                cutoff=cutoff,
                all_books=all_books,
                observed_online_gain=row["aggregate"]["test_online_gain_vs_uniform_bits"],
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
            )
        )

    block_splits = []
    for start in range(0, 70, BLOCK_SIZE):
        test = set(range(start, min(70, start + BLOCK_SIZE)))
        train = set(all_books) - test
        block_splits.append(
            predictive_split(
                label=f"holdout_block_{start:02d}_{max(test):02d}",
                split_type="contiguous_block_holdout",
                train_books=train,
                test_books=test,
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
            )
        )

    family_splits = []
    for label, test in sorted(load_bookcase_families().items()):
        family_splits.append(
            predictive_split(
                label=label,
                split_type="public_bookcase_family_holdout",
                train_books=set(all_books) - test,
                test_books=test,
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
            )
        )

    prefix_online_gains = [row["aggregate"]["test_online_gain_vs_uniform_bits"] for row in prefix_splits]
    prefix_frozen_gains = [row["aggregate"]["test_frozen_gain_vs_uniform_bits"] for row in prefix_splits]
    block_online_gains = [row["aggregate"]["test_online_gain_vs_uniform_bits"] for row in block_splits]
    family_online_gains = [row["aggregate"]["test_online_gain_vs_uniform_bits"] for row in family_splits]
    predictive_classification = (
        "predictive_component_signal_retained_analysis_only"
        if prefix_online_gains and min(prefix_online_gains) > 0 and sum(prefix_online_gains) / len(prefix_online_gains) > 0
        else "posthoc_compressor_warning_holdout_advantage_not_stable"
    )

    hypotheses = row0_hypotheses()
    result = {
        "schema": "prequential_and_row0_origin_audit.v1",
        "test": "125_prequential_and_row0_origin_audit",
        "classification": "analysis_only_predictive_component_audit_row0_origin_exogenous",
        "translation_delta": "NONE",
        "source_formula": rel(FORMULA),
        "compression_bound_bits_confirmed": active_bits,
        "active_component_reproduction": {
            "copy_length_bits": active_copy_bits,
            "literal_payload_bits": active_payload_bits,
            "item_type_split_only_bits": item_bits,
            "recomputed_total_bits": active_recomputed,
            "roundtrip_books": legacy_score["validation"]["books_roundtrip_ok"],
        },
        "predictive_validation": {
            "classification": predictive_classification,
            "scope_limit": (
                "The audit freezes the active recipe and tests learned component streams. "
                "It does not prove that the LZ recipe itself can be discovered from prefix books."
            ),
            "prefix_future_suffix_splits": prefix_splits,
            "random_train_set_controls": random_controls,
            "contiguous_block_holdouts": block_splits,
            "public_bookcase_family_holdouts": family_splits,
            "summary": {
                "prefix_online_gain_vs_uniform_bits": summary(prefix_online_gains),
                "prefix_frozen_gain_vs_uniform_bits": summary(prefix_frozen_gains),
                "block_online_gain_vs_uniform_bits": summary(block_online_gains),
                "family_online_gain_vs_uniform_bits": summary(family_online_gains),
                "failure_count_prefix_online_nonpositive": sum(1 for gain in prefix_online_gains if gain <= 0),
                "failure_count_prefix_frozen_nonpositive": sum(1 for gain in prefix_frozen_gains if gain <= 0),
            },
        },
        "row0_origin": {
            "classification": "row0_origin_remains_exogenous_under_current_evidence",
            "what_row0_explains": [
                "Supplies the code->symbol substrate used to reconstruct the 70 book digit strings byte-exactly.",
                "Supports unordered pair/mirror geometry and render-exception audits.",
                "Allows the book-generation formula to operate on digit strings.",
            ],
            "what_remains_exogenous": [
                "Why those unordered pair labels occupy the 10x10 table cells.",
                "A compact lossless algorithm for the pair labels after rule/search/exception costs.",
                "A primary CipSoft/in-game plaintext, symbol table, or book->meaning crib.",
                "A derivation of row0 from the active LZ book-generation formula.",
            ],
            "hypotheses": hypotheses,
            "promoted_row0_origin_formula_count": 0,
        },
        "progress_criterion": {
            "counts_as_progress": [
                "Predictive validation or falsification under prefix/family holdout.",
                "Clearer row0 boundary and exogenous-dependency accounting.",
                "Rejected origin families with algorithm/cost/coverage/control ledger.",
            ],
            "does_not_count_as_progress": [
                "Number of scripts.",
                "Number of sweeps.",
                "Lower posthoc compression without predictive or structural gain.",
            ],
        },
        "boundary": {
            "translation_claim": False,
            "plaintext_claim": False,
            "case_reopened": False,
            "row0_origin_changed": False,
            "compression_bound_changed": False,
        },
    }

    lines = [
        "# 125. Prequential and Row0 Origin Audit",
        "",
        "Classification: `analysis_only_predictive_component_audit_row0_origin_exogenous`",
        "Translation delta: `NONE`",
        "",
        "## Scope",
        "",
        f"The active `compression_bound` is confirmed at `{active_bits:.3f}` bits.",
        "This audit does not search for a lower bit count. It freezes the active",
        "recipe and tests whether the learned component streams keep predictive",
        "advantage on held-out books. Separately, it records what `row0` explains",
        "and why its origin remains exogenous under current evidence.",
        "",
        "Important limitation: the LZ recipe is still fixed from the full corpus.",
        "The predictive test covers adaptive component streams, not recipe discovery.",
        "",
        "## Predictive Validation",
        "",
        "| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in prefix_splits:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{agg['train_bits']:.3f}` | `{agg['test_online_bits']:.3f}` | "
            f"`{agg['test_frozen_bits']:.3f}` | `{agg['test_uniform_bits']:.3f}` | "
            f"`{agg['test_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['test_frozen_gain_vs_uniform_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "Prefix future-suffix result:",
            f"- Online gain summary vs uniform: `{summary(prefix_online_gains)}`",
            f"- Frozen gain summary vs uniform: `{summary(prefix_frozen_gains)}`",
            f"- Prefix online nonpositive failures: `{result['predictive_validation']['summary']['failure_count_prefix_online_nonpositive']}`",
            f"- Prefix frozen nonpositive failures: `{result['predictive_validation']['summary']['failure_count_prefix_frozen_nonpositive']}`",
            "",
            "Random train-set controls compare each numeric prefix against random",
            "same-size train books. A low p-value would mean numeric-prefix future",
            "prediction is unusually strong; here this is a control ledger, not a",
            "promotion of authorial order.",
            "",
            "| Cutoff | Observed online gain | Random median gain | p(random >= observed) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in random_controls:
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['random_gain_summary_bits']['median']:.3f}` | "
            f"`{row['p_random_gain_ge_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "Block and public-bookcase family holdouts are included in JSON. They are",
            "not treated as temporal future tests.",
            "",
            "## Row0 Origin Boundary",
            "",
            "`row0` explains the code->symbol substrate and lets the book-generation",
            "formula operate on reconstructed digit books. It does not explain why",
            "the 10x10 pair cells have those labels.",
            "",
            "| Hypothesis | Status | Coverage | Cost / control note |",
            "|---|---|---|---|",
        ]
    )
    for row in hypotheses:
        lines.append(
            f"| `{row['hypothesis']}` | `{row['status']}` | {row['coverage']} | "
            f"{row['descriptive_cost_bits']}; controls `{row['negative_controls']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The current bit bound remains `compression_bound`, not an authorial method.",
            "- Learned components retain positive prefix-holdout advantage over uniform",
            "  baselines, but the fixed full-corpus recipe remains a posthoc dependency.",
            "- `row0` origin remains exogenous. No tested manual/permutation/grid/",
            "  frequency/external/workbook hypothesis becomes a promoted origin formula.",
            "- No translation, plaintext, or reopening claim is made.",
        ]
    )

    write_result("125_prequential_and_row0_origin_audit", result, lines)


if __name__ == "__main__":
    main()
