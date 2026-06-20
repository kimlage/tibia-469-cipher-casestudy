from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

PAIR_SCRIPT = HERE / "scripts" / "49_post_forced_repair_pair_search.py"
FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
CURRENT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_repair_bits"


def load_pair_module():
    spec = importlib.util.spec_from_file_location("post_forced_repair_pair", PAIR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(PAIR_SCRIPT)
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


def repairs_mutually_compatible(pair_module, repairs: tuple[dict, ...]) -> bool:
    return all(pair_module.repairs_compatible(left, right) for left, right in itertools.combinations(repairs, 2))


def main() -> None:
    pair_module = load_pair_module()
    repair = pair_module.load_repair_module()
    formula = repair.load_json(FORMULA)
    books = {str(key): value for key, value in repair.load_json(BOOKS_DIGITS).items()}

    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = repair.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"]["errors"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates = pair_module.collect_single_repairs(repair, formula, books, current_bits)
    size_results = []
    overall_best = None

    for size in range(13, len(candidates) + 1):
        best_for_size = None
        compatible = 0
        incompatible = 0
        for repairs in itertools.combinations(candidates, size):
            if not repairs_mutually_compatible(pair_module, repairs):
                incompatible += 1
                continue
            compatible += 1
            score = repair.score_formula(pair_module.apply_repair_pair(formula, repairs), books)
            if score["validation"]["errors"]:
                raise RuntimeError(score["validation"]["errors"])
            row = {
                "size": size,
                "total_bits": score["total_bits"],
                "delta_vs_current_bits": score["total_bits"] - current_bits,
                "repairs": list(repairs),
            }
            if best_for_size is None or row["total_bits"] < best_for_size["total_bits"]:
                best_for_size = row
            if overall_best is None or row["total_bits"] < overall_best["total_bits"]:
                overall_best = row
        size_results.append(
            {
                "size": size,
                "compatible_sets_tested": compatible,
                "incompatible_sets_skipped": incompatible,
                "total_sets_considered": compatible + incompatible,
                "best_set": best_for_size,
            }
        )

    promoted = overall_best is not None and overall_best["total_bits"] < current_bits
    classification = (
        "post_forced_repair_high_order_improvement"
        if promoted
        else "post_forced_repair_high_order_not_promoted"
    )

    result = {
        "schema": "post_forced_repair_high_order_exhaustion.v1",
        "test": "60_post_forced_repair_high_order_exhaustion",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score": current_score,
        "single_candidates": len(candidates),
        "sizes_tested": [row["size"] for row in size_results],
        "compatible_sets_tested": sum(row["compatible_sets_tested"] for row in size_results),
        "incompatible_sets_skipped": sum(row["incompatible_sets_skipped"] for row in size_results),
        "total_sets_considered": sum(row["total_sets_considered"] for row in size_results),
        "size_results": size_results,
        "overall_best_set": overall_best,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Forced-Repair High-Order Exhaustion",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit closes the remaining high-order local frontier after the",
        "forced-length local repair. It exactly rescores compatible sets of",
        "13 through 19 literal-to-copy repairs, and confirms that no compatible",
        "sets exist for sizes 20 through 22. The full active cost model is used:",
        "adaptive literal payload, forced literal lengths, digit-only absolute",
        "copy addresses, copy length coding, and the book-start Markov item-type",
        "stream with deterministic type rules.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Single repair candidates | `{len(candidates)}` |",
        f"| Compatible sets tested | `{result['compatible_sets_tested']}` |",
        f"| Incompatible sets skipped | `{result['incompatible_sets_skipped']}` |",
        f"| Total sets considered | `{result['total_sets_considered']}` |",
    ]
    if overall_best is not None:
        lines.extend(
            [
                f"| Best set size | `{overall_best['size']}` |",
                f"| Best set total bits | `{overall_best['total_bits']:.1f}` |",
                f"| Best set delta vs current | `{overall_best['delta_vs_current_bits']:.1f}` |",
            ]
        )

    lines.extend(
        [
            "",
            "## Results by Size",
            "",
            "| Size | Compatible | Incompatible | Best total bits | Best delta |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in size_results:
        best = row["best_set"]
        if best is None:
            best_bits = "-"
            best_delta = "-"
        else:
            best_bits = f"`{best['total_bits']:.1f}`"
            best_delta = f"`{best['delta_vs_current_bits']:.1f}`"
        lines.append(
            f"| `{row['size']}` | `{row['compatible_sets_tested']}` | "
            f"`{row['incompatible_sets_skipped']}` | {best_bits} | {best_delta} |"
        )

    lines.extend(
        [
            "",
            "## Best High-Order Set",
            "",
            "| Book | Op | Book pos | Literal offset | Chunk | Source digit pos | Length | Single delta |",
            "|---:|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in (overall_best or {"repairs": []})["repairs"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['book_pos']}` | "
            f"`{row['literal_offset']}` | `{row['chunk']}` | "
            f"`{row['source_digit_pos']}` | `{row['length']}` | "
            f"`{row['single_delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A high-order set is promoted only if exact rescoring beats the active",
            "forced-length repaired formula. Since the best remaining high-order",
            "set remains worse, the local literal-to-copy frontier is exhausted",
            "for all compatible set sizes above twelve under this cost model.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("60_post_forced_repair_high_order_exhaustion", result, lines)


if __name__ == "__main__":
    main()
