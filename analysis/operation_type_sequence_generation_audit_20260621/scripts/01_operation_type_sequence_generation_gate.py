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
SHAPE_COUNT_GATE = (
    ROOT
    / "analysis"
    / "operation_shape_count_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_shape_count_generation_gate.json"
)

OUT_STEM = "01_operation_type_sequence_generation_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 1000
RANDOM_SEED = 4692026062105


Row = dict[str, Any]
Sequence = str


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
    module = load_module("source_free_skeleton_for_type_sequence", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[Row]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        seq = "".join("L" if str(op["type"]) == "literal" else "C" for op in by_book[book])
        rows.append(
            {
                "book": book,
                "book_length": sum(lengths),
                "op_count": len(seq),
                "literal_count": seq.count("L"),
                "copy_count": seq.count("C"),
                "sequence": seq,
                "shape_key": f"ops={len(seq)}|lit={seq.count('L')}",
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


def normalize(seq: str, op_count: int, literal_count: int) -> str:
    seq = "".join(ch for ch in seq if ch in {"L", "C"})
    if len(seq) < op_count:
        seq += "C" * (op_count - len(seq))
    seq = seq[:op_count]
    current_lit = seq.count("L")
    chars = list(seq)
    if current_lit < literal_count:
        for index in range(op_count - 1, -1, -1):
            if chars[index] == "C":
                chars[index] = "L"
                current_lit += 1
                if current_lit == literal_count:
                    break
    elif current_lit > literal_count:
        for index in range(op_count - 1, -1, -1):
            if chars[index] == "L":
                chars[index] = "C"
                current_lit -= 1
                if current_lit == literal_count:
                    break
    return "".join(chars)


def mode(values: list[str]) -> str:
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value))


def front_literals(row: Row) -> str:
    return "L" * int(row["literal_count"]) + "C" * int(row["copy_count"])


def back_literals(row: Row) -> str:
    return "C" * int(row["copy_count"]) + "L" * int(row["literal_count"])


def even_literals(row: Row) -> str:
    op_count = int(row["op_count"])
    literal_count = int(row["literal_count"])
    if literal_count == 0:
        return "C" * op_count
    positions = {
        round((i + 1) * (op_count + 1) / (literal_count + 1)) - 1
        for i in range(literal_count)
    }
    positions = {max(0, min(op_count - 1, pos)) for pos in positions}
    while len(positions) < literal_count:
        for pos in range(op_count):
            positions.add(pos)
            if len(positions) == literal_count:
                break
    return "".join("L" if index in positions else "C" for index in range(op_count))


def alternating_from_start(row: Row) -> str:
    op_count = int(row["op_count"])
    literal_count = int(row["literal_count"])
    chars = ["C"] * op_count
    placed = 0
    for index in range(0, op_count, 2):
        if placed >= literal_count:
            break
        chars[index] = "L"
        placed += 1
    for index in range(op_count):
        if placed >= literal_count:
            break
        if chars[index] == "C":
            chars[index] = "L"
            placed += 1
    return "".join(chars)


def alternating_from_second(row: Row) -> str:
    op_count = int(row["op_count"])
    literal_count = int(row["literal_count"])
    chars = ["C"] * op_count
    placed = 0
    for index in range(1, op_count, 2):
        if placed >= literal_count:
            break
        chars[index] = "L"
        placed += 1
    for index in range(op_count):
        if placed >= literal_count:
            break
        if chars[index] == "C":
            chars[index] = "L"
            placed += 1
    return "".join(chars)


def train_template_model(
    rows: list[Row],
    name: str,
    key_fn: Callable[[Row], str],
) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(str(row["sequence"]))
    templates = {key: mode(values) for key, values in groups.items()}
    fallback_by_shape = {
        key: mode([str(row["sequence"]) for row in rows if str(row["shape_key"]) == key])
        for key in {str(row["shape_key"]) for row in rows}
    }
    fallback = mode([str(row["sequence"]) for row in rows])
    return {
        "name": name,
        "kind": "template",
        "key_fn": key_fn,
        "templates": templates,
        "fallback_by_shape": fallback_by_shape,
        "fallback": fallback,
        "payload_records": sum(len(seq) for seq in templates.values()),
        "parameters": {
            "context_count": len(templates),
            "template_entries": sum(len(seq) for seq in templates.values()),
        },
    }


def train_models(rows: list[Row]) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = [
        {
            "name": "front_literals",
            "kind": "deterministic",
            "predict": front_literals,
            "payload_records": 1,
            "parameters": {},
        },
        {
            "name": "back_literals",
            "kind": "deterministic",
            "predict": back_literals,
            "payload_records": 1,
            "parameters": {},
        },
        {
            "name": "even_literals",
            "kind": "deterministic",
            "predict": even_literals,
            "payload_records": 1,
            "parameters": {},
        },
        {
            "name": "alternating_from_start",
            "kind": "deterministic",
            "predict": alternating_from_start,
            "payload_records": 1,
            "parameters": {},
        },
        {
            "name": "alternating_from_second",
            "kind": "deterministic",
            "predict": alternating_from_second,
            "payload_records": 1,
            "parameters": {},
        },
    ]
    specs: list[tuple[str, Callable[[Row], str]]] = [
        ("shape", lambda row: str(row["shape_key"])),
        ("book_mod10_x_shape", lambda row: f"{int(row['book']) % 10}|{row['shape_key']}"),
        ("book_mod5_x_shape", lambda row: f"{int(row['book']) % 5}|{row['shape_key']}"),
        ("length_bucket_x_shape", lambda row: f"{bucket(int(row['book_length']))}|{row['shape_key']}"),
        (
            "book_mod10_x_length_bucket_x_shape",
            lambda row: f"{int(row['book']) % 10}|{bucket(int(row['book_length']))}|{row['shape_key']}",
        ),
    ]
    for name, key_fn in specs:
        models.append(train_template_model(rows, f"template_{name}", key_fn))
    return models


def predict(model: dict[str, Any], row: Row) -> str:
    if model["kind"] == "deterministic":
        seq = model["predict"](row)
    else:
        key = model["key_fn"](row)
        seq = model["templates"].get(key)
        if seq is None:
            seq = model["fallback_by_shape"].get(str(row["shape_key"]), model["fallback"])
    return normalize(seq, int(row["op_count"]), int(row["literal_count"]))


def score_model(rows: list[Row], model: dict[str, Any]) -> dict[str, Any]:
    predictions = []
    exact_books = 0
    type_hits = 0
    total_ops = 0
    correction_payload_records = 0
    for row in rows:
        predicted = predict(model, row)
        truth = str(row["sequence"])
        exact = predicted == truth
        hits = sum(1 for a, b in zip(predicted, truth) if a == b)
        exact_books += int(exact)
        type_hits += hits
        total_ops += len(truth)
        if not exact:
            correction_payload_records += len(truth)
        predictions.append(
            {
                "book": int(row["book"]),
                "shape": str(row["shape_key"]),
                "truth": truth,
                "predicted": predicted,
                "exact": exact,
                "type_hits": hits,
                "op_count": int(row["op_count"]),
            }
        )
    correction_records = len(rows) - exact_books
    paid_records = int(model["payload_records"]) + correction_payload_records
    return {
        "model": model["name"],
        "kind": model["kind"],
        "payload_records": int(model["payload_records"]),
        "book_count": len(rows),
        "total_ops": total_ops,
        "exact_books": exact_books,
        "type_hits": type_hits,
        "type_errors": total_ops - type_hits,
        "correction_records": correction_records,
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
            int(item["type_hits"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
    )


def random_sequence(row: Row, rng: random.Random) -> str:
    op_count = int(row["op_count"])
    literal_count = int(row["literal_count"])
    positions = set(rng.sample(range(op_count), literal_count)) if literal_count else set()
    return "".join("L" if index in positions else "C" for index in range(op_count))


def random_control(rows: list[Row], *, trials: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    exact_values = []
    hit_values = []
    for _ in range(trials):
        exact = 0
        hits = 0
        for row in rows:
            predicted = random_sequence(row, rng)
            truth = str(row["sequence"])
            exact += int(predicted == truth)
            hits += sum(1 for a, b in zip(predicted, truth) if a == b)
        exact_values.append(exact)
        hit_values.append(hits)
    exact_sorted = sorted(exact_values)
    hit_sorted = sorted(hit_values)
    p95_index = int(0.95 * (trials - 1))
    return {
        "trials": trials,
        "mean_exact_books": mean(exact_values),
        "p95_exact_books": exact_sorted[p95_index],
        "max_exact_books": max(exact_values),
        "mean_type_hits": mean(hit_values),
        "p95_type_hits": hit_sorted[p95_index],
        "max_type_hits": max(hit_values),
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
        models = train_models(train)
        train_scored = [score_model(train, model) for model in models]
        best_train = choose_best(train_scored)
        selected = next(model for model in models if model["name"] == best_train["model"])
        test_score = score_model(test, selected)
        control = random_control(test, trials=RANDOM_TRIALS, seed=RANDOM_SEED + cutoff * 100003)
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_model": selected["name"],
                "train_exact_books": int(best_train["exact_books"]),
                "train_type_hits": int(best_train["type_hits"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_type_hits": int(test_score["type_hits"]),
                "test_total_ops": int(test_score["total_ops"]),
                "test_random_mean_exact_books": control["mean_exact_books"],
                "test_random_p95_exact_books": control["p95_exact_books"],
                "test_random_mean_type_hits": control["mean_type_hits"],
                "test_random_p95_type_hits": control["p95_type_hits"],
                "beats_random_p95_exact": int(test_score["exact_books"]) > control["p95_exact_books"],
                "beats_random_p95_type_hits": int(test_score["type_hits"]) > control["p95_type_hits"],
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def compact_model(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "predictions"}


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    lines = [
        "# Operation Type Sequence Generation Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the literal/copy type sequence within each book can be",
        "generated after granting `(op_count, literal_count)`. This is",
        "source-free and target-text-free.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Literal/copy totals: `{s['literal_operation_count']}` / `{s['copy_operation_count']}`.",
        f"- Models tested: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best type hits: `{s['best_type_hits']}/{s['operation_count']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact sequence atlas `{s['exact_sequence_atlas_records']}`.",
        f"- Best paid records vs exact type fields: `{s['best_paid_records']}` vs `{s['exact_type_field_records']}`.",
        f"- Paid-record delta vs exact type fields: `{s['paid_record_delta_vs_exact_type_fields']:+d}`.",
        f"- Random mean/p95/max exact books: `{s['random_mean_exact_books']:.3f}` / `{s['random_p95_exact_books']}` / `{s['random_max_exact_books']}`.",
        f"- Random mean/p95/max type hits: `{s['random_mean_type_hits']:.3f}` / `{s['random_p95_type_hits']}` / `{s['random_max_type_hits']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 exact cells: `{s['prequential_beats_random_p95_exact_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Models",
        "",
        "| Model | Kind | Exact books | Type hits | Paid records | Payload |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in data["top_models"]:
        lines.append(
            "| "
            f"`{item['model']}` | "
            f"`{item['kind']}` | "
            f"`{item['exact_books']}/{item['book_count']}` | "
            f"`{item['type_hits']}/{item['total_ops']}` | "
            f"`{item['paid_records']}` | "
            f"`{item['payload_records']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected model | Test exact | Test hits | Random p95 exact | Random p95 hits | Beats exact | Beats hits | Cover all |",
            "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for cell in data["prequential"]:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_model']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_type_hits']}/{cell['test_total_ops']}` | "
            f"`{cell['test_random_p95_exact_books']}` | "
            f"`{cell['test_random_p95_type_hits']}` | "
            f"`{cell['beats_random_p95_exact']}` | "
            f"`{cell['beats_random_p95_type_hits']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes operation-type-sequence generator: `{s['promotes_operation_type_sequence_generator']}`.",
            f"- Audit-only paid-record reduction: `{s['audit_only_paid_record_reduction']}`.",
            "- Literal/copy sequence remains retained unless a later joint parser derives it with lengths and copy availability.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    shape_count = load_json(SHAPE_COUNT_GATE)
    assert_boundary("operation_shape_count_generation_gate", shape_count)
    rows = make_rows(reconstruct())
    scored, best = evaluate(rows)
    cells = prequential(rows)
    control = random_control(rows, trials=RANDOM_TRIALS, seed=RANDOM_SEED)
    promotes = (
        int(best["exact_books"]) == len(rows)
        and int(best["paid_records"]) < len(rows)
        and all(cell["covers_all_test_books"] for cell in cells)
    )
    classification = (
        "operation_type_sequence_generator_promoted"
        if promotes
        else "operation_type_sequence_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            int(item["type_hits"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
        reverse=True,
    )[:10]
    summary = {
        "book_count": len(rows),
        "operation_count": sum(int(row["op_count"]) for row in rows),
        "literal_operation_count": sum(int(row["literal_count"]) for row in rows),
        "copy_operation_count": sum(int(row["copy_count"]) for row in rows),
        "model_count": len(scored),
        "best_model": best["model"],
        "best_kind": best["kind"],
        "best_exact_books": int(best["exact_books"]),
        "best_type_hits": int(best["type_hits"]),
        "best_type_errors": int(best["type_errors"]),
        "best_paid_records": int(best["paid_records"]),
        "best_payload_records": int(best["payload_records"]),
        "exact_sequence_atlas_records": len(rows),
        "exact_type_field_records": sum(int(row["op_count"]) for row in rows),
        "paid_record_delta_vs_exact_type_fields": int(best["paid_records"])
        - sum(int(row["op_count"]) for row in rows),
        "audit_only_paid_record_reduction": int(best["paid_records"])
        < sum(int(row["op_count"]) for row in rows),
        "random_trials": RANDOM_TRIALS,
        "random_mean_exact_books": control["mean_exact_books"],
        "random_p95_exact_books": control["p95_exact_books"],
        "random_max_exact_books": control["max_exact_books"],
        "random_mean_type_hits": control["mean_type_hits"],
        "random_p95_type_hits": control["p95_type_hits"],
        "random_max_type_hits": control["max_type_hits"],
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(1 for cell in cells if cell["covers_all_test_books"]),
        "prequential_beats_random_p95_exact_cells": sum(
            1 for cell in cells if cell["beats_random_p95_exact"]
        ),
        "prequential_beats_random_p95_type_hit_cells": sum(
            1 for cell in cells if cell["beats_random_p95_type_hits"]
        ),
        "promotes_operation_type_sequence_generator": promotes,
        "interpretation": (
            "Simple source-free policies and paid type templates do not generate "
            "the literal/copy order exactly under prefix holdout."
        ),
    }
    data = {
        "schema": "operation_type_sequence_generation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_shape_count_generation_gate": rel(SHAPE_COUNT_GATE),
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
            "operation_type_sequence_status": "retained_after_simple_generation_gate",
            "operation_shape_count_status": "retained_after_simple_generation_gate",
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
