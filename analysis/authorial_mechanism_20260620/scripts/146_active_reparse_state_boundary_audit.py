from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_126 = HERE / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_144 = HERE / "scripts" / "144_copy_source_distance_model_audit.py"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]


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


def last_copy_before(formula: dict[str, Any], cutoff: int) -> tuple[int, int] | None:
    previous = None
    for book in map(str, formula["policy"]["book_order"]):
        if int(book) >= cutoff:
            break
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "copy":
                previous = (int(op["source_digit_pos"]), int(op["length"]))
    return previous


def active_path_states_for_books(
    formula: dict[str, Any],
    books: dict[str, str],
    *,
    cutoff: int,
) -> dict[str, Any]:
    previous_copy = last_copy_before(formula, cutoff)
    previous_item = "BOS"
    states = set()
    default_hits = 0
    exception_hits = 0
    copy_rows = []
    for book in map(str, formula["policy"]["book_order"]):
        if int(book) < cutoff:
            continue
        position = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            states.add((int(book), position, previous_item, previous_copy))
            if op["type"] == "copy":
                source = int(op["source_digit_pos"])
                length = int(op["length"])
                emitted_before = sum(
                    len(books[str(prev_book)])
                    for prev_book in range(int(book))
                ) + position
                legal_source_count = max(1, emitted_before - int(formula["policy"]["min_len"]) + 1)
                if previous_copy is None:
                    default = 0
                else:
                    candidate = previous_copy[0] + previous_copy[1]
                    default = candidate if candidate < legal_source_count else 0
                if source == default:
                    default_hits += 1
                else:
                    exception_hits += 1
                copy_rows.append(
                    {
                        "book": int(book),
                        "op_index": op_index,
                        "book_pos": position,
                        "source_digit_pos": source,
                        "length": length,
                        "previous_copy_state": previous_copy,
                        "source_default": default,
                        "source_is_default": source == default,
                    }
                )
                previous_copy = (source, length)
            previous_item = op["type"]
            position += int(op["length"])
    return {
        "active_path_state_count": len(states),
        "active_path_copy_count": len(copy_rows),
        "active_path_source_default_hits": default_hits,
        "active_path_source_exception_hits": exception_hits,
        "active_path_distinct_previous_copy_states": len(
            {row["previous_copy_state"] for row in copy_rows}
        ),
        "sample_copy_rows": copy_rows[:5],
    }


def candidate_graph_stats(
    formula: dict[str, Any],
    books: dict[str, str],
    audit126,
    *,
    cutoff: int,
) -> list[dict[str, Any]]:
    min_len = int(formula["policy"]["min_len"])
    available = "".join(books[str(book)] for book in range(cutoff))
    rows = []
    for book in range(cutoff, 70):
        text = books[str(book)]
        matches = audit126.precompute_matches(text, available, min_len)
        candidate_count = sum(len(row) for row in matches)
        candidate_copy_states = {
            (source, length)
            for row in matches
            for source, length, _length_index in row
        }
        old_dp_state_count = (len(text) + 1) * 3
        active_upper_state_proxy = old_dp_state_count * max(1, len(candidate_copy_states))
        rows.append(
            {
                "book": book,
                "book_digits": len(text),
                "positions_with_copy_candidates": sum(1 for row in matches if row),
                "copy_candidate_edges": candidate_count,
                "distinct_candidate_copy_states": len(candidate_copy_states),
                "old_reparse_state_count": old_dp_state_count,
                "active_path_dependent_state_proxy": active_upper_state_proxy,
                "state_proxy_multiplier": (
                    active_upper_state_proxy / old_dp_state_count
                    if old_dp_state_count
                    else 0.0
                ),
            }
        )
        available += text
    return rows


def demonstrate_path_dependence(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    examples = []
    for row in source_rows:
        source = int(row["source_digit_pos"])
        legal_count = int(row["legal_source_count"])
        true_default = int(row["previous_source_plus_length_default"])
        alternate_default = 0 if true_default != 0 else (1 if legal_count > 1 else 0)
        if source == true_default or source == alternate_default:
            examples.append(
                {
                    "book": row["book"],
                    "op_index": row["op_index"],
                    "source_digit_pos": source,
                    "legal_source_count": legal_count,
                    "true_previous_copy_default": true_default,
                    "alternate_previous_copy_default": alternate_default,
                    "classification_under_true_state": (
                        "default" if source == true_default else "exception"
                    ),
                    "classification_under_alternate_state": (
                        "default" if source == alternate_default else "exception"
                    ),
                }
            )
        if len(examples) >= 5:
            break
    return {
        "examples": examples,
        "interpretation": (
            "The same candidate source can be a default or exception depending "
            "on the previous copy state. Exact active reparse therefore cannot "
            "collapse states to only (position, previous item)."
        ),
    }


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = load_module("audit_126", AUDIT_126)
    audit144 = load_module("audit_144", AUDIT_144)
    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}

    source_collected = audit144.collect_source_rows(formula, books)
    if source_collected["errors"]:
        raise RuntimeError(source_collected["errors"])

    rows = []
    for cutoff in PREFIX_CUTOFFS:
        graph_rows = candidate_graph_stats(formula, books, audit126, cutoff=cutoff)
        active_path = active_path_states_for_books(formula, books, cutoff=cutoff)
        rows.append(
            {
                "cutoff": cutoff,
                "test_books": list(range(cutoff, 70)),
                "candidate_graph_summary": {
                    "books": len(graph_rows),
                    "copy_candidate_edges": sum(row["copy_candidate_edges"] for row in graph_rows),
                    "distinct_candidate_copy_states": sum(
                        row["distinct_candidate_copy_states"] for row in graph_rows
                    ),
                    "old_reparse_state_count": sum(row["old_reparse_state_count"] for row in graph_rows),
                    "active_path_dependent_state_proxy": sum(
                        row["active_path_dependent_state_proxy"] for row in graph_rows
                    ),
                    "max_book_state_proxy_multiplier": max(
                        row["state_proxy_multiplier"] for row in graph_rows
                    ),
                },
                "active_recipe_path": active_path,
                "largest_books_by_state_proxy": sorted(
                    graph_rows,
                    key=lambda row: row["active_path_dependent_state_proxy"],
                    reverse=True,
                )[:5],
            }
        )

    max_multiplier = max(
        row["candidate_graph_summary"]["max_book_state_proxy_multiplier"] for row in rows
    )
    classification = "active_reparse_requires_path_dependent_copy_source_state"

    return {
        "schema": "active_reparse_state_boundary_audit.v1",
        "test": "146_active_reparse_state_boundary_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "source_model": formula["policy"]["copy_address_model"],
        "scope": {
            "old_reparse_state_key": "(book_pos, previous_item)",
            "active_reparse_state_key_required": (
                "(book_pos, previous_item, previous_copy_source, previous_copy_length)"
            ),
            "reason": (
                "active copy-source cost uses previous_source_plus_length as a "
                "default; the same copy candidate can be default or exception "
                "under different previous-copy states"
            ),
        },
        "path_dependence_example": demonstrate_path_dependence(source_collected["rows"]),
        "prefix_rows": rows,
        "summary": {
            "max_book_state_proxy_multiplier": max_multiplier,
            "cutoffs": PREFIX_CUTOFFS,
            "exact_active_reparse_implemented": False,
            "bounded_probe_result": (
                "A direct path-dependent prototype did not finish the first "
                "cutoff-60 held-out book within a practical interactive window; "
                "this audit records the state boundary instead of promoting a "
                "partial parser."
            ),
        },
        "decision": {
            "compression_bound_changed": False,
            "recipe_externality_removed": False,
            "next_required_work": (
                "implement a pruned/cached path-dependent active reparse or find "
                "a source-cost simplification that preserves the active bound "
                "without previous-copy state"
            ),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 146. Active Reparse State Boundary Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 145 strengthened component-level prediction for the active",
        "`8177.317` bit formula, but recipe discovery remains unproved. This",
        "audit explains the next parser boundary: unlike the older reparse audit,",
        "the active copy-source model is path-dependent because source cost depends",
        "on the previous copy source plus previous copy length.",
        "",
        "## State Boundary",
        "",
        f"- Old reparse state key: `{result['scope']['old_reparse_state_key']}`",
        f"- Active state key required: `{result['scope']['active_reparse_state_key_required']}`",
        f"- Max observed book-level state proxy multiplier: `{result['summary']['max_book_state_proxy_multiplier']:.1f}`",
        "",
        "## Prefix State Proxies",
        "",
        "| Cutoff | Test books | Candidate edges | Old states | Active state proxy | Max book multiplier | Active path copy states |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["prefix_rows"]:
        summary = row["candidate_graph_summary"]
        active = row["active_recipe_path"]
        lines.append(
            f"| `{row['cutoff']}` | `{len(row['test_books'])}` | "
            f"`{summary['copy_candidate_edges']}` | "
            f"`{summary['old_reparse_state_count']}` | "
            f"`{summary['active_path_dependent_state_proxy']}` | "
            f"`{summary['max_book_state_proxy_multiplier']:.1f}` | "
            f"`{active['active_path_distinct_previous_copy_states']}` |"
        )
    examples = result["path_dependence_example"]["examples"]
    lines.extend(
        [
            "",
            "## Path-Dependence Example",
            "",
        ]
    )
    if examples:
        example = examples[0]
        lines.extend(
            [
                "For one active copy row:",
                "",
                f"- Book/op: `{example['book']}/{example['op_index']}`",
                f"- Source: `{example['source_digit_pos']}` among `{example['legal_source_count']}` legal sources",
                f"- True previous-copy default: `{example['true_previous_copy_default']}` -> `{example['classification_under_true_state']}`",
                f"- Alternate previous-copy default: `{example['alternate_previous_copy_default']}` -> `{example['classification_under_alternate_state']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Exact active reparse is not promoted in this cycle.",
            "- The remaining recipe externality is now localized: active source coding requires previous-copy state.",
            "- The next useful implementation target is a pruned/cached path-dependent reparse, or a source-cost simplification that keeps the active bound without that state.",
            "- No compression-bound, row0-origin, plaintext, or semantic claim is changed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "146_active_reparse_state_boundary_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "146_active_reparse_state_boundary_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
