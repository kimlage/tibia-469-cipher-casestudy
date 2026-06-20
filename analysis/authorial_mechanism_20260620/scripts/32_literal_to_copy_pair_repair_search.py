from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASE_SCRIPT = HERE / "scripts" / "29_literal_to_copy_repair_search.py"
SOURCE_FORMULA = HERE / "sequential_lz_literal_payload_formula_469.json"
REPAIRED_FORMULA = HERE / "sequential_lz_literal_copy_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"


def load_repair_module():
    spec = importlib.util.spec_from_file_location("literal_repair", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def collect_single_repairs(repair, formula: dict, books: dict[str, str]) -> list[dict]:
    current_bits = repair.score_formula(formula, books)["total_bits"]
    min_len = int(formula["policy"]["min_len"])
    candidates = []
    for ctx in repair.iter_literal_contexts(formula):
        text = ctx["text"]
        for start in range(len(text)):
            available = ctx["emitted_before_op"] + text[:start]
            max_len = len(text) - start
            for length in range(min_len, max_len + 1):
                chunk = text[start : start + length]
                source_pos = available.find(chunk)
                if source_pos < 0:
                    continue
                candidate = {
                    "book": ctx["book"],
                    "op_index": ctx["op_index"],
                    "book_pos": ctx["book_pos"],
                    "literal_offset": start,
                    "source_pos": source_pos,
                    "length": length,
                    "chunk": chunk,
                }
                score = repair.score_formula(repair.apply_repair(formula, candidate), books)
                if score["validation"]["errors"]:
                    continue
                candidates.append(
                    {
                        **candidate,
                        "single_total_bits": score["total_bits"],
                        "single_delta_vs_source_bits": score["total_bits"] - current_bits,
                    }
                )
    return candidates


def repairs_compatible(left: dict, right: dict) -> bool:
    if (left["book"], left["op_index"]) != (right["book"], right["op_index"]):
        return True
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
        group = sorted(group, key=lambda repair: repair["literal_offset"])
        ops = out["book_recipes"][book]["ops"]
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
                    "source_pos": repair["source_pos"],
                    "length": repair["length"],
                    "target_start": repair["book_pos"] + start,
                }
            )
            cursor = end
        if cursor < len(text):
            replacement.append({"type": "literal", "text": text[cursor:], "length": len(text) - cursor})
        ops[op_index : op_index + 1] = replacement
    return out


def main() -> None:
    repair = load_repair_module()
    source_formula = repair.load_json(SOURCE_FORMULA)
    repaired_formula = repair.load_json(REPAIRED_FORMULA)
    books = {str(key): value for key, value in repair.load_json(BOOKS_DIGITS).items()}

    source_bits = repair.score_formula(source_formula, books)["total_bits"]
    repaired_bits = repaired_formula["mdl_estimate_rough"]["sequential_lz_literal_copy_repair_bits"]
    candidates = collect_single_repairs(repair, source_formula, books)

    best_pair = None
    compatible_pairs = 0
    overlapping_pairs = 0
    for left, right in itertools.combinations(candidates, 2):
        if not repairs_compatible(left, right):
            overlapping_pairs += 1
            continue
        compatible_pairs += 1
        candidate_formula = apply_repair_pair(source_formula, (left, right))
        score = repair.score_formula(candidate_formula, books)
        if score["validation"]["errors"]:
            raise RuntimeError(score["validation"]["errors"])
        row = {
            "total_bits": score["total_bits"],
            "delta_vs_source_bits": score["total_bits"] - source_bits,
            "delta_vs_repaired_bits": score["total_bits"] - repaired_bits,
            "repairs": [left, right],
        }
        if best_pair is None or row["total_bits"] < best_pair["total_bits"]:
            best_pair = row

    best_single = min(candidates, key=lambda row: row["single_total_bits"])
    promoted = best_pair is not None and best_pair["total_bits"] < repaired_bits
    classification = (
        "literal_to_copy_pair_repair_improvement"
        if promoted
        else "literal_to_copy_pair_repair_not_promoted"
    )

    result = {
        "schema": "literal_to_copy_pair_repair_search.v1",
        "test": "32_literal_to_copy_pair_repair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(SOURCE_FORMULA.relative_to(ROOT)),
        "repaired_formula": str(REPAIRED_FORMULA.relative_to(ROOT)),
        "source_formula_bits": source_bits,
        "current_repaired_formula_bits": repaired_bits,
        "single_candidates": len(candidates),
        "compatible_pairs_tested": compatible_pairs,
        "overlapping_pairs_skipped": overlapping_pairs,
        "total_pairs_considered": compatible_pairs + overlapping_pairs,
        "best_single_repair": best_single,
        "best_pair_repair": best_pair,
        "boundary": repaired_formula["boundary"],
    }

    lines = [
        "# Literal-to-Copy Pair Repair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether two literal-to-copy repairs become cheaper",
        "together under the adaptive literal-payload model, even when the second",
        "repair is not individually profitable after the known local repair.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Source formula bits | `{source_bits:.1f}` |",
        f"| Current repaired formula bits | `{repaired_bits:.1f}` |",
        f"| Single repair candidates | `{len(candidates)}` |",
        f"| Compatible pairs tested | `{compatible_pairs}` |",
        f"| Overlapping pairs skipped | `{overlapping_pairs}` |",
    ]
    if best_pair is not None:
        lines.extend(
            [
                f"| Best pair total bits | `{best_pair['total_bits']:.1f}` |",
                f"| Best pair delta vs source | `{best_pair['delta_vs_source_bits']:.1f}` |",
                f"| Best pair delta vs repaired | `{best_pair['delta_vs_repaired_bits']:.1f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Pair",
            "",
            "| Book | Literal offset | Chunk | Source pos | Length | Single delta vs source |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )
    for repair_row in (best_pair or {"repairs": []})["repairs"]:
        lines.append(
            f"| `{repair_row['book']}` | `{repair_row['literal_offset']}` | "
            f"`{repair_row['chunk']}` | `{repair_row['source_pos']}` | "
            f"`{repair_row['length']}` | `{repair_row['single_delta_vs_source_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The best compatible two-repair recipe is still worse than the current",
            "one-step repaired formula. The local literal-to-copy frontier remains",
            "closed under single repairs and compatible repair pairs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("32_literal_to_copy_pair_repair_search", result, lines)


if __name__ == "__main__":
    main()
