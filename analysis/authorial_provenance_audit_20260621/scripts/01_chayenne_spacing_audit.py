#!/usr/bin/env python3
"""Audit the spacing in Chayenne's 2009 numeric 469 reply.

This is intentionally analysis-only. It tests whether the primary-source
spacing in the Chayenne answer behaves like a mechanically meaningful boundary
in the committed 70-book digit corpus. It does not test or promote plaintext.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
BOOKS_PATH = REPO_ROOT / "analysis/audit_20260609/books_digits.json"
OUT_DIR = (
    REPO_ROOT
    / "analysis/authorial_provenance_audit_20260621/reports/test_results"
)
JSON_OUT = OUT_DIR / "01_chayenne_spacing_audit.json"
MD_OUT = OUT_DIR / "01_chayenne_spacing_audit.md"

SOURCE_URLS = {
    "portaltibia_chayenne_2009": "https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/",
    "tibiawiki_br_469_stable": "https://www.tibiawiki.com.br/index.php?stableid=140740&title=469",
    "s2ward_issue_3": "https://github.com/s2ward/469/issues/3",
    "solvingtibia_reddit_thread": "https://www.reddit.com/r/SolvingTibia/comments/tkam3x/469_a_language_blinked_between_entities/",
}

CHAYENNE_BLOCKS = [
    "114514519485611451908304576512282177",
    "6612527570584",
]
CHAYENNE_SOURCE_SURFACE = (
    "114514519485611451908304576512282177 [visible emoticon/image separator] 6612527570584 xD"
)
RANDOM_SEED = 46920260621
SHUFFLE_TRIALS = 2000
SPLIT_SHUFFLE_TRIALS = 1000


def load_books() -> Dict[int, str]:
    raw = json.loads(BOOKS_PATH.read_text())
    return {int(k): str(v) for k, v in raw.items()}


def find_occurrences(books: Dict[int, str], needle: str) -> List[Dict[str, int]]:
    hits: List[Dict[str, int]] = []
    for book_id in sorted(books):
        text = books[book_id]
        start = 0
        while True:
            pos = text.find(needle, start)
            if pos < 0:
                break
            hits.append({"book": book_id, "start": pos})
            start = pos + 1
    return hits


def context_snippets(
    books: Dict[int, str],
    hits: Iterable[Dict[str, int]],
    needle: str,
    flank: int = 12,
    limit: int = 12,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for hit in list(hits)[:limit]:
        text = books[hit["book"]]
        start = hit["start"]
        end = start + len(needle)
        rows.append(
            {
                "book": hit["book"],
                "start": start,
                "pre": text[max(0, start - flank) : start],
                "match": needle,
                "post": text[end : end + flank],
            }
        )
    return rows


def substring_distribution(books: Dict[int, str], needle: str) -> Dict[str, object]:
    n = len(needle)
    counts: Counter[str] = Counter()
    for text in books.values():
        for i in range(0, max(0, len(text) - n + 1)):
            counts[text[i : i + n]] += 1
    target_count = counts[needle]
    ge_count = (
        sum(1 for value in counts.values() if value >= target_count)
        if target_count
        else None
    )
    return {
        "length": n,
        "target_count": target_count,
        "unique_substrings": len(counts),
        "max_count": max(counts.values()) if counts else 0,
        "num_substrings_at_or_above_target_count": ge_count,
        "top_rank_fraction": ge_count / len(counts) if counts and ge_count else None,
    }


def build_substring_sets_by_len(books: Dict[int, str], max_len: int) -> Dict[int, set]:
    by_len = {}
    for n in range(1, max_len + 1):
        values = set()
        for text in books.values():
            for i in range(0, max(0, len(text) - n + 1)):
                values.add(text[i : i + n])
        by_len[n] = values
    return by_len


def valid_full_split_boundaries_from_sets(
    joined: str, substrings_by_len: Dict[int, set]
) -> List[int]:
    out: List[int] = []
    for boundary in range(1, len(joined)):
        left = joined[:boundary]
        right = joined[boundary:]
        if (
            left in substrings_by_len.get(len(left), set())
            and right in substrings_by_len.get(len(right), set())
        ):
            out.append(boundary)
    return out


def shuffle_string(rng: random.Random, text: str) -> str:
    chars = list(text)
    rng.shuffle(chars)
    return "".join(chars)


def shuffle_hit_controls(books: Dict[int, str], targets: Dict[str, str]) -> Dict[str, object]:
    rng = random.Random(RANDOM_SEED)
    controls: Dict[str, object] = {}
    for label, target in targets.items():
        hit_trials = 0
        for _ in range(SHUFFLE_TRIALS):
            shuffled = shuffle_string(rng, target)
            if find_occurrences(books, shuffled):
                hit_trials += 1
        controls[label] = {
            "trials": SHUFFLE_TRIALS,
            "hit_trials": hit_trials,
            "hit_rate": hit_trials / SHUFFLE_TRIALS,
        }
    return controls


def shuffle_split_controls(books: Dict[int, str], joined: str) -> Dict[str, object]:
    rng = random.Random(RANDOM_SEED + 1)
    substrings_by_len = build_substring_sets_by_len(books, len(joined) - 1)
    split_hit_trials = 0
    first_examples: List[Dict[str, object]] = []
    for trial in range(SPLIT_SHUFFLE_TRIALS):
        shuffled = shuffle_string(rng, joined)
        boundaries = valid_full_split_boundaries_from_sets(shuffled, substrings_by_len)
        if boundaries:
            split_hit_trials += 1
            if len(first_examples) < 5:
                first_examples.append({"trial": trial, "boundaries": boundaries})
    return {
        "trials": SPLIT_SHUFFLE_TRIALS,
        "split_hit_trials": split_hit_trials,
        "hit_rate": split_hit_trials / SPLIT_SHUFFLE_TRIALS,
        "first_examples": first_examples,
    }


def pairs_from_start(text: str) -> List[str]:
    return [text[i : i + 2] for i in range(0, len(text), 2)]


def binary_profile(text: str) -> Dict[str, object]:
    value = int(text)
    bit_length = value.bit_length()
    return {
        "digits": len(text),
        "parity_mod_2": len(text) % 2,
        "digit_length_mod_5": len(text) % 5,
        "digit_length_mod_10": len(text) % 10,
        "integer_bit_length": bit_length,
        "integer_bit_length_mod_5": bit_length % 5,
    }


def md_table(rows: List[List[object]], headers: List[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_markdown(result: Dict[str, object]) -> None:
    chunks = result["chunks"]
    controls = result["controls"]
    split = result["summary"]
    distribution = result["distribution"]
    pair_alignment = result["pair_alignment"]

    rows = []
    for chunk in chunks:
        rows.append(
            [
                chunk["label"],
                chunk["length_digits"],
                chunk["occurrence_count"],
                ", ".join(f'{h["book"]}:{h["start"]}' for h in chunk["occurrences"]),
            ]
        )

    dist_rows = []
    for label, row in distribution.items():
        top_fraction = row["top_rank_fraction"]
        dist_rows.append(
            [
                label,
                row["length"],
                row["target_count"],
                row["max_count"],
                row["unique_substrings"],
                row["num_substrings_at_or_above_target_count"]
                if row["num_substrings_at_or_above_target_count"] is not None
                else "n/a",
                f"{top_fraction:.6f}" if top_fraction is not None else "n/a",
            ]
        )

    control_rows = []
    for label, row in controls["shuffle_hit_controls"].items():
        control_rows.append(
            [label, row["trials"], row["hit_trials"], f'{row["hit_rate"]:.6f}']
        )
    control_rows.append(
        [
            "joined_valid_full_split",
            controls["shuffle_split_controls"]["trials"],
            controls["shuffle_split_controls"]["split_hit_trials"],
            f'{controls["shuffle_split_controls"]["hit_rate"]:.6f}',
        ]
    )

    body = f"""# Chayenne Spacing Audit

Status: `analysis_only`

Translation delta: `NONE`

Plaintext claim: `false`

Case reopened: `false`

## Primary Surface

Source surface:

```text
{CHAYENNE_SOURCE_SURFACE}
```

The primary-source answer has two numeric blocks separated by a visible
emoticon/image marker and whitespace. This audit tests that visible boundary
as a mechanical boundary only.

## Result

- Joined numeric string occurrence count: `{split["joined_occurrence_count"]}`
- Valid full split boundaries where both sides are attested book substrings:
  `{split["valid_full_split_boundaries"]}`
- Source boundary: `{split["source_boundary"]}`
- Source boundary is unique full split: `{split["source_boundary_unique_full_split"]}`

{md_table(rows, ["chunk", "length", "occurrences", "book:start hits"])}

## Repetition Rank

{md_table(dist_rows, ["target", "length", "target count", "max count", "unique substrings", "count >= target", "top fraction"])}

## Negative Controls

{md_table(control_rows, ["control", "trials", "hits", "hit rate"])}

## Pair And Binary Alignment

- Block 1 pairs from start: `{pair_alignment["block_1_pairs_from_start"]}`
- Block 2 pairs from start: `{pair_alignment["block_2_pairs_from_start"]}`
- Block 2 pairs with leading zero: `{pair_alignment["block_2_pairs_with_leading_zero"]}`
- Block 2 pairs with trailing zero: `{pair_alignment["block_2_pairs_with_trailing_zero"]}`
- Joined pairs from start: `{pair_alignment["joined_pairs_from_start"]}`

Binary/integer profiles are included in the JSON. The relevant finding is that
the second block and the joined string are not naturally 2-digit aligned, and
the integer bit lengths do not produce a clean 5-bit eye grouping.

## Decision

Classification: `PROMOTED_MECHANICAL_CLUE`

Narrow claim:
`chayenne_primary_separator_marks_unique_join_between_two_attested_book_substrings`

This does not promote word spacing, plaintext, translation, row0 origin, or an
authorial origin formula. It supports a narrower provenance/mechanical clue:
Chayenne's public numeric answer appears to have been assembled from two
existing 469-corpus numeric modules, with the visible source separator preserving
their join.

Row0 status: `unchanged_exogenous`

Translation/plaintext status: `NONE`
"""
    MD_OUT.write_text(body)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = load_books()
    joined = "".join(CHAYENNE_BLOCKS)
    source_boundary = len(CHAYENNE_BLOCKS[0])

    chunk_rows = []
    for idx, block in enumerate(CHAYENNE_BLOCKS, start=1):
        hits = find_occurrences(books, block)
        chunk_rows.append(
            {
                "label": f"block_{idx}",
                "text": block,
                "length_digits": len(block),
                "occurrence_count": len(hits),
                "occurrences": hits,
                "context_examples": context_snippets(books, hits, block),
            }
        )

    joined_hits = find_occurrences(books, joined)
    substrings_by_len = build_substring_sets_by_len(books, len(joined) - 1)
    valid_boundaries = valid_full_split_boundaries_from_sets(joined, substrings_by_len)

    distribution = {
        "block_1": substring_distribution(books, CHAYENNE_BLOCKS[0]),
        "block_2": substring_distribution(books, CHAYENNE_BLOCKS[1]),
        "joined": substring_distribution(books, joined),
    }

    controls = {
        "shuffle_hit_controls": shuffle_hit_controls(
            books,
            {
                "block_1": CHAYENNE_BLOCKS[0],
                "block_2": CHAYENNE_BLOCKS[1],
                "joined": joined,
            },
        ),
        "shuffle_split_controls": shuffle_split_controls(books, joined),
    }

    result = {
        "audit": "01_chayenne_spacing_audit",
        "status": "analysis_only",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_urls": SOURCE_URLS,
        "primary_surface": CHAYENNE_SOURCE_SURFACE,
        "chunks": chunk_rows,
        "summary": {
            "joined_numeric": joined,
            "joined_length_digits": len(joined),
            "joined_occurrence_count": len(joined_hits),
            "joined_occurrences": joined_hits,
            "source_boundary": source_boundary,
            "valid_full_split_boundaries": valid_boundaries,
            "source_boundary_unique_full_split": valid_boundaries == [source_boundary],
        },
        "distribution": distribution,
        "controls": controls,
        "pair_alignment": {
            "block_1_pairs_from_start": pairs_from_start(CHAYENNE_BLOCKS[0]),
            "block_2_pairs_from_start": pairs_from_start(CHAYENNE_BLOCKS[1]),
            "block_2_pairs_with_leading_zero": pairs_from_start("0" + CHAYENNE_BLOCKS[1]),
            "block_2_pairs_with_trailing_zero": pairs_from_start(CHAYENNE_BLOCKS[1] + "0"),
            "joined_pairs_from_start": pairs_from_start(joined),
        },
        "binary_profiles": {
            "block_1": binary_profile(CHAYENNE_BLOCKS[0]),
            "block_2": binary_profile(CHAYENNE_BLOCKS[1]),
            "joined": binary_profile(joined),
        },
        "decision": {
            "classification": "PROMOTED_MECHANICAL_CLUE",
            "narrow_claim": "chayenne_primary_separator_marks_unique_join_between_two_attested_book_substrings",
            "word_spacing_claim": False,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "authorial_origin_formula_status": "not_promoted",
        },
    }

    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True))
    write_markdown(result)
    print(JSON_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
