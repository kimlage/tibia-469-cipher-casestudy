from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    formula = load_json("analysis/generator_search_20260618/tape_based_formula_469.json")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "poi_throne_order_motif_test",
        "classification": "watchlist_only",
        "translation_delta": "NONE",
        "metric": "7/14 ritual-order motif vs current 14-symbol and module/tape order evidence",
        "symbol_count": len(formula["symbol_to_codes"]),
        "module_slice_count": formula["validation"]["module_slice_count"],
        "stop_rule": "Accept only if a fixed PoI-derived order predicts symbol/module order better than controls.",
    }
    lines = [
        "# PoI Throne Order Motif Test",
        "",
        verdict_line(result),
        "",
        f"The current substrate has {result['symbol_count']} symbols and",
        f"{result['module_slice_count']} module slices. A 7/14 ritual analogy is",
        "not yet a predictive order model.",
    ]
    write_result("poi_throne_order_motif_test", result, lines)


if __name__ == "__main__":
    main()
