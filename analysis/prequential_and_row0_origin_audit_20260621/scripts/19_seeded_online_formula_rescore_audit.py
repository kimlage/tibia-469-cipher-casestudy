from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
AUDIT_129 = AUTHORIAL / "scripts" / "129_online_deterministic_reparse_compile.py"
AUDIT_15 = HERE / "scripts" / "15_leave_one_book_out_book_bounded_source_audit.py"
BOOTSTRAP_SEED = TEST_RESULTS / "18_online_bootstrap_seed_policy_audit.json"
ONLINE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_formula_469.json"
)

COMPONENT_KEYS = [
    "literal_bits_no_payload",
    "literal_payload_bits",
    "copy_address_bits",
    "copy_length_code_bits",
    "item_type_split_only_stream_bits",
]
INVENTORY_KEYS = ["literal_runs", "literal_digits", "copy_items", "copied_digits"]


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


def clean_ops(encoded: dict[str, Any]) -> list[dict[str, Any]]:
    ops = []
    for op in encoded["ops"]:
        if op["type"] == "literal":
            ops.append({"type": "literal", "text": op["text"], "length": int(op["length"])})
        elif op["type"] == "copy":
            ops.append(
                {
                    "type": "copy",
                    "source_digit_pos": int(op["source_digit_pos"]),
                    "length": int(op["length"]),
                    "target_start": int(op["target_start"]),
                }
            )
        else:
            raise ValueError(op)
    return ops


def score_formula(*, formula: dict[str, Any], books: dict[str, str], audit126, compile129):
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)
    return compile129.score_splitonly_formula(
        formula=formula,
        books=books,
        audit126=audit126,
        frontier=frontier,
        midpoint=midpoint,
        copy_module=copy_module,
        item_module=item_module,
    )


def build_book_bounded_seed_formula(
    *,
    source_formula: dict[str, Any],
    books: dict[str, str],
    audit126,
    audit128,
    audit15,
) -> dict[str, Any]:
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)
    copy_rows = copy_module.collect_copy_rows(source_formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(source_formula, books)
    item_rows, item_stats = item_module.collect_item_rows(source_formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    out = copy.deepcopy(source_formula)
    out["book_recipes"] = {}
    for book in range(70):
        book_key = str(book)
        if book == 0:
            out["book_recipes"][book_key] = {
                "length": len(books[book_key]),
                "ops": [
                    {
                        "type": "literal",
                        "text": books[book_key],
                        "length": len(books[book_key]),
                    }
                ],
            }
            continue
        train_books = list(range(book))
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=source_formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        available = "".join(books[str(train_book)] for train_book in train_books)
        encoded = audit15.encode_book_book_bounded_reparse(
            audit126=audit126,
            book=book_key,
            text=books[book_key],
            available=available,
            source_boundaries=audit15.source_ranges(books, train_books),
            formula=source_formula,
            train_counts=train_counts,
        )
        if encoded["validation"]["errors"]:
            raise RuntimeError(encoded["validation"])
        out["book_recipes"][book_key] = {
            "length": len(books[book_key]),
            "ops": clean_ops(encoded),
        }
    return out


def score_summary(score: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_bits": score["total_bits"],
        "validation": score["validation"],
        "inventory": {key: score[key] for key in INVENTORY_KEYS},
        "component_bits": {key: score[key] for key in COMPONENT_KEYS},
    }


def component_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, float]:
    return {
        key: candidate["component_bits"][key] - baseline["component_bits"][key]
        for key in COMPONENT_KEYS
    }


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    compile129 = load_module("compile129_online_reparse", AUDIT_129)
    audit15 = load_module("audit15_book_bounded", AUDIT_15)

    source_formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    online_formula = load_json(ONLINE_FORMULA)
    bootstrap_seed = load_json(BOOTSTRAP_SEED)

    online_score = score_summary(
        score_formula(formula=online_formula, books=books, audit126=audit126, compile129=compile129)
    )
    seeded_online_formula = copy.deepcopy(online_formula)
    seeded_online_formula["book_recipes"]["0"]["ops"] = [
        {"type": "literal", "text": books["0"], "length": len(books["0"])}
    ]
    seeded_online_score = score_summary(
        score_formula(
            formula=seeded_online_formula,
            books=books,
            audit126=audit126,
            compile129=compile129,
        )
    )
    book_bounded_seed_formula = build_book_bounded_seed_formula(
        source_formula=source_formula,
        books=books,
        audit126=audit126,
        audit128=audit128,
        audit15=audit15,
    )
    book_bounded_seed_score = score_summary(
        score_formula(
            formula=book_bounded_seed_formula,
            books=books,
            audit126=audit126,
            compile129=compile129,
        )
    )

    candidates = [
        {
            "candidate": "online_reparse_formula",
            "status": "baseline_promoted_elsewhere",
            **online_score,
            "delta_vs_online_bits": 0.0,
            "component_delta_vs_online_bits": {
                key: 0.0 for key in COMPONENT_KEYS
            },
            "interpretation": "Existing deterministic online formula from audit 129.",
        },
        {
            "candidate": "seeded_online_formula_rescored",
            "status": (
                "rejected_as_full_scorer_promotion"
                if seeded_online_score["total_bits"] >= online_score["total_bits"]
                else "would_promote_if_lower"
            ),
            **seeded_online_score,
            "delta_vs_online_bits": seeded_online_score["total_bits"] - online_score["total_bits"],
            "component_delta_vs_online_bits": component_delta(seeded_online_score, online_score),
            "interpretation": (
                "Book 0 is replaced by one full literal seed inside the existing "
                "online formula and then rescored under the complete active ledger."
            ),
        },
        {
            "candidate": "book_bounded_seeded_online_formula_rescored",
            "status": (
                "rejected_as_full_scorer_promotion"
                if book_bounded_seed_score["total_bits"] >= online_score["total_bits"]
                else "would_promote_if_lower"
            ),
            **book_bounded_seed_score,
            "delta_vs_online_bits": book_bounded_seed_score["total_bits"]
            - online_score["total_bits"],
            "component_delta_vs_online_bits": component_delta(
                book_bounded_seed_score, online_score
            ),
            "interpretation": (
                "Book 0 is a literal seed and books 1-69 are reparsed from "
                "previous books only with book-bounded source constraints, then "
                "rescored under the complete active ledger."
            ),
        },
    ]
    promoted = [
        row
        for row in candidates[1:]
        if row["total_bits"] < online_score["total_bits"] and row["validation"]["errors"] == []
    ]
    classification = (
        "seed_policy_rejected_by_full_formula_rescore"
        if not promoted
        else "seed_policy_promoted_by_full_formula_rescore"
    )
    return {
        "schema": "seeded_online_formula_rescore_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "bootstrap_seed_policy": rel(BOOTSTRAP_SEED),
            "online_formula": rel(ONLINE_FORMULA),
            "recipe_reparse": rel(AUDIT_126),
            "online_compile": rel(AUDIT_129),
            "book_bounded_parser": rel(AUDIT_15),
        },
        "bootstrap_policy_reference": {
            "raw_seeded_stream_saving_vs_online_bits": bootstrap_seed["summary"][
                "raw_seeded_stream_saving_vs_online_bits"
            ],
            "raw_seeded_failure_books": bootstrap_seed["summary"]["raw_seeded_failure_books"],
            "note": (
                "Audit 18 is a per-book seed accounting ledger. This audit asks "
                "whether the same seed idea survives the complete formula scorer."
            ),
        },
        "candidates": candidates,
        "summary": {
            "online_formula_bits": online_score["total_bits"],
            "seeded_online_formula_bits": seeded_online_score["total_bits"],
            "seeded_online_delta_vs_online_bits": seeded_online_score["total_bits"]
            - online_score["total_bits"],
            "book_bounded_seeded_formula_bits": book_bounded_seed_score["total_bits"],
            "book_bounded_seeded_delta_vs_online_bits": book_bounded_seed_score[
                "total_bits"
            ]
            - online_score["total_bits"],
            "promoted_candidate_count": len(promoted),
            "promoted_candidates": [row["candidate"] for row in promoted],
            "all_roundtrip": all(row["validation"]["errors"] == [] for row in candidates),
            "interpretation": (
                "The raw seed closes the per-book cold-start failure, but once "
                "converted into formula recipes and rescored under the complete "
                "ledger, it does not beat the existing online formula."
            ),
        },
        "decision": {
            "seed_policy_status": "useful_bootstrap_accounting_not_formula_promotion",
            "compression_bound_status": "unchanged",
            "generation_explanation_status": "seed_caveat_clarified_but_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "19_seeded_online_formula_rescore_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Seeded Online Formula Rescore Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 18 showed that an explicit raw seed for book `0` closes the only",
        "per-book previous-books-only local failure. This audit asks the stricter",
        "question: if the seed policy is converted back into actual formula recipes",
        "and rescored under the complete active ledger, does it still improve the",
        "current online formula?",
        "",
        "## Summary",
        "",
        f"- Online formula: `{result['summary']['online_formula_bits']:.3f}` bits.",
        f"- Seeded online formula: `{result['summary']['seeded_online_formula_bits']:.3f}` bits.",
        f"- Seeded delta vs online: `{result['summary']['seeded_online_delta_vs_online_bits']:.3f}` bits.",
        f"- Book-bounded seeded formula: `{result['summary']['book_bounded_seeded_formula_bits']:.3f}` bits.",
        f"- Book-bounded seeded delta vs online: `{result['summary']['book_bounded_seeded_delta_vs_online_bits']:.3f}` bits.",
        f"- Promoted candidates: `{result['summary']['promoted_candidates']}`.",
        "",
        "## Candidates",
        "",
        "| Candidate | Status | Total bits | Delta vs online | Literal digits | Copied digits | Roundtrip |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in result["candidates"]:
        lines.append(
            f"| `{row['candidate']}` | `{row['status']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_online_bits']:.3f}` | "
            f"`{row['inventory']['literal_digits']}` | `{row['inventory']['copied_digits']}` | "
            f"`{row['validation']['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The raw seed remains useful bootstrap accounting, but it is not promoted as a full-formula improvement.",
            "- The existing online formula remains the cheaper complete scored recipe.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "19_seeded_online_formula_rescore_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
