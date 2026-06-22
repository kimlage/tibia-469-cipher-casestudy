from __future__ import annotations

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
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
SEED_SUBCODEC_GATE = TEST_RESULTS / "05_seed_derived_tape_subcodec_gate.json"
SEED_WALK_GATE = TEST_RESULTS / "06_seed_walk_source_model_gate.json"

OUT_STEM = "17_hybrid_innovation_tape_subcodec_gate"
SEED_BOOKS = list(range(10))
MIN_LENGTHS = [2, 3, 4, 5, 6, 7, 8]
STRATEGIES = ["max_cover", "local_saving"]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
DIGIT_BITS = math.log2(10)


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


def canonical_tape(ops_by_book: dict[str, list[dict[str, Any]]]) -> str:
    parts = []
    for book in range(10, 70):
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                parts.append(op.get("payload", ""))
    return "".join(parts)


def seed_text(books: dict[int, str]) -> str:
    return "".join(books[book] for book in SEED_BOOKS)


def build_index(source: str, min_len: int) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos in range(0, len(source) - min_len + 1):
        index.setdefault(source[pos : pos + min_len], []).append(pos)
    return index


def best_match(
    text: str,
    pos: int,
    source: str,
    index: dict[str, list[int]],
    min_len: int,
) -> tuple[int, int] | None:
    if pos + min_len > len(text):
        return None
    candidates = index.get(text[pos : pos + min_len], [])
    best: tuple[int, int] | None = None
    for source_pos in candidates:
        length = min_len
        cap = min(len(text) - pos, len(source) - source_pos)
        while length < cap and text[pos + length] == source[source_pos + length]:
            length += 1
        if best is None or (length, -source_pos) > (best[1], -best[0]):
            best = (source_pos, length)
    return best


def copy_cost(source_len: int, text_len: int, pos: int, hybrid: bool) -> float:
    source_bits = math.log2(max(1, source_len))
    length_bits = math.log2(max(1, text_len - pos))
    origin_bits = 1.0 if hybrid else 0.0
    mode_bits = 1.0
    return mode_bits + origin_bits + source_bits + length_bits


def literal_cost() -> float:
    return 1.0 + DIGIT_BITS


def hybrid_subcodec(text: str, seed: str, min_len: int, strategy: str) -> dict[str, Any]:
    seed_index = build_index(seed, min_len)
    pos = 0
    copy_items = 0
    seed_copy_items = 0
    prior_copy_items = 0
    copy_digits = 0
    literal_digits = 0
    source_bits = 0.0
    length_bits = 0.0
    origin_bits = 0.0
    mode_bits = 0.0
    while pos < len(text):
        options = []
        seed_match = best_match(text, pos, seed, seed_index, min_len)
        if seed_match is not None:
            source_pos, length = seed_match
            cost = copy_cost(len(seed), len(text), pos, hybrid=True)
            options.append(("seed", source_pos, length, cost))
        prior = text[:pos]
        if len(prior) >= min_len:
            prior_index = build_index(prior, min_len)
            prior_match = best_match(text, pos, prior, prior_index, min_len)
            if prior_match is not None:
                source_pos, length = prior_match
                cost = copy_cost(len(prior), len(text), pos, hybrid=True)
                options.append(("prior", source_pos, length, cost))
        chosen = None
        if options:
            if strategy == "max_cover":
                chosen = max(options, key=lambda item: (item[2], -item[3], item[0] == "prior"))
            elif strategy == "local_saving":
                profitable = [
                    item for item in options if item[2] * DIGIT_BITS > item[3]
                ]
                if profitable:
                    chosen = max(
                        profitable,
                        key=lambda item: (item[2] * DIGIT_BITS - item[3], item[2]),
                    )
            else:
                raise KeyError(strategy)
        if chosen is None:
            literal_digits += 1
            mode_bits += 1.0
            pos += 1
            continue
        source_name, _source_pos, length, cost = chosen
        copy_items += 1
        copy_digits += length
        if source_name == "seed":
            seed_copy_items += 1
            source_bits += math.log2(len(seed))
        else:
            prior_copy_items += 1
            source_bits += math.log2(pos)
        length_bits += math.log2(max(1, len(text) - pos))
        origin_bits += 1.0
        mode_bits += 1.0
        pos += length
    literal_bits = literal_digits * DIGIT_BITS
    total_bits = source_bits + length_bits + origin_bits + mode_bits + literal_bits
    raw_bits = len(text) * DIGIT_BITS
    return {
        "min_len": min_len,
        "strategy": strategy,
        "copy_items": copy_items,
        "seed_copy_items": seed_copy_items,
        "prior_copy_items": prior_copy_items,
        "copy_digits": copy_digits,
        "literal_digits": literal_digits,
        "source_bits": source_bits,
        "length_bits": length_bits,
        "origin_bits": origin_bits,
        "mode_bits": mode_bits,
        "literal_bits": literal_bits,
        "total_bits": total_bits,
        "raw_bits": raw_bits,
        "saving_vs_raw_bits": raw_bits - total_bits,
        "coverage_fraction": copy_digits / len(text) if text else 0.0,
    }


def shuffled_controls(text: str, seed: str, min_len: int, strategy: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + min_len * 97 + sum(ord(ch) for ch in strategy))
    chars = list(text)
    savings = []
    coverages = []
    copy_items = []
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        row = hybrid_subcodec("".join(chars), seed, min_len, strategy)
        savings.append(row["saving_vs_raw_bits"])
        coverages.append(row["copy_digits"])
        copy_items.append(row["copy_items"])
    savings.sort()
    coverages.sort()
    copy_items.sort()
    return {
        "trials": RANDOM_TRIALS,
        "saving_mean": mean(savings),
        "saving_p95": percentile(savings, 0.95),
        "saving_max": savings[-1],
        "coverage_mean": mean(coverages),
        "coverage_p95": percentile(coverages, 0.95),
        "coverage_max": coverages[-1],
        "copy_items_mean": mean(copy_items),
        "copy_items_p95": percentile(copy_items, 0.95),
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    seed_subcodec = load_json(SEED_SUBCODEC_GATE)
    seed_walk = load_json(SEED_WALK_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("seed_derived_tape_subcodec_gate", seed_subcodec)
    assert_boundary("seed_walk_source_model_gate", seed_walk)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape = canonical_tape(ledger["canonical_ops_by_book"])
    seed = seed_text(books)
    rows = []
    for strategy in STRATEGIES:
        for min_len in MIN_LENGTHS:
            observed = hybrid_subcodec(tape, seed, min_len, strategy)
            control = shuffled_controls(tape, seed, min_len, strategy)
            rows.append(
                {
                    **observed,
                    "control_saving_p95": control["saving_p95"],
                    "control_saving_max": control["saving_max"],
                    "control_coverage_p95": control["coverage_p95"],
                    "control_copy_items_p95": control["copy_items_p95"],
                    "beats_saving_p95": observed["saving_vs_raw_bits"]
                    > control["saving_p95"],
                    "beats_coverage_p95": observed["copy_digits"]
                    > control["coverage_p95"],
                }
            )
    best = max(rows, key=lambda row: (row["saving_vs_raw_bits"], row["copy_digits"]))
    best_coverage = max(rows, key=lambda row: (row["copy_digits"], row["saving_vs_raw_bits"]))
    promotes_subcodec = best["saving_vs_raw_bits"] > 0 and best["beats_saving_p95"]
    weak_hybrid_clue = (
        not promotes_subcodec
        and best_coverage["beats_coverage_p95"]
        and best_coverage["beats_saving_p95"]
    )
    summary = {
        "literal_tape_digits": len(tape),
        "seed_text_digits": len(seed),
        "raw_bits": len(tape) * DIGIT_BITS,
        "best_strategy": best["strategy"],
        "best_min_len": best["min_len"],
        "best_total_bits": best["total_bits"],
        "best_saving_vs_raw_bits": best["saving_vs_raw_bits"],
        "best_control_saving_p95": best["control_saving_p95"],
        "best_copy_digits": best["copy_digits"],
        "best_literal_digits": best["literal_digits"],
        "best_copy_items": best["copy_items"],
        "best_seed_copy_items": best["seed_copy_items"],
        "best_prior_copy_items": best["prior_copy_items"],
        "best_coverage_strategy": best_coverage["strategy"],
        "best_coverage_min_len": best_coverage["min_len"],
        "best_coverage_copy_digits": best_coverage["copy_digits"],
        "best_coverage_control_p95": best_coverage["control_coverage_p95"],
        "promotes_hybrid_subcodec": promotes_subcodec,
        "weak_hybrid_subcodec_clue": weak_hybrid_clue,
        "interpretation": (
            "This gate tests a stronger paid subcodec for the innovation tape: "
            "copies may reference either seed-book text or prior emitted tape, "
            "with explicit mode, origin, source, length, and literal costs. It "
            "compares paid savings against raw tape and same-multiset shuffled "
            "controls."
        ),
    }
    return {
        "schema": "hybrid_innovation_tape_subcodec_gate_v1",
        "scope": "analysis_only_paid_seed_plus_prior_tape_subcodec",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "seed_derived_tape_subcodec_gate": rel(SEED_SUBCODEC_GATE),
            "seed_walk_source_model_gate": rel(SEED_WALK_GATE),
        },
        "rows": rows,
        "summary": summary,
        "classification": (
            "hybrid_innovation_tape_subcodec_promoted"
            if promotes_subcodec
            else (
                "hybrid_innovation_tape_subcodec_weak_clue"
                if weak_hybrid_clue
                else "hybrid_innovation_tape_subcodec_rejected"
            )
        ),
        "decision": {
            "promotes_hybrid_subcodec": promotes_subcodec,
            "weak_hybrid_subcodec_clue": weak_hybrid_clue,
            "generator_status": "not_promoted",
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
        "# Hybrid Innovation Tape Subcodec Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the innovation tape can be reduced by a paid hybrid",
        "subcodec that copies from seed-book text or from prior emitted tape,",
        "instead of keeping all `266` digits as raw literal payload.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Seed text digits: `{s['seed_text_digits']}`.",
        f"- Raw tape bits: `{s['raw_bits']:.3f}`.",
        f"- Best strategy/min_len: `{s['best_strategy']}` / `{s['best_min_len']}`.",
        f"- Best total bits: `{s['best_total_bits']:.3f}`.",
        f"- Best saving vs raw: `{s['best_saving_vs_raw_bits']:.3f}`.",
        f"- Best control saving p95: `{s['best_control_saving_p95']:.3f}`.",
        f"- Best copy/literal digits: `{s['best_copy_digits']}` / `{s['best_literal_digits']}`.",
        f"- Best copy items seed/prior: `{s['best_seed_copy_items']}` / `{s['best_prior_copy_items']}`.",
        f"- Best coverage strategy/min_len: `{s['best_coverage_strategy']}` / `{s['best_coverage_min_len']}`.",
        f"- Best coverage digits/control p95: `{s['best_coverage_copy_digits']}` / `{s['best_coverage_control_p95']:.3f}`.",
        f"- Promotes hybrid subcodec: `{s['promotes_hybrid_subcodec']}`.",
        f"- Weak hybrid subcodec clue: `{s['weak_hybrid_subcodec_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Rows",
        "",
        "| Strategy | Min len | Total bits | Saving | Control p95 | Copy digits | Literal digits | Copy items | Seed/Prior items | Coverage p95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: (item["saving_vs_raw_bits"], item["copy_digits"]),
        reverse=True,
    ):
        lines.append(
            f"| `{row['strategy']}` | `{row['min_len']}` | "
            f"`{row['total_bits']:.3f}` | `{row['saving_vs_raw_bits']:.3f}` | "
            f"`{row['control_saving_p95']:.3f}` | `{row['copy_digits']}` | "
            f"`{row['literal_digits']}` | `{row['copy_items']}` | "
            f"`{row['seed_copy_items']}/{row['prior_copy_items']}` | "
            f"`{row['control_coverage_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The hybrid seed+prior-tape subcodec is promoted only if paid bits beat raw tape and shuffled controls.",
            "- Coverage alone is not enough; source, origin, length, mode, and residual literal costs are charged.",
            "- Under this gate the literal innovation tape remains an external payload dependency.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)


if __name__ == "__main__":
    main()
