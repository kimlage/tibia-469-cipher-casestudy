from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

CURRENT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE51 = TEST_RESULTS / "51_copy_length_segmentation_exception_audit.json"
AUDIT_129 = AUTHORIAL / "scripts" / "129_online_deterministic_reparse_compile.py"
AUDIT_136 = AUTHORIAL / "scripts" / "136_copy_length_default_decodability_audit.py"
AUDIT_137 = AUTHORIAL / "scripts" / "137_copy_source_default_decodability_audit.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_bits"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def score_compatible_components(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    compile129,
    audit136,
    audit137,
    modules: dict[str, Any],
) -> dict[str, Any]:
    split = compile129.score_splitonly_formula(
        formula=formula,
        books=books,
        audit126=modules["audit126"],
        frontier=modules["frontier"],
        midpoint=modules["midpoint"],
        copy_module=modules["copy_module"],
        item_module=modules["item_module"],
    )
    source_rows = audit137.collect_source_rows(formula, books)
    length_rows = audit136.collect_copy_length_rows(formula, books)
    errors = list(split["validation"]["errors"])
    errors.extend(source_rows["errors"])
    errors.extend(length_rows["errors"])
    source_bits = None
    length_bits = None
    if not source_rows["errors"]:
        source_model = audit137.score_source_default_exception(source_rows["rows"])
        source_bits = float(source_model["stream_bits"]) + 12.0
    else:
        source_model = None
    if not length_rows["errors"]:
        length_model = audit136.score_default_exception_model(
            length_rows["rows"],
            min_len=int(formula["policy"]["min_len"]),
            default_key="decoder_max_possible_default",
        )
        length_bits = float(length_model["stream_bits"]) + 8.0
    else:
        length_model = None
    return {
        "errors": errors,
        "split_score_total_bits": split["total_bits"],
        "literal_bits_no_payload": split["literal_bits_no_payload"],
        "literal_payload_bits": split["literal_payload_bits"],
        "item_type_bits": split["item_type_split_only_stream_bits"],
        "copy_source_bits": source_bits,
        "copy_length_bits": length_bits,
        "literal_runs": split["literal_runs"],
        "literal_digits": split["literal_digits"],
        "copy_items": split["copy_items"],
        "copied_digits": split["copied_digits"],
        "source_model": source_model,
        "length_model": length_model,
    }


def component_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, float]:
    keys = [
        "literal_bits_no_payload",
        "literal_payload_bits",
        "item_type_bits",
        "copy_source_bits",
        "copy_length_bits",
    ]
    return {
        key: float(candidate[key]) - float(baseline[key])
        for key in keys
        if candidate[key] is not None and baseline[key] is not None
    }


def reconstruct_book(formula: dict[str, Any], books: dict[str, str], book: str) -> list[dict[str, Any]]:
    emitted = ""
    for prior in map(str, formula["policy"]["book_order"]):
        if prior == book:
            break
        for op in formula["book_recipes"][prior]["ops"]:
            emitted += op["text"] if op["type"] == "literal" else emitted[
                int(op["source_digit_pos"]) : int(op["source_digit_pos"]) + int(op["length"])
            ]
    target = books[book]
    book_pos = 0
    rows = []
    for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
        if op["type"] == "literal":
            text = op["text"]
            rows.append(
                {
                    "op_index": op_index,
                    "type": "literal",
                    "start": book_pos,
                    "end": book_pos + len(text),
                    "text": text,
                }
            )
            emitted += text
            book_pos += len(text)
        else:
            source = int(op["source_digit_pos"])
            length = int(op["length"])
            text = emitted[source : source + length]
            rows.append(
                {
                    "op_index": op_index,
                    "type": "copy",
                    "start": book_pos,
                    "end": book_pos + length,
                    "text": text,
                    "source_digit_pos": source,
                }
            )
            emitted += text
            book_pos += length
    if "".join(row["text"] for row in rows) != target:
        raise RuntimeError({"book": book, "type": "reconstruct_book_mismatch"})
    return rows


def apply_targetmax_trim(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    exception: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    book = str(exception["book"])
    op_index = int(exception["op_index"])
    slack = int(exception["target_max_slack"])
    ops = out["book_recipes"][book]["ops"]
    if op_index + 1 >= len(ops):
        raise RuntimeError({"type": "missing_next_op", "exception": exception})
    current = ops[op_index]
    following = ops[op_index + 1]
    rows = reconstruct_book(formula, books, book)
    following_text = rows[op_index + 1]["text"]
    remaining_text = following_text[slack:]
    current["length"] = int(current["length"]) + slack
    if following["type"] == "literal":
        following["text"] = following["text"][slack:]
        following["length"] = len(following["text"])
    elif mode == "preserve_next_mode":
        following["source_digit_pos"] = int(following["source_digit_pos"]) + slack
        following["length"] = int(following["length"]) - slack
    elif mode == "literalize_next_remainder":
        following.clear()
        following.update(
            {
                "type": "literal",
                "text": remaining_text,
                "length": len(remaining_text),
            }
        )
    else:
        raise RuntimeError(f"unknown mode: {mode}")
    if following.get("length") == 0:
        del ops[op_index + 1]
    return out


def roundtrip_errors(formula: dict[str, Any], books: dict[str, str]) -> list[dict[str, Any]]:
    emitted = ""
    errors = []
    for book in map(str, formula["policy"]["book_order"]):
        rendered = []
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != int(op["length"]):
                    errors.append({"book": book, "op_index": op_index, "type": "literal_length_mismatch"})
            else:
                source = int(op["source_digit_pos"])
                length = int(op["length"])
                chunk = emitted[source : source + length]
                if len(chunk) != length:
                    errors.append({"book": book, "op_index": op_index, "type": "short_copy"})
            rendered.append(chunk)
            emitted += chunk
        if "".join(rendered) != books[book]:
            errors.append({"book": book, "type": "book_roundtrip_mismatch"})
    return errors


def make_result() -> dict[str, Any]:
    gate51 = load_json(GATE51)
    assert_boundary("copy_length_segmentation_exception_audit", gate51)
    compile129 = load_module("compile129", AUDIT_129)
    audit136 = load_module("audit136", AUDIT_136)
    audit137 = load_module("audit137", AUDIT_137)
    audit126 = compile129.load_audit_126()
    modules = {
        "audit126": audit126,
        "frontier": load_module("frontier", audit126.FRONTIER),
        "midpoint": load_module("midpoint", audit126.MIDPOINT),
        "copy_module": load_module("copy_context", audit126.COPY_CONTEXT),
        "item_module": load_module("item_context", audit126.ITEM_CONTEXT),
    }
    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    baseline = score_compatible_components(
        formula=formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    if baseline["errors"]:
        raise RuntimeError({"type": "baseline_score_errors", "errors": baseline["errors"][:5]})
    candidates = []
    for exception in gate51["exception_rows"]:
        for mode in ["preserve_next_mode", "literalize_next_remainder"]:
            candidate_formula = apply_targetmax_trim(
                formula=formula,
                books=books,
                exception=exception,
                mode=mode,
            )
            rt_errors = roundtrip_errors(candidate_formula, books)
            score = score_compatible_components(
                formula=candidate_formula,
                books=books,
                compile129=compile129,
                audit136=audit136,
                audit137=audit137,
                modules=modules,
            )
            deltas = component_delta(score, baseline) if not score["errors"] else {}
            compatible_delta = sum(deltas.values()) if deltas else None
            candidates.append(
                {
                    "mode": mode,
                    "book": exception["book"],
                    "op_index": exception["op_index"],
                    "following_op_type": exception["first_covered_following_op_type"],
                    "slack": exception["target_max_slack"],
                    "roundtrip_ok": not rt_errors,
                    "roundtrip_errors": rt_errors[:5],
                    "score_errors": score["errors"][:5],
                    "compatible_component_delta_bits": compatible_delta,
                    "candidate_total_proxy_bits": (
                        None if compatible_delta is None else current_total + compatible_delta
                    ),
                    "component_delta_bits": deltas,
                    "inventory": {
                        "literal_runs": score["literal_runs"],
                        "literal_digits": score["literal_digits"],
                        "copy_items": score["copy_items"],
                        "copied_digits": score["copied_digits"],
                    },
                }
            )
    valid = [
        row
        for row in candidates
        if row["roundtrip_ok"]
        and not row["score_errors"]
        and row["compatible_component_delta_bits"] is not None
    ]
    improving = [
        row for row in valid if float(row["compatible_component_delta_bits"]) < 0
    ]
    best = min(
        valid,
        key=lambda row: float(row["compatible_component_delta_bits"]),
    ) if valid else None
    classification = (
        "targetmax_local_resegmentation_has_proxy_improvements_unpromoted"
        if improving
        else "targetmax_local_resegmentation_no_proxy_improvement"
    )
    return {
        "schema": "targetmax_resegmentation_candidate_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_length_segmentation_exception_audit": rel(GATE51),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
            "scoring_note": (
                "Candidate totals are compatible component proxies: current bound "
                "plus rescored deltas for literal structure, literal payload, item "
                "type, copy source default/exception, and copy length default/"
                "exception. No bound is promoted from this proxy."
            ),
        },
        "summary": {
            "current_total_bits": current_total,
            "exception_count": len(gate51["exception_rows"]),
            "candidate_count": len(candidates),
            "valid_candidate_count": len(valid),
            "improving_proxy_candidate_count": len(improving),
            "best_candidate": best,
            "best_proxy_delta_bits": (
                None if best is None else best["compatible_component_delta_bits"]
            ),
            "best_proxy_total_bits": (
                None if best is None else best["candidate_total_proxy_bits"]
            ),
            "valid_by_mode": {
                mode: sum(1 for row in valid if row["mode"] == mode)
                for mode in ["preserve_next_mode", "literalize_next_remainder"]
            },
            "improving_by_mode": {
                mode: sum(1 for row in improving if row["mode"] == mode)
                for mode in ["preserve_next_mode", "literalize_next_remainder"]
            },
            "interpretation": (
                "Local target-max resegmentation is mechanically testable. Any "
                "proxy improvement remains unpromoted until an exact current-bound "
                "scorer or full reparse objective validates it."
            ),
        },
        "candidates": candidates,
        "decision": {
            "compression_bound_status": "unchanged_proxy_only",
            "targetmax_resegmentation_status": (
                "local_candidates_mapped_proxy_not_promoted"
            ),
            "generation_explanation_status": "resegmentation_path_opened",
            "next_mainline_status": "exact_bound_scorer_or_joint_reparse_required_before_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "52_targetmax_resegmentation_candidate_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_candidate"]
    lines = [
        "# Target-Max Resegmentation Candidate Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 51 showed that each non-target-max copy length enters one following",
        "operation and stops inside it. This audit tests the local mechanical",
        "rewrite: extend the copy to target-max and trim the following op.",
        "",
        "## Summary",
        "",
        f"- Current total bits: `{s['current_total_bits']:.6f}`.",
        f"- Exceptions tested: `{s['exception_count']}`.",
        f"- Candidates tested: `{s['candidate_count']}`.",
        f"- Valid candidates: `{s['valid_candidate_count']}`.",
        f"- Proxy-improving candidates: `{s['improving_proxy_candidate_count']}`.",
        f"- Valid by mode: `{s['valid_by_mode']}`.",
        f"- Improving by mode: `{s['improving_by_mode']}`.",
    ]
    if best:
        lines.extend(
            [
                f"- Best proxy delta: `{best['compatible_component_delta_bits']:+.6f}` bits.",
                f"- Best proxy total: `{best['candidate_total_proxy_bits']:.6f}` bits.",
                f"- Best candidate: book `{best['book']}`, op `{best['op_index']}`, mode `{best['mode']}`, slack `{best['slack']}`.",
                f"- Best component deltas: `{best['component_delta_bits']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Candidate Table",
            "",
            "| Book | Op | Mode | Next | Slack | Roundtrip | Score errors | Proxy delta |",
            "|---:|---:|---|---|---:|---|---:|---:|",
        ]
    )
    for row in result["candidates"]:
        delta = row["compatible_component_delta_bits"]
        delta_text = "NA" if delta is None else f"{delta:+.6f}"
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['mode']}` | "
            f"`{row['following_op_type']}` | `{row['slack']}` | "
            f"`{row['roundtrip_ok']}` | `{len(row['score_errors'])}` | "
            f"`{delta_text}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is not a promoted formula gate. It maps whether the local",
            "target-max resegmentation rewrite is mechanically valid and whether",
            "the available compatible component scorer sees a possible improvement.",
            "A real compression-bound promotion still requires exact scoring under",
            "the current full source-substitution ledger or a joint reparse objective.",
            "",
            "## Boundary",
            "",
            "- No new formula is emitted.",
            "- Compression bound is unchanged.",
            "- Candidate totals are proxy diagnostics, not promoted bounds.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "52_targetmax_resegmentation_candidate_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
