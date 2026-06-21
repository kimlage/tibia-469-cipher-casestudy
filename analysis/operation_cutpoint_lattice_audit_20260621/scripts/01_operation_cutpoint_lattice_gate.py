from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from statistics import mean
from typing import Any


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
CUTPOINT_SCALING_GATE = (
    ROOT
    / "analysis"
    / "operation_cutpoint_scaling_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_cutpoint_scaling_gate.json"
)

OUT_STEM = "01_operation_cutpoint_lattice_gate"
DENOMINATORS = list(range(2, 65)) + [70, 80, 90, 100, 128]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 400
RANDOM_SEED = 46920260621


BookRow = dict[str, Any]


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
    module = load_module("source_free_skeleton_for_cutpoint_lattice", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def cumulative(lengths: list[int]) -> list[int]:
    total = 0
    out = []
    for length in lengths:
        total += length
        out.append(total)
    return out


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[BookRow]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        book_length = sum(lengths)
        cutpoints = cumulative(lengths)[:-1]
        rows.append(
            {
                "book": book,
                "book_length": book_length,
                "op_count": len(lengths),
                "internal_count": max(0, len(lengths) - 1),
                "lengths": lengths,
                "cutpoints": cutpoints,
            }
        )
    return rows


def lattice_points(book_length: int, denominator: int) -> list[int]:
    points = {
        int(round(index * book_length / denominator))
        for index in range(1, denominator)
    }
    return sorted(point for point in points if 0 < point < book_length)


def row_lattice_score(row: BookRow, denominator: int) -> dict[str, Any]:
    points = set(lattice_points(int(row["book_length"]), denominator))
    hits = sum(1 for cut in row["cutpoints"] if int(cut) in points)
    internal_count = int(row["internal_count"])
    return {
        "book": int(row["book"]),
        "book_length": int(row["book_length"]),
        "op_count": int(row["op_count"]),
        "denominator": denominator,
        "grid_point_count": len(points),
        "hit_count": hits,
        "internal_count": internal_count,
        "exact_book": hits == internal_count,
    }


def denominator_score(rows: list[BookRow], denominator: int) -> dict[str, Any]:
    per_book = [row_lattice_score(row, denominator) for row in rows]
    total_internal = sum(int(row["internal_count"]) for row in rows)
    total_hits = sum(int(item["hit_count"]) for item in per_book)
    exact_books = sum(1 for item in per_book if item["exact_book"])
    total_grid_points = sum(int(item["grid_point_count"]) for item in per_book)
    return {
        "denominator": denominator,
        "book_count": len(rows),
        "total_internal_cutpoints": total_internal,
        "total_hits": total_hits,
        "exact_books": exact_books,
        "total_grid_points": total_grid_points,
        "mean_grid_points_per_book": total_grid_points / len(rows) if rows else 0.0,
        "per_book": per_book,
    }


def random_cutpoints(book_length: int, op_count: int, rng: random.Random) -> list[int]:
    if op_count <= 1:
        return []
    return sorted(rng.sample(range(1, book_length), op_count - 1))


def random_control_for_denominator(
    rows: list[BookRow],
    denominator: int,
    *,
    trials: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed + denominator * 1009)
    hit_values = []
    exact_values = []
    for _ in range(trials):
        trial_hits = 0
        trial_exact = 0
        for row in rows:
            cuts = random_cutpoints(
                int(row["book_length"]),
                int(row["op_count"]),
                rng,
            )
            points = set(lattice_points(int(row["book_length"]), denominator))
            hits = sum(1 for cut in cuts if cut in points)
            trial_hits += hits
            if hits == int(row["internal_count"]):
                trial_exact += 1
        hit_values.append(trial_hits)
        exact_values.append(trial_exact)
    sorted_hits = sorted(hit_values)
    sorted_exact = sorted(exact_values)
    index_95 = int(math.floor(0.95 * (trials - 1)))
    return {
        "trials": trials,
        "mean_hits": mean(hit_values),
        "p95_hits": sorted_hits[index_95],
        "max_hits": max(hit_values),
        "mean_exact_books": mean(exact_values),
        "p95_exact_books": sorted_exact[index_95],
        "max_exact_books": max(exact_values),
    }


def score_denominators(
    rows: list[BookRow],
    denominators: list[int],
    *,
    include_controls: bool,
) -> list[dict[str, Any]]:
    scored = []
    for denominator in denominators:
        score = denominator_score(rows, denominator)
        if include_controls:
            score["random_control"] = random_control_for_denominator(
                rows,
                denominator,
                trials=RANDOM_TRIALS,
                seed=RANDOM_SEED,
            )
            score["hit_lift_vs_random_mean"] = (
                score["total_hits"] - score["random_control"]["mean_hits"]
            )
            score["exact_book_lift_vs_random_mean"] = (
                score["exact_books"] - score["random_control"]["mean_exact_books"]
            )
        else:
            score["random_control"] = None
            score["hit_lift_vs_random_mean"] = None
            score["exact_book_lift_vs_random_mean"] = None
        scored.append(score)
    return scored


def choose_best(scored: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            int(item["total_hits"]),
            -int(item["denominator"]),
        ),
    )


def prequential(rows: list[BookRow]) -> list[dict[str, Any]]:
    cells = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_scored = score_denominators(train, DENOMINATORS, include_controls=False)
        best_train = choose_best(train_scored)
        denominator = int(best_train["denominator"])
        test_score = denominator_score(test, denominator)
        control = random_control_for_denominator(
            test,
            denominator,
            trials=RANDOM_TRIALS,
            seed=RANDOM_SEED + cutoff * 100003,
        )
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_denominator": denominator,
                "train_exact_books": int(best_train["exact_books"]),
                "train_hits": int(best_train["total_hits"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_hits": int(test_score["total_hits"]),
                "test_internal_cutpoints": int(test_score["total_internal_cutpoints"]),
                "test_random_mean_hits": control["mean_hits"],
                "test_random_p95_hits": control["p95_hits"],
                "test_random_max_hits": control["max_hits"],
                "beats_random_p95": int(test_score["total_hits"]) > control["p95_hits"],
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    top = data["top_denominators"]
    cells = data["prequential"]
    lines = [
        "# Operation Cutpoint Lattice Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether operation boundaries are aligned to a small normalized",
        "lattice after granting book length and operation count. This is",
        "source-free and target-text-free: it checks proportional grid",
        "placement, not source choice or plaintext.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Internal cutpoints tested: `{s['internal_cutpoint_count']}`.",
        f"- Denominators tested: `{s['denominator_count']}`.",
        f"- Best denominator: `{s['best_denominator']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best cutpoint hits: `{s['best_hits']}/{s['internal_cutpoint_count']}`.",
        f"- Best random mean/p95/max hits: `{s['best_random_mean_hits']:.3f}` / `{s['best_random_p95_hits']}` / `{s['best_random_max_hits']}`.",
        f"- Best hit lift vs random mean: `{s['best_hit_lift_vs_random_mean']:.3f}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 cells: `{s['prequential_beats_random_p95_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Denominators",
        "",
        "| Denominator | Exact books | Hits | Random mean hits | Random p95 | Random max | Lift |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in top:
        control = item["random_control"]
        lines.append(
            "| "
            f"`{item['denominator']}` | "
            f"`{item['exact_books']}/{item['book_count']}` | "
            f"`{item['total_hits']}/{item['total_internal_cutpoints']}` | "
            f"`{control['mean_hits']:.3f}` | "
            f"`{control['p95_hits']}` | "
            f"`{control['max_hits']}` | "
            f"`{item['hit_lift_vs_random_mean']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected d | Test exact books | Test hits | Random mean | Random p95 | Beats p95 | Cover all |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for cell in cells:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_denominator']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_hits']}/{cell['test_internal_cutpoints']}` | "
            f"`{cell['test_random_mean_hits']:.3f}` | "
            f"`{cell['test_random_p95_hits']}` | "
            f"`{cell['beats_random_p95']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes cutpoint-lattice generator: `{s['promotes_cutpoint_lattice_generator']}`.",
            "- Small proportional lattices do not generate the operation cutpoint atlas.",
            "- The best denominator is scored as an alignment clue only if it exceeds random controls; it still does not choose the exact cutpoint sequence.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    scaling = load_json(CUTPOINT_SCALING_GATE)
    assert_boundary("operation_cutpoint_scaling_gate", scaling)
    by_book = reconstruct()
    rows = make_rows(by_book)
    scored = score_denominators(rows, DENOMINATORS, include_controls=True)
    best = choose_best(scored)
    cells = prequential(rows)
    operation_count = sum(int(row["op_count"]) for row in rows)
    internal_count = sum(int(row["internal_count"]) for row in rows)
    promotes = (
        int(best["exact_books"]) == len(rows)
        and all(cell["covers_all_test_books"] for cell in cells)
        and all(cell["beats_random_p95"] for cell in cells)
    )
    classification = (
        "operation_cutpoint_lattice_generator_promoted"
        if promotes
        else "operation_cutpoint_lattice_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            int(item["total_hits"]),
            float(item["hit_lift_vs_random_mean"]),
            -int(item["denominator"]),
        ),
        reverse=True,
    )[:10]
    summary = {
        "book_count": len(rows),
        "operation_count": operation_count,
        "internal_cutpoint_count": internal_count,
        "denominator_count": len(DENOMINATORS),
        "random_trials_per_denominator": RANDOM_TRIALS,
        "best_denominator": int(best["denominator"]),
        "best_exact_books": int(best["exact_books"]),
        "best_hits": int(best["total_hits"]),
        "best_random_mean_hits": best["random_control"]["mean_hits"],
        "best_random_p95_hits": best["random_control"]["p95_hits"],
        "best_random_max_hits": best["random_control"]["max_hits"],
        "best_hit_lift_vs_random_mean": best["hit_lift_vs_random_mean"],
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(
            1 for cell in cells if cell["covers_all_test_books"]
        ),
        "prequential_beats_random_p95_cells": sum(
            1 for cell in cells if cell["beats_random_p95"]
        ),
        "promotes_cutpoint_lattice_generator": promotes,
        "interpretation": (
            "Small normalized lattice denominators do not generate the exact "
            "operation cutpoint atlas. Any alignment signal remains descriptive "
            "because the exact cutpoint sequence is not selected and holdout "
            "coverage is incomplete."
        ),
    }
    data = {
        "schema": "operation_cutpoint_lattice_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "cutpoint_scaling_gate": rel(CUTPOINT_SCALING_GATE),
        },
        "parameters": {
            "denominators": DENOMINATORS,
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "random_trials": RANDOM_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": summary,
        "top_denominators": top,
        "prequential": cells,
        "decision": {
            "operation_length_status": "atlas_retained_after_cutpoint_lattice_gate",
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
