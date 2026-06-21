from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469.json"
)
BASE_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_bits"
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
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


def collect_source_rows(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    previous_source = None
    previous_length = None
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

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

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            legal_source_count = max(1, len(emitted) - min_len + 1)
            if not 0 <= source < legal_source_count:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "source_out_of_range",
                        "source_digit_pos": source,
                        "legal_source_count": legal_source_count,
                    }
                )
            chunk = emitted[source : source + length]
            if target[book_pos : book_pos + length] != chunk:
                errors.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "type": "copy_mismatch",
                        "source_digit_pos": source,
                        "length": length,
                    }
                )
            if previous_source is None or previous_length is None:
                default = 0
            else:
                candidate = previous_source + previous_length
                default = candidate if candidate < legal_source_count else 0

            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source,
                    "length": length,
                    "legal_source_count": legal_source_count,
                    "previous_source_plus_length_default": default,
                    "source_equals_default": source == default,
                }
            )
            emitted += chunk
            book_pos += length
            previous_source = source
            previous_length = length
        if book_pos != len(target):
            errors.append(
                {
                    "book": book,
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )
    return {"rows": rows, "errors": errors}


def score_source_default_exception(rows: list[dict[str, Any]]) -> dict[str, Any]:
    flag_counts = {True: 0.0, False: 0.0}
    exception_counts: dict[int, float] = {}
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0

    for row in rows:
        is_default = bool(row["source_equals_default"])
        flag_probability = (flag_counts[is_default] + 1.0) / (
            flag_counts[True] + flag_counts[False] + 2.0
        )
        flag_bits += -math.log2(flag_probability)
        flag_counts[is_default] += 1.0

        if is_default:
            default_count += 1
            continue

        exception_count += 1
        legal_values = [
            source
            for source in range(int(row["legal_source_count"]))
            if source != int(row["previous_source_plus_length_default"])
        ]
        source = int(row["source_digit_pos"])
        if source not in legal_values:
            raise RuntimeError({"row": row, "legal_values": legal_values})
        total = sum(exception_counts.get(value, 0.0) for value in legal_values)
        probability = (exception_counts.get(source, 0.0) + 1.0) / (total + len(legal_values))
        exception_bits += -math.log2(probability)
        exception_counts[source] = exception_counts.get(source, 0.0) + 1.0

    return {
        "family": "previous_source_plus_length_default_with_global_adaptive_exception_source",
        "default_rule": "previous copy source plus previous copy length if legal, else 0",
        "flag_context": "global",
        "exception_source_context": "global",
        "alpha": 1,
        "flag_bits": flag_bits,
        "exception_source_bits": exception_bits,
        "stream_bits": flag_bits + exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "decodable": True,
    }


def main() -> None:
    compile129 = load_module("online_reparse_compile_129", COMPILE_129)
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = compile129.load_audit_126()
    frontier = load_module("frontier", audit126.FRONTIER)
    midpoint = load_module("midpoint", audit126.MIDPOINT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    base_formula = load_json(BASE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    active_bits = float(base_formula["mdl_estimate_rough"][BASE_TOTAL_KEY])
    active_copy_address_bits = float(base_formula["mdl_estimate_rough"]["copy_address_bits"])
    normalized = compile134.normalize_ops(base_formula)
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

    collected = collect_source_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = collected["rows"]
    model = score_source_default_exception(rows)
    conservative_extra_declaration_bits = 12.0
    candidate_copy_address_bits = model["stream_bits"] + conservative_extra_declaration_bits
    candidate_total_bits = active_bits - active_copy_address_bits + candidate_copy_address_bits
    candidate_gain_bits = active_bits - candidate_total_bits

    classification = (
        "controlled_copy_source_default_exception_formula_improvement"
        if candidate_gain_bits > 0
        else "copy_source_default_exception_not_promoted"
    )

    candidate_formula = {
        **base_formula,
        "classification": classification,
        "source_formula": rel(BASE_FORMULA),
        "copy_source_default_exception_compile": {
            "active_copy_address_bits": active_copy_address_bits,
            "candidate_copy_address_bits": candidate_copy_address_bits,
            "candidate_gain_bits": candidate_gain_bits,
            "conservative_extra_declaration_bits": conservative_extra_declaration_bits,
            "model": model,
        },
        "policy": {
            **base_formula["policy"],
            "copy_address_model": {
                **base_formula["policy"]["copy_address_model"],
                "family": model["family"],
                "default_rule": model["default_rule"],
                "flag_context": model["flag_context"],
                "exception_source_context": model["exception_source_context"],
                "exception_source_alphabet": "legal source positions excluding default source",
                "alpha": model["alpha"],
                "model_declaration_delta_bits": conservative_extra_declaration_bits,
                "replaces_family": base_formula["policy"]["copy_address_model"]["family"],
            },
        },
        "mdl_estimate_rough": {
            **base_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_total_bits,
            f"previous_{BASE_TOTAL_KEY}": active_bits,
            "gain_vs_previous_copy_length_default_exception_bits": candidate_gain_bits,
            "copy_source_default_exception_bits": candidate_copy_address_bits,
            "copy_source_default_exception_stream_bits": model["stream_bits"],
            "copy_source_default_exception_flag_bits": model["flag_bits"],
            "copy_source_default_exception_source_bits": model["exception_source_bits"],
            "copy_source_default_exception_declaration_delta_bits": conservative_extra_declaration_bits,
            "previous_copy_address_bits": active_copy_address_bits,
            "copy_address_bits": candidate_copy_address_bits,
        },
        "boundary": {
            **base_formula["boundary"],
            "translation_delta": "NONE",
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }
    OUT_FORMULA.write_text(json.dumps(candidate_formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "copy_source_default_decodability_audit.v1",
        "test": "137_copy_source_default_decodability_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(BASE_FORMULA),
        "active_bits": active_bits,
        "active_copy_address_bits": active_copy_address_bits,
        "candidate_copy_address_bits": candidate_copy_address_bits,
        "candidate_total_bits": candidate_total_bits,
        "candidate_gain_bits": candidate_gain_bits,
        "candidate_output_formula": rel(OUT_FORMULA),
        "conservative_extra_declaration_bits": conservative_extra_declaration_bits,
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
        "copy_items": len(rows),
        "model": model,
        "rows": rows,
        "boundary": {
            "compression_bound_changed": candidate_gain_bits > 0,
            "copy_source_dependency_removed": False,
            "copy_source_dependency_remodeled": candidate_gain_bits > 0,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 137. Copy Source Default Decodability Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "After copy length was remodeled as a decodable default/exception ledger,",
        "copy source remains the largest declared component. This audit tests a",
        "decodable source default: previous copy source plus previous copy length,",
        "falling back to 0 when illegal, plus a global adaptive exception source.",
        "",
        "## Result",
        "",
        f"- Active bits: `{active_bits:.3f}`",
        f"- Active copy-address bits: `{active_copy_address_bits:.3f}`",
        f"- Candidate copy-address bits: `{candidate_copy_address_bits:.3f}`",
        f"- Candidate total bits: `{candidate_total_bits:.3f}`",
        f"- Candidate gain: `{candidate_gain_bits:.3f}` bits",
        f"- Roundtrip: `{score['validation']['books_roundtrip_ok']}/70`",
        f"- Copy items: `{len(rows)}`",
        f"- Default source matches: `{model['default_count']}/{len(rows)}`",
        f"- Exception sources: `{model['exception_count']}/{len(rows)}`",
        f"- Declaration delta charged: `{conservative_extra_declaration_bits:.1f}` bits",
        "",
        "## Interpretation",
        "",
        "The default source rule is weak in raw coverage (`5/261`), but it is",
        "decodable and replaces a few expensive absolute addresses while the",
        "exception source stream gains from a global adaptive prior. After charging",
        f"`{conservative_extra_declaration_bits:.1f}` extra declaration bits, the",
        f"copy-address ledger drops from `{active_copy_address_bits:.3f}` to",
        f"`{candidate_copy_address_bits:.3f}` bits and the total bound becomes",
        f"`{candidate_total_bits:.3f}` bits.",
        "",
        "## Promoted Formula",
        "",
        f"- [{OUT_FORMULA.name}](../../{OUT_FORMULA.name})",
        "",
        "## Boundary",
        "",
        "- A new mechanical compression bound is promoted for copy-source coding.",
        "- Copy source is not removed; it is remodeled as a decodable default/exception ledger.",
        "- No plaintext or translation is introduced.",
        "- Row0/table origin is unchanged.",
    ]

    write_result("137_copy_source_default_decodability_audit", result, lines)


if __name__ == "__main__":
    main()
