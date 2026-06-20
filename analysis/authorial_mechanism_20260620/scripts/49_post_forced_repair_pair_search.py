from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BASE_SCRIPT = HERE / "scripts" / "46_forced_length_literal_repair_search.py"
FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
CURRENT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_repair_bits"


def load_repair_module():
    spec = importlib.util.spec_from_file_location("forced_length_literal_repair", BASE_SCRIPT)
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


def collect_single_repairs(repair, formula: dict, books: dict[str, str], current_bits: float) -> list[dict]:
    min_len = int(formula["policy"]["min_len"])
    candidates = []
    for ctx in repair.iter_literal_contexts(formula):
        text = ctx["text"]
        for start in range(len(text)):
            available = ctx["emitted_before_op"] + text[:start]
            max_len = len(text) - start
            for length in range(min_len, max_len + 1):
                chunk = text[start : start + length]
                source_digit_pos = available.find(chunk)
                if source_digit_pos < 0:
                    continue
                candidate = {
                    "book": ctx["book"],
                    "op_index": ctx["op_index"],
                    "book_pos": ctx["book_pos"],
                    "literal_offset": start,
                    "source_digit_pos": source_digit_pos,
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
                        "single_delta_vs_current_bits": score["total_bits"] - current_bits,
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
        group = sorted(group, key=lambda row: row["literal_offset"])
        ops = out["book_recipes"][book]["ops"]
        original = ops[op_index]
        text = original["text"]
        replacement = []
        cursor = 0
        for row in group:
            start = row["literal_offset"]
            end = start + row["length"]
            if start < cursor:
                raise ValueError("overlapping repairs")
            if start > cursor:
                replacement.append({"type": "literal", "text": text[cursor:start], "length": start - cursor})
            replacement.append(
                {
                    "type": "copy",
                    "source_digit_pos": row["source_digit_pos"],
                    "length": row["length"],
                    "target_start": row["book_pos"] + start,
                }
            )
            cursor = end
        if cursor < len(text):
            replacement.append({"type": "literal", "text": text[cursor:], "length": len(text) - cursor})
        ops[op_index : op_index + 1] = replacement
    return out


def main() -> None:
    repair = load_repair_module()
    formula = repair.load_json(FORMULA)
    books = {str(key): value for key, value in repair.load_json(BOOKS_DIGITS).items()}

    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = repair.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"]["errors"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates = collect_single_repairs(repair, formula, books, current_bits)
    best_pair = None
    compatible_pairs = 0
    overlapping_pairs = 0
    for left, right in itertools.combinations(candidates, 2):
        if not repairs_compatible(left, right):
            overlapping_pairs += 1
            continue
        compatible_pairs += 1
        score = repair.score_formula(apply_repair_pair(formula, (left, right)), books)
        if score["validation"]["errors"]:
            raise RuntimeError(score["validation"]["errors"])
        row = {
            "total_bits": score["total_bits"],
            "delta_vs_current_bits": score["total_bits"] - current_bits,
            "repairs": [left, right],
        }
        if best_pair is None or row["total_bits"] < best_pair["total_bits"]:
            best_pair = row

    best_single = min(candidates, key=lambda row: row["single_total_bits"]) if candidates else None
    promoted = best_pair is not None and best_pair["total_bits"] < current_bits
    classification = (
        "post_forced_repair_pair_improvement"
        if promoted
        else "post_forced_repair_pair_not_promoted"
    )

    result = {
        "schema": "post_forced_repair_pair_search.v1",
        "test": "49_post_forced_repair_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score": current_score,
        "single_candidates": len(candidates),
        "compatible_pairs_tested": compatible_pairs,
        "overlapping_pairs_skipped": overlapping_pairs,
        "total_pairs_considered": compatible_pairs + overlapping_pairs,
        "best_single_repair": best_single,
        "best_pair_repair": best_pair,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Forced-Repair Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether two compatible literal-to-copy repairs become",
        "cheaper together after the forced-length local repair. The full active",
        "cost model is used: adaptive literal payload, forced literal lengths,",
        "digit-only absolute copy addresses, copy length coding, and the",
        "book-start Markov item-type stream with deterministic type rules.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Single repair candidates | `{len(candidates)}` |",
        f"| Compatible pairs tested | `{compatible_pairs}` |",
        f"| Overlapping pairs skipped | `{overlapping_pairs}` |",
    ]
    if best_single is not None:
        lines.append(f"| Best single delta | `{best_single['single_delta_vs_current_bits']:.1f}` |")
    if best_pair is not None:
        lines.extend(
            [
                f"| Best pair total bits | `{best_pair['total_bits']:.1f}` |",
                f"| Best pair delta vs current | `{best_pair['delta_vs_current_bits']:.1f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Pair",
            "",
            "| Book | Literal offset | Chunk | Source digit pos | Length | Single delta |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in (best_pair or {"repairs": []})["repairs"]:
        lines.append(
            f"| `{row['book']}` | `{row['literal_offset']}` | `{row['chunk']}` | "
            f"`{row['source_digit_pos']}` | `{row['length']}` | "
            f"`{row['single_delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A pair is promoted only if exact rescoring beats the active",
            "forced-length repaired formula. If the best pair remains worse, the",
            "local literal-to-copy frontier is closed under compatible repair",
            "pairs for this cost model.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("49_post_forced_repair_pair_search", result, lines)


if __name__ == "__main__":
    main()
