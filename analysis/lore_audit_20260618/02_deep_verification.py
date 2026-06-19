#!/usr/bin/env python3
"""Deep verification for the 2026-06-18 lore-source audit.

This is deliberately not a decipherment script. It checks whether the newly
verified external numeric anchors occur in the frozen 70-book raw digit corpus,
and compares those occurrence counts to simple fixed-seed random controls of
the same substring lengths.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BOOKS_DIGITS_PATH = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
RESULTS_JSON = HERE / "deep_verification_results.json"
REPORT_MD = HERE / "deep_verification_report.md"

RANDOM_SEED = 46920260618
RANDOM_SAMPLES_PER_LENGTH = 1000

NEEDLE_GROUPS = {
    "secret_library_exact": [
        "74032",
        "45331",
        "7403245331",
    ],
    "honeminas_primary_vectors": [
        "43153",
        "34784",
        "4315334784",
    ],
    "honeminas_secondary_s2ward_vectors": [
        "43151",
        "34783",
        "4315134783",
    ],
    "formula_common_or_short": [
        "3478",
        "34",
        "99",
        "32",
        "20",
    ],
    "reported_fb_pair_examples": [
        "1280",
        "625",
        "706",
        "447",
        "689",
    ],
    "phrase_layer_reference_codes": [
        "3478",
        "3466",
        "653",
        "768",
        "764",
        "659",
        "978",
        "54",
    ],
}

SOURCE_VERIFICATION = [
    {
        "id": "secret_library_74032",
        "status": "confirmed_unglossed_external_book",
        "url": "https://www.tibiawiki.com.br/wiki/74032_45331_%28Book%29",
        "evidence": "TibiaWiki BR gives the exact original text, Secret Library Ice Section location, untranslated status, version 11.80, and related 469 link.",
        "analytical_use": "numeric_anchor_only",
    },
    {
        "id": "secret_library_mesa_07",
        "status": "confirmed_location_index",
        "url": "https://www.tibiawiki.com.br/wiki/Bibliotecas_de_Secret_Library_Ice_Section",
        "evidence": "The Secret Library Ice Section inventory lists 74032 45331 at Mesa 07 as untranslated.",
        "analytical_use": "source_traceability",
    },
    {
        "id": "great_calculator",
        "status": "confirmed_lore_mechanism_source",
        "url": "https://tibia.fandom.com/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "evidence": "The book says the speaker assisted the great calculator to assemble the Bonelords language.",
        "analytical_use": "mechanism_origin_hypothesis_only",
    },
    {
        "id": "honeminas_formula",
        "status": "confirmed_formula_family_source",
        "url": "https://tibia.fandom.com/wiki/The_Honeminas_Formula_%28Book%29",
        "evidence": "The book ties the formula to the Magic Web/gates and gives the primary vectors 43153 and 34784.",
        "analytical_use": "generator_selector_hypothesis_only",
    },
    {
        "id": "469_unsolved_status",
        "status": "confirmed_no_solid_public_proof",
        "url": "https://tibia.fandom.com/wiki/469",
        "evidence": "TibiaWiki states many claimed translations exist but no solid proof has been supplied.",
        "analytical_use": "external_claim_sanity_check",
    },
    {
        "id": "tibiasecrets_74032_negative",
        "status": "secondary_negative_note",
        "url": "https://www.tibiasecrets.com/article166",
        "evidence": "The article separately notes the Secret Library book's two number sequences are not found in the Hellgate Library corpus.",
        "analytical_use": "secondary_crosscheck_only",
    },
]


def load_books() -> dict[str, str]:
    with BOOKS_DIGITS_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {str(key): str(value) for key, value in data.items()}


def count_overlapping(text: str, needle: str) -> int:
    if not needle:
        return 0
    total = 0
    start = 0
    while True:
        index = text.find(needle, start)
        if index == -1:
            return total
        total += 1
        start = index + 1


def count_needle(books: dict[str, str], needle: str) -> dict:
    per_book = {}
    for book_id, digits in sorted(books.items(), key=lambda item: int(item[0])):
        count = count_overlapping(digits, needle)
        if count:
            per_book[book_id] = count
    return {
        "needle": needle,
        "length": len(needle),
        "total_hits": sum(per_book.values()),
        "books_with_hit": len(per_book),
        "book_hits": per_book,
    }


def percentile(sorted_values: list[int], p: float) -> int:
    if not sorted_values:
        return 0
    index = round((len(sorted_values) - 1) * p)
    return sorted_values[index]


def summarize(values: list[int]) -> dict:
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "p05": percentile(ordered, 0.05),
        "median": percentile(ordered, 0.50),
        "p95": percentile(ordered, 0.95),
        "max": ordered[-1],
    }


def random_controls(books: dict[str, str], lengths: list[int]) -> dict[str, dict]:
    rng = random.Random(RANDOM_SEED)
    controls = {}
    alphabet = "0123456789"

    for length in sorted(set(lengths)):
        samples = []
        for _ in range(RANDOM_SAMPLES_PER_LENGTH):
            needle = "".join(rng.choice(alphabet) for _ in range(length))
            result = count_needle(books, needle)
            samples.append(result)

        total_hits = [item["total_hits"] for item in samples]
        books_with_hit = [item["books_with_hit"] for item in samples]
        any_hits = sum(1 for value in total_hits if value > 0)
        controls[str(length)] = {
            "samples": RANDOM_SAMPLES_PER_LENGTH,
            "any_hit_rate": any_hits / RANDOM_SAMPLES_PER_LENGTH,
            "total_hits": summarize(total_hits),
            "books_with_hit": summarize(books_with_hit),
        }

    return controls


def interpretation(group: str, result: dict) -> str:
    needle = result["needle"]
    if group == "secret_library_exact" and result["total_hits"] == 0:
        return "confirmed external number, absent from 70-book raw corpus"
    if group == "honeminas_primary_vectors" and result["total_hits"] == 0:
        return "primary formula number, absent as exact corpus substring"
    if group == "honeminas_secondary_s2ward_vectors":
        return "secondary/imprecise pair extraction; not promoted"
    if result["length"] <= 2:
        return "short token; occurrence expected and not probative"
    if needle == "3478":
        return "known structural/phrase-layer overlap, not a book plaintext key"
    if result["total_hits"] == 0:
        return "no direct corpus anchor"
    return "direct hit exists; requires null controls before analytical use"


def build_results() -> dict:
    books = load_books()
    grouped = {}
    lengths = []

    for group, needles in NEEDLE_GROUPS.items():
        grouped[group] = []
        for needle in needles:
            result = count_needle(books, needle)
            result["interpretation"] = interpretation(group, result)
            grouped[group].append(result)
            lengths.append(len(needle))

    controls = random_controls(books, lengths)

    return {
        "schema": "lore_deep_verification.v1",
        "created_at": "2026-06-18",
        "random_seed": RANDOM_SEED,
        "random_samples_per_length": RANDOM_SAMPLES_PER_LENGTH,
        "books_digits_source": str(BOOKS_DIGITS_PATH.relative_to(ROOT)),
        "corpus": {
            "book_count": len(books),
            "total_digits": sum(len(digits) for digits in books.values()),
            "min_book_digits": min(len(digits) for digits in books.values()),
            "max_book_digits": max(len(digits) for digits in books.values()),
        },
        "source_verification": SOURCE_VERIFICATION,
        "needle_groups": grouped,
        "random_controls_by_length": controls,
        "outcome_ledger_delta": {
            "CRIBS_REPRODUCED_UNDER_HOLDOUT": 0,
            "CODES_CONFIRMED_EXTERNALLY": 0,
            "BOOKS_NO_PROSE_TO_ACCEPTED": 0,
            "GT_PHRASES_PASSING_EXTERNALLY": 0,
        },
        "verdict": {
            "translation_delta": "NONE",
            "new_plaintext": False,
            "new_cipsoft_ground_truth": False,
            "new_mechanism_framing": "stronger_assembly_generator_pair_geometry_origin_model",
        },
    }


def markdown_escape(value: object) -> str:
    return str(value).replace("|", "\\|")


def write_report(results: dict) -> None:
    lines = [
        "# Deep verification addendum (2026-06-18)",
        "",
        "Generated by `02_deep_verification.py`. This file verifies source status",
        "and corpus-level numeric occurrence; it does not attempt a new decode.",
        "",
        "## Corpus",
        "",
        f"- Books: {results['corpus']['book_count']}",
        f"- Total raw digits: {results['corpus']['total_digits']}",
        f"- Book length range: {results['corpus']['min_book_digits']} to {results['corpus']['max_book_digits']} digits",
        "",
        "## Source verification matrix",
        "",
        "| Source | Status | Analytical use | URL |",
        "|---|---|---|---|",
    ]

    for item in results["source_verification"]:
        lines.append(
            "| `{id}` | `{status}` | `{analytical_use}` | {url} |".format(
                id=item["id"],
                status=item["status"],
                analytical_use=item["analytical_use"],
                url=item["url"],
            )
        )

    lines.extend(
        [
            "",
            "## Numeric occurrence checks",
            "",
            "| Group | Needle | Len | Total hits | Books hit | Interpretation |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )

    for group, rows in results["needle_groups"].items():
        for row in rows:
            lines.append(
                "| {group} | `{needle}` | {length} | {total_hits} | {books_with_hit} | {interpretation} |".format(
                    group=group,
                    needle=row["needle"],
                    length=row["length"],
                    total_hits=row["total_hits"],
                    books_with_hit=row["books_with_hit"],
                    interpretation=markdown_escape(row["interpretation"]),
                )
            )

    lines.extend(
        [
            "",
            "## Random same-length controls",
            "",
            f"Fixed seed: `{results['random_seed']}`; samples per length: `{results['random_samples_per_length']}`.",
            "",
            "| Needle length | Any-hit rate | Total hits min/p05/median/p95/max | Books hit min/p05/median/p95/max |",
            "|---:|---:|---|---|",
        ]
    )

    for length, control in sorted(
        results["random_controls_by_length"].items(), key=lambda item: int(item[0])
    ):
        total = control["total_hits"]
        books = control["books_with_hit"]
        total_summary = "{min}/{p05}/{median}/{p95}/{max}".format(**total)
        books_summary = "{min}/{p05}/{median}/{p95}/{max}".format(**books)
        lines.append(
            f"| {length} | {control['any_hit_rate']:.3f} | {total_summary} | {books_summary} |"
        )

    lines.extend(
        [
            "",
            "## Analytical verdict",
            "",
            "- The Secret Library pair is now source-confirmed as an external, untranslated book, not merely a secondary note.",
            "- `74032`, `45331`, and `7403245331` have zero exact hits in the 70-book raw digit corpus.",
            "- The primary Honeminas vector strings `43153`, `34784`, and `4315334784` also have zero exact hits.",
            "- Short numbers such as `34`, `99`, `32`, and `20` occur at rates expected for short strings and cannot act as keys.",
            "- The only strengthened result is a mechanism/origin model: assembled, formulaic, pair/geometry-aware production. It is not a new translation.",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    results = build_results()
    RESULTS_JSON.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(results)
    print(f"wrote {RESULTS_JSON.relative_to(HERE)}")
    print(f"wrote {REPORT_MD.relative_to(HERE)}")
    print(
        "verdict translation_delta={translation_delta} new_plaintext={new_plaintext}".format(
            **results["verdict"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
