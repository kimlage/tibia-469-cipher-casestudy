from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
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
REPLAY_GATE = TEST_RESULTS / "01_innovation_tape_replay_gate.json"

OUT_STEM = "03_innovation_tape_structure_gate"
SEED_BOOKS = list(range(10))
MIN_COVER_LENGTHS = [2, 3, 4, 5]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"


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


def canonical_tape(ops_by_book: dict[str, list[dict[str, Any]]]) -> str:
    parts = []
    for book in range(10, 70):
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                parts.append(op.get("payload", ""))
    return "".join(parts)


def seed_text(books: dict[int, str]) -> str:
    return "".join(books[book] for book in SEED_BOOKS)


def longest_external_match(text: str, pos: int, source: str, min_len: int) -> int:
    max_len = 0
    if pos + min_len > len(text):
        return 0
    needle = text[pos : pos + min_len]
    index = source.find(needle)
    while index != -1:
        length = min_len
        cap = min(len(text) - pos, len(source) - index)
        while length < cap and text[pos + length] == source[index + length]:
            length += 1
        max_len = max(max_len, length)
        index = source.find(needle, index + 1)
    return max_len


def greedy_external_cover(text: str, source: str, min_len: int) -> dict[str, Any]:
    pos = 0
    covered = 0
    items = 0
    literal_digits = 0
    while pos < len(text):
        length = longest_external_match(text, pos, source, min_len)
        if length >= min_len:
            covered += length
            items += 1
            pos += length
        else:
            literal_digits += 1
            pos += 1
    return {
        "min_len": min_len,
        "covered_digits": covered,
        "literal_digits": literal_digits,
        "copy_items": items,
        "coverage_fraction": covered / len(text) if text else 0.0,
    }


def longest_prior_tape_match(text: str, pos: int, min_len: int) -> int:
    if pos + min_len > len(text):
        return 0
    source = text[:pos]
    if len(source) < min_len:
        return 0
    return longest_external_match(text, pos, source, min_len)


def greedy_prior_tape_cover(text: str, min_len: int) -> dict[str, Any]:
    pos = 0
    covered = 0
    items = 0
    literal_digits = 0
    while pos < len(text):
        length = longest_prior_tape_match(text, pos, min_len)
        if length >= min_len:
            covered += length
            items += 1
            pos += length
        else:
            literal_digits += 1
            pos += 1
    return {
        "min_len": min_len,
        "covered_digits": covered,
        "literal_digits": literal_digits,
        "copy_items": items,
        "coverage_fraction": covered / len(text) if text else 0.0,
    }


def prev_context(prefix: str, order: int) -> str:
    if order == 0:
        return ""
    return prefix[-order:].rjust(order, "^")


def prequential_markov_bits(text: str, order: int) -> float:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0.0
    prefix = ""
    for digit in text:
        context = prev_context(prefix, order)
        counter = counts[context]
        probability = (counter[digit] + ALPHA) / (
            sum(counter.values()) + ALPHA * len(DIGITS)
        )
        total += -math.log2(probability)
        counter[digit] += 1
        prefix += digit
    return total


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


def control_distribution(
    tape: str,
    source: str,
    metric: str,
    min_len: int | None = None,
    order: int | None = None,
) -> dict[str, Any]:
    rng = random.Random(
        RANDOM_SEED
        + sum(ord(ch) for ch in metric)
        + (min_len or 0) * 101
        + (order or 0) * 1009
    )
    chars = list(tape)
    values = []
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        shuffled = "".join(chars)
        if metric == "seed_cover":
            values.append(greedy_external_cover(shuffled, source, min_len or 2)["covered_digits"])
        elif metric == "prior_tape_cover":
            values.append(greedy_prior_tape_cover(shuffled, min_len or 2)["covered_digits"])
        elif metric == "markov_bits":
            values.append(prequential_markov_bits(shuffled, order or 0))
        else:
            raise KeyError(metric)
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "mean": mean(values),
        "p05": percentile(values, 0.05),
        "p95": percentile(values, 0.95),
        "min": values[0],
        "max": values[-1],
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    replay = load_json(REPLAY_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("innovation_tape_replay_gate", replay)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape = canonical_tape(ledger["canonical_ops_by_book"])
    seeds = seed_text(books)
    seed_rows = []
    prior_rows = []
    for min_len in MIN_COVER_LENGTHS:
        observed_seed = greedy_external_cover(tape, seeds, min_len)
        seed_control = control_distribution(tape, seeds, "seed_cover", min_len=min_len)
        seed_rows.append(
            {
                **observed_seed,
                "control_mean": seed_control["mean"],
                "control_p95": seed_control["p95"],
                "beats_control_p95": observed_seed["covered_digits"] > seed_control["p95"],
            }
        )
        observed_prior = greedy_prior_tape_cover(tape, min_len)
        prior_control = control_distribution(tape, seeds, "prior_tape_cover", min_len=min_len)
        prior_rows.append(
            {
                **observed_prior,
                "control_mean": prior_control["mean"],
                "control_p95": prior_control["p95"],
                "beats_control_p95": observed_prior["covered_digits"] > prior_control["p95"],
            }
        )
    markov_rows = []
    for order in [0, 1, 2]:
        observed = prequential_markov_bits(tape, order)
        control = control_distribution(tape, seeds, "markov_bits", order=order)
        markov_rows.append(
            {
                "order": order,
                "bits": observed,
                "bits_per_digit": observed / len(tape),
                "control_mean": control["mean"],
                "control_p05": control["p05"],
                "beats_control_p05": observed < control["p05"],
            }
        )
    best_seed = max(seed_rows, key=lambda row: row["covered_digits"])
    best_prior = max(prior_rows, key=lambda row: row["covered_digits"])
    best_markov = min(markov_rows, key=lambda row: row["bits"])
    promotes_structure = (
        best_seed["beats_control_p95"]
        or best_prior["beats_control_p95"]
        or best_markov["beats_control_p05"]
    )
    summary = {
        "literal_tape_digits": len(tape),
        "seed_text_digits": len(seeds),
        "best_seed_min_len": best_seed["min_len"],
        "best_seed_covered_digits": best_seed["covered_digits"],
        "best_seed_control_p95": best_seed["control_p95"],
        "best_prior_min_len": best_prior["min_len"],
        "best_prior_covered_digits": best_prior["covered_digits"],
        "best_prior_control_p95": best_prior["control_p95"],
        "best_markov_order": best_markov["order"],
        "best_markov_bits": best_markov["bits"],
        "best_markov_bpd": best_markov["bits_per_digit"],
        "best_markov_control_p05": best_markov["control_p05"],
        "promotes_tape_structure": promotes_structure,
        "interpretation": (
            "This gate asks whether the innovation tape itself has a mechanical "
            "source: seed-derived coverage, self-recurrence, or prequential "
            "digit structure beyond shuffled controls."
        ),
    }
    return {
        "schema": "innovation_tape_structure_gate_v1",
        "scope": "analysis_only_innovation_tape_structure_controls",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "innovation_tape_replay_gate": rel(REPLAY_GATE),
        },
        "seed_cover_rows": seed_rows,
        "prior_tape_cover_rows": prior_rows,
        "markov_rows": markov_rows,
        "summary": summary,
        "classification": (
            "innovation_tape_structure_promoted"
            if promotes_structure
            else "innovation_tape_structure_not_promoted"
        ),
        "decision": {
            "promotes_tape_structure": promotes_structure,
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
        "# Innovation Tape Structure Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the `266`-digit innovation tape has structure of its own:",
        "coverage by seed-book substrings, coverage by prior tape substrings, or",
        "prequential Markov digit predictability beyond shuffled same-multiset",
        "controls.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Seed text digits: `{s['seed_text_digits']}`.",
        f"- Best seed min length: `{s['best_seed_min_len']}`.",
        f"- Best seed covered digits: `{s['best_seed_covered_digits']}`.",
        f"- Best seed control p95: `{s['best_seed_control_p95']:.3f}`.",
        f"- Best prior-tape min length: `{s['best_prior_min_len']}`.",
        f"- Best prior-tape covered digits: `{s['best_prior_covered_digits']}`.",
        f"- Best prior-tape control p95: `{s['best_prior_control_p95']:.3f}`.",
        f"- Best Markov order: `{s['best_markov_order']}`.",
        f"- Best Markov bits: `{s['best_markov_bits']:.3f}`.",
        f"- Best Markov bpd: `{s['best_markov_bpd']:.6f}`.",
        f"- Best Markov control p05: `{s['best_markov_control_p05']:.3f}`.",
        f"- Promotes tape structure: `{s['promotes_tape_structure']}`.",
        "",
        s["interpretation"],
        "",
        "## Seed Coverage",
        "",
        "| Min len | Covered | Literal residual | Copy items | Control p95 | Beats p95 |",
        "| ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["seed_cover_rows"]:
        lines.append(
            f"| `{row['min_len']}` | `{row['covered_digits']}` | "
            f"`{row['literal_digits']}` | `{row['copy_items']}` | "
            f"`{row['control_p95']:.3f}` | `{row['beats_control_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Prior Tape Coverage",
            "",
            "| Min len | Covered | Literal residual | Copy items | Control p95 | Beats p95 |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["prior_tape_cover_rows"]:
        lines.append(
            f"| `{row['min_len']}` | `{row['covered_digits']}` | "
            f"`{row['literal_digits']}` | `{row['copy_items']}` | "
            f"`{row['control_p95']:.3f}` | `{row['beats_control_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Markov Rows",
            "",
            "| Order | Bits | Bits/digit | Control p05 | Beats p05 |",
            "| ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["markov_rows"]:
        lines.append(
            f"| `{row['order']}` | `{row['bits']:.3f}` | "
            f"`{row['bits_per_digit']:.6f}` | "
            f"`{row['control_p05']:.3f}` | `{row['beats_control_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Tape structure is promoted only if it beats same-multiset shuffled controls.",
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
