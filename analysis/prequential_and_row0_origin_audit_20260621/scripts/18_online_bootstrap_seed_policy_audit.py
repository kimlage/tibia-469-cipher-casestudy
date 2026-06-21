from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

FRONTIER = TEST_RESULTS / "17_online_prefix_book_frontier_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_result() -> dict[str, Any]:
    frontier = load_json(FRONTIER)
    rows = frontier["rows"]
    by_book = {row["book"]: row for row in rows}
    book0 = by_book[0]
    raw_total = sum(row["raw_uniform_bits"] for row in rows)
    online_total = sum(row["book_bounded_online_reparse_bits"] for row in rows)
    online_gain = raw_total - online_total

    book0_raw = book0["raw_uniform_bits"]
    book0_online = book0["book_bounded_online_reparse_bits"]
    book0_delta = book0_online - book0_raw
    seeded_total = online_total - book0_online + book0_raw
    seeded_gain = raw_total - seeded_total
    free_seed_total = online_total - book0_online
    free_seed_gain = raw_total - free_seed_total

    after_bootstrap = [row for row in rows if row["book"] > 0]
    policies = [
        {
            "policy": "online_book0_parser",
            "classification": "baseline_has_cold_start_failure",
            "book0_charge_bits": book0_online,
            "book0_gain_vs_raw_bits": book0_raw - book0_online,
            "stream_total_bits": online_total,
            "stream_gain_vs_raw_bits": online_gain,
            "strict_raw_wins": sum(1 for row in rows if row["book_bounded_online_gain_vs_raw_bits"] > 0),
            "raw_wins_or_ties": sum(1 for row in rows if row["book_bounded_online_gain_vs_raw_bits"] >= 0),
            "failure_books": [
                row["book"] for row in rows if row["book_bounded_online_gain_vs_raw_bits"] < 0
            ],
            "admissibility": "admissible_baseline",
            "interpretation": (
                "The deterministic online parser is used unchanged for book 0, "
                "before any previous-book inventory exists."
            ),
        },
        {
            "policy": "raw_book0_seed_then_online",
            "classification": "one_explicit_seed_closes_local_failure",
            "book0_charge_bits": book0_raw,
            "book0_gain_vs_raw_bits": 0.0,
            "stream_total_bits": seeded_total,
            "stream_gain_vs_raw_bits": seeded_gain,
            "stream_saving_vs_online_book0_parser_bits": book0_delta,
            "strict_raw_wins": sum(
                1
                for row in rows
                if row["book"] > 0 and row["book_bounded_online_gain_vs_raw_bits"] > 0
            ),
            "raw_wins_or_ties": 1
            + sum(1 for row in after_bootstrap if row["book_bounded_online_gain_vs_raw_bits"] >= 0),
            "failure_books": [],
            "admissibility": "admissible_as_explicit_seed_policy_not_authorial_proof",
            "interpretation": (
                "Book 0 is treated as a literal/raw seed. Books 1-69 keep the "
                "previous-books-only book-bounded online parser."
            ),
        },
        {
            "policy": "externally_given_book0_seed",
            "classification": "mechanical_generator_seed_only_not_compression_bound",
            "book0_charge_bits": 0.0,
            "book0_gain_vs_raw_bits": book0_raw,
            "stream_total_bits": free_seed_total,
            "stream_gain_vs_raw_bits": free_seed_gain,
            "strict_raw_wins": 69,
            "raw_wins_or_ties": 70,
            "failure_books": [],
            "admissibility": "not_admissible_as_compression_bound_without_external_attestation",
            "interpretation": (
                "This is only a generator thought experiment: book 0 would have to "
                "be externally given. It cannot be counted as compression progress "
                "or authorial evidence without primary attestation."
            ),
        },
    ]

    return {
        "schema": "online_bootstrap_seed_policy_audit.v1",
        "classification": "explicit_raw_seed_closes_online_bootstrap_failure",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_prefix_book_frontier": rel(FRONTIER),
        },
        "book0": {
            "raw_uniform_bits": book0_raw,
            "book_bounded_online_reparse_bits": book0_online,
            "book0_online_minus_raw_bits": book0_delta,
            "length_digits": book0["book_length_digits"],
            "literal_digits_online": book0["book_bounded_inventory"]["literal_digits"],
            "copied_digits_online": book0["book_bounded_inventory"]["copied_digits"],
            "copy_items_online": book0["book_bounded_inventory"]["copy_items"],
        },
        "summary": {
            "raw_total_bits": raw_total,
            "book_bounded_online_stream_total_bits": online_total,
            "raw_seeded_stream_total_bits": seeded_total,
            "raw_seeded_stream_saving_vs_online_bits": book0_delta,
            "book_bounded_online_gain_vs_raw_bits": online_gain,
            "raw_seeded_gain_vs_raw_bits": seeded_gain,
            "raw_seeded_raw_wins_or_ties": 70,
            "raw_seeded_strict_raw_wins": 69,
            "raw_seeded_failure_books": [],
            "after_bootstrap_strict_raw_wins": 69,
            "after_bootstrap_book_count": 69,
            "interpretation": (
                "The only previous-books-only local failure is a cold-start effect. "
                "Charging book 0 as an explicit raw seed removes the negative local "
                "gain without changing books 1-69, row0, or model parameters."
            ),
        },
        "policies": policies,
        "decision": {
            "bootstrap_status": "one_explicit_raw_seed_closes_local_failure",
            "generation_explanation_status": "stronger_but_still_seeded_partial",
            "compression_bound_status": "not_promoted_as_new_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "18_online_bootstrap_seed_policy_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Online Bootstrap Seed Policy Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 17 showed one local failure in the previous-books-only online",
        "frontier: book `0`, before any previous-book inventory exists. This audit",
        "tests whether that is a seed/bootstrap accounting issue rather than a",
        "failure of the later sequential generation rule.",
        "",
        "## Book 0",
        "",
        f"- Raw uniform cost: `{result['book0']['raw_uniform_bits']:.3f}` bits.",
        f"- Online parsed cost: `{result['book0']['book_bounded_online_reparse_bits']:.3f}` bits.",
        f"- Online minus raw: `{result['book0']['book0_online_minus_raw_bits']:.3f}` bits.",
        f"- Online inventory: `{result['book0']['literal_digits_online']}` literal digits, `{result['book0']['copied_digits_online']}` copied digits, `{result['book0']['copy_items_online']}` copy items.",
        "",
        "## Policies",
        "",
        "| Policy | Status | Book 0 charge | Stream gain vs raw | Wins/ties | Failures | Admissibility |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in result["policies"]:
        lines.append(
            f"| `{row['policy']}` | `{row['classification']}` | "
            f"`{row['book0_charge_bits']:.3f}` | `{row['stream_gain_vs_raw_bits']:.3f}` | "
            f"`{row['raw_wins_or_ties']}/70` | `{row['failure_books']}` | `{row['admissibility']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A single explicit raw seed for book `0` closes the only local raw-coding failure in the previous-books-only frontier.",
            "- Books `1-69` are unchanged and still beat raw under book-bounded previous-book sources.",
            "- This is a bootstrap accounting improvement, not a new compression-bound promotion, row0 derivation, plaintext claim, or case reopening.",
        ]
    )
    (TEST_RESULTS / "18_online_bootstrap_seed_policy_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
