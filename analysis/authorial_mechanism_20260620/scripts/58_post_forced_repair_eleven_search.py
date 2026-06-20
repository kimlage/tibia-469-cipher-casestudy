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
    best_eleven = None
    compatible_elevens = 0
    incompatible_elevens = 0
    for repairs in itertools.combinations(candidates, 11):
        if not repairs_mutually_compatible(pair_module, repairs):
            incompatible_elevens += 1
            continue
        compatible_elevens += 1
        score = repair.score_formula(pair_module.apply_repair_pair(formula, repairs), books)
        if score["validation"]["errors"]:
            raise RuntimeError(score["validation"]["errors"])
        row = {
            "total_bits": score["total_bits"],
            "delta_vs_current_bits": score["total_bits"] - current_bits,
            "repairs": list(repairs),
        }
        if best_eleven is None or row["total_bits"] < best_eleven["total_bits"]:
            best_eleven = row

    best_single = min(candidates, key=lambda row: row["single_total_bits"]) if candidates else None
    promoted = best_eleven is not None and best_eleven["total_bits"] < current_bits
    classification = (
        "post_forced_repair_eleven_improvement"
        if promoted
        else "post_forced_repair_eleven_not_promoted"
    )

    result = {
        "schema": "post_forced_repair_eleven_search.v1",
        "test": "58_post_forced_repair_eleven_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score": current_score,
        "single_candidates": len(candidates),
        "compatible_elevens_tested": compatible_elevens,
        "incompatible_elevens_skipped": incompatible_elevens,
        "total_elevens_considered": compatible_elevens + incompatible_elevens,
        "best_single_repair": best_single,
        "best_eleven_repair": best_eleven,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Forced-Repair Eleven-Repair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether eleven compatible literal-to-copy repairs become",
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
        f"| Compatible eleven-repair sets tested | `{compatible_elevens}` |",
        f"| Incompatible eleven-repair sets skipped | `{incompatible_elevens}` |",
    ]
    if best_single is not None:
        lines.append(f"| Best single delta | `{best_single['single_delta_vs_current_bits']:.1f}` |")
    if best_eleven is not None:
        lines.extend(
            [
                f"| Best eleven-repair total bits | `{best_eleven['total_bits']:.1f}` |",
                f"| Best eleven-repair delta vs current | `{best_eleven['delta_vs_current_bits']:.1f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Eleven-Repair Set",
            "",
            "| Book | Op | Book pos | Literal offset | Chunk | Source digit pos | Length | Single delta |",
            "|---:|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    for row in (best_eleven or {"repairs": []})["repairs"]:
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
            "An eleven-repair set is promoted only if exact rescoring beats the active",
            "forced-length repaired formula. If the best set remains worse, the",
            "local literal-to-copy frontier is closed under compatible eleven-repair",
            "sets for this cost model.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("58_post_forced_repair_eleven_search", result, lines)


if __name__ == "__main__":
    main()
