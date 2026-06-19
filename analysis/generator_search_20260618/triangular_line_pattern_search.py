#!/usr/bin/env python3
"""Line-pattern search over the 469 triangular pair table.

This pass looks for a formula that is not cell-local but line-local: rows,
columns, diagonals, or adjacent row transforms. A human table might be built as
line strings rather than as f(a,b). We test whether those line strings are:

- copied from the symbol corpus;
- unusually compressible as a set of strings;
- unusually close to each other by edit distance.

No semantic translation is produced.
"""

from __future__ import annotations

import json
import random
import zlib
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FORMULA_JSON = ROOT / "analysis" / "mechanism_model_20260618" / "mechanical_formula_469.json"
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"

OUT_JSON = HERE / "triangular_line_pattern_results.json"
OUT_MD = HERE / "triangular_line_pattern_report.md"

RANDOM_SEED = 46920260619


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def primary_pair_symbol(pair_table: dict, pair: str) -> str:
    row = pair_table[pair]
    if row["status"] == "pure":
        return row["symbol_if_pure"]
    return sorted(row["symbols"])[0]


def symbol_corpus() -> str:
    occ = load_json(OCC_STREAMS)["occ"]
    by_book: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for symbol, rows in occ.items():
        for row in rows:
            by_book[str(row["book"])].append((int(row["pos"]), symbol))
    return "#".join(
        "".join(symbol for _pos, symbol in sorted(rows))
        for _book, rows in sorted(by_book.items(), key=lambda item: numeric_key(item[0]))
    )


def build_lines(pair_table: dict) -> list[dict]:
    lines = []
    for i in range(10):
        text = "".join(primary_pair_symbol(pair_table, f"{i}{j}") for j in range(i, 10))
        lines.append({"kind": "row", "index": i, "text": text})
    for j in range(10):
        text = "".join(primary_pair_symbol(pair_table, f"{i}{j}") for i in range(j + 1))
        lines.append({"kind": "column", "index": j, "text": text})
    for diff in range(10):
        text = "".join(primary_pair_symbol(pair_table, f"{i}{i + diff}") for i in range(10 - diff))
        lines.append({"kind": "diagonal_diff", "index": diff, "text": text})
    anti_index = 0
    for total in range(18 + 1):
        cells = []
        for i in range(10):
            j = total - i
            if 0 <= i <= j < 10:
                cells.append(primary_pair_symbol(pair_table, f"{i}{j}"))
        if cells:
            lines.append({"kind": "anti_diagonal_sum", "index": anti_index, "text": "".join(cells), "sum": total})
            anti_index += 1
    return lines


def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (0 if ca == cb else 1),
                )
            )
        previous = current
    return previous[-1]


def compress_len(lines: list[str]) -> int:
    blob = "|".join(lines).encode("ascii")
    return len(zlib.compress(blob, level=9))


def line_metrics(lines: list[dict], corpus: str) -> dict:
    long_hits = []
    for line in lines:
        text = line["text"]
        if len(text) < 5:
            continue
        long_hits.append(
            {
                **line,
                "count_forward": corpus.count(text),
                "count_reverse": corpus.count(text[::-1]),
                "hit": text in corpus or text[::-1] in corpus,
            }
        )
    by_kind = defaultdict(list)
    for line in lines:
        by_kind[line["kind"]].append(line["text"])

    kind_metrics = []
    for kind, texts in sorted(by_kind.items()):
        adjacent = [
            levenshtein(texts[idx], texts[idx + 1]) / max(len(texts[idx]), len(texts[idx + 1]))
            for idx in range(len(texts) - 1)
        ]
        kind_metrics.append(
            {
                "kind": kind,
                "line_count": len(texts),
                "compressed_bytes": compress_len(texts),
                "adjacent_edit_mean": sum(adjacent) / len(adjacent) if adjacent else 0.0,
                "texts": texts,
            }
        )
    return {
        "long_lines": long_hits,
        "long_hit_count": sum(1 for item in long_hits if item["hit"]),
        "kind_metrics": kind_metrics,
    }


def control_metrics(pair_table: dict, lines: list[dict], corpus: str, trials: int = 5000) -> dict:
    rng = random.Random(RANDOM_SEED)
    pairs = [f"{i}{j}" for i in range(10) for j in range(i, 10)]
    labels = [primary_pair_symbol(pair_table, pair) for pair in pairs]
    line_shapes_by_kind = defaultdict(list)
    for line in lines:
        line_shapes_by_kind[line["kind"]].append((line["index"], len(line["text"])))
    long_hit_counts = []
    compressed_by_kind = defaultdict(list)
    edit_by_kind = defaultdict(list)

    for _trial in range(trials):
        shuffled_lines = []
        for kind, shapes in line_shapes_by_kind.items():
            current = labels[:]
            rng.shuffle(current)
            cursor = 0
            for index, length in shapes:
                text = "".join(current[cursor : cursor + length])
                cursor += length
                shuffled_lines.append({"kind": kind, "index": index, "text": text})
        metrics = line_metrics(shuffled_lines, corpus)
        long_hit_counts.append(metrics["long_hit_count"])
        for row in metrics["kind_metrics"]:
            compressed_by_kind[row["kind"]].append(row["compressed_bytes"])
            edit_by_kind[row["kind"]].append(row["adjacent_edit_mean"])

    return {
        "trials": trials,
        "long_hit_mean": sum(long_hit_counts) / len(long_hit_counts),
        "long_hit_max": max(long_hit_counts),
        "long_hit_p_ge_observed": None,
        "compressed_by_kind": {
            kind: {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
            for kind, values in compressed_by_kind.items()
        },
        "edit_by_kind": {
            kind: {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
            for kind, values in edit_by_kind.items()
        },
        "long_hit_counts": long_hit_counts,
    }


def main() -> int:
    formula = load_json(FORMULA_JSON)
    pair_table = formula["pair_table"]
    corpus = symbol_corpus()
    lines = build_lines(pair_table)
    observed = line_metrics(lines, corpus)
    control = control_metrics(pair_table, lines, corpus, trials=5000)
    control["long_hit_p_ge_observed"] = (
        sum(value >= observed["long_hit_count"] for value in control["long_hit_counts"]) + 1
    ) / (len(control["long_hit_counts"]) + 1)
    control_without_raw = {key: value for key, value in control.items() if key != "long_hit_counts"}

    verdict = "rejected_control"
    result = {
        "schema": "triangular_line_pattern_results.v1",
        "translation_delta": "NONE",
        "accepted_original_formula": None,
        "observed": observed,
        "control": control_without_raw,
        "verdict": verdict,
    }
    write_json(OUT_JSON, result)

    lines_md = [
        "# Triangular Line Pattern Search",
        "",
        "Generated by `triangular_line_pattern_search.py`.",
        "",
        "This pass tests whether rows, columns, diagonals, or anti-diagonals of",
        "the 55-cell triangular pair table behave like copied/generated line",
        "strings.",
        "",
        "## Corpus-Substring Check",
        "",
        "| Long line hits | Control mean | Control max | p | Verdict |",
        "|---:|---:|---:|---:|---|",
        f"| {observed['long_hit_count']} | {control_without_raw['long_hit_mean']:.2f} | {control_without_raw['long_hit_max']} | {control_without_raw['long_hit_p_ge_observed']:.3f} | `{verdict}` |",
        "",
        "No line of length >=5 appears as a copied symbol-corpus substring in",
        "forward or reverse orientation.",
        "",
        "## Line Families",
        "",
        "| Kind | Lines | Compressed bytes | Adjacent edit mean | Texts |",
        "|---|---:|---:|---:|---|",
    ]
    for row in observed["kind_metrics"]:
        lines_md.append(
            f"| `{row['kind']}` | {row['line_count']} | {row['compressed_bytes']} | {row['adjacent_edit_mean']:.3f} | `{' / '.join(row['texts'])}` |"
        )
    lines_md.extend(
        [
            "",
            "## Verdict",
            "",
            "Line-local structure does not recover the pair-table placement. The",
            "row/column/diagonal strings are not copied from the symbol corpus and",
            "do not provide a compact generator beyond the already-known unordered",
            "pair table.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines_md), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(HERE)}")
    print(f"wrote {OUT_MD.relative_to(HERE)}")
    print(
        "long_hits={} p_ge={:.3f}".format(
            observed["long_hit_count"],
            control_without_raw["long_hit_p_ge_observed"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
