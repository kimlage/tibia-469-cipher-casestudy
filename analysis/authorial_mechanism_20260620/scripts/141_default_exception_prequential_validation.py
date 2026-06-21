from __future__ import annotations

import copy
import csv
import importlib.util
import json
import math
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
AUDIT_137 = HERE / "scripts" / "137_copy_source_default_decodability_audit.py"
BOOKCASE_MANIFEST = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "tables"
    / "hellgate_public_bookcase_manifest.csv"
)

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
BLOCK_SIZE = 10


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


def bookcase_families() -> dict[str, set[int]]:
    if not BOOKCASE_MANIFEST.exists():
        return {}
    families: dict[str, set[int]] = {}
    with BOOKCASE_MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("local_match_status") != "resolved_unique" or not row.get("local_bookid"):
                continue
            label = f"hellgate_public_bookcase_{row['bookcase_public']}"
            families.setdefault(label, set()).add(int(row["local_bookid"]))
    return {label: books for label, books in families.items() if len(books) >= 2}


def copy_length_context(row: dict[str, Any]) -> str:
    return "first_half" if int(row["book"]) < 35 else "second_half"


def split_rows(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["book"]) in books]


def copy_length_counts(rows: list[dict[str, Any]], *, min_len: int) -> dict[str, Any]:
    counts = {"flag": {}, "exception": {}}
    score_copy_length_default_exception(
        rows,
        min_len=min_len,
        counts=counts,
        update=True,
    )
    return counts


def source_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"flag": {True: 0.0, False: 0.0}, "exception": {}}
    score_source_default_exception(rows, counts=counts, update=True)
    return counts


def score_copy_length_default_exception(
    rows: list[dict[str, Any]],
    *,
    min_len: int,
    counts: dict[str, Any] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = copy.deepcopy(counts) if counts is not None else {"flag": {}, "exception": {}}
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    for row in rows:
        context = copy_length_context(row)
        default = int(row["decoder_max_possible_default"])
        length = int(row["length"])
        is_default = length == default
        flag_bucket = local["flag"].setdefault(context, {True: 0.0, False: 0.0})
        flag_probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(flag_probability)
        if update:
            flag_bucket[is_default] += 1.0
        if is_default:
            default_count += 1
            continue
        legal_lengths = [
            value for value in range(min_len, default + 1) if value != default
        ]
        if length not in legal_lengths:
            raise RuntimeError({"row": row, "legal_lengths": legal_lengths})
        exception_bucket = local["exception"].setdefault(context, {})
        total = sum(exception_bucket.get(value, 0.0) for value in legal_lengths)
        probability = (exception_bucket.get(length, 0.0) + 1.0) / (
            total + len(legal_lengths)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[length] = exception_bucket.get(length, 0.0) + 1.0
        exception_count += 1
    return {
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "counts": local,
    }


def score_source_default_exception(
    rows: list[dict[str, Any]],
    *,
    counts: dict[str, Any] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = (
        copy.deepcopy(counts)
        if counts is not None
        else {"flag": {True: 0.0, False: 0.0}, "exception": {}}
    )
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    for row in rows:
        source = int(row["source_digit_pos"])
        default = int(row["previous_source_plus_length_default"])
        is_default = source == default
        flag_bucket = local["flag"]
        probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(probability)
        if update:
            flag_bucket[is_default] += 1.0
        if is_default:
            default_count += 1
            continue
        legal_sources = [
            value
            for value in range(int(row["legal_source_count"]))
            if value != default
        ]
        if source not in legal_sources:
            raise RuntimeError({"row": row, "legal_sources": legal_sources})
        exception_bucket = local["exception"]
        total = sum(exception_bucket.get(value, 0.0) for value in legal_sources)
        probability = (exception_bucket.get(source, 0.0) + 1.0) / (
            total + len(legal_sources)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[source] = exception_bucket.get(source, 0.0) + 1.0
        exception_count += 1
    return {
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "counts": local,
    }


def uniform_copy_length_bits(rows: list[dict[str, Any]], *, min_len: int) -> float:
    return sum(
        math.log2(int(row["decoder_max_possible_default"]) - min_len + 1)
        for row in rows
    )


def uniform_source_bits(rows: list[dict[str, Any]]) -> float:
    return sum(math.log2(int(row["legal_source_count"])) for row in rows)


def predictive_split(
    *,
    label: str,
    split_type: str,
    train_books: set[int],
    test_books: set[int],
    length_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    min_len: int,
) -> dict[str, Any]:
    train_length = split_rows(length_rows, train_books)
    test_length = split_rows(length_rows, test_books)
    train_source = split_rows(source_rows, train_books)
    test_source = split_rows(source_rows, test_books)

    length_train_counts = copy_length_counts(train_length, min_len=min_len)
    source_train_counts = source_counts(train_source)
    train_length_score = score_copy_length_default_exception(
        train_length,
        min_len=min_len,
        counts=None,
        update=True,
    )
    train_source_score = score_source_default_exception(
        train_source,
        counts=None,
        update=True,
    )
    online_length = score_copy_length_default_exception(
        test_length,
        min_len=min_len,
        counts=length_train_counts,
        update=True,
    )
    frozen_length = score_copy_length_default_exception(
        test_length,
        min_len=min_len,
        counts=length_train_counts,
        update=False,
    )
    online_source = score_source_default_exception(
        test_source,
        counts=source_train_counts,
        update=True,
    )
    frozen_source = score_source_default_exception(
        test_source,
        counts=source_train_counts,
        update=False,
    )
    uniform = {
        "copy_length": uniform_copy_length_bits(test_length, min_len=min_len),
        "copy_source": uniform_source_bits(test_source),
    }
    online = {
        "copy_length": online_length["bits"],
        "copy_source": online_source["bits"],
    }
    frozen = {
        "copy_length": frozen_length["bits"],
        "copy_source": frozen_source["bits"],
    }
    train = {
        "copy_length": train_length_score["bits"],
        "copy_source": train_source_score["bits"],
    }
    train_events = len(train_length) + len(train_source)
    test_events = len(test_length) + len(test_source)
    return {
        "label": label,
        "split_type": split_type,
        "train_books": sorted(train_books),
        "test_books": sorted(test_books),
        "event_counts": {
            "train_copy_length": len(train_length),
            "test_copy_length": len(test_length),
            "train_copy_source": len(train_source),
            "test_copy_source": len(test_source),
        },
        "train_bits": train,
        "test_online_bits": online,
        "test_frozen_bits": frozen,
        "test_uniform_bits": uniform,
        "aggregate": {
            "train_bits": train["copy_length"] + train["copy_source"],
            "test_online_bits": online["copy_length"] + online["copy_source"],
            "test_frozen_bits": frozen["copy_length"] + frozen["copy_source"],
            "test_uniform_bits": uniform["copy_length"] + uniform["copy_source"],
            "online_gain_vs_uniform_bits": (
                uniform["copy_length"]
                + uniform["copy_source"]
                - online["copy_length"]
                - online["copy_source"]
            ),
            "frozen_gain_vs_uniform_bits": (
                uniform["copy_length"]
                + uniform["copy_source"]
                - frozen["copy_length"]
                - frozen["copy_source"]
            ),
            "online_train_test_gap_bits_per_event": (
                (online["copy_length"] + online["copy_source"]) / max(1, test_events)
                - (train["copy_length"] + train["copy_source"]) / max(1, train_events)
            ),
        },
        "component_gain_vs_uniform_bits": {
            "copy_length_online": uniform["copy_length"] - online["copy_length"],
            "copy_length_frozen": uniform["copy_length"] - frozen["copy_length"],
            "copy_source_online": uniform["copy_source"] - online["copy_source"],
            "copy_source_frozen": uniform["copy_source"] - frozen["copy_source"],
        },
        "default_match_counts": {
            "test_copy_length_online_defaults": online_length["default_count"],
            "test_copy_length_online_exceptions": online_length["exception_count"],
            "test_copy_source_online_defaults": online_source["default_count"],
            "test_copy_source_online_exceptions": online_source["exception_count"],
        },
    }


def split_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["online_gain_vs_uniform_bits"]) for row in rows]
    frozen = [float(row["aggregate"]["frozen_gain_vs_uniform_bits"]) for row in rows]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["aggregate"]["online_gain_vs_uniform_bits"],
            "frozen_gain_vs_uniform_bits": row["aggregate"]["frozen_gain_vs_uniform_bits"],
            "component_gain_vs_uniform_bits": row["component_gain_vs_uniform_bits"],
        }
        for row in rows
        if row["aggregate"]["online_gain_vs_uniform_bits"] <= 0
        or row["aggregate"]["frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "split_count": len(rows),
        "online_gain_vs_uniform_bits": summary(online),
        "frozen_gain_vs_uniform_bits": summary(frozen),
        "nonpositive_gain_failures": failures,
    }


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit136 = load_module("audit_136", AUDIT_136)
    audit137 = load_module("audit_137", AUDIT_137)
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    normalized = compile134.normalize_ops(formula)
    active_bits = float(formula["mdl_estimate_rough"][SOURCE_TOTAL_KEY])
    min_len = int(normalized["policy"]["min_len"])

    length_collected = audit136.collect_copy_length_rows(normalized, books)
    source_collected = audit137.collect_source_rows(normalized, books)
    if length_collected["errors"]:
        raise RuntimeError(length_collected["errors"])
    if source_collected["errors"]:
        raise RuntimeError(source_collected["errors"])
    length_rows = length_collected["rows"]
    source_rows = source_collected["rows"]
    if len(length_rows) != len(source_rows):
        raise RuntimeError((len(length_rows), len(source_rows)))

    all_books = set(range(70))
    prefix_rows = [
        predictive_split(
            label=f"prefix_{cutoff}_future_suffix",
            split_type="prefix_future_suffix",
            train_books=set(range(cutoff)),
            test_books=set(range(cutoff, 70)),
            length_rows=length_rows,
            source_rows=source_rows,
            min_len=min_len,
        )
        for cutoff in PREFIX_CUTOFFS
    ]
    block_rows = []
    for start in range(0, 70, BLOCK_SIZE):
        test = set(range(start, min(70, start + BLOCK_SIZE)))
        block_rows.append(
            predictive_split(
                label=f"holdout_block_{start:02d}_{max(test):02d}",
                split_type="contiguous_block_holdout",
                train_books=all_books - test,
                test_books=test,
                length_rows=length_rows,
                source_rows=source_rows,
                min_len=min_len,
            )
        )
    family_rows = [
        predictive_split(
            label=label,
            split_type="public_bookcase_family_holdout",
            train_books=all_books - test,
            test_books=test,
            length_rows=length_rows,
            source_rows=source_rows,
            min_len=min_len,
        )
        for label, test in sorted(bookcase_families().items())
    ]

    prefix_failures = split_summary(prefix_rows)["nonpositive_gain_failures"]
    family_failures = split_summary(family_rows)["nonpositive_gain_failures"]
    prefix_online_failures = [
        row
        for row in prefix_rows
        if row["aggregate"]["online_gain_vs_uniform_bits"] <= 0
    ]
    prefix_frozen_failures = [
        row
        for row in prefix_rows
        if row["aggregate"]["frozen_gain_vs_uniform_bits"] <= 0
    ]
    if prefix_online_failures:
        classification = "default_exception_components_fail_prefix_online_holdout"
    elif prefix_frozen_failures:
        classification = "default_exception_components_online_predictive_frozen_unstable"
    elif family_failures:
        classification = "default_exception_components_partial_under_family_holdout"
    else:
        classification = "default_exception_components_predictive_under_tested_holdouts"

    return {
        "schema": "default_exception_prequential_validation.v1",
        "test": "141_default_exception_prequential_validation",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "active_total_bits": active_bits,
            "components_tested": [
                "copy_length decoder_max_possible default plus adaptive exception length",
                "copy_source previous-source-plus-length default plus adaptive exception source",
            ],
            "baseline": "uniform legal copy length and uniform legal source address per event",
            "declaration_bits_excluded_from_holdout": (
                "Holdout rows test stream prediction only; declaration charges are "
                "fixed global model costs and are not relearned per split."
            ),
        },
        "prefix_future_suffix": {
            "summary": split_summary(prefix_rows),
            "rows": prefix_rows,
        },
        "contiguous_block_holdouts": {
            "summary": split_summary(block_rows),
            "rows": block_rows,
        },
        "public_bookcase_family_holdouts": {
            "summary": split_summary(family_rows),
            "rows": family_rows,
        },
        "decision": {
            "generation_status": classification,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "prefix_online_failure_count": len(prefix_online_failures),
            "prefix_frozen_failure_count": len(prefix_frozen_failures),
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 141. Default/Exception Prequential Validation",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 136 and 137 promoted copy-length and copy-source",
        "default/exception ledgers. This audit asks whether those components",
        "predict held-out books with frozen train counts, or whether the gains",
        "are only full-corpus compression. It does not search new parameters.",
        "",
        "## Prefix Future-Suffix Splits",
        "",
        "| Split | Train books | Test books | Online gain | Frozen gain | Copy-length online | Copy-source online |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["prefix_future_suffix"]["rows"]:
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{row['aggregate']['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['aggregate']['frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['component_gain_vs_uniform_bits']['copy_length_online']:.3f}` | "
            f"`{row['component_gain_vs_uniform_bits']['copy_source_online']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Prefix online gain summary: `{result['prefix_future_suffix']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Prefix frozen gain summary: `{result['prefix_future_suffix']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Block online gain summary: `{result['contiguous_block_holdouts']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Family online gain summary: `{result['public_bookcase_family_holdouts']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Family nonpositive failures: `{result['public_bookcase_family_holdouts']['summary']['nonpositive_gain_failures']}`",
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "default_exception_components_predictive_under_tested_holdouts":
        lines.append(
            "The default/exception components retain positive gains against legal "
            "uniform baselines across the tested prefix, block, and family holdouts."
        )
    elif result["classification"] == "default_exception_components_partial_under_family_holdout":
        lines.append(
            "The default/exception components retain prefix predictive value but "
            "have family-holdout failures, so they remain partial generation "
            "evidence rather than a final authorial method."
        )
    elif result["classification"] == "default_exception_components_online_predictive_frozen_unstable":
        lines.append(
            "The default/exception components retain positive online gains on all "
            "prefix holdouts, but frozen counts from the first 10 books lose to "
            "the legal uniform baseline because copy-source prediction is sparse. "
            "The components are therefore online-predictive but not stable enough "
            "to promote as a frozen generation method."
        )
    else:
        lines.append(
            "At least one prefix online holdout loses to the legal uniform "
            "baseline, so the promoted components should be treated as posthoc "
            "compression until a better train-only model is found."
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced here.",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "141_default_exception_prequential_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "141_default_exception_prequential_validation.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
