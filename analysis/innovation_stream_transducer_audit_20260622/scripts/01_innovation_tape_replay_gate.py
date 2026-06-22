from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
LATENT_TRANSDUCER_AUDIT = (
    ROOT
    / "analysis"
    / "latent_transducer_generation_audit_20260622"
    / "reports"
    / "final_latent_transducer_generation_audit.md"
)

OUT_STEM = "01_innovation_tape_replay_gate"
SEED_BOOKS = list(range(10))
MIN_COPY_THRESHOLDS = [5, 8, 12, 20]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 200


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def canonical_tape_and_ops(
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[int, list[dict[str, Any]]]]:
    tape = []
    canonical = {}
    for book in range(10, 70):
        rows = []
        for op in ops_by_book[str(book)]:
            row = {
                "type": op["type"],
                "target_start": int(op["target_start"]),
                "length": int(op["length"]),
                "source": op.get("source"),
            }
            if op["type"] == "literal":
                payload = op.get("payload", "")
                tape.append(payload)
                row["payload"] = payload
            rows.append(row)
        canonical[book] = rows
    return "".join(tape), canonical


def find_target_copy_candidates(
    emitted: str,
    target: str,
    pos: int,
    min_len: int,
) -> list[tuple[int, int]]:
    if pos + min_len > len(target):
        return []
    needle = target[pos : pos + min_len]
    source = emitted.find(needle)
    rows = []
    while source != -1:
        length = min_len
        cap = min(len(target) - pos, len(emitted) - source)
        while length < cap and emitted[source + length] == target[pos + length]:
            length += 1
        rows.append((source, length))
        source = emitted.find(needle, source + 1)
    return rows


def merge_literal_ops(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for op in ops:
        if (
            op["type"] == "literal"
            and merged
            and merged[-1]["type"] == "literal"
            and merged[-1]["target_start"] + merged[-1]["length"] == op["target_start"]
        ):
            merged[-1]["length"] += op["length"]
            merged[-1]["payload"] += op["payload"]
            continue
        merged.append(dict(op))
    return merged


def target_conditioned_replay_book(
    emitted: str,
    target: str,
    tape: str,
    tape_pos: int,
    threshold: int,
) -> tuple[dict[str, Any], str, int]:
    pos = 0
    generated = []
    ops = []
    first_mismatch = None
    while pos < len(target):
        candidates = find_target_copy_candidates(emitted + "".join(generated), target, pos, threshold)
        if candidates:
            source, length = min(
                candidates,
                key=lambda item: (-item[1], item[0]),
            )
            chunk = target[pos : pos + length]
            generated.append(chunk)
            ops.append(
                {
                    "type": "copy",
                    "target_start": pos,
                    "length": length,
                    "source": source,
                }
            )
            pos += length
            continue
        if tape_pos >= len(tape):
            first_mismatch = pos
            break
        digit = tape[tape_pos]
        tape_pos += 1
        generated.append(digit)
        ops.append(
            {
                "type": "literal",
                "target_start": pos,
                "length": 1,
                "source": None,
                "payload": digit,
            }
        )
        if digit != target[pos] and first_mismatch is None:
            first_mismatch = pos
            break
        pos += 1
    text = "".join(generated)
    result = {
        "exact_text": text == target,
        "generated_prefix_len": len(text),
        "first_mismatch": first_mismatch,
        "ops": merge_literal_ops(ops),
    }
    return result, emitted + text, tape_pos


def blind_replay_book(
    emitted: str,
    target_len: int,
    tape: str,
    tape_pos: int,
    threshold: int,
) -> tuple[dict[str, Any], str, int]:
    pos = 0
    generated = []
    ops = []
    while pos < target_len:
        remaining = target_len - pos
        if len(emitted) >= threshold and remaining >= threshold:
            length = min(remaining, max(threshold, min(160, len(emitted))))
            source = 0
            chunk = emitted[source : source + length]
            generated.append(chunk)
            ops.append(
                {
                    "type": "copy",
                    "target_start": pos,
                    "length": length,
                    "source": source,
                }
            )
            pos += length
            continue
        if tape_pos >= len(tape):
            break
        digit = tape[tape_pos]
        tape_pos += 1
        generated.append(digit)
        ops.append(
            {
                "type": "literal",
                "target_start": pos,
                "length": 1,
                "source": None,
                "payload": digit,
            }
        )
        pos += 1
    text = "".join(generated)
    result = {
        "generated_text": text,
        "generated_prefix_len": len(text),
        "ops": merge_literal_ops(ops),
    }
    return result, emitted + text, tape_pos


def cutpoints(ops: list[dict[str, Any]], book_len: int) -> set[int]:
    return {
        op["target_start"] + op["length"]
        for op in ops[:-1]
        if 0 < op["target_start"] + op["length"] < book_len
    }


def compare_ops(
    predicted: list[dict[str, Any]],
    canonical: list[dict[str, Any]],
    book_len: int,
) -> dict[str, Any]:
    pred_cuts = cutpoints(predicted, book_len)
    canon_cuts = cutpoints(canonical, book_len)
    canon_by_start = {op["target_start"]: op for op in canonical}
    source_length_hits = 0
    literal_span_hits = 0
    for op in predicted:
        stable = canon_by_start.get(op["target_start"])
        if stable is None:
            continue
        if op["type"] == "copy" and stable["type"] == "copy":
            if op["length"] == stable["length"] and op["source"] == stable["source"]:
                source_length_hits += 1
        if op["type"] == "literal" and stable["type"] == "literal":
            if op["length"] == stable["length"]:
                literal_span_hits += 1
    return {
        "exact_ops": predicted == canonical,
        "predicted_ops": len(predicted),
        "canonical_ops": len(canonical),
        "cutpoint_hits": len(pred_cuts & canon_cuts),
        "canonical_cutpoints": len(canon_cuts),
        "predicted_cutpoints": len(pred_cuts),
        "source_length_hits": source_length_hits,
        "canonical_copy_ops": sum(1 for op in canonical if op["type"] == "copy"),
        "literal_span_hits": literal_span_hits,
        "canonical_literal_ops": sum(1 for op in canonical if op["type"] == "literal"),
    }


def replay_all(
    books: dict[int, str],
    canonical: dict[int, list[dict[str, Any]]],
    tape: str,
    threshold: int,
    mode: str,
) -> dict[str, Any]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    tape_pos = 0
    rows = []
    exact_books = []
    for book in range(10, 70):
        if mode == "target_conditioned":
            result, emitted, tape_pos = target_conditioned_replay_book(
                emitted,
                books[book],
                tape,
                tape_pos,
                threshold,
            )
            generated_text = books[book] if result["exact_text"] else None
            exact_text = result["exact_text"]
        elif mode == "blind":
            result, emitted, tape_pos = blind_replay_book(
                emitted,
                len(books[book]),
                tape,
                tape_pos,
                threshold,
            )
            generated_text = result["generated_text"]
            exact_text = generated_text == books[book]
        else:
            raise KeyError(mode)
        comparison = compare_ops(result["ops"], canonical[book], len(books[book]))
        prefix_len = (
            len(books[book])
            if exact_text
            else common_prefix_len(generated_text or "", books[book])
        )
        row = {
            "book": book,
            "exact_text": exact_text,
            "prefix_len": prefix_len,
            "prefix_fraction": prefix_len / len(books[book]),
            "tape_pos_after_book": tape_pos,
            **comparison,
        }
        rows.append(row)
        if exact_text:
            exact_books.append(book)
    return {
        "mode": mode,
        "threshold": threshold,
        "exact_books": exact_books,
        "exact_book_count": len(exact_books),
        "exact_nontrivial_books": [
            book for book in exact_books if len(canonical[book]) > 1
        ],
        "exact_nontrivial_book_count": len(
            [book for book in exact_books if len(canonical[book]) > 1]
        ),
        "tape_digits_consumed": tape_pos,
        "tape_digits_total": len(tape),
        "mean_prefix_fraction": mean(row["prefix_fraction"] for row in rows),
        "exact_ops_books": sum(1 for row in rows if row["exact_ops"]),
        "cutpoint_hits": sum(row["cutpoint_hits"] for row in rows),
        "canonical_cutpoints": sum(row["canonical_cutpoints"] for row in rows),
        "source_length_hits": sum(row["source_length_hits"] for row in rows),
        "canonical_copy_ops": sum(row["canonical_copy_ops"] for row in rows),
        "literal_span_hits": sum(row["literal_span_hits"] for row in rows),
        "canonical_literal_ops": sum(row["canonical_literal_ops"] for row in rows),
        "sample_rows": rows[:12],
    }


def common_prefix_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index
    return limit


def shuffled_controls(
    books: dict[int, str],
    canonical: dict[int, list[dict[str, Any]]],
    tape: str,
    threshold: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + threshold)
    values = []
    chars = list(tape)
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        row = replay_all(
            books,
            canonical,
            "".join(chars),
            threshold,
            "target_conditioned",
        )
        values.append(row["exact_book_count"])
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "exact_book_mean": mean(values),
        "exact_book_p95": percentile(values, 0.95),
        "exact_book_max": values[-1],
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape, canonical = canonical_tape_and_ops(ledger["canonical_ops_by_book"])
    target_rows = [
        replay_all(books, canonical, tape, threshold, "target_conditioned")
        for threshold in MIN_COPY_THRESHOLDS
    ]
    blind_rows = [
        replay_all(books, canonical, tape, threshold, "blind")
        for threshold in MIN_COPY_THRESHOLDS
    ]
    control_rows = [
        {
            "threshold": threshold,
            **shuffled_controls(books, canonical, tape, threshold),
        }
        for threshold in MIN_COPY_THRESHOLDS
    ]
    best = max(
        target_rows,
        key=lambda row: (
            row["exact_nontrivial_book_count"],
            row["exact_book_count"],
            row["cutpoint_hits"],
        ),
    )
    control_by_threshold = {row["threshold"]: row for row in control_rows}
    best_control = control_by_threshold[best["threshold"]]
    promotes_replay = (
        best["exact_nontrivial_book_count"] > 0
        and best["exact_book_count"] > best_control["exact_book_p95"]
    )
    summary = {
        "literal_tape_digits": len(tape),
        "literal_tape_chunks": sum(
            1
            for rows in canonical.values()
            for op in rows
            if op["type"] == "literal"
        ),
        "thresholds_tested": MIN_COPY_THRESHOLDS,
        "best_threshold": best["threshold"],
        "best_exact_books": best["exact_book_count"],
        "best_exact_nontrivial_books": best["exact_nontrivial_book_count"],
        "best_tape_digits_consumed": best["tape_digits_consumed"],
        "best_cutpoint_hits": best["cutpoint_hits"],
        "best_canonical_cutpoints": best["canonical_cutpoints"],
        "best_source_length_hits": best["source_length_hits"],
        "best_canonical_copy_ops": best["canonical_copy_ops"],
        "best_shuffle_exact_book_p95": best_control["exact_book_p95"],
        "best_blind_exact_books": max(row["exact_book_count"] for row in blind_rows),
        "promotes_innovation_tape_replay": promotes_replay,
        "interpretation": (
            "The canonical literal payload can be treated as a single innovation "
            "tape and replayed with online copy policies. The target-conditioned "
            "layer is an upper bound because it asks whether candidate copies "
            "match the known target; blind replay is the closed-loop control."
        ),
    }
    return {
        "schema": "innovation_tape_replay_gate_v1",
        "scope": "analysis_only_literal_tape_plus_online_copy_transducer",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "latent_transducer_audit": rel(LATENT_TRANSDUCER_AUDIT),
        },
        "target_conditioned_rows": target_rows,
        "blind_rows": blind_rows,
        "shuffle_control_rows": control_rows,
        "summary": summary,
        "classification": (
            "innovation_tape_replay_promoted"
            if promotes_replay
            else "innovation_tape_replay_not_promoted"
        ),
        "decision": {
            "promotes_innovation_tape_replay": promotes_replay,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Innovation Tape Replay Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the canonical literal payload can be treated as one external",
        "innovation tape consumed by an online copy transducer, instead of as",
        "operation-local literal payload attached to a fixed skeleton.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Literal tape chunks: `{s['literal_tape_chunks']}`.",
        f"- Thresholds tested: `{s['thresholds_tested']}`.",
        f"- Best threshold: `{s['best_threshold']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Best exact nontrivial books: `{s['best_exact_nontrivial_books']}`.",
        f"- Best tape digits consumed: `{s['best_tape_digits_consumed']}/{s['literal_tape_digits']}`.",
        f"- Best cutpoint hits: `{s['best_cutpoint_hits']}/{s['best_canonical_cutpoints']}`.",
        f"- Best source+length hits: `{s['best_source_length_hits']}/{s['best_canonical_copy_ops']}`.",
        f"- Best shuffled-tape exact-book p95: `{s['best_shuffle_exact_book_p95']}`.",
        f"- Best blind replay exact books: `{s['best_blind_exact_books']}`.",
        f"- Promotes innovation tape replay: `{s['promotes_innovation_tape_replay']}`.",
        "",
        s["interpretation"],
        "",
        "## Target-Conditioned Rows",
        "",
        "| Threshold | Exact books | Nontrivial exact | Tape used | Cutpoints | Source+length | Shuffle p95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    controls = {row["threshold"]: row for row in result["shuffle_control_rows"]}
    for row in result["target_conditioned_rows"]:
        control = controls[row["threshold"]]
        lines.append(
            f"| `{row['threshold']}` | `{row['exact_book_count']}/60` | "
            f"`{row['exact_nontrivial_book_count']}` | "
            f"`{row['tape_digits_consumed']}/{row['tape_digits_total']}` | "
            f"`{row['cutpoint_hits']}/{row['canonical_cutpoints']}` | "
            f"`{row['source_length_hits']}/{row['canonical_copy_ops']}` | "
            f"`{control['exact_book_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Blind Rows",
            "",
            "| Threshold | Exact books | Mean prefix fraction | Tape used |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["blind_rows"]:
        lines.append(
            f"| `{row['threshold']}` | `{row['exact_book_count']}/60` | "
            f"`{row['mean_prefix_fraction']:.6f}` | "
            f"`{row['tape_digits_consumed']}/{row['tape_digits_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The target-conditioned layer is an upper bound, not a closed-loop generator.",
            "- Blind replay is the closed-loop control.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
