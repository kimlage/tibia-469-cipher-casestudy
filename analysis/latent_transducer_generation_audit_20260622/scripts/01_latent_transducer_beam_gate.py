from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
ROUTE_REVIEW = (
    ROOT
    / "analysis"
    / "skeleton_generation_route_review_20260622"
    / "reports"
    / "final_skeleton_generation_route_review.md"
)

OUT_STEM = "01_latent_transducer_beam_gate"
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
MIN_COPY_LEN = 5
BEAM_WIDTH = 80
MAX_LITERAL_LEN = 12
MAX_COPY_CANDIDATE_LEN = 160
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000


@dataclass(frozen=True)
class BeamState:
    pos: int
    score: float
    ops: tuple[tuple[Any, ...], ...]


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


def prev2_context(prefix: str) -> tuple[str, str]:
    if not prefix:
        return ("BOS", "BOS")
    if len(prefix) == 1:
        return ("BOS", prefix[-1])
    return (prefix[-2], prefix[-1])


def train_prev2(
    books: dict[int, str],
    book_ids: list[int],
) -> tuple[dict[tuple[str, str], Counter[str]], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for book in book_ids:
        prefix = ""
        for digit in books[book]:
            counts[prev2_context(prefix)][digit] += 1
            prefix += digit
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    return counts, global_counts


def digit_cost(
    digit: str,
    prefix: str,
    digit_counts: dict[tuple[str, str], Counter[str]],
    global_digit_counts: Counter[str],
) -> float:
    counter = digit_counts.get(prev2_context(prefix), global_digit_counts)
    total = sum(counter.values())
    probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
    return -math.log2(probability)


def book_surprisals(
    target: str,
    digit_counts: dict[tuple[str, str], Counter[str]],
    global_digit_counts: Counter[str],
) -> list[float]:
    prefix = ""
    values = []
    for digit in target:
        value = digit_cost(digit, prefix, digit_counts, global_digit_counts)
        values.append(value)
        prefix += digit
    return values


def age_bucket(age: int) -> str:
    if age == 1:
        return "age_1"
    if age <= 3:
        return "age_2_3"
    if age <= 7:
        return "age_4_7"
    if age <= 15:
        return "age_8_15"
    if age <= 31:
        return "age_16_31"
    if age <= 63:
        return "age_32_63"
    return "age_64_plus"


def surprisal_bin(value: float) -> str:
    if value < 2.0:
        return "surp_lt_2"
    if value < 3.0:
        return "surp_2_3"
    if value < 4.0:
        return "surp_3_4"
    if value < 5.0:
        return "surp_4_5"
    return "surp_ge_5"


def length_bucket(length: int) -> str:
    if length <= 2:
        return "len_1_2"
    if length <= 4:
        return "len_3_4"
    if length <= 7:
        return "len_5_7"
    if length <= 12:
        return "len_8_12"
    if length <= 20:
        return "len_13_20"
    if length <= 40:
        return "len_21_40"
    if length <= 80:
        return "len_41_80"
    return "len_81_plus"


def logp(counter: Counter[Any], key: Any, support_size: int) -> float:
    return -math.log2(
        (counter[key] + ALPHA) / (sum(counter.values()) + ALPHA * support_size)
    )


def log2comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2)


def boundary_flags(
    book: int,
    length: int,
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[int]:
    flags = [0] * length
    if str(book) not in ops_by_book:
        return flags
    for op in ops_by_book[str(book)][:-1]:
        cutpoint = int(op["target_start"]) + int(op["length"])
        if 0 < cutpoint < length:
            flags[cutpoint] = 1
    return flags


def normalize_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        item = {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row.get("source"),
        }
        out.append(item)
    return out


def train_parameters(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
    cutoff: int,
) -> dict[str, Any]:
    digit_counts, global_digit_counts = train_prev2(books, list(range(cutoff)))
    type_counts: Counter[str] = Counter()
    length_counts: dict[str, Counter[str]] = defaultdict(Counter)
    boundary_counts: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    global_boundary_counts: Counter[int] = Counter()
    for book in range(10, cutoff):
        target = books[book]
        surprisals = book_surprisals(target, digit_counts, global_digit_counts)
        flags = boundary_flags(book, len(target), ops_by_book)
        last_boundary = 0
        for pos in range(1, len(target)):
            age_key = age_bucket(pos - last_boundary)
            surp_key = surprisal_bin(surprisals[pos])
            flag = flags[pos]
            boundary_counts[(age_key, surp_key)][flag] += 1
            global_boundary_counts[flag] += 1
            if flag:
                last_boundary = pos
        for op in ops_by_book[str(book)]:
            op_type = op["type"]
            type_counts[op_type] += 1
            length_counts[op_type][length_bucket(int(op["length"]))] += 1
    return {
        "digit_counts": digit_counts,
        "global_digit_counts": global_digit_counts,
        "type_counts": type_counts,
        "length_counts": length_counts,
        "boundary_counts": boundary_counts,
        "global_boundary_counts": global_boundary_counts,
    }


def boundary_cost(
    start: int,
    end: int,
    book_length: int,
    surprisals: list[float],
    params: dict[str, Any],
) -> float:
    cost = 0.0
    for pos in range(start + 1, end):
        age_key = age_bucket(pos - start)
        surp_key = surprisal_bin(surprisals[pos])
        counter = params["boundary_counts"].get(
            (age_key, surp_key), params["global_boundary_counts"]
        )
        cost += logp(counter, 0, 2)
    if end < book_length:
        age_key = age_bucket(end - start)
        surp_key = surprisal_bin(surprisals[end])
        counter = params["boundary_counts"].get(
            (age_key, surp_key), params["global_boundary_counts"]
        )
        cost += logp(counter, 1, 2)
    return cost


def literal_digit_cost(target: str, start: int, end: int, params: dict[str, Any]) -> float:
    prefix = target[:start]
    cost = 0.0
    for digit in target[start:end]:
        cost += digit_cost(
            digit,
            prefix,
            params["digit_counts"],
            params["global_digit_counts"],
        )
        prefix += digit
    return cost


def op_prior_cost(op_type: str, length: int, params: dict[str, Any]) -> float:
    type_cost = logp(params["type_counts"], op_type, 2)
    len_cost = logp(params["length_counts"][op_type], length_bucket(length), 8)
    return type_cost + len_cost


def find_source_maxima(emitted: str, target: str, pos: int) -> list[tuple[int, int]]:
    rows: list[tuple[int, int]] = []
    if pos + MIN_COPY_LEN > len(target):
        return rows
    needle = target[pos : pos + MIN_COPY_LEN]
    source = emitted.find(needle)
    seen = set()
    while source != -1:
        if source not in seen:
            seen.add(source)
            max_len = MIN_COPY_LEN
            cap = min(len(target) - pos, len(emitted) - source, MAX_COPY_CANDIDATE_LEN)
            while max_len < cap and emitted[source + max_len] == target[pos + max_len]:
                max_len += 1
            rows.append((source, max_len))
        source = emitted.find(needle, source + 1)
    return rows


def copy_candidates(emitted: str, target: str, pos: int) -> list[tuple[int, int]]:
    maxima = find_source_maxima(emitted, target, pos)
    if not maxima:
        return []
    best_source_for_length: dict[int, int] = {}
    for source, max_len in maxima:
        for length in range(MIN_COPY_LEN, max_len + 1):
            prior = best_source_for_length.get(length)
            if prior is None or source < prior:
                best_source_for_length[length] = source
    return sorted((length, source) for length, source in best_source_for_length.items())


def candidate_ops(
    emitted_base: str,
    target: str,
    pos: int,
    params: dict[str, Any],
    surprisals: list[float],
) -> list[tuple[float, tuple[Any, ...]]]:
    emitted = emitted_base + target[:pos]
    out: list[tuple[float, tuple[Any, ...]]] = []
    max_literal = min(MAX_LITERAL_LEN, len(target) - pos)
    for length in range(1, max_literal + 1):
        end = pos + length
        score = (
            op_prior_cost("literal", length, params)
            + literal_digit_cost(target, pos, end, params)
            + boundary_cost(pos, end, len(target), surprisals, params)
        )
        out.append((score, ("literal", pos, length, None)))
    for length, source in copy_candidates(emitted, target, pos):
        end = pos + length
        score = (
            op_prior_cost("copy", length, params)
            + math.log2(max(1, len(emitted)))
            * 0.05
            + boundary_cost(pos, end, len(target), surprisals, params)
        )
        out.append((score, ("copy", pos, length, source)))
    return out


def parse_book(
    emitted_base: str,
    target: str,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    surprisals = book_surprisals(
        target,
        params["digit_counts"],
        params["global_digit_counts"],
    )
    beam = [BeamState(pos=0, score=0.0, ops=())]
    candidates_by_pos: dict[int, list[tuple[float, tuple[Any, ...]]]] = {}
    best_by_pos: dict[int, list[BeamState]] = defaultdict(list)
    while beam:
        next_states: list[BeamState] = []
        finished: list[BeamState] = []
        for state in beam:
            if state.pos == len(target):
                finished.append(state)
                continue
            if state.pos not in candidates_by_pos:
                candidates_by_pos[state.pos] = candidate_ops(
                    emitted_base, target, state.pos, params, surprisals
                )
            for op_score, op in candidates_by_pos[state.pos]:
                next_states.append(
                    BeamState(
                        pos=state.pos + int(op[2]),
                        score=state.score + op_score,
                        ops=state.ops + (op,),
                    )
                )
        if finished:
            best = min(finished, key=lambda item: item.score)
            return [
                {
                    "type": op[0],
                    "target_start": int(op[1]),
                    "length": int(op[2]),
                    "source": op[3],
                }
                for op in best.ops
            ]
        best_by_pos.clear()
        for state in next_states:
            best_by_pos[state.pos].append(state)
        beam = []
        for states in best_by_pos.values():
            beam.extend(sorted(states, key=lambda item: item.score)[: max(4, BEAM_WIDTH // 8)])
        beam = sorted(beam, key=lambda item: item.score)[:BEAM_WIDTH]
    raise RuntimeError("beam exhausted")


def cutpoints(ops: list[dict[str, Any]], book_length: int) -> set[int]:
    return {
        int(op["target_start"]) + int(op["length"])
        for op in ops[:-1]
        if 0 < int(op["target_start"]) + int(op["length"]) < book_length
    }


def compare_book(
    predicted: list[dict[str, Any]],
    canonical: list[dict[str, Any]],
    book_length: int,
) -> dict[str, Any]:
    predicted_cuts = cutpoints(predicted, book_length)
    canonical_cuts = cutpoints(canonical, book_length)
    false_positive = len(predicted_cuts - canonical_cuts)
    false_negative = len(canonical_cuts - predicted_cuts)
    candidate_positions = book_length - 1
    cutpoint_atlas_bits = log2comb(candidate_positions, len(canonical_cuts))
    cutpoint_correction_bits = log2comb(len(predicted_cuts), false_positive) + log2comb(
        candidate_positions - len(predicted_cuts), false_negative
    )
    canonical_by_start = {op["target_start"]: op for op in canonical}
    source_length_hits = 0
    copy_start_hits = 0
    literal_span_hits = 0
    for op in predicted:
        stable = canonical_by_start.get(op["target_start"])
        if stable is None:
            continue
        if op["type"] == "copy" and stable["type"] == "copy":
            copy_start_hits += 1
            if op["length"] == stable["length"] and op["source"] == stable["source"]:
                source_length_hits += 1
        if op["type"] == "literal" and stable["type"] == "literal" and op["length"] == stable["length"]:
            literal_span_hits += 1
    return {
        "exact_ops": predicted == canonical,
        "predicted_op_count": len(predicted),
        "canonical_op_count": len(canonical),
        "predicted_cutpoints": len(predicted_cuts),
        "canonical_cutpoints": len(canonical_cuts),
        "cutpoint_hits": len(predicted_cuts & canonical_cuts),
        "cutpoint_false_positive": false_positive,
        "cutpoint_false_negative": false_negative,
        "cutpoint_atlas_bits": cutpoint_atlas_bits,
        "cutpoint_correction_bits": cutpoint_correction_bits,
        "cutpoint_saving_vs_atlas_bits": cutpoint_atlas_bits - cutpoint_correction_bits,
        "copy_start_hits": copy_start_hits,
        "source_length_hits": source_length_hits,
        "literal_span_hits": literal_span_hits,
        "predicted_literal_digits": sum(op["length"] for op in predicted if op["type"] == "literal"),
        "canonical_literal_digits": sum(op["length"] for op in canonical if op["type"] == "literal"),
        "predicted_copy_ops": sum(1 for op in predicted if op["type"] == "copy"),
        "canonical_copy_ops": sum(1 for op in canonical if op["type"] == "copy"),
    }


def random_cutpoint_control(
    books: dict[int, str],
    canonical_by_book: dict[int, list[dict[str, Any]]],
    predicted_counts: dict[int, int],
    book_ids: list[int],
    rng: random.Random,
) -> dict[str, Any]:
    values = []
    for _ in range(RANDOM_TRIALS):
        hits = 0
        for book in book_ids:
            actual = cutpoints(canonical_by_book[book], len(books[book]))
            candidates = list(range(1, len(books[book])))
            count = min(predicted_counts[book], len(candidates))
            predicted = set(rng.sample(candidates, count)) if count else set()
            hits += len(predicted & actual)
        values.append(hits)
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "hit_mean": mean(values),
        "hit_p95": percentile(values, 0.95),
        "hit_max": values[-1],
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def evaluate_cutoff(
    books: dict[int, str],
    canonical_by_book: dict[int, list[dict[str, Any]]],
    ops_by_book: dict[str, list[dict[str, Any]]],
    cutoff: int,
) -> dict[str, Any]:
    params = train_parameters(books, ops_by_book, cutoff)
    emitted = "".join(books[index] for index in range(cutoff))
    rows = []
    exact_books = []
    predicted_counts = {}
    for book in range(cutoff, 70):
        predicted = parse_book(emitted, books[book], params)
        canonical = canonical_by_book[book]
        comparison = compare_book(predicted, canonical, len(books[book]))
        comparison["book"] = book
        rows.append(comparison)
        predicted_counts[book] = comparison["predicted_cutpoints"]
        if comparison["exact_ops"]:
            exact_books.append(book)
        emitted += books[book]
    rng = random.Random(RANDOM_SEED + cutoff)
    control = random_cutpoint_control(
        books,
        canonical_by_book,
        predicted_counts,
        list(range(cutoff, 70)),
        rng,
    )
    cutpoint_hits = sum(row["cutpoint_hits"] for row in rows)
    return {
        "cutoff": cutoff,
        "test_books": len(rows),
        "exact_books": exact_books,
        "exact_book_count": len(exact_books),
        "nontrivial_exact_book_count": len(
            [book for book in exact_books if len(canonical_by_book[book]) > 1]
        ),
        "predicted_ops": sum(row["predicted_op_count"] for row in rows),
        "canonical_ops": sum(row["canonical_op_count"] for row in rows),
        "cutpoint_hits": cutpoint_hits,
        "canonical_cutpoints": sum(row["canonical_cutpoints"] for row in rows),
        "predicted_cutpoints": sum(row["predicted_cutpoints"] for row in rows),
        "cutpoint_false_positive": sum(row["cutpoint_false_positive"] for row in rows),
        "cutpoint_false_negative": sum(row["cutpoint_false_negative"] for row in rows),
        "cutpoint_atlas_bits": sum(row["cutpoint_atlas_bits"] for row in rows),
        "cutpoint_correction_bits": sum(row["cutpoint_correction_bits"] for row in rows),
        "cutpoint_saving_vs_atlas_bits": sum(
            row["cutpoint_saving_vs_atlas_bits"] for row in rows
        ),
        "copy_start_hits": sum(row["copy_start_hits"] for row in rows),
        "source_length_hits": sum(row["source_length_hits"] for row in rows),
        "predicted_copy_ops": sum(row["predicted_copy_ops"] for row in rows),
        "canonical_copy_ops": sum(row["canonical_copy_ops"] for row in rows),
        "literal_span_hits": sum(row["literal_span_hits"] for row in rows),
        "predicted_literal_digits": sum(row["predicted_literal_digits"] for row in rows),
        "canonical_literal_digits": sum(row["canonical_literal_digits"] for row in rows),
        "random_cutpoint_hit_mean": control["hit_mean"],
        "random_cutpoint_hit_p95": control["hit_p95"],
        "random_cutpoint_hit_max": control["hit_max"],
        "beats_random_cutpoint_p95": cutpoint_hits > control["hit_p95"],
        "sample_book_rows": rows[:10],
    }


def make_result() -> dict[str, Any]:
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ops_by_book = copy_ledger["canonical_ops_by_book"]
    canonical_by_book = {
        book: normalize_ops(ops_by_book[str(book)])
        for book in range(10, 70)
    }
    cutoff_rows = [
        evaluate_cutoff(books, canonical_by_book, ops_by_book, cutoff)
        for cutoff in PREFIX_CUTOFFS
    ]
    aggregate_exact = sum(row["exact_book_count"] for row in cutoff_rows)
    aggregate_nontrivial_exact = sum(
        row["nontrivial_exact_book_count"] for row in cutoff_rows
    )
    aggregate_cutpoint_hits = sum(row["cutpoint_hits"] for row in cutoff_rows)
    aggregate_cutpoints = sum(row["canonical_cutpoints"] for row in cutoff_rows)
    cells_beating_random = sum(
        1 for row in cutoff_rows if row["beats_random_cutpoint_p95"]
    )
    promotes_generator = (
        aggregate_nontrivial_exact > 0
        and cells_beating_random == len(PREFIX_CUTOFFS)
    )
    summary = {
        "cutoff_count": len(PREFIX_CUTOFFS),
        "beam_width": BEAM_WIDTH,
        "min_copy_len": MIN_COPY_LEN,
        "max_literal_len": MAX_LITERAL_LEN,
        "aggregate_exact_books": aggregate_exact,
        "aggregate_nontrivial_exact_books": aggregate_nontrivial_exact,
        "aggregate_cutpoint_hits": aggregate_cutpoint_hits,
        "aggregate_canonical_cutpoints": aggregate_cutpoints,
        "cells_beating_random_cutpoint_p95": cells_beating_random,
        "aggregate_source_length_hits": sum(
            row["source_length_hits"] for row in cutoff_rows
        ),
        "aggregate_cutpoint_atlas_bits": sum(
            row["cutpoint_atlas_bits"] for row in cutoff_rows
        ),
        "aggregate_cutpoint_correction_bits": sum(
            row["cutpoint_correction_bits"] for row in cutoff_rows
        ),
        "aggregate_cutpoint_saving_vs_atlas_bits": sum(
            row["cutpoint_saving_vs_atlas_bits"] for row in cutoff_rows
        ),
        "aggregate_canonical_copy_ops": sum(row["canonical_copy_ops"] for row in cutoff_rows),
        "aggregate_predicted_literal_digits": sum(
            row["predicted_literal_digits"] for row in cutoff_rows
        ),
        "aggregate_canonical_literal_digits": sum(
            row["canonical_literal_digits"] for row in cutoff_rows
        ),
        "promotes_latent_transducer_generator": promotes_generator,
        "interpretation": (
            "This first joint transducer gate decodes operations from a shared "
            "literal/copy/boundary cost model under prefix holdout, but it still "
            "uses the target digit stream as teacher-forced input. Promotion "
            "requires nontrivial exact books plus random-control survival."
        ),
    }
    return {
        "schema": "latent_transducer_beam_gate_v1",
        "scope": "analysis_only_prefix_trained_joint_literal_copy_boundary_parser",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "route_review": rel(ROUTE_REVIEW),
        },
        "model": {
            "teacher_forced_target_stream": True,
            "emits_closed_loop_digits_without_target": False,
            "beam_width": BEAM_WIDTH,
            "state": [
                "prev2_digits",
                "age_since_last_boundary",
                "surprisal_bin",
                "operation_type",
                "length_bucket",
                "copy_availability_from_material_emitted_so_far",
            ],
            "candidate_generation": (
                "literal lengths 1..12 and copy lengths 5..160 from earliest "
                "available source supporting each length"
            ),
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": (
            "latent_transducer_generator_promoted"
            if promotes_generator
            else "latent_transducer_first_gate_not_promoted"
        ),
        "decision": {
            "promotes_latent_transducer_generator": promotes_generator,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Latent Transducer Beam Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test the first joint literal/copy/boundary transducer route. The decoder",
        "trains parameters on prefix books, freezes them, then parses future books",
        "with a beam that chooses literal spans or available copy spans in one pass.",
        "",
        "This is not a closed-loop digit generator yet: the target digit stream is",
        "teacher-forced so that the gate can isolate whether the operation skeleton",
        "emerges from joint transduction rather than a declared atlas.",
        "",
        "## Summary",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Beam width: `{s['beam_width']}`.",
        f"- Aggregate exact books: `{s['aggregate_exact_books']}`.",
        f"- Aggregate nontrivial exact books: `{s['aggregate_nontrivial_exact_books']}`.",
        f"- Aggregate cutpoint hits: `{s['aggregate_cutpoint_hits']}/{s['aggregate_canonical_cutpoints']}`.",
        f"- Cells beating random cutpoint p95: `{s['cells_beating_random_cutpoint_p95']}/{s['cutoff_count']}`.",
        f"- Aggregate source+length hits: `{s['aggregate_source_length_hits']}/{s['aggregate_canonical_copy_ops']}`.",
        f"- Aggregate cutpoint atlas bits: `{s['aggregate_cutpoint_atlas_bits']:.3f}`.",
        f"- Aggregate cutpoint correction bits: `{s['aggregate_cutpoint_correction_bits']:.3f}`.",
        f"- Aggregate cutpoint saving vs atlas: `{s['aggregate_cutpoint_saving_vs_atlas_bits']:.3f}`.",
        f"- Predicted literal digits: `{s['aggregate_predicted_literal_digits']}`.",
        f"- Canonical literal digits: `{s['aggregate_canonical_literal_digits']}`.",
        f"- Promotes latent transducer generator: `{s['promotes_latent_transducer_generator']}`.",
        "",
        s["interpretation"],
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Exact books | Nontrivial exact | Cutpoint hits | Random p95 | Cutpoint saving | Source+length | Literal digits |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['exact_book_count']}/{row['test_books']}` | "
            f"`{row['nontrivial_exact_book_count']}` | "
            f"`{row['cutpoint_hits']}/{row['canonical_cutpoints']}` | "
            f"`{row['random_cutpoint_hit_p95']:.3f}` | "
            f"`{row['cutpoint_saving_vs_atlas_bits']:.3f}` | "
            f"`{row['source_length_hits']}/{row['canonical_copy_ops']}` | "
            f"`{row['predicted_literal_digits']}/{row['canonical_literal_digits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The first latent-transducer beam is not promoted as a generator unless the JSON summary says otherwise.",
            "- This gate tests the right joint object but remains target-stream teacher-forced.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
