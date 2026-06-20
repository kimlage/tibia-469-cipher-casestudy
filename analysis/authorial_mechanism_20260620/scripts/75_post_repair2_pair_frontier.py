from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_frontier_module():
    spec = importlib.util.spec_from_file_location("minaddr_frontier", FRONTIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frontier module: {FRONTIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_single_candidates(frontier, formula: dict, books: dict[str, str], current_bits: float) -> tuple[list[dict], dict]:
    min_len = int(formula["policy"]["min_len"])
    candidates = []
    counts = {"literal_to_copy_tested": 0, "copy_to_literal_tested": 0, "invalid_singles": 0}
    for context in frontier.iter_contexts(formula):
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
                    score = frontier.score_formula(frontier.apply_literal_to_copy(formula, repair), books)
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
            score = frontier.score_formula(frontier.apply_copy_to_literal(formula, repair), books)
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


def strip_score(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "score"}


def main() -> None:
    frontier = load_frontier_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = frontier.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates, single_counts = collect_single_candidates(frontier, formula, books, current_bits)
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
        score = frontier.score_formula(apply_repair_pair(formula, (left, right)), books)
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
        "post_repair2_pair_frontier_improvement"
        if promoted
        else "post_repair2_pair_frontier_closed"
    )

    result = {
        "schema": "post_repair2_pair_frontier.v1",
        "test": "75_post_repair2_pair_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "single_counts": single_counts,
        "valid_single_candidates": len(candidates),
        "best_single_repair": best_single,
        "pair_counts": pair_counts,
        "best_pair_repair": best_pair,
        "promotion_rule": (
            "promote only if two compatible local edits after the active repair2 formula "
            "beat the active formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Repair2 Pair Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether two compatible local edits become cheaper",
        "together after the one-step post-repair2 frontier closed. It uses the",
        "active full rescoring model: contextual literal payload, contextual",
        "item types with forced rules, bounded copy lengths, and min_len-bounded",
        "absolute source addresses.",
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
            "The compatible-pair frontier is closed if the best fully rescored pair",
            "remains at or above zero delta. This is a mechanical recipe audit only;",
            "it does not introduce plaintext, row0 meaning, or authorial intent.",
        ]
    )
    write_result("75_post_repair2_pair_frontier", result, lines)


if __name__ == "__main__":
    main()
