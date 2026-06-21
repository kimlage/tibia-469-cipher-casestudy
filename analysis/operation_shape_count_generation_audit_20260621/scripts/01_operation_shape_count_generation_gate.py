from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
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
OP_COUNT_GATE = (
    ROOT
    / "analysis"
    / "operation_count_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_count_generation_gate.json"
)

OUT_STEM = "01_operation_shape_count_generation_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 1000
RANDOM_SEED = 4692026062104


Row = dict[str, Any]
Shape = tuple[int, int]


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
    module = load_module("source_free_skeleton_for_shape_count", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[Row]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        types = [str(op["type"]) for op in by_book[book]]
        literal_count = sum(1 for op_type in types if op_type == "literal")
        copy_count = sum(1 for op_type in types if op_type == "copy")
        rows.append(
            {
                "book": book,
                "book_length": sum(lengths),
                "op_count": len(lengths),
                "literal_count": literal_count,
                "copy_count": copy_count,
                "shape": (len(lengths), literal_count),
            }
        )
    return rows


def bucket(value: int) -> str:
    if value <= 80:
        return "le80"
    if value <= 120:
        return "le120"
    if value <= 160:
        return "le160"
    if value <= 220:
        return "le220"
    return "gt220"


def shape_to_text(shape: Shape) -> str:
    return f"ops={shape[0]}|lit={shape[1]}|copy={shape[0] - shape[1]}"


def mode(values: list[Shape]) -> Shape:
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value))


def shape_error(predicted: Shape, truth: Shape) -> int:
    return abs(predicted[0] - truth[0]) + abs(predicted[1] - truth[1])


def context_model(rows: list[Row], key_fn: Callable[[Row], str]) -> dict[str, Shape]:
    groups: dict[str, list[Shape]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(tuple(row["shape"]))
    return {key: mode(values) for key, values in groups.items()}


def clamp_shape(op_count: int, literal_count: int) -> Shape:
    op_count = max(1, int(op_count))
    literal_count = max(0, min(int(literal_count), op_count))
    return op_count, literal_count


def train_models(rows: list[Row]) -> list[dict[str, Any]]:
    shapes = [tuple(row["shape"]) for row in rows]
    fallback = mode(shapes)
    models: list[dict[str, Any]] = []

    def add(name: str, predict: Callable[[Row], Shape], parameters: dict[str, Any], payload_records: int) -> None:
        models.append(
            {
                "name": name,
                "predict": predict,
                "parameters": parameters,
                "payload_records": payload_records,
            }
        )

    add("constant_shape_mode", lambda _row, v=fallback: v, {"value": shape_to_text(fallback)}, 1)

    # Length-derived deterministic families. They are deliberately simple and
    # source-free; corrections pay for misses.
    for op_divisor in range(8, 81):
        for lit_divisor in range(20, 181, 5):
            add(
                f"length_div_ops_{op_divisor}_lit_{lit_divisor}",
                lambda row, od=op_divisor, ld=lit_divisor: clamp_shape(
                    round(int(row["book_length"]) / od),
                    round(int(row["book_length"]) / ld),
                ),
                {"op_divisor": op_divisor, "literal_divisor": lit_divisor},
                2,
            )

    context_specs: list[tuple[str, Callable[[Row], str]]] = [
        ("book_mod10", lambda row: str(int(row["book"]) % 10)),
        ("book_mod5", lambda row: str(int(row["book"]) % 5)),
        ("book_decade", lambda row: str(int(row["book"]) // 10)),
        ("book_length_bucket", lambda row: bucket(int(row["book_length"]))),
        (
            "book_mod10_x_length_bucket",
            lambda row: f"{int(row['book']) % 10}|{bucket(int(row['book_length']))}",
        ),
        (
            "book_mod5_x_length_bucket",
            lambda row: f"{int(row['book']) % 5}|{bucket(int(row['book_length']))}",
        ),
    ]
    for name, key_fn in context_specs:
        mapping = context_model(rows, key_fn)
        add(
            f"context_{name}",
            lambda row, mapping=mapping, key_fn=key_fn, fallback=fallback: mapping.get(
                key_fn(row),
                fallback,
            ),
            {
                "context_count": len(mapping),
                "fallback": shape_to_text(fallback),
                "mapping": {key: shape_to_text(value) for key, value in mapping.items()},
            },
            1 + len(mapping),
        )
    return models


def score_model(rows: list[Row], model: dict[str, Any]) -> dict[str, Any]:
    predictions = []
    exact = 0
    total_error = 0
    op_exact = 0
    literal_exact = 0
    for row in rows:
        predicted = tuple(model["predict"](row))
        truth = tuple(row["shape"])
        error = shape_error(predicted, truth)
        exact += int(predicted == truth)
        total_error += error
        op_exact += int(predicted[0] == truth[0])
        literal_exact += int(predicted[1] == truth[1])
        predictions.append(
            {
                "book": int(row["book"]),
                "book_length": int(row["book_length"]),
                "truth": shape_to_text(truth),
                "predicted": shape_to_text(predicted),
                "error": error,
            }
        )
    correction_records = len(rows) - exact
    paid_records = int(model["payload_records"]) + correction_records
    return {
        "model": model["name"],
        "payload_records": int(model["payload_records"]),
        "book_count": len(rows),
        "exact_books": exact,
        "op_count_exact_books": op_exact,
        "literal_count_exact_books": literal_exact,
        "total_shape_error": total_error,
        "mean_shape_error": total_error / len(rows) if rows else 0.0,
        "correction_records": correction_records,
        "paid_records": paid_records,
        "parameters": model["parameters"],
        "predictions": predictions,
    }


def choose_best(scored: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            -int(item["total_shape_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
    )


def random_control(rows: list[Row], shapes: list[Shape], *, trials: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    exact_values = []
    error_values = []
    for _ in range(trials):
        exact = 0
        total_error = 0
        for row in rows:
            predicted = rng.choice(shapes)
            truth = tuple(row["shape"])
            exact += int(predicted == truth)
            total_error += shape_error(predicted, truth)
        exact_values.append(exact)
        error_values.append(total_error)
    exact_sorted = sorted(exact_values)
    error_sorted = sorted(error_values)
    p95_index = int(0.95 * (trials - 1))
    p05_index = int(0.05 * (trials - 1))
    return {
        "trials": trials,
        "mean_exact_books": mean(exact_values),
        "p95_exact_books": exact_sorted[p95_index],
        "max_exact_books": max(exact_values),
        "mean_total_shape_error": mean(error_values),
        "p05_total_shape_error": error_sorted[p05_index],
        "min_total_shape_error": min(error_values),
    }


def evaluate(rows: list[Row]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    models = train_models(rows)
    scored = [score_model(rows, model) for model in models]
    return scored, choose_best(scored)


def prequential(rows: list[Row]) -> list[dict[str, Any]]:
    cells = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_models_list = train_models(train)
        train_scored = [score_model(train, model) for model in train_models_list]
        best_train = choose_best(train_scored)
        selected_model = next(model for model in train_models_list if model["name"] == best_train["model"])
        test_score = score_model(test, selected_model)
        control = random_control(
            test,
            [tuple(row["shape"]) for row in train],
            trials=RANDOM_TRIALS,
            seed=RANDOM_SEED + cutoff * 100003,
        )
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_model": selected_model["name"],
                "train_exact_books": int(best_train["exact_books"]),
                "train_total_shape_error": int(best_train["total_shape_error"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_total_shape_error": int(test_score["total_shape_error"]),
                "test_random_mean_exact_books": control["mean_exact_books"],
                "test_random_p95_exact_books": control["p95_exact_books"],
                "test_random_max_exact_books": control["max_exact_books"],
                "test_random_mean_total_shape_error": control["mean_total_shape_error"],
                "beats_random_p95_exact": int(test_score["exact_books"]) > control["p95_exact_books"],
                "beats_random_p05_error": int(test_score["total_shape_error"]) < control["p05_total_shape_error"],
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def compact_model(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "predictions"}


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    top = data["top_models"]
    cells = data["prequential"]
    lines = [
        "# Operation Shape Count Generation Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether each book's coarse operation shape, `(op_count, literal_count)`,",
        "can be generated from book id and book length before exact type sequence,",
        "cutpoints, or source choice.",
        "",
        "## Summary",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Operation total: `{s['operation_count']}`.",
        f"- Literal operation total: `{s['literal_operation_count']}`.",
        f"- Model candidates: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best exact shape books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best op-count exact books: `{s['best_op_count_exact_books']}/{s['book_count']}`.",
        f"- Best literal-count exact books: `{s['best_literal_count_exact_books']}/{s['book_count']}`.",
        f"- Best total shape error: `{s['best_total_shape_error']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact shape atlas `{s['exact_shape_atlas_records']}`.",
        f"- Paid-record delta vs exact atlas: `{s['paid_record_delta_vs_exact_atlas']:+d}`.",
        f"- Random mean/p95/max exact books: `{s['random_mean_exact_books']:.3f}` / `{s['random_p95_exact_books']}` / `{s['random_max_exact_books']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 exact cells: `{s['prequential_beats_random_p95_exact_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Models",
        "",
        "| Model | Exact shape | Op exact | Literal exact | Error | Paid records | Payload |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in top:
        lines.append(
            "| "
            f"`{item['model']}` | "
            f"`{item['exact_books']}/{item['book_count']}` | "
            f"`{item['op_count_exact_books']}/{item['book_count']}` | "
            f"`{item['literal_count_exact_books']}/{item['book_count']}` | "
            f"`{item['total_shape_error']}` | "
            f"`{item['paid_records']}` | "
            f"`{item['payload_records']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected model | Test exact | Test error | Random mean exact | Random p95 exact | Beats p95 | Cover all |",
            "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for cell in cells:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_model']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_total_shape_error']}` | "
            f"`{cell['test_random_mean_exact_books']:.3f}` | "
            f"`{cell['test_random_p95_exact_books']}` | "
            f"`{cell['beats_random_p95_exact']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes operation-shape-count generator: `{s['promotes_operation_shape_count_generator']}`.",
            f"- Audit-only paid-record reduction: `{s['audit_only_paid_record_reduction']}`.",
            "- Coarse operation shape remains retained unless a later joint parser derives it with cutpoints.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    op_count = load_json(OP_COUNT_GATE)
    assert_boundary("operation_count_generation_gate", op_count)
    rows = make_rows(reconstruct())
    scored, best = evaluate(rows)
    cells = prequential(rows)
    control = random_control(
        rows,
        [tuple(row["shape"]) for row in rows],
        trials=RANDOM_TRIALS,
        seed=RANDOM_SEED,
    )
    promotes = (
        int(best["exact_books"]) == len(rows)
        and int(best["paid_records"]) < len(rows)
        and all(cell["covers_all_test_books"] for cell in cells)
    )
    classification = (
        "operation_shape_count_generator_promoted"
        if promotes
        else "operation_shape_count_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            -int(item["total_shape_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
        reverse=True,
    )[:12]
    summary = {
        "book_count": len(rows),
        "operation_count": sum(int(row["op_count"]) for row in rows),
        "literal_operation_count": sum(int(row["literal_count"]) for row in rows),
        "copy_operation_count": sum(int(row["copy_count"]) for row in rows),
        "model_count": len(scored),
        "best_model": best["model"],
        "best_exact_books": int(best["exact_books"]),
        "best_op_count_exact_books": int(best["op_count_exact_books"]),
        "best_literal_count_exact_books": int(best["literal_count_exact_books"]),
        "best_total_shape_error": int(best["total_shape_error"]),
        "best_mean_shape_error": best["mean_shape_error"],
        "best_paid_records": int(best["paid_records"]),
        "best_payload_records": int(best["payload_records"]),
        "exact_shape_atlas_records": len(rows),
        "paid_record_delta_vs_exact_atlas": int(best["paid_records"]) - len(rows),
        "audit_only_paid_record_reduction": int(best["paid_records"]) < len(rows),
        "random_trials": RANDOM_TRIALS,
        "random_mean_exact_books": control["mean_exact_books"],
        "random_p95_exact_books": control["p95_exact_books"],
        "random_max_exact_books": control["max_exact_books"],
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(1 for cell in cells if cell["covers_all_test_books"]),
        "prequential_beats_random_p95_exact_cells": sum(
            1 for cell in cells if cell["beats_random_p95_exact"]
        ),
        "promotes_operation_shape_count_generator": promotes,
        "interpretation": (
            "Simple source-free models do not generate the per-book operation "
            "shape counts exactly under full-fit and prefix holdout."
        ),
    }
    data = {
        "schema": "operation_shape_count_generation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_count_generation_gate": rel(OP_COUNT_GATE),
        },
        "parameters": {
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "random_trials": RANDOM_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": summary,
        "top_models": [compact_model(row) for row in top],
        "best_model_predictions": best["predictions"],
        "prequential": cells,
        "decision": {
            "operation_shape_count_status": "retained_after_simple_generation_gate",
            "operation_count_status": "retained_after_simple_generation_gate",
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
