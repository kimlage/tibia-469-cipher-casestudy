from __future__ import annotations

import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
TYPE_SEQUENCE_GATE = (
    ROOT
    / "analysis"
    / "operation_type_sequence_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_type_sequence_generation_gate.json"
)

OUT_STEM = "01_operation_type_weighted_length_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Row = dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def reconstruct() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_type_weighted_length", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[Row]:
    rows = []
    for book in sorted(by_book):
        types = ["L" if str(op["type"]) == "literal" else "C" for op in by_book[book]]
        lengths = [int(op["length"]) for op in by_book[book]]
        rows.append(
            {
                "book": book,
                "book_length": sum(lengths),
                "op_count": len(lengths),
                "types": types,
                "type_sequence": "".join(types),
                "lengths": lengths,
            }
        )
    return rows


def bucket_ratio(index: int, total: int) -> str:
    if total <= 1:
        return "only"
    ratio = index / (total - 1)
    if ratio < 0.25:
        return "q1"
    if ratio < 0.50:
        return "q2"
    if ratio < 0.75:
        return "q3"
    return "q4"


def positive_round_to_sum(raw: list[float], total: int) -> list[int]:
    if not raw:
        return []
    if total < len(raw):
        # The canonical skeleton never has fewer digits than operations, but keep
        # the helper total-safe for controls.
        return [1] * total + [0] * (len(raw) - total)
    floor_values = [max(1, int(value)) for value in raw]
    current = sum(floor_values)
    if current > total:
        order = sorted(range(len(raw)), key=lambda i: (raw[i] - int(raw[i]), raw[i]))
        for index in order:
            if current == total:
                break
            removable = floor_values[index] - 1
            if removable <= 0:
                continue
            delta = min(removable, current - total)
            floor_values[index] -= delta
            current -= delta
        return floor_values
    remainders = [raw[i] - int(raw[i]) for i in range(len(raw))]
    order = sorted(range(len(raw)), key=lambda i: (-remainders[i], i))
    index = 0
    while current < total:
        floor_values[order[index % len(order)]] += 1
        current += 1
        index += 1
    return floor_values


def allocate_by_weights(types: list[str], book_length: int, weights: list[float]) -> list[int]:
    weights = [max(0.001, weight) for weight in weights]
    total_weight = sum(weights)
    raw = [book_length * weight / total_weight for weight in weights]
    out = positive_round_to_sum(raw, book_length)
    if len(out) != len(types) or sum(out) != book_length or min(out) <= 0:
        raise RuntimeError("bad allocation")
    return out


def train_average_lengths(rows: list[Row], key_fn: Callable[[Row, int], str], default: float) -> dict[str, float]:
    groups: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        for index, length in enumerate(row["lengths"]):
            groups[key_fn(row, index)].append(int(length))
    return {key: mean(values) if values else default for key, values in groups.items()}


def train_models(rows: list[Row]) -> list[dict[str, Any]]:
    all_lengths = [int(length) for row in rows for length in row["lengths"]]
    default = mean(all_lengths)
    median_default = median(all_lengths)
    models: list[dict[str, Any]] = []

    def add_weight_model(name: str, key_fn: Callable[[Row, int], str], parameters: dict[str, Any]) -> None:
        weights = train_average_lengths(rows, key_fn, default)
        models.append(
            {
                "name": name,
                "kind": "weighted",
                "key_fn": key_fn,
                "weights": weights,
                "fallback": default,
                "payload_records": len(weights),
                "parameters": parameters | {"weight_count": len(weights)},
            }
        )

    models.append(
        {
            "name": "uniform_all_ops",
            "kind": "fixed",
            "weight_fn": lambda row, index: 1.0,
            "payload_records": 1,
            "parameters": {},
        }
    )
    models.append(
        {
            "name": "literal_copy_constants",
            "kind": "fixed",
            "weight_fn": lambda row, index: 3.0 if row["types"][index] == "L" else 1.0,
            "payload_records": 2,
            "parameters": {"literal_weight": 3.0, "copy_weight": 1.0},
        }
    )
    models.append(
        {
            "name": "copy_literal_constants",
            "kind": "fixed",
            "weight_fn": lambda row, index: 1.0 if row["types"][index] == "L" else 3.0,
            "payload_records": 2,
            "parameters": {"literal_weight": 1.0, "copy_weight": 3.0},
        }
    )
    models.append(
        {
            "name": "bookend_heavy",
            "kind": "fixed",
            "weight_fn": lambda row, index: 3.0
            if index in {0, int(row["op_count"]) - 1}
            else 1.0,
            "payload_records": 2,
            "parameters": {"edge_weight": 3.0, "inner_weight": 1.0},
        }
    )
    models.append(
        {
            "name": "median_all_ops",
            "kind": "fixed",
            "weight_fn": lambda row, index, value=median_default: float(value),
            "payload_records": 1,
            "parameters": {"median": median_default},
        }
    )
    add_weight_model("learned_by_type", lambda row, index: row["types"][index], {})
    add_weight_model(
        "learned_by_type_x_position_quartile",
        lambda row, index: f"{row['types'][index]}|{bucket_ratio(index, int(row['op_count']))}",
        {},
    )
    add_weight_model(
        "learned_by_op_index",
        lambda row, index: f"op={index}",
        {},
    )
    add_weight_model(
        "learned_by_type_x_op_index",
        lambda row, index: f"{row['types'][index]}|op={index}",
        {},
    )
    add_weight_model(
        "learned_by_shape_x_type_x_position",
        lambda row, index: (
            f"ops={row['op_count']}|lit={row['types'].count('L')}|"
            f"{row['types'][index]}|{bucket_ratio(index, int(row['op_count']))}"
        ),
        {},
    )
    return models


def predict(model: dict[str, Any], row: Row) -> list[int]:
    if model["kind"] == "fixed":
        weights = [float(model["weight_fn"](row, index)) for index in range(int(row["op_count"]))]
    else:
        weights = [
            float(model["weights"].get(model["key_fn"](row, index), model["fallback"]))
            for index in range(int(row["op_count"]))
        ]
    return allocate_by_weights(row["types"], int(row["book_length"]), weights)


def score_model(rows: list[Row], model: dict[str, Any]) -> dict[str, Any]:
    predictions = []
    exact_books = 0
    row_hits = 0
    total_ops = 0
    absolute_error = 0
    correction_payload_records = 0
    for row in rows:
        predicted = predict(model, row)
        truth = [int(value) for value in row["lengths"]]
        exact = predicted == truth
        hits = sum(1 for a, b in zip(predicted, truth) if a == b)
        error = sum(abs(a - b) for a, b in zip(predicted, truth))
        exact_books += int(exact)
        row_hits += hits
        total_ops += len(truth)
        absolute_error += error
        if not exact:
            correction_payload_records += len(truth)
        predictions.append(
            {
                "book": int(row["book"]),
                "type_sequence": row["type_sequence"],
                "truth": truth,
                "predicted": predicted,
                "exact": exact,
                "row_hits": hits,
                "absolute_error": error,
            }
        )
    paid_records = int(model["payload_records"]) + correction_payload_records
    return {
        "model": model["name"],
        "kind": model["kind"],
        "payload_records": int(model["payload_records"]),
        "book_count": len(rows),
        "total_ops": total_ops,
        "exact_books": exact_books,
        "row_hits": row_hits,
        "row_errors": total_ops - row_hits,
        "absolute_error": absolute_error,
        "correction_payload_records": correction_payload_records,
        "paid_records": paid_records,
        "parameters": model["parameters"],
        "predictions": predictions,
    }


def choose_best(scored: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            int(item["row_hits"]),
            -int(item["absolute_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
    )


def evaluate(rows: list[Row]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    models = train_models(rows)
    scored = [score_model(rows, model) for model in models]
    return scored, choose_best(scored)


def prequential(rows: list[Row]) -> list[dict[str, Any]]:
    cells = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        models = train_models(train)
        train_scored = [score_model(train, model) for model in models]
        best_train = choose_best(train_scored)
        selected = next(model for model in models if model["name"] == best_train["model"])
        test_score = score_model(test, selected)
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_model": selected["name"],
                "train_exact_books": int(best_train["exact_books"]),
                "train_row_hits": int(best_train["row_hits"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_row_hits": int(test_score["row_hits"]),
                "test_total_ops": int(test_score["total_ops"]),
                "test_absolute_error": int(test_score["absolute_error"]),
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def compact_model(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "predictions"}


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# Operation Type-Weighted Length Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether operation lengths can be generated by simple weighted",
        "allocation once book length and literal/copy sequence are granted.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Models tested: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best row hits: `{s['best_row_hits']}/{s['operation_count']}`.",
        f"- Best absolute error: `{s['best_absolute_error']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact length fields `{s['exact_length_field_records']}`.",
        f"- Paid-record delta vs exact length fields: `{s['paid_record_delta_vs_exact_length_fields']:+d}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Models",
        "",
        "| Model | Kind | Exact books | Row hits | Abs error | Paid records | Payload |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in data["top_models"]:
        lines.append(
            "| "
            f"`{item['model']}` | "
            f"`{item['kind']}` | "
            f"`{item['exact_books']}/{item['book_count']}` | "
            f"`{item['row_hits']}/{item['total_ops']}` | "
            f"`{item['absolute_error']}` | "
            f"`{item['paid_records']}` | "
            f"`{item['payload_records']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected model | Test exact | Test row hits | Test abs error | Cover all |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for cell in data["prequential"]:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_model']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_row_hits']}/{cell['test_total_ops']}` | "
            f"`{cell['test_absolute_error']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes type-weighted length generator: `{s['promotes_type_weighted_length_generator']}`.",
            f"- Audit-only paid-record reduction: `{s['audit_only_paid_record_reduction']}`.",
            "- Length sequence remains retained unless a later joint parser derives it with source/copy availability.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    type_seq = load_json(TYPE_SEQUENCE_GATE)
    assert_boundary("operation_type_sequence_generation_gate", type_seq)
    rows = make_rows(reconstruct())
    scored, best = evaluate(rows)
    cells = prequential(rows)
    total_ops = sum(int(row["op_count"]) for row in rows)
    promotes = (
        int(best["exact_books"]) == len(rows)
        and int(best["paid_records"]) < total_ops
        and all(cell["covers_all_test_books"] for cell in cells)
    )
    classification = (
        "operation_type_weighted_length_generator_promoted"
        if promotes
        else "operation_type_weighted_length_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            int(item["row_hits"]),
            -int(item["absolute_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
        reverse=True,
    )[:10]
    summary = {
        "book_count": len(rows),
        "operation_count": total_ops,
        "model_count": len(scored),
        "best_model": best["model"],
        "best_kind": best["kind"],
        "best_exact_books": int(best["exact_books"]),
        "best_row_hits": int(best["row_hits"]),
        "best_row_errors": int(best["row_errors"]),
        "best_absolute_error": int(best["absolute_error"]),
        "best_paid_records": int(best["paid_records"]),
        "best_payload_records": int(best["payload_records"]),
        "exact_length_field_records": total_ops,
        "paid_record_delta_vs_exact_length_fields": int(best["paid_records"]) - total_ops,
        "audit_only_paid_record_reduction": int(best["paid_records"]) < total_ops,
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(1 for cell in cells if cell["covers_all_test_books"]),
        "promotes_type_weighted_length_generator": promotes,
        "interpretation": (
            "Simple source-free weighted allocation rules do not generate the "
            "operation length sequence under full-fit and prefix holdout."
        ),
    }
    data = {
        "schema": "operation_type_weighted_length_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_type_sequence_generation_gate": rel(TYPE_SEQUENCE_GATE),
        },
        "parameters": {"prefix_cutoffs": PREFIX_CUTOFFS},
        "summary": summary,
        "top_models": [compact_model(row) for row in top],
        "best_model_predictions": best["predictions"],
        "prequential": cells,
        "decision": {
            "operation_length_status": "atlas_retained_after_type_weighted_length_gate",
            "operation_type_sequence_status": "retained_after_simple_generation_gate",
            "row0_origin_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged_8154_676268",
            "translation_or_plaintext_status": "NONE",
        },
    }
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
