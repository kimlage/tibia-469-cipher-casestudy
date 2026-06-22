#!/usr/bin/env python3
"""V5 mark-identity stream gate.

The near-source-mark audit showed that local offsets are tiny but mark identity
is expensive. This gate asks whether the exact source-mark rank stream itself
has a simple sequential code that can beat the existing copy-hint tape.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "v5_mark_identity_stream_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

NEAR_MARK_SCRIPT = (
    ROOT
    / "analysis"
    / "v5_near_source_mark_offset_audit_20260622"
    / "scripts"
    / "01_v5_near_source_mark_offset_gate.py"
)
NEAR_MARK_GATE = (
    ROOT
    / "analysis"
    / "v5_near_source_mark_offset_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v5_near_source_mark_offset_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_v5_mark_identity_stream_gate.json"
MD_OUT = TEST_RESULTS / "01_v5_mark_identity_stream_gate.md"
FINAL_OUT = FRONT / "reports" / "final_v5_mark_identity_stream_audit.md"


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


def load_near_module() -> Any:
    spec = importlib.util.spec_from_file_location("near_mark_gate", NEAR_MARK_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {NEAR_MARK_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signed_bits(value: int) -> float:
    return math.log2(2 * abs(value) + 1)


def score_models(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    scores = {
        "absolute_rank_plus_offset": 0.0,
        "global_delta_rank_plus_offset": 0.0,
        "book_delta_rank_plus_offset": 0.0,
        "invalid_rank_bucket_plus_offset_lower_bound": 0.0,
    }
    previous_rank = None
    previous_book_rank: tuple[int, int] | None = None
    deltas = []
    ranks = []
    for row in rows:
        rank = int(row["source_mark_recent_rank"])
        offset = int(row["source_offset"])
        offset_bits = signed_bits(offset)
        ranks.append(rank)
        scores["absolute_rank_plus_offset"] += math.log2(rank) + offset_bits
        if previous_rank is None:
            scores["global_delta_rank_plus_offset"] += math.log2(rank) + offset_bits
        else:
            delta = rank - previous_rank
            deltas.append(abs(delta))
            scores["global_delta_rank_plus_offset"] += signed_bits(delta) + offset_bits
        if previous_book_rank is None or previous_book_rank[0] != int(row["book"]):
            scores["book_delta_rank_plus_offset"] += math.log2(rank) + offset_bits
        else:
            scores["book_delta_rank_plus_offset"] += signed_bits(rank - previous_book_rank[1]) + offset_bits
        # This lower bound is not decodable: it pays only the rank bucket, not the exact rank.
        scores["invalid_rank_bucket_plus_offset_lower_bound"] += (
            math.log2(max(1, math.floor(math.log2(rank)) + 1)) + offset_bits
        )
        previous_rank = rank
        previous_book_rank = (int(row["book"]), rank)
    return {
        "copy_hint_bits": hint_bits,
        "delta_abs_median": sorted(deltas)[len(deltas) // 2] if deltas else 0,
        "model_bits": scores,
        "model_deltas_vs_copy_hint": {
            key: value - hint_bits
            for key, value in scores.items()
        },
        "rank_median": sorted(ranks)[len(ranks) // 2] if ranks else 0,
        "rows": len(rows),
    }


def make_result() -> dict[str, Any]:
    near_gate = load_json(NEAR_MARK_GATE)
    assert_boundary("v5_near_source_mark_offset_gate", near_gate)
    near = load_near_module()
    rows = near.collect_fallback_rows()
    scores = score_models(rows)
    best_valid = min(
        (
            (value, key)
            for key, value in scores["model_deltas_vs_copy_hint"].items()
            if not key.startswith("invalid_")
        ),
        key=lambda item: item[0],
    )
    promoted = best_valid[0] < 0
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_V5_MARK_IDENTITY_STREAM_PROGRAM"
            if promoted
            else "V5_MARK_IDENTITY_STREAM_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "next_blocker": "exact source-mark identity remains external; simple rank/delta streams do not beat copy hints",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "v5_near_source_mark_offset_gate": rel(NEAR_MARK_GATE),
            "v5_near_source_mark_offset_script": rel(NEAR_MARK_SCRIPT),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "v5_mark_identity_stream_gate.v1",
        "scope": "analysis_only_v5_mark_identity_stream",
        "summary": scores | {
            "best_valid_delta_vs_copy_hint": best_valid[0],
            "best_valid_model": best_valid[1],
            "promoted": promoted,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# V5 Mark-Identity Stream Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Rows: `{s['rows']}`.",
        f"- Copy-hint bits: `{s['copy_hint_bits']:.3f}`.",
        f"- Source mark rank median: `{s['rank_median']}`.",
        f"- Global rank-delta median: `{s['delta_abs_median']}`.",
        f"- Best valid model: `{s['best_valid_model']}`.",
        f"- Best valid delta vs copy-hint: `{s['best_valid_delta_vs_copy_hint']:.3f}` bits.",
        "",
        "## Model Deltas",
        "",
        "| Model | Bits | Delta vs copy-hint |",
        "| --- | ---: | ---: |",
    ]
    for key, bits in s["model_bits"].items():
        lines.append(
            f"| `{key}` | `{bits:.3f}` | `{s['model_deltas_vs_copy_hint'][key]:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_V5_MARK_IDENTITY_STREAM_PROGRAM`."
                if s["promoted"]
                else "`V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`: valid exact-rank streams remain more expensive than copy-hints."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final V5 Mark-Identity Stream Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether the source-mark identity stream for the `101` v5 "
        "fallback copies can be coded directly, after the near-mark offset audit "
        "showed that local offsets are small.",
        "",
        f"The best valid exact stream is `{s['best_valid_model']}`, but it is "
        f"`{s['best_valid_delta_vs_copy_hint']:.3f}` bits worse than the existing "
        "copy-hint tape. A rank-bucket-plus-offset lower bound is much cheaper, "
        "but it is not decodable because it does not identify the exact mark.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_V5_MARK_IDENTITY_STREAM_PROGRAM`."
            if s["promoted"]
            else "`V5_MARK_IDENTITY_STREAM_NOT_PROMOTED`."
        ),
        "",
        "The remaining copy-origin blocker is exact source-mark identity, not local "
        "offset or a simple sequential rank-delta stream.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_v5_mark_identity_stream_gate.py](../scripts/01_v5_mark_identity_stream_gate.py)",
        "- [01_v5_mark_identity_stream_gate.json](test_results/01_v5_mark_identity_stream_gate.json)",
        "- [01_v5_mark_identity_stream_gate.md](test_results/01_v5_mark_identity_stream_gate.md)",
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
