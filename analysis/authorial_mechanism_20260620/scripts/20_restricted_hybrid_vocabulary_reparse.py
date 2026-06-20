from __future__ import annotations

import bisect
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

SEP = "#"
LOG2_10 = math.log2(10)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def literal_run_bits(length: int) -> float:
    return 1 + gamma_bits(length + 1) + length * LOG2_10


def copy_bits(emitted_len: int, length: int, min_len: int, source_type_bits: int = 0) -> float:
    return 1 + source_type_bits + math.log2(max(2, emitted_len)) + gamma_bits(length - min_len + 1)


def macro_ref_bits(motif_count: int, source_type_bits: int = 0) -> float:
    return 1 + source_type_bits + math.log2(max(2, motif_count))


def dictionary_bits(motifs: list[str]) -> float:
    if not motifs:
        return 0.0
    return gamma_bits(len(motifs) + 1) + sum(
        gamma_bits(len(motif) + 1) + len(motif) * LOG2_10
        for motif in motifs
    )


def add_index_entries(available: str, index: dict[str, list[int]], min_len: int, previous_len: int) -> None:
    for end in range(max(min_len, previous_len + 1), len(available) + 1):
        start = end - min_len
        key = available[start:end]
        if SEP not in key:
            index.setdefault(key, []).append(start)


def match_candidates(
    target: str,
    pos: int,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
) -> list[tuple[int, int]]:
    if pos + min_len > len(target):
        return []
    key = target[pos : pos + min_len]
    candidates = index.get(key, [])
    if not candidates:
        return []

    by_length: dict[int, int] = {}
    max_len = len(target) - pos
    for source_pos in candidates:
        length = min_len
        while length < max_len:
            source_next = source_pos + length
            if source_next >= len(available) or available[source_next] == SEP:
                break
            if available[source_next] != target[pos + length]:
                break
            length += 1
        for candidate_len in range(min_len, length + 1):
            previous = by_length.get(candidate_len)
            if previous is None or source_pos < previous:
                by_length[candidate_len] = source_pos
    return [(source_pos, length) for length, source_pos in sorted(by_length.items())]


def candidate_motifs(
    books: dict[str, str],
    order: list[str],
    min_len: int,
    max_len: int,
    max_keep: int,
) -> tuple[list[str], list[str], list[dict]]:
    counts: Counter[str] = Counter()
    for book in order:
        text = books[book]
        for length in range(min_len, max_len + 1):
            for start in range(0, len(text) - length + 1):
                counts[text[start : start + length]] += 1

    scored = []
    for motif, count in counts.items():
        if count < 2:
            continue
        table_cost = gamma_bits(len(motif) + 1) + len(motif) * LOG2_10
        gross_repeat_value = (count - 1) * len(motif) * LOG2_10
        scored.append(
            {
                "motif": motif,
                "count": count,
                "length": len(motif),
                "score": gross_repeat_value - table_cost,
            }
        )
    scored.sort(key=lambda row: (row["score"], row["count"], row["length"], row["motif"]), reverse=True)

    raw_top = [row["motif"] for row in scored[:max_keep]]
    filtered: list[str] = []
    for row in scored:
        motif = row["motif"]
        if any(motif in selected or selected in motif for selected in filtered):
            continue
        filtered.append(motif)
        if len(filtered) >= max_keep:
            break
    return raw_top, filtered, scored[:12]


def build_macro_lookup(motifs: list[str]) -> dict[str, list[tuple[int, str]]]:
    lookup: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for motif_id, motif in enumerate(motifs):
        lookup[motif[0]].append((motif_id, motif))
    for rows in lookup.values():
        rows.sort(key=lambda row: (-len(row[1]), row[0]))
    return lookup


def precompute_book_choices(
    text: str,
    available: str,
    index: dict[str, list[int]],
    min_len: int,
    macro_lookup: dict[str, list[tuple[int, str]]],
) -> tuple[list[list[tuple[int, int]]], list[list[tuple[int, int]]], list[int]]:
    local_available = available
    local_index = {key: positions[:] for key, positions in index.items()}
    copy_matches: list[list[tuple[int, int]]] = []
    macro_matches: list[list[tuple[int, int]]] = []
    break_positions = set()

    for pos in range(len(text)):
        copies = match_candidates(text, pos, local_available, local_index, min_len)
        macros = [
            (motif_id, len(motif))
            for motif_id, motif in macro_lookup.get(text[pos], [])
            if text.startswith(motif, pos)
        ]
        copy_matches.append(copies)
        macro_matches.append(macros)
        if copies or macros:
            break_positions.add(pos)
        previous_len = len(local_available)
        local_available += text[pos]
        add_index_entries(local_available, local_index, min_len, previous_len)

    endpoints = sorted(break_positions | {len(text)})
    return copy_matches, macro_matches, endpoints


def encode_books_hybrid(
    books: dict[str, str],
    order: list[str],
    min_len: int,
    motifs: list[str],
    conservative_source_type_bits: bool,
) -> dict:
    macro_lookup = build_macro_lookup(motifs)
    source_type_bits = 1 if conservative_source_type_bits and motifs else 0
    total_bits = gamma_bits(len(order) + 1)
    total_bits += sum(gamma_bits(len(books[book]) + 1) for book in order)
    table_bits = dictionary_bits(motifs)
    total_bits += table_bits

    available = ""
    index: dict[str, list[int]] = {}
    emitted = ""
    rendered = {}
    errors = []
    stats = Counter()
    recipes = {}

    for book in order:
        text = books[book]
        copy_matches, macro_matches, endpoints = precompute_book_choices(
            text,
            available,
            index,
            min_len,
            macro_lookup,
        )
        n = len(text)
        dp = [0.0] * (n + 1)
        choice: list[tuple | None] = [None] * (n + 1)

        for pos in range(n - 1, -1, -1):
            best_cost = float("inf")
            best_choice: tuple | None = None

            start_idx = bisect.bisect_right(endpoints, pos)
            for end in endpoints[start_idx:]:
                length = end - pos
                cost = literal_run_bits(length) + dp[end]
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("literal", length)

            emitted_len = len(available) + pos
            for source_pos, length in copy_matches[pos]:
                cost = copy_bits(emitted_len, length, min_len, source_type_bits) + dp[pos + length]
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("copy", source_pos, length)

            for motif_id, length in macro_matches[pos]:
                cost = macro_ref_bits(len(motifs), source_type_bits) + dp[pos + length]
                if cost < best_cost:
                    best_cost = cost
                    best_choice = ("macro", motif_id, length)

            if best_choice is None:
                raise RuntimeError(f"no parse choice at {book}:{pos}")
            dp[pos] = best_cost
            choice[pos] = best_choice

        total_bits += dp[0]
        pos = 0
        parts = []
        ops = []
        while pos < n:
            selected = choice[pos]
            assert selected is not None
            if selected[0] == "literal":
                length = int(selected[1])
                chunk = text[pos : pos + length]
                ops.append({"type": "literal", "length": length})
                stats["literal_runs"] += 1
                stats["literal_digits"] += length
                pos += length
            elif selected[0] == "copy":
                _, source_pos, length = selected
                chunk = emitted[source_pos : source_pos + length]
                ops.append({"type": "copy", "length": length, "source_pos": source_pos})
                stats["copy_items"] += 1
                stats["copied_digits"] += length
                pos += length
            elif selected[0] == "macro":
                _, motif_id, length = selected
                chunk = motifs[motif_id]
                ops.append({"type": "macro", "length": length, "motif_id": motif_id})
                stats["macro_items"] += 1
                stats["macro_digits"] += length
                stats[f"macro_{motif_id}_uses"] += 1
                pos += length
            else:
                raise ValueError(selected)
            parts.append(chunk)
            emitted += chunk

        rendered[book] = "".join(parts)
        if rendered[book] != text:
            errors.append(book)
        recipes[book] = {"length": len(text), "ops": ops}

        previous_len = len(available)
        available += text
        add_index_entries(available, index, min_len, previous_len)
        previous_len = len(available)
        available += SEP
        emitted += SEP
        add_index_entries(available, index, min_len, previous_len)

    return {
        "total_bits": total_bits,
        "table_bits": table_bits,
        "stats": dict(stats),
        "errors": errors,
        "books_roundtrip_ok": len(order) - len(errors),
        "recipes": recipes,
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]

    raw_motifs, filtered_motifs, top_candidates = candidate_motifs(
        books,
        order,
        min_len=min_len,
        max_len=32,
        max_keep=128,
    )
    motif_sets = {
        "raw_top": raw_motifs,
        "redundancy_filtered_top": filtered_motifs,
    }
    tested_ks = [0, 4, 8, 16, 32, 64]

    rows = []
    for family, motifs in motif_sets.items():
        for motif_count in tested_ks:
            selected_motifs = motifs[:motif_count]
            for conservative in (False, True):
                encoded = encode_books_hybrid(
                    books,
                    order,
                    min_len,
                    selected_motifs,
                    conservative_source_type_bits=conservative,
                )
                model = (
                    f"{family}_k{motif_count}_"
                    + ("decodable_source_type" if conservative else "optimistic_no_source_type")
                )
                rows.append(
                    {
                        "model": model,
                        "motif_family": family,
                        "motif_count": motif_count,
                        "decodable_reference_ledger": bool(conservative or motif_count == 0),
                        "table_bits": encoded["table_bits"],
                        "total_bits": encoded["total_bits"],
                        "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                        "books_roundtrip_ok": encoded["books_roundtrip_ok"],
                        "errors": encoded["errors"],
                        "stats": encoded["stats"],
                        "motifs": selected_motifs[:12],
                    }
                )
    rows.sort(key=lambda row: row["total_bits"])

    best_decodable = next(row for row in rows if row["decodable_reference_ledger"])
    best_any = rows[0]
    if (
        best_decodable["motif_count"] > 0
        and best_decodable["total_bits"] < current_bits
        and best_decodable["books_roundtrip_ok"] == len(order)
    ):
        classification = "restricted_hybrid_vocabulary_candidate"
    elif (
        best_any["motif_count"] > 0
        and best_any["total_bits"] < current_bits
        and best_any["books_roundtrip_ok"] == len(order)
    ):
        classification = "restricted_hybrid_vocabulary_optimistic_only_not_promoted"
    else:
        classification = "restricted_hybrid_vocabulary_not_promoted"

    result = {
        "schema": "restricted_hybrid_vocabulary_reparse.v1",
        "test": "20_restricted_hybrid_vocabulary_reparse",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "candidate_generation": {
            "min_len": min_len,
            "max_len": 32,
            "families": list(motif_sets),
            "tested_ks": tested_ks,
            "top_scored_candidates": top_candidates,
        },
        "models": rows,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Restricted Hybrid Vocabulary Reparse",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests a controlled reparse rather than a cost-only recoding of",
        "the existing DP LZ parse. A small declared dictionary of repeated digit",
        "motifs is added to the existing literal-run plus prior-copy vocabulary.",
        "The dictionary is charged as raw digit entries, and each model must",
        "roundtrip all 70 books.",
        "",
        "## Best Models",
        "",
        "| Model | Motifs | Table bits | Total bits | Delta vs current | Roundtrip | Macro items | Decodable |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:12]:
        stats = row["stats"]
        lines.append(
            f"| `{row['model']}` | `{row['motif_count']}` | `{row['table_bits']:.1f}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` | "
            f"`{row['books_roundtrip_ok']}/70` | `{stats.get('macro_items', 0)}` | "
            f"`{row['decodable_reference_ledger']}` |"
        )

    lines.extend(
        [
            "",
            "## Top Motif Candidates",
            "",
            "| Motif | Len | Count | Score |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in top_candidates[:8]:
        motif = row["motif"]
        display = motif if len(motif) <= 24 else motif[:24] + "..."
        lines.append(
            f"| `{display}` | `{row['length']}` | `{row['count']}` | `{row['score']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The restricted hybrid vocabulary does not improve the current formula.",
            "The best dictionary-using optimistic reparse is still above the current",
            "then-current gamma-length DP LZ baseline after the raw motif table is",
            "charged, and the decodable source-type variants are further away.",
            "That result was later superseded by the Rice-length reparse.",
            "",
            "## Boundary",
            "",
            "This is a mechanical generation audit only. Motifs are digit strings,",
            "not words or plaintext, and no semantic claim is introduced.",
        ]
    )
    write_result("20_restricted_hybrid_vocabulary_reparse", result, lines)


if __name__ == "__main__":
    main()
