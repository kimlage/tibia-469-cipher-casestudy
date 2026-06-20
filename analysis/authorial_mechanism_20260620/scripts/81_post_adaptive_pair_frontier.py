from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_pair_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
ADAPTIVE = HERE / "scripts/79_post_adaptive_copy_length_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_pair_repair_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_adaptive_module():
    spec = importlib.util.spec_from_file_location("post_adaptive_frontier", ADAPTIVE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive module: {ADAPTIVE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_formula(formula: dict, books: dict[str, str], adaptive, base_frontier) -> dict:
    return adaptive.score_formula(formula, books, base_frontier)


def collect_single_candidates(
    formula: dict,
    books: dict[str, str],
    current_bits: float,
    adaptive,
    base_frontier,
) -> tuple[list[dict], dict]:
    min_len = int(formula["policy"]["min_len"])
    candidates = []
    counts = {"literal_to_copy_tested": 0, "copy_to_literal_tested": 0, "invalid_singles": 0}
    for context in base_frontier.iter_contexts(formula):
        if context["kind"] == "literal":
            text = context["text"]
            for start in range(len(text)):
                available = context["emitted_before_op"] + text[:start]
                for length in range(min_len, len(text) - start + 1):
                    chunk = text[start : start + length]
                    source_digit_pos = available.find(chunk)
                    if source_digit_pos < 0:
                        continue
                    repair = {
                        "edit_type": "literal_to_copy",
                        "book": context["book"],
                        "op_index": context["op_index"],
                        "book_pos": context["book_pos"],
                        "literal_offset": start,
                        "length": length,
                        "source_digit_pos": source_digit_pos,
                        "text": chunk,
                    }
                    counts["literal_to_copy_tested"] += 1
                    score = score_formula(base_frontier.apply_literal_to_copy(formula, repair), books, adaptive, base_frontier)
                    if score["validation"]["errors"]:
                        counts["invalid_singles"] += 1
                        continue
                    candidates.append(
                        {
                            **repair,
                            "single_total_bits": score["total_bits"],
                            "single_delta_bits": score["total_bits"] - current_bits,
                        }
                    )
        elif context["kind"] == "copy":
            repair = {
                "edit_type": "copy_to_literal",
                "book": context["book"],
                "op_index": context["op_index"],
                "book_pos": context["book_pos"],
                "length": len(context["text"]),
                "text": context["text"],
            }
            counts["copy_to_literal_tested"] += 1
            score = score_formula(base_frontier.apply_copy_to_literal(formula, repair), books, adaptive, base_frontier)
            if score["validation"]["errors"]:
                counts["invalid_singles"] += 1
                continue
            candidates.append(
                {
                    **repair,
                    "single_total_bits": score["total_bits"],
                    "single_delta_bits": score["total_bits"] - current_bits,
                }
            )
    return candidates, counts


def repairs_compatible(left: dict, right: dict) -> bool:
    if (left["book"], left["op_index"]) != (right["book"], right["op_index"]):
        return True
    if left["edit_type"] != right["edit_type"]:
        return False
    if left["edit_type"] == "copy_to_literal":
        return False
    left_span = (left["literal_offset"], left["literal_offset"] + left["length"])
    right_span = (right["literal_offset"], right["literal_offset"] + right["length"])
    return left_span[1] <= right_span[0] or right_span[1] <= left_span[0]


def apply_repair_pair(formula: dict, repairs: tuple[dict, dict]) -> dict:
    out = copy.deepcopy(formula)
    grouped: dict[tuple[str, int], list[dict]] = {}
    for repair in repairs:
        grouped.setdefault((repair["book"], repair["op_index"]), []).append(repair)

    for (book, op_index), group in sorted(
        grouped.items(),
        key=lambda item: (int(item[0][0]), item[0][1]),
        reverse=True,
    ):
        ops = out["book_recipes"][book]["ops"]
        if len(group) == 1 and group[0]["edit_type"] == "copy_to_literal":
            repair = group[0]
            ops[op_index] = {
                "type": "literal",
                "text": repair["text"],
                "length": len(repair["text"]),
            }
            continue

        group = sorted(group, key=lambda row: row["literal_offset"])
        original = ops[op_index]
        text = original["text"]
        replacement = []
        cursor = 0
        for repair in group:
            start = repair["literal_offset"]
            end = start + repair["length"]
            if start < cursor:
                raise ValueError("overlapping repairs")
            if start > cursor:
                replacement.append({"type": "literal", "text": text[cursor:start], "length": start - cursor})
            replacement.append(
                {
                    "type": "copy",
                    "source_digit_pos": repair["source_digit_pos"],
                    "length": repair["length"],
                    "target_start": repair["book_pos"] + start,
                }
            )
            cursor = end
        if cursor < len(text):
            replacement.append({"type": "literal", "text": text[cursor:], "length": len(text) - cursor})
        ops[op_index : op_index + 1] = replacement
    return out


def strip_score(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {key: value for key, value in row.items() if key != "score"}


def main() -> None:
    adaptive = load_adaptive_module()
    base_frontier = adaptive.load_frontier_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = score_formula(formula, books, adaptive, base_frontier)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates, single_counts = collect_single_candidates(formula, books, current_bits, adaptive, base_frontier)
    best_single = min(candidates, key=lambda row: row["single_delta_bits"]) if candidates else None
    best_pair = None
    pair_counts = {
        "total_pairs_considered": 0,
        "compatible_pairs": 0,
        "overlapping_pairs_skipped": 0,
        "invalid_pairs": 0,
        "valid_pairs": 0,
    }

    for left, right in itertools.combinations(candidates, 2):
        pair_counts["total_pairs_considered"] += 1
        if not repairs_compatible(left, right):
            pair_counts["overlapping_pairs_skipped"] += 1
            continue
        pair_counts["compatible_pairs"] += 1
        score = score_formula(apply_repair_pair(formula, (left, right)), books, adaptive, base_frontier)
        if score["validation"]["errors"]:
            pair_counts["invalid_pairs"] += 1
            continue
        pair_counts["valid_pairs"] += 1
        row = {
            "total_bits": score["total_bits"],
            "delta_bits": score["total_bits"] - current_bits,
            "repairs": [left, right],
            "score": score,
        }
        if best_pair is None or row["total_bits"] < best_pair["total_bits"]:
            best_pair = row

    promoted = best_pair is not None and best_pair["delta_bits"] < -1e-9
    classification = (
        "controlled_post_adaptive_pair_repair_improvement"
        if promoted
        else "post_adaptive_pair_frontier_closed"
    )

    if promoted:
        out = apply_repair_pair(formula, tuple(best_pair["repairs"]))
        score = best_pair["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_pair_repair_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits": current_bits,
                    "gain_vs_previous_adaptive_repair2_bits": current_bits - score["total_bits"],
                    "literal_bits_no_payload": score["literal_bits_no_payload"],
                    "adaptive_context_order_literal_payload_bits": score["literal_payload_bits"],
                    "copy_bits": score["copy_bits"],
                    "copy_address_bits": score["copy_address_bits"],
                    "copy_length_code_bits": score["copy_length_code_bits"],
                    "bounded_adaptive_copy_length_bits": score["copy_length_code_bits"],
                    "item_type_context_order_stream_bits": score["item_type_stream_bits"],
                    "literal_runs": score["literal_runs"],
                    "literal_digits": score["literal_digits"],
                    "copy_items": score["copy_items"],
                    "copied_digits": score["copied_digits"],
                    "forced_literal_length_count": score["forced_literal_length_count"],
                    "forced_literal_length_saved_bits": score["forced_literal_length_saved_bits"],
                },
                "post_adaptive_pair_repair": {
                    "repairs": best_pair["repairs"],
                    "delta_bits": best_pair["delta_bits"],
                    "total_bits": best_pair["total_bits"],
                },
                "validation": {
                    **out["validation"],
                    "post_adaptive_pair_repair_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                },
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_adaptive_pair_frontier.v1",
        "test": "81_post_adaptive_pair_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "single_counts": single_counts,
        "valid_single_candidates": len(candidates),
        "best_single_repair": best_single,
        "pair_counts": pair_counts,
        "best_pair_repair": strip_score(best_pair),
        "best_pair_score": best_pair["score"] if best_pair else None,
        "promotion_rule": (
            "promote only if two compatible local edits beat the active adaptive "
            "copy-length formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Adaptive Pair Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests compatible pairs of local recipe edits after adaptive",
        "bounded copy-length coding became the active formula. It scores pairs of",
        "single literal-to-copy and copy-to-literal edits under full adaptive",
        "rescoring.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.3f}` |",
        f"| Literal-to-copy candidates tested | `{single_counts['literal_to_copy_tested']}` |",
        f"| Copy-to-literal candidates tested | `{single_counts['copy_to_literal_tested']}` |",
        f"| Invalid single candidates | `{single_counts['invalid_singles']}` |",
        f"| Valid single candidates | `{len(candidates)}` |",
        f"| Total pairs considered | `{pair_counts['total_pairs_considered']}` |",
        f"| Compatible pairs | `{pair_counts['compatible_pairs']}` |",
        f"| Invalid compatible pairs | `{pair_counts['invalid_pairs']}` |",
        f"| Valid pairs scored | `{pair_counts['valid_pairs']}` |",
    ]
    if best_single is not None:
        lines.append(f"| Best single delta | `{best_single['single_delta_bits']:.3f}` |")
    if best_pair is not None:
        lines.extend(
            [
                f"| Best pair total bits | `{best_pair['total_bits']:.3f}` |",
                f"| Best pair delta | `{best_pair['delta_bits']:.3f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Pair",
            "",
            "| Type | Book | Op | Text | Length | Single delta |",
            "|---|---:|---:|---|---:|---:|",
        ]
    )
    for row in (best_pair or {"repairs": []})["repairs"]:
        lines.append(
            f"| `{row['edit_type']}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['text']}` | `{row['length']}` | `{row['single_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The pair frontier is closed if the best fully rescored compatible pair",
            "remains at or above zero delta. This is a mechanical recipe audit only;",
            "it does not introduce plaintext, row0 meaning, or authorial intent.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("81_post_adaptive_pair_frontier", result, lines)


if __name__ == "__main__":
    main()
