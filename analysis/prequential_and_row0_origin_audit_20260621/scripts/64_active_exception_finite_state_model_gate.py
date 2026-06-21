from __future__ import annotations

import itertools
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
STOP_RULE_GATE_63 = (
    TEST_RESULTS / "63_active_exception_stop_rule_separability_gate.json"
)

RANDOM_SEED = 469
PERMUTATION_TRIALS = 1000
MAX_FEATURE_ARITY = 3


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


def band(value: int, cuts: tuple[int, ...], labels: tuple[str, ...]) -> str:
    for cut, label in zip(cuts, labels):
        if value <= cut:
            return label
    return labels[-1]


def max_target_extension(
    *, emitted: str, source_pos: int, target: str, book_pos: int
) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def collect_copy_rows(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    emitted = ""
    previous_copy: dict[str, int] | None = None
    previous_exception: bool | None = None
    copies_since_exception: int | None = None
    copy_index = 0
    rows: list[dict[str, Any]] = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        ops = formula["book_recipes"][book]["ops"]
        for op_index, op in enumerate(ops):
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
                raise RuntimeError({"book": book, "op_index": op_index, "type": "bad_op"})

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = emitted[source : source + length]
            target_chunk = target[book_pos : book_pos + length]
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

            decoder_max = min(len(emitted) - source, len(target) - book_pos)
            target_max = max_target_extension(
                emitted=emitted,
                source_pos=source,
                target=target,
                book_pos=book_pos,
            )
            is_exception = target_max > length
            source_distance = len(emitted) - source
            remaining = len(target) - book_pos
            book_ratio = book_pos / len(target) if target else 0.0
            previous_end = None if previous_copy is None else previous_copy["end"]
            previous_length = None if previous_copy is None else previous_copy["length"]
            row = {
                "book": int(book),
                "copy_index": copy_index,
                "op_index": op_index,
                "book_pos": book_pos,
                "book_length": len(target),
                "remaining_before_copy": remaining,
                "source_digit_pos": source,
                "source_distance": source_distance,
                "decoder_max": decoder_max,
                "length": length,
                "target_max": target_max,
                "is_targetmax_exception": is_exception,
                "features": {
                    "book_half": "first" if int(book) < 35 else "second",
                    "book_quartile": band(
                        int(book), (17, 34, 52), ("q1", "q2", "q3", "q4")
                    ),
                    "op_phase": (
                        "op0"
                        if op_index == 0
                        else "op1"
                        if op_index == 1
                        else "op2_3"
                        if op_index <= 3
                        else "op4plus"
                    ),
                    "book_pos_band": (
                        "start"
                        if book_pos == 0
                        else "q1"
                        if book_ratio <= 0.25
                        else "q2"
                        if book_ratio <= 0.50
                        else "q3"
                        if book_ratio <= 0.75
                        else "q4"
                    ),
                    "remaining_band": band(
                        remaining, (10, 25, 50, 100), ("le10", "le25", "le50", "le100", "gt100")
                    ),
                    "source_distance_band": band(
                        source_distance,
                        (20, 50, 100, 500),
                        ("le20", "le50", "le100", "le500", "gt500"),
                    ),
                    "decoder_max_band": band(
                        decoder_max,
                        (10, 20, 50, 100),
                        ("le10", "le20", "le50", "le100", "gt100"),
                    ),
                    "source_previous_end": (
                        "none"
                        if previous_end is None
                        else "yes"
                        if source == previous_end
                        else "no"
                    ),
                    "previous_exception": (
                        "none"
                        if previous_exception is None
                        else "yes"
                        if previous_exception
                        else "no"
                    ),
                    "previous_length_band": (
                        "none"
                        if previous_length is None
                        else band(
                            previous_length,
                            (10, 20, 50, 100),
                            ("le10", "le20", "le50", "le100", "gt100"),
                        )
                    ),
                    "copies_since_exception": (
                        "none"
                        if copies_since_exception is None
                        else band(
                            copies_since_exception,
                            (0, 1, 4),
                            ("zero", "one", "two_to_four", "five_plus"),
                        )
                    ),
                },
            }
            rows.append(row)
            emitted += chunk
            book_pos += length
            previous_copy = {
                "source_digit_pos": source,
                "length": length,
                "end": source + length,
            }
            previous_exception = is_exception
            copies_since_exception = 0 if is_exception else (copies_since_exception or 0) + 1
            copy_index += 1
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


def log2_comb(n: int, k: int) -> float:
    return math.log2(math.comb(n, k))


def kt_bits(contexts: list[tuple[str, ...]], labels: list[bool]) -> float:
    counts: dict[tuple[str, ...], list[int]] = defaultdict(lambda: [0, 0])
    total = 0.0
    for context, label in zip(contexts, labels):
        false_count, true_count = counts[context]
        denom = false_count + true_count + 1.0
        numer = (true_count if label else false_count) + 0.5
        total += -math.log2(numer / denom)
        if label:
            counts[context][1] += 1
        else:
            counts[context][0] += 1
    return total


def context_vectors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = list(rows[0]["features"])
    specs: list[tuple[str, ...]] = []
    for arity in range(1, MAX_FEATURE_ARITY + 1):
        specs.extend(itertools.combinations(names, arity))

    vectors = []
    for spec in specs:
        contexts = [tuple(row["features"][name] for name in spec) for row in rows]
        vectors.append(
            {
                "features": spec,
                "arity": len(spec),
                "contexts": contexts,
                "context_count": len(set(contexts)),
            }
        )
    return vectors


def score_models(
    vectors: list[dict[str, Any]], labels: list[bool], descriptor_bits: float
) -> list[dict[str, Any]]:
    scored = []
    for vector in vectors:
        data_bits = kt_bits(vector["contexts"], labels)
        total_bits = descriptor_bits + data_bits
        positives_by_context: dict[tuple[str, ...], int] = defaultdict(int)
        totals_by_context: dict[tuple[str, ...], int] = defaultdict(int)
        for context, label in zip(vector["contexts"], labels):
            totals_by_context[context] += 1
            if label:
                positives_by_context[context] += 1
        densest_context = max(
            totals_by_context,
            key=lambda context: (
                positives_by_context[context] / totals_by_context[context],
                positives_by_context[context],
                totals_by_context[context],
                context,
            ),
        )
        scored.append(
            {
                "features": list(vector["features"]),
                "arity": vector["arity"],
                "context_count": vector["context_count"],
                "data_bits": data_bits,
                "descriptor_bits": descriptor_bits,
                "total_bits": total_bits,
                "densest_context": list(densest_context),
                "densest_context_positive_count": positives_by_context[densest_context],
                "densest_context_total_count": totals_by_context[densest_context],
                "densest_context_positive_rate": (
                    positives_by_context[densest_context] / totals_by_context[densest_context]
                ),
            }
        )
    return sorted(
        scored,
        key=lambda row: (
            row["total_bits"],
            row["data_bits"],
            row["arity"],
            row["context_count"],
            row["features"],
        ),
    )


def permutation_control(
    vectors: list[dict[str, Any]],
    labels: list[bool],
    descriptor_bits: float,
    observed_best_bits: float,
    explicit_list_bits: float,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    permuted_best_bits = []
    for _ in range(PERMUTATION_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        best = score_models(vectors, shuffled, descriptor_bits)[0]
        permuted_best_bits.append(best["total_bits"])
    sorted_bits = sorted(permuted_best_bits)
    return {
        "seed": RANDOM_SEED,
        "trials": PERMUTATION_TRIALS,
        "best_total_bits_min": min(permuted_best_bits),
        "best_total_bits_median": sorted_bits[len(sorted_bits) // 2],
        "best_total_bits_max": max(permuted_best_bits),
        "p_permuted_total_bits_le_observed": (
            sum(bits <= observed_best_bits for bits in permuted_best_bits)
            / PERMUTATION_TRIALS
        ),
        "p_permuted_improvement_ge_observed": (
            sum(
                (explicit_list_bits - bits)
                >= (explicit_list_bits - observed_best_bits)
                for bits in permuted_best_bits
            )
            / PERMUTATION_TRIALS
        ),
        "permuted_beats_explicit_list_count": sum(
            bits < explicit_list_bits for bits in permuted_best_bits
        ),
    }


def render_markdown(result: dict[str, Any]) -> str:
    s = result["summary"]
    best = s["best_model"]
    control = s["permutation_control"]
    return "\n".join(
        [
            "# Active Exception Finite-State Model Gate",
            "",
            f"Classification: `{result['classification']}`",
            "Translation delta: `NONE`",
            "",
            "## Purpose",
            "",
            "Gate 63 rejects simple stop-rule separators for the residual",
            "target-max exceptions. This gate asks whether a compact finite-state",
            "context model over online, decoder-valid features can explain the same",
            "exception stream better than an explicit exception list.",
            "",
            "## Summary",
            "",
            f"- Copy events: `{s['copy_event_count']}`.",
            f"- Target-max exceptions: `{s['exception_count']}`.",
            f"- Context models tested: `{s['model_count']}`.",
            f"- Uniform label cost: `{s['uniform_label_bits']:.6f}` bits.",
            f"- Global KT label cost: `{s['global_kt_bits']:.6f}` bits.",
            f"- Explicit exception-list cost: `{s['explicit_exception_list_bits']:.6f}` bits.",
            "",
            "## Best Finite-State Context Model",
            "",
            f"- Features: `{best['features']}`.",
            f"- Contexts used: `{best['context_count']}`.",
            f"- Data bits: `{best['data_bits']:.6f}`.",
            f"- Descriptor bits: `{best['descriptor_bits']:.6f}`.",
            f"- Total bits: `{best['total_bits']:.6f}`.",
            f"- Delta versus explicit exception list: `{best['delta_vs_explicit_list_bits']:+.6f}` bits.",
            f"- Densest context: `{best['densest_context']}` "
            f"with `{best['densest_context_positive_count']}` / "
            f"`{best['densest_context_total_count']}` exceptions.",
            "",
            "## Controls",
            "",
            f"- Permutation trials: `{control['trials']}`.",
            f"- Permuted best-total min/median/max: "
            f"`{control['best_total_bits_min']:.6f}` / "
            f"`{control['best_total_bits_median']:.6f}` / "
            f"`{control['best_total_bits_max']:.6f}`.",
            f"- P(permuted best total <= observed): "
            f"`{control['p_permuted_total_bits_le_observed']:.6f}`.",
            f"- Permuted models beating explicit-list cost: "
            f"`{control['permuted_beats_explicit_list_count']}`.",
            "",
            "## Decision",
            "",
            f"- Interpretation: {s['interpretation']}",
            "- Current compression bound remains `8156.049986` bits.",
            "- Copy length remains a declared dependency.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No new formula is emitted.",
            "",
        ]
    )


def main() -> None:
    formula = load_json(ACTIVE_FORMULA)
    books = load_json(BOOKS_DIGITS)
    stop_rule_gate = load_json(STOP_RULE_GATE_63)
    assert_boundary("stop_rule_gate_63", stop_rule_gate)

    rows = collect_copy_rows(formula, books)
    labels = [bool(row["is_targetmax_exception"]) for row in rows]
    exception_count = sum(labels)
    if len(rows) != 261 or exception_count != 19:
        raise RuntimeError(
            {
                "copy_event_count": len(rows),
                "exception_count": exception_count,
                "expected": [261, 19],
            }
        )

    vectors = context_vectors(rows)
    descriptor_bits = math.log2(len(vectors))
    scored = score_models(vectors, labels, descriptor_bits)
    best = scored[0]
    explicit_list_bits = log2_comb(len(labels), exception_count)
    best["delta_vs_explicit_list_bits"] = best["total_bits"] - explicit_list_bits
    top_models = []
    for row in scored[:12]:
        item = dict(row)
        item["delta_vs_explicit_list_bits"] = item["total_bits"] - explicit_list_bits
        top_models.append(item)

    control = permutation_control(
        vectors=vectors,
        labels=labels,
        descriptor_bits=descriptor_bits,
        observed_best_bits=best["total_bits"],
        explicit_list_bits=explicit_list_bits,
    )

    if (
        best["total_bits"] < explicit_list_bits
        and control["p_permuted_total_bits_le_observed"] <= 0.05
    ):
        classification = "active_exception_finite_state_candidate_found"
        interpretation = (
            "A compact online context model beats the explicit exception-list "
            "baseline under permutation control. It is a structural candidate, "
            "not a formula promotion."
        )
        finite_state_status = "candidate_found_unpromoted"
    else:
        classification = "active_exception_finite_state_not_promotable"
        interpretation = (
            "The best online finite-state context model does not provide a "
            "controlled, compact replacement for the explicit residual exception "
            "list. Residual target-max boundaries remain nonlocal/ad hoc under "
            "the current evidence."
        )
        finite_state_status = "no_controlled_compact_exception_model"

    result = {
        "schema": "active_exception_finite_state_model_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "stop_rule_gate_63": rel(STOP_RULE_GATE_63),
        },
        "scope": {
            "analysis_only": True,
            "copy_event_count": len(rows),
            "exception_count": exception_count,
            "model_family": "KT-coded finite-state contexts over online decoder-valid features",
            "max_feature_arity": MAX_FEATURE_ARITY,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "does_not_search_plaintext": True,
            "row0_origin_changed": False,
        },
        "summary": {
            "copy_event_count": len(rows),
            "exception_count": exception_count,
            "model_count": len(vectors),
            "descriptor_bits": descriptor_bits,
            "uniform_label_bits": float(len(labels)),
            "global_kt_bits": kt_bits([("global",)] * len(labels), labels),
            "explicit_exception_list_bits": explicit_list_bits,
            "best_model": best,
            "top_models": top_models,
            "permutation_control": control,
            "interpretation": interpretation,
        },
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "copy_length_dependency_status": "retained_declared",
            "finite_state_exception_status": finite_state_status,
            "generation_explanation_status": "residual_boundaries_require_richer_nonlocal_parser_state",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "64_active_exception_finite_state_model_gate.json"
    md_path = TEST_RESULTS / "64_active_exception_finite_state_model_gate.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
