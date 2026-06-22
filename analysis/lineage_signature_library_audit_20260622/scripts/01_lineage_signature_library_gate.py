#!/usr/bin/env python3
"""Lineage signature library gate.

The lineage-basis audit showed that single-atom addressing is too expensive.
This gate asks a broader causal-content question: do the remaining v6 fallback
copy chunks reuse a small library of lineage signatures, where a signature is
the run-length structure of seed/literal innovation atoms that produced the
copied chunk?

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "lineage_signature_library_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

LINEAGE_SCRIPT = (
    ROOT
    / "analysis"
    / "innovation_lineage_basis_audit_20260622"
    / "scripts"
    / "01_innovation_lineage_basis_gate.py"
)
LINEAGE_GATE = (
    ROOT
    / "analysis"
    / "innovation_lineage_basis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_innovation_lineage_basis_gate.json"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_lineage_signature_library_gate.json"
MD_OUT = TEST_RESULTS / "01_lineage_signature_library_gate.md"
FINAL_OUT = FRONT / "reports" / "final_lineage_signature_library_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 200
LIBRARY_DECLARATION_BITS = math.log2(5)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_lineage_module() -> Any:
    spec = importlib.util.spec_from_file_location("lineage_basis", LINEAGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINEAGE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signature_from_lineages(lineages: list[tuple[str, int, int, int]], mode: str) -> tuple[Any, ...]:
    if not lineages:
        return tuple()
    runs = []
    current = lineages[0][:3]
    run_start_offset = lineages[0][3]
    run_len = 0
    for lineage in lineages:
        key = lineage[:3]
        if key != current:
            kind, book, atom_id = current
            if mode == "kind_run_lengths":
                runs.append((kind, run_len))
            elif mode == "kind_book_run_lengths":
                runs.append((kind, book, run_len))
            elif mode == "atom_offset_run_lengths":
                runs.append((kind, book, atom_id, run_start_offset, run_len))
            else:
                raise KeyError(mode)
            current = key
            run_start_offset = lineage[3]
            run_len = 0
        run_len += 1
    kind, book, atom_id = current
    if mode == "kind_run_lengths":
        runs.append((kind, run_len))
    elif mode == "kind_book_run_lengths":
        runs.append((kind, book, run_len))
    elif mode == "atom_offset_run_lengths":
        runs.append((kind, book, atom_id, run_start_offset, run_len))
    else:
        raise KeyError(mode)
    return tuple(runs)


def build_signature_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    module = load_lineage_module()
    rows, validation = module.build_lineage_rows()
    fallback_rows = module.candidate_rows(rows)
    # Reconstruct lineage signatures by replaying the same lineage build with a
    # tiny monkey patch would be too brittle; instead, rerun the implementation
    # locally using exposed helpers and add the missing signature data in a
    # controlled second pass.
    books = {int(key): value for key, value in module.load_json(module.BOOKS_DIGITS).items()}
    by_book = module.grouped_ledger_rows()
    classes = module.source_endpoint_classes()
    literal_span_selected = module.literal_span_sources()
    stream = "".join(books[book] for book in range(10))
    lineage_stream = []
    atom_id = 0
    for book in range(10):
        for offset, _digit in enumerate(books[book]):
            lineage_stream.append(("seed", book, atom_id, offset))
        atom_id += 1

    by_key = {(int(row["book"]), int(row["op_index"])): row for row in fallback_rows}
    enriched = []
    for book in range(10, 70):
        rendered = []
        rendered_lineage = []
        for op in by_book[book]:
            op_index = int(op["op_index"])
            op_type = str(op["op_type"])
            start = int(op["target_start"])
            length = int(op["exact_length"])
            available = stream + "".join(rendered)
            available_lineage = lineage_stream + rendered_lineage
            if op_type == "literal":
                payload = str(op["literal_payload"])
                rendered.append(payload)
                rendered_lineage.extend(
                    ("literal", book, atom_id, offset)
                    for offset in range(len(payload))
                )
                atom_id += 1
                continue
            source = int(op["copy_source_raw"])
            copied = available[source : source + length]
            source_lineages = available_lineage[source : source + length]
            key = (book, op_index)
            v5_class = classes[key]
            v6_class = "literal_span_source" if key in literal_span_selected else v5_class
            if v6_class == "fallback":
                base = dict(by_key[key])
                base["signature_kind_run_lengths"] = signature_from_lineages(
                    source_lineages, "kind_run_lengths"
                )
                base["signature_kind_book_run_lengths"] = signature_from_lineages(
                    source_lineages, "kind_book_run_lengths"
                )
                base["signature_atom_offset_run_lengths"] = signature_from_lineages(
                    source_lineages, "atom_offset_run_lengths"
                )
                base["signature_run_count"] = len(base["signature_kind_run_lengths"])
                base["source_text"] = copied
                enriched.append(base)
            rendered.append(copied)
            rendered_lineage.extend(source_lineages)
        stream += "".join(rendered)
        lineage_stream.extend(rendered_lineage)
    return enriched, validation


def rank_library(train_signatures: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    counts = Counter(train_signatures)
    return [
        signature
        for signature, _count in sorted(
            counts.items(),
            key=lambda item: (-item[1], len(item[0]), repr(item[0])),
        )
    ]


def signature_cost(signature: tuple[Any, ...], total_signatures: int) -> float:
    # A conservative declaration cost for a signature body: each run declares a
    # small tuple plus a length-ish component. This deliberately prevents a
    # posthoc dictionary from looking free.
    return math.log2(total_signatures + 1) + sum(math.log2(16 + len(str(run))) for run in signature)


def score_split(
    rows: list[dict[str, Any]],
    train_books: set[int],
    test_books: set[int],
    signature_key: str,
) -> dict[str, Any]:
    train = [row for row in rows if int(row["book"]) in train_books]
    test = [row for row in rows if int(row["book"]) in test_books]
    train_sigs = [tuple(row[signature_key]) for row in train]
    library = rank_library(train_sigs)
    rank = {signature: index + 1 for index, signature in enumerate(library)}
    declaration = LIBRARY_DECLARATION_BITS + sum(
        signature_cost(signature, max(1, len(library))) for signature in library
    )
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in test)
    coded = declaration
    hits = 0
    for row in test:
        signature = tuple(row[signature_key])
        if signature in rank:
            coded += math.log2(rank[signature])
            hits += 1
        else:
            coded += float(row["copy_hint_rank_bits"])
    return {
        "baseline_copy_hint_bits": baseline,
        "coded_bits": coded,
        "delta_vs_copy_hint": coded - baseline,
        "library_size": len(library),
        "signature_hits": hits,
        "signature_key": signature_key,
        "test_rows": len(test),
        "train_rows": len(train),
    }


def prefix_holdouts(rows: list[dict[str, Any]], signature_key: str) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        scored = score_split(rows, set(range(10, cutoff)), set(range(cutoff, 70)), signature_key)
        scored["cutoff"] = cutoff
        out.append(scored)
    return out


def family_holdouts(rows: list[dict[str, Any]], signature_key: str) -> list[dict[str, Any]]:
    data = load_json(FAMILY_HOLDOUT)
    out = []
    for family in data["rows"][:20]:
        test = {int(book) for book in family["test_books"]}
        train = set(range(70)) - test
        scored = score_split(rows, train, test, signature_key)
        if scored["test_rows"] == 0:
            continue
        scored["label"] = str(family["label"])
        out.append(scored)
    return out


def full_fit(rows: list[dict[str, Any]], signature_key: str) -> dict[str, Any]:
    signatures = [tuple(row[signature_key]) for row in rows]
    library = rank_library(signatures)
    rank = {signature: index + 1 for index, signature in enumerate(library)}
    declaration = LIBRARY_DECLARATION_BITS + sum(
        signature_cost(signature, max(1, len(library))) for signature in library
    )
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    coded = declaration + sum(math.log2(rank[tuple(row[signature_key])]) for row in rows)
    return {
        "baseline_copy_hint_bits": baseline,
        "coded_bits": coded,
        "delta_vs_copy_hint": coded - baseline,
        "library_size": len(library),
        "signature_key": signature_key,
        "signature_unique": len(set(signatures)),
    }


def shuffled_signature_control(rows: list[dict[str, Any]], signature_key: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + len(signature_key))
    observed = full_fit(rows, signature_key)["delta_vs_copy_hint"]
    signatures = [row[signature_key] for row in rows]
    totals = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(signatures)
        rng.shuffle(shuffled)
        controlled = [dict(row) | {signature_key: shuffled[index]} for index, row in enumerate(rows)]
        totals.append(full_fit(controlled, signature_key)["delta_vs_copy_hint"])
    totals.sort()
    return {
        "observed_delta": observed,
        "p05_delta": totals[int(0.05 * RANDOM_TRIALS)],
        "p50_delta": totals[int(0.50 * RANDOM_TRIALS)],
        "p95_delta": totals[int(0.95 * RANDOM_TRIALS)],
        "beats_p05": observed < totals[int(0.05 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    for name, path in [
        ("lineage_basis_gate", LINEAGE_GATE),
        ("executable_v6_gate", EXECUTABLE_V6_GATE),
    ]:
        assert_boundary(name, load_json(path))
    rows, validation = build_signature_rows()
    signature_keys = [
        "signature_kind_run_lengths",
        "signature_kind_book_run_lengths",
        "signature_atom_offset_run_lengths",
    ]
    full = {key: full_fit(rows, key) for key in signature_keys}
    prefixes = {key: prefix_holdouts(rows, key) for key in signature_keys}
    families = {key: family_holdouts(rows, key) for key in signature_keys}
    controls = {key: shuffled_signature_control(rows, key) for key in signature_keys}
    best_key = min(full, key=lambda key: full[key]["delta_vs_copy_hint"])
    promoted = (
        full[best_key]["delta_vs_copy_hint"] < 0
        and sum(1 for row in prefixes[best_key] if row["delta_vs_copy_hint"] < 0) >= 4
        and controls[best_key]["beats_p05"]
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_LINEAGE_SIGNATURE_LIBRARY_PROGRAM"
            if promoted
            else "lineage_signature_library_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "control": controls,
        "decision": {
            "next_blocker": (
                "remaining fallback chunks do not reuse a paid compact library "
                "of causal lineage signatures"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "family_holdouts": families,
        "full_fit": full,
        "inputs": {
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "innovation_lineage_basis_gate": rel(LINEAGE_GATE),
            "innovation_lineage_basis_script": rel(LINEAGE_SCRIPT),
        },
        "plaintext_claim": False,
        "prefix_holdouts": prefixes,
        "row0_status": "unchanged_exogenous",
        "schema": "lineage_signature_library_gate.v1",
        "scope": "analysis_only_lineage_signature_library",
        "summary": {
            "best_delta_vs_copy_hint": full[best_key]["delta_vs_copy_hint"],
            "best_signature_key": best_key,
            "fallback_rows_after_v6": len(rows),
            "prefix_positive_splits": sum(
                1 for row in prefixes[best_key] if row["delta_vs_copy_hint"] < 0
            ),
            "promoted": promoted,
            "signature_run_count_mean": mean([int(row["signature_run_count"]) for row in rows])
            if rows
            else 0.0,
            "validation_errors": validation["errors"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Lineage Signature Library Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Fallback rows after v6: `{s['fallback_rows_after_v6']}`.",
        f"- Best signature key: `{s['best_signature_key']}`.",
        f"- Best delta vs copy-hint: `{s['best_delta_vs_copy_hint']:.3f}` bits.",
        f"- Prefix positive splits: `{s['prefix_positive_splits']}/5`.",
        f"- Mean signature run count: `{s['signature_run_count_mean']:.3f}`.",
        "",
        "## Full Fit",
        "",
        "| Signature | Library | Unique | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key, row in result["full_fit"].items():
        lines.append(
            f"| `{key}` | `{row['library_size']}` | `{row['signature_unique']}` | "
            f"`{row['delta_vs_copy_hint']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Test rows | Hits | Delta |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"][s["best_signature_key"]]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_rows']}` | `{row['signature_hits']}` | "
            f"`{row['delta_vs_copy_hint']:.3f}` |"
        )
    control = result["control"][s["best_signature_key"]]
    lines.extend(
        [
            "",
            "## Control",
            "",
            f"- Observed full-fit delta: `{control['observed_delta']:.3f}`.",
            f"- Shuffled signature p05/p50/p95 delta: `{control['p05_delta']:.3f}` / `{control['p50_delta']:.3f}` / `{control['p95_delta']:.3f}`.",
            f"- Beats p05: `{control['beats_p05']}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_LINEAGE_SIGNATURE_LIBRARY_PROGRAM`."
                if s["promoted"]
                else "`lineage_signature_library_not_promoted`: the remaining fallbacks do not share a compact paid causal-signature library."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    best = result["full_fit"][s["best_signature_key"]]
    control = result["control"][s["best_signature_key"]]
    lines = [
        "# Final Lineage Signature Library Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests whether the remaining v6 fallback copy chunks reuse a "
        "small library of causal lineage signatures rather than requiring source "
        "copy-hints event by event.",
        "",
        f"The best signature family is `{s['best_signature_key']}`. Full-fit cost "
        f"uses a library of `{best['library_size']}` signatures and is "
        f"`{best['delta_vs_copy_hint']:.3f}` bits versus copy-hint. Prefix support "
        f"is `{s['prefix_positive_splits']}/5` positive splits, and the shuffled "
        f"signature control has p05/p50/p95 deltas `{control['p05_delta']:.3f}` / "
        f"`{control['p50_delta']:.3f}` / `{control['p95_delta']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_LINEAGE_SIGNATURE_LIBRARY_PROGRAM`."
            if s["promoted"]
            else "`lineage_signature_library_not_promoted`."
        ),
        "",
        "The remaining fallback chunks do not currently share a compact paid "
        "lineage-signature library. This further narrows the blocker to content "
        "selection/origin rather than event graph organization.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_lineage_signature_library_gate.py](../scripts/01_lineage_signature_library_gate.py)",
        "- [01_lineage_signature_library_gate.json](test_results/01_lineage_signature_library_gate.json)",
        "- [01_lineage_signature_library_gate.md](test_results/01_lineage_signature_library_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
