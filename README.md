# The Tibia "469" Bonelord Cipher — CLOSED

**Final verdict (2026-06-10): the 70-book "469" corpus does not contain a translatable message.** This is not "we gave up" — it is a positive, adversarially-verified, control-tested result. The corpus is **provably reproducible without a message**, and the part that isn't copy-paste **provably isn't language**.

> Full evidence, history, and reproduction paths: **[docs/469_final_report.md](docs/469_final_report.md)** — the definitive document of this project.

*Not affiliated with or endorsed by CipSoft GmbH; Tibia and Bonelord are trademarks of CipSoft GmbH.*

---

## The verdict in five findings

1. **Two unrelated cipher systems.** The NPC/poll *phrases* are a variable-length digit-group word-code (small codebook recovered: 6 entries attested in-DB + 7 reconstructed; validation-only — never CipSoft-confirmed). The 70 *books* are a separate fixed 2-digit-code → 14-symbol system, mechanically solved end-to-end: 99 codes → 14 symbols, zero ambiguity, byte-exact reconstruction 70/70.

2. **The book symbol layer is non-linguistic — five disqualifiers spanning three independent axes, all of which hold on the deduplicated corpus.** Flat-random fits the frequency profile better than every language tested (UNIFORM 3691 < English 4296 < German 4850 < Spanish 9408; deduped: 639 < 788 < 887 < 1737); per-symbol rates are language-impossible (F 10%, V 6.6%, R 0.56%, O 0.17%); the reduced-alphabet/abjad escape is closed; the only sequential structure is verbatim copy-paste; the code→symbol map is a reversal-invariant lookup table (86/89 reverse-pairs same-symbol), not a letter cipher.

3. **The corpus is provably message-free recombination.** 20/70 books are exact substrings of other books; 62 modules cover 81.5% of all digits; only ~995 of 5,729 symbols are novel. A two-part generative code (module inventory + assembly) describes the corpus in 24,628 bits — beating the strongest competing tokenization (the LEARNED lexicon, 29,757 bits) by **~5,130 bits (~17%)**, and the weaker MIXA1 lexicon by 10,149 bits (29%) — while the same test *loses* on genuine-language controls. The books were assembled by **copying pre-encoded digit strings from a fixed text→code lexicon**, not by enciphering fresh text.

4. **Every internal attack surface is exhausted.** Substitution solving (anti-pareidolia anagram gate), mathemagic/number systems (~56 probe families, all NULL), Ottendorf/index ciphers, transposition/re-pairing, alternative segmentations (MDL contest), metadata channels, zero-omission side channel, the homophone-selection channel (**per-occurrence capacity 0 bits**, with a one-shot residual ≤~1,460 bits that is unreadable as language — selection is deterministic: 95.9% code agreement on non-copied repeats, z=+16.4, one variant cell corpus-wide), and the residual "German-like" signal (**repeated-motif structure, not language** — a powered pre-registered split-half test shows real language would score z≈+9; the corpus scores +1.3 to +3.0).

5. **The only thing that can reopen this is CipSoft.** An officially attested book→plaintext pair or symbol table would be testable immediately against the validated mechanical model. As of 2026-06-09, no such material exists publicly; all published "solutions" are falsified or unverified (see report §8).

## Start here — how to read this

| If you want… | Read |
|---|---|
| the 60-second verdict | this page (the five findings above) |
| the full evidence, falsification stack, corrections & reproduction guide | **[docs/469_final_report.md](docs/469_final_report.md)** — the canonical document |
| a browsable, page-by-page deep dive | the **[project wiki](docs/wiki/README.md)** (9 pages + glossary) |
| the reusable method, told for a general audience | the **[case study](case-study/README.md)** |
| to reproduce the numbers yourself | [analysis/audit_20260609/](analysis/audit_20260609/) + [scripts/README.md](scripts/README.md) |
| definitions of the coined terms | the [glossary](docs/wiki/GLOSSARY.md) |

The **final report is canonical**; the wiki and case study are derived views of the same verified findings. Older snapshots (`docs/469_frozen_deliverable_2026-06-01.md`, `docs/plans/`) are retained as history and are superseded by the report.

## What this project produced

- **[docs/469_final_report.md](docs/469_final_report.md)** — the final report: full falsification stack, timeline 2005→2026, corrections ledger, external claims register, reproduction guide.
- **[docs/wiki/](docs/wiki/)** — the 9-page project wiki (puzzle background, data & method, the two-cipher finding, phrase codebook, attempts & dead ends, lessons).
- **[analysis/audit_20260609/](analysis/audit_20260609/)** — committed scripts + raw outputs behind every number in the final report.
- **[scripts/](scripts/README.md)** — ~554 probe/gate/audit scripts from the structural-search era (see [scripts/README.md](scripts/README.md) for what is load-bearing vs historical); `export_workbook_to_sqlite.py` regenerates the operational DB from the committed `.xlsx` workbooks.
- A methodology: multi-agent adversarial verification, pre-registered nulls, holdout gates, and an outcome ledger — the discipline that kept *plausible-looking output* from being mistaken for *signal* (and rejected a tempting 100%-coverage external "solution" because it failed two ground-truth cribs).

## Structural discoveries (how the corpus was made)

Real findings about the *production process*, none of which yield meaning: the anchors **34=B, 78=E, 67=A** (re-unifying phrase and book layers on the "BE A" prefix); the reversal-invariant homophone table; the deterministic segment→code lexicon with proximity-rotation surface behavior; the rule-governed omitted-zero mechanic; the module inventory that generates all 70 books.

---

## License, data & trademarks

The original analysis, code, and documentation are MIT-licensed (see [LICENSE](LICENSE)). The repository also includes numeric data **derived from** *Tibia* (the Bonelord digit corpora), included nominatively to make the cryptanalysis reproducible — see [NOTICE](NOTICE) for provenance and the trademark/affiliation position. *Tibia* and *Bonelord* are trademarks of CipSoft GmbH; this project is **not affiliated with or endorsed by CipSoft GmbH**.

The repo follows the **wiki-viva kit** documentation conventions in *frozen-artifact mode* — see [AGENTS.md](AGENTS.md), [`wiki.config.yaml`](wiki.config.yaml).

---

**Status: closed (2026-06-10).** No further internal decode work is warranted — the remaining failure mode would be pareidolia, which this project spent its discipline budget learning to refuse.
