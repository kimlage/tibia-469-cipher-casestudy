from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_repair_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/46_forced_length_literal_repair_search.py"

DIGITS = [str(i) for i in range(10)]
BOS = "BOS"
ALPHA_RANGE = range(1, 65)


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


def load_scorer():
    spec = importlib.util.spec_from_file_location("forced_repair_scorer", SCORER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer: {SCORER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_payload_stream(formula: dict) -> str:
    return "".join(
        op["text"]
        for book in map(str, formula["policy"]["book_order"])
        for op in formula["book_recipes"][book]["ops"]
        if op["type"] == "literal"
    )


def literal_run_segments(formula: dict) -> list[str]:
    return [
        op["text"]
        for book in map(str, formula["policy"]["book_order"])
        for op in formula["book_recipes"][book]["ops"]
        if op["type"] == "literal"
    ]


def book_literal_segments(formula: dict) -> list[list[str]]:
    return [
        [op["text"] for op in formula["book_recipes"][str(book)]["ops"] if op["type"] == "literal"]
        for book in formula["policy"]["book_order"]
    ]


def previous_emitted_context_pairs(formula: dict) -> list[tuple[str, str]]:
    pairs = []
    emitted = ""
    for book in map(str, formula["policy"]["book_order"]):
        for op in formula["book_recipes"][book]["ops"]:
            length = int(op["length"])
            if op["type"] == "literal":
                for digit in op["text"]:
                    context = emitted[-1] if emitted else BOS
                    pairs.append((context, digit))
                    emitted += digit
            elif op["type"] == "copy":
                start = int(op["source_digit_pos"])
                chunk = emitted[start : start + length]
                if len(chunk) != length:
                    raise ValueError({"book": book, "op": op, "type": "short_copy"})
                emitted += chunk
            else:
                raise ValueError(op)
    return pairs


def previous_literal_pairs_global(stream: str) -> list[tuple[str, str]]:
    pairs = []
    previous = BOS
    for digit in stream:
        pairs.append((previous, digit))
        previous = digit
    return pairs


def previous_literal_pairs_run_reset(segments: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for segment in segments:
        previous = BOS
        for digit in segment:
            pairs.append((previous, digit))
            previous = digit
    return pairs


def previous_literal_pairs_book_reset(book_segments: list[list[str]]) -> list[tuple[str, str]]:
    pairs = []
    for segments in book_segments:
        previous = BOS
        for segment in segments:
            for digit in segment:
                pairs.append((previous, digit))
                previous = digit
    return pairs


def adaptive_markov_bits(pairs: list[tuple[str, str]], alpha: int) -> float:
    counts = defaultdict(lambda: {digit: 0 for digit in DIGITS})
    totals = defaultdict(int)
    bits = 0.0
    for context, digit in pairs:
        probability = (counts[context][digit] + alpha) / (totals[context] + len(DIGITS) * alpha)
        bits += -math.log2(probability)
        counts[context][digit] += 1
        totals[context] += 1
    return bits


def context_summary(pairs: list[tuple[str, str]]) -> dict:
    counts = Counter(context for context, _digit in pairs)
    return {
        "context_count": len(counts),
        "context_histogram": dict(sorted(counts.items())),
    }


def best_markov_model(name: str, pairs: list[tuple[str, str]], family_bits: int, current_total: float) -> dict:
    rows = []
    for alpha in ALPHA_RANGE:
        payload_bits = adaptive_markov_bits(pairs, alpha)
        model_bits = gamma_bits(alpha + 1) + family_bits
        rows.append(
            {
                "model": name,
                "alpha": alpha,
                "payload_bits": payload_bits,
                "model_declaration_bits": model_bits,
                "payload_plus_model_bits": payload_bits + model_bits,
                "family_bits_charged": family_bits,
                "decodable": True,
            }
        )
    rows.sort(key=lambda row: row["payload_plus_model_bits"])
    best = rows[0]
    return {
        **best,
        "context_summary": context_summary(pairs),
        "total_bits_if_replacing_payload_model": current_total + best["payload_plus_model_bits"],
        "sweep_top16": rows[:16],
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    scorer = load_scorer()
    score = scorer.score_formula(formula, books)

    if score["validation"]["errors"]:
        raise RuntimeError(score["validation"])

    current_formula_bits = formula["mdl_estimate_rough"][
        "sequential_lz_digit_address_forced_length_literal_repair_bits"
    ]
    payload_model = formula["policy"]["literal_payload_model"]
    current_alpha = int(payload_model["alpha"])
    stream = literal_payload_stream(formula)
    current_payload_bits = score["literal_payload_bits"]
    current_model_bits = int(payload_model["model_declaration_bits"])
    current_payload_plus_model = current_payload_bits + current_model_bits
    current_without_payload_model = current_formula_bits - current_payload_plus_model

    models = [
        {
            "model": "adaptive_dirichlet_zero_order_current",
            "alpha": current_alpha,
            "payload_bits": current_payload_bits,
            "model_declaration_bits": current_model_bits,
            "payload_plus_model_bits": current_payload_plus_model,
            "family_bits_charged": 0,
            "decodable": True,
            "context_summary": {"context_count": 1, "context_histogram": {"GLOBAL": len(stream)}},
            "total_bits_if_replacing_payload_model": current_formula_bits,
        },
        best_markov_model(
            "adaptive_prev_literal_digit_global",
            previous_literal_pairs_global(stream),
            family_bits=2,
            current_total=current_without_payload_model,
        ),
        best_markov_model(
            "adaptive_prev_literal_digit_book_reset",
            previous_literal_pairs_book_reset(book_literal_segments(formula)),
            family_bits=3,
            current_total=current_without_payload_model,
        ),
        best_markov_model(
            "adaptive_prev_literal_digit_run_reset",
            previous_literal_pairs_run_reset(literal_run_segments(formula)),
            family_bits=3,
            current_total=current_without_payload_model,
        ),
        best_markov_model(
            "adaptive_prev_emitted_digit",
            previous_emitted_context_pairs(formula),
            family_bits=3,
            current_total=current_without_payload_model,
        ),
    ]
    models.sort(key=lambda row: row["total_bits_if_replacing_payload_model"])
    best = models[0]
    promoted = best["model"] != "adaptive_dirichlet_zero_order_current"
    classification = (
        "controlled_literal_payload_context_improvement"
        if promoted
        else "post_forced_repair_literal_payload_context_not_promoted"
    )

    if promoted:
        out = {
            "schema": "sequential_lz_digit_address_forced_length_literal_context_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                **formula["policy"],
                "literal_payload_model": {
                    "family": best["model"],
                    "alpha": best["alpha"],
                    "alphabet": DIGITS,
                    "contexts": [BOS, *DIGITS],
                    "context_source": (
                        "previous emitted digit in the already generated digit stream; BOS only before "
                        "the first generated digit"
                    ),
                    "model_declaration_bits": best["model_declaration_bits"],
                    "family_bits_charged": best["family_bits_charged"],
                    "decodable": True,
                },
            },
            "book_recipes": formula["book_recipes"],
            "mdl_estimate_rough": {
                **formula["mdl_estimate_rough"],
                "fixed_bits": score["fixed_bits"] - current_model_bits + best["model_declaration_bits"],
                "sequential_lz_digit_address_forced_length_literal_context_bits": best[
                    "total_bits_if_replacing_payload_model"
                ],
                "previous_sequential_lz_digit_address_forced_length_literal_repair_bits": current_formula_bits,
                "gain_vs_previous_forced_length_literal_repair_bits": (
                    current_formula_bits - best["total_bits_if_replacing_payload_model"]
                ),
                "previous_adaptive_literal_payload_bits": current_payload_bits,
                "adaptive_context_literal_payload_bits": best["payload_bits"],
                "literal_payload_model_declaration_bits": best["model_declaration_bits"],
                "literal_payload_context_model": best["model"],
                "literal_payload_context_alpha": best["alpha"],
            },
            "literal_payload_digit_histogram": dict(sorted(Counter(stream).items())),
            "literal_payload_context_summary": best["context_summary"],
            "validation": {
                **formula["validation"],
                "literal_payload_context_roundtrip_audit": {
                    "book_count": score["validation"]["book_count"],
                    "books_roundtrip_ok": score["validation"]["books_roundtrip_ok"],
                    "errors": score["validation"]["errors"],
                },
            },
            "boundary": formula["boundary"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_forced_repair_literal_payload_context_search.v1",
        "test": "61_post_forced_repair_literal_payload_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_formula_bits,
        "current_formula_score_audit": {
            "score_formula_total_bits": score["total_bits"],
            "fixed_bits": score["fixed_bits"],
            "literal_payload_bits": current_payload_bits,
            "literal_payload_model_declaration_bits": current_model_bits,
            "payload_plus_model_bits": current_payload_plus_model,
            "current_without_payload_model_bits": current_without_payload_model,
            "roundtrip_books": score["validation"]["books_roundtrip_ok"],
        },
        "literal_digits": len(stream),
        "literal_runs": len(literal_run_segments(formula)),
        "literal_digit_histogram": dict(sorted(Counter(stream).items())),
        "best_model": best,
        "models": models,
        "promotion_rule": (
            "promote only if a decodable contextual payload model beats the current "
            "zero-order alpha=14 payload after charged alpha and context-family bits"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Forced-Repair Literal Payload Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit incorporates the follow-up generation-formula report as a",
        "frontier check rather than as a stale baseline. The report's major",
        "recommendations were already tested in scripts `13` through `60`; this",
        "script tests one remaining natural refinement: whether the final literal",
        "payload is cheaper when coded by a decodable previous-digit context.",
        "",
        "The recipe, copy addresses, item-type ledger, book-length ledger, forced",
        "literal-length rule, and local repair are fixed. Only the literal payload",
        "model is replaced. Candidate totals subtract the current payload plus its",
        "declared model bits and add the contextual payload plus charged alpha and",
        "context-family bits.",
        "",
        "## Model Ranking",
        "",
        "| Rank | Model | Alpha | Payload bits | Model bits | Total bits | Delta vs active | Contexts |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['alpha']}` | "
            f"`{row['payload_bits']:.1f}` | `{row['model_declaration_bits']}` | "
            f"`{row['total_bits_if_replacing_payload_model']:.1f}` | "
            f"`{row['total_bits_if_replacing_payload_model'] - current_formula_bits:.1f}` | "
            f"`{row['context_summary']['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The active formula remains `{current_formula_bits:.1f}` bits. Its",
            f"literal payload costs `{current_payload_bits:.1f}` bits plus",
            f"`{current_model_bits}` declaration bits at `alpha={current_alpha}`.",
            f"The best contextual candidate is `{best['model']}` at",
            f"`{best['total_bits_if_replacing_payload_model']:.1f}` bits.",
            "",
            "A contextual model can only promote if it is decodable and beats the",
            "current zero-order payload after declaration cost. This test does not",
            "promote plaintext, row0 meaning, physical order, or authorial intent.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                "The best contextual payload model is decodable from the already",
                "generated stream, beats the active zero-order literal payload after",
                "charged declaration bits, and therefore emits a new mechanical",
                "formula artifact:",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("61_post_forced_repair_literal_payload_context_search", result, lines)


if __name__ == "__main__":
    main()
