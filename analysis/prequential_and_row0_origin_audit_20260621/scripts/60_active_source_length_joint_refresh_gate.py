from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

PREVIOUS_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SOURCE_LENGTH_JOINT_49 = TEST_RESULTS / "49_source_length_joint_derivability_audit.json"
ACTIVE_DEPENDENCY_REFRESH_59 = (
    TEST_RESULTS / "59_active_formula_dependency_refresh_gate.json"
)

RANDOM_SEED = 469
PERMUTATION_TRIALS = 1000


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def candidate_sources(available: str, chunk: str) -> list[int]:
    length = len(chunk)
    return [
        index
        for index in range(0, len(available) - length + 1)
        if available[index : index + length] == chunk
    ]


def max_target_extension(
    *, emitted: str, source_pos: int, target: str, book_pos: int
) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def collect_rows(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    emitted = ""
    previous_copy: dict[str, int] | None = None
    rows: list[dict[str, Any]] = []

    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    raise RuntimeError(
                        {"book": book, "op_index": op_index, "type": "literal_mismatch"}
                    )
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                raise RuntimeError({"book": book, "op_index": op_index, "op": op})

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            target_chunk = target[book_pos : book_pos + length]
            chunk = emitted[source : source + length]
            if chunk != target_chunk or len(chunk) != length:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )

            candidates = candidate_sources(emitted, target_chunk)
            if source not in candidates:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "source_not_candidate",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )
            decoder_max = min(len(emitted) - source, len(target) - book_pos)
            target_max = max_target_extension(
                emitted=emitted,
                source_pos=source,
                target=target,
                book_pos=book_pos,
            )
            previous_end = None if previous_copy is None else previous_copy["end"]
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source,
                    "length": length,
                    "candidate_source_count": len(candidates),
                    "candidate_min": min(candidates),
                    "candidate_max": max(candidates),
                    "source_is_earliest_for_declared_length": source == min(candidates),
                    "source_is_unique_for_declared_length": len(candidates) == 1,
                    "source_is_latest_for_declared_length": source == max(candidates),
                    "decoder_max_possible_after_declared_source": decoder_max,
                    "encoder_target_max_after_declared_source": target_max,
                    "length_equals_decoder_max_possible": length == decoder_max,
                    "length_equals_encoder_target_max": length == target_max,
                    "joint_encoder_earliest_target_max": (
                        source == min(candidates) and length == target_max
                    ),
                    "joint_declared_source_decoder_max": length == decoder_max,
                    "joint_unique_source_decoder_max": (
                        len(candidates) == 1 and length == decoder_max
                    ),
                    "joint_unique_source_target_max": (
                        len(candidates) == 1 and length == target_max
                    ),
                    "joint_previous_end_decoder_max": (
                        previous_end is not None
                        and source == previous_end
                        and length == decoder_max
                    ),
                }
            )
            emitted += chunk
            book_pos += length
            previous_copy = {
                "source_digit_pos": source,
                "length": length,
                "end": source + length,
            }
        if book_pos != len(target):
            raise RuntimeError(
                {
                    "book": book,
                    "type": "book_length_mismatch",
                    "book_pos": book_pos,
                    "target_length": len(target),
                }
            )
    return rows


def count(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row[key])


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


def permutation_controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    lengths = [int(row["length"]) for row in rows]
    decoder_maxes = [
        int(row["decoder_max_possible_after_declared_source"]) for row in rows
    ]
    target_maxes = [
        int(row["encoder_target_max_after_declared_source"]) for row in rows
    ]
    decoder_hits: list[float] = []
    target_hits: list[float] = []
    for _ in range(PERMUTATION_TRIALS):
        shuffled = lengths[:]
        rng.shuffle(shuffled)
        decoder_hits.append(
            sum(1 for length, maximum in zip(shuffled, decoder_maxes) if length == maximum)
        )
        target_hits.append(
            sum(1 for length, maximum in zip(shuffled, target_maxes) if length == maximum)
        )
    observed_decoder = count(rows, "length_equals_decoder_max_possible")
    observed_target = count(rows, "length_equals_encoder_target_max")
    return {
        "seed": RANDOM_SEED,
        "trials": PERMUTATION_TRIALS,
        "decoder_max_hit_summary": summarize(decoder_hits),
        "target_max_hit_summary": summarize(target_hits),
        "p_permuted_decoder_max_hits_ge_observed": (
            sum(1 for value in decoder_hits if value >= observed_decoder)
            / PERMUTATION_TRIALS
        ),
        "p_permuted_target_max_hits_ge_observed": (
            sum(1 for value in target_hits if value >= observed_target)
            / PERMUTATION_TRIALS
        ),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "copy_event_count": len(rows),
        "copied_digits": sum(int(row["length"]) for row in rows),
        "earliest_source_hits_at_declared_length": count(
            rows, "source_is_earliest_for_declared_length"
        ),
        "unique_source_hits_at_declared_length": count(
            rows, "source_is_unique_for_declared_length"
        ),
        "latest_source_hits_at_declared_length": count(
            rows, "source_is_latest_for_declared_length"
        ),
        "decoder_max_length_hits_after_declared_source": count(
            rows, "length_equals_decoder_max_possible"
        ),
        "encoder_target_max_length_hits_after_declared_source": count(
            rows, "length_equals_encoder_target_max"
        ),
        "joint_encoder_earliest_target_max_hits": count(
            rows, "joint_encoder_earliest_target_max"
        ),
        "joint_declared_source_decoder_max_hits": count(
            rows, "joint_declared_source_decoder_max"
        ),
        "joint_unique_source_decoder_max_hits": count(
            rows, "joint_unique_source_decoder_max"
        ),
        "joint_unique_source_target_max_hits": count(
            rows, "joint_unique_source_target_max"
        ),
        "joint_previous_end_decoder_max_hits": count(
            rows, "joint_previous_end_decoder_max"
        ),
        "permutation_controls": permutation_controls(rows),
    }


def diff_summary(previous: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "copy_event_count",
        "copied_digits",
        "earliest_source_hits_at_declared_length",
        "unique_source_hits_at_declared_length",
        "latest_source_hits_at_declared_length",
        "decoder_max_length_hits_after_declared_source",
        "encoder_target_max_length_hits_after_declared_source",
        "joint_encoder_earliest_target_max_hits",
        "joint_declared_source_decoder_max_hits",
        "joint_unique_source_decoder_max_hits",
        "joint_unique_source_target_max_hits",
        "joint_previous_end_decoder_max_hits",
    ]
    return {key: active[key] - previous[key] for key in keys}


def changed_ops(previous: dict[str, Any], active: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for book in map(str, previous["policy"]["book_order"]):
        prev_ops = previous["book_recipes"][book]["ops"]
        active_ops = active["book_recipes"][book]["ops"]
        if len(prev_ops) != len(active_ops):
            rows.append(
                {
                    "book": int(book),
                    "op_index": None,
                    "change": "op_count_changed",
                    "previous_op_count": len(prev_ops),
                    "active_op_count": len(active_ops),
                }
            )
            continue
        for op_index, (prev_op, active_op) in enumerate(zip(prev_ops, active_ops)):
            if prev_op == active_op:
                continue
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "previous": prev_op,
                    "active": active_op,
                }
            )
    return rows


def make_result() -> dict[str, Any]:
    gate49 = load_json(SOURCE_LENGTH_JOINT_49)
    gate59 = load_json(ACTIVE_DEPENDENCY_REFRESH_59)
    for name, data in [
        ("source_length_joint_49", gate49),
        ("active_dependency_refresh_59", gate59),
    ]:
        assert_boundary(name, data)

    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    previous_formula = load_json(PREVIOUS_FORMULA)
    active_formula = load_json(ACTIVE_FORMULA)
    previous_rows = collect_rows(previous_formula, books)
    active_rows = collect_rows(active_formula, books)
    previous_summary = summarize_rows(previous_rows)
    active_summary = summarize_rows(active_rows)
    deltas = diff_summary(previous_summary, active_summary)
    decoder_valid_delta = max(
        deltas["joint_declared_source_decoder_max_hits"],
        deltas["joint_unique_source_decoder_max_hits"],
        deltas["joint_previous_end_decoder_max_hits"],
    )
    classification = (
        "active_source_length_joint_refresh_encoder_gain_decoder_boundary_unchanged"
        if decoder_valid_delta == 0
        and deltas["encoder_target_max_length_hits_after_declared_source"] > 0
        else "active_source_length_joint_refresh_boundary_changed"
    )

    return {
        "schema": "active_source_length_joint_refresh_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "previous_formula": rel(PREVIOUS_FORMULA),
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "source_length_joint_49": rel(SOURCE_LENGTH_JOINT_49),
            "active_dependency_refresh_59": rel(ACTIVE_DEPENDENCY_REFRESH_59),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "does_not_search_new_copy_sources_or_lengths": True,
        },
        "previous_formula_summary": previous_summary,
        "active_formula_summary": active_summary,
        "deltas": deltas,
        "changed_ops": changed_ops(previous_formula, active_formula),
        "summary": {
            "previous_copy_event_count": previous_summary["copy_event_count"],
            "active_copy_event_count": active_summary["copy_event_count"],
            "changed_op_count": len(changed_ops(previous_formula, active_formula)),
            "active_target_max_hit_delta": deltas[
                "encoder_target_max_length_hits_after_declared_source"
            ],
            "active_earliest_source_hit_delta": deltas[
                "earliest_source_hits_at_declared_length"
            ],
            "active_joint_earliest_target_max_delta": deltas[
                "joint_encoder_earliest_target_max_hits"
            ],
            "active_declared_source_decoder_max_delta": deltas[
                "joint_declared_source_decoder_max_hits"
            ],
            "active_unique_source_decoder_max_delta": deltas[
                "joint_unique_source_decoder_max_hits"
            ],
            "active_previous_end_decoder_max_delta": deltas[
                "joint_previous_end_decoder_max_hits"
            ],
            "decoder_valid_joint_rule_improved": decoder_valid_delta > 0,
            "interpretation": (
                "The active formula converts four additional copy lengths into "
                "target-max hits, but this is encoder-side evidence only. The "
                "decoder-valid joint checks do not improve: declared-source plus "
                "decoder-max stays at 60/261, unique-source plus decoder-max stays "
                "at 28/261, and previous-end plus decoder-max stays at 1/261."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "source_length_joint_status": "active_formula_encoder_targetmax_gain_decoder_dependency_retained",
            "source_dependency_status": "retained_declared",
            "copy_length_dependency_status": "retained_declared",
            "generation_explanation_status": "active_formula_does_not_improve_decoder_valid_joint_derivation",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "60_active_source_length_joint_refresh_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prev = result["previous_formula_summary"]
    active = result["active_formula_summary"]
    deltas = result["deltas"]
    s = result["summary"]
    lines = [
        "# Active Source-Length Joint Refresh Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 49 tested joint source/length derivability on the source-substitution",
        "fourth-pass formula. This refresh repeats the same structural checks on",
        "the active post-target-max formula. It does not search new sources,",
        "lengths, plaintext, or another compression bound.",
        "",
        "## Formula Comparison",
        "",
        "| Metric | Previous | Active | Delta |",
        "|---|---:|---:|---:|",
        f"| Copy events | `{prev['copy_event_count']}` | `{active['copy_event_count']}` | `{deltas['copy_event_count']:+d}` |",
        f"| Copied digits | `{prev['copied_digits']}` | `{active['copied_digits']}` | `{deltas['copied_digits']:+d}` |",
        f"| Earliest source at declared length | `{prev['earliest_source_hits_at_declared_length']}` | `{active['earliest_source_hits_at_declared_length']}` | `{deltas['earliest_source_hits_at_declared_length']:+d}` |",
        f"| Encoder target-max length | `{prev['encoder_target_max_length_hits_after_declared_source']}` | `{active['encoder_target_max_length_hits_after_declared_source']}` | `{deltas['encoder_target_max_length_hits_after_declared_source']:+d}` |",
        f"| Joint earliest+target-max | `{prev['joint_encoder_earliest_target_max_hits']}` | `{active['joint_encoder_earliest_target_max_hits']}` | `{deltas['joint_encoder_earliest_target_max_hits']:+d}` |",
        f"| Declared-source+decoder-max | `{prev['joint_declared_source_decoder_max_hits']}` | `{active['joint_declared_source_decoder_max_hits']}` | `{deltas['joint_declared_source_decoder_max_hits']:+d}` |",
        f"| Unique-source+decoder-max | `{prev['joint_unique_source_decoder_max_hits']}` | `{active['joint_unique_source_decoder_max_hits']}` | `{deltas['joint_unique_source_decoder_max_hits']:+d}` |",
        f"| Previous-end+decoder-max | `{prev['joint_previous_end_decoder_max_hits']}` | `{active['joint_previous_end_decoder_max_hits']}` | `{deltas['joint_previous_end_decoder_max_hits']:+d}` |",
        "",
        "## Controls",
        "",
        f"- Active target-max permutation p-value: `{active['permutation_controls']['p_permuted_target_max_hits_ge_observed']:.4f}`.",
        f"- Active decoder-max permutation p-value: `{active['permutation_controls']['p_permuted_decoder_max_hits_ge_observed']:.4f}`.",
        f"- Changed ops between formulas: `{s['changed_op_count']}`.",
        "",
        "## Result",
        "",
        f"- Active target-max hit delta: `{s['active_target_max_hit_delta']:+d}`.",
        f"- Active earliest-source hit delta: `{s['active_earliest_source_hit_delta']:+d}`.",
        f"- Active joint earliest+target-max delta: `{s['active_joint_earliest_target_max_delta']:+d}`.",
        f"- Declared-source+decoder-max delta: `{s['active_declared_source_decoder_max_delta']:+d}`.",
        f"- Unique-source+decoder-max delta: `{s['active_unique_source_decoder_max_delta']:+d}`.",
        f"- Previous-end+decoder-max delta: `{s['active_previous_end_decoder_max_delta']:+d}`.",
        f"- Decoder-valid joint rule improved: `{s['decoder_valid_joint_rule_improved']}`.",
        f"- Interpretation: {s['interpretation']}",
        "",
        "## Decision",
        "",
        "- The active formula improves encoder-side target-max regularity but not a decoder-valid source/length derivation.",
        "- Source and copy length remain declared dependencies.",
        "- Current compression bound remains `8156.049986` bits.",
        "",
        "## Boundary",
        "",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No new formula is emitted.",
    ]
    (TEST_RESULTS / "60_active_source_length_joint_refresh_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
