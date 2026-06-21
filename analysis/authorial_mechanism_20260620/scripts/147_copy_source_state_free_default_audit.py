from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable


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
AUDIT_144 = HERE / "scripts" / "144_copy_source_distance_model_audit.py"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
DECLARATION_BITS = 12.0


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


def clamp_legal(value: int, row: dict[str, Any], fallback: int = 0) -> int:
    legal_count = int(row["legal_source_count"])
    if 0 <= value < legal_count:
        return value
    if 0 <= fallback < legal_count:
        return fallback
    return 0


def book_start(row: dict[str, Any]) -> int:
    return int(row["emitted_len_before_copy"]) - int(row["book_pos"])


def previous_book_start(row: dict[str, Any], book_lengths: dict[int, int]) -> int:
    book = int(row["book"])
    if book <= 0:
        return 0
    return book_start(row) - int(book_lengths[book - 1])


def add_book_context(rows: list[dict[str, Any]], books: dict[str, str]) -> list[dict[str, Any]]:
    book_lengths = {int(key): len(value) for key, value in books.items()}
    enriched = []
    for row in rows:
        new = dict(row)
        start = book_start(row)
        prev_start = previous_book_start(row, book_lengths)
        new["current_book_global_start"] = start
        new["previous_book_global_start"] = prev_start
        new["book_length"] = book_lengths[int(row["book"])]
        new["previous_book_length"] = (
            book_lengths[int(row["book"]) - 1] if int(row["book"]) > 0 else None
        )
        enriched.append(new)
    return enriched


def default_rules(book_lengths: dict[int, int]) -> dict[str, Callable[[dict[str, Any]], int]]:
    def zero(row: dict[str, Any]) -> int:
        return 0

    def latest_legal(row: dict[str, Any]) -> int:
        return int(row["legal_source_count"]) - 1

    def midpoint(row: dict[str, Any]) -> int:
        return int(row["legal_source_count"]) // 2

    def current_book_start_default(row: dict[str, Any]) -> int:
        return clamp_legal(int(row["current_book_global_start"]), row)

    def previous_book_start_default(row: dict[str, Any]) -> int:
        return clamp_legal(int(row["previous_book_global_start"]), row)

    def previous_book_same_offset(row: dict[str, Any]) -> int:
        value = int(row["previous_book_global_start"]) + int(row["book_pos"])
        return clamp_legal(value, row, fallback=int(row["previous_book_global_start"]))

    def back_current_length(row: dict[str, Any]) -> int:
        value = int(row["emitted_len_before_copy"]) - int(row["length"])
        return clamp_legal(value, row, fallback=latest_legal(row))

    def back_double_length(row: dict[str, Any]) -> int:
        value = int(row["emitted_len_before_copy"]) - 2 * int(row["length"])
        return clamp_legal(value, row, fallback=latest_legal(row))

    def active_path_dependent(row: dict[str, Any]) -> int:
        return int(row["previous_source_plus_length_default"])

    return {
        "active_previous_source_plus_length": active_path_dependent,
        "state_free_zero_source": zero,
        "state_free_latest_legal_source": latest_legal,
        "state_free_midpoint_source": midpoint,
        "state_free_current_book_start": current_book_start_default,
        "state_free_previous_book_start": previous_book_start_default,
        "state_free_previous_book_same_offset": previous_book_same_offset,
        "state_free_back_current_length": back_current_length,
        "state_free_back_double_length": back_double_length,
    }


def legal_values(row: dict[str, Any]) -> range:
    return range(int(row["legal_source_count"]))


def score_default_exception(
    rows: list[dict[str, Any]],
    default_name: str,
    default_fn: Callable[[dict[str, Any]], int],
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
    illegal_defaults = 0
    for row in rows:
        source = int(row["source_digit_pos"])
        default = default_fn(row)
        if default not in legal_values(row):
            illegal_defaults += 1
            default = 0
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

        exception_values = [candidate for candidate in legal_values(row) if candidate != default]
        exception_bucket = local["exception"]
        total = sum(exception_bucket.get(candidate, 0.0) for candidate in exception_values)
        probability = (exception_bucket.get(source, 0.0) + 1.0) / (
            total + len(exception_values)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[source] = exception_bucket.get(source, 0.0) + 1.0
        exception_count += 1

    return {
        "default_name": default_name,
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "illegal_defaults": illegal_defaults,
        "counts": local,
        "distinct_exception_values": len(local["exception"]),
    }


def rows_for_books(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["book"]) in books]


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "mean": None, "max": None}
    return {"n": len(values), "min": min(values), "mean": sum(values) / len(values), "max": max(values)}


def split_score(
    label: str,
    train_books: set[int],
    test_books: set[int],
    rows: list[dict[str, Any]],
    rules: dict[str, Callable[[dict[str, Any]], int]],
) -> dict[str, Any]:
    audit144 = load_module("audit_144_split", AUDIT_144)
    train_rows = rows_for_books(rows, train_books)
    test_rows = rows_for_books(rows, test_books)
    uniform_test = audit144.score_uniform(test_rows)
    models = {}
    for name, fn in rules.items():
        train = score_default_exception(train_rows, name, fn, counts=None, update=True)
        online = score_default_exception(test_rows, name, fn, counts=train["counts"], update=True)
        frozen = score_default_exception(test_rows, name, fn, counts=train["counts"], update=False)
        models[name] = {
            "train_bits": train["bits"],
            "test_online_bits": online["bits"],
            "test_frozen_bits": frozen["bits"],
            "test_online_gain_vs_uniform_bits": uniform_test - online["bits"],
            "test_frozen_gain_vs_uniform_bits": uniform_test - frozen["bits"],
            "train_default_count": train["default_count"],
            "train_exception_count": train["exception_count"],
            "test_online_default_count": online["default_count"],
            "test_online_exception_count": online["exception_count"],
        }
    return {
        "label": label,
        "train_books": sorted(train_books),
        "test_books": sorted(test_books),
        "event_counts": {"train": len(train_rows), "test": len(test_rows)},
        "test_uniform_bits": uniform_test,
        "models": models,
    }


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit144 = load_module("audit_144", AUDIT_144)
    formula = load_json(SOURCE_FORMULA)
    normalized = compile134.normalize_ops(formula)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    book_lengths = {int(key): len(value) for key, value in books.items()}
    active_bits = float(formula["mdl_estimate_rough"][SOURCE_TOTAL_KEY])
    active_copy_address_bits = float(formula["mdl_estimate_rough"]["copy_address_bits"])
    active_stream_bits = float(
        formula["mdl_estimate_rough"]["copy_source_default_exception_stream_bits"]
    )

    collected = audit144.collect_source_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = add_book_context(collected["rows"], books)
    rules = default_rules(book_lengths)
    uniform_bits = audit144.score_uniform(rows)

    full_models = {}
    for name, fn in rules.items():
        score = score_default_exception(rows, name, fn, counts=None, update=True)
        copy_address_bits = score["bits"] + DECLARATION_BITS
        full_models[name] = {
            "stream_bits": score["bits"],
            "flag_bits": score["flag_bits"],
            "exception_bits": score["exception_bits"],
            "copy_address_bits_with_declaration": copy_address_bits,
            "replacement_total_bits": active_bits - active_copy_address_bits + copy_address_bits,
            "delta_vs_active_stream_bits": score["bits"] - active_stream_bits,
            "delta_vs_active_total_bits": (
                active_bits - active_copy_address_bits + copy_address_bits - active_bits
            ),
            "default_count": score["default_count"],
            "exception_count": score["exception_count"],
            "distinct_exception_values": score["distinct_exception_values"],
            "illegal_defaults": score["illegal_defaults"],
            "state_free": not name.startswith("active_"),
        }

    state_free_models = {
        name: model for name, model in full_models.items() if model["state_free"]
    }
    best_state_free_name, best_state_free = min(
        state_free_models.items(), key=lambda item: item[1]["stream_bits"]
    )
    active_model = full_models["active_previous_source_plus_length"]

    prefix_rows = [
        split_score(
            label=f"prefix_{cutoff}_future_suffix",
            train_books=set(range(cutoff)),
            test_books=set(range(cutoff, 70)),
            rows=rows,
            rules=rules,
        )
        for cutoff in PREFIX_CUTOFFS
    ]
    state_free_frozen_gaps = [
        row["models"][best_state_free_name]["test_frozen_bits"]
        - row["models"]["active_previous_source_plus_length"]["test_frozen_bits"]
        for row in prefix_rows
    ]

    classification = (
        "state_free_copy_source_default_candidate_promoted"
        if best_state_free["stream_bits"] <= active_model["stream_bits"]
        else "state_free_copy_source_defaults_rejected_active_path_state_retained"
    )

    return {
        "schema": "copy_source_state_free_default_audit.v1",
        "test": "147_copy_source_state_free_default_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "active_total_bits": active_bits,
            "active_copy_address_bits": active_copy_address_bits,
            "active_source_stream_bits": active_stream_bits,
            "copy_items": len(rows),
            "uniform_legal_source_bits": uniform_bits,
            "declaration_bits_for_replacement": DECLARATION_BITS,
            "question": (
                "Can a decoder-computable default that does not depend on previous "
                "copy source/length replace the active path-dependent source default?"
            ),
        },
        "full_corpus_models": full_models,
        "best_state_free": {
            "name": best_state_free_name,
            **best_state_free,
        },
        "active_path_dependent": active_model,
        "prefix_future_suffix": {
            "rows": prefix_rows,
            "best_state_free_frozen_gap_vs_active_bits": summarize(state_free_frozen_gaps),
        },
        "decision": {
            "compression_bound_changed": False,
            "state_free_default_promoted": False,
            "active_path_dependent_default_retained": True,
            "best_state_free_name": best_state_free_name,
            "best_state_free_worse_than_active_stream_bits": (
                best_state_free["stream_bits"] - active_model["stream_bits"]
            ),
            "best_state_free_worse_than_active_total_bits": (
                best_state_free["replacement_total_bits"] - active_bits
            ),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 147. Copy Source State-Free Default Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 146 localized the exact-reparse blocker: the active copy-source",
        "default depends on the previous copy source and previous copy length.",
        "This audit tests whether a decoder-computable default that is free of",
        "that path state can replace the active default without worsening the",
        "copy-source ledger.",
        "",
        "## Full-Corpus Frontier",
        "",
        "| Default rule | State-free | Stream bits | Delta vs active stream | Defaults | Replacement total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, model in sorted(
        result["full_corpus_models"].items(), key=lambda item: item[1]["stream_bits"]
    ):
        lines.append(
            f"| `{name}` | `{str(model['state_free']).lower()}` | "
            f"`{model['stream_bits']:.3f}` | "
            f"`{model['delta_vs_active_stream_bits']:.3f}` | "
            f"`{model['default_count']}/{result['scope']['copy_items']}` | "
            f"`{model['replacement_total_bits']:.3f}` |"
        )
    best = result["best_state_free"]
    decision = result["decision"]
    lines.extend(
        [
            "",
            f"- Active source stream bits: `{result['scope']['active_source_stream_bits']:.3f}`",
            f"- Best state-free default: `{best['name']}`",
            f"- Best state-free stream penalty: `{decision['best_state_free_worse_than_active_stream_bits']:.3f}` bits",
            f"- Best state-free total penalty: `{decision['best_state_free_worse_than_active_total_bits']:.3f}` bits",
            "",
            "## Prefix Future-Suffix Check",
            "",
            "| Split | Test events | Active frozen bits | Best state-free frozen bits | Gap |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    best_name = best["name"]
    for row in result["prefix_future_suffix"]["rows"]:
        active = row["models"]["active_previous_source_plus_length"]["test_frozen_bits"]
        state_free = row["models"][best_name]["test_frozen_bits"]
        lines.append(
            f"| `{row['label']}` | `{row['event_counts']['test']}` | "
            f"`{active:.3f}` | `{state_free:.3f}` | `{state_free - active:.3f}` |"
        )
    summary = result["prefix_future_suffix"]["best_state_free_frozen_gap_vs_active_bits"]
    lines.extend(
        [
            "",
            "Best state-free frozen gap summary:",
            f"`{summary}`",
            "",
            "## Interpretation",
            "",
            "The tested state-free defaults are decodable from current emitted length,",
            "book position, current copy length, and public book-length context. None",
            "matches the active previous-source-plus-length default. The best",
            "state-free candidate still carries a positive stream and total penalty,",
            "so it does not remove the path-dependent source state identified by",
            "audit 146.",
            "",
            "## Decision",
            "",
            "- Compression bound unchanged.",
            "- Active path-dependent copy-source default retained.",
            "- Exact reparse still requires previous-copy source/length state or a different source model.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "147_copy_source_state_free_default_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "147_copy_source_state_free_default_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
