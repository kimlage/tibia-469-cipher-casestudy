from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

TYPE_DERIVED_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_formula_469.json"
)
TYPE_DERIVED_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_type_derived_bits"
)
COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def legal_sources(emitted: str, length: int, min_len: int) -> list[int]:
    legal_source_count = max(1, len(emitted) - min_len + 1)
    return [pos for pos in range(legal_source_count) if pos + length <= len(emitted)]


def max_target_extension(*, emitted: str, source_pos: int, target: str, book_pos: int) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def audit_sources(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    rows = []
    errors = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append({"book": book, "op_index": op_index, "type": "literal_mismatch"})
                emitted += text
                book_pos += len(text)
                continue

            if op["type"] != "copy":
                errors.append({"book": book, "op_index": op_index, "type": "bad_op", "op": op})
                continue

            source_pos = int(op["source_digit_pos"])
            length = int(op["length"])
            chunk = emitted[source_pos : source_pos + length]
            target_chunk = target[book_pos : book_pos + length]
            if chunk != target_chunk or len(chunk) != length:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source_pos,
                        "length": length,
                    }
                )
            candidates = [
                pos
                for pos in legal_sources(emitted, length, min_len)
                if emitted[pos : pos + length] == target_chunk
            ]
            if source_pos not in candidates:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "source_not_in_candidate_set",
                        "source_digit_pos": source_pos,
                        "candidate_count": len(candidates),
                    }
                )
                earliest = latest = None
            else:
                earliest = min(candidates)
                latest = max(candidates)

            max_ext = max_target_extension(
                emitted=emitted,
                source_pos=source_pos,
                target=target,
                book_pos=book_pos,
            )
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source_pos,
                    "length": length,
                    "candidate_count": len(candidates),
                    "earliest_source": earliest,
                    "latest_source": latest,
                    "is_unique_source": len(candidates) == 1,
                    "is_earliest_source": earliest == source_pos,
                    "is_latest_source": latest == source_pos,
                    "max_target_extension": max_ext,
                    "length_equals_max_target_extension": length == max_ext,
                    "extension_slack": max_ext - length,
                }
            )
            emitted += chunk
            book_pos += length
        if book_pos != len(target):
            errors.append(
                {
                    "book": book,
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )

    candidate_counts = [row["candidate_count"] for row in rows]
    extension_slacks = [row["extension_slack"] for row in rows]
    summary = {
        "copy_items": len(rows),
        "unique_source_count": sum(row["is_unique_source"] for row in rows),
        "earliest_source_count": sum(row["is_earliest_source"] for row in rows),
        "latest_source_count": sum(row["is_latest_source"] for row in rows),
        "length_equals_max_target_extension_count": sum(
            row["length_equals_max_target_extension"] for row in rows
        ),
        "candidate_count_min": min(candidate_counts) if candidate_counts else 0,
        "candidate_count_mean": statistics.mean(candidate_counts) if candidate_counts else 0.0,
        "candidate_count_max": max(candidate_counts) if candidate_counts else 0,
        "extension_slack_min": min(extension_slacks) if extension_slacks else 0,
        "extension_slack_mean": statistics.mean(extension_slacks) if extension_slacks else 0.0,
        "extension_slack_max": max(extension_slacks) if extension_slacks else 0,
    }
    return {"summary": summary, "rows": rows, "errors": errors}


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    compact_formula = load_json(TYPE_DERIVED_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    active_bits = float(compact_formula["mdl_estimate_rough"][TYPE_DERIVED_TOTAL_KEY])
    normalized = compile134.normalize_ops(compact_formula)
    score = compile129.score_splitonly_formula(
        formula=normalized,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )
    if score["validation"]["errors"]:
        raise RuntimeError(score["validation"])
    if abs(float(score["total_bits"]) - active_bits) > 1e-9:
        raise RuntimeError({"active_bits": active_bits, "score_bits": score["total_bits"]})

    audit = audit_sources(normalized, books)
    if audit["errors"]:
        raise RuntimeError(audit["errors"])

    summary = audit["summary"]
    if summary["earliest_source_count"] == summary["copy_items"]:
        classification = "copy_sources_are_earliest_exact_chunk_occurrences"
    else:
        classification = "copy_sources_not_fully_earliest_canonical"

    result = {
        "schema": "copy_source_canonicality_audit.v1",
        "test": "135_copy_source_canonicality_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(TYPE_DERIVED_FORMULA),
        "active_bits": active_bits,
        "recomputed_bits": score["total_bits"],
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
        "summary": summary,
        "rows": audit["rows"],
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
            "copy_source_dependency_removed": False,
        },
    }

    lines = [
        "# 135. Copy Source Canonicality Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The compact online formula still declares copy source and copy length.",
        "This audit checks whether the declared copy source is arbitrary or",
        "canonical relative to the copied chunk: for every copy, it enumerates all",
        "legal prior occurrences of the copied chunk at the same length.",
        "",
        "## Result",
        "",
        f"- Active bits: `{active_bits:.3f}`",
        f"- Recomputed bits: `{score['total_bits']:.3f}`",
        f"- Roundtrip: `{score['validation']['books_roundtrip_ok']}/70`",
        f"- Copy items: `{summary['copy_items']}`",
        f"- Earliest-source copies: `{summary['earliest_source_count']}/{summary['copy_items']}`",
        f"- Unique-source copies: `{summary['unique_source_count']}/{summary['copy_items']}`",
        f"- Latest-source copies: `{summary['latest_source_count']}/{summary['copy_items']}`",
        f"- Candidate count min/mean/max: `{summary['candidate_count_min']}` / "
        f"`{summary['candidate_count_mean']:.3f}` / `{summary['candidate_count_max']}`",
        f"- Length equals target-max extension: "
        f"`{summary['length_equals_max_target_extension_count']}/{summary['copy_items']}`",
        "",
        "## Interpretation",
        "",
    ]
    if classification == "copy_sources_are_earliest_exact_chunk_occurrences":
        lines.extend(
            [
                "Every declared source is the earliest legal occurrence of the",
                "actual copied chunk at the declared copy length. This supports a",
                "canonical encoder-side source rule, not arbitrary source choice.",
                "It does not remove the decoder dependency on copy source, because",
                "the copied chunk is not otherwise available at decode time.",
            ]
        )
    else:
        lines.extend(
            [
                "Some copy sources are not the earliest legal occurrence of the",
                "copied chunk. Source choice remains a declared recipe dependency",
                "with no canonical earliest-source explanation.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
            "- Copy source remains a declared decoding dependency.",
        ]
    )
    write_result("135_copy_source_canonicality_audit", result, lines)


if __name__ == "__main__":
    main()
