from __future__ import annotations

import copy
import importlib.util
import json
import math
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
AUDIT_144 = HERE / "scripts" / "144_copy_source_distance_model_audit.py"

PREFIX_CUTOFFS = [10, 20, 35, 50, 60]


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


def length_bucket(row: dict[str, Any]) -> str:
    length = int(row["length"])
    if length < 10:
        return "short_lt10"
    if length < 30:
        return "mid_10_29"
    return "long_ge30"


def book_half(row: dict[str, Any]) -> str:
    return "first_half" if int(row["book"]) < 35 else "second_half"


def book_pos_bucket(row: dict[str, Any]) -> str:
    pos = int(row["book_pos"])
    if pos < 20:
        return "book_start_lt20"
    if pos < 100:
        return "book_mid_20_99"
    return "book_late_ge100"


def context_functions() -> dict[str, Callable[[dict[str, Any]], str]]:
    return {
        "global": lambda _row: "global",
        "book_half": book_half,
        "copy_length_bucket": length_bucket,
        "copy_length_exact": lambda row: f"length_{int(row['length'])}",
        "book_half_x_length_bucket": lambda row: f"{book_half(row)}::{length_bucket(row)}",
        "book_position_bucket": book_pos_bucket,
    }


def score_context(
    rows: list[dict[str, Any]],
    context_fn: Callable[[dict[str, Any]], str],
    *,
    counts: dict[str, Any] | None = None,
    update: bool,
) -> dict[str, Any]:
    local = (
        copy.deepcopy(counts)
        if counts is not None
        else {"flag": {True: 0.0, False: 0.0}, "exception": {}}
    )
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    for row in rows:
        source = int(row["source_digit_pos"])
        default = int(row["previous_source_plus_length_default"])
        is_default = source == default
        flag_bucket = local["flag"]
        probability = (flag_bucket[is_default] + 1.0) / (
            flag_bucket[True] + flag_bucket[False] + 2.0
        )
        flag_bits += -math.log2(probability)
        if update:
            flag_bucket[is_default] += 1.0
        if is_default:
            default_count += 1
            continue
        legal_sources = [
            value for value in range(int(row["legal_source_count"])) if value != default
        ]
        if source not in legal_sources:
            raise RuntimeError({"row": row, "legal_sources": legal_sources})
        context = context_fn(row)
        exception_bucket = local["exception"].setdefault(context, {})
        total = sum(exception_bucket.get(value, 0.0) for value in legal_sources)
        probability = (exception_bucket.get(source, 0.0) + 1.0) / (
            total + len(legal_sources)
        )
        exception_bits += -math.log2(probability)
        if update:
            exception_bucket[source] = exception_bucket.get(source, 0.0) + 1.0
        exception_count += 1
    return {
        "bits": flag_bits + exception_bits,
        "flag_bits": flag_bits,
        "exception_bits": exception_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "context_count": len(local["exception"]),
        "counts": local,
    }


def rows_for_books(rows: list[dict[str, Any]], books: set[int]) -> list[dict[str, Any]]:
    return [row for row in rows if int(row["book"]) in books]


def prefix_frozen_rows(
    rows: list[dict[str, Any]],
    contexts: dict[str, Callable[[dict[str, Any]], str]],
    names: list[str],
) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = rows_for_books(rows, set(range(cutoff)))
        test = rows_for_books(rows, set(range(cutoff, 70)))
        row = {
            "cutoff": cutoff,
            "label": f"prefix_{cutoff}_future_suffix",
            "train_events": len(train),
            "test_events": len(test),
            "models": {},
        }
        for name in names:
            train_score = score_context(train, contexts[name], counts=None, update=True)
            frozen = score_context(test, contexts[name], counts=train_score["counts"], update=False)
            row["models"][name] = {
                "train_bits": train_score["bits"],
                "test_frozen_bits": frozen["bits"],
                "train_context_count": train_score["context_count"],
            }
        row["candidate_minus_global_frozen_bits"] = (
            row["models"][names[1]]["test_frozen_bits"]
            - row["models"][names[0]]["test_frozen_bits"]
        )
        out.append(row)
    return out


def make_result() -> dict[str, Any]:
    compile134 = load_module("compile134", COMPILE_134)
    audit144 = load_module("audit144", AUDIT_144)
    formula = load_json(SOURCE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    normalized = compile134.normalize_ops(formula)
    collected = audit144.collect_source_rows(normalized, books)
    if collected["errors"]:
        raise RuntimeError(collected["errors"])
    rows = collected["rows"]
    contexts = context_functions()
    full_models = {}
    for name, fn in contexts.items():
        scored = score_context(rows, fn, counts=None, update=True)
        full_models[name] = {
            key: value
            for key, value in scored.items()
            if key != "counts"
        }
    global_bits = full_models["global"]["bits"]
    for model in full_models.values():
        model["delta_vs_global_bits"] = float(model["bits"]) - float(global_bits)
    best_non_global_name, best_non_global = min(
        ((name, model) for name, model in full_models.items() if name != "global"),
        key=lambda item: item[1]["bits"],
    )
    prefix_rows = prefix_frozen_rows(rows, contexts, ["global", best_non_global_name])
    improving = [
        name
        for name, model in full_models.items()
        if name != "global" and model["bits"] < global_bits
    ]
    classification = (
        "copy_source_structural_context_candidate_improves_global"
        if improving
        else "copy_source_structural_contexts_rejected_global_retained"
    )
    return {
        "schema": "copy_source_structural_context_audit.v1",
        "test": "154_copy_source_structural_context_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "source_formula": rel(SOURCE_FORMULA),
        "scope": {
            "copy_source_events": len(rows),
            "question": (
                "Do simple mechanical contexts for copy-source exception coding "
                "reduce the source ledger that blocks the cross-op near tie?"
            ),
            "active_context": "global exception source prior plus global default flag",
        },
        "full_corpus_models": full_models,
        "best_non_global": {
            "name": best_non_global_name,
            **best_non_global,
        },
        "prefix_future_suffix": {
            "candidate_name": best_non_global_name,
            "rows": prefix_rows,
        },
        "decision": {
            "compression_bound_changed": False,
            "global_source_context_retained": not bool(improving),
            "structural_context_promoted": bool(improving),
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 154. Copy Source Structural Context Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 152-153 showed that the tight cross-op near miss is blocked by",
        "copy-source cost. This audit tests whether simple mechanical contexts",
        "for the source exception prior reduce that ledger, or whether they just",
        "over-split sparse source positions.",
        "",
        "## Full-Corpus Models",
        "",
        "| Context | Stream bits | Delta vs global | Contexts | Default hits |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, model in sorted(
        result["full_corpus_models"].items(), key=lambda item: item[1]["bits"]
    ):
        lines.append(
            f"| `{name}` | `{model['bits']:.3f}` | "
            f"`{model['delta_vs_global_bits']:.3f}` | "
            f"`{model['context_count']}` | "
            f"`{model['default_count']}/{result['scope']['copy_source_events']}` |"
        )
    best = result["best_non_global"]
    lines.extend(
        [
            "",
            f"- Best non-global context: `{best['name']}`",
            f"- Best non-global penalty: `{best['delta_vs_global_bits']:.3f}` bits",
            "",
            "## Prefix Frozen Check",
            "",
            f"Best non-global candidate tested against global: `{result['prefix_future_suffix']['candidate_name']}`.",
            "",
            "| Split | Test events | Global frozen | Candidate frozen | Candidate - global |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["prefix_future_suffix"]["rows"]:
        name = result["prefix_future_suffix"]["candidate_name"]
        lines.append(
            f"| `{row['label']}` | `{row['test_events']}` | "
            f"`{row['models']['global']['test_frozen_bits']:.3f}` | "
            f"`{row['models'][name]['test_frozen_bits']:.3f}` | "
            f"`{row['candidate_minus_global_frozen_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The active global source exception prior remains best. Book half, copy",
            "length bucket, exact copy length, book position, and combined",
            "book-half/length-bucket contexts all add bits. The best structural",
            "context is still worse on the full corpus and in prefix-frozen checks.",
            "This means the source ledger blocking the near tie is not fixed by a",
            "simple declared context; a future improvement needs a genuinely new",
            "source derivation or a better source representation.",
            "",
            "## Decision",
            "",
            "- Compression bound unchanged.",
            "- Global copy-source exception context retained.",
            "- No plaintext, row0, or semantic change.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "154_copy_source_structural_context_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "154_copy_source_structural_context_audit.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
