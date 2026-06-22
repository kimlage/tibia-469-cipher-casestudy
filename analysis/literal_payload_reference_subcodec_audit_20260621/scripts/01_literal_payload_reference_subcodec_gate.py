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

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
LITERAL_PAYLOAD_LEDGER = (
    ROOT
    / "analysis"
    / "literal_payload_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_literal_payload_ledger.json"
)
SKELETON_AMBIGUITY = (
    ROOT
    / "analysis"
    / "skeleton_decoder_ambiguity_audit_20260621"
    / "reports"
    / "test_results"
    / "01_skeleton_decoder_ambiguity_gate.json"
)

OUT_STEM = "01_literal_payload_reference_subcodec_gate"
SEED_BOOKS = list(range(10))
RANDOM_TRIALS = 500
RANDOM_SEED = 46920260621


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


def reconstruct_skeleton() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_literal_payload_ref", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def find_occurrences(haystack: str, needle: str) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return out
        out.append(index)
        start = index + 1


def log2_choice_count(count: int) -> float:
    if count <= 1:
        return 0.0
    return math.log2(count)


def extract_literal_rows(
    books: dict[int, str],
    skeleton_by_book: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    emitted = "".join(books[index] for index in SEED_BOOKS)
    rows: list[dict[str, Any]] = []
    for book in sorted(skeleton_by_book):
        if book < 10:
            continue
        target = books[book]
        local = ""
        for op_index, op in enumerate(skeleton_by_book[book]):
            start = int(op["target_start"])
            length = int(op["length"])
            if len(local) != start:
                raise RuntimeError({"book": book, "op_index": op_index, "local_len": len(local), "start": start})
            chunk = target[start : start + length]
            available = emitted + local
            if len(chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_chunk"})
            if op["type"] == "literal":
                legal_source_count = max(0, len(available) - length + 1)
                occurrences = find_occurrences(available, chunk)
                raw_bits = length * math.log2(10)
                source_bits = log2_choice_count(legal_source_count)
                reference_possible = bool(occurrences)
                reference_without_mode_bits = (
                    source_bits if reference_possible else float("inf")
                )
                rows.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "target_start": start,
                        "length": length,
                        "payload": chunk,
                        "available_len": len(available),
                        "legal_source_count": legal_source_count,
                        "prior_occurrence_count": len(occurrences),
                        "earliest_occurrence": occurrences[0] if occurrences else None,
                        "raw_bits": raw_bits,
                        "reference_source_bits": reference_without_mode_bits,
                        "reference_saves_without_mode": (
                            reference_possible and reference_without_mode_bits < raw_bits
                        ),
                    }
                )
            local += chunk
        if local != target:
            raise RuntimeError({"book": book, "type": "roundtrip_failed"})
        emitted += target
    return rows


def score_rows(rows: list[dict[str, Any]], *, charge_mode_bits: bool) -> dict[str, Any]:
    raw_bits = sum(float(row["raw_bits"]) for row in rows)
    mode_bits = len(rows) if charge_mode_bits else 0
    selected = []
    total = mode_bits
    for row in rows:
        raw = float(row["raw_bits"])
        ref = float(row["reference_source_bits"])
        use_ref = ref < raw
        if use_ref:
            total += ref
            selected.append(row)
        else:
            total += raw
    return {
        "raw_bits": raw_bits,
        "charge_mode_bits": charge_mode_bits,
        "mode_bits": mode_bits,
        "selected_reference_count": len(selected),
        "selected_reference_digits": sum(int(row["length"]) for row in selected),
        "selected_reference_source_bits": sum(
            float(row["reference_source_bits"]) for row in selected
        ),
        "total_bits": total,
        "delta_vs_raw_bits": total - raw_bits,
        "selected_rows": selected,
    }


def random_digit_string(rng: random.Random, length: int) -> str:
    return "".join(str(rng.randrange(10)) for _ in range(length))


def random_control_rows(template_rows: list[dict[str, Any]], seed_text: str, rng: random.Random) -> list[dict[str, Any]]:
    emitted = seed_text
    rows = []
    for template in template_rows:
        length = int(template["length"])
        chunk = random_digit_string(rng, length)
        legal_source_count = max(0, len(emitted) - length + 1)
        occurrences = find_occurrences(emitted, chunk)
        raw_bits = length * math.log2(10)
        source_bits = log2_choice_count(legal_source_count)
        rows.append(
            {
                "length": length,
                "payload": chunk,
                "available_len": len(emitted),
                "legal_source_count": legal_source_count,
                "prior_occurrence_count": len(occurrences),
                "raw_bits": raw_bits,
                "reference_source_bits": source_bits if occurrences else float("inf"),
            }
        )
        emitted += chunk
    return rows


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def run_controls(rows: list[dict[str, Any]], seed_text: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    deltas = []
    ref_counts = []
    ref_digits = []
    for _ in range(RANDOM_TRIALS):
        random_rows = random_control_rows(rows, seed_text, rng)
        score = score_rows(random_rows, charge_mode_bits=True)
        deltas.append(float(score["delta_vs_raw_bits"]))
        ref_counts.append(int(score["selected_reference_count"]))
        ref_digits.append(int(score["selected_reference_digits"]))
    return {
        "trials": RANDOM_TRIALS,
        "seed": RANDOM_SEED,
        "delta_mean": mean(deltas),
        "delta_min": min(deltas),
        "delta_p05": percentile(deltas, 5),
        "delta_p50": percentile(deltas, 50),
        "delta_p95": percentile(deltas, 95),
        "delta_max": max(deltas),
        "reference_count_mean": mean(ref_counts),
        "reference_count_max": max(ref_counts),
        "reference_digit_mean": mean(ref_digits),
        "reference_digit_max": max(ref_digits),
    }


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    c = data["controls"]
    lines = [
        "# Literal Payload Reference Subcodec Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether literal payload chunks that already occurred in emitted text",
        "can be replaced by declared prior references after paying mode/source cost.",
        "",
        "## Summary",
        "",
        f"- Literal chunks/digits: `{s['literal_chunk_count']}` / `{s['literal_digit_count']}`.",
        f"- Chunks with prior occurrence: `{s['prior_occurrence_rows']}`.",
        f"- Prior-occurrence digits: `{s['prior_occurrence_digits']}`.",
        f"- Raw uniform payload bits: `{s['raw_bits']:.3f}`.",
        f"- Beneficial references before mode cost: `{s['beneficial_reference_count_without_mode']}` chunks / `{s['beneficial_reference_digits_without_mode']}` digits.",
        f"- No-mode reference delta: `{s['no_mode_delta_vs_raw_bits']:.3f}` bits.",
        f"- Charged reference delta: `{s['charged_delta_vs_raw_bits']:.3f}` bits.",
        f"- Charged selected references: `{s['charged_selected_reference_count']}` chunks / `{s['charged_selected_reference_digits']}` digits.",
        "",
        "## Random Controls",
        "",
        f"- Trials: `{c['trials']}`.",
        f"- Charged delta mean/min/p05/p50/p95/max: `{c['delta_mean']:.3f}` / `{c['delta_min']:.3f}` / `{c['delta_p05']:.3f}` / `{c['delta_p50']:.3f}` / `{c['delta_p95']:.3f}` / `{c['delta_max']:.3f}`.",
        f"- Reference count mean/max: `{c['reference_count_mean']:.3f}` / `{c['reference_count_max']}`.",
        f"- Reference digit mean/max: `{c['reference_digit_mean']:.3f}` / `{c['reference_digit_max']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes literal payload reference subcodec: `{s['promotes_literal_payload_reference_subcodec']}`.",
        "- Prior whole-chunk recurrence is diagnostic only unless it beats raw payload after mode/source cost and controls.",
        "- Literal payload remains a declared dependency.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    ledger = load_json(LITERAL_PAYLOAD_LEDGER)
    ambiguity = load_json(SKELETON_AMBIGUITY)
    assert_boundary("literal_payload_ledger", ledger)
    assert_boundary("skeleton_decoder_ambiguity", ambiguity)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    skeleton = reconstruct_skeleton()
    rows = extract_literal_rows(books, skeleton)
    seed_text = "".join(books[index] for index in SEED_BOOKS)
    no_mode_score = score_rows(rows, charge_mode_bits=False)
    charged_score = score_rows(rows, charge_mode_bits=True)
    controls = run_controls(rows, seed_text)
    prior_rows = [row for row in rows if int(row["prior_occurrence_count"]) > 0]
    beneficial_no_mode = [
        row for row in rows if bool(row["reference_saves_without_mode"])
    ]
    promotes = (
        float(charged_score["delta_vs_raw_bits"]) < 0
        and float(charged_score["delta_vs_raw_bits"]) < float(controls["delta_p05"])
    )
    summary = {
        "literal_chunk_count": len(rows),
        "literal_digit_count": sum(int(row["length"]) for row in rows),
        "prior_occurrence_rows": len(prior_rows),
        "prior_occurrence_digits": sum(int(row["length"]) for row in prior_rows),
        "raw_bits": float(charged_score["raw_bits"]),
        "beneficial_reference_count_without_mode": len(beneficial_no_mode),
        "beneficial_reference_digits_without_mode": sum(
            int(row["length"]) for row in beneficial_no_mode
        ),
        "no_mode_total_bits": float(no_mode_score["total_bits"]),
        "no_mode_delta_vs_raw_bits": float(no_mode_score["delta_vs_raw_bits"]),
        "charged_total_bits": float(charged_score["total_bits"]),
        "charged_delta_vs_raw_bits": float(charged_score["delta_vs_raw_bits"]),
        "charged_selected_reference_count": int(charged_score["selected_reference_count"]),
        "charged_selected_reference_digits": int(charged_score["selected_reference_digits"]),
        "promotes_literal_payload_reference_subcodec": promotes,
        "interpretation": (
            "Whole-chunk recurrence inside literal payload is tested as a "
            "declared-reference subcodec. Promotion requires the charged model "
            "to beat raw payload and random same-length controls."
        ),
    }
    data = {
        "schema": "literal_payload_reference_subcodec_gate.v1",
        "classification": (
            "literal_payload_reference_subcodec_promoted"
            if promotes
            else "literal_payload_reference_subcodec_rejected"
        ),
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "literal_payload_ledger": rel(LITERAL_PAYLOAD_LEDGER),
            "skeleton_decoder_ambiguity_gate": rel(SKELETON_AMBIGUITY),
        },
        "scope": {
            "analysis_only": True,
            "skeleton_granted": True,
            "literal_payload_subcodec_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": summary,
        "controls": controls,
        "literal_rows": rows,
        "selected_reference_rows": charged_score["selected_rows"],
        "decision": {
            "literal_payload_status": "declared_dependency_retained",
            "compression_bound_status": "unchanged_8154_676268",
            "row0_origin_status": "unchanged_exogenous",
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
