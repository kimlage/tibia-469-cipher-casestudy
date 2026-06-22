# E1 — GroundTruth / KeyTable Audit (primary workbook `iter129`)

Date: 2026-06-21
Classification: `AUDIT_ONLY_NO_SEMANTICS`
Translation delta: `NONE`
Row0 origin: `POSITIVE_EVIDENCE_FOR_HAND_BUILT` (placement indistinguishable from constrained-random)
Plaintext claim: `False` · Case reopened: `False`

Backlog item **E1** (do plano [docs/plans/2026-06-21_avaliacao_e_plano_formula.md](../../../docs/plans/2026-06-21_avaliacao_e_plano_formula.md)): *minerar `bonelord_469_iter129.xlsx` (`GroundTruthSources_*`, `KeyTable`, `ExternalGroundTruthCheck`) atrás de provenance/ordem de fill que prediga a colocação de row0.* Era o lead de maior EV do projeto e nunca havia sido lido. Executado via DB operacional read-only (`data/bonelord_operational.sqlite`, sheets = tabelas `sheet__*`). Reprodutível: [scripts/e1_keytable_structure_audit.py](../scripts/e1_keytable_structure_audit.py).

---

## Pergunta e veredito

**A planilha primária contém a receita de construção de row0 (uma ordem, uma sequência de fill, uma fonte externa, um mapa pré-projeto)?**

**Não.** A planilha armazena a **tabela acabada** (`sheet__keytable`, o grid 10×10 que É o row0 canônico) mas **nenhum registro de como ela foi construída**. As abas "GroundTruth" são **registros de validação de decode externo** (wikis/fóruns da comunidade), não provenance autoral. Uma varredura de nomes de tabela por `order/seed/charset/keyboard/alphabet/fill/origin/provenance/sortorder/glyph/sprite/construct` retornou **nada** (só `anchor*`, que são códigos-âncora do corpus).

→ A hipótese "talvez fonte externa / ordem externa" para row0 passa de **`BLOCKED/não-testado`** para **`buscado-negativo no artefato primário`**. Isso **fortalece o veredito hand-built** e fecha (negativamente) o lead de maior EV.

**Bônus (a parte que vale mais):** a tabela acabada estava materializada e foi interrogada diretamente. A estrutura dela é **evidência positiva de construção manual, frequency-seeded** — o teste discriminador A3/A4 do plano, executado no objeto real.

---

## O que as abas contêm (E1 literal)

| Aba (tabela) | Linhas | O que é | Relevância para origem de row0 |
|---|---:|---|---|
| `sheet__keytable` | 10 | **O grid 10×10 row0** (row, c_0..c_9) | **É o próprio row0** — objeto, não recipe |
| `sheet__digitcodemap_auto` | 99 | mapa código→letra + contagens | confirma 99/99 contra o KeyTable |
| `sheet__groundtruthsources_v121/v122/v129` | 5/10/21 | listas de **fontes externas** (TibiaSecrets, TibiaWiki, s2ward/469, A Wrinkled Bonelord, entrevista Chayenne, Avar Tar…) | validação de decode, **não** provenance |
| `sheet__externalgroundtruthcheck_v120` | 2 | **2 cribs de frase atestadas**, ambas `pass=TRUE`: `"be a wit than be <*> fool!"`, `"you've through so yet far away"` | camada de **frase** (word-code), não de livro/tabela |
| `sheet__externalvalidation_v129` | 11 | 11 strings numéricas externas com fontes verificadas (3478, 486486, poll 2020, Hellgate books…) | âncoras externas; nenhum par número↔significado oficial novo |
| `sheet__groundtruthpolicy_auto` | 16 | política de crib (enforced/tier) | metas de validação; crib 7 = `469 -> FOOL via FV anagram` (camada interpretação) |

Nenhuma dessas abas descreve ordem de símbolo, sequência de preenchimento, charset/glyph, ou mapa pré-existente.

---

## Análise estrutural rigorosa do KeyTable (o row0 real)

Grid reconstruído (code `rc` = row r, col c):

```
    0 1 2 3 4 5 6 7 8 9
 0  * N R V F T I I I T
 1  N E F N A E T V I I
 2  R F A O L I N S T N
 3  V N O E B L V A T N
 4  F A L B E F N E E N
 5  T E I L F V I E E I
 6  I T N V N I E A C V
 7  I V S A E E A N E A
 8  I I T T E E C E A T
 9  T N N N N I V A T E
```

| Teste | Resultado | Leitura |
|---|---|---|
| Consistência KeyTable↔mapa | **99/99**; único código não-usado = `39` (definido como N, nunca aparece nos 70 livros) | KeyTable é o row0 canônico, completo (100 células) |
| **T1 — simetria (par não-ordenado)** | **44/45** puras; única assimetria **`19=I` vs `91=N`** | tabela é lookup simétrico com **um único "slip"** (I e N são os 2 símbolos de maior inventário) |
| T2 — diagonal | `* E A E E V E N A E`; **E=5/10** | leve hábito diagonal-E |
| **T3 — órbita 6↔9** | **20/36 (0,56) preservadas na grade crua** | **FRACO** — contradiz o "p~0,001 robusto" documentado; ver reconciliação |
| **T4 — inventário vs frequência** | **Pearson 0,917** (100 células); Spearman 0,890 (55 slots) | inventário ~ derivável da frequência interna (insight A2 confirmado) |
| **T5 — feature → símbolo** | `unordered_pair` 0,990 (= a própria simetria); todo o resto fraco (product 0,73 = memorização, digit_sum 0,44, row/col 0,27) | **nenhuma regra de coordenada** explica a colocação |
| **gate canônico** | log2(55!/Πk!) = **157,5 bits** (doc cita 160,521 — ~3 bits de diferença, reconciliar) | custo de arranjo do multiset conhecido |
| **A2 — inventário por frequência** | modelo proporcional erra L1=**14/55** | metade da especificação de row0 (o multiset) é largamente frequency-determinada |

### O teste decisivo — placement-dado-restrições é aleatório

Null de permutação preservando **multiset + simetria** (embaralha os 55 rótulos de slot, N=20.000):

| Estatística de textura | Observado | Null (média±sd) | p(≥obs) |
|---|---:|---:|---:|
| Arestas de mesmo-símbolo adjacente | 22 | 18,8 ± 5,6 | **0,334** |
| Concentração símbolo-por-linha | 27 | 27,1 ± 1,8 | **0,624** |

**Duas estatísticas independentes: a colocação dos símbolos nos 55 slots é estatisticamente indistinguível de um preenchimento aleatório**, uma vez condicionada nas duas coisas que já conhecíamos (simetria de par não-ordenado + inventário por frequência). O único resíduo fraco é diagonal-E (p=0,020), que o paid-anchor gate do projeto já mostrou colapsar a negativo quando se cobra o custo de *nomear* o rótulo.

---

## Conclusões

1. **E1 (provenance) = negativo no artefato primário.** A planilha não contém recipe/ordem/fonte de row0. O lead de maior EV está fechado: não há fórmula escondida na planilha.
2. **Evidência POSITIVA de hand-built (o ganho real).** O row0 é consistente com **tabela feita à mão, frequency-seeded, simétrica em pares não-ordenados, com um único slip de keying (`19/91`) e um leve hábito de E na diagonal**. Dado isso, a colocação off-diagonal é constrained-arbitrary — **não há fórmula sub-lookup a encontrar porque a placement é aleatória-dadas-as-restrições**. Isto re-enquadra `row0_origin_frontier_saturated_current_corpus` de "busca exausta sem achar fórmula" para "**evidência positiva de que nenhuma fórmula existe além de {simetria + inventário-por-frequência + 1 slip}**".
3. **Reconciliação a registrar.** A órbita 6↔9 é **fraca na grade crua (20/36)**, contradizendo o "p~0,001" documentado — exemplo concreto do over-claim sinalizado em §3.3 do plano. O gate canônico recomputa para 157,5 bits (vs 160,521 citado) — diferença de convenção de slot/label a reconciliar.

## Impacto no Outcome Ledger

- **Métricas semânticas:** inalteradas (0/0/0-de-70/0). Nenhum par número↔significado oficial novo.
- **Sob o Outcome Ledger *gerativo* (proposto em F0-1):** este é um **negativo pré-registrável que fecha uma frente** — resultado válido e honrado, não esteira de bits. A questão A muda de "aberta/saturada" para "**resolvida como hand-built constrained-random; vitória futura só por evidência documental (entrevista/charset) externa**".

## Próximos passos derivados

- **A2 (promover):** o inventário é frequency-determinado (L1=14/55) — formalizar `homophone_count ≈ f(freq)` e creditar o multiset como derivado, baixando o custo livre de row0 ao termo de arranjo (~157 bits), que esta auditoria mostra ser arbitrário.
- **E5/E3 agora são a única rota A:** já que o artefato primário não tem provenance, só uma **declaração do autor (entrevista)** ou um **charset/ordem externa pré-datada** pode mover row0. E2 (Tibia.pic) permanece o único caminho que poderia *derivar* row0 de asset externo.
- **Fechar a frente de busca-de-fórmula row0 interna** com este resultado como o negativo pré-registrado (em vez de mais brute-force).

## Fontes

- [scripts/e1_keytable_structure_audit.py](../scripts/e1_keytable_structure_audit.py) — auditoria reprodutível (determinística, DB read-only).
- DB: `data/bonelord_operational.sqlite` → `sheet__keytable`, `sheet__digitcodemap_auto`, `sheet__groundtruthsources_v121/122/129`, `sheet__externalgroundtruthcheck_v120`, `sheet__externalvalidation_v129`, `sheet__groundtruthpolicy_auto`.
