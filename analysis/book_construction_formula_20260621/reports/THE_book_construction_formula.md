# A Fórmula Completa de Construção dos Livros (Fórmula B)

Date: 2026-06-21
Classification: `MECHANICAL_FORMULA_VERIFIED_70_70` · `AUDIT_ONLY_NO_SEMANTICS`
Translation delta: `NONE` · Plaintext claim: `False`
Reprodutível: [scripts/book_construction_formula.py](../scripts/book_construction_formula.py) (roundtrip 70/70 assertado)

> "Fórmula", aqui, é um **gerador determinístico verificável** que reproduz os 70 livros **byte-exato**, mais a separação honesta entre o que é **regra derivável** e o que é **input autoral irredutível**. Não existe uma função fechada `f(k)→livro` mais curta que isto, e a seção 5 prova por quê.

---

## 1. Objetos

- **Alfabeto:** dígitos `0–9`.
- **Stream:** `S` = concatenação dos 70 livros na ordem operacional (`book_0 ++ book_1 ++ … ++ book_69`), `|S| = 11.263` dígitos.
- **Camada de linguagem (separada, já dada):** a tabela `row0` 10×10 mapeia cada par de dígitos `rc` → 1 de 14 símbolos (ver E1). A Fórmula B opera sobre os **dígitos**; row0 só é aplicada depois, para *ler* os símbolos.

## 2. A fórmula (o gerador)

```python
MIN_LEN = 6   # única constante

def generate(ops):           # recipe -> stream (decoder)
    out = []
    for op in ops:
        if op[0] == 'L':                 # literal: emite 1 dígito
            out.append(op[1])
        else:                            # cópia: ('C', source_pos, length)
            _, p, L = op
            out.append("".join(out)[p:p+L])   # copia de material já emitido
    return "".join(out)
# os livros são generate(ops) cortado pelos book_lengths.
```

A **recipe** (`ops`) é derivada de `S` por uma regra determinística (encoder):

> Em cada posição, se os próximos `≥6` dígitos já ocorreram antes em `S`, **copie o match mais longo, da ocorrência mais cedo**; senão, emita um **literal**.

A recipe é uma **função pura de (`S`, `MIN_LEN`)** — não há busca, não há escolha estocástica.

## 3. Prova de completude — roundtrip 70/70

`generate(parse(S))` == `S` byte-a-byte, e o split por `book_lengths` reproduz **70/70 livros byte-exato**. (Assertado no script.) A fórmula é **completa e correta**: não falta nada para reconstruir o corpus inteiro.

## 4. A recipe e a conta de materiais

| Item | Valor |
|---|---|
| Operações totais | **1.059** = **268 cópias** + **791 literais** |
| Dígitos por cópia | **10.472 / 11.263 = 93,0%** |
| Dígitos literais | 791 = 7,0% |
| Comprimento de cópia | min 6 · média 39,1 · **máx 303** |
| Fontes de cópia canônicas (ocorrência mais cedo) | **268/268** |

**Conta de materiais (ledger simples, não-tunado):**

| Canal | bits | natureza |
|---|---:|---|
| stream de op-type (cópia/literal) | 1.059 | **input** (não previsível para frente) |
| fontes de cópia | 3.122 | **input do decoder** (encoder: = mais-cedo) |
| comprimentos de cópia | 2.372 | **input** (longest-match olha o futuro) |
| payload literal (791 dígitos) | 2.628 | **input autoral** |
| book lengths (70 números) | 1.028 | **input** |
| **TOTAL** | **10.209** | (o projeto tunou para ~8.154 via codificação de entropia) |

A regra **gera 93% dos dígitos de graça**; os ~10.209 bits (tunados a ~8.154) são o **input** que a regra não deriva.

## 5. O que é REGRA vs INPUT — e por que não há função fechada

- **Regra (0 bits, derivável):** o mecanismo de cópia; as fontes são **canônicas = ocorrência mais cedo** (regularidade encoder-side, 268/268); `target_start`, op-type-por-forma e parte dos comprimentos são deriváveis da forma/posição.
- **Input irredutível (~50% dos bits):** as **fontes de cópia** (~3.122 bits) continuam **dependência do decoder** — para copiar, o decoder precisa saber *de onde*, e "ocorrência mais cedo" exige já ter o trecho copiado (circular). Mais: op-type e comprimento dependem do **futuro** do stream (longest-match), então são gravados, não previstos. Isto — a **circularidade target-aware** — é a prova de que a recipe é uma **lista**, não uma função: um gerador forward não consegue decidir copiar/literal sem já conhecer a saída.

### 5b. Confirmação independente (commits do Codex, 2026-06-21)

Um agente paralelo (Codex) atacou exatamente a derivabilidade da recipe e chegou ao mesmo limite, com números:

- **`generation_boundary_closure_audit`**: `0/5` geradores promovidos; piso de `593` unidades materializadas; **`operation_skeleton` é o primeiro bloqueador**. = "a recipe é uma lista, não uma função".
- **`skeleton_decoder_ambiguity_audit`**: mesmo **concedendo o skeleton exato**, o decoder precisa de **3.434,227 bits** de escolha irredutível (`10^1033,8` opções) = source-branching `2.550,594` + literal-payload `883,633`. "Não pode virar regra de geração sem reintroduzir acesso ao texto-alvo." **Esta é a prova numérica da seção 5** (circularidade target-aware).
- **`target_conditioned_source_collapse_audit`** (commit mais recente): *dado o chunk-alvo*, a fonte de cópia **colapsa para a ocorrência mais cedo em 200/208** (8 exceções), codificável em **só 58,085 bits** (p<0,0001 vs aleatório) — vs 2.550,594 naïve. Conclusão: a escolha de fonte é **target-conditioned** (precisa do conteúdo copiado), logo **downstream do mecanismo de target-stream, não um bloqueador primário independente**.
- Geradores de **op-type-sequence, op-count, op-length (Markov/motif/cutpoint/recursive-partition)** e **literal-payload-reference-subcodec**: **todos rejeitados** (0/5 holdout). O op-stream não é derivável.

> **Reconciliação dos dois números (importante):** "fonte = earliest" é **forte e confirmado** — 200/208 (58 bits dado o alvo). O "78/208" de `skeleton_decoder_ambiguity` é uma medida *diferente* (cópias com fonte *única*); os 232,9 bits são o custo *oracle-rank* se você **não** usa a regra earliest. Ambos concordam no essencial: a fonte é **canônica encoder-side (earliest) mas target-conditioned** — não decodável forward. O bloqueador real **não é** copy-source; é o **target-stream** (o próprio conteúdo dos livros), que circula de volta para: os livros são seu próprio conteúdo, não há mensagem separada gerando-os.

## 6. O núcleo autoral irredutível

Removendo toda cópia mútua (cada livro pode copiar de qualquer outro), restam **170 / 11.263 dígitos = 1,5%** que aparecem em **nenhum outro lugar** do corpus. **53/70 livros são montagem pura** (zero conteúdo novo). O cold-start do `book_0` = 144 dígitos.

→ Todo o "conteúdo autoral" do corpus de 70 livros cabe em **~170 dígitos (≈85 símbolos)**. É aqui — e só aqui — que qualquer mensagem teria que viver.

## 7. A fórmula, em uma frase

> **Cada livro é montado colando, da esquerda para a direita, a passagem ≥6-dígitos mais longa já disponível em tudo que foi escrito antes (da ocorrência mais cedo); onde não há passagem disponível, digita-se um literal. O corpus inteiro é gerado assim a partir de um núcleo-semente de ~170 dígitos.** Verificado: 70/70 byte-exato.

Isto é montagem por copy-paste a partir de um banco compartilhado — coincide com a lore in-game ("the great calculator … assemble the bonelords language", E5), com a estatística (93% cópia, 20/70 livros 100% dentro de outro, B1), e é **message-free** (o núcleo de 170 dígitos não tem estrutura recuperável; veredito não-linguístico).

## 8. Limite (honesto)

A fórmula é **completa como procedimento + recipe** e está **provada (70/70)**. O que **não** existe é uma fórmula mais curta que a recipe: a circularidade target-aware (seção 5) e o núcleo irredutível (seção 6) garantem que os ~170 dígitos-semente + as escolhas de cópia são **input autoral**, não output de regra. Derivá-los exigiria a mensagem (que toda evidência diz inexistir) ou ground-truth oficial (que o E5 indica inexistir publicamente). **A fórmula para nos 170 dígitos — esse é o fim, não um insight faltando.**

## Fontes

- [scripts/book_construction_formula.py](../scripts/book_construction_formula.py) — gerador + prova 70/70 + conta de materiais (determinístico).
- Dados: `analysis/audit_20260609/books_digits.json`.
- Contexto: [B1](../../b1_null_corpus_compressor_audit_20260621/reports/final_b1_null_corpus_compressor_audit.md) · [E1](../../e1_groundtruth_keytable_audit_20260621/reports/final_e1_groundtruth_keytable_audit.md) · [E5](../../e5_author_method_lore_audit_20260621/reports/final_e5_author_method_lore_audit.md).
