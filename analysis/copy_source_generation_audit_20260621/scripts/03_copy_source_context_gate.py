from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_copy_source_ledger.json"
POLICY_GATE = TEST_RESULTS / "02_copy_source_policy_gate.json"
OUT_STEM = "03_copy_source_context_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Row = dict[str, Any]
ContextFn = Callable[[Row], str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def bucket(value: int) -> str:
    if value <= 1:
        return "le1"
    if value <= 3:
        return "le3"
    if value <= 5:
        return "le5"
    if value <= 8:
        return "le8"
    if value <= 13:
        return "le13"
    if value <= 21:
        return "le21"
    if value <= 34:
        return "le34"
    return "gt34"


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda r: "global",
        "book_mod10": lambda r: f"bookmod10={int(r['book']) % 10}",
        "op_index": lambda r: f"op={r['op_index']}",
        "target_phase_10": lambda r: f"phase10={int(r['target_start']) % 10}",
        "target_phase_16": lambda r: f"phase16={int(r['target_start']) % 16}",
        "length": lambda r: f"len={r['length']}",
        "length_bucket": lambda r: f"lenb={bucket(int(r['length']))}",
        "matching_count_bucket": lambda r: (
            f"matchb={bucket(int(r['matching_source_count']))}"
        ),
        "op_index_x_length": lambda r: f"op={r['op_index']}|len={r['length']}",
        "book_mod10_x_length": lambda r: (
            f"bookmod10={int(r['book']) % 10}|len={r['length']}"
        ),
        "phase10_x_length": lambda r: (
            f"phase10={int(r['target_start']) % 10}|len={r['length']}"
        ),
    }


def majority_source(rows: list[Row]) -> int:
    counts = Counter(int(row["canonical_source"]) for row in rows)
    return min(counts, key=lambda source: (-counts[source], source))


def train_model(rows: list[Row], name: str, fn: ContextFn) -> dict[str, Any]:
    grouped: dict[str, list[Row]] = defaultdict(list)
    for row in rows:
        grouped[fn(row)].append(row)
    return {
        "context_name": name,
        "fallback_source": majority_source(rows),
        "mapping": {context: majority_source(values) for context, values in grouped.items()},
        "context_count": len(grouped),
    }


def evaluate(rows: list[Row], model: dict[str, Any], fn: ContextFn) -> dict[str, Any]:
    scored = []
    table_source_bits = 0.0
    for source in model["mapping"].values():
        max_legal = max(int(row["legal_source_count"]) for row in rows)
        table_source_bits += math.log2(max_legal)
    for row in rows:
        source = int(model["mapping"].get(fn(row), model["fallback_source"]))
        legal = 0 <= source < int(row["legal_source_count"])
        source_exact = legal and source == int(row["canonical_source"])
        chunk_hit = legal and source in row["matching_sources"]
        scored.append(
            {
                "book": row["book"],
                "predicted_source": source,
                "legal": legal,
                "source_exact": source_exact,
                "chunk_hit": chunk_hit,
            }
        )
    misses = [row for row, score in zip(rows, scored) if not score["chunk_hit"]]
    correction_bits = sum(math.log2(int(row["legal_source_count"])) for row in misses)
    return {
        "context_name": model["context_name"],
        "context_count": model["context_count"],
        "copy_events": len(rows),
        "legal_predictions": sum(1 for row in scored if row["legal"]),
        "source_exact_events": sum(1 for row in scored if row["source_exact"]),
        "chunk_hit_events": sum(1 for row in scored if row["chunk_hit"]),
        "table_source_bits": table_source_bits,
        "correction_bits_for_chunk_misses": correction_bits,
        "total_bits_with_corrections": table_source_bits + correction_bits,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["chunk_hit_events"],
        row["source_exact_events"],
        -row["context_count"],
        row["context_name"],
    )


def prequential(rows: list[Row], contexts: dict[str, ContextFn]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        trained = []
        for name, fn in contexts.items():
            model = train_model(train, name, fn)
            train_score = evaluate(train, model, fn)
            trained.append((name, fn, model, train_score))
        selected_name, selected_fn, selected_model, selected_train = max(
            trained, key=lambda item: score_key(item[3])
        )
        test_score = evaluate(test, selected_model, selected_fn)
        oracle = max(
            [evaluate(test, model, fn) for _name, fn, model, _score in trained],
            key=score_key,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
                "train_chunk_hits": selected_train["chunk_hit_events"],
                "train_copy_events": selected_train["copy_events"],
                "test_chunk_hits": test_score["chunk_hit_events"],
                "test_copy_events": test_score["copy_events"],
                "test_source_exact": test_score["source_exact_events"],
                "oracle_context": oracle["context_name"],
                "oracle_test_chunk_hits": oracle["chunk_hit_events"],
                "oracle_test_source_exact": oracle["source_exact_events"],
                "selected_matches_oracle": (
                    test_score["chunk_hit_events"] == oracle["chunk_hit_events"]
                    and test_score["source_exact_events"] == oracle["source_exact_events"]
                ),
            }
        )
    return out


def make_result() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    policy_gate = load_json(POLICY_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("copy_source_policy_gate", policy_gate)
    rows = list(ledger["copy_rows"])
    contexts = context_families()
    raw_absolute_source_bits = float(ledger["summary"]["raw_absolute_source_bits"])
    scores = []
    for name, fn in contexts.items():
        model = train_model(rows, name, fn)
        scores.append(evaluate(rows, model, fn))
    scores.sort(key=score_key, reverse=True)
    best = scores[0]
    preq = prequential(rows, contexts)
    promotes = (
        best["chunk_hit_events"] == best["copy_events"]
        and best["total_bits_with_corrections"] < raw_absolute_source_bits
        and all(row["test_chunk_hits"] == row["test_copy_events"] for row in preq)
    )
    classification = (
        "copy_source_context_generator_promoted"
        if promotes
        else "copy_source_context_generator_rejected"
    )
    return {
        "schema": "copy_source_context_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_ledger": str(LEDGER.relative_to(ROOT)),
            "copy_source_policy_gate": str(POLICY_GATE.relative_to(ROOT)),
        },
        "scope": {
            "analysis_only": True,
            "exact_skeleton_granted": True,
            "literal_payload_granted": True,
            "source_table_is_source_bearing": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "copy_events": len(rows),
            "context_family_count": len(contexts),
            "best_context": best["context_name"],
            "best_context_count": best["context_count"],
            "best_chunk_hits": best["chunk_hit_events"],
            "best_source_exact": best["source_exact_events"],
            "best_total_bits_with_corrections": best["total_bits_with_corrections"],
            "best_net_vs_raw_absolute_source_bits": (
                best["total_bits_with_corrections"] - raw_absolute_source_bits
            ),
            "prequential_cells": len(preq),
            "prequential_cover_all_chunk_cells": sum(
                1 for row in preq if row["test_chunk_hits"] == row["test_copy_events"]
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_copy_source_generator": promotes,
            "interpretation": (
                "Source context tables are source-bearing selectors. They do "
                "not remove source declarations unless they generalize and beat "
                "raw source declaration after paid table and corrections."
            ),
        },
        "full_fit_scoreboard": scores,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "copy_source_status": "external_after_context_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Copy Source Context Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether simple source-bearing context tables can predict copy",
        "source after granting exact skeleton and literal payload.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_events']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best chunk hits: `{s['best_chunk_hits']}/{s['copy_events']}`.",
        f"- Best source-exact hits: `{s['best_source_exact']}/{s['copy_events']}`.",
        f"- Best net vs raw absolute source bits: `{s['best_net_vs_raw_absolute_source_bits']:.3f}` bits.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_chunk_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Context | Chunk hits | Source exact | Contexts | Net vs raw |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    raw = (
        s["best_total_bits_with_corrections"]
        - s["best_net_vs_raw_absolute_source_bits"]
    )
    for row in result["full_fit_scoreboard"]:
        net = row["total_bits_with_corrections"] - raw
        lines.append(
            f"| `{row['context_name']}` | `{row['chunk_hit_events']}/{row['copy_events']}` | "
            f"`{row['source_exact_events']}/{row['copy_events']}` | "
            f"`{row['context_count']}` | `{net:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Context | Test chunk hits | Test source exact | Oracle context |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_chunk_hits']}/{row['test_copy_events']}` | "
            f"`{row['test_source_exact']}/{row['test_copy_events']}` | "
            f"`{row['oracle_context']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes copy-source generator: `{s['promotes_copy_source_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
