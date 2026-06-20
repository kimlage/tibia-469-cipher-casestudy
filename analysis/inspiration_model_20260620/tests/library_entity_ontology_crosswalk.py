from __future__ import annotations

from _common import load_json, verdict_line, write_result


def main() -> None:
    formula = load_json("analysis/generator_search_20260618/tape_based_formula_469.json")
    external = load_json("analysis/post_review_20260619/external_numeric_string_classifier_results.json")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "library_entity_ontology_crosswalk",
        "classification": "weak_clue",
        "translation_delta": "NONE",
        "metric": "70-book object inventory plus Secret Library anchor vs tape/module assembly",
        "book_count": formula["validation"]["book_count"],
        "books_roundtrip_ok": formula["validation"]["books_roundtrip_ok"],
        "secret_library_classification": next(row["classification"] for row in external["rows"] if row["name"] == "secret_library_74032_45331"),
        "stop_rule": "Book-as-entity remains ontology unless it predicts new module/literal structure.",
    }
    lines = [
        "# Library Entity Ontology Crosswalk",
        "",
        verdict_line(result),
        "",
        f"The 70-book artifact round-trips mechanically ({result['books_roundtrip_ok']}/{result['book_count']}).",
        f"Secret Library remains `{result['secret_library_classification']}`.",
        "",
        "The book-as-object model is a useful framing for source classification, not",
        "a semantic translation route.",
    ]
    write_result("library_entity_ontology_crosswalk", result, lines)


if __name__ == "__main__":
    main()
