from __future__ import annotations

from _common import HERE, verdict_line, write_result


def main() -> None:
    ontology = HERE / "quest_mechanism_ontology.yaml"
    corpus = HERE / "knightmare_design_corpus.yaml"
    ontology_text = ontology.read_text(encoding="utf-8")
    corpus_text = corpus.read_text(encoding="utf-8")
    result = {
        "schema": "inspiration_test_result.v1",
        "test": "02_extract_quest_mechanisms",
        "classification": "accepted_mechanical",
        "translation_delta": "NONE",
        "mechanism_count": ontology_text.count("\n  ") - ontology_text.count("\n    "),
        "corpus_entries": corpus_text.count("\n  ") - corpus_text.count("\n    "),
        "metric": "quest mechanisms extracted as ontology/comparandum entries",
        "stop_rule": "Quest mechanisms are comparanda unless they predict row0, module, render, or source class under controls.",
    }
    lines = [
        "# Extract Quest Mechanisms",
        "",
        verdict_line(result),
        "",
        "Quest mechanisms were extracted into ontology/corpus files and remain",
        "analysis-only comparanda.",
    ]
    write_result("02_extract_quest_mechanisms", result, lines)


if __name__ == "__main__":
    main()
