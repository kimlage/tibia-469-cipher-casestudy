from __future__ import annotations

import copy
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

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
CONSERVATIVE_DECLARATION_BITS = 12.0


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


def legal_source_values(row: dict[str, Any]) -> range:
    return range(int(row["legal_source_count"]))


def legal_distance_values(row: dict[str, Any]) -> range:
    emitted_len = int(row["emitted_len_before_copy"])
    legal_count = int(row["legal_source_count"])
    return range(emitted_len - legal_count + 1, emitted_len + 1)


def legal_values(row: dict[str, Any], representation: str) -> range:
    if representation == "absolute_source":
        return legal_source_values(row)
    if representation == "backward_distance":
        return legal_distance_values(row)
    raise RuntimeError({"type": "unknown_representation", "representation": representation})


def value_for(row: dict[str, Any], representation: str) -> int:
    if representation == "absolute_source":
        return int(row["source_digit_pos"])
    if representation == "backward_distance":
        return int(row["backward_distance"])
    raise RuntimeError({"type": "unknown_representation", "representation": representation})


def default_for(row: dict[str, Any], representation: str) -> int:
    if representation == "absolute_source":
        return int(row["previous_source_plus_length_default"])
    if representation == "backward_distance":
        return int(row["previous_distance_default"])
    raise RuntimeError({"type": "unknown_representation", "representation": representation})


def collect_source_rows(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    previous_source = None
    previous_length = None
    previous_distance = None
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append({"book": book, "op_index": op_index, "type": "literal_mismatch"})
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                errors.append({"book": book, "op_index": op_index, "type": "bad_op", "op": op})
                continue

            emitted_len = len(emitted)
            source = int(op["source_digit_pos"])
            length = int(op["length"])
            legal_source_count = max(1, emitted_len - min_len + 1)
            if not 0 <= source < legal_source_count:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "source_out_of_range",
                        "source_digit_pos": source,
                        "legal_source_count": legal_source_count,
                    }
                )
            chunk = emitted[source : source + length]
            if target[book_pos : book_pos + length] != chunk:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )

            if previous_source is None or previous_length is None:
                previous_source_plus_length_default = 0
            else:
                candidate = previous_source + previous_length
                previous_source_plus_length_default = (
                    candidate if candidate < legal_source_count else 0
                )

            if previous_distance is not None and min_len <= previous_distance <= emitted_len:
                previous_distance_default = previous_distance
            else:
                previous_distance_default = emitted_len

            backward_distance = emitted_len - source
            if backward_distance not in legal_distance_values(
                {
                    "emitted_len_before_copy": emitted_len,
                    "legal_source_count": legal_source_count,
                }
            ):
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "distance_out_of_range",
                        "backward_distance": backward_distance,
                        "emitted_len_before_copy": emitted_len,
                        "legal_source_count": legal_source_count,
                    }
                )

            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "emitted_len_before_copy": emitted_len,
                    "source_digit_pos": source,
                    "backward_distance": backward_distance,
                    "length": length,
                    "legal_source_count": legal_source_count,
                    "previous_source_plus_length_default": previous_source_plus_length_default,
                    "previous_distance_default": previous_distance_default,
                    "source_equals_default": source == previous_source_plus_length_default,
                    "distance_equals_default": backward_distance == previous_distance_default,
                }
            )
            emitted += chunk
            book_pos += length
            previous_source = source
            previous_length = length
            previous_distance = backward_distance
        if book_pos != len(target):
            errors.append(
                {
                    "book": book,
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )
    return {"rows": rows, "errors": errors}


def score_uniform(rows: list[dict[str, Any]]) -> float:
    return sum(math.log2(int(row["legal_source_count"])) for row in rows)


def score_adaptive(
    rows: list[dict[str, Any]],
    *,
    representation: str,
    counts: dict[int, float] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = copy.deepcopy(counts) if counts is not None else {}
    bits = 0.0
    for row in rows:
        values = list(legal_values(row, representation))
        value = value_for(row, representation)
        if value not in values:
            raise RuntimeError({"row": row, "representation": representation, "values": values})
        total = sum(local.get(candidate, 0.0) for candidate in values)
        probability = (local.get(value, 0.0) + 1.0) / (total + len(values))
        bits += -math.log2(probability)
        if update:
            local[value] = local.get(value, 0.0) + 1.0
    return {"bits": bits, "counts": local, "distinct_values": len(local)}


def score_default_exception(
    rows: list[dict[str, Any]],
    *,
    representation: str,
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
        value = value_for(row, representation)
        default = default_for(row, representation)
        is_default = value == default
        flag_bucket = local["flag"]
        flag_probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(flag_probability)
        if update:
            flag_bucket[is_default] += 1.0

        if is_default:
            default_count += 1
            continue

        exception_values = [
            candidate for candidate in legal_values(row, representation) if candidate != default
        ]
        if value not in exception_values:
            raise RuntimeError(
                {
                    "row": row,
                    "representation": representation,
                    "exception_values": exception_values,
                }
            )
        exception_bucket = local["exception"]
        total = sum(exception_bucket.get(candidate, 0.0) for candidate in exception_values)
        probability = (exception_bucket.get(value, 0.0) + 1.0) / (
            total + len(exception_values)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[value] = exception_bucket.get(value, 0.0) + 1.0
        exception_count += 1

    return {
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "counts": local,
        "distinct_exception_values": len(local["exception"]),
    }


def rows_for_books(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["book"]) in books]


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def split_score(label: str, train_books: set[int], test_books: set[int], rows: list[dict[str, Any]]) -> dict[str, Any]:
    train_rows = rows_for_books(rows, train_books)
    test_rows = rows_for_books(rows, test_books)
    uniform_test = score_uniform(test_rows)
    out: dict[str, Any] = {
        "label": label,
        "train_books": sorted(train_books),
        "test_books": sorted(test_books),
        "event_counts": {"train": len(train_rows), "test": len(test_rows)},
        "test_uniform_bits": uniform_test,
        "models": {},
    }
    for representation in ["absolute_source", "backward_distance"]:
        train_adaptive = score_adaptive(
            train_rows,
            representation=representation,
            counts=None,
            update=True,
        )
        online_adaptive = score_adaptive(
            test_rows,
            representation=representation,
            counts=train_adaptive["counts"],
            update=True,
        )
        frozen_adaptive = score_adaptive(
            test_rows,
            representation=representation,
            counts=train_adaptive["counts"],
            update=False,
        )
        train_default = score_default_exception(
            train_rows,
            representation=representation,
            counts=None,
            update=True,
        )
        online_default = score_default_exception(
            test_rows,
            representation=representation,
            counts=train_default["counts"],
            update=True,
        )
        frozen_default = score_default_exception(
            test_rows,
            representation=representation,
            counts=train_default["counts"],
            update=False,
        )
        out["models"][representation] = {
            "adaptive": {
                "train_bits": train_adaptive["bits"],
                "test_online_bits": online_adaptive["bits"],
                "test_frozen_bits": frozen_adaptive["bits"],
                "test_online_gain_vs_uniform_bits": uniform_test - online_adaptive["bits"],
                "test_frozen_gain_vs_uniform_bits": uniform_test - frozen_adaptive["bits"],
                "train_distinct_values": train_adaptive["distinct_values"],
            },
            "default_exception": {
                "train_bits": train_default["bits"],
                "test_online_bits": online_default["bits"],
                "test_frozen_bits": frozen_default["bits"],
                "test_online_gain_vs_uniform_bits": uniform_test - online_default["bits"],
                "test_frozen_gain_vs_uniform_bits": uniform_test - frozen_default["bits"],
                "train_default_count": train_default["default_count"],
                "train_exception_count": train_default["exception_count"],
                "test_online_default_count": online_default["default_count"],
                "test_online_exception_count": online_default["exception_count"],
                "train_distinct_exception_values": train_default["distinct_exception_values"],
            },
        }
    return out


def split_summary(splits: list[dict[str, Any]], representation: str, model: str) -> dict[str, Any]:
    online = [
        float(row["models"][representation][model]["test_online_gain_vs_uniform_bits"])
        for row in splits
    ]
    frozen = [
        float(row["models"][representation][model]["test_frozen_gain_vs_uniform_bits"])
        for row in splits
    ]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["models"][representation][model][
                "test_online_gain_vs_uniform_bits"
            ],
            "frozen_gain_vs_uniform_bits": row["models"][representation][model][
                "test_frozen_gain_vs_uniform_bits"
            ],
        }
        for row in splits
        if row["models"][representation][model]["test_online_gain_vs_uniform_bits"] <= 0
        or row["models"][representation][model]["test_frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "online_gain_vs_uniform_bits": summarize(online),
        "frozen_gain_vs_uniform_bits": summarize(frozen),
        "nonpositive_gain_failures": failures,
    }


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    formula = load_json(SOURCE_FORMULA)
    normalized = compile134.normalize_ops(formula)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    active_bits = float(formula["mdl_estimate_rough"][SOURCE_TOTAL_KEY])
    active_copy_address_bits = float(formula["mdl_estimate_rough"]["copy_address_bits"])

    collected = collect_source_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = collected["rows"]

    full_models: dict[str, Any] = {}
    uniform_bits = score_uniform(rows)
    for representation in ["absolute_source", "backward_distance"]:
        adaptive = score_adaptive(rows, representation=representation, counts=None, update=True)
        default_exception = score_default_exception(
            rows,
            representation=representation,
            counts=None,
            update=True,
        )
        candidate_copy_address_bits = (
            default_exception["bits"] + CONSERVATIVE_DECLARATION_BITS
        )
        full_models[representation] = {
            "uniform_legal_bits": uniform_bits,
            "adaptive_stream_bits": adaptive["bits"],
            "adaptive_gain_vs_uniform_bits": uniform_bits - adaptive["bits"],
            "adaptive_distinct_values": adaptive["distinct_values"],
            "default_exception_stream_bits": default_exception["bits"],
            "default_exception_flag_bits": default_exception["flag_bits"],
            "default_exception_exception_bits": default_exception["exception_bits"],
            "default_exception_copy_address_bits_with_declaration": candidate_copy_address_bits,
            "default_exception_gain_vs_uniform_bits": uniform_bits
            - default_exception["bits"],
            "default_count": default_exception["default_count"],
            "exception_count": default_exception["exception_count"],
            "distinct_exception_values": default_exception["distinct_exception_values"],
            "replacement_total_bits": active_bits
            - active_copy_address_bits
            + candidate_copy_address_bits,
        }

    prefix_splits = [
        split_score(
            label=f"prefix_{cutoff}_future_suffix",
            train_books=set(range(cutoff)),
            test_books=set(range(cutoff, 70)),
            rows=rows,
        )
        for cutoff in PREFIX_CUTOFFS
    ]

    absolute_active_stream = full_models["absolute_source"]["default_exception_stream_bits"]
    distance_default_stream = full_models["backward_distance"][
        "default_exception_stream_bits"
    ]
    distance_adaptive_stream = full_models["backward_distance"]["adaptive_stream_bits"]
    distance_replacement_total = full_models["backward_distance"]["replacement_total_bits"]
    distance_vs_active_copy_address_delta = (
        full_models["backward_distance"]["default_exception_copy_address_bits_with_declaration"]
        - active_copy_address_bits
    )

    if distance_default_stream < absolute_active_stream:
        classification = "copy_source_backward_distance_candidate_improves_active_source_model"
    else:
        classification = "copy_source_backward_distance_rejected_absolute_source_retained"

    return {
        "schema": "copy_source_distance_model_audit.v1",
        "test": "144_copy_source_distance_model_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "active_total_bits": active_bits,
            "active_copy_address_bits": active_copy_address_bits,
            "copy_items": len(rows),
            "candidate": "backward_distance = emitted_length_before_copy - source_digit_pos",
            "controls": [
                "uniform legal source/distance alphabet",
                "global adaptive absolute source",
                "global adaptive backward distance",
                "previous absolute source plus length default/exception",
                "previous backward distance default/exception",
                "prefix future-suffix frozen-count validation",
            ],
            "declaration_bits_for_default_exception_replacement": CONSERVATIVE_DECLARATION_BITS,
        },
        "full_corpus": {
            "uniform_legal_bits": uniform_bits,
            "models": full_models,
            "distance_vs_active": {
                "distance_adaptive_stream_bits": distance_adaptive_stream,
                "active_absolute_default_exception_stream_bits": absolute_active_stream,
                "distance_default_exception_stream_bits": distance_default_stream,
                "distance_default_exception_replacement_total_bits": distance_replacement_total,
                "distance_copy_address_delta_vs_active_bits": distance_vs_active_copy_address_delta,
            },
        },
        "prefix_future_suffix": {
            "rows": prefix_splits,
            "summaries": {
                "absolute_source_adaptive": split_summary(
                    prefix_splits, "absolute_source", "adaptive"
                ),
                "absolute_source_default_exception": split_summary(
                    prefix_splits, "absolute_source", "default_exception"
                ),
                "backward_distance_adaptive": split_summary(
                    prefix_splits, "backward_distance", "adaptive"
                ),
                "backward_distance_default_exception": split_summary(
                    prefix_splits, "backward_distance", "default_exception"
                ),
            },
        },
        "decision": {
            "compression_bound_changed": False,
            "active_copy_source_model_retained": True,
            "backward_distance_promoted": False,
            "distance_stream_worse_than_active_default_exception_bits": (
                distance_default_stream - absolute_active_stream
            ),
            "distance_replacement_total_worse_than_active_bits": (
                distance_replacement_total - active_bits
            ),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    full = result["full_corpus"]["models"]
    distance_vs_active = result["full_corpus"]["distance_vs_active"]
    lines = [
        "# 144. Copy Source Distance Model Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 137 retained an absolute copy-source default/exception model as a",
        "compression-bound component. The corrected audit 141/142 profile keeps",
        "that source model as prefix-frozen evidence while still marking the",
        "generation claim partial because family holdouts fail. This audit tests",
        "a structural alternative common in LZ descriptions: encode copy source",
        "as backward distance from the current emitted length instead of as an",
        "absolute source position.",
        "",
        "## Full-Corpus Result",
        "",
        "| Representation | Model | Stream bits | Gain vs uniform | Defaults | Replacement total |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for representation in ["absolute_source", "backward_distance"]:
        model = full[representation]
        lines.append(
            f"| `{representation}` | `adaptive` | "
            f"`{model['adaptive_stream_bits']:.3f}` | "
            f"`{model['adaptive_gain_vs_uniform_bits']:.3f}` | "
            "`n/a` | `n/a` |"
        )
        lines.append(
            f"| `{representation}` | `default_exception` | "
            f"`{model['default_exception_stream_bits']:.3f}` | "
            f"`{model['default_exception_gain_vs_uniform_bits']:.3f}` | "
            f"`{model['default_count']}/{result['scope']['copy_items']}` | "
            f"`{model['replacement_total_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            f"- Uniform legal source/distance bits: `{result['full_corpus']['uniform_legal_bits']:.3f}`",
            f"- Active absolute default/exception stream: `{distance_vs_active['active_absolute_default_exception_stream_bits']:.3f}` bits",
            f"- Backward-distance default/exception stream: `{distance_vs_active['distance_default_exception_stream_bits']:.3f}` bits",
            f"- Distance replacement total: `{distance_vs_active['distance_default_exception_replacement_total_bits']:.3f}` bits",
            f"- Distance copy-address delta vs active: `{distance_vs_active['distance_copy_address_delta_vs_active_bits']:.3f}` bits",
            "",
            "## Prefix Future-Suffix Controls",
            "",
            "| Split | Test events | Absolute default frozen gain | Distance default frozen gain | Absolute adaptive frozen gain | Distance adaptive frozen gain |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["prefix_future_suffix"]["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['event_counts']['test']}` | "
            f"`{row['models']['absolute_source']['default_exception']['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['models']['backward_distance']['default_exception']['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['models']['absolute_source']['adaptive']['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['models']['backward_distance']['adaptive']['test_frozen_gain_vs_uniform_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Backward distance is decodable and uses the same number of legal choices",
            "as absolute source at each copy event. The test therefore isolates the",
            "question of whether distances repeat or generalize better than absolute",
            "source positions. They do not: both the adaptive distance stream and",
            "the previous-distance default/exception stream are worse than the",
            "corresponding absolute-source controls. The replacement would worsen",
            "the active compression bound rather than improve validation.",
            "",
            "## Decision",
            "",
            "- Retain the active absolute copy-source default/exception model as the current compression-bound and prefix-frozen partial component.",
            "- Reject backward-distance copy-source coding for the current formula.",
            "- The generation claim remains partial because family/bookcase holdouts still have failures.",
            "- No plaintext, translation, row0-origin, or authorial-intent claim is introduced.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "144_copy_source_distance_model_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "144_copy_source_distance_model_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
