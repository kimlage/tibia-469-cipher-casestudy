#!/usr/bin/env python3
"""Innovation lineage basis gate.

The causal graph audit showed that graph macros do not replace residual tapes.
This audit tests the next content-origin question without opening another local
endpoint/source selector: if every emitted digit is traced back to a seed or
literal innovation atom, can remaining v6 fallback copy origins be addressed in
that innovation basis more cheaply than copy hints?

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "innovation_lineage_basis_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
EXECUTABLE_V6_FINAL = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "final_executable_v6_literal_span_origin_audit.md"
)
CAUSAL_GRAPH_FINAL = (
    ROOT
    / "analysis"
    / "causal_event_graph_program_audit_20260622"
    / "reports"
    / "final_causal_event_graph_program_audit.md"
)
UNANCHORED_SCRIPT = (
    ROOT
    / "analysis"
    / "unanchored_copy_origin_representation_audit_20260622"
    / "scripts"
    / "01_unanchored_copy_origin_representation_gate.py"
)
EXECUTABLE_V6_SCRIPT = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "scripts"
    / "01_executable_v6_literal_span_origin_gate.py"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_innovation_lineage_basis_gate.json"
MD_OUT = TEST_RESULTS / "01_innovation_lineage_basis_gate.md"
FINAL_OUT = FRONT / "reports" / "final_innovation_lineage_basis_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 200
MODEL_DECLARATION_BITS = math.log2(4)

Lineage = tuple[str, int, int, int]


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
    decision = data.get("decision", {})
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grouped_ledger_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def source_endpoint_classes() -> dict[tuple[int, int], str]:
    module = load_module("unanchored_copy_origin", UNANCHORED_SCRIPT)
    rows = module.summarize_source_endpoint_mode("source_endpoint_memory")["rows"]
    return {(int(row["book"]), int(row["op_index"])): str(row["row_class"]) for row in rows}


def literal_span_sources() -> set[tuple[int, int]]:
    module = load_module("executable_v6_literal_span_origin", EXECUTABLE_V6_SCRIPT)
    return set(module.literal_span_source_events())


def atom_rank(active_atoms: list[dict[str, Any]], atom_id: int) -> int:
    selected = next(atom for atom in active_atoms if int(atom["atom_id"]) == atom_id)
    selected_start = int(selected["start"])
    return 1 + sum(1 for atom in active_atoms if int(atom["start"]) > selected_start)


def is_contiguous_single_atom(lineages: list[Lineage]) -> tuple[bool, dict[str, Any] | None]:
    if not lineages:
        return False, None
    atom_key = lineages[0][:3]
    offsets = [lineage[3] for lineage in lineages]
    if any(lineage[:3] != atom_key for lineage in lineages):
        return False, None
    expected = list(range(offsets[0], offsets[0] + len(offsets)))
    if offsets != expected:
        return False, None
    return True, {
        "atom_book": atom_key[1],
        "atom_id": atom_key[2],
        "atom_kind": atom_key[0],
        "atom_offset": offsets[0],
        "atom_span_length": len(offsets),
    }


def build_lineage_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    classes = source_endpoint_classes()
    literal_span_selected = literal_span_sources()

    stream = "".join(books[book] for book in range(10))
    lineage_stream: list[Lineage] = []
    atoms = []
    atom_id = 0
    cursor = 0
    for book in range(10):
        start = cursor
        for offset, _digit in enumerate(books[book]):
            lineage_stream.append(("seed", book, atom_id, offset))
        cursor += len(books[book])
        atoms.append(
            {
                "atom_id": atom_id,
                "book": book,
                "kind": "seed",
                "length": len(books[book]),
                "op_index": None,
                "start": start,
            }
        )
        atom_id += 1

    rows = []
    errors = []
    for book in range(10, 70):
        rendered = []
        rendered_lineage: list[Lineage] = []
        for op in by_book[book]:
            op_index = int(op["op_index"])
            op_type = str(op["op_type"])
            start = int(op["target_start"])
            length = int(op["exact_length"])
            available = stream + "".join(rendered)
            available_lineage = lineage_stream + rendered_lineage
            if op_type == "literal":
                payload = str(op["literal_payload"])
                literal_atom = {
                    "atom_id": atom_id,
                    "book": book,
                    "kind": "literal",
                    "length": len(payload),
                    "op_index": op_index,
                    "start": len(stream) + len("".join(rendered)),
                }
                atoms.append(literal_atom)
                rendered.append(payload)
                rendered_lineage.extend(
                    ("literal", book, atom_id, offset)
                    for offset in range(len(payload))
                )
                atom_id += 1
                continue

            source = int(op["copy_source_raw"])
            copied = available[source : source + length]
            expected = books[book][start : start + length]
            if copied != expected:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "reason": "copy_payload_mismatch",
                    }
                )
            source_lineages = available_lineage[source : source + length]
            single, single_info = is_contiguous_single_atom(source_lineages)
            key = (book, op_index)
            v5_class = classes[key]
            v6_class = "literal_span_source" if key in literal_span_selected else v5_class
            active_atoms = [atom for atom in atoms if int(atom["start"]) <= len(available)]
            lineage_bits = None
            if single and single_info is not None:
                selected_atom_id = int(single_info["atom_id"])
                selected_atom = next(atom for atom in active_atoms if int(atom["atom_id"]) == selected_atom_id)
                rank = atom_rank(active_atoms, selected_atom_id)
                lineage_bits = math.log2(rank) + math.log2(max(1, int(selected_atom["length"])))
                single_info["atom_rank"] = rank
                single_info["atom_length"] = int(selected_atom["length"])
            rows.append(
                {
                    "atom_count_available": len(active_atoms),
                    "book": book,
                    "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                    "exact_length": length,
                    "lineage_address_bits": lineage_bits,
                    "lineage_single_atom": single,
                    "lineage_single_atom_info": single_info,
                    "op_index": op_index,
                    "source": source,
                    "target_start": start,
                    "v5_class": v5_class,
                    "v6_class": v6_class,
                }
            )
            rendered.append(copied)
            rendered_lineage.extend(source_lineages)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            errors.append({"book": book, "reason": "book_roundtrip_mismatch"})
        stream += rendered_book
        lineage_stream.extend(rendered_lineage)
    return rows, {
        "atom_count": len(atoms),
        "atoms": atoms,
        "errors": errors,
        "lineage_digits": len(lineage_stream),
        "roundtrip_70_70": not errors and len(lineage_stream) == sum(len(books[idx]) for idx in range(70)),
    }


def candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["v6_class"] == "fallback"]


def score(rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    lineage_bits = 0.0
    coverage = 0
    by_kind: Counter[str] = Counter()
    for row in rows:
        bits = row["lineage_address_bits"]
        if bits is None:
            lineage_bits += float(row["copy_hint_rank_bits"])
        else:
            lineage_bits += float(bits)
            coverage += 1
            info = row["lineage_single_atom_info"] or {}
            by_kind[str(info.get("atom_kind", "unknown"))] += 1
    total = lineage_bits + MODEL_DECLARATION_BITS
    return {
        "baseline_copy_hint_bits": baseline,
        "coverage": coverage,
        "delta_after_declaration_vs_copy_hint": total - baseline,
        "lineage_address_bits_before_declaration": lineage_bits,
        "model_declaration_bits": MODEL_DECLARATION_BITS,
        "rows": len(rows),
        "single_atom_by_kind": dict(by_kind),
        "total_bits_after_declaration": total,
    }


def prefix_holdouts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        test = [row for row in rows if int(row["book"]) >= cutoff]
        s = score(test)
        out.append(
            {
                "cutoff": cutoff,
                "test_delta_after_declaration": s["delta_after_declaration_vs_copy_hint"],
                "test_rows": s["rows"],
                "test_single_atom_coverage": s["coverage"],
            }
        )
    return out


def family_holdouts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = load_json(FAMILY_HOLDOUT)
    out = []
    for family in data["rows"][:20]:
        books = {int(book) for book in family["test_books"]}
        test = [row for row in rows if int(row["book"]) in books]
        if not test:
            continue
        s = score(test)
        out.append(
            {
                "label": str(family["label"]),
                "test_delta_after_declaration": s["delta_after_declaration_vs_copy_hint"],
                "test_rows": s["rows"],
                "test_single_atom_coverage": s["coverage"],
            }
        )
    return out


def randomized_lineage_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 1001)
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    observed = score(rows)["total_bits_after_declaration"]
    totals = []
    observed_cover = [row for row in rows if row["lineage_address_bits"] is not None]
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        covered_indices = set(rng.sample(range(len(rows)), min(len(observed_cover), len(rows))))
        for index, row in enumerate(rows):
            if index not in covered_indices:
                total += float(row["copy_hint_rank_bits"])
                continue
            # Preserve the rough atom-count and source-offset scale but break
            # the true innovation lineage.
            info = row["lineage_single_atom_info"] or {}
            atom_count = max(1, int(row["atom_count_available"]))
            atom_length = max(1, int(info.get("atom_length", row["exact_length"])))
            rank = rng.randint(1, atom_count)
            total += math.log2(rank) + math.log2(atom_length)
        totals.append(total + MODEL_DECLARATION_BITS)
    totals.sort()
    return {
        "baseline_copy_hint_bits": baseline,
        "observed_bits_after_declaration": observed,
        "observed_delta": observed - baseline,
        "p05_delta": totals[int(0.05 * RANDOM_TRIALS)] - baseline,
        "p50_delta": totals[int(0.50 * RANDOM_TRIALS)] - baseline,
        "p95_delta": totals[int(0.95 * RANDOM_TRIALS)] - baseline,
        "beats_p05": observed < totals[int(0.05 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    rows, validation = build_lineage_rows()
    fallback_rows = candidate_rows(rows)
    full = score(fallback_rows)
    prefix = prefix_holdouts(fallback_rows)
    family = family_holdouts(fallback_rows)
    control = randomized_lineage_control(fallback_rows)
    promoted = (
        full["delta_after_declaration_vs_copy_hint"] < 0
        and sum(1 for row in prefix if row["test_delta_after_declaration"] < 0) >= 4
        and control["beats_p05"]
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_INNOVATION_LINEAGE_BASIS_PROGRAM"
            if promoted
            else "innovation_lineage_basis_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "control": control,
        "decision": {
            "next_blocker": (
                "remaining fallback source choices are not explained by a compact "
                "seed/literal innovation lineage basis"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "family_holdouts": family,
        "inputs": {
            "causal_graph_final": rel(CAUSAL_GRAPH_FINAL),
            "executable_v6_final": rel(EXECUTABLE_V6_FINAL),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "prefix_holdouts": prefix,
        "row0_status": "unchanged_exogenous",
        "schema": "innovation_lineage_basis_gate.v1",
        "scope": "analysis_only_innovation_lineage_basis",
        "summary": full
        | {
            "fallback_rows_after_v6": len(fallback_rows),
            "lineage_atom_count": validation["atom_count"],
            "lineage_digits": validation["lineage_digits"],
            "prefix_positive_splits": sum(
                1 for row in prefix if row["test_delta_after_declaration"] < 0
            ),
            "promoted": promoted,
            "v6_external_bits_excluding_seed": float(v6["summary"]["v6_external_bits_excluding_seed"]),
        },
        "translation_delta": "NONE",
        "validation": validation | {"atoms": validation["atoms"][:80]},
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Innovation Lineage Basis Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- V6 fallback rows tested: `{s['fallback_rows_after_v6']}`.",
        f"- Lineage atoms: `{s['lineage_atom_count']}`.",
        f"- Baseline copy-hint bits: `{s['baseline_copy_hint_bits']:.3f}`.",
        f"- Single-atom lineage coverage: `{s['coverage']}`.",
        f"- Total bits after declaration: `{s['total_bits_after_declaration']:.3f}`.",
        f"- Delta vs copy-hint: `{s['delta_after_declaration_vs_copy_hint']:.3f}`.",
        f"- Prefix positive splits: `{s['prefix_positive_splits']}/5`.",
        f"- Single-atom by kind: `{s['single_atom_by_kind']}`.",
        "",
        "## Prefix Holdout",
        "",
        "| Cutoff | Rows | Coverage | Delta |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in result["prefix_holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_rows']}` | `{row['test_single_atom_coverage']}` | "
            f"`{row['test_delta_after_declaration']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Control",
            "",
            f"- Observed delta: `{c['observed_delta']:.3f}`.",
            f"- Randomized lineage p05/p50/p95 delta: `{c['p05_delta']:.3f}` / `{c['p50_delta']:.3f}` / `{c['p95_delta']:.3f}`.",
            f"- Beats p05: `{c['beats_p05']}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_INNOVATION_LINEAGE_BASIS_PROGRAM`."
                if s["promoted"]
                else "`innovation_lineage_basis_not_promoted`: innovation lineage is useful provenance, but it does not replace the remaining v6 fallback copy-hint tape."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Final Innovation Lineage Basis Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit propagates digit-level lineage from seed and literal innovation "
        "atoms through the executable v6 decoder, then asks whether the remaining "
        "v6 fallback copy origins can be addressed in that innovation basis.",
        "",
        f"The v6 fallback set has `{s['fallback_rows_after_v6']}` copy events and "
        f"`{s['baseline_copy_hint_bits']:.3f}` copy-hint bits. Only `{s['coverage']}` "
        "sources are contiguous intervals inside a single seed/literal lineage "
        f"atom. The lineage-address program costs `{s['total_bits_after_declaration']:.3f}` "
        f"bits after declaration, delta `{s['delta_after_declaration_vs_copy_hint']:.3f}` "
        "versus copy-hint.",
        "",
        f"Prefix support is `{s['prefix_positive_splits']}/5` positive splits. The "
        f"randomized-lineage control has p05/p50/p95 deltas `{c['p05_delta']:.3f}` / "
        f"`{c['p50_delta']:.3f}` / `{c['p95_delta']:.3f}`, and observed beats p05 "
        f"is `{c['beats_p05']}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_INNOVATION_LINEAGE_BASIS_PROGRAM`."
            if s["promoted"]
            else "`innovation_lineage_basis_not_promoted`."
        ),
        "",
        "The lineage basis is useful provenance for the causal ledger, but it does "
        "not explain the remaining fallback source choices as a compact content "
        "origin program. The blocker remains origin/selection of innovation content.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_innovation_lineage_basis_gate.py](../scripts/01_innovation_lineage_basis_gate.py)",
        "- [01_innovation_lineage_basis_gate.json](test_results/01_innovation_lineage_basis_gate.json)",
        "- [01_innovation_lineage_basis_gate.md](test_results/01_innovation_lineage_basis_gate.md)",
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
