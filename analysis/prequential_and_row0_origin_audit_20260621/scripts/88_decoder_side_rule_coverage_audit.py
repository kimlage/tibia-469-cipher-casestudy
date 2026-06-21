from __future__ import annotations

import importlib.util
import json
import math
import random
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE86_SCRIPT = HERE / "scripts" / "86_global_item_literal_length_control_gate.py"
GATE87 = TEST_RESULTS / "87_stable_path_projection_boundary_audit.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

PROJECTION_MODE = "payload_uniform_no_item_or_literal_length"
RANDOM_SEED = 469
CONTROL_TRIALS = 1000


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


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def stable_projection_rows(gate86_module, gate82_module, gate77_module) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cutoff in gate77_module.CUTOFFS:
        rows.extend(
            gate86_module.run_cutoff(
                cutoff,
                gate77_module,
                gate82_module,
                mode=PROJECTION_MODE,
            )
        )
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    canonical = []
    for book in sorted(by_book):
        book_rows = sorted(by_book[book], key=lambda row: int(row["cutoff"]))
        signatures = {row["signature"] for row in book_rows}
        if len(signatures) != 1:
            raise RuntimeError({"book": book, "type": "unstable_projection", "signatures": signatures})
        canonical.append(book_rows[0])
    return canonical


def target_match_sources(emitted: str, chunk: str) -> list[int]:
    length = len(chunk)
    return [
        index
        for index in range(0, len(emitted) - length + 1)
        if emitted[index : index + length] == chunk
    ]


def collect_copy_rule_rows(
    *,
    canonical_rows: list[dict[str, Any]],
    books: dict[str, str],
    min_len: int,
) -> list[dict[str, Any]]:
    emitted = "".join(books[str(book)] for book in range(10))
    previous_copy_end: int | None = None
    previous_copy_length: int | None = None
    rows: list[dict[str, Any]] = []

    for row in canonical_rows:
        book = int(row["book"])
        target = books[str(book)]
        book_pos = 0
        for op_index, op in enumerate(row["signature_ops"]):
            if op["type"] == "literal":
                length = int(op["length"])
                chunk = target[book_pos : book_pos + length]
                if len(chunk) != length:
                    raise RuntimeError({"book": book, "op_index": op_index, "type": "short_literal"})
                emitted += chunk
                book_pos += length
                continue
            if op["type"] != "copy":
                raise RuntimeError({"book": book, "op_index": op_index, "op": op})

            source = int(op["source"])
            length = int(op["length"])
            remaining = len(target) - book_pos
            if remaining < length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "overrun"})
            target_chunk = target[book_pos : book_pos + length]
            copied = emitted[source : source + length]
            if copied != target_chunk or len(copied) != length:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source": source,
                        "length": length,
                    }
                )
            legal_source_count = max(1, len(emitted) - min_len + 1)
            latest_legal_source = legal_source_count - 1
            decoder_max = min(remaining, len(emitted) - source)
            match_sources = target_match_sources(emitted, target_chunk)
            if source not in match_sources:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "not_target_match"})
            previous_end_hit = previous_copy_end is not None and source == previous_copy_end
            previous_length_hit = previous_copy_length is not None and length == previous_copy_length
            row_out = {
                "book": book,
                "op_index": op_index,
                "book_pos": book_pos,
                "global_target_pos": len(emitted),
                "source": source,
                "length": length,
                "remaining_book_digits": remaining,
                "legal_source_count": legal_source_count,
                "decoder_max_possible_after_declared_source": decoder_max,
                "target_match_source_count": len(match_sources),
                "source_is_zero": source == 0,
                "source_is_previous_copy_end": previous_end_hit,
                "source_is_latest_legal": source == latest_legal_source,
                "source_is_earliest_target_match": source == min(match_sources),
                "source_is_latest_target_match": source == max(match_sources),
                "source_is_unique_target_match": len(match_sources) == 1,
                "length_is_min_len": length == min_len,
                "length_is_previous_copy_length": previous_length_hit,
                "length_is_remaining_book": length == remaining,
                "length_is_decoder_max": length == decoder_max,
                "joint_previous_end_decoder_max": previous_end_hit and length == decoder_max,
                "joint_zero_decoder_max": source == 0 and length == decoder_max,
                "joint_latest_legal_decoder_max": source == latest_legal_source and length == decoder_max,
                "joint_earliest_target_match_decoder_max": source == min(match_sources)
                and length == decoder_max,
                "joint_unique_target_match_decoder_max": len(match_sources) == 1
                and length == decoder_max,
            }
            rows.append(row_out)
            emitted += copied
            book_pos += length
            previous_copy_end = source + length
            previous_copy_length = length
        if book_pos != len(target):
            raise RuntimeError({"book": book, "book_pos": book_pos, "target_length": len(target)})
    return rows


def count(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row[key])


def rule_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "source_is_zero",
        "source_is_previous_copy_end",
        "source_is_latest_legal",
        "source_is_earliest_target_match",
        "source_is_latest_target_match",
        "source_is_unique_target_match",
        "length_is_min_len",
        "length_is_previous_copy_length",
        "length_is_remaining_book",
        "length_is_decoder_max",
        "joint_previous_end_decoder_max",
        "joint_zero_decoder_max",
        "joint_latest_legal_decoder_max",
        "joint_earliest_target_match_decoder_max",
        "joint_unique_target_match_decoder_max",
    ]
    counts = {key: count(rows, key) for key in keys}
    source_rule_keys = [
        "source_is_zero",
        "source_is_previous_copy_end",
        "source_is_latest_legal",
    ]
    length_rule_keys = [
        "length_is_min_len",
        "length_is_previous_copy_length",
        "length_is_remaining_book",
        "length_is_decoder_max",
    ]
    joint_decoder_keys = [
        "joint_previous_end_decoder_max",
        "joint_zero_decoder_max",
        "joint_latest_legal_decoder_max",
    ]
    return {
        "copy_event_count": len(rows),
        "copied_digits": sum(int(row["length"]) for row in rows),
        "counts": counts,
        "best_decoder_side_source_rule": max(
            source_rule_keys, key=lambda key: (counts[key], key)
        ),
        "best_decoder_side_source_rule_hits": max(counts[key] for key in source_rule_keys),
        "best_decoder_side_length_rule": max(
            length_rule_keys, key=lambda key: (counts[key], key)
        ),
        "best_decoder_side_length_rule_hits": max(counts[key] for key in length_rule_keys),
        "best_decoder_side_joint_rule": max(
            joint_decoder_keys, key=lambda key: (counts[key], key)
        ),
        "best_decoder_side_joint_rule_hits": max(counts[key] for key in joint_decoder_keys),
        "target_match_source_count_summary": summarize(
            [float(row["target_match_source_count"]) for row in rows]
        ),
        "legal_source_count_summary": summarize(
            [float(row["legal_source_count"]) for row in rows]
        ),
        "decoder_max_minus_length_summary": summarize(
            [
                float(row["decoder_max_possible_after_declared_source"] - row["length"])
                for row in rows
            ]
        ),
    }


def controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    lengths = [int(row["length"]) for row in rows]
    decoder_maxes = [
        int(row["decoder_max_possible_after_declared_source"]) for row in rows
    ]
    previous_end_hits = []
    zero_hits = []
    latest_hits = []
    decoder_length_hits = []
    for _ in range(CONTROL_TRIALS):
        previous = 0
        zero = 0
        latest = 0
        for row in rows:
            legal = int(row["legal_source_count"])
            source = rng.randrange(legal)
            if row["source_is_previous_copy_end"] and source == int(row["source"]):
                previous += 1
            if source == 0:
                zero += 1
            if source == legal - 1:
                latest += 1
        shuffled = lengths[:]
        rng.shuffle(shuffled)
        decoder_length_hits.append(
            sum(1 for length, maximum in zip(shuffled, decoder_maxes) if length == maximum)
        )
        previous_end_hits.append(previous)
        zero_hits.append(zero)
        latest_hits.append(latest)

    observed_previous = count(rows, "source_is_previous_copy_end")
    observed_zero = count(rows, "source_is_zero")
    observed_latest = count(rows, "source_is_latest_legal")
    observed_decoder = count(rows, "length_is_decoder_max")
    return {
        "seed": RANDOM_SEED,
        "trials": CONTROL_TRIALS,
        "random_source_previous_end_hit_summary": summarize(previous_end_hits),
        "random_source_zero_hit_summary": summarize(zero_hits),
        "random_source_latest_hit_summary": summarize(latest_hits),
        "permuted_length_decoder_max_hit_summary": summarize(decoder_length_hits),
        "p_random_previous_end_hits_ge_observed": sum(
            1 for value in previous_end_hits if value >= observed_previous
        )
        / CONTROL_TRIALS,
        "p_random_zero_hits_ge_observed": sum(
            1 for value in zero_hits if value >= observed_zero
        )
        / CONTROL_TRIALS,
        "p_random_latest_hits_ge_observed": sum(
            1 for value in latest_hits if value >= observed_latest
        )
        / CONTROL_TRIALS,
        "p_permuted_decoder_max_hits_ge_observed": sum(
            1 for value in decoder_length_hits if value >= observed_decoder
        )
        / CONTROL_TRIALS,
    }


def make_result() -> dict[str, Any]:
    gate87 = load_json(GATE87)
    assert_boundary("stable_path_projection_boundary_audit", gate87)
    if gate87["classification"] != "stable_path_projection_boundary_only":
        raise RuntimeError("gate87 boundary changed")

    gate86_module = load_module("gate86_for_gate88", GATE86_SCRIPT)
    gate82_module = gate86_module.load_module(
        "gate82_for_gate88",
        gate86_module.GATE82_SCRIPT,
    )
    gate77_module = gate82_module.load_module(
        "gate77_for_gate88",
        gate82_module.GATE77_SCRIPT,
    )
    context = gate77_module.load_parser_context_for_cutoff(10)
    min_len = int(context["formula"]["policy"]["min_len"])
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}

    start = time.perf_counter()
    canonical_rows = stable_projection_rows(gate86_module, gate82_module, gate77_module)
    copy_rows = collect_copy_rule_rows(
        canonical_rows=canonical_rows,
        books=books,
        min_len=min_len,
    )
    elapsed = time.perf_counter() - start
    rules = rule_summary(copy_rows)
    control_rows = controls(copy_rows)
    decoder_joint_covers_all = (
        rules["best_decoder_side_joint_rule_hits"] == rules["copy_event_count"]
    )
    literal_payload_remaining = gate87["dependency_counts"][
        "materialized_literal_payload_digit_fields"
    ]
    promotes_generator = decoder_joint_covers_all and literal_payload_remaining == 0
    classification = (
        "decoder_side_rule_covers_projection"
        if promotes_generator
        else "decoder_side_rule_coverage_insufficient"
    )

    return {
        "schema": "decoder_side_rule_coverage_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate87": rel(GATE87),
            "gate86_script": rel(GATE86_SCRIPT),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "projection_mode": PROJECTION_MODE,
            "decoder_side_rules_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "projection_copy_event_count": rules["copy_event_count"],
            "projection_copied_digits": rules["copied_digits"],
            "literal_payload_digits_still_materialized": literal_payload_remaining,
            "best_decoder_side_source_rule": rules["best_decoder_side_source_rule"],
            "best_decoder_side_source_rule_hits": rules[
                "best_decoder_side_source_rule_hits"
            ],
            "best_decoder_side_length_rule": rules["best_decoder_side_length_rule"],
            "best_decoder_side_length_rule_hits": rules[
                "best_decoder_side_length_rule_hits"
            ],
            "best_decoder_side_joint_rule": rules["best_decoder_side_joint_rule"],
            "best_decoder_side_joint_rule_hits": rules[
                "best_decoder_side_joint_rule_hits"
            ],
            "decoder_joint_covers_all": decoder_joint_covers_all,
            "promotes_generator": promotes_generator,
            "interpretation": (
                "Simple decoder-side source and length rules explain only part "
                "of the stable projection. The projection remains target-text "
                "dependent unless copy source, copy length, and literal payload "
                "can be generated without oracle access."
            ),
        },
        "rule_summary": rules,
        "controls": control_rows,
        "sample_failures": [
            {
                key: row[key]
                for key in [
                    "book",
                    "op_index",
                    "book_pos",
                    "source",
                    "length",
                    "legal_source_count",
                    "decoder_max_possible_after_declared_source",
                    "target_match_source_count",
                ]
            }
            for row in copy_rows
            if not row[rules["best_decoder_side_joint_rule"]]
        ][:25],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "decoder_side_rule_coverage_insufficient",
            "source_length_parser_status": "target_text_dependency_not_removed",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "88_decoder_side_rule_coverage_audit.json"
    md_path = TEST_RESULTS / "88_decoder_side_rule_coverage_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    controls_out = result["controls"]
    counts = result["rule_summary"]["counts"]
    lines = [
        "# Decoder-Side Rule Coverage Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 87 showed that the stable path projection still uses target text.",
        "This audit tests simple decoder-side rules for the projection copy",
        "sources and lengths, with negative controls for random legal sources and",
        "permuted lengths.",
        "",
        "## Coverage",
        "",
        f"- Projection copy events: `{s['projection_copy_event_count']}`.",
        f"- Projection copied digits: `{s['projection_copied_digits']}`.",
        f"- Literal payload digits still materialized: `{s['literal_payload_digits_still_materialized']}`.",
        f"- Best decoder-side source rule: `{s['best_decoder_side_source_rule']}` = `{s['best_decoder_side_source_rule_hits']}/{s['projection_copy_event_count']}`.",
        f"- Best decoder-side length rule: `{s['best_decoder_side_length_rule']}` = `{s['best_decoder_side_length_rule_hits']}/{s['projection_copy_event_count']}`.",
        f"- Best decoder-side joint rule: `{s['best_decoder_side_joint_rule']}` = `{s['best_decoder_side_joint_rule_hits']}/{s['projection_copy_event_count']}`.",
        f"- Decoder joint rule covers all: `{s['decoder_joint_covers_all']}`.",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        "",
        "## Rule Counts",
        "",
        "| Rule | Hits |",
        "|---|---:|",
    ]
    for key in sorted(counts):
        lines.append(f"| `{key}` | `{counts[key]}` |")
    lines.extend(
        [
            "",
            "## Controls",
            "",
            f"- Previous-end source p-value: `{controls_out['p_random_previous_end_hits_ge_observed']:.4f}`.",
            f"- Zero source p-value: `{controls_out['p_random_zero_hits_ge_observed']:.4f}`.",
            f"- Latest-legal source p-value: `{controls_out['p_random_latest_hits_ge_observed']:.4f}`.",
            f"- Decoder-max length p-value: `{controls_out['p_permuted_decoder_max_hits_ge_observed']:.4f}`.",
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
            "- Row0 remains unchanged and exogenous.",
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
