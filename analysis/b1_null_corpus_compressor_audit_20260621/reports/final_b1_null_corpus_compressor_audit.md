# B1 — Null-corpus + Generic-compressor Control (Fórmula B)

Date: 2026-06-21
Classification: `AUDIT_ONLY_NO_SEMANTICS`
Translation delta: `NONE`
Verdict: `FORMULA_B_IS_MESSAGE_FREE_COPY_ASSEMBLY` · bit-sweep = compression treadmill (quantificado)
Plaintext claim: `False` · Case reopened: `False`

Backlog item **B1**: testar se o bound bespoke (~8.154 bits) é especial, ou se (a) um compressor off-the-shelf alcança a mesma description-length e (b) um processo de montagem *message-free* reproduz o copy-fraction do corpus. Reprodutível: [scripts/b1_null_corpus_compressor_audit.py](../scripts/b1_null_corpus_compressor_audit.py).

---

## TL;DR

1. **Um compressor genérico quase empata o bound bespoke.** `brotli -q11` = **8.384 bits** (só **+230** vs 8.154,68); raw lzma2/deflate sem header = **8.776/8.792 bits** (+621/+637). Os ~150 scripts e ~324 commits do bit-sweep ganharam **~230 bits** sobre uma chamada de uma linha — e **zero** desse ganho marginal é uma regra de autoria recuperada (é codificação de entropia mais apertada dos mesmos canais declarados). **Treadmill quantificado.**
2. **Copy-fraction é reproduzível por montagem message-free.** Um null de "banco-de-módulos + cópia" (sem mensagem) atinge **copyfrac 0,911 ≈ 0,930** do real. O alto copy-fraction — fato central sobre o qual toda a Fórmula B foi construída — **não é evidência de mensagem nem de algoritmo autoral especial**.
3. **O mecanismo é copy-paste de passagens longas e verbatim.** **20/70 livros estão inteiramente contidos em um único outro livro**; 26/70 são substring exato da concatenação dos outros 69; 35 cópias têm ≥100 dígitos (média 39,1, **máx 303**). Isto é copy-paste humano de passagens, não uma função geradora fina.

→ A "fórmula dos livros" é: **um banco de passagens pré-existentes, montadas por copy-paste, com resíduo literal curto e quase-incompressível.** Não há função fechada escondida; o conteúdo autoral irredutível é pequeno (~144 dígitos de seed do book-0 + ~791 dígitos literais ≈ 8%), consistente com o veredito "sem mensagem".

---

## Resultados

### Parte 1 — compressores genéricos vs bespoke

| Modelo | bits | bits/dígito | Δ vs bespoke |
|---|---:|---:|---:|
| raw uniforme (sem modelo) | 37.415 | 3,322 | +29.260 |
| **brotli -q11** (com header) | **8.384** | 0,744 | **+230** |
| zstd -22 (com header) | 8.592 | 0,763 | +437 |
| raw lzma2 (headerless) | 8.776 | 0,779 | +621 |
| raw deflate (headerless) | 8.792 | 0,781 | +637 |
| **bespoke (page-18)** | **8.154,68** | **0,724** | — |

Leitura honesta: ~77% da compressão total (37.415 → ~8.800) sai de **uma linha** de compressor genérico. O esforço bespoke inteiro adiciona ~3–8% a mais (→ 8.154) — e essa fração marginal **não corresponde a nenhuma dependência derivada** (0/5; ~50% do recipe ainda é declarado). O bit-ladder mede aperto de codificação, não descoberta de processo.

### Parte 1b — modelo local puro (Markov), sem modelo de cópia

| Ordem | bits | bits/dígito |
|---|---:|---:|
| 0 | 36.818 | 3,269 |
| 1 | 33.262 | 2,953 |
| 2 | 24.454 | 2,171 |
| 3 | **19.665** | **1,746** |
| 4 | 19.299 | 1,714 |
| 5 | 19.763 | 1,755 |

Estatística local sozinha satura em **~19.300 bits (1,71/díg)**. Para descer a ~8.154 é preciso o **modelo de cópia cross-book** — ou seja, o templating cross-book é real e carrega ~11.000 bits da compressibilidade. Mas é **templating (copy-paste)**, não linguagem.

### Parte 2 — copy-fraction: real vs nulos message-free (parse LZ greedy idêntico, min_len=6)

| Corpus | copy-fraction | crude-MDL (bits) |
|---|---:|---:|
| **REAL** | **0,930** | 9.181 |
| IID-uniforme | 0,030 | 48.262 |
| Markov-ordem2 | 0,670 | 36.774 |
| **SharedBank-copy (message-free)** | **0,911** | 20.585 |

- IID ~0,03: aleatório não tem matches longos.
- Markov-ordem2 ~0,67: estatística local já produz muitos 6-grams casados, mas fica abaixo do real.
- **SharedBank ~0,91 ≈ real 0,93**: um gerador message-free de banco-de-módulos reproduz o copy-fraction. (O MDL do SharedBank é maior porque meu banco usa módulos curtos 5–18; o real usa cópias **mais longas** — ver abaixo — o que o torna *mais* templado que meu null, reforçando "copy-paste de passagens inteiras".)

### Parte 2 — estrutura de cópia do REAL (a impressão digital do mecanismo)

- 268 cópias, 791 literais, 10.472 dígitos copiados (0,930).
- comprimento de cópia: min 6, **mediana 16, média 39,1, máx 303**; **62 cópias ≥50, 35 cópias ≥100**.
- **26/70 livros** são substring exato da concatenação dos outros 69.
- **20/70 livros estão inteiramente contidos em UM único outro livro** (ex.: book 0 ⊂ book 10, book 1 ⊂ book 10, book 12 ⊂ book 21, book 32 ⊂ book 58…).

Cópias longas e verbatim de passagens/livros inteiros = **copy-paste em editor de texto**, não um algoritmo gerador fino nem um codificador de mensagem.

---

## Gaps e insights

**Metodológico (gap real do projeto):** o controle B1 — compressor genérico + null message-free — **nunca foi rodado** em ~150 scripts. O Outcome Ledger pegava falsos positivos no *portão de promoção* mas nunca *benchmarkou o empreendimento inteiro* contra um baseline trivial. Resultado: o bit-ladder esteve ~empatando uma chamada de `brotli` o tempo todo, sem ninguém medir isso. **Recomendação:** qualquer claim de compression-bound deve reportar o baseline de compressor genérico e o ganho marginal sobre ele — caso contrário "8.154 bits" soa como descoberta quando é codificação de entropia.

**Mecânico (a fórmula, de fato):** Fórmula B ≈ **banco de passagens compartilhado + copy-paste + resíduo literal curto**. A impressão digital concreta: 20/70 livros 100% dentro de outro, 35 cópias ≥100 dígitos, máx 303. O núcleo autoral irredutível é o **seed do book-0 (144 dígitos)** + os ~791 dígitos literais (~8% do corpus), que são quase-incompressíveis (consistente com "sem mensagem"). A questão "qual a ordem/fonte das cópias" que o projeto perseguiu por 3.003 bits é **secundária e em larga parte um artefato de qual ocorrência-mais-cedo o parser escolhe** — não um canal de informação autoral.

**De lore (ponte):** este mecanismo bate com a lore "Great Calculator / assemble" e com a evidência Chayenne 2009 (cobertura 0,918 — passagens do corpus remontadas), e com "20/70 books são substrings" já notado no relatório final. O que B1 acrescenta: o processo é reproduzível por um gerador **sem mensagem**, então a lore "assemble" descreve um **método de fabricação**, não um canal semântico.

## Impacto no Outcome Ledger

- Métricas semânticas: inalteradas (0/0/0-de-70/0).
- Sob o Ledger *gerativo* (F0-1): **B1 fecha a frente B como auto-similaridade message-free** — negativo pré-registrável e válido. A Fórmula B está **mecanicamente explicada** (copy-paste de banco); o que resta é o seed/cold-start irredutível (~8%) e a constatação de que o bit-sweep adicional é negative-EV.

## Próximos (derivados)

- **Parar** o bit-sweep sub-bespoke: ele compete com `brotli`, não recupera autoria.
- B2/B3 (copy-source/literal collapse) só valem como *quantificação do resíduo irredutível*, não como busca de regra geradora.
- A única pergunta autoral viva da Fórmula B — "de onde veio a primeira passagem do banco (o seed)?" — coincide com seed_primacy (sem subset especial) → é o book-0 + literais, conteúdo autoral bruto, provavelmente sem mensagem.

## Fontes

- [scripts/b1_null_corpus_compressor_audit.py](../scripts/b1_null_corpus_compressor_audit.py) — reprodutível, determinístico.
- Dados: `analysis/audit_20260609/books_digits.json` (70 livros, 11.263 dígitos).
