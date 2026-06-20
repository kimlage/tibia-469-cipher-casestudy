# Intermediate Script Test Report

Verdict: `open_mechanism_only`. Translation delta: `NONE`.

The new hypothesis is H25:

```text
469 digits -> row0 14-symbol stream -> possible intermediate script/conlang/formula layer
```

The hypothesis is worth preserving because Jekhr provides an explicit
Tibia-native example of:

```text
written symbols -> Latin transcription/pronunciation -> vocabulary/meaning
```

It remains weak for 469 because the accepted book-layer tests already classify
row0 as non-linguistic and mechanically assembled. Future work may only test
whether row0 behaves more like a script/control family than like direct
English/German/plaintext.

Required future tests:

| Test | Stop rule |
|---|---|
| known-language recovery benchmark | Must recover known controls before touching 469 |
| 469 intermediate-script audit | Must beat conlang, shuffle, and gibberish controls |
| 469-to-Tibia-conlang match | Must improve MDL and survive held-out books |
| spell/keyword formula control | Phrase-layer only, not book-layer promotion |
| community translation validator | Labels claims; does not promote them |

No current result passes those future tests because full corpora have not been
assembled and no official 469 semantic ground truth exists.
