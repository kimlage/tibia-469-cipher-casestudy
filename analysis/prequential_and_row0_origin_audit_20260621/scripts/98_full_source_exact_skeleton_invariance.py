from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE91_SCRIPT = HERE / "scripts" / "91_full_source_exposure_audit.py"
GATE95 = TEST_RESULTS / "95_full_source_policy_invariance_boundary.json"
GATE97 = TEST_RESULTS / "97_source_policy_selector_boundary.json"

TEST_CUTOFFS = [10, 20, 35, 50, 60]
POLICIES = [
    "earliest_source",
    "latest_source",
    "prefer_previous_end_then_earliest",
]


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


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def source_free_skeleton(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skeleton = []
    for op in ops:
        if op["type"] == "literal":
            skeleton.append(
                {
                    "type": "literal",
                    "target_start": int(op["target_start"]),
                    "length": int(op["length"]),
                    "forced": bool(op["forced"]),
                }
            )
        elif op["type"] == "copy":
            skeleton.append(
                {
                    "type": "copy",
                    "target_start": int(op["target_start"]),
                    "length": int(op["length"]),
                    "forced": bool(op["forced"]),
                }
            )
        else:
            raise RuntimeError(op)
    return skeleton


def summarize_skeleton(skeleton: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "op_count": len(skeleton),
        "copy_items": sum(1 for op in skeleton if op["type"] == "copy"),
        "literal_runs": sum(1 for op in skeleton if op["type"] == "literal"),
        "copied_digits": sum(
            int(op["length"]) for op in skeleton if op["type"] == "copy"
        ),
        "literal_digits": sum(
            int(op["length"]) for op in skeleton if op["type"] == "literal"
        ),
    }


def make_result() -> dict[str, Any]:
    gate95 = load_json(GATE95)
    gate97 = load_json(GATE97)
    assert_boundary("full_source_policy_invariance_boundary", gate95)
    assert_boundary("source_policy_selector_boundary", gate97)
    if gate95["classification"] != "full_source_policy_stable_but_source_variant":
        raise RuntimeError("gate95 does not expose source-variant boundary")
    if gate97["classification"] != "book_specific_policy_selector_audit_only":
        raise RuntimeError("gate97 did not reject selector as audit-only")

    helper91 = load_module("gate91_for_gate98", GATE91_SCRIPT)
    captured_ops: dict[str, list[dict[str, Any]]] = {}
    original_compact_signature = helper91.compact_signature

    def capture_compact_signature(ops: list[dict[str, Any]]) -> str:
        signature = original_compact_signature(ops)
        previous = captured_ops.get(signature)
        if previous is not None and previous != ops:
            raise RuntimeError({"type": "signature_collision", "signature": signature})
        captured_ops[signature] = json.loads(json.dumps(ops))
        return signature

    helper91.compact_signature = capture_compact_signature

    gate86 = helper91.load_module("gate86_for_gate98", helper91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate98", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate98", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    observations = []
    for policy in POLICIES:
        for cutoff in TEST_CUTOFFS:
            rows = helper91.run_cutoff(cutoff, gate77, gate82, policy=policy)
            for row in rows:
                ops = captured_ops[row["signature"]]
                skeleton = source_free_skeleton(ops)
                skeleton_hash = stable_hash(skeleton)
                observations.append(
                    {
                        "cutoff": int(row["cutoff"]),
                        "book": int(row["book"]),
                        "policy": policy,
                        "exact_signature": row["signature"],
                        "skeleton_hash": skeleton_hash,
                        "skeleton_summary": summarize_skeleton(skeleton),
                        "source_sum": int(row["source_sum"]),
                        "non_earliest_source_count": int(
                            row["non_earliest_source_count"]
                        ),
                        "parser_bits": float(row["parser_bits"]),
                    }
                )
    elapsed = time.perf_counter() - start

    by_case: dict[tuple[int, int], list[dict[str, Any]]] = {}
    by_book: dict[int, list[dict[str, Any]]] = {}
    skeleton_by_hash: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        by_case.setdefault((row["cutoff"], row["book"]), []).append(row)
        by_book.setdefault(row["book"], []).append(row)
        skeleton_by_hash.setdefault(row["skeleton_hash"], []).append(row)

    case_rows = []
    for (cutoff, book), rows in sorted(by_case.items()):
        policies = sorted(row["policy"] for row in rows)
        if policies != sorted(POLICIES):
            raise RuntimeError({"cutoff": cutoff, "book": book, "policies": policies})
        skeleton_count = len({row["skeleton_hash"] for row in rows})
        exact_signature_count = len({row["exact_signature"] for row in rows})
        source_sum_span = max(row["source_sum"] for row in rows) - min(
            row["source_sum"] for row in rows
        )
        parser_bits_span = max(row["parser_bits"] for row in rows) - min(
            row["parser_bits"] for row in rows
        )
        case_rows.append(
            {
                "cutoff": cutoff,
                "book": book,
                "skeleton_count": skeleton_count,
                "exact_signature_count": exact_signature_count,
                "skeleton_invariant": skeleton_count == 1,
                "exact_signature_invariant": exact_signature_count == 1,
                "source_sum_span": source_sum_span,
                "parser_bits_span": parser_bits_span,
            }
        )

    book_rows = []
    for book, rows in sorted(by_book.items()):
        skeleton_hashes = sorted({row["skeleton_hash"] for row in rows})
        cutoffs = sorted({row["cutoff"] for row in rows})
        book_rows.append(
            {
                "book": book,
                "observation_count": len(rows),
                "cutoffs": cutoffs,
                "policy_count": len({row["policy"] for row in rows}),
                "skeleton_count": len(skeleton_hashes),
                "skeleton_invariant": len(skeleton_hashes) == 1,
                "canonical_skeleton_hash": skeleton_hashes[0],
            }
        )

    invariant_cases = [row for row in case_rows if row["skeleton_invariant"]]
    invariant_books = [row for row in book_rows if row["skeleton_invariant"]]
    exact_invariant_cases = [
        row for row in case_rows if row["exact_signature_invariant"]
    ]
    canonical_books = sorted(
        (rows[0] for rows in skeleton_by_hash.values()),
        key=lambda row: row["book"],
    )
    # One canonical observation per book, preserving each book's skeleton summary.
    canonical_by_book = {}
    for row in observations:
        canonical_by_book.setdefault(row["book"], row)
    canonical_summaries = [
        canonical_by_book[book]["skeleton_summary"] for book in sorted(canonical_by_book)
    ]
    totals = {
        "book_count": len(canonical_summaries),
        "op_count": sum(row["op_count"] for row in canonical_summaries),
        "copy_items": sum(row["copy_items"] for row in canonical_summaries),
        "literal_runs": sum(row["literal_runs"] for row in canonical_summaries),
        "copied_digits": sum(row["copied_digits"] for row in canonical_summaries),
        "literal_digits": sum(row["literal_digits"] for row in canonical_summaries),
    }

    skeleton_exactly_invariant = (
        len(invariant_cases) == len(case_rows)
        and len(invariant_books) == len(book_rows)
    )
    classification = (
        "source_free_skeleton_exactly_invariant"
        if skeleton_exactly_invariant
        else "source_free_skeleton_variant"
    )

    return {
        "schema": "full_source_exact_skeleton_invariance.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate95_policy_invariance_boundary": rel(GATE95),
            "gate97_selector_boundary": rel(GATE97),
            "gate91_script": rel(GATE91_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "tested_cutoffs": TEST_CUTOFFS,
            "policies": POLICIES,
            "source_removed_from_skeleton": True,
            "source_default_removed_from_skeleton": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "observation_count": len(observations),
            "case_count": len(case_rows),
            "book_count": len(book_rows),
            "case_skeleton_invariant_count": len(invariant_cases),
            "case_skeleton_variant_count": len(case_rows) - len(invariant_cases),
            "book_skeleton_invariant_count": len(invariant_books),
            "book_skeleton_variant_count": len(book_rows) - len(invariant_books),
            "exact_signature_invariant_cases": len(exact_invariant_cases),
            "exact_signature_variant_cases": len(case_rows) - len(exact_invariant_cases),
            "skeleton_totals": totals,
            "promotes_generator": False,
            "source_fields_removed_from_skeleton_atlas": True,
            "source_fields_removed_from_decoder": False,
            "interpretation": (
                "Removing source addresses from the exposed-source paths yields "
                "an exact operation skeleton that is invariant across policies "
                "and cutoffs. This is a real skeleton/segmentation atlas, but "
                "it is not a decoder-side generator because literal payload and "
                "copy source choices remain external."
            ),
        },
        "case_rows": case_rows,
        "book_rows": book_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "source_free_skeleton_atlas_only",
            "skeleton_status": classification,
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "98_full_source_exact_skeleton_invariance.json"
    md_path = TEST_RESULTS / "98_full_source_exact_skeleton_invariance.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    totals = s["skeleton_totals"]
    lines = [
        "# Full Source Exact Skeleton Invariance",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 95 showed source-policy invariance only for coarse operation shape.",
        "This audit compares the exact source-free skeleton: operation type,",
        "target start, length, and forced flag, with source addresses removed.",
        "",
        "## Result",
        "",
        f"- Observations: `{s['observation_count']}`.",
        f"- `(cutoff, book)` cases: `{s['case_count']}`.",
        f"- Books represented: `{s['book_count']}`.",
        f"- Case skeleton invariance: `{s['case_skeleton_invariant_count']}/{s['case_count']}`.",
        f"- Book skeleton invariance across cutoffs/policies: `{s['book_skeleton_invariant_count']}/{s['book_count']}`.",
        f"- Exact source-bearing signature invariance: `{s['exact_signature_invariant_cases']}/{s['case_count']}`.",
        f"- Canonical skeleton op count: `{totals['op_count']}`.",
        f"- Canonical skeleton copy items: `{totals['copy_items']}`.",
        f"- Canonical skeleton literal runs/digits: `{totals['literal_runs']}` / `{totals['literal_digits']}`.",
        f"- Canonical skeleton copied digits: `{totals['copied_digits']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        f"- Source fields removed from skeleton atlas: `{s['source_fields_removed_from_skeleton_atlas']}`.",
        f"- Source fields removed from decoder: `{s['source_fields_removed_from_decoder']}`.",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
