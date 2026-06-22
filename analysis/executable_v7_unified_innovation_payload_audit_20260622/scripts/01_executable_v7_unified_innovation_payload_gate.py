#!/usr/bin/env python3
"""Executable v7 unified innovation payload integration gate.

This gate integrates the promoted unified innovation payload ledger into the
executable decoder contract after v6. The v7 decoder no longer grants seed
books and derived-book literal payload as separate raw tapes. Instead, it
replays one paid innovation stream, splits it into seed books and literal
payload chunks, then runs the existing v6 operation/source/length contract.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v7_unified_innovation_payload_audit_20260622"
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
UNIFIED_PAYLOAD_GATE = (
    ROOT
    / "analysis"
    / "unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_innovation_payload_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v7_unified_innovation_payload_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v7_unified_innovation_payload_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v7_unified_innovation_payload_audit.md"


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


def render_payload_events(events: list[dict[str, Any]]) -> str:
    output: list[str] = []
    for event in events:
        if event["kind"] == "literal":
            output.append(str(event["text"]))
        elif event["kind"] == "copy":
            available = "".join(output)
            source = int(event["source"])
            length = int(event["length"])
            copied = available[source : source + length]
            if len(copied) != length:
                raise RuntimeError({"reason": "payload_copy_short", "event": event})
            output.append(copied)
        else:
            raise RuntimeError({"reason": "unknown_payload_event", "event": event})
    return "".join(output)


def split_payload_stream(stream: str, segments: list[dict[str, Any]]) -> tuple[dict[int, str], dict[str, str], list[dict[str, Any]]]:
    seed_books: dict[int, str] = {}
    literal_payloads: dict[str, str] = {}
    checks = []
    for segment in segments:
        start = int(segment["start"])
        end = int(segment["end"])
        text = stream[start:end]
        label = str(segment["label"])
        kind = str(segment["kind"])
        checks.append(
            {
                "end": end,
                "kind": kind,
                "label": label,
                "length": len(text),
                "matches_recorded_segment": bool(segment["matches"]),
                "start": start,
            }
        )
        if kind == "seed_book":
            seed_books[int(label.rsplit("_", 1)[1])] = text
        elif kind == "derived_literal":
            literal_payloads[label] = text
        else:
            raise RuntimeError({"reason": "unknown_segment_kind", "segment": segment})
    return seed_books, literal_payloads, checks


def literal_label(row: dict[str, Any]) -> str:
    return f"literal_b{row['book']}_op{row['op_index']}_{row['literal_tape_start']}_{row['literal_tape_end']}"


def grouped_rows(ledger: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in ledger["ledger_rows"]:
        grouped.setdefault(int(row["book"]), []).append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def validate_decoder_roundtrip(seed_books: dict[int, str], literal_payloads: dict[str, str], ledger: dict[str, Any]) -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_rows(ledger)
    emitted = "".join(seed_books[book] for book in range(10))
    exact = 10
    errors = []
    literal_consumed = []
    for book in range(10, 70):
        rendered: list[str] = []
        for row in by_book[book]:
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            if op_type == "literal":
                label = literal_label(row)
                payload = literal_payloads.get(label)
                if payload is None:
                    errors.append({"book": book, "op_index": int(row["op_index"]), "reason": "missing_literal_payload", "label": label})
                    payload = ""
                if len(payload) != length:
                    errors.append({"book": book, "op_index": int(row["op_index"]), "reason": "literal_length_mismatch", "label": label})
                rendered.append(payload)
                literal_consumed.append(label)
                continue
            available = emitted + "".join(rendered)
            source = int(row["copy_source_raw"])
            copied = available[source : source + length]
            expected = books[book][start : start + length]
            if copied != expected:
                errors.append(
                    {
                        "book": book,
                        "op_index": int(row["op_index"]),
                        "reason": "copy_payload_mismatch",
                        "source": source,
                    }
                )
            rendered.append(copied)
        rendered_book = "".join(rendered)
        if rendered_book == books[book]:
            exact += 1
        else:
            errors.append(
                {
                    "book": book,
                    "expected_len": len(books[book]),
                    "reason": "rendered_book_mismatch",
                    "rendered_len": len(rendered_book),
                }
            )
        emitted += rendered_book
    return {
        "errors": errors,
        "exact_books": exact,
        "literal_payloads_consumed": len(literal_consumed),
        "roundtrip_70_70": exact == 70 and not errors,
    }


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    payload = load_json(UNIFIED_PAYLOAD_GATE)
    ledger = load_json(UNIFIED_LEDGER)
    for name, data in [
        ("executable_v6_literal_span_origin_gate", v6),
        ("unified_innovation_payload_gate", payload),
        ("unified_external_tape_ledger", ledger),
    ]:
        assert_boundary(name, data)
    if v6["classification"] != "PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER":
        raise RuntimeError("v6 executable ledger is not promoted")
    if payload["classification"] != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("unified innovation payload ledger is not promoted")

    stream = render_payload_events(payload["event_ledger"])
    seed_books, literal_payloads, segment_checks = split_payload_stream(stream, payload["segments"])
    validation = validate_decoder_roundtrip(seed_books, literal_payloads, ledger)
    v6s = v6["summary"]
    ps = payload["summary"]
    v7_external_total = (
        float(v6s["v6_external_bits_including_seed"])
        - float(v6s["seed_payload_bits"])
        - float(v6s["literal_payload_bits"])
        + float(ps["total_bits_after_declaration"])
    )
    delta_vs_v6 = v7_external_total - float(v6s["v6_external_bits_including_seed"])
    promoted = validation["roundtrip_70_70"] and delta_vs_v6 < 0
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V7_UNIFIED_INNOVATION_PAYLOAD_LEDGER"
            if promoted
            else "executable_v7_unified_innovation_payload_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v7_promoted": promoted,
            "generation_explanation_status": (
                "executable_payload_dependency_reduced_not_source_free_generator"
                if promoted
                else "not_reduced"
            ),
            "next_blocker": (
                "policy/origin for introducing innovation chunks; residual composition, "
                "fallback copy hints, and row0 remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
            "unified_innovation_payload_gate": rel(UNIFIED_PAYLOAD_GATE),
        },
        "payload_segment_checks": segment_checks,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v7_unified_innovation_payload_gate.v1",
        "scope": "analysis_only_executable_v7_unified_innovation_payload",
        "summary": {
            "candidate_v7_external_bits_total_content_included": v7_external_total,
            "copy_bits": float(v6s["copy_bits"]),
            "delta_vs_v6_including_seed": delta_vs_v6,
            "literal_payload_bits_replaced": float(v6s["literal_payload_bits"]),
            "online_x64_coarse_bits": float(v6s["online_x64_coarse_bits"]),
            "payload_replay_bits": float(ps["total_bits_after_declaration"]),
            "payload_replay_copy_ops": int(ps["copy_ops"]),
            "payload_replay_literal_runs": int(ps["literal_runs"]),
            "residual_composition_bits": float(v6s["residual_composition_bits"]),
            "seed_payload_bits_replaced": float(v6s["seed_payload_bits"]),
            "source_class_counts": v6s["class_counts"],
            "v6_external_bits_including_seed": float(v6s["v6_external_bits_including_seed"]),
            "v7_roundtrip_70_70": validation["roundtrip_70_70"],
        },
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v7 Unified Innovation Payload Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Roundtrip: `{result['validation']['exact_books']}/70`.",
        f"- V6 external bits including seed: `{s['v6_external_bits_including_seed']:.3f}`.",
        f"- V7 external bits, content included: `{s['candidate_v7_external_bits_total_content_included']:.3f}`.",
        f"- Delta vs v6: `{s['delta_vs_v6_including_seed']:.3f}` bits.",
        f"- Payload replay bits: `{s['payload_replay_bits']:.3f}`.",
        f"- Replaced seed payload: `{s['seed_payload_bits_replaced']:.3f}`.",
        f"- Replaced literal payload: `{s['literal_payload_bits_replaced']:.3f}`.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is an executable ledger integration. It reduces declared payload "
        "dependency but still uses a target-conditioned innovation replay ledger.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v7 Unified Innovation Payload Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit integrates the promoted unified innovation payload ledger into "
        "the executable decoder contract. Instead of granting seed books `0..9` "
        "and derived literal payloads as separate raw tapes, v7 replays one paid "
        "innovation stream, splits it into seed/literal segments, then runs the "
        "v6 operation/source/length contract.",
        "",
        f"Roundtrip remains `{result['validation']['exact_books']}/70`. External "
        f"bits including seed fall from v6 `{s['v6_external_bits_including_seed']:.3f}` "
        f"to v7 `{s['candidate_v7_external_bits_total_content_included']:.3f}`, "
        f"a reduction of `{-s['delta_vs_v6_including_seed']:.3f}` bits.",
        "",
        f"The replaced fields are seed payload `{s['seed_payload_bits_replaced']:.3f}` "
        f"and literal payload `{s['literal_payload_bits_replaced']:.3f}`. The new "
        f"payload replay costs `{s['payload_replay_bits']:.3f}` bits and consists "
        f"of `{s['payload_replay_copy_ops']}` copy events plus "
        f"`{s['payload_replay_literal_runs']}` literal runs.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This is a real executable dependency reduction, but not a complete "
        "source-free generator. The innovation replay ledger is still "
        "target-conditioned. The next blocker is the policy/origin for innovation "
        "chunk introduction; residual composition, fallback copy hints, and row0 "
        "remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v7_unified_innovation_payload_gate.py](../scripts/01_executable_v7_unified_innovation_payload_gate.py)",
        "- [01_executable_v7_unified_innovation_payload_gate.json](test_results/01_executable_v7_unified_innovation_payload_gate.json)",
        "- [01_executable_v7_unified_innovation_payload_gate.md](test_results/01_executable_v7_unified_innovation_payload_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    if result["translation_delta"] != "NONE":
        raise RuntimeError("translation boundary changed")
    if result["plaintext_claim"] is not False or result["case_reopened"] is not False:
        raise RuntimeError("semantic boundary violated")
    if result["row0_status"] != "unchanged_exogenous":
        raise RuntimeError("row0 boundary changed")
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
