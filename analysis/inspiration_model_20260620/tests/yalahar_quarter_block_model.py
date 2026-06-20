from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    formula = load_json("analysis/generator_search_20260618/tape_based_formula_469.json")
    validation = formula["validation"]
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "yalahar_quarter_block_model",
        "classification": "watchlist_only",
        "translation_delta": "NONE",
        "metric": "whether city-quarter/block lore adds a non-duplicative target beyond tape/module components",
        "module_slice_count": validation["module_slice_count"],
        "tape_components": len(formula["tape_components"]),
        "books_roundtrip_ok": validation["books_roundtrip_ok"],
        "stop_rule": "Only reopen if quarter/block metadata predicts module order or residual spans better than existing tape formula.",
    }
    lines = [
        "# Yalahar Quarter Block Model",
        "",
        verdict_line(result),
        "",
        f"The accepted baseline already round-trips {result['books_roundtrip_ok']} books with",
        f"{result['module_slice_count']} module slices over {result['tape_components']} tape components.",
        "",
        "Yalahar-style block lore is a comparandum, not a tested improvement.",
    ]
    write_result("yalahar_quarter_block_model", result, lines)


if __name__ == "__main__":
    main()
