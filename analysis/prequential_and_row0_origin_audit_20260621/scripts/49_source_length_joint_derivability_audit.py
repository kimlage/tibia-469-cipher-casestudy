from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

CURRENT_FORMULA = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SOURCE_SELECTION = TEST_RESULTS / "31_source_selection_derivation_boundary_gate.json"
COPY_LENGTH = TEST_RESULTS / "32_copy_length_derivation_boundary_gate.json"
CURRENT_DEPENDENCY = TEST_RESULTS / "48_current_formula_dependency_scoreboard.json"

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
        raise RuntimeError(f"{name} changed row0 origin status")
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
    min_len = int(formula["policy"]["min_len"])
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
            encoder_target_max = max_target_extension(
                emitted=emitted,
                source_pos=source,
                target=target,
                book_pos=book_pos,
            )
            previous_source = (
                None if previous_copy is None else previous_copy["source_digit_pos"]
            )
            previous_end = None if previous_copy is None else previous_copy["end"]

            candidate_decoder_max_matches = 0
            candidate_target_max_matches = 0
            candidate_joint_target_max_matches = 0
            for candidate in candidates:
                candidate_decoder_max = min(
                    len(emitted) - candidate, len(target) - book_pos
                )
                candidate_target_max = max_target_extension(
                    emitted=emitted,
                    source_pos=candidate,
                    target=target,
                    book_pos=book_pos,
                )
                if length == candidate_decoder_max:
                    candidate_decoder_max_matches += 1
                if length == candidate_target_max:
                    candidate_target_max_matches += 1
                if candidate == min(candidates) and length == candidate_target_max:
                    candidate_joint_target_max_matches += 1

            legal_length_count = max(1, decoder_max - min_len + 1)
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "global_target_pos": len(emitted),
                    "source_digit_pos": source,
                    "length": length,
                    "candidate_source_count": len(candidates),
                    "candidate_min": min(candidates),
                    "candidate_max": max(candidates),
                    "source_is_earliest_for_declared_length": source == min(candidates),
                    "source_is_unique_for_declared_length": len(candidates) == 1,
                    "source_is_latest_for_declared_length": source == max(candidates),
                    "source_is_previous_source": source == previous_source,
                    "source_is_previous_end": source == previous_end,
                    "decoder_max_possible_after_declared_source": decoder_max,
                    "encoder_target_max_after_declared_source": encoder_target_max,
                    "length_equals_decoder_max_possible": length == decoder_max,
                    "length_equals_encoder_target_max": length == encoder_target_max,
                    "joint_declared_source_decoder_max": length == decoder_max,
                    "joint_encoder_earliest_target_max": (
                        source == min(candidates) and length == encoder_target_max
                    ),
                    "joint_encoder_earliest_declared_length": source == min(candidates),
                    "joint_unique_source_decoder_max": (
                        len(candidates) == 1 and length == decoder_max
                    ),
                    "joint_unique_source_target_max": (
                        len(candidates) == 1 and length == encoder_target_max
                    ),
                    "joint_previous_end_decoder_max": (
                        previous_end is not None
                        and source == previous_end
                        and length == decoder_max
                    ),
                    "uniform_candidate_probability": 1.0 / len(candidates),
                    "uniform_candidate_decoder_max_match_probability": (
                        candidate_decoder_max_matches / len(candidates)
                    ),
                    "uniform_candidate_target_max_match_probability": (
                        candidate_target_max_matches / len(candidates)
                    ),
                    "uniform_candidate_earliest_target_max_probability": (
                        candidate_joint_target_max_matches / len(candidates)
                    ),
                    "uniform_legal_length_decoder_max_probability": (
                        1.0 / legal_length_count
                    ),
                    "uniform_legal_length_target_max_probability": (
                        1.0 / legal_length_count
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
    legal_decoder_hits: list[float] = []
    legal_target_hits: list[float] = []
    for _ in range(PERMUTATION_TRIALS):
        shuffled = lengths[:]
        rng.shuffle(shuffled)
        decoder_hits.append(
            sum(1 for length, maximum in zip(shuffled, decoder_maxes) if length == maximum)
        )
        target_hits.append(
            sum(1 for length, maximum in zip(shuffled, target_maxes) if length == maximum)
        )
        legal_decoder_hits.append(
            sum(1 for length, maximum in zip(shuffled, decoder_maxes) if length <= maximum)
        )
        legal_target_hits.append(
            sum(1 for length, maximum in zip(shuffled, target_maxes) if length <= maximum)
        )
    observed_decoder = count(rows, "length_equals_decoder_max_possible")
    observed_target = count(rows, "length_equals_encoder_target_max")
    return {
        "seed": RANDOM_SEED,
        "trials": PERMUTATION_TRIALS,
        "decoder_max_hit_summary": summarize(decoder_hits),
        "target_max_hit_summary": summarize(target_hits),
        "legal_under_decoder_max_summary": summarize(legal_decoder_hits),
        "legal_under_target_max_summary": summarize(legal_target_hits),
        "p_permuted_decoder_max_hits_ge_observed": (
            sum(1 for value in decoder_hits if value >= observed_decoder)
            / PERMUTATION_TRIALS
        ),
        "p_permuted_target_max_hits_ge_observed": (
            sum(1 for value in target_hits if value >= observed_target)
            / PERMUTATION_TRIALS
        ),
    }


def make_result() -> dict[str, Any]:
    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    source_selection = load_json(SOURCE_SELECTION)
    copy_length = load_json(COPY_LENGTH)
    current_dependency = load_json(CURRENT_DEPENDENCY)
    for name, data in [
        ("source_selection", source_selection),
        ("copy_length", copy_length),
        ("current_dependency", current_dependency),
    ]:
        assert_boundary(name, data)

    rows = collect_rows(formula, books)
    copy_event_count = len(rows)
    if copy_event_count != int(source_selection["summary"]["copy_items"]):
        raise RuntimeError("source-selection copy count mismatch")
    if copy_event_count != int(copy_length["summary"]["copy_items"]):
        raise RuntimeError("copy-length copy count mismatch")

    earliest_hits = count(rows, "source_is_earliest_for_declared_length")
    prior_earliest_hits = int(source_selection["summary"]["earliest_source_hits"])
    target_max_hits = count(rows, "length_equals_encoder_target_max")
    decoder_max_hits = count(rows, "length_equals_decoder_max_possible")
    unique_hits = count(rows, "source_is_unique_for_declared_length")
    joint_encoder_hits = count(rows, "joint_encoder_earliest_target_max")
    joint_decoder_source_declared_hits = count(rows, "joint_declared_source_decoder_max")
    joint_unique_decoder_hits = count(rows, "joint_unique_source_decoder_max")
    joint_unique_target_hits = count(rows, "joint_unique_source_target_max")
    previous_end_decoder_hits = count(rows, "joint_previous_end_decoder_max")

    expected = {
        "uniform_candidate_earliest_source_hits": sum(
            row["uniform_candidate_probability"] for row in rows
        ),
        "uniform_candidate_decoder_max_hits": sum(
            row["uniform_candidate_decoder_max_match_probability"] for row in rows
        ),
        "uniform_candidate_target_max_hits": sum(
            row["uniform_candidate_target_max_match_probability"] for row in rows
        ),
        "uniform_candidate_earliest_target_max_hits": sum(
            row["uniform_candidate_earliest_target_max_probability"] for row in rows
        ),
        "uniform_legal_length_decoder_max_hits": sum(
            row["uniform_legal_length_decoder_max_probability"] for row in rows
        ),
        "uniform_legal_length_target_max_hits": sum(
            row["uniform_legal_length_target_max_probability"] for row in rows
        ),
    }
    controls = permutation_controls(rows)

    source_dependency_removed = False
    length_dependency_removed = False
    full_joint_dependency_removed = False
    classification = "source_length_joint_derivation_partial_decoder_dependency_retained"
    if full_joint_dependency_removed:
        classification = "source_length_joint_derivation_promoted"

    return {
        "schema": "source_length_joint_derivability_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "source_selection_boundary": rel(SOURCE_SELECTION),
            "copy_length_boundary": rel(COPY_LENGTH),
            "current_dependency_scoreboard": rel(CURRENT_DEPENDENCY),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
            "tested_question": (
                "Whether copy source and copy length become decoder-derived when "
                "evaluated as a joint dependency instead of separate ledgers."
            ),
        },
        "summary": {
            "copy_event_count": copy_event_count,
            "copied_digits": sum(int(row["length"]) for row in rows),
            "prior_source_boundary_earliest_hits": prior_earliest_hits,
            "earliest_source_hits_at_declared_length": earliest_hits,
            "source_substitution_non_earliest_delta_vs_prior_boundary": (
                prior_earliest_hits - earliest_hits
            ),
            "unique_source_hits_at_declared_length": unique_hits,
            "ambiguous_source_hits_at_declared_length": copy_event_count - unique_hits,
            "decoder_max_length_hits_after_declared_source": decoder_max_hits,
            "encoder_target_max_length_hits_after_declared_source": target_max_hits,
            "joint_encoder_earliest_declared_length_hits": earliest_hits,
            "joint_encoder_earliest_target_max_hits": joint_encoder_hits,
            "joint_declared_source_decoder_max_hits": joint_decoder_source_declared_hits,
            "joint_unique_source_decoder_max_hits": joint_unique_decoder_hits,
            "joint_unique_source_target_max_hits": joint_unique_target_hits,
            "joint_previous_end_decoder_max_hits": previous_end_decoder_hits,
            "source_dependency_removed_by_joint_rule": source_dependency_removed,
            "length_dependency_removed_by_joint_rule": length_dependency_removed,
            "full_joint_dependency_removed": full_joint_dependency_removed,
            "expected_control_hits": expected,
            "permutation_controls": controls,
            "interpretation": (
                "The joint view shows that the latest source-substituted "
                "formula traded away part of the earlier all-earliest source "
                "canonicality. The remaining joint source/length regularity is "
                "still mostly encoder-side and does not turn the pair into a "
                "decoder-known rule. Source remains target-dependent, and the "
                "only decoder-valid length default after a declared source "
                "covers 60 of 261 copy events."
            ),
        },
        "hypotheses": {
            "declared_source_plus_decoder_max_length": {
                "algorithm": (
                    "Decode the declared source, then take the maximum possible "
                    "copy length from that source bounded by emitted text and "
                    "remaining book length."
                ),
                "decoder_valid": True,
                "coverage": f"{joint_decoder_source_declared_hits}/{copy_event_count}",
                "contradictions": copy_event_count - joint_decoder_source_declared_hits,
                "descriptor_cost_status": (
                    "Retains the full source ledger and still needs length "
                    "exceptions; not a full joint derivation."
                ),
            },
            "earliest_source_plus_target_max_length": {
                "algorithm": (
                    "With the future target chunk known, choose the earliest "
                    "source for the declared copied chunk and extend it to the "
                    "maximal target match."
                ),
                "decoder_valid": False,
                "coverage": f"{joint_encoder_hits}/{copy_event_count}",
                "contradictions": copy_event_count - joint_encoder_hits,
                "descriptor_cost_status": (
                    "High coverage but depends on future target text; retained "
                    "as encoder-oracle evidence only."
                ),
            },
            "unique_source_plus_decoder_max_length": {
                "algorithm": (
                    "When the declared-length target chunk has only one source "
                    "candidate, pair that source with decoder max length."
                ),
                "decoder_valid": False,
                "coverage": f"{joint_unique_decoder_hits}/{copy_event_count}",
                "contradictions": copy_event_count - joint_unique_decoder_hits,
                "descriptor_cost_status": (
                    "Uniqueness is evaluated against the future target chunk, "
                    "so it cannot remove source during decoding."
                ),
            },
            "previous_end_plus_decoder_max_length": {
                "algorithm": (
                    "Use previous copy end as a state-only source default and "
                    "take decoder max length."
                ),
                "decoder_valid": True,
                "coverage": f"{previous_end_decoder_hits}/{copy_event_count}",
                "contradictions": copy_event_count - previous_end_decoder_hits,
                "descriptor_cost_status": "Coverage too low for promotion.",
            },
        },
        "rows": rows,
        "decision": {
            "compression_bound_status": "unchanged",
            "source_length_joint_status": "encoder_regularities_coupled_decoder_dependency_retained",
            "source_dependency_status": "retained_declared",
            "copy_length_dependency_status": "retained_declared_with_partial_decoder_default",
            "generation_explanation_status": "joint_dependency_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "49_source_length_joint_derivability_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    controls = s["permutation_controls"]
    expected = s["expected_control_hits"]
    lines = [
        "# Source-Length Joint Derivability Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate tests whether the two remaining copy dependencies, source and",
        "length, become derivable when they are evaluated as a joint pair rather",
        "than as separate ledgers. It is an analysis-only boundary test: no new",
        "formula is emitted and no compression bound is promoted.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Copied digits: `{s['copied_digits']}`.",
        f"- Prior source-boundary earliest-source hits: `{s['prior_source_boundary_earliest_hits']}/{s['copy_event_count']}`.",
        f"- Earliest-source hits at declared length: `{s['earliest_source_hits_at_declared_length']}/{s['copy_event_count']}`.",
        f"- Non-earliest delta after source substitutions: `{s['source_substitution_non_earliest_delta_vs_prior_boundary']}`.",
        f"- Unique / ambiguous source candidates: `{s['unique_source_hits_at_declared_length']}` / `{s['ambiguous_source_hits_at_declared_length']}`.",
        f"- Decoder max-length hits after declared source: `{s['decoder_max_length_hits_after_declared_source']}/{s['copy_event_count']}`.",
        f"- Encoder target-max hits after declared source: `{s['encoder_target_max_length_hits_after_declared_source']}/{s['copy_event_count']}`.",
        f"- Joint encoder earliest+target-max hits: `{s['joint_encoder_earliest_target_max_hits']}/{s['copy_event_count']}`.",
        f"- Joint declared-source+decoder-max hits: `{s['joint_declared_source_decoder_max_hits']}/{s['copy_event_count']}`.",
        f"- Joint unique-source+decoder-max hits: `{s['joint_unique_source_decoder_max_hits']}/{s['copy_event_count']}`.",
        f"- Joint previous-end+decoder-max hits: `{s['joint_previous_end_decoder_max_hits']}/{s['copy_event_count']}`.",
        "",
        "## Controls",
        "",
        f"- Uniform candidate expected earliest-source hits: `{expected['uniform_candidate_earliest_source_hits']:.3f}`.",
        f"- Uniform candidate expected target-max hits: `{expected['uniform_candidate_target_max_hits']:.3f}`.",
        f"- Uniform candidate expected earliest+target-max hits: `{expected['uniform_candidate_earliest_target_max_hits']:.3f}`.",
        f"- Uniform legal-length expected decoder-max hits: `{expected['uniform_legal_length_decoder_max_hits']:.3f}`.",
        f"- Length permutation target-max hit summary: `{controls['target_max_hit_summary']}`.",
        f"- P(permuted target-max hits >= observed): `{controls['p_permuted_target_max_hits_ge_observed']:.4f}`.",
        f"- Length permutation decoder-max hit summary: `{controls['decoder_max_hit_summary']}`.",
        f"- P(permuted decoder-max hits >= observed): `{controls['p_permuted_decoder_max_hits_ge_observed']:.4f}`.",
        "",
        "## Interpretation",
        "",
        "The copy source and length regularities are coupled, but the coupling is",
        "mostly on the encoder side. The latest source-substituted formula no",
        "longer preserves the earlier `261/261` all-earliest source pattern:",
        "current coverage is `251/261`. Most declared lengths are still",
        "target-maximal after the declared source, and the joint earliest+target",
        "max pattern covers `230/261`; neither rule is decoder-valid because both",
        "checks require the future target text. The decoder-valid version that",
        "keeps source declared and derives length as max-possible covers only",
        "`60/261` events, so it does not remove the copy-length ledger. A simple",
        "state-only previous-end joint rule covers `1/261` events.",
        "",
        "## Boundary",
        "",
        "- Source and length remain declared dependencies in the current formula.",
        "- The result sharpens the structural-parser target but does not promote a new formula.",
        "- Compression bound is unchanged.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "49_source_length_joint_derivability_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
