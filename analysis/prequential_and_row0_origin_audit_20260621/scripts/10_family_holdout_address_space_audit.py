from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
FAMILY_LOSS = TEST_RESULTS / "09_recipe_reparse_family_loss_decomposition.json"
EPSILON_BITS = 1e-3


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def book_offsets(books: dict[str, str]) -> dict[int, int]:
    offsets = {}
    cursor = 0
    for book in range(70):
        offsets[book] = cursor
        cursor += len(books[str(book)])
    return offsets


def address_bits_for_target(target_digit_global: int, min_len: int) -> float:
    legal_source_count = max(1, target_digit_global - min_len + 1)
    return math.log2(max(2, legal_source_count))


def find_legal_sources(local_emitted: str, chunk: str, min_len: int) -> list[int]:
    target_digit_global = len(local_emitted)
    legal_source_count = max(1, target_digit_global - min_len + 1)
    sources = []
    for source_pos in range(legal_source_count):
        if source_pos + len(chunk) > target_digit_global:
            continue
        if local_emitted[source_pos : source_pos + len(chunk)] == chunk:
            sources.append(source_pos)
    return sources


def reprice_active_recipe_in_holdout_coordinates(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    train_books: list[int],
    test_books: list[int],
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    offsets = book_offsets(books)
    local_emitted = "".join(books[str(book)] for book in train_books)
    copy_rows = []
    original_address_bits = 0.0
    rebased_address_bits = 0.0
    errors = []

    for book in test_books:
        text = books[str(book)]
        rendered = []
        pos = 0
        for op_index, op in enumerate(formula["book_recipes"][str(book)]["ops"]):
            op_type = op["type"]
            length = int(op["length"])
            if op_type == "literal":
                chunk = str(op["text"])
                if len(chunk) != length:
                    errors.append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "type": "literal_length_mismatch",
                        }
                    )
                if text[pos : pos + length] != chunk:
                    errors.append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "type": "literal_text_mismatch",
                        }
                    )
                rendered.append(chunk)
                local_emitted += chunk
                pos += length
                continue

            if op_type != "copy":
                errors.append({"book": book, "op_index": op_index, "type": "unknown_op"})
                continue

            chunk = text[pos : pos + length]
            original_target = offsets[book] + pos
            rebased_target = len(local_emitted)
            original_bits = address_bits_for_target(original_target, min_len)
            rebased_bits = address_bits_for_target(rebased_target, min_len)
            sources = find_legal_sources(local_emitted, chunk, min_len)
            if not sources:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_chunk_not_available_after_rebase",
                        "target_start": pos,
                        "length": length,
                    }
                )
            original_address_bits += original_bits
            rebased_address_bits += rebased_bits
            copy_rows.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "target_start": pos,
                    "length": length,
                    "original_target_digit_global": original_target,
                    "rebased_target_digit_global": rebased_target,
                    "original_address_bits": original_bits,
                    "rebased_address_bits": rebased_bits,
                    "rebased_minus_original_bits": rebased_bits - original_bits,
                    "legal_rebased_source_count": len(sources),
                    "earliest_rebased_source": sources[0] if sources else None,
                }
            )
            rendered.append(chunk)
            local_emitted += chunk
            pos += length

        if "".join(rendered) != text:
            errors.append({"book": book, "type": "book_render_mismatch"})

    return {
        "copy_address_bits_original_coordinates": original_address_bits,
        "copy_address_bits_rebased_holdout_coordinates": rebased_address_bits,
        "coordinate_shift_bits": rebased_address_bits - original_address_bits,
        "copy_rows": copy_rows,
        "validation": {"errors": errors, "roundtrip_ok": not errors},
    }


def reparse_address_bits(
    *,
    audit126,
    formula: dict[str, Any],
    books: dict[str, str],
    train_books: list[int],
    test_books: list[int],
    train_counts: dict[str, Any],
) -> dict[str, Any]:
    available = "".join(books[str(book)] for book in train_books)
    rows = []
    total = 0.0
    errors = []
    for book in test_books:
        encoded = audit126.encode_book_frozen_reparse(
            book=str(book),
            text=books[str(book)],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )
        total += encoded["copy_address_bits"]
        if encoded["validation"]["errors"]:
            errors.append({"book": book, "errors": encoded["validation"]["errors"]})
        copy_ops = [op for op in encoded["ops"] if op["type"] == "copy"]
        rows.append(
            {
                "book": book,
                "copy_address_bits": encoded["copy_address_bits"],
                "copy_count": len(copy_ops),
                "copy_targets": [op["target_start"] for op in copy_ops],
                "copy_lengths": [op["length"] for op in copy_ops],
            }
        )
        available += books[str(book)]
    return {
        "copy_address_bits": total,
        "book_rows": rows,
        "validation": {"errors": errors, "roundtrip_ok": not errors},
    }


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    family_loss = load_json(FAMILY_LOSS)
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for loss_row in family_loss["rows"]:
        test_books = list(loss_row["test_books"])
        train_books = sorted(all_books - set(test_books))
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        active_rebased = reprice_active_recipe_in_holdout_coordinates(
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=test_books,
        )
        reparse = reparse_address_bits(
            audit126=audit126,
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=test_books,
            train_counts=train_counts,
        )
        original_delta = (
            reparse["copy_address_bits"]
            - active_rebased["copy_address_bits_original_coordinates"]
        )
        rebased_delta = (
            reparse["copy_address_bits"]
            - active_rebased["copy_address_bits_rebased_holdout_coordinates"]
        )
        coordinate_shift = active_rebased["coordinate_shift_bits"]
        explained_share = None
        if abs(original_delta) > 1e-9:
            explained_share = coordinate_shift / original_delta
        rows.append(
            {
                "label": loss_row["label"],
                "test_books": test_books,
                "active_original_copy_address_bits": active_rebased[
                    "copy_address_bits_original_coordinates"
                ],
                "active_rebased_copy_address_bits": active_rebased[
                    "copy_address_bits_rebased_holdout_coordinates"
                ],
                "reparse_copy_address_bits": reparse["copy_address_bits"],
                "reparse_minus_active_original_address_bits": original_delta,
                "reparse_minus_active_rebased_address_bits": rebased_delta,
                "active_rebased_minus_original_address_bits": coordinate_shift,
                "coordinate_shift_explained_share": explained_share,
                "copy_count": len(active_rebased["copy_rows"]),
                "active_rebased_validation": active_rebased["validation"],
                "reparse_validation": reparse["validation"],
                "active_copy_rows": active_rebased["copy_rows"],
                "reparse_book_rows": reparse["book_rows"],
            }
        )

    all_valid = all(
        row["active_rebased_validation"]["errors"] == []
        and row["reparse_validation"]["errors"] == []
        for row in rows
    )
    rebased_nonpositive = [
        row for row in rows if row["reparse_minus_active_rebased_address_bits"] <= EPSILON_BITS
    ]
    original_positive = [
        row for row in rows if row["reparse_minus_active_original_address_bits"] > 1e-9
    ]
    classification = (
        "family_copy_address_losses_are_holdout_coordinate_artifacts"
        if all_valid and len(rebased_nonpositive) == len(rows)
        else "family_copy_address_losses_partly_survive_rebased_coordinates"
    )
    return {
        "schema": "family_holdout_address_space_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "family_loss_decomposition": rel(FAMILY_LOSS),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
        },
        "epsilon_bits": EPSILON_BITS,
        "rows": rows,
        "summary": {
            "family_count": len(rows),
            "all_rebased_active_roundtrip": all(
                row["active_rebased_validation"]["errors"] == [] for row in rows
            ),
            "all_reparse_roundtrip": all(
                row["reparse_validation"]["errors"] == [] for row in rows
            ),
            "original_positive_address_loss_count": len(original_positive),
            "rebased_nonpositive_address_loss_count": len(rebased_nonpositive),
            "mean_original_address_delta_bits": sum(
                row["reparse_minus_active_original_address_bits"] for row in rows
            )
            / len(rows),
            "mean_rebased_address_delta_bits": sum(
                row["reparse_minus_active_rebased_address_bits"] for row in rows
            )
            / len(rows),
            "total_coordinate_shift_bits": sum(
                row["active_rebased_minus_original_address_bits"] for row in rows
            ),
            "interpretation": (
                "The apparent copy-address losses in the family-loss audit are "
                "caused by comparing reparse addresses emitted after the training "
                "complement against active-recipe addresses charged in their "
                "original global numeric positions."
            ),
        },
        "decision": {
            "address_loss_status": "coordinate_comparison_artifact",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "10_family_holdout_address_space_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Family Holdout Address Space Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 09 localized the five family holdout losses to copy-address bits.",
        "This audit tests whether that is a real recipe loss or a coordinate",
        "artifact: the active recipe was originally charged in global numeric",
        "book order, while the family reparse emits held-out books after the",
        "training complement.",
        "",
        "## Summary",
        "",
        f"- Families checked: `{result['summary']['family_count']}`.",
        f"- Active recipe roundtrips after holdout-coordinate rebase: `{result['summary']['all_rebased_active_roundtrip']}`.",
        f"- Reparse roundtrips: `{result['summary']['all_reparse_roundtrip']}`.",
        f"- Positive original-coordinate address losses: `{result['summary']['original_positive_address_loss_count']}`.",
        f"- Nonpositive rebased-coordinate address losses: `{result['summary']['rebased_nonpositive_address_loss_count']}`.",
        f"- Mean original-coordinate address delta: `{result['summary']['mean_original_address_delta_bits']:.3f}` bits.",
        f"- Mean rebased-coordinate address delta: `{result['summary']['mean_rebased_address_delta_bits']:.3f}` bits.",
        f"- Total active rebase coordinate shift: `{result['summary']['total_coordinate_shift_bits']:.3f}` bits.",
        "",
        "## Rows",
        "",
        "| Family | Books | Original delta | Rebased delta | Coordinate shift | Explained share | Copy count |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        share = row["coordinate_shift_explained_share"]
        share_text = "None" if share is None else f"{share:.3f}"
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['reparse_minus_active_original_address_bits']:.3f}` | "
            f"`{row['reparse_minus_active_rebased_address_bits']:.3f}` | "
            f"`{row['active_rebased_minus_original_address_bits']:.3f}` | "
            f"`{share_text}` | `{row['copy_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The copy-address losses from audit 09 do not survive a same-coordinate comparison.",
            f"- Rebased deltas are interpreted with epsilon `{result['epsilon_bits']}` bits.",
            "- The active recipe remains useful as a full-corpus compression reference, but original-coordinate active address bits are not a fair holdout comparator for families emitted after their training complement.",
            "- This strengthens the family-holdout recipe validation without promoting a final authorial method.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "10_family_holdout_address_space_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
