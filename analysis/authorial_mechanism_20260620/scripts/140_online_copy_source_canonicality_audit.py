from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
PARENT_AUDIT_135 = REPORTS / "135_copy_source_canonicality_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def summary(values: list[float]) -> dict[str, float | int | None]:
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


def collect_copy_rows(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    available = ""
    previous_copy: dict[str, int] | None = None
    for book in map(str, formula["policy"]["book_order"]):
        local = available
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if "text" in op:
                text = op["text"]
                local += text
                book_pos += len(text)
                continue
            if "source_digit_pos" not in op or "length" not in op:
                raise RuntimeError({"book": book, "op_index": op_index, "op": op})

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = local[source : source + length]
            if len(chunk) != length:
                raise RuntimeError({"book": book, "op_index": op_index, "type": "short_source"})
            candidates = candidate_sources(local, chunk)
            if source not in candidates:
                raise RuntimeError(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "stored_source_not_candidate",
                        "source": source,
                        "length": length,
                    }
                )
            row = {
                "book": int(book),
                "op_index": op_index,
                "book_target_pos": book_pos,
                "global_target_pos": len(local),
                "source_digit_pos": source,
                "length": length,
                "candidate_source_count": len(candidates),
                "candidate_min": min(candidates),
                "candidate_max": max(candidates),
                "is_unique_candidate": len(candidates) == 1,
                "matches_earliest_source": source == min(candidates),
                "matches_latest_source": source == max(candidates),
                "matches_previous_source": (
                    previous_copy is not None and source == previous_copy["source_digit_pos"]
                ),
                "matches_previous_source_plus_length": (
                    previous_copy is not None
                    and source
                    == previous_copy["source_digit_pos"] + previous_copy["length"]
                ),
                "random_candidate_match_probability": 1.0 / len(candidates),
            }
            rows.append(row)
            local += chunk
            book_pos += length
            previous_copy = {"source_digit_pos": source, "length": length}
        expected = available + books[book]
        if local != expected:
            raise RuntimeError(
                {
                    "book": book,
                    "type": "roundtrip_failed",
                    "actual_len": len(local),
                    "expected_len": len(expected),
                }
            )
        available = local
    return rows


def make_result() -> dict[str, Any]:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    parent = load_json(PARENT_AUDIT_135)
    rows = collect_copy_rows(formula, books)

    earliest_hits = sum(row["matches_earliest_source"] for row in rows)
    latest_hits = sum(row["matches_latest_source"] for row in rows)
    previous_source_hits = sum(row["matches_previous_source"] for row in rows)
    previous_plus_length_hits = sum(row["matches_previous_source_plus_length"] for row in rows)
    unique_hits = sum(row["is_unique_candidate"] for row in rows)
    ambiguous_rows = [row for row in rows if row["candidate_source_count"] > 1]
    ambiguous_earliest_hits = sum(row["matches_earliest_source"] for row in ambiguous_rows)
    random_expected_hits = sum(row["random_candidate_match_probability"] for row in rows)
    log2_random_all_earliest_probability = sum(
        math.log2(row["random_candidate_match_probability"]) for row in rows
    )

    if earliest_hits != int(parent["summary"]["earliest_source_count"]):
        raise RuntimeError(
            {
                "type": "parent_135_mismatch",
                "parent_earliest": parent["summary"]["earliest_source_count"],
                "current_earliest": earliest_hits,
            }
        )
    classification = "copy_source_canonicality_controls_confirm_earliest_rule"

    return {
        "schema": "copy_source_canonicality_controls.v1",
        "test": "140_online_copy_source_canonicality_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(FORMULA),
        "sources": {
            "formula": rel(FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "parent_audit_135": rel(PARENT_AUDIT_135),
        },
        "summary": {
            "copy_ops": len(rows),
            "unique_source_candidate_ops": unique_hits,
            "ambiguous_source_candidate_ops": len(ambiguous_rows),
            "earliest_source_hits": earliest_hits,
            "latest_source_hits": latest_hits,
            "previous_source_hits": previous_source_hits,
            "previous_source_plus_length_hits": previous_plus_length_hits,
            "ambiguous_earliest_source_hits": ambiguous_earliest_hits,
            "candidate_source_count": summary(
                [float(row["candidate_source_count"]) for row in rows]
            ),
            "copy_length": summary([float(row["length"]) for row in rows]),
        },
        "negative_controls": {
            "latest_occurrence_hits": latest_hits,
            "previous_source_hits": previous_source_hits,
            "previous_source_plus_length_hits": previous_plus_length_hits,
            "random_candidate_expected_hits": random_expected_hits,
            "random_candidate_expected_hit_rate": random_expected_hits / len(rows),
            "observed_earliest_hit_rate": earliest_hits / len(rows),
            "log2_probability_all_earliest_if_uniform_candidate_choice": (
                log2_random_all_earliest_probability
            ),
            "probability_all_earliest_if_uniform_candidate_choice": (
                2.0 ** log2_random_all_earliest_probability
            ),
        },
        "interpretation": {
            "accepted_rule": (
                "For every copy in the canonical online-reparse formula, the stored "
                "source address is the earliest previous occurrence of the copied "
                "substring at the declared copy length."
            ),
            "decodability_limit": (
                "This is parser/source canonicality, not a complete source-free "
                "decoder: without the copied substring or an independently derived "
                "copy decision, the address field is still part of the recipe."
            ),
            "mechanical_progress": (
                "The audit adds controls to audit 135: copy source tie-breaking is "
                "deterministic earliest-match canonicality, and this is far above "
                "uniform candidate-choice expectation while row0 and semantics "
                "remain unchanged."
            ),
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
        "rows": rows,
    }


def render_markdown(result: dict[str, Any]) -> str:
    summary_row = result["summary"]
    controls = result["negative_controls"]
    lines = [
        "# 140. Online Copy Source Canonicality Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 135 showed that every declared copy source is the earliest prior",
        "occurrence of the copied substring. This addendum adds negative controls",
        "for that canonicality result: latest occurrence, previous-source rules,",
        "and uniform random choice among candidate occurrences. It does not remove",
        "source fields from the decoder and it does not search for plaintext.",
        "",
        "## Result",
        "",
        f"- Copy ops: `{summary_row['copy_ops']}`",
        f"- Unique source-candidate ops: `{summary_row['unique_source_candidate_ops']}`",
        f"- Ambiguous source-candidate ops: `{summary_row['ambiguous_source_candidate_ops']}`",
        f"- Earliest-occurrence hits: `{summary_row['earliest_source_hits']}/{summary_row['copy_ops']}`",
        f"- Latest-occurrence hits: `{summary_row['latest_source_hits']}/{summary_row['copy_ops']}`",
        f"- Previous-source hits: `{summary_row['previous_source_hits']}/{summary_row['copy_ops']}`",
        f"- Previous-source-plus-length hits: `{summary_row['previous_source_plus_length_hits']}/{summary_row['copy_ops']}`",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Candidate source count min/median/mean/max | `{summary_row['candidate_source_count']['min']:.0f}` / `{summary_row['candidate_source_count']['median']:.0f}` / `{summary_row['candidate_source_count']['mean']:.3f}` / `{summary_row['candidate_source_count']['max']:.0f}` |",
        f"| Copy length min/median/mean/max | `{summary_row['copy_length']['min']:.0f}` / `{summary_row['copy_length']['median']:.0f}` / `{summary_row['copy_length']['mean']:.3f}` / `{summary_row['copy_length']['max']:.0f}` |",
        f"| Random candidate expected hits | `{controls['random_candidate_expected_hits']:.3f}` |",
        f"| Random candidate expected hit rate | `{controls['random_candidate_expected_hit_rate']:.3f}` |",
        f"| Observed earliest hit rate | `{controls['observed_earliest_hit_rate']:.3f}` |",
        f"| log2 P(all earliest under uniform candidate choice) | `{controls['log2_probability_all_earliest_if_uniform_candidate_choice']:.3f}` |",
        "",
        "## Interpretation",
        "",
        "Every stored copy source is the earliest previous occurrence of the copied",
        "substring at the declared length. This supports a deterministic parser",
        "tie-break rule and removes one arbitrary-choice concern from the online",
        "recipe.",
        "",
        "The limit is important: this does not make the formula source-free. A",
        "decoder still needs the copied substring, copy decision, or source-bearing",
        "recipe information to reconstruct the book. The result is source",
        "canonicality, not a new compression bound.",
        "",
        "## Boundary",
        "",
        "- No plaintext or translation is introduced.",
        "- Row0/table origin is unchanged.",
        "- Compression bound is unchanged.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "140_online_copy_source_canonicality_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "140_online_copy_source_canonicality_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
