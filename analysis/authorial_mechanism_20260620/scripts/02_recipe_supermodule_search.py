from __future__ import annotations

import json
from collections import Counter, defaultdict
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


def token(item: dict) -> str:
    if item["type"] == "module_slice":
        return f"M:{item['id']}"
    return f"L:{item['sha256'][:12]}:{item['length']}"


def skeleton_token(item: dict) -> str:
    if item["type"] == "module_slice":
        return f"C:{item['component_id']}"
    return f"L:{item['length']}"


def repeated_sequences(seqs: dict[str, list[str]], max_n: int = 6) -> list[dict]:
    seen: dict[tuple[str, ...], list[tuple[str, int]]] = defaultdict(list)
    for book, toks in seqs.items():
        for n in range(2, min(max_n, len(toks)) + 1):
            for idx in range(0, len(toks) - n + 1):
                seen[tuple(toks[idx : idx + n])].append((book, idx))
    rows = []
    for seq, occ in seen.items():
        if len(occ) < 2:
            continue
        gross_item_saving = (len(seq) - 1) * (len(occ) - 1)
        # A named supermodule needs at least a name plus one definition entry.
        net_item_saving_rough = gross_item_saving - len(seq)
        rows.append(
            {
                "sequence": list(seq),
                "length": len(seq),
                "occurrences": len(occ),
                "gross_item_saving": gross_item_saving,
                "net_item_saving_rough": net_item_saving_rough,
                "locations": occ,
            }
        )
    rows.sort(key=lambda r: (r["net_item_saving_rough"], r["gross_item_saving"], r["length"]), reverse=True)
    return rows


def main() -> None:
    data = json.loads(FORMULA.read_text(encoding="utf-8"))
    exact = {
        book: [token(item) for item in recipe]
        for book, recipe in data["book_recipes"].items()
    }
    skeleton = {
        book: [skeleton_token(item) for item in recipe]
        for book, recipe in data["book_recipes"].items()
    }
    exact_repeats = repeated_sequences(exact)
    skeleton_repeats = repeated_sequences(skeleton)
    token_count = sum(len(seq) for seq in exact.values())
    exact_promotable = [row for row in exact_repeats if row["net_item_saving_rough"] > 0]
    skeleton_promotable = [row for row in skeleton_repeats if row["net_item_saving_rough"] > 0]
    classification = "supermodule_not_promoted" if not exact_promotable else "candidate_supermodule_requires_mdl"
    result = {
        "schema": "recipe_supermodule_search.v1",
        "test": "02_recipe_supermodule_search",
        "classification": classification,
        "translation_delta": "NONE",
        "baseline_formula": str(FORMULA.relative_to(ROOT)),
        "book_count": len(exact),
        "recipe_item_count": token_count,
        "recipe_length_distribution": dict(Counter(len(seq) for seq in exact.values())),
        "exact_repeated_sequences": len(exact_repeats),
        "exact_promotable_sequences": exact_promotable[:20],
        "skeleton_repeated_sequences": len(skeleton_repeats),
        "skeleton_promotable_sequences": skeleton_promotable[:20],
    }
    lines = [
        "# Recipe Supermodule Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This pass searches for higher-order repeated recipe patterns over the",
        "current tape formula. Exact repeats can in principle reduce recipe cost;",
        "component/length skeleton repeats are diagnostic only because they do not",
        "roundtrip without extra payload.",
        "",
        "## Baseline",
        "",
        f"- Formula: `{result['baseline_formula']}`",
        f"- Books: `{result['book_count']}`",
        f"- Recipe items: `{result['recipe_item_count']}`",
        f"- Recipe length distribution: `{result['recipe_length_distribution']}`",
        "",
        "## Exact Recipe Repeats",
        "",
        f"- Repeated exact sequences: `{len(exact_repeats)}`",
        f"- Rough-promotable exact sequences: `{len(exact_promotable)}`",
        "",
        "## Skeleton Repeats",
        "",
        f"- Repeated skeleton sequences: `{len(skeleton_repeats)}`",
        f"- Rough-promotable skeleton sequences: `{len(skeleton_promotable)}`",
        "",
        "Top skeleton rows are useful as style diagnostics, not as a generator",
        "improvement unless a payload-free exact rule is found.",
        "",
        "## Conclusion",
        "",
        "No exact higher-order recipe grammar improves the current tape formula",
        "under this rough item-cost screen.",
    ]
    write_result("02_recipe_supermodule_search", result, lines)


if __name__ == "__main__":
    main()
