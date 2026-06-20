from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

HIERARCHICAL = HERE / "hierarchical_reference_formula_469.json"
BASE = ROOT / "analysis/mechanism_model_20260618/mechanical_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
OCC_STREAMS = ROOT / "analysis/audit_20260609/homophone_channel/occ_streams.json"

SEP = "#"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def numeric_book_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def pair_key(code: str) -> str:
    return "".join(sorted(code))


def pair_digits(key: str) -> tuple[int, int]:
    return int(key[0]), int(key[1])


def reconstruct_components_with_provenance(formula: dict) -> dict[str, dict]:
    emitted_chars: list[str] = []
    emitted_meta: list[dict] = []
    components: dict[str, dict] = {}

    for recipe in formula["component_generation"]:
        comp_id = recipe["component_id"]
        chars: list[str] = []
        meta: list[dict] = []
        for op_index, op in enumerate(recipe["ops"]):
            if op["type"] == "literal":
                for ch in op["text"]:
                    row = {
                        "component_id": comp_id,
                        "component_pos": len(chars),
                        "inventory_op": "inventory_literal",
                        "inventory_op_index": op_index,
                    }
                    chars.append(ch)
                    meta.append(row)
                    emitted_chars.append(ch)
                    emitted_meta.append(row)
            elif op["type"] == "self_ref":
                source_meta = emitted_meta[op["source_pos"] : op["source_pos"] + op["length"]]
                source_chars = emitted_chars[op["source_pos"] : op["source_pos"] + op["length"]]
                for ch, src in zip(source_chars, source_meta):
                    row = {
                        "component_id": comp_id,
                        "component_pos": len(chars),
                        "inventory_op": "inventory_self_ref",
                        "inventory_source_component": src.get("component_id"),
                        "inventory_source_pos": src.get("component_pos"),
                        "inventory_op_index": op_index,
                    }
                    chars.append(ch)
                    meta.append(row)
                    emitted_chars.append(ch)
                    emitted_meta.append(row)
            else:
                raise ValueError(op)
        text = "".join(chars)
        if len(text) != recipe["length"]:
            raise ValueError((comp_id, recipe["length"], len(text)))
        components[comp_id] = {"text": text, "meta": meta}
        emitted_chars.append(SEP)
        emitted_meta.append({"component_id": SEP, "component_pos": -1, "inventory_op": "separator"})
    return components


def render_books_with_provenance(formula: dict, components: dict[str, dict]) -> dict[str, dict]:
    books = {}
    for book, recipe in formula["book_recipes"].items():
        chars: list[str] = []
        meta: list[dict] = []
        for item_index, item in enumerate(recipe):
            if item["type"] == "literal":
                for ch in item["text"]:
                    chars.append(ch)
                    meta.append(
                        {
                            "book_op": "book_literal",
                            "book_item_index": item_index,
                            "component_id": None,
                            "component_pos": None,
                            "inventory_op": "book_literal",
                        }
                    )
            elif item["type"] in {"module_slice", "tape_span", "tape_ref"}:
                component = components[item["component_id"]]
                start, end = item["start"], item["end"]
                for ch, src in zip(component["text"][start:end], component["meta"][start:end]):
                    chars.append(ch)
                    meta.append(
                        {
                            "book_op": item["type"],
                            "book_item_index": item_index,
                            "component_id": item["component_id"],
                            "component_pos": src["component_pos"],
                            "inventory_op": src["inventory_op"],
                            "inventory_source_component": src.get("inventory_source_component"),
                        }
                    )
            else:
                raise ValueError(item)
        books[str(book)] = {"text": "".join(chars), "meta": meta}
    return books


def token_streams(occ_streams: dict) -> dict[str, list[dict]]:
    by_book_pos: dict[str, dict[int, dict]] = defaultdict(dict)
    for sym, rows in occ_streams["occ"].items():
        for row in rows:
            by_book_pos[str(row["book"])][int(row["pos"])] = {
                "pos": int(row["pos"]),
                "code": row["code"],
                "symbol": sym,
                "novel": bool(row["novel"]),
                "xuniq": bool(row["xuniq"]),
            }
    return {book: [positions[pos] for pos in sorted(positions)] for book, positions in by_book_pos.items()}


def pair_labels(base: dict) -> dict[str, str]:
    labels = {}
    for key, row in base["pair_table"].items():
        if row["status"] == "pure":
            labels[key] = row["symbol_if_pure"]
        else:
            labels[key] = "|".join(row["symbols"])
    return labels


def aggregate_pair_features(books: dict, digits: dict, streams: dict, labels: dict) -> list[dict]:
    rows = {}
    for key, label in labels.items():
        a, b = pair_digits(key)
        rows[key] = {
            "pair": key,
            "label": label,
            "a": a,
            "b": b,
            "sum": a + b,
            "diff": b - a,
            "prod": a * b,
            "diag": int(a == b),
            "has_zero": int(a == 0 or b == 0),
            "has_six": int(a == 6 or b == 6),
            "has_nine": int(a == 9 or b == 9),
            "has_six_or_nine": int(a in {6, 9} or b in {6, 9}),
            "usage_count": 0,
            "omitted_count": 0,
            "novel_count": 0,
            "xuniq_count": 0,
            "first_global": 10**9,
            "first_book": 10**9,
            "first_token_pos": 10**9,
            "book_op_counts": Counter(),
            "inventory_op_counts": Counter(),
            "component_counts": Counter(),
            "source_component_counts": Counter(),
        }

    global_pos = 0
    errors = []
    for book in sorted(streams, key=numeric_book_key):
        if book not in books:
            continue
        raw = digits[book]
        rendered = books[book]["text"]
        if rendered != raw:
            errors.append({"book": book, "error": "formula_raw_mismatch"})
            continue
        digit_pos = 0
        for token in streams[book]:
            code = token["code"]
            if raw[digit_pos : digit_pos + 2] == code:
                width = 2
            elif raw[digit_pos : digit_pos + 1] == code[1]:
                width = 1
            else:
                errors.append({"book": book, "pos": token["pos"], "code": code, "digit_pos": digit_pos})
                break
            key = pair_key(code)
            if key in rows:
                row = rows[key]
                row["usage_count"] += 1
                row["omitted_count"] += int(width == 1)
                row["novel_count"] += int(token["novel"])
                row["xuniq_count"] += int(token["xuniq"])
                row["first_global"] = min(row["first_global"], global_pos)
                row["first_book"] = min(row["first_book"], int(book))
                row["first_token_pos"] = min(row["first_token_pos"], int(token["pos"]))
                span_meta = books[book]["meta"][digit_pos : digit_pos + width]
                for meta in span_meta:
                    row["book_op_counts"][meta["book_op"]] += 1
                    row["inventory_op_counts"][meta["inventory_op"]] += 1
                    if meta.get("component_id"):
                        row["component_counts"][meta["component_id"]] += 1
                    if meta.get("inventory_source_component"):
                        row["source_component_counts"][meta["inventory_source_component"]] += 1
            digit_pos += width
            global_pos += 1
        if digit_pos != len(raw):
            errors.append({"book": book, "error": "digit_pos_mismatch", "digit_pos": digit_pos, "raw_len": len(raw)})

    if errors:
        raise ValueError(errors[:5])

    feature_rows = []
    for row in rows.values():
        total_digits = max(1, sum(row["book_op_counts"].values()))
        total_inventory = max(1, sum(row["inventory_op_counts"].values()))
        usage = max(1, row["usage_count"])
        component_total = max(1, sum(row["component_counts"].values()))
        source_total = max(1, sum(row["source_component_counts"].values()))
        out = {
            key: value
            for key, value in row.items()
            if key
            not in {
                "book_op_counts",
                "inventory_op_counts",
                "component_counts",
                "source_component_counts",
            }
        }
        for op in ["book_literal", "module_slice", "tape_span", "tape_ref"]:
            out[f"bookop_{op}_frac"] = row["book_op_counts"][op] / total_digits
        for op in ["book_literal", "inventory_literal", "inventory_self_ref"]:
            out[f"invop_{op}_frac"] = row["inventory_op_counts"][op] / total_inventory
        out["component_diversity"] = len(row["component_counts"])
        out["source_component_diversity"] = len(row["source_component_counts"])
        out["top_component_frac"] = (row["component_counts"].most_common(1)[0][1] / component_total) if row["component_counts"] else 0.0
        out["top_source_component_frac"] = (
            row["source_component_counts"].most_common(1)[0][1] / source_total
            if row["source_component_counts"]
            else 0.0
        )
        out["omitted_frac"] = row["omitted_count"] / usage
        out["novel_frac"] = row["novel_count"] / usage
        out["xuniq_frac"] = row["xuniq_count"] / usage
        feature_rows.append(out)
    return sorted(feature_rows, key=lambda row: row["pair"])


def majority_label(labels: list[str]) -> str:
    counts = Counter(labels)
    return min(counts, key=lambda label: (-counts[label], label))


def evaluate_stump(rows: list[dict], labels: list[str], feature: str, threshold: float) -> dict:
    left = [idx for idx, row in enumerate(rows) if row[feature] <= threshold]
    right = [idx for idx, row in enumerate(rows) if row[feature] > threshold]
    if not left or not right:
        return {"hits": -1}
    left_label = majority_label([labels[idx] for idx in left])
    right_label = majority_label([labels[idx] for idx in right])
    predictions = [right_label] * len(rows)
    for idx in left:
        predictions[idx] = left_label
    hits = sum(predictions[idx] == labels[idx] for idx in range(len(rows)))
    errors = len(rows) - hits
    label_count = len(set(labels))
    model_bits = (
        math.ceil(math.log2(64))
        + math.ceil(math.log2(128))
        + 2 * math.ceil(math.log2(label_count))
        + errors * (math.ceil(math.log2(len(rows))) + math.ceil(math.log2(label_count)))
    )
    lookup_bits = len(rows) * math.log2(label_count)
    return {
        "feature": feature,
        "threshold": threshold,
        "left_label": left_label,
        "right_label": right_label,
        "hits": hits,
        "accuracy": hits / len(rows),
        "errors": errors,
        "model_bits_rough": model_bits,
        "lookup_bits": lookup_bits,
        "gain_vs_lookup_bits": lookup_bits - model_bits,
    }


def best_stump(rows: list[dict], labels: list[str], features: list[str]) -> dict:
    best = None
    for feature in features:
        values = sorted({row[feature] for row in rows})
        if len(values) < 2:
            continue
        thresholds = [(left + right) / 2 for left, right in zip(values, values[1:])]
        for threshold in thresholds:
            result = evaluate_stump(rows, labels, feature, threshold)
            if result["hits"] < 0:
                continue
            if best is None or (
                result["hits"],
                result["gain_vs_lookup_bits"],
                -result["model_bits_rough"],
            ) > (
                best["hits"],
                best["gain_vs_lookup_bits"],
                -best["model_bits_rough"],
            ):
                best = result
    if best is None:
        raise ValueError("no stump candidates")
    return best


def fill_by_order(rows: list[dict], labels: list[str], feature: str, reverse: bool) -> dict:
    inventory = Counter(labels)
    symbol_order = [label for label, _ in inventory.most_common()]
    ordered_indices = sorted(range(len(rows)), key=lambda idx: (rows[idx][feature], rows[idx]["pair"]), reverse=reverse)
    assigned = [None] * len(rows)
    cursor = 0
    for label in symbol_order:
        for _ in range(inventory[label]):
            if cursor >= len(ordered_indices):
                break
            assigned[ordered_indices[cursor]] = label
            cursor += 1
    hits = sum(assigned[idx] == labels[idx] for idx in range(len(rows)))
    return {
        "feature": feature,
        "reverse": reverse,
        "hits": hits,
        "accuracy": hits / len(rows),
    }


def best_order_fill(rows: list[dict], labels: list[str], features: list[str]) -> dict:
    results = []
    for feature in features:
        results.append(fill_by_order(rows, labels, feature, False))
        results.append(fill_by_order(rows, labels, feature, True))
    results.sort(key=lambda row: (row["hits"], row["feature"], row["reverse"]), reverse=True)
    return results[0]


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_ge_observed": (sum(value >= observed for value in values) + 1) / (len(values) + 1),
    }


def run_controls(rows: list[dict], labels: list[str], features: list[str], observed_stump: int, observed_order: int) -> dict:
    stump_hits = []
    stump_gain = []
    order_hits = []
    for seed in range(700):
        rng = random.Random(469900 + seed)
        shuffled = labels[:]
        rng.shuffle(shuffled)
        stump = best_stump(rows, shuffled, features)
        order = best_order_fill(rows, shuffled, features)
        stump_hits.append(stump["hits"])
        stump_gain.append(stump["gain_vs_lookup_bits"])
        order_hits.append(order["hits"])
    return {
        "stump_hits": summarize(stump_hits, observed_stump),
        "stump_gain_vs_lookup_bits": summarize(stump_gain, 0.0),
        "order_fill_hits": summarize(order_hits, observed_order),
    }


def classify(stump: dict, order: dict, controls: dict) -> str:
    if stump["gain_vs_lookup_bits"] > 0 and controls["stump_hits"]["p_ge_observed"] <= 0.01:
        return "candidate_hierarchical_provenance_pair_formula"
    if controls["stump_hits"]["p_ge_observed"] <= 0.05 or controls["order_fill_hits"]["p_ge_observed"] <= 0.05:
        return "weak_hierarchical_provenance_signal_not_formula"
    return "hierarchical_provenance_not_pair_table_formula"


def main() -> None:
    hierarchical = load_json(HIERARCHICAL)
    base = load_json(BASE)
    digits = load_json(BOOKS_DIGITS)
    occ = load_json(OCC_STREAMS)

    components = reconstruct_components_with_provenance(hierarchical)
    books = render_books_with_provenance(hierarchical, components)
    streams = token_streams(occ)
    labels_by_pair = pair_labels(base)
    rows = aggregate_pair_features(books, digits, streams, labels_by_pair)

    labels = [row["label"] for row in rows]
    feature_names = [
        key
        for key, value in rows[0].items()
        if key not in {"pair", "label"} and isinstance(value, (int, float))
    ]
    stump = best_stump(rows, labels, feature_names)
    order = best_order_fill(rows, labels, feature_names)
    controls = run_controls(rows, labels, feature_names, stump["hits"], order["hits"])
    classification = classify(stump, order, controls)

    result = {
        "schema": "hierarchical_provenance_pair_label_audit.v1",
        "test": "09_hierarchical_provenance_pair_label_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "inputs": {
            "hierarchical_formula": str(HIERARCHICAL.relative_to(ROOT)),
            "base_formula": str(BASE.relative_to(ROOT)),
            "occ_streams": str(OCC_STREAMS.relative_to(ROOT)),
        },
        "pair_count": len(rows),
        "label_inventory": dict(sorted(Counter(labels).items())),
        "feature_count": len(feature_names),
        "best_stump": stump,
        "best_order_fill": order,
        "controls": controls,
        "boundary": {
            "semantic_delta": "NONE",
            "book_generation_changed": False,
            "pair_table_origin_explained": classification == "candidate_hierarchical_provenance_pair_formula",
        },
    }

    lines = [
        "# Hierarchical Provenance Pair-Label Audit",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit asks whether the new hierarchical generation provenance",
        "explains the unresolved 55-cell unordered pair table. It derives",
        "per-pair features from book recipe operations, tape inventory",
        "self-reference operations, component usage, omitted-zero rendering,",
        "and canonical `occ_streams.json` token positions.",
        "",
        "## Best Stump",
        "",
        "| Feature | Threshold | Hits | Accuracy | Rough gain vs lookup | Control p(hit) | Control p(gain>=0) |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| `{stump['feature']}` | `{stump['threshold']:.4f}` | `{stump['hits']}/55` | "
            f"`{stump['accuracy']:.3f}` | `{stump['gain_vs_lookup_bits']:.1f}` | "
            f"`{controls['stump_hits']['p_ge_observed']:.4f}` | "
            f"`{controls['stump_gain_vs_lookup_bits']['p_ge_observed']:.4f}` |"
        ),
        "",
        "## Best Inventory-Preserving Order Fill",
        "",
        "| Feature | Reverse | Hits | Accuracy | Control p(hit) |",
        "|---|---:|---:|---:|---:|",
        (
            f"| `{order['feature']}` | `{order['reverse']}` | `{order['hits']}/55` | "
            f"`{order['accuracy']:.3f}` | `{controls['order_fill_hits']['p_ge_observed']:.4f}` |"
        ),
        "",
        "## Control Summary",
        "",
        "| Control metric | Runs | Mean | Max | p(>= observed) |",
        "|---|---:|---:|---:|---:|",
        (
            f"| `best_stump_hits` | `{controls['stump_hits']['runs']}` | "
            f"`{controls['stump_hits']['mean']:.2f}` | `{controls['stump_hits']['max']:.0f}` | "
            f"`{controls['stump_hits']['p_ge_observed']:.4f}` |"
        ),
        (
            f"| `best_order_fill_hits` | `{controls['order_fill_hits']['runs']}` | "
            f"`{controls['order_fill_hits']['mean']:.2f}` | `{controls['order_fill_hits']['max']:.0f}` | "
            f"`{controls['order_fill_hits']['p_ge_observed']:.4f}` |"
        ),
        "",
        "## Boundary",
        "",
        "The hierarchical formula improves book generation, but these provenance",
        "features do not promote a pair-table origin formula unless they beat",
        "inventory-preserving controls and rough lookup cost. No plaintext or",
        "semantic claim is introduced.",
    ]
    write_result("09_hierarchical_provenance_pair_label_audit", result, lines)


if __name__ == "__main__":
    main()
