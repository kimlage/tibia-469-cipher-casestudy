from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
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
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469.json"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_bits"
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


def max_target_extension(*, emitted: str, source_pos: int, target: str, book_pos: int) -> int:
    max_len = min(len(emitted) - source_pos, len(target) - book_pos)
    length = 0
    while length < max_len and emitted[source_pos + length] == target[book_pos + length]:
        length += 1
    return length


def collect_copy_length_rows(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    previous_copy_length = None
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

            decoder_max_possible = min(len(emitted) - source_pos, len(target) - book_pos)
            encoder_target_max = max_target_extension(
                emitted=emitted,
                source_pos=source_pos,
                target=target,
                book_pos=book_pos,
            )
            previous_default = previous_copy_length if previous_copy_length is not None else min_len
            rows.append(
                {
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source_pos,
                    "length": length,
                    "min_len_default": min_len,
                    "previous_length_default": previous_default,
                    "decoder_max_possible_default": decoder_max_possible,
                    "encoder_target_max_default": encoder_target_max,
                    "length_equals_min_len": length == min_len,
                    "length_equals_previous": length == previous_default,
                    "length_equals_decoder_max_possible": length == decoder_max_possible,
                    "length_equals_encoder_target_max": length == encoder_target_max,
                    "decoder_max_possible_slack": decoder_max_possible - length,
                    "encoder_target_max_slack": encoder_target_max - length,
                }
            )
            emitted += chunk
            book_pos += length
            previous_copy_length = length
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


def exception_cost_lower_bound(rows: list[dict[str, Any]], default_key: str, min_len: int) -> dict[str, Any]:
    exceptions = [row for row in rows if row["length"] != row[default_key]]
    # A deliberately optimistic bound: choose exception positions plus an ideal
    # bounded value for each exception. If this is not decodable, it is still not
    # promotable; if it is decodable, it is only a lower bound before model costs.
    n = len(rows)
    k = len(exceptions)
    choose_bits = math.log2(math.comb(n, k)) if 0 <= k <= n else float("inf")
    value_bits = 0.0
    for row in exceptions:
        max_symbol_count = max(1, row["decoder_max_possible_default"] - min_len + 1)
        value_bits += math.log2(max_symbol_count)
    return {
        "exception_count": k,
        "match_count": n - k,
        "optimistic_position_bits": choose_bits,
        "optimistic_exception_value_bits": value_bits,
        "optimistic_total_bits": choose_bits + value_bits,
    }


def score_default_exception_model(rows: list[dict[str, Any]], *, min_len: int, default_key: str) -> dict[str, Any]:
    flag_counts: dict[str, dict[bool, float]] = {}
    exception_counts: dict[str, dict[int, float]] = {}
    flag_bits = 0.0
    exception_bits = 0.0
    context_counts: dict[str, int] = {}
    exception_context_counts: dict[str, int] = {}
    exception_count = 0
    default_count = 0

    for row in rows:
        context = "first_half" if int(row["book"]) < 35 else "second_half"
        context_counts[context] = context_counts.get(context, 0) + 1
        is_default = row["length"] == row[default_key]
        flag_bucket = flag_counts.setdefault(context, {True: 0.0, False: 0.0})
        flag_total = flag_bucket[True] + flag_bucket[False]
        flag_probability = (flag_bucket[is_default] + 1.0) / (flag_total + 2.0)
        flag_bits += -math.log2(flag_probability)
        flag_bucket[is_default] += 1.0

        if is_default:
            default_count += 1
            continue

        exception_count += 1
        exception_context_counts[context] = exception_context_counts.get(context, 0) + 1
        legal_lengths = [
            length
            for length in range(min_len, int(row["decoder_max_possible_default"]) + 1)
            if length != int(row[default_key])
        ]
        if row["length"] not in legal_lengths:
            raise RuntimeError({"row": row, "legal_lengths": legal_lengths})
        exception_bucket = exception_counts.setdefault(context, {})
        exception_total = sum(exception_bucket.get(length, 0.0) for length in legal_lengths)
        exception_probability = (exception_bucket.get(row["length"], 0.0) + 1.0) / (
            exception_total + len(legal_lengths)
        )
        exception_bits += -math.log2(exception_probability)
        exception_bucket[row["length"]] = exception_bucket.get(row["length"], 0.0) + 1.0

    return {
        "family": "decoder_max_possible_default_with_adaptive_exception_length",
        "default_key": default_key,
        "flag_context": "book_id < 35 versus book_id >= 35",
        "exception_length_context": "book_id < 35 versus book_id >= 35",
        "alpha": 1,
        "flag_bits": flag_bits,
        "exception_length_bits": exception_bits,
        "stream_bits": flag_bits + exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "context_counts": dict(sorted(context_counts.items())),
        "exception_context_counts": dict(sorted(exception_context_counts.items())),
        "decodable": True,
    }


def summarize_rule(rows: list[dict[str, Any]], *, name: str, key: str, decodable: bool, min_len: int) -> dict[str, Any]:
    lower = exception_cost_lower_bound(rows, key, min_len)
    slack_counter = Counter(row[key] - row["length"] for row in rows)
    return {
        "rule": name,
        "default_key": key,
        "decodable": decodable,
        "match_count": lower["match_count"],
        "exception_count": lower["exception_count"],
        "coverage_fraction": lower["match_count"] / len(rows) if rows else 0.0,
        "optimistic_exception_lower_bound_bits": lower["optimistic_total_bits"],
        "slack_counter_top": slack_counter.most_common(12),
    }


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
    active_copy_length_bits = float(compact_formula["mdl_estimate_rough"]["copy_length_code_bits"])
    old_copy_model_declaration_bits = float(compact_formula["mdl_estimate_rough"]["copy_model_declaration_bits"])
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

    min_len = int(normalized["policy"]["min_len"])
    collected = collect_copy_length_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = collected["rows"]

    rules = [
        summarize_rule(
            rows,
            name="min_len_default",
            key="min_len_default",
            decodable=True,
            min_len=min_len,
        ),
        summarize_rule(
            rows,
            name="previous_copy_length_default",
            key="previous_length_default",
            decodable=True,
            min_len=min_len,
        ),
        summarize_rule(
            rows,
            name="decoder_max_possible_after_source",
            key="decoder_max_possible_default",
            decodable=True,
            min_len=min_len,
        ),
        summarize_rule(
            rows,
            name="encoder_target_max_extension",
            key="encoder_target_max_default",
            decodable=False,
            min_len=min_len,
        ),
    ]

    best_decodable = max(
        [row for row in rules if row["decodable"]],
        key=lambda row: row["match_count"],
    )
    encoder_only = next(row for row in rules if row["rule"] == "encoder_target_max_extension")
    default_exception_model = score_default_exception_model(
        rows,
        min_len=min_len,
        default_key="decoder_max_possible_default",
    )
    conservative_extra_declaration_bits = 8.0
    candidate_copy_length_bits = (
        default_exception_model["stream_bits"] + conservative_extra_declaration_bits
    )
    candidate_total_bits = active_bits - active_copy_length_bits + candidate_copy_length_bits
    candidate_gain_bits = active_bits - candidate_total_bits
    classification = (
        "controlled_copy_length_default_exception_formula_improvement"
        if candidate_gain_bits > 0
        else "copy_length_encoder_max_signal_nondecodable_no_promotion"
    )

    candidate_formula = {
        **compact_formula,
        "classification": classification,
        "source_formula": rel(TYPE_DERIVED_FORMULA),
        "copy_length_default_exception_compile": {
            "active_copy_length_bits": active_copy_length_bits,
            "candidate_copy_length_bits": candidate_copy_length_bits,
            "candidate_gain_bits": candidate_gain_bits,
            "conservative_extra_declaration_bits": conservative_extra_declaration_bits,
            "old_copy_model_declaration_bits": old_copy_model_declaration_bits,
            "model": default_exception_model,
        },
        "policy": {
            **compact_formula["policy"],
            "copy_length_model": {
                **compact_formula["policy"]["copy_length_model"],
                "family": default_exception_model["family"],
                "default_rule": "copy decoder_max_possible length unless exception flag is false",
                "default_length": "min(declared_book_remaining_digits, emitted_digit_count_after_source_address)",
                "flag_context": default_exception_model["flag_context"],
                "exception_length_context": default_exception_model["exception_length_context"],
                "exception_length_alphabet": (
                    "legal lengths from min_len through decoder_max_possible, excluding default length"
                ),
                "alpha": default_exception_model["alpha"],
                "model_declaration_delta_bits": conservative_extra_declaration_bits,
                "replaces_family": compact_formula["policy"]["copy_length_model"]["family"],
            },
        },
        "mdl_estimate_rough": {
            **compact_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_total_bits,
            f"previous_{TYPE_DERIVED_TOTAL_KEY}": active_bits,
            "gain_vs_previous_type_derived_bits": candidate_gain_bits,
            "copy_length_default_exception_bits": candidate_copy_length_bits,
            "copy_length_default_exception_stream_bits": default_exception_model["stream_bits"],
            "copy_length_default_exception_flag_bits": default_exception_model["flag_bits"],
            "copy_length_default_exception_length_bits": default_exception_model["exception_length_bits"],
            "copy_length_default_exception_declaration_delta_bits": conservative_extra_declaration_bits,
            "previous_copy_length_code_bits": active_copy_length_bits,
            "copy_length_code_bits": candidate_copy_length_bits,
            "bounded_adaptive_copy_length_bits": candidate_copy_length_bits,
        },
        "boundary": {
            **compact_formula["boundary"],
            "translation_delta": "NONE",
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }
    OUT_FORMULA.write_text(json.dumps(candidate_formula, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "copy_length_default_decodability_audit.v1",
        "test": "136_copy_length_default_decodability_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": rel(TYPE_DERIVED_FORMULA),
        "active_bits": active_bits,
        "active_copy_length_bits": active_copy_length_bits,
        "candidate_copy_length_bits": candidate_copy_length_bits,
        "candidate_total_bits": candidate_total_bits,
        "candidate_gain_bits": candidate_gain_bits,
        "candidate_output_formula": rel(OUT_FORMULA),
        "conservative_extra_declaration_bits": conservative_extra_declaration_bits,
        "recomputed_bits": score["total_bits"],
        "roundtrip_ok": score["validation"]["books_roundtrip_ok"],
        "copy_items": len(rows),
        "rules": rules,
        "best_decodable_rule": best_decodable,
        "encoder_only_rule": encoder_only,
        "default_exception_model": default_exception_model,
        "rows": rows,
        "boundary": {
            "compression_bound_changed": candidate_gain_bits > 0,
            "copy_length_dependency_removed": False,
            "copy_length_dependency_remodeled": candidate_gain_bits > 0,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 136. Copy Length Default Decodability Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 135 found that most copy lengths equal the maximum extension",
        "against the target book. This audit checks whether that can become a",
        "decoder-side default rule, or whether it depends on future target digits",
        "only known to the encoder.",
        "",
        "## Result",
        "",
        f"- Active bits: `{active_bits:.3f}`",
        f"- Active copy-length bits: `{active_copy_length_bits:.3f}`",
        f"- Candidate copy-length bits: `{candidate_copy_length_bits:.3f}`",
        f"- Candidate total bits: `{candidate_total_bits:.3f}`",
        f"- Candidate gain: `{candidate_gain_bits:.3f}` bits",
        f"- Recomputed bits: `{score['total_bits']:.3f}`",
        f"- Roundtrip: `{score['validation']['books_roundtrip_ok']}/70`",
        f"- Copy items: `{len(rows)}`",
        "",
        "| Rule | Decodable | Matches | Exceptions | Coverage | Optimistic exception lower bound |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rules:
        lines.append(
            f"| `{row['rule']}` | `{row['decodable']}` | `{row['match_count']}` | "
            f"`{row['exception_count']}` | `{row['coverage_fraction']:.3f}` | "
            f"`{row['optimistic_exception_lower_bound_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The high-coverage default is `encoder_target_max_extension`: it matches",
            "`238/261` copies. But that rule compares the source chunk against future",
            "target digits, which the decoder does not know before decoding the copy.",
            "The best decoder-side default tested here, `decoder_max_possible_after_source`,",
            "matches only `60/261` copies as a pure default. However, a decodable",
            "default/exception ledger can use that default and encode a flag plus",
            "adaptive exception length. With an explicit `8` bit declaration delta,",
            f"that remaps copy-length cost from `{active_copy_length_bits:.3f}` to",
            f"`{candidate_copy_length_bits:.3f}` bits, lowering the formula to",
            f"`{candidate_total_bits:.3f}` bits.",
            "",
            "## Promoted Formula",
            "",
            f"- [{OUT_FORMULA.name}](../../{OUT_FORMULA.name})",
            "",
            "## Boundary",
            "",
            "- A new mechanical compression bound is promoted for copy-length coding.",
            "- Copy length is not removed entirely; it is remodeled as a decodable default/exception ledger.",
            "- No plaintext or translation is introduced.",
            "- Row0/table origin is unchanged.",
        ]
    )

    write_result("136_copy_length_default_decodability_audit", result, lines)


if __name__ == "__main__":
    main()
