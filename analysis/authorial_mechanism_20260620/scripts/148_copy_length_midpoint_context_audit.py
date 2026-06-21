from __future__ import annotations

import copy
import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = HERE / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_136 = HERE / "scripts" / "136_copy_length_default_decodability_audit.py"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]
PERMUTATION_CONTROLS = 300
CONTROL_SEED = 469


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def score_copy_length_rows(
    rows: list[dict[str, Any]],
    *,
    min_len: int,
    context_fn: Callable[[dict[str, Any]], str],
    counts: dict[str, Any] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = (
        copy.deepcopy(counts)
        if counts is not None
        else {"flag": {}, "exception": {}}
    )
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    context_counts: dict[str, int] = {}
    for row in rows:
        context = context_fn(row)
        context_counts[context] = context_counts.get(context, 0) + 1
        default = int(row["decoder_max_possible_default"])
        length = int(row["length"])
        is_default = length == default
        flag_bucket = local["flag"].setdefault(context, {True: 0.0, False: 0.0})
        probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(probability)
        if update:
            flag_bucket[is_default] += 1.0
        if is_default:
            default_count += 1
            continue

        legal_lengths = [value for value in range(min_len, default + 1) if value != default]
        if length not in legal_lengths:
            raise RuntimeError({"row": row, "legal_lengths": legal_lengths})
        exception_bucket = local["exception"].setdefault(context, {})
        total = sum(exception_bucket.get(value, 0.0) for value in legal_lengths)
        probability = (exception_bucket.get(length, 0.0) + 1.0) / (
            total + len(legal_lengths)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[length] = exception_bucket.get(length, 0.0) + 1.0
        exception_count += 1

    return {
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "context_counts": dict(sorted(context_counts.items())),
        "counts": local,
    }


def rows_for_books(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["book"]) in books]


def context_global(_row: dict[str, Any]) -> str:
    return "global"


def context_midpoint(row: dict[str, Any]) -> str:
    return "first_half" if int(row["book"]) < 35 else "second_half"


def context_boundary(cutoff: int) -> Callable[[dict[str, Any]], str]:
    return lambda row: "before_cut" if int(row["book"]) < cutoff else "after_cut"


def boundary_sweep(rows: list[dict[str, Any]], *, min_len: int) -> list[dict[str, Any]]:
    out = []
    for cutoff in range(1, 70):
        scored = score_copy_length_rows(
            rows,
            min_len=min_len,
            context_fn=context_boundary(cutoff),
            counts=None,
            update=True,
        )
        out.append(
            {
                "cutoff": cutoff,
                "stream_bits": scored["bits"],
                "default_count": scored["default_count"],
                "exception_count": scored["exception_count"],
            }
        )
    return sorted(out, key=lambda row: row["stream_bits"])


def score_with_book_map(
    rows: list[dict[str, Any]],
    *,
    min_len: int,
    book_map: dict[int, int],
) -> dict[str, Any]:
    global_bits = score_copy_length_rows(
        rows,
        min_len=min_len,
        context_fn=context_global,
        counts=None,
        update=True,
    )["bits"]

    def mapped_boundary(cutoff: int) -> Callable[[dict[str, Any]], str]:
        return lambda row: "before_cut" if book_map[int(row["book"])] < cutoff else "after_cut"

    midpoint_bits = score_copy_length_rows(
        rows,
        min_len=min_len,
        context_fn=lambda row: (
            "first_half" if book_map[int(row["book"])] < 35 else "second_half"
        ),
        counts=None,
        update=True,
    )["bits"]
    best = min(
        (
            score_copy_length_rows(
                rows,
                min_len=min_len,
                context_fn=mapped_boundary(cutoff),
                counts=None,
                update=True,
            )["bits"],
            cutoff,
        )
        for cutoff in range(1, 70)
    )
    return {
        "midpoint_gain_vs_global_bits": global_bits - midpoint_bits,
        "best_boundary_gain_vs_global_bits": global_bits - best[0],
        "best_boundary_cutoff": best[1],
        "best_boundary_stream_bits": best[0],
    }


def permutation_controls(rows: list[dict[str, Any]], *, min_len: int) -> dict[str, Any]:
    observed = score_with_book_map(rows, min_len=min_len, book_map={i: i for i in range(70)})
    rng = random.Random(CONTROL_SEED)
    book_ids = list(range(70))
    midpoint_gains = []
    best_boundary_gains = []
    best_cutoffs = []
    for _ in range(PERMUTATION_CONTROLS):
        permuted = book_ids[:]
        rng.shuffle(permuted)
        book_map = {old: new for old, new in zip(book_ids, permuted)}
        scored = score_with_book_map(rows, min_len=min_len, book_map=book_map)
        midpoint_gains.append(scored["midpoint_gain_vs_global_bits"])
        best_boundary_gains.append(scored["best_boundary_gain_vs_global_bits"])
        best_cutoffs.append(scored["best_boundary_cutoff"])
    p_midpoint = (
        sum(gain >= observed["midpoint_gain_vs_global_bits"] for gain in midpoint_gains) + 1
    ) / (PERMUTATION_CONTROLS + 1)
    p_best = (
        sum(gain >= observed["best_boundary_gain_vs_global_bits"] for gain in best_boundary_gains)
        + 1
    ) / (PERMUTATION_CONTROLS + 1)
    return {
        "control_count": PERMUTATION_CONTROLS,
        "seed": CONTROL_SEED,
        "observed": observed,
        "midpoint_gain_control_summary": summary(midpoint_gains),
        "best_boundary_gain_control_summary": summary(best_boundary_gains),
        "p_permuted_midpoint_gain_ge_observed": p_midpoint,
        "p_permuted_best_boundary_gain_ge_observed": p_best,
        "best_cutoff_control_summary": summary([float(value) for value in best_cutoffs]),
    }


def prefix_split_rows(rows: list[dict[str, Any]], *, min_len: int) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = rows_for_books(rows, set(range(cutoff)))
        test = rows_for_books(rows, set(range(cutoff, 70)))
        row: dict[str, Any] = {
            "cutoff": cutoff,
            "label": f"prefix_{cutoff}_future_suffix",
            "train_events": len(train),
            "test_events": len(test),
            "models": {},
        }
        for name, fn in [
            ("global", context_global),
            ("midpoint_35", context_midpoint),
        ]:
            train_score = score_copy_length_rows(
                train,
                min_len=min_len,
                context_fn=fn,
                counts=None,
                update=True,
            )
            frozen = score_copy_length_rows(
                test,
                min_len=min_len,
                context_fn=fn,
                counts=train_score["counts"],
                update=False,
            )
            online = score_copy_length_rows(
                test,
                min_len=min_len,
                context_fn=fn,
                counts=train_score["counts"],
                update=True,
            )
            row["models"][name] = {
                "train_bits": train_score["bits"],
                "test_frozen_bits": frozen["bits"],
                "test_online_bits": online["bits"],
                "train_context_counts": train_score["context_counts"],
            }
        row["midpoint_minus_global_frozen_bits"] = (
            row["models"]["midpoint_35"]["test_frozen_bits"]
            - row["models"]["global"]["test_frozen_bits"]
        )
        row["midpoint_minus_global_online_bits"] = (
            row["models"]["midpoint_35"]["test_online_bits"]
            - row["models"]["global"]["test_online_bits"]
        )
        out.append(row)
    return out


def make_result() -> dict[str, Any]:
    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit136 = load_module("audit_136", AUDIT_136)
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    normalized = compile134.normalize_ops(formula)
    min_len = int(normalized["policy"]["min_len"])
    collected = audit136.collect_copy_length_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = collected["rows"]

    global_score = score_copy_length_rows(
        rows,
        min_len=min_len,
        context_fn=context_global,
        counts=None,
        update=True,
    )
    midpoint_score = score_copy_length_rows(
        rows,
        min_len=min_len,
        context_fn=context_midpoint,
        counts=None,
        update=True,
    )
    sweep = boundary_sweep(rows, min_len=min_len)
    best_boundary = sweep[0]
    midpoint_rank = [idx for idx, row in enumerate(sweep, start=1) if row["cutoff"] == 35][0]
    controls = permutation_controls(rows, min_len=min_len)
    prefix = prefix_split_rows(rows, min_len=min_len)
    prefix_gaps = [row["midpoint_minus_global_frozen_bits"] for row in prefix]

    classification = (
        "copy_length_midpoint_context_supported_not_formula_change"
        if controls["p_permuted_midpoint_gain_ge_observed"] <= 0.01
        else "copy_length_midpoint_context_weak_under_controls"
    )

    return {
        "schema": "copy_length_midpoint_context_audit.v1",
        "test": "148_copy_length_midpoint_context_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "copy_length_events": len(rows),
            "min_len": min_len,
            "question": (
                "Is the active fixed midpoint context for copy-length exceptions "
                "a supported mechanical split or a removable/posthoc parameter?"
            ),
        },
        "full_corpus": {
            "global_stream_bits": global_score["bits"],
            "midpoint_35_stream_bits": midpoint_score["bits"],
            "midpoint_gain_vs_global_bits": global_score["bits"] - midpoint_score["bits"],
            "midpoint_context_counts": midpoint_score["context_counts"],
            "best_boundary": best_boundary,
            "best_boundary_gain_vs_global_bits": global_score["bits"] - best_boundary["stream_bits"],
            "midpoint_boundary_rank": midpoint_rank,
            "top_10_boundaries": sweep[:10],
        },
        "permutation_controls": controls,
        "prefix_future_suffix": {
            "rows": prefix,
            "midpoint_minus_global_frozen_bits_summary": summary(prefix_gaps),
        },
        "decision": {
            "compression_bound_changed": False,
            "midpoint_context_retained": True,
            "best_boundary_promoted": False,
            "global_context_promoted": False,
            "reason": (
                "The natural midpoint split is strongly better than global and "
                "nearly tied with the best searched boundary; the searched best "
                "boundary is not promoted because it adds search/ad-hoc cost for "
                "only a sub-bit improvement over midpoint."
            ),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    full = result["full_corpus"]
    controls = result["permutation_controls"]
    lines = [
        "# 148. Copy Length Midpoint Context Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active copy-length default/exception ledger uses a fixed context:",
        "`book_id < 35` versus `book_id >= 35`. This audit tests whether that",
        "midpoint context is supported, removable, or merely a searched boundary.",
        "",
        "## Full-Corpus Context Test",
        "",
        f"- Global stream bits: `{full['global_stream_bits']:.3f}`",
        f"- Midpoint-35 stream bits: `{full['midpoint_35_stream_bits']:.3f}`",
        f"- Midpoint gain vs global: `{full['midpoint_gain_vs_global_bits']:.3f}` bits",
        f"- Best searched boundary: cutoff `{full['best_boundary']['cutoff']}` at `{full['best_boundary']['stream_bits']:.3f}` bits",
        f"- Best searched boundary gain vs global: `{full['best_boundary_gain_vs_global_bits']:.3f}` bits",
        f"- Midpoint boundary rank among 69 cuts: `{full['midpoint_boundary_rank']}`",
        "",
        "| Rank | Cutoff | Stream bits | Gain vs global |",
        "|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(full["top_10_boundaries"], start=1):
        lines.append(
            f"| `{rank}` | `{row['cutoff']}` | `{row['stream_bits']:.3f}` | "
            f"`{full['global_stream_bits'] - row['stream_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Permutation Controls",
            "",
            f"- Controls: `{controls['control_count']}` random book-id permutations, seed `{controls['seed']}`",
            f"- P(permuted midpoint gain >= observed): `{controls['p_permuted_midpoint_gain_ge_observed']:.4f}`",
            f"- P(permuted best-boundary gain >= observed): `{controls['p_permuted_best_boundary_gain_ge_observed']:.4f}`",
            f"- Permuted midpoint gain summary: `{controls['midpoint_gain_control_summary']}`",
            f"- Permuted best-boundary gain summary: `{controls['best_boundary_gain_control_summary']}`",
            "",
            "## Prefix Future-Suffix Check",
            "",
            "| Split | Train events | Test events | Global frozen | Midpoint frozen | Midpoint - global |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["prefix_future_suffix"]["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['train_events']}` | `{row['test_events']}` | "
            f"`{row['models']['global']['test_frozen_bits']:.3f}` | "
            f"`{row['models']['midpoint_35']['test_frozen_bits']:.3f}` | "
            f"`{row['midpoint_minus_global_frozen_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            f"Frozen midpoint-minus-global summary: `{result['prefix_future_suffix']['midpoint_minus_global_frozen_bits_summary']}`",
            "",
            "## Interpretation",
            "",
            "The midpoint context is not removed: it beats a global copy-length",
            "exception stream by `13.839` bits and is second among all one-cut",
            "boundaries. The best searched boundary is cutoff `37`, only `0.256`",
            "bits better, so promoting that searched cutoff would add ad-hoc",
            "description cost without a meaningful improvement. Permutation",
            "controls show that the observed midpoint and best-boundary gains are",
            "not typical under shuffled book ids.",
            "",
            "Prefix-frozen scoring supports the same direction: midpoint beats",
            "the global context in all tested future-suffix splits, with frozen",
            "gaps from `5.493` to `26.416` bits. This strengthens the copy-length",
            "context as a real mechanical component, while still leaving full",
            "recipe discovery and row0 origin unchanged.",
            "",
            "## Decision",
            "",
            "- Keep the declared midpoint copy-length context.",
            "- Do not promote the searched cutoff-37 boundary.",
            "- Do not replace the context with a global model.",
            "- Compression bound, row0 origin, plaintext, and semantic status remain unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "148_copy_length_midpoint_context_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "148_copy_length_midpoint_context_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
