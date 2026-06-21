from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
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
MARKOV_GATE = (
    ROOT
    / "analysis"
    / "operation_length_markov_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_length_markov_gate.json"
)

OUT_STEM = "01_operation_length_motif_library_gate"
MOTIF_LENGTHS = range(2, 7)
LIBRARY_SIZES = [0, 5, 10, 20, 40, 80]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]

Symbol = str
Motif = tuple[Symbol, ...]


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
    module = load_module("source_free_skeleton_for_length_motif", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def sequences(by_book: dict[int, list[dict[str, Any]]], mode: str) -> dict[int, list[Symbol]]:
    out: dict[int, list[Symbol]] = {}
    for book, ops in by_book.items():
        if mode == "length":
            out[book] = [str(int(op["length"])) for op in ops]
        elif mode == "type_length":
            out[book] = [f"{op['type']}:{int(op['length'])}" for op in ops]
        else:
            raise ValueError(mode)
    return out


def motif_counts(seqs: dict[int, list[Symbol]]) -> Counter[Motif]:
    counts: Counter[Motif] = Counter()
    for seq in seqs.values():
        for width in MOTIF_LENGTHS:
            for start in range(0, len(seq) - width + 1):
                counts[tuple(seq[start : start + width])] += 1
    return counts


def motif_score(motif: Motif, count: int) -> int:
    return count * (len(motif) - 1) - len(motif)


def select_library(seqs: dict[int, list[Symbol]], size: int) -> list[Motif]:
    if size <= 0:
        return []
    counts = motif_counts(seqs)
    candidates = [
        (motif_score(motif, count), count, len(motif), motif)
        for motif, count in counts.items()
        if count >= 2 and motif_score(motif, count) > 0
    ]
    candidates.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)
    return [motif for _score, _count, _length, motif in candidates[:size]]


def parse_sequence(seq: list[Symbol], library: list[Motif]) -> dict[str, Any]:
    by_start: dict[Symbol, list[Motif]] = {}
    for motif in library:
        by_start.setdefault(motif[0], []).append(motif)
    for motifs in by_start.values():
        motifs.sort(key=lambda motif: (len(motif), motif), reverse=True)

    n = len(seq)
    best: list[tuple[int, int, list[tuple[str, Motif | tuple[Symbol, ...]]]] | None] = [
        None
    ] * (n + 1)
    best[n] = (0, 0, [])
    for pos in range(n - 1, -1, -1):
        options: list[tuple[int, int, list[tuple[str, Motif | tuple[Symbol, ...]]]]] = []
        singleton = (seq[pos],)
        tail = best[pos + 1]
        if tail is not None:
            options.append((tail[0] + 1, tail[1] + 1, [("residual", singleton)] + tail[2]))
        for motif in by_start.get(seq[pos], []):
            width = len(motif)
            if tuple(seq[pos : pos + width]) != motif:
                continue
            tail = best[pos + width]
            if tail is not None:
                options.append((tail[0] + 1, tail[1], [("motif", motif)] + tail[2]))
        best[pos] = min(options, key=lambda row: (row[0], row[1], len(row[2])))
    parsed = best[0]
    if parsed is None:
        raise RuntimeError("unparseable sequence")
    assignment_count, residual_count, assignments = parsed
    motif_assignments = assignment_count - residual_count
    return {
        "assignment_count": assignment_count,
        "motif_assignment_count": motif_assignments,
        "residual_singletons": residual_count,
        "all_motif_covered": residual_count == 0,
        "assignments": [
            {"kind": kind, "motif": list(motif)} for kind, motif in assignments
        ],
    }


def evaluate_library(seqs: dict[int, list[Symbol]], library: list[Motif], mode: str) -> dict[str, Any]:
    rows = []
    for book in sorted(seqs):
        parsed = parse_sequence(seqs[book], library)
        rows.append(
            {
                "book": book,
                "op_count": len(seqs[book]),
                "assignment_count": parsed["assignment_count"],
                "motif_assignment_count": parsed["motif_assignment_count"],
                "residual_singletons": parsed["residual_singletons"],
                "all_motif_covered": parsed["all_motif_covered"],
            }
        )
    library_payload_records = sum(len(motif) for motif in library)
    assignment_records = sum(row["assignment_count"] for row in rows)
    exact_atlas_records = sum(row["op_count"] for row in rows)
    total_records = library_payload_records + assignment_records
    return {
        "mode": mode,
        "library_size": len(library),
        "library_payload_records": library_payload_records,
        "assignment_records": assignment_records,
        "total_records": total_records,
        "exact_atlas_records": exact_atlas_records,
        "delta_vs_exact_atlas_records": total_records - exact_atlas_records,
        "residual_singletons": sum(row["residual_singletons"] for row in rows),
        "all_motif_books": sum(1 for row in rows if row["all_motif_covered"]),
        "book_count": len(rows),
        "rows": rows,
        "library": [list(motif) for motif in library],
    }


def best_for_sequences(seqs: dict[int, list[Symbol]], mode: str) -> dict[str, Any]:
    scores = []
    for size in LIBRARY_SIZES:
        library = select_library(seqs, size)
        scores.append(evaluate_library(seqs, library, mode))
    scores.sort(
        key=lambda row: (
            row["delta_vs_exact_atlas_records"],
            row["residual_singletons"],
            row["library_size"],
        )
    )
    return {"best": scores[0], "scoreboard": scores}


def prequential(all_seqs: dict[int, list[Symbol]], mode: str) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = {book: seq for book, seq in all_seqs.items() if book < cutoff}
        test = {book: seq for book, seq in all_seqs.items() if book >= cutoff}
        train_result = best_for_sequences(train, mode)
        library = [tuple(row) for row in train_result["best"]["library"]]
        test_score = evaluate_library(test, library, mode)
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_library_size": len(library),
                "train_delta_vs_exact_atlas_records": train_result["best"][
                    "delta_vs_exact_atlas_records"
                ],
                "train_residual_singletons": train_result["best"]["residual_singletons"],
                "test_delta_vs_exact_atlas_records": test_score[
                    "delta_vs_exact_atlas_records"
                ],
                "test_residual_singletons": test_score["residual_singletons"],
                "test_all_motif_books": test_score["all_motif_books"],
                "test_book_count": test_score["book_count"],
            }
        )
    return out


def make_result() -> dict[str, Any]:
    markov = load_json(MARKOV_GATE)
    assert_boundary("operation_length_markov_gate", markov)
    by_book = reconstruct()
    mode_results = {}
    for mode in ["length", "type_length"]:
        seqs = sequences(by_book, mode)
        full = best_for_sequences(seqs, mode)
        preq = prequential(seqs, mode)
        mode_results[mode] = {
            "full_fit": full,
            "prequential_rows": preq,
        }
    best_mode = min(
        mode_results,
        key=lambda mode: (
            mode_results[mode]["full_fit"]["best"]["delta_vs_exact_atlas_records"],
            mode_results[mode]["full_fit"]["best"]["residual_singletons"],
        ),
    )
    best = mode_results[best_mode]["full_fit"]["best"]
    promotes = (
        best["delta_vs_exact_atlas_records"] < 0
        and best["residual_singletons"] == 0
        and all(
            row["test_residual_singletons"] == 0
            for row in mode_results[best_mode]["prequential_rows"]
        )
    )
    classification = (
        "operation_length_motif_generator_promoted"
        if promotes
        else "operation_length_motif_library_not_promoted"
    )
    return {
        "schema": "operation_length_motif_library_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_length_markov_gate": rel(MARKOV_GATE),
        },
        "scope": {
            "analysis_only": True,
            "tests_subbook_length_motifs": True,
            "book_lengths_granted": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "operation_count": sum(len(ops) for ops in by_book.values()),
            "best_mode": best_mode,
            "best_library_size": best["library_size"],
            "best_total_records": best["total_records"],
            "best_exact_atlas_records": best["exact_atlas_records"],
            "best_delta_vs_exact_atlas_records": best[
                "delta_vs_exact_atlas_records"
            ],
            "best_residual_singletons": best["residual_singletons"],
            "best_all_motif_books": best["all_motif_books"],
            "promotes_operation_length_motif_generator": promotes,
            "interpretation": (
                "Repeated sub-book length motifs exist, but the paid motif "
                "library does not remove the need for residual length records "
                "and does not generalize as a generator under prefix holdout."
            ),
        },
        "mode_results": mode_results,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "operation_length_status": "atlas_retained_after_motif_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Operation Length Motif Library Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether operation lengths are generated by a reusable sub-book",
        "motif library rather than a one-row-per-operation atlas.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Best mode: `{s['best_mode']}`.",
        f"- Best library size: `{s['best_library_size']}`.",
        f"- Best records vs exact atlas: `{s['best_total_records']}` vs `{s['best_exact_atlas_records']}` (`{s['best_delta_vs_exact_atlas_records']:+d}`).",
        f"- Best residual singletons: `{s['best_residual_singletons']}`.",
        f"- Best all-motif-covered books: `{s['best_all_motif_books']}/{s['book_count']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Mode | Library | Records | Delta | Residuals | All-motif books |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, data in result["mode_results"].items():
        for row in data["full_fit"]["scoreboard"]:
            lines.append(
                f"| `{mode}` | `{row['library_size']}` | `{row['total_records']}` | "
                f"`{row['delta_vs_exact_atlas_records']:+d}` | "
                f"`{row['residual_singletons']}` | `{row['all_motif_books']}/{row['book_count']}` |"
            )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Mode | Cutoff | Library | Test delta | Test residuals | All-motif books |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for mode, data in result["mode_results"].items():
        for row in data["prequential_rows"]:
            lines.append(
                f"| `{mode}` | `{row['cutoff_book']}` | `{row['selected_library_size']}` | "
                f"`{row['test_delta_vs_exact_atlas_records']:+d}` | "
                f"`{row['test_residual_singletons']}` | "
                f"`{row['test_all_motif_books']}/{row['test_book_count']}` |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes operation-length motif generator: `{s['promotes_operation_length_motif_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
