#!/usr/bin/env python3
"""Residual content-basis program gate.

Recent executable-decoder gates narrowed the live blocker to origin/selection
of content, not row0, plaintext, compression micro-sweeps, or graph
organization. This audit tests a constructive alternative to event-by-event
copy hints: when a v6 fallback copy chunk is paid once, can it enter an online
content basis that generates later fallback chunks by content reference?

The model is deliberately executable-ledger oriented. A miss pays the existing
v6 copy-hint bits and adds that emitted chunk to the basis. A hit pays a basis
reference instead of a source hint. The test is promoted only if the paid basis
program reduces the fallback tape and survives prefix/family/order controls.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "residual_content_basis_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
LINEAGE_SCRIPT = (
    ROOT
    / "analysis"
    / "innovation_lineage_basis_audit_20260622"
    / "scripts"
    / "01_innovation_lineage_basis_gate.py"
)
LINEAGE_FINAL = (
    ROOT
    / "analysis"
    / "innovation_lineage_basis_audit_20260622"
    / "reports"
    / "final_innovation_lineage_basis_audit.md"
)
SIGNATURE_FINAL = (
    ROOT
    / "analysis"
    / "lineage_signature_library_audit_20260622"
    / "reports"
    / "final_lineage_signature_library_audit.md"
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

JSON_OUT = TEST_RESULTS / "01_residual_content_basis_program_gate.json"
MD_OUT = TEST_RESULTS / "01_residual_content_basis_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_residual_content_basis_program_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260623
RANDOM_TRIALS = 200
MODEL_DECLARATION_BITS = math.log2(3)


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


def load_lineage_module() -> Any:
    spec = importlib.util.spec_from_file_location("innovation_lineage_basis", LINEAGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINEAGE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fallback_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    module = load_lineage_module()
    rows, validation = module.build_lineage_rows()
    if validation["errors"]:
        raise RuntimeError({"lineage_validation_errors": validation["errors"]})
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    out = []
    for row in module.candidate_rows(rows):
        book = int(row["book"])
        start = int(row["target_start"])
        length = int(row["exact_length"])
        content = books[book][start : start + length]
        out.append(
            {
                "book": book,
                "content": content,
                "copy_hint_rank_bits": float(row["copy_hint_rank_bits"]),
                "exact_length": length,
                "op_index": int(row["op_index"]),
                "source": int(row["source"]),
                "target_start": start,
            }
        )
    out.sort(key=lambda item: (item["book"], item["op_index"]))
    return out, validation


def basis_ref_bits(basis_size: int, offset_count: int, mode: str) -> float:
    if mode == "exact":
        return math.log2(max(1, basis_size))
    if mode == "substring":
        return math.log2(max(1, basis_size)) + math.log2(max(1, offset_count))
    raise ValueError(mode)


def first_basis_hit(content: str, basis: list[str], mode: str) -> tuple[int, int] | None:
    if mode == "exact":
        for index, chunk in enumerate(basis):
            if content == chunk:
                return index, 1
        return None
    if mode == "substring":
        matches = []
        for index, chunk in enumerate(basis):
            pos = chunk.find(content)
            if pos >= 0:
                matches.append((index, max(1, len(chunk) - len(content) + 1)))
        if not matches:
            return None
        return min(matches, key=lambda item: (item[0], item[1]))
    raise ValueError(mode)


def online_basis_score(
    rows: list[dict[str, Any]],
    *,
    mode: str,
    initial_basis: list[str] | None = None,
    add_misses: bool = True,
    add_hits: bool = False,
    include_declaration: bool = True,
) -> dict[str, Any]:
    basis = list(initial_basis or [])
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    total = MODEL_DECLARATION_BITS if include_declaration else 0.0
    hits = 0
    misses = 0
    hit_bits = 0.0
    miss_bits = 0.0
    events = []
    for row in rows:
        content = str(row["content"])
        hit = first_basis_hit(content, basis, mode)
        if hit is None:
            bits = float(row["copy_hint_rank_bits"])
            total += bits
            miss_bits += bits
            misses += 1
            status = "paid_copy_hint_basis_create" if add_misses else "paid_copy_hint_no_basis"
            if add_misses:
                basis.append(content)
        else:
            basis_index, offset_count = hit
            bits = basis_ref_bits(len(basis), offset_count, mode)
            total += bits
            hit_bits += bits
            hits += 1
            status = "derived_basis_reference"
            if add_hits:
                basis.append(content)
        events.append(
            {
                "basis_size_after": len(basis),
                "book": int(row["book"]),
                "bits": bits,
                "content_length": len(content),
                "hit": hit is not None,
                "op_index": int(row["op_index"]),
                "status": status,
            }
        )
    return {
        "baseline_copy_hint_bits": baseline,
        "basis_final_size": len(basis),
        "coded_bits": total,
        "delta_vs_copy_hint": total - baseline,
        "hit_bits": hit_bits,
        "hit_rate": hits / len(rows) if rows else 0.0,
        "hits": hits,
        "miss_bits": miss_bits,
        "misses": misses,
        "mode": mode,
        "model_declaration_bits": MODEL_DECLARATION_BITS if include_declaration else 0.0,
        "rows": len(rows),
        "sample_events": events[:40],
    }


def score_modes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        mode: online_basis_score(rows, mode=mode)
        for mode in ["exact", "substring"]
    }


def prefix_holdouts(rows: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_score = online_basis_score(
            train,
            mode=mode,
            include_declaration=False,
        )
        train_basis = []
        for row in train:
            content = str(row["content"])
            if first_basis_hit(content, train_basis, mode) is None:
                train_basis.append(content)
        frozen = online_basis_score(
            test,
            mode=mode,
            initial_basis=train_basis,
            add_misses=False,
        )
        online = online_basis_score(
            test,
            mode=mode,
            initial_basis=train_basis,
            add_misses=True,
        )
        out.append(
            {
                "cutoff": cutoff,
                "frozen_delta": frozen["delta_vs_copy_hint"],
                "frozen_hits": frozen["hits"],
                "online_delta": online["delta_vs_copy_hint"],
                "online_hits": online["hits"],
                "test_rows": len(test),
                "train_basis_size": train_score["basis_final_size"],
                "train_rows": len(train),
            }
        )
    return out


def family_holdouts(rows: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    data = load_json(FAMILY_HOLDOUT)
    out = []
    for family in data["rows"][:20]:
        test_books = {int(book) for book in family["test_books"]}
        train = [row for row in rows if int(row["book"]) not in test_books]
        test = [row for row in rows if int(row["book"]) in test_books]
        if not test:
            continue
        train_basis = []
        for row in train:
            content = str(row["content"])
            if first_basis_hit(content, train_basis, mode) is None:
                train_basis.append(content)
        frozen = online_basis_score(
            test,
            mode=mode,
            initial_basis=train_basis,
            add_misses=False,
        )
        out.append(
            {
                "frozen_delta": frozen["delta_vs_copy_hint"],
                "frozen_hits": frozen["hits"],
                "label": str(family["label"]),
                "test_rows": len(test),
                "train_basis_size": len(train_basis),
            }
        )
    return out


def control_order(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + (0 if mode == "exact" else 1000))
    observed = online_basis_score(rows, mode=mode)
    deltas = []
    hit_counts = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(rows)
        rng.shuffle(shuffled)
        scored = online_basis_score(shuffled, mode=mode)
        deltas.append(scored["delta_vs_copy_hint"])
        hit_counts.append(scored["hits"])
    deltas.sort()
    hit_counts.sort()
    return {
        "beats_p05_delta": observed["delta_vs_copy_hint"] < deltas[int(0.05 * RANDOM_TRIALS)],
        "beats_p95_hits": observed["hits"] > hit_counts[int(0.95 * RANDOM_TRIALS)],
        "observed_delta": observed["delta_vs_copy_hint"],
        "observed_hits": observed["hits"],
        "p05_delta": deltas[int(0.05 * RANDOM_TRIALS)],
        "p50_delta": deltas[int(0.50 * RANDOM_TRIALS)],
        "p95_delta": deltas[int(0.95 * RANDOM_TRIALS)],
        "p05_hits": hit_counts[int(0.05 * RANDOM_TRIALS)],
        "p50_hits": hit_counts[int(0.50 * RANDOM_TRIALS)],
        "p95_hits": hit_counts[int(0.95 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def control_content_shuffle(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + (2000 if mode == "exact" else 3000))
    observed = online_basis_score(rows, mode=mode)
    contents = [str(row["content"]) for row in rows]
    deltas = []
    hits = []
    for _ in range(RANDOM_TRIALS):
        shuffled_contents = list(contents)
        rng.shuffle(shuffled_contents)
        shuffled_rows = [dict(row, content=content) for row, content in zip(rows, shuffled_contents)]
        scored = online_basis_score(shuffled_rows, mode=mode)
        deltas.append(scored["delta_vs_copy_hint"])
        hits.append(scored["hits"])
    deltas.sort()
    hits.sort()
    return {
        "beats_p05_delta": observed["delta_vs_copy_hint"] < deltas[int(0.05 * RANDOM_TRIALS)],
        "beats_p95_hits": observed["hits"] > hits[int(0.95 * RANDOM_TRIALS)],
        "observed_delta": observed["delta_vs_copy_hint"],
        "observed_hits": observed["hits"],
        "p05_delta": deltas[int(0.05 * RANDOM_TRIALS)],
        "p50_delta": deltas[int(0.50 * RANDOM_TRIALS)],
        "p95_delta": deltas[int(0.95 * RANDOM_TRIALS)],
        "p05_hits": hits[int(0.05 * RANDOM_TRIALS)],
        "p50_hits": hits[int(0.50 * RANDOM_TRIALS)],
        "p95_hits": hits[int(0.95 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    rows, validation = fallback_rows()
    modes = score_modes(rows)
    best_mode = min(modes, key=lambda key: modes[key]["delta_vs_copy_hint"])
    prefix = {mode: prefix_holdouts(rows, mode) for mode in modes}
    family = {mode: family_holdouts(rows, mode) for mode in modes}
    controls = {
        mode: {
            "content_shuffle": control_content_shuffle(rows, mode),
            "order_shuffle": control_order(rows, mode),
        }
        for mode in modes
    }
    best = modes[best_mode]
    prefix_positive = sum(1 for row in prefix[best_mode] if row["online_delta"] < 0)
    family_positive = sum(1 for row in family[best_mode] if row["frozen_delta"] < 0)
    promoted = (
        best["delta_vs_copy_hint"] < 0
        and prefix_positive >= 4
        and controls[best_mode]["order_shuffle"]["beats_p05_delta"]
        and controls[best_mode]["content_shuffle"]["beats_p05_delta"]
    )
    weak = (
        not promoted
        and best["delta_vs_copy_hint"] < 0
        and prefix_positive >= 3
    )
    classification = (
        "PROMOTED_RESIDUAL_CONTENT_BASIS_PROGRAM"
        if promoted
        else "WEAK_RESIDUAL_CONTENT_BASIS_CLUE"
        if weak
        else "residual_content_basis_program_not_promoted"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "next_blocker": (
                "residual content origin remains external unless a content basis "
                "or innovation source can beat paid copy hints under controls"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "family_holdouts": family,
        "inputs": {
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "innovation_lineage_basis_final": rel(LINEAGE_FINAL),
            "lineage_script": rel(LINEAGE_SCRIPT),
            "lineage_signature_library_final": rel(SIGNATURE_FINAL),
        },
        "mode_scores": modes,
        "plaintext_claim": False,
        "prefix_holdouts": prefix,
        "row0_status": "unchanged_exogenous",
        "schema": "residual_content_basis_program_gate.v1",
        "scope": "analysis_only_residual_content_basis",
        "summary": {
            "best_delta_vs_copy_hint": best["delta_vs_copy_hint"],
            "best_hits": best["hits"],
            "best_mode": best_mode,
            "best_rows": best["rows"],
            "classification": classification,
            "fallback_rows_after_v6": len(rows),
            "family_positive_splits": family_positive,
            "prefix_positive_splits": prefix_positive,
            "promoted": promoted,
            "v6_external_bits_excluding_seed": float(v6["summary"]["v6_external_bits_excluding_seed"]),
        },
        "translation_delta": "NONE",
        "validation": {
            "lineage_atom_count": validation["atom_count"],
            "lineage_digits": validation["lineage_digits"],
            "roundtrip_70_70": validation["roundtrip_70_70"],
            "validation_errors": validation["errors"],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Residual Content-Basis Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- V6 fallback rows tested: `{s['fallback_rows_after_v6']}`.",
        f"- Best mode: `{s['best_mode']}`.",
        f"- Best hits: `{s['best_hits']}/{s['best_rows']}`.",
        f"- Best delta vs copy-hint: `{s['best_delta_vs_copy_hint']:.3f}` bits.",
        f"- Prefix positive splits: `{s['prefix_positive_splits']}/5`.",
        f"- Family positive splits: `{s['family_positive_splits']}`.",
        "",
        "## Full Fit",
        "",
        "| Mode | Hits | Misses | Basis | Coded bits | Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode, row in result["mode_scores"].items():
        lines.append(
            f"| `{mode}` | `{row['hits']}` | `{row['misses']}` | "
            f"`{row['basis_final_size']}` | `{row['coded_bits']:.3f}` | "
            f"`{row['delta_vs_copy_hint']:.3f}` |"
        )
    lines.extend(
        [
            "",
            f"## Prefix Holdout: `{s['best_mode']}`",
            "",
            "| Cutoff | Train basis | Test rows | Frozen hits | Frozen delta | Online hits | Online delta |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"][s["best_mode"]]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_basis_size']}` | `{row['test_rows']}` | "
            f"`{row['frozen_hits']}` | `{row['frozen_delta']:.3f}` | "
            f"`{row['online_hits']}` | `{row['online_delta']:.3f}` |"
        )
    controls = result["controls"][s["best_mode"]]
    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- Order-shuffle observed delta: `{controls['order_shuffle']['observed_delta']:.3f}`; "
            f"p05/p50/p95: `{controls['order_shuffle']['p05_delta']:.3f}` / "
            f"`{controls['order_shuffle']['p50_delta']:.3f}` / "
            f"`{controls['order_shuffle']['p95_delta']:.3f}`.",
            f"- Content-shuffle observed delta: `{controls['content_shuffle']['observed_delta']:.3f}`; "
            f"p05/p50/p95: `{controls['content_shuffle']['p05_delta']:.3f}` / "
            f"`{controls['content_shuffle']['p50_delta']:.3f}` / "
            f"`{controls['content_shuffle']['p95_delta']:.3f}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_RESIDUAL_CONTENT_BASIS_PROGRAM`."
                if s["promoted"]
                else "`residual_content_basis_program_not_promoted`: online content-basis reuse does not replace the remaining v6 fallback copy-hint tape under paid controls."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    controls = result["controls"][s["best_mode"]]
    lines = [
        "# Final Residual Content-Basis Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests a constructive content-origin route after executable v6. "
        "Instead of paying every remaining fallback copy hint independently, a "
        "paid fallback chunk may enter an online content basis; later fallback "
        "chunks can then be generated by exact or substring reference to that basis.",
        "",
        f"The tested set is the `{s['fallback_rows_after_v6']}` v6 fallback copy "
        "events. The best mode is "
        f"`{s['best_mode']}`, with `{s['best_hits']}/{s['best_rows']}` basis hits "
        f"and delta `{s['best_delta_vs_copy_hint']:.3f}` bits versus the existing "
        "copy-hint tape.",
        "",
        f"Prefix support is `{s['prefix_positive_splits']}/5` positive online "
        f"splits. Family support has `{s['family_positive_splits']}` positive "
        "frozen splits. Order-shuffle p05/p50/p95 deltas are "
        f"`{controls['order_shuffle']['p05_delta']:.3f}` / "
        f"`{controls['order_shuffle']['p50_delta']:.3f}` / "
        f"`{controls['order_shuffle']['p95_delta']:.3f}`; content-shuffle "
        "p05/p50/p95 deltas are "
        f"`{controls['content_shuffle']['p05_delta']:.3f}` / "
        f"`{controls['content_shuffle']['p50_delta']:.3f}` / "
        f"`{controls['content_shuffle']['p95_delta']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_RESIDUAL_CONTENT_BASIS_PROGRAM`."
            if s["promoted"]
            else "`residual_content_basis_program_not_promoted`."
        ),
        "",
        "The remaining fallback chunks do not currently reduce to a compact "
        "online content basis. This keeps the main blocker at origin/selection "
        "of residual content, rather than event graph organization or another "
        "source-address representation.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_residual_content_basis_program_gate.py](../scripts/01_residual_content_basis_program_gate.py)",
        "- [01_residual_content_basis_program_gate.json](test_results/01_residual_content_basis_program_gate.json)",
        "- [01_residual_content_basis_program_gate.md](test_results/01_residual_content_basis_program_gate.md)",
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
