from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
FORMULA = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def longest_component_match(text: str, components: list[dict], min_len: int = 8) -> int:
    best = 0
    n = len(text)
    for i in range(n):
        for j in range(i + min_len, n + 1):
            piece = text[i:j]
            if any(piece in comp["text"] for comp in components):
                best = max(best, len(piece))
    return best


def greedy_cover(text: str, components: list[dict], min_len: int = 8) -> int:
    covered = [False] * len(text)
    for i in range(len(text)):
        best_j = None
        for j in range(len(text), i + min_len - 1, -1):
            piece = text[i:j]
            if any(piece in comp["text"] for comp in components):
                best_j = j
                break
        if best_j is not None:
            for k in range(i, best_j):
                covered[k] = True
    return sum(covered)


def main() -> None:
    data = json.loads(FORMULA.read_text(encoding="utf-8"))
    components = data["tape_components"]
    literals = []
    for book, recipe in data["book_recipes"].items():
        for idx, item in enumerate(recipe):
            if item["type"] == "literal":
                literals.append(
                    {
                        "book": book,
                        "recipe_index": idx,
                        "text": item["text"],
                        "length": item["length"],
                        "sha256": item["sha256"],
                    }
                )
    total_literal_digits = sum(item["length"] for item in literals)
    rows = []
    for item in literals:
        full_matches = [comp["id"] for comp in components if item["text"] in comp["text"]]
        longest = longest_component_match(item["text"], components)
        covered = greedy_cover(item["text"], components)
        rows.append(
            {
                "book": item["book"],
                "recipe_index": item["recipe_index"],
                "length": item["length"],
                "full_component_matches": full_matches,
                "longest_component_substring": longest,
                "greedy_min8_covered_digits": covered,
            }
        )
    full_absorbable = [row for row in rows if row["full_component_matches"]]
    covered_digits = sum(row["greedy_min8_covered_digits"] for row in rows)
    long_rows = sorted(rows, key=lambda r: (r["greedy_min8_covered_digits"], r["longest_component_substring"]), reverse=True)[:20]
    # Addressing each absorbed fragment costs at least a component id plus start/end;
    # require a conservative 24-digit gain before promotion.
    promotable_digits = sum(row["length"] for row in full_absorbable if row["length"] >= 24)
    classification = "literal_absorption_not_promoted" if promotable_digits == 0 else "candidate_literal_absorption_requires_mdl"
    result = {
        "schema": "literal_absorption_search.v1",
        "test": "04_literal_absorption_search",
        "classification": classification,
        "translation_delta": "NONE",
        "literal_items": len(literals),
        "literal_digits": total_literal_digits,
        "full_absorbable_items": len(full_absorbable),
        "full_absorbable_digits": sum(row["length"] for row in full_absorbable),
        "promotable_full_absorbable_digits_rough": promotable_digits,
        "greedy_min8_covered_digits": covered_digits,
        "top_partial_matches": long_rows,
    }
    lines = [
        "# Literal Absorption Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This pass asks whether remaining literal recipe digits in the current tape",
        "formula can be absorbed by existing tape components. It is a rough screen",
        "for generation-method improvement, not a semantic test.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Literal items | `{len(literals)}` |",
        f"| Literal digits | `{total_literal_digits}` |",
        f"| Fully absorbable items | `{len(full_absorbable)}` |",
        f"| Fully absorbable digits | `{sum(row['length'] for row in full_absorbable)}` |",
        f"| Rough-promotable fully absorbable digits | `{promotable_digits}` |",
        f"| Greedy min-8 partial covered digits | `{covered_digits}` |",
        "",
        "## Conclusion",
        "",
        "Remaining literals do not currently justify a new absorption layer under",
        "the conservative rough screen. Partial overlaps are diagnostic only unless",
        "a lower-cost addressing rule is found.",
    ]
    write_result("04_literal_absorption_search", result, lines)


if __name__ == "__main__":
    main()
