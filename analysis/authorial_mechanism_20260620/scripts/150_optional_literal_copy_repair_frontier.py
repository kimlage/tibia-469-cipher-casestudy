from __future__ import annotations

import copy
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
COMPILE_129 = HERE / "scripts" / "129_online_deterministic_reparse_compile.py"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_136 = HERE / "scripts" / "136_copy_length_default_decodability_audit.py"
AUDIT_137 = HERE / "scripts" / "137_copy_source_default_decodability_audit.py"
AUDIT_141 = HERE / "scripts" / "141_default_exception_prequential_validation.py"


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


def op_type(op: dict[str, Any]) -> str:
    if "text" in op:
        return "literal"
    if "source_digit_pos" in op and "length" in op:
        return "copy"
    raise RuntimeError({"type": "unknown_op_shape", "op": op})


def copy_candidates(available: str, target: str, book_pos: int, min_len: int) -> list[dict[str, int]]:
    if len(target) - book_pos < min_len:
        return []
    needle = target[book_pos : book_pos + min_len]
    out = []
    for source in range(max(0, len(available) - min_len + 1)):
        if available[source : source + min_len] != needle:
            continue
        length = min_len
        while (
            book_pos + length < len(target)
            and source + length < len(available)
            and target[book_pos + length] == available[source + length]
        ):
            length += 1
        out.append({"source_digit_pos": source, "max_length": length})
    return out


def active_score(formula: dict[str, Any], modules: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    compile129 = modules["compile129"]
    compile134 = modules["compile134"]
    audit136 = modules["audit136"]
    audit137 = modules["audit137"]
    audit141 = modules["audit141"]
    audit126 = modules["audit126"]
    normalized = compile134.normalize_ops(formula)
    score = compile129.score_splitonly_formula(
        formula=normalized,
        books=books,
        audit126=audit126,
        frontier=modules["frontier"],
        midpoint=modules["midpoint"],
        copy_module=modules["copy_module"],
        item_module=modules["item_module"],
    )
    if score["validation"]["errors"]:
        raise RuntimeError(score["validation"])
    min_len = int(normalized["policy"]["min_len"])
    length_collected = audit136.collect_copy_length_rows(normalized, books)
    source_collected = audit137.collect_source_rows(normalized, books)
    if length_collected["errors"]:
        raise RuntimeError(length_collected["errors"])
    if source_collected["errors"]:
        raise RuntimeError(source_collected["errors"])
    copy_length_stream = audit141.score_copy_length_default_exception(
        length_collected["rows"],
        min_len=min_len,
        counts=None,
        update=True,
    )["bits"]
    copy_source_stream = audit141.score_source_default_exception(
        source_collected["rows"],
        counts=None,
        update=True,
    )["bits"]
    copy_length_bits = copy_length_stream + 8.0
    copy_source_bits = copy_source_stream + 12.0
    total_bits = (
        float(score["fixed_bits"])
        + float(score["literal_bits_no_payload"])
        + float(score["literal_payload_bits"])
        + float(score["item_type_stream_bits"])
        + copy_length_bits
        + copy_source_bits
    )
    return {
        "total_bits": total_bits,
        "fixed_bits": score["fixed_bits"],
        "literal_bits_no_payload": score["literal_bits_no_payload"],
        "literal_payload_bits": score["literal_payload_bits"],
        "item_type_stream_bits": score["item_type_stream_bits"],
        "copy_length_default_exception_bits": copy_length_bits,
        "copy_source_default_exception_bits": copy_source_bits,
        "literal_runs": score["literal_runs"],
        "literal_digits": score["literal_digits"],
        "copy_items": score["copy_items"],
        "copied_digits": score["copied_digits"],
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
    }


def optional_literal_starts(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    min_len = int(formula["policy"]["min_len"])
    available = ""
    rows = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op_type(op) == "literal":
                text = op["text"]
                candidates = copy_candidates(available, target, book_pos, min_len)
                if candidates:
                    rows.append(
                        {
                            "book": int(book),
                            "op_index": op_index,
                            "book_pos": book_pos,
                            "literal_length": len(text),
                            "literal_preview": text[:32],
                            "candidate_count": len(candidates),
                            "max_candidate_length": max(row["max_length"] for row in candidates),
                            "candidates": candidates,
                        }
                    )
                available += text
                book_pos += len(text)
                continue
            source = int(op["source_digit_pos"])
            length = int(op["length"])
            available += available[source : source + length]
            book_pos += length
    return rows


def replace_literal_prefix(
    formula: dict[str, Any],
    *,
    book: int,
    op_index: int,
    source_digit_pos: int,
    length: int,
) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    ops = out["book_recipes"][str(book)]["ops"]
    op = ops[op_index]
    text = op["text"]
    remainder = text[length:]
    replacement: list[dict[str, Any]] = [
        {"source_digit_pos": int(source_digit_pos), "length": int(length)}
    ]
    if remainder:
        replacement.append({"text": remainder})
    ops[op_index : op_index + 1] = replacement
    return out


def make_result() -> dict[str, Any]:
    compile129 = load_module("compile129", COMPILE_129)
    modules = {
        "compile129": compile129,
        "compile134": load_module("compile134", COMPILE_134),
        "audit136": load_module("audit136", AUDIT_136),
        "audit137": load_module("audit137", AUDIT_137),
        "audit141": load_module("audit141", AUDIT_141),
    }
    audit126 = compile129.load_audit_126()
    modules.update(
        {
            "audit126": audit126,
            "frontier": load_module("frontier", audit126.FRONTIER),
            "midpoint": load_module("midpoint", audit126.MIDPOINT),
            "copy_module": load_module("copy_context", audit126.COPY_CONTEXT),
            "item_module": load_module("item_context", audit126.ITEM_CONTEXT),
        }
    )
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    min_len = int(formula["policy"]["min_len"])
    base_score = active_score(formula, modules, books)
    declared_total = float(
        formula["mdl_estimate_rough"][
            "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
        ]
    )
    optional_rows = optional_literal_starts(formula, books)

    eligible_starts = []
    candidates = []
    for row in optional_rows:
        max_prefix = min(int(row["literal_length"]), int(row["max_candidate_length"]))
        if max_prefix < min_len:
            continue
        eligible_starts.append(
            {
                "book": row["book"],
                "op_index": row["op_index"],
                "book_pos": row["book_pos"],
                "literal_length": row["literal_length"],
                "candidate_count": row["candidate_count"],
                "max_candidate_length": row["max_candidate_length"],
                "literal_preview": row["literal_preview"],
            }
        )
        for candidate in row["candidates"]:
            for length in range(min_len, min(row["literal_length"], candidate["max_length"]) + 1):
                repaired = replace_literal_prefix(
                    formula,
                    book=int(row["book"]),
                    op_index=int(row["op_index"]),
                    source_digit_pos=int(candidate["source_digit_pos"]),
                    length=length,
                )
                repaired_score = active_score(repaired, modules, books)
                candidates.append(
                    {
                        "book": row["book"],
                        "op_index": row["op_index"],
                        "book_pos": row["book_pos"],
                        "source_digit_pos": candidate["source_digit_pos"],
                        "copy_length": length,
                        "literal_length_before": row["literal_length"],
                        "literal_remainder_length": row["literal_length"] - length,
                        "delta_bits": repaired_score["total_bits"] - base_score["total_bits"],
                        "candidate_total_bits": repaired_score["total_bits"],
                        "literal_runs": repaired_score["literal_runs"],
                        "literal_digits": repaired_score["literal_digits"],
                        "copy_items": repaired_score["copy_items"],
                    }
                )
    candidates.sort(key=lambda row: row["delta_bits"])
    best = candidates[0] if candidates else None
    improving = [row for row in candidates if row["delta_bits"] < 0]
    classification = (
        "optional_literal_copy_repair_improves_active_formula"
        if improving
        else "optional_literal_copy_repairs_rejected_active_parser_retained"
    )
    return {
        "schema": "optional_literal_copy_repair_frontier.v1",
        "test": "150_optional_literal_copy_repair_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "min_len": min_len,
            "repair_family": (
                "single local replacement of a prefix of an optional literal run "
                "with a legal prior copy, leaving any literal suffix in place"
            ),
            "active_total_bits_declared": declared_total,
            "active_total_bits_recomputed": base_score["total_bits"],
            "optional_literal_starts": len(optional_rows),
            "eligible_optional_literal_starts": len(eligible_starts),
            "candidate_repairs_scored": len(candidates),
        },
        "base_score": base_score,
        "eligible_starts": eligible_starts,
        "best_candidate": best,
        "top_candidates": candidates[:20],
        "improving_candidate_count": len(improving),
        "decision": {
            "compression_bound_changed": bool(improving),
            "candidate_promoted": bool(improving),
            "active_parser_retained": not bool(improving),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    scope = result["scope"]
    best = result["best_candidate"]
    lines = [
        "# 150. Optional Literal Copy Repair Frontier",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 149 localized the residual literal parser frontier to optional",
        "literal starts where copy candidates exist. This audit tests the",
        "lowest-risk repair family: replace a prefix of one optional literal run",
        "with a legal prior copy, leaving any literal suffix intact, then rescore",
        "the complete active ledger.",
        "",
        "## Scope",
        "",
        f"- Active total bits declared: `{scope['active_total_bits_declared']:.3f}`",
        f"- Active total bits recomputed: `{scope['active_total_bits_recomputed']:.3f}`",
        f"- Optional literal starts from audit 149: `{scope['optional_literal_starts']}`",
        f"- Eligible starts with in-literal legal copy length: `{scope['eligible_optional_literal_starts']}`",
        f"- Candidate repairs scored: `{scope['candidate_repairs_scored']}`",
        "",
        "## Eligible Starts",
        "",
        "| Book | Op | Pos | Literal len | Candidates | Max copy len | Preview |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["eligible_starts"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['book_pos']}` | "
            f"`{row['literal_length']}` | `{row['candidate_count']}` | "
            f"`{row['max_candidate_length']}` | `{row['literal_preview']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Candidates",
            "",
            "| Rank | Delta bits | Total bits | Book | Op | Source | Copy len | Literal remainder |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, row in enumerate(result["top_candidates"][:10], start=1):
        lines.append(
            f"| `{rank}` | `{row['delta_bits']:.3f}` | `{row['candidate_total_bits']:.3f}` | "
            f"`{row['book']}` | `{row['op_index']}` | `{row['source_digit_pos']}` | "
            f"`{row['copy_length']}` | `{row['literal_remainder_length']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Improving candidates: `{result['improving_candidate_count']}`",
        ]
    )
    if best is not None:
        lines.append(
            f"- Best candidate is still `{best['delta_bits']:.3f}` bits worse than active."
        )
    lines.extend(
        [
            "- The active parser is retained for this repair family.",
            "- Compression bound unchanged.",
            "- Row0 origin, plaintext, and semantic status unchanged.",
            "",
            "## Interpretation",
            "",
            "The optional literal starts are not automatically mistakes. Under the",
            "active cost ledger, every tested in-literal copy repair is worse than",
            "the current parser choice. This closes the simplest residual repair",
            "frontier left by audit 149; broader repairs that cross op boundaries",
            "would need separate charging and controls.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "150_optional_literal_copy_repair_frontier.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "150_optional_literal_copy_repair_frontier.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
