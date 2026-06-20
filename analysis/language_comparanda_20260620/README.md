---
title: "469 language comparanda"
date: 2026-06-20
status: benchmark_and_controls_only
translation_delta: NONE
---

# 469 Language Comparanda

This directory incorporates the 2026-06-20 external research note on Tibia
constructed languages and possible non-numeric intermediate layers.

It is a frozen-artifact extension, not a new decode attempt. Its job is to
preserve a reusable registry of Tibia language comparanda, confidence labels,
positive controls, negative controls, and stop rules for any future method that
claims to translate or segment 469-like material.

## Gates

- No 469 plaintext, symbol-letter, book translation, or code-word claim is
  promoted from these comparanda.
- Community pages can define benchmark corpora and confidence tiers, but they
  are not `official_gt`.
- Any future intermediate-script claim must beat language and gibberish
  controls and improve MDL before it can be called mechanical progress.
- Semantic progress still requires CipSoft/in-game number-to-text,
  book-to-text, or symbol-to-meaning ground truth.

## Contents

- `source_research_summary.md` - distilled incorporation of the external
  research file provided on 2026-06-20.
- `language_registry.yaml` - language/source registry with allowed and blocked
  use.
- `source_confidence.yaml` - confidence labels and community-translation policy.
- `lexica/` - minimal seed lexica and anchors used only as controls.
- `scripts/01_language_registry_audit.py` - registry/source/row0 guardrail
  audit.
- `scripts/02_benchmark_readiness_audit.py` - benchmark and stop-rule
  readiness audit.
- `reports/` - generated and human-readable reports.

Translation delta: `NONE`.
