---
title: "469 — Avaliação completa e plano/backlog para a fórmula de criação (linguagem + livros)"
date: 2026-06-21
status: ready_to_execute
scope: evaluation_plan_backlog_generation_and_row0_origin
translation_delta: NONE
method: multi_agent_audit (12 leitores + 5 críticos adversariais + 3 geradores de insight + síntese)
supersedes_context: docs/plans/2026-06-19_lore_evidence_mechanical_parallel_plan.md
canonical_bound_note: "bound de compressão aparece como 8154.68/8177.32/8343.06/8558.67 em docs diferentes; reconciliar (ver F0-2)"
---

# Avaliação Completa e Plano — Fórmula de Criação da Linguagem e dos Livros (469)

*Auditoria do projeto reaberto. Lente: Outcome Ledger (atividade ≠ progresso). Data: 2026-06-21.*

> **Como este documento foi produzido.** Auditoria multi-agente de todo o repositório (18 páginas de wiki, 22 diretórios de análise, ~150 scripts, o relatório final): 12 leitores profundos + 5 críticos adversariais + 3 geradores de insight + uma síntese. Os números abaixo foram re-derivados contra o DB ao vivo e os JSONs de resultado; pontos de inconsistência entre artefatos estão sinalizados (não corrigidos silenciosamente).

---

## 0. TL;DR — onde estamos e o veredito honesto

- **Há duas fórmulas, não uma.** (A) a **LINGUAGEM** = a tabela `row0` que mapeia código-dígito → 14 símbolos (concretamente as ~55 células de pares não-ordenados); (B) os **LIVROS** = a receita de montagem por cópia LZ que reconstrói os 70 livros byte-exato. Elas são problemas **evidencialmente separados** e devem ser tratadas como tal o tempo todo.

- **Fórmula B — progresso ESTRUTURAL real, progresso SEMÂNTICO/GERATIVO zero.** O gerador LZ sequencial reconstrói **70/70** livros byte-exato, copiando ~10.451–10.490 de 11.263 dígitos de material já emitido. O *bound* de descrição caiu de **17.753,5 → ~8.154,7 bits**. Mas **0/5** dependências (copy-source, copy-length, literal-payload, seed/book-0, ordem) foram promovidas a gerador derivado; **~4.272,8 de 8.558,7 bits (49,9%)** continuam sendo *recipe fixo/declarado*, não aprendido. O *bound* menor **não é** progresso semântico.

- **Fórmula A — congelada, sem movimento real desde 2026-06-18.** O melhor candidato de regra recupera **21/55** células, a **1,935× o custo de lookup** (ou seja, *pior* que armazenar a tabela). O *gate* canônico é **160,521 bits** (multinomial do multiset de rótulos). O melhor sinal estrutural genuíno (órbita 6↔9) fica em **205,837 bits — 45,3 bits ACIMA do gate**. `row0_origin_frontier_saturated_current_corpus` é honesto *como afirmação sobre busca algorítmica*, mas **superdeclarado como afirmação sobre origem**.

- **O maior risco epistêmico: a esteira de compressão (treadmill) disfarçada de rigor.** ~324 commits em ~2 dias, ~529 scripts, dezenas de *gates* com ganhos sub-1-bit (alguns **sub-0,001 bit**: passes de substituição de fonte a +0,000671 / +0,000503 / +0,000310 bits). O Outcome Ledger foi criado para matar exatamente esse padrão; aqui ele foi *honrado no portão de promoção* (0/5 promovidos) mas *violado na alocação de atenção* (o contador de bits virou proxy de progresso de fato).

- **Circularidade central da Fórmula B.** Source, length e segmentação são todos **target-aware**: o *parser* precisa do texto-alvo para escolher a fonte ("earliest-match" exige conhecer o trecho a copiar). Isso é um **compressor/encoder**, não um **gerador/decoder**. Provar que a receita é *redundante dado o texto* (o reparse online, −215,6 bits, 175/175 roundtrips de sufixo) é real e não-trivial — mas é **categoricamente distinto** de provar que o texto foi gerado por essa receita.

- **A "ordem numérica" é o melhor ajuste de compressão (+188,58 bits raw sobre o melhor rival), mas NÃO é autoral.** 0 cutoffs prequenciais ordem-específicos a p≤0,05; conjuntos de treino aleatórios batem o prefixo numérico (p~1,0); a vitória do reparse (130) é um **artefato mecânico** da disponibilidade sequencial de inventário de cópia. "Melhor-ajuste ≠ autorado."

- **O "seed books 0-9" foi FALSIFICADO como especial.** Sentam no **percentil 21** de seeds aleatórias (−1.132,8 bits vs mediana). O verdadeiro piso irredutível é o **cold-start do book-0 (144 dígitos não-copiáveis)** + ~266 literais residuais quase-incompressíveis (883,6 bits raw, só 7,0 bits de estrutura de histograma) — consistente com o veredito "sem mensagem" visto agora pelo lado da geração.

- **A única destrava real é externa (CipSoft).** Tanto A quanto B têm **assinaturas negativas convergentes**: ambos saturam bem abaixo do lookup e falham holdout/família. Isso é consistente com **montagem manual, target-aware** — "a fórmula é uma pessoa com uma planilha e o hábito de copiar-colar", não uma função fechada. A condição de vitória realista para A é **documental/provenance**, não um bit-count menor.

- **Recomendação central.** **PARE** o bit-sweep e a brute-force de row0 (ambos saturados/mis-scoped). Redirecione todo o esforço para três coisas: (1) **controles decisivos jamais rodados** (corpus-nulo, compressor genérico off-the-shelf, holdout cego de descoberta-de-receita); (2) **provenance externa** (a planilha in-repo `bonelord_469_iter129.xlsx` com `GroundTruthSources_*`, as entrevistas do autor, a rota Tibia.pic/charset); (3) **collapses de dependência baratos e derivados** (min-match length → literal-payload; length+history → copy-source; frequência → tamanho de inventário homófono). Pré-registre um **Outcome Ledger gerativo com stop-rule** antes de qualquer nova busca.

- **Bottom line.** O projeto tem um **substrato mecânico sólido** e **disciplina anti-pareidolia exemplar no portão**, mas confundiu um contador de bits descendente com progresso em direção à fórmula autoral. Os dois desconhecidos genuinamente autorais — a regra de rótulo de row0 e a origem do seed/cold-start — moveram **exatamente zero**.

---

## 1. O substrato sólido (o que qualquer fórmula precisa reproduzir)

Estes fatos foram re-derivados byte-a-byte do DB ao vivo e dos JSONs; são os pontos fixos. Qualquer fórmula candidata para A ou B é obrigada a reproduzi-los.

**Forma do corpus.** 70 livros · **11.263 dígitos brutos** · **5.729 símbolos decodificados** · alfabeto de **14 símbolos** = 13 letras latinas `{A,B,C,E,F,I,L,N,O,R,S,T,V}` + a máscara `*` (código `00`). Letras *ausentes*: D,G,H,J,K,M,P,Q,U,W,X,Y,Z.

**O mapa código→símbolo (99→14).** Exatamente **99 códigos** mapeados, **0 ambíguos**, único código de 2 dígitos não-usado = **`39`**. Geometria de reversão-invariante: dos 88 códigos não-palíndromos cujo reverso está presente, **86 mapeiam ao mesmo símbolo**; **54/55** classes de par não-ordenado são puras. O **único conflito direcionado** é `{1,9}`: `19→I` mas `91→N`. Células mortas `32/33/38` = 1 ocorrência cada. Esta é a impressão digital de uma **tabela de lookup construída à mão sobre o par não-ordenado** (acurácia de feature `unordered_pair` = **0,990**, vs `digit_sum` 0,444, `row` 0,273, `column` 0,263) — mata teorias de checksum/raiz-digital/aritmética.

**70/70 — precisa de re-enunciado honesto.** O "70/70 byte-exato" é verdadeiro **apenas em sentido fraco**: o decode depende de um *parse* escolhido externamente. (a) **20/70** parses são não-únicos (50 únicos / 20 múltiplos / 0 nenhum por DP independente); (b) as posições de zero-omitido efetivamente gravadas (`sheet__booksdigitmodel_v118.omitidxs_1based`) **não regeneram** o decode (naive 0/70, padded 4/70 — o próprio `audit_recon.out` imprime "full reconstruction OK: 0/70"); (c) a tabela canônica que carregava o parse (`row0_code_symbol_probe_books`) **não existe mais no DB operacional**. O honesto: *"dado um parse escolhido, todos os 70 decodes são consistentes com o mapa"* — consistência interna, **não** reconstrução derivada. O parse de zero-omitido (195 omissões) é um **grau de liberdade autoral não cobrado**.

**Âncoras B/E/A (a ponte de duas-cifras).** `34/43→B`, `78/66→E`, `67→A`; phrase `'be'` = `34|78` = B+E. A camada de frase mapeia códigos→**palavras**; a camada de livro mapeia as mesmas âncoras→**letras**. O mapa foi plausivelmente semeado de poucas âncoras-letra e preenchido homofonicamente (E tem 17 códigos, A tem 10, B tem 2) — e o **tamanho do inventário homófono acompanha a frequência do símbolo** (Pearson 0,895, p=5e-5).

**Os 5 (na verdade 3 eixos) desqualificadores não-linguísticos** (mantidos no resíduo deduplicado de 995 símbolos):
1. **Perfil de frequência** abaixo de qualquer língua: UNIFORM 0,654 < EN 0,806 < DE 0,908 < ES 1,778 (escala-livre). Per-símbolo: I~20,6% / E~17,6% / N~12,6% / F~10% / V~6,6% … R~0,6% / O~0,18% — **F/V hiper-enriquecidos, R/O quase-ausentes**, perfil anti-inglês.
2. **Lookup reversão-invariante** (86/88, 54/55) — propriedade de tabela, não de mensagem.
3. **Templating verbatim** (~82% dos dígitos são cópia cross-book; 995 símbolos novos = 17,4%).
4. **Substitution-solve = NULL** (sem solve crível; a "solução" alemã/MHG dá 100% de cobertura mas 0% nas cribs inglesas — o melhor exemplo anti-pareidolia do projeto).
5. **Power gap**: língua real pontua z~+9–10 no instrumento; o corpus pontua +1,3 a +3,0. Este é o braço decisivo.

> **Implicação para a síntese.** O alvo não é "achar o gerador oculto de um artefato significativo". É **reproduzir uma construção sem-mensagem**. O conteúdo informacional do artefato é genuinamente baixo. É legítimo que a resposta final seja um **negativo** ("não há descrição sub-lookup; é uma tabela feita à mão + montagem copy-paste").

---

## 2. Estado da Fórmula B — montagem dos livros (modelo LZ)

### 2.1 O gerador LZ (o que é, concretamente)

Concatenação em ordem numérica de 70 livros. Cada livro é parseado por LZ-DP de custo-mínimo em **cópias** (~92% dos dígitos) do stream global já-emitido + **runs literais** (~8%). Book-0 = seed literal de 128–144 dígitos. Inventário do perfil ativo: **348 ops** (261 copy + 87 literal por uma contagem; **283 copy / 85 literal / 773 literais / 10.490 copiados** por outra), ~857 dígitos literais, ~10.406–10.490 copiados.

> **Inconsistência a registrar (não cosmética):** os artefatos citam pelo menos dois inventários — `261 copy / 10.406 copiado / 857 literal` (projeção-skeleton, books 0-9 como seed) e `283 copy / 10.490 copiado / 773 literal` (perfil ativo full-corpus, verificado em `04_recipe_externality_audit.json`). E o *bound* "atual" aparece como **8.154,68 / 8.177,32 / 8.206,18 / 8.343,06 / 8.558,67** em documentos diferentes (page-09 cita 8.177; page-18 cita 8.154; a validação prequencial está ancorada em 8.558,67). **Escolha um número canônico e reconcilie** — a ambiguidade está ativamente escondendo o que está e o que não está resolvido.

### 2.2 A escada de bits (17.753 → 8.154): real como bound, parcialmente esteira

Âncoras (todas verificadas como monotônicas *como bound de compressão*): 17.753,5 (tape) → 10.190,0 (seq-LZ v1) → 9.823,3 (DP) → 9.596,5 (Rice-k4) → 9.073,3 (length ledger, −464) → 8.996,2 → 8.842,0 → 8.614,1 (bounded copy length, −189) → **8.558,667 (split-only, micro-sweep freeze)** → 8.343,062 (online reparse, −215,6) → 8.206,178 → 8.177,317 → 8.162,4 → … → **8.154,6763 (atual)**.

**Onde o ganho é real vs onde é esteira:**
- **Real (remoção honesta de campo):** book_length, copy target_start, literal length e op type são todos **DERIVADOS** (decodáveis da forma do campo / posição cumulativa / comprimento). Remoções lossless legítimas.
- **Defensável mas target-aware:** o reparse online (−215,6 bits, **maior drop sub-8558**) — prova redundância dado o texto, não geração.
- **Esteira pura:** abaixo de ~8.558, os ganhos são dominados por reparametrizações de eficiência de codificação (alfabetos default/exception, Rice vs truncated-binary, alphas adaptativos) de canais que **continuam declarados externamente**. Os passes de source-substitution rendendo 0,0003–2,06 bits e os ~14 scripts near-duplicados de repair-exhaustion (sizes 3-22, *todos* +0,9 a +23,7 *pior*) são bookkeeping pós-hoc.

### 2.3 Cada campo do recipe: decodável / derivado / declarado / exógeno

| Campo | Bits (~) | Status | Comentário honesto |
|---|---|---|---|
| op type | ~248 | **derivado** | book-start markov; OK |
| target_start | — | **derivado** | da posição cumulativa |
| copy length | ~1.348 | **decodável** | default `decoder_max_possible` bate só ~58/261; resto é stream de exceção (≈lista armazenada) |
| **copy source** | **~3.003** | **DECLARADO** | maior canal isolado (~37% do bound); 208 campos; default bate **5/261** → ~98% stream de exceção = lista de endereços disfarçada |
| **literal payload** | ~2.614 | **DECLARADO** | 53 chunks / 266 dígitos; quase-uniforme; 0/5 holdout |
| book_length | 566 | **declarado** (residual) | só lookup (70 células) dá 70/70; melhor policy 14/70 |
| book order | (332,5 free) | **declarado** | canonical retido, 0 cutoffs ordem-específicos |
| seed / book-0 | ~478 raw | **EXÓGENO** | 144 dígitos não-copiáveis; cold-start |

**O split aprendido/fixo (o número mais honesto do projeto), verificado em `04_recipe_externality_audit.json`:** de 8.558,667 bits → **4.285,876 aprendidos (50,08%)** / **4.272,791 fixos-não-aprendidos (49,92%)**. O *breakdown* fixo: **copy_address 3.284,79** + fixed_ledger 620 + literal_structure 368.

> **Alerta de double-counting.** Uma moldura alternativa "consolidated streams @8.177" reporta 7.157,3 bits = **87,5% aprendido** — mas isso conta o copy-**address** como stream aprendido. A auditoria de externalidade corretamente reclassifica copy-address no balde **FIXO**. **Cite 50/50, nunca 87,5%**, como a fração aprendida honesta. (As três contabilidades — 50/50 @8558, 87,5/12,5 @8177, 609 campos @8154 — nunca foram reconciliadas; isso deve ser feito.)

### 2.4 Validação prequencial e as FALHAS de holdout

- **Não generaliza como método autoral** — "partial predictive structure" apenas. Todo *gate* que reivindicaria o contrário é corretamente recusado.
- **A receita NUNCA é descoberta no holdout.** `04` admite: todo prefix-holdout *recebe a estrutura de receita do full-corpus antes de pontuar*. Só ~50% dos bits são prequencialmente pontuados; os outros 4.272,8 são **injetados, não preditos**. "Validação prequencial" valida 3 sub-modelos categóricos, **não um gerador**.
- **Baseline inflado.** "Bate raw 70/70" usa uniforme 3,32 bits/dígito — o pior nulo possível; provar que o texto é não-aleatório é algo que o projeto já sabia. **Nenhum holdout usa um nulo competitivo (Markov n-grama no treino).**
- **Holdouts de família FALHAM (real):** 3/19 famílias falham (bookcase_33 −2,966 / _8 −0,166 / _6 −0,395), todas famílias de 2 livros com 4-15 eventos — assinatura de overfitting. Um seletor train-only não as resgata; só um oráculo heldout.
- **Controle de treino aleatório (o resultado mais subdivulgado, e é NEGATIVO):** p(random ≥ observado) = **1,0** nos cutoffs 10/20/35; 0,96–0,98 nos cutoffs 50/60. Subconjuntos de treino aleatórios comprimem livros futuros **tão bem ou melhor** que o prefixo numérico.

### 2.5 Quanto do recipe é externalidade fixa

Piso de dependência explícito e fechado: **593 unidades materializadas** = 1 book_order + 70 book_lengths + 261 skeleton records + 208 copy sources + 53 literal chunks. **Geradores promovidos = 0/5** (verificado em `generation_boundary_closure_audit`). O núcleo exógeno irredutível dos LIVROS, reconciliado ao dígito, são **quatro coisas**: (i) cold-start de 144 dígitos não-copiáveis; (ii) seed de 1.696 dígitos (books 0-9, sem sinal de ordem autoral); (iii) atlas materializado de 261 ops sem gramática source-free (melhor 3/60 livros, +660 bits pior); (iv) ~266 literais quase-incompressíveis + ~79 bits de lookup residual-drift em 10 sítios.

> **Veredito Fórmula B.** Progresso **estrutural/mecânico genuíno** (70/70 roundtrip; ~50% derivado; segmentação efetivamente forçada dado o texto; reparse redundante). Progresso **semântico/gerativo: ZERO** (0/5 dependências derivadas; ~4.272 bits declarados; circularidade target-aware nunca quebrada; holdouts de família falham). O *bound* de 8.154 é um **bound de compressão**, não um método de autoria descoberto.

---

## 3. Estado da Fórmula A — a linguagem / row0

### 3.1 O objeto e o gate

A tabela tem **55 células** sobre **15 rótulos distintos** (E:11, N:8, I:7, T:6, A:6, V:5, F:3, L:2 + 7 singletons), entropia de rótulo 3,398 bits/célula. O **gate canônico de promoção é 160,521 bits** (verificado: `log2(55!/Πk_i!) = 160,5207`) — o custo de colocar o multiset de inventário *já conhecido* nas 55 células. Baselines mais fracos: 209,405 (alfabeto 14-símbolos), 214,879 (alfabeto 15-rótulos). **Qualquer fórmula de origem promovida precisa bater 160,521 após cobrar regra + parâmetros + exceções + ordem + custo-de-busca, E passar controles.**

### 3.2 Famílias de hipótese testadas e por que rejeitadas (~45-50 famílias, 82 scripts)

Por classe, *todas* abaixo de promoção:

- **Aritmética/algébrica:** deep_formula 0,495 acc; algebraic_composition 55/55 *só via 55 buckets* (=lookup-disguise); finite_group 55/55 @1,215×; direct_symbol 18/55.
- **Geometria/visual:** circle_1_to_0 28/55 (p=0,348); sevenseg_rotate180 53/55 majority mas **219,0 > 214,9** bits; keypad/clock/seven-seg todos sub-promoção.
- **Low-rank/latente:** bilinear 18/55 (LOO p=0,026 mas **14,931×** lookup); quotient 11/46.
- **Grafo/regra/predicado:** biclique 27/55; pair_rule_cover 34/55 (10 regras); symbol_predicate_dnf 44/55 **@4,592×**.
- **Inventário/quota/fill:** `pair_table_frequency_allocation` Pearson **0,895** nos *tamanhos* de classe (o clue de conteúdo mais forte); deterministic_apportionment L1=12.
- **Órbita 6↔9:** automorphism 47/55 preservado (p=0,033); robusto 51/55 (p até **0,0009**); quotient +3,6 bits. **Sinal real, não-gerativo.**
- **Permutação/seed/traversal:** **matrix_generator_exhaustive — 294.528 candidatos, MELHOR 21/55 @1,935×, TODOS lookup-disguise.** inventory_shuffle_seed 19/55 (p=0,976, *pior* que controle).
- **Lore/external:** lore_text_subsequence 13/55; k5_eye 18/55 (p=0,451); eye_5x2 20/55 (p=0,176).

**O gate paid-anchor (o instrumento anti-pareidolia mais afiado):** 13 âncoras dão +54,178 bits nominais que colapsam a **−11,852 bits líquidos** quando se cobra explicitamente o rótulo (não só a célula). Rare-singletons → ~0; diagonal-E → −8,852. Isto mata as "clues" diagonal-E e rare-singleton como descritivas, não gerativas.

### 3.3 O teto 21/55 e a saturação — honesta mas superdeclarada

`row0_origin_frontier_saturated_current_corpus` é **justo como afirmação sobre busca brute-force algorítmica** (82 famílias, controles, ML probe pair-cell 0,222 LOO p=0,129 = at-chance). É **prematuro como afirmação sobre origem**. Três motivos:

1. **A moldura de duas-baselines é um over-claim latente.** A família órbita reporta "split MDL/lookup 0,983" e "+3,6 bits" contra o baseline *fraco* (209,4), enquanto o gate é 160,521. Contra o gate real, o melhor sinal **perde por 45,3 bits**. Reporte tudo contra 160,521.
2. **`external_fixed_source_order` está BLOQUEADO, não testado.** A origem mais plausível de uma tabela feita à mão em 2005 — *o autor transcreveu símbolos na ordem de leitura de alguma lista pré-existente* — foi declarada inadmissível por construção. Isso torna "saturated" parcialmente infalsificável.
3. **Os artefatos 06-21 (`row0_real_origin_search`, `05_hypothesis_requirement_audit`) NÃO rodam busca nova** — `row0_real_origin_search.py` só faz `read_json` de 9 resultados prévios e hard-coda as classificações; `05` hard-coda `passes_as_origin_formula:False`. São **consolidações de bookkeeping** do trabalho 06-18/19, não testes frescos de exaustão. Não os cite como evidência independente de saturação.

### 3.4 A questão central: gerada por regra ou feita à mão?

**O gate é logicamente auto-derrotante para a hipótese declarada.** O próprio veredito-líder do projeto é "tabela 10×10 feita à mão". Uma tabela feita à mão *por definição* não tem fórmula geradora mais curta que sua própria listagem — é o que "feita à mão" significa. Então o gate MDL pede à hipótese hand-built para se refutar, e qualquer falha em bater o lookup é lida como "nenhuma origem encontrada" em vez de **evidência POSITIVA a favor de hand-built**. `manual_authorial_lookup` está literalmente rotulado `accepted_as_exogenous_substrate_not_origin_formula`.

**Fatoração honesta de row0 em três sub-problemas** (a síntese deve manter separados):
- **(A) superfície ordenada de 99 células** — tem estrutura atestada real (mirror render, 39-ausente, conflito 19/91). Único clue promovido. **Explicada.**
- **(B) o MULTISET de rótulos / tamanhos de classe** — fortemente explicado pela frequência interna de símbolo (**Pearson 0,895, p=5e-5**). **Parcialmente derivável.**
- **(C) a ATRIBUIÇÃO de rótulos às 55 células** — o núcleo genuinamente **NÃO resolvido**, em platô a 21/55 abaixo do lookup. Conflar A/C/D infla progresso aparente.

> **Veredito Fórmula A.** Saturada *como função coordenada→símbolo*. **NÃO** saturada nos canais asset-de-cliente, ordem-externa-pré-registrada, fill-direcionado-100-células, e inventário-derivado-de-frequência. A condição de vitória realista é **documental**, não um bit menor. A evidência é levemente **positiva** para uma tabela feita à mão, frequency-seeded, com fold 6↔9 e pressão diagonal-E — que legitimamente não tem fórmula sub-lookup, tornando o MDL o instrumento errado para a questão de origem.

---

## 4. Avaliação crítica das decisões e do método

### 4.1 O que foi bem decidido (preservar)

- **Disciplina anti-pareidolia institucionalizada e que MORDE.** A rejeição da "solução" alemã/MHG (100% cobertura, 0% nas cribs) é a melhor decisão metodológica do projeto. Os gates de lookup-disguise (MDL/lookup>1), o paid-anchor gate, os nulos de shuffle, os controles Avar Tar (min8 0/115 pass) — tudo real e aplicado.
- **Holdouts de família que FALHAM são reportados, não escondidos.** 3 famílias falham; 0/5 promovidos; row0 intocado. Isso é raro e honra o Outcome Ledger no portão.
- **A distinção decodável-vs-derivado** é a ferramenta mais afiada do projeto e deve ancorar o deliverable: o bit-ladder mede *decodabilidade* (compressão); o piso de 593 unidades e as falhas 0/5 medem *derivabilidade* (geração). **Eles desacoplaram** — bits caíram ~2.000 enquanto os geradores derivados ficaram em 0/5.
- **A separação accept-structure / reject-origin** de row0 é o postura anti-pareidolia correta.
- **O fencing do reparse** ("predictive, not authorial", train-set controls p=0,1538) está correto.

### 4.2 Decisões questionáveis

- **MDL ≠ autoria (o erro de categoria central).** O bit-ladder conflata description-length com evidência gerativa. LZ comprime byte-exato qualquer string auto-similar; roundtrip + bits baixos é *necessário mas longe de suficiente* para "foi assim que foi feito". O projeto sabe disso (rotula AUDIT_ONLY_COMPRESSION) mas organiza o trabalho inteiro em torno de baixar o número.
- **Ordem numérica como conveniência de custo tratada como fato.** A vitória do reparse (130) é mecanicamente forçada (LZ sequencial maximiza inventário disponível processando em ordem de concatenação) e **circular**. O controle prequencial (120/125) diz o oposto: numérico NÃO é especial. Essa tensão nunca foi reconciliada em um lugar.
- **Seed exógeno como "irredutível" é metric-dependent.** O book-0 é mediano em comprimento (34/70); seu status de "seed" vem *inteiramente* de ser o primeiro sob ordem numérica — a própria afirmação sob auditoria. O cold-start é genérico (qualquer livro emitido primeiro paga a penalidade); "book-0 é irredutivelmente exógeno" reduz-se a "a primeira emissão não tem desconto de contexto prévio" — tautologia de coding online.
- **O gate "regra-compacta-tem-que-vencer-lookup" aplicado a uma tabela possivelmente manual.** Como em §3.4: o gate exclui por construção a hipótese mais provável. Falta um **segundo canal de aceitação baseado em PREDIÇÃO** (a regra, ajustada num subconjunto de células, prediz células heldout acima do shuffle null?), não em compressão.

### 4.3 O treadmill de compressão vs progresso real

A escada fragmenta em promoções sub-1-bit (8.160,827 → 8.160,826421 → 8.160,825917 → 8.160,825608 — quatro passes para ganhos sub-0,001 bit, cada um com seu commit). Razão verb null:promotion ~6:1. ~529 scripts em 3 dias renderam, no máximo, **3-4 fatos estruturais reutilizáveis** (defaults decoder-válidos, a regra de segmentação 207/208, a regra optional-literal length≤5 & remaining≥10, a viabilidade do sparse parser). Insight-por-script muito baixo. **O gate captura falsos positivos mas não fornece saída positiva nem stop-rule** — defeito estrutural idêntico ao platô original, agora medido em bits.

### 4.4 O que a disciplina Outcome Ledger acertou — e a lacuna estrutural

Acertou: as 4 métricas semânticas seguem 0/0/0-de-70/0, nunca falsamente movidas. **A lacuna:** o Ledger foi projetado para a questão de *decodificação*; suas 4 métricas são todas de tradução. O objetivo *gerativo* pós-06-18 **não tem métrica de outcome pré-registrada**, então o proxy de fato virou "bits descendo" — exatamente o tipo de cadência que o Ledger avisa contra. O instrumento da própria disciplina não cobre a nova questão.

---

## 5. Insights e novas hipóteses de ataque (ranqueadas)

Fusão das melhores ideias dos insight-generators e critics, priorizadas por valor/esforço, separadas por alvo. Cada uma tem experimento, sinal esperado e esforço.

### Alvo B (livros)

**B1 — Corpus-nulo + compressor genérico (controle decisivo, jamais rodado).** *[esforço: médio]*
- **Experimento:** sintetizar 70 "livros" pelo mesmo processo copy-heavy a partir de um dicionário-seed aleatório; rodar o pipeline inteiro de 8.154 bits + a regra 207/208 sobre eles. Em paralelo, benchmark do código bespoke contra gzip/PPM/zstd-dict no stream de 11.263 dígitos, cobrando a description-length completa (incl. os ~4.272 bits fixos).
- **Sinal:** se o nulo atinge ~0,72 bits/dígito, ~90% copy-fraction e segmentação 200/208-style, **toda a frente B é confirmada como auto-similaridade LZ genérica, não evidência autoral** → parar o sweep. Se um compressor off-the-shelf bate o bound bespoke, os micro-sweeps são esteira pura.

**B2 — Collapse de copy-source via length+history.** *[esforço: médio]*
- **Experimento:** dado só o length do op (do atlas) e o prefixo emitido, enumerar todas as posições de fonte que atingem aquele length exato; checar se "earliest" recupera a fonte declarada. Medir bits residuais = log2(#candidatos). Testar um switch earliest/latest condicionado a length/offset para as 8 exceções.
- **Sinal:** o copy-source verdadeiro é ~232,9 bits de rank-oráculo (não os 2.550,6 "raw" reportados), efetivamente **earliest em 200/208 + flag latest 1-bit em 7 + 1 anomalia** (book-17 op0). Se length+history determina a fonte unicamente em ~200/208, o canal isolado mais caro (~3.003 bits / 37% do bound) colapsa de "208 campos livres" para "derivado de length + flag + anomalia". **Maior alavancagem de B.**

**B3 — Literal-payload via min-match length.** *[esforço: baixo]*
- **Experimento:** varrer `min_len ∈ {3,4,5,6,7}`; contar literais *forçados* (sem match ≥min_len) vs escolhidos. (Já se sabe: 34/38 literais "copiáveis" têm length<5; só **4 anomalias** verdadeiras de length-5; e os scripts são internamente inconsistentes — DP usa min_len=6 mas o ledger tem itens em 5.)
- **Sinal:** se ~95% dos chunks literais são forçados sob um min_len, a dependência de 266 dígitos colapsa para **~4 anomalias + seed**; residual livre cai de 266 para <30. Derivação genuína de uma dependência.

**B4 — Forward generative reach (ataca a circularidade diretamente).** *[esforço: médio]*
- **Experimento:** construir um *emitter* que, dados books 0..k−1 + regra fixa (earliest-match, min_len, decisão copy/literal), **emite** o book k SEM acesso ao alvo; pontuar dígitos-até-primeira-divergência. Comparar ao mesmo emitter num corpus-nulo PRNG.
- **Sinal:** reach >> nulo → política genuinamente gerativa para grande fração, e as divergências localizam as escolhas livres reais. Reach ≈ nulo → estrutura é genérica; copy-source é input autoral irredutível, quantificar e parar.

**B5 — Holdout cego de descoberta-de-receita (o teste que pode promover ou matar).** *[esforço: médio]*
- **Experimento:** o sparse Dijkstra parser (gates 73-77) já existe mas só rodou no corpus visto. Deixá-lo **escolher** segmentação em books de teste a partir do inventário só-treino, sem receber a receita do full-corpus, depois pontuar.
- **Sinal:** promove um gerador (enorme) ou prova que nenhum generaliza (fecha a frente B honestamente). Substituir o baseline uniforme 3,32 por Markov order-2 no treino.

**B6 — Cobrar o parse de zero-omitido.** *[esforço: baixo]*
- **Experimento:** testar a regra de render leading-zero-omission contra as 195 omissões reais; medir bits residuais. Re-derivar os desqualificadores sob parses alternativos válidos (20 livros não-únicos) para confirmar invariância.
- **Sinal:** regra reproduz >90% → camada de render barata, dobrar para dentro. <50% → input autoral; o headline bound subestima a fórmula.

### Alvo A (linguagem)

**A1 — Modelo composicional typed-layer pontuado por PREDIÇÃO (não MDL).** *[esforço: baixo]*
- **Experimento:** empilhar (L1) diagonal-default=E (6/10 células diagonais são E), (L2) órbita 6↔9 (fold 9 células, p~0,001), (L3) residual frequency-prior. Ajustar em 40 células aleatórias, predizer as 15 heldout, comparar a um inventory-preserving shuffle null (1000 draws). Pré-registrar threshold = bate 95º percentil do null.
- **Sinal:** se L1+L2+L3 predizem células *off-diagonal* heldout acima do null → **primeira estrutura row0 parcial promovível desde 06-18**. Se off-diagonal é null (provável), confirmação pré-registrada limpa de que a colocação off-diagonal é exógena — um resultado de parada real.

**A2 — Derivar o tamanho de inventário homófono de frequência (ponte A↔B + baixa o gate).** *[esforço: baixo]*
- **Experimento:** ajustar `homophone_count(símbolo) = round(α·freq + β)` (E=17, I=15, N=15 … R/O/S/C=2; correlação já conhecida 0,895). Re-derivar o gate de lookup de row0 *concedendo o inventário como derivado* (não livre).
- **Sinal:** se uma regra 1-2 parâmetros reproduz os 14 counts abaixo do custo raw, **deriva metade da especificação de row0** (o multiset) e baixa o gate de 160,521 por ~25-30 bits — legitimamente. A colocação pode então ser honestamente declarada exógena.

**A3 — Discriminador hand-built vs rule-generated (resolve a meta-questão com instrumento positivo).** *[esforço: médio]*
- **Experimento:** gerar 2.000 tabelas sintéticas sob regime R (regras tentadas) e regime H (frequency-inventory + anchor-then-greedy-com-ruído); computar estatísticas de textura (run-lengths, ilhas de rótulo 4-adjacentes, autocorrelação lag (1,0)/(0,1)/(1,1)); treinar classificador R-vs-H; pontuar a tabela real. Pré-registrar stats e threshold.
- **Sinal:** real firmemente no cluster H (P>0,9) → primeira evidência *positiva* de hand-built → licencia fechar a busca-de-fórmula de row0 como "nenhuma fórmula existe, por construção". No cluster R → reabrir aquela família.

**A4 — Fill direcionado de 100 células com simetria emergente.** *[esforço: médio]*
- **Experimento:** modelar o autor preenchendo o grid 10×10 ordenado em ordem direcionada (row-major, column-major, boustrophedon, diagonal), copiando ab→ba; pré-registrar as ordens (leakage-safe). Perguntar se os pontos de assimetria únicos (`39` ausente, `19/91` conflito) caem onde a ordem prediz "divergência de processo" (uma célula pulada, uma mis-keyed).
- **Sinal:** se uma ordem + modelo de slip único prediz unicamente `{39 pulado, 19/91 mis-keyed}` e a taxa de acerto por acaso é baixa, **essa é a trajetória de escrita do autor** — uma afirmação de *construção* falsificável (que é o que "feita à mão" de fato significa).

### Alvo externo (evidência)

**E1 — Minerar `bonelord_469_iter129.xlsx` (1926 sheets, `GroundTruthSources_v121/122/129`, `ExternalGroundTruthCheck`, `KeyTable`).** *[esforço: baixo — maior EV]*
- **Experimento:** ler as sheets de GroundTruth/External. Procurar: lista de ordem de símbolo/fonte, sequência de fill, string-fonte externa, mapeamento código→símbolo pré-projeto. Cross-check qualquer ordem encontrada contra row0 com controle leakage-aware.
- **Sinal:** qualquer sheet com lista ordenada que prediz colocação de row0 = **a provenance da fórmula, recuperada**. Ausência (após leitura real) rebaixa "talvez fonte externa" de "bloqueado/não-testado" para "buscado-negativo no artefato primário", fortalecendo o veredito hand-built.

**E2 — Rota Tibia.pic / charset-glyph (a única que poderia DERIVAR row0 de artefato externo).** *[esforço: alto]*
- **Experimento:** obter cliente Tibia pré-2010 (era pré-rename Beholder→Bonelord); extrair Tibia.pic (font bitmap) e .dat/.spr. Testar se os 14 símbolos `*ABCEFILNORSTV` correspondem a um slice estruturado da ordem de glyph do charset (ordem pré-registrada ANTES de olhar row0). Se sim, testar se a colocação das 55 células é a ordem de leitura desse slice contra o gate 160,521.
- **Sinal:** os 14 símbolos = exatamente os glyphs presentes de um slice de charset definível (D,G,H,J,K,M… ausentes por razão estrutural), E a ordem prediz ≥40/55 com shuffle p<0,01 → **primeira origem row0 promovida**, e move `CODES_CONFIRMED_EXTERNALLY`.

**E3 — Ordem externa pré-registrada (converte o escape-hatch BLOQUEADO em teste falsificável).** *[esforço: médio]*
- **Experimento:** pré-comprometer ~8-12 ordens que existem independentes de row0: alfabeto/QWERTZ alemão (CipSoft é alemã; autor Bednarzik), QWERTY, numpad, telefone, lista de runa/spell in-game, e as strings-nome de lore (TELBENNA, HONEMINAS, BONELORD, GREAT CALCULATOR — que já dirigem as melhores linhas 21/55). YAML commitado antes do fit.
- **Sinal:** uma ordem sobrevivendo ao permutation null no nível de célula = a primeira destrava documental. Tudo-null finalmente fecha a porta "talvez lista externa" *com evidência* em vez de um bloqueio.

**E4 — Strings 469 externas como segundo corpus (holdout out-of-sample genuíno).** *[esforço: baixo]*
- **Experimento:** decodificar as sequências externas in-repo (torg.pl 2007 Ks1/Ks2, mediavida 2020 Book1/2/3) com o mapa 99→14; checar se decodificam limpo ao alfabeto de 14 sem códigos ilegais. Rodar o parser LZ num book externo usando só os 70 livros como inventário.
- **Sinal:** decode limpo → confirmação externa do mapa (move métrica). Livros externos reconstruídos a alta copy-fraction → modelo shared-bank confirmado em dados não-vistos. Códigos ilegais → mapa incompleto.

**E5 — Minerar entrevistas do autor (PortalTibia, Rookie/Knightmare) para método declarado.** *[esforço: baixo]*
- **Experimento:** WebFetch das URLs; extrair qualquer afirmação sobre como a linguagem/os 70 livros/o sistema numérico foram criados. Classificar: hand-table vs gerador-algorítmico vs RNG.
- **Sinal:** uma frase ("eu só digitei números", "usei um script", "fiz uma tabela no papel") reclassifica a questão gerativa inteira e pode justificar aceitar `manual_authorial_lookup` como a resposta para A.

**E6 — Calibração null-author (Paradox Tower / Ljkhbl-Nilse / Avar Tar).** *[esforço: médio]*
- **Experimento:** rodar a bateria row0 inteira (matrix/orbit/diagonal/eye) sobre uma tabela construída de uma fonte de ruído conhecida da mesma era/mão; medir best-fit %, taxa diagonal-default, p-value da órbita.
- **Sinal:** se o gibberish-baseline também mostra ~21/55 e órbita sobrevivente → a estrutura residual de row0 é "o que a tabela-à-mão de um dev de 2005 parece" → fechar a frente. Row0 excedendo o baseline → o excesso é o alvo real.

---

## 6. Plano (fases)

### Fase 0 — Reframe e congelamento (1-2 dias) **[questiona premissas, não só mais buscas]**
- **Objetivo:** parar a negative-EV activity e pré-registrar o que conta como progresso.
- **Entregáveis:** (1) **Outcome Ledger gerativo** pré-registrado: um gerador promovido precisa derivar ≥1 das 5 dependências source-free, abaixo do piso de lookup, sobrevivendo a holdout de família E ao holdout cego de descoberta-de-receita. (2) **Stop-rule:** nenhum commit para ganho <1 bit; nenhum gate novo a menos que mire uma dependência declarada ou uma rota de evidência externa. (3) Reconciliar o bound canônico (8.154/8.177/8.343/8.558) e o inventário (261 vs 283) em uma tabela de estado. (4) Hard-reclassificar demona/honeminas/magic-web de "retained as context" para `BLOCKED_NEEDS_EXTERNAL_SOURCE`.
- **Critério de sucesso honesto:** o documento de pré-registro existe e o congelamento é respeitado. *Não conta* nenhum bit movido.

### Fase 1 — Controles decisivos (3-5 dias)
- **Objetivo:** descobrir se a frente B inteira é auto-similaridade LZ genérica.
- **Entregáveis:** B1 (corpus-nulo + compressor genérico), B4 (forward reach), B5 (holdout cego de descoberta-de-receita com baseline Markov competitivo).
- **Critério de sucesso honesto:** um veredito binário pré-registrado — *"a estrutura B é genérica"* (resultado negativo publicável sob o Ledger) **ou** *"a estrutura B é distinguível de um nulo sem-mensagem por uma estatística pré-registrada"*. Qualquer um é um outcome real. O bit-count **não** é o critério.

### Fase 2 — Collapses de dependência baratos (1 semana)
- **Objetivo:** mover dependências de DECLARADO para DERIVADO ou IRREDUTÍVEL-com-residual-quantificado.
- **Entregáveis:** B2 (copy-source via length+history), B3 (literal-payload via min-match), B6 (parse de zero-omitido), A2 (inventário homófono de frequência).
- **Critério de sucesso honesto:** cada uma das 5 dependências B + o inventário de A particionada em {derivada, irredutível, aberta} com **residual quantificado**. Sucesso = ≥1 dependência muda de estado OU é provada irredutível com piso quantificado. Lookup-disguises (condicionar em chaves target-derived near-únicas) são automaticamente reprovados.

### Fase 3 — Provenance externa (paralelo, esforço contínuo)
- **Objetivo:** obter o único tipo de evidência que pode mover as métricas do Ledger e derivar row0.
- **Entregáveis:** E1 (minerar iter129.xlsx), E5 (entrevistas), E4 (strings externas como holdout), E2 (Tibia.pic — esforço alto, maior upside), E3 (ordem externa pré-registrada).
- **Critério de sucesso honesto:** uma crib atestada externamente passa o decode-gate (move `GT_PHRASES_PASSING_EXTERNALLY` / `CODES_CONFIRMED_EXTERNALLY`), OU uma ordem/fonte documental prediz row0/seed a custo-cobrado zero, OU todas as rotas in-repo são exauridas e formalmente fechadas. Achar uma planilha de construção é a vitória de máximo EV.

### Fase 4 — Tentativa positiva em row0 e fechamento honesto (1 semana)
- **Objetivo:** dar a A o único teste predição-based (não-MDL) que falta, e então fechar ou promover.
- **Entregáveis:** A1 (typed-layer por predição holdout), A3 (discriminador hand-built), A4 (fill direcionado), E6 (calibração null-author).
- **Critério de sucesso honesto:** ou uma estrutura row0 parcial promovida (predição off-diagonal heldout acima do null) — primeiro progresso A real desde 06-18 — ou um **negativo pré-registrado limpo**: "a colocação off-diagonal é exógena/hand-arbitrária; A é documental, não algorítmica". Ambos fecham a meta-questão.

---

## 7. Backlog priorizado

| ID | Item | Alvo | Objetivo | Esforço | Valor esperado | Gate de sucesso / critério de parada | Depende de |
|---|---|---|---|---|---|---|---|
| **F0-1** | Pré-registrar Outcome Ledger gerativo + stop-rule | meta | Definir progresso antes de buscar | baixo | alto | Doc existe; <1-bit gates proibidos | — |
| **F0-2** | Reconciliar bound canônico (8154/8177/8343/8558) e inventário (261 vs 283) | meta | Eliminar ambiguidade que esconde o estado | baixo | médio | Uma tabela de estado única citada por todos os docs | — |
| **F0-3** | Hard-reclassificar lore (demona/honeminas/magic-web) → BLOCKED | meta | Impedir re-litígio | baixo | médio | Status muda de "context" para BLOCKED | — |
| **E1** | Minerar `iter129.xlsx` (GroundTruthSources, KeyTable, ExternalGT) — **✅ CONCLUÍDO 21/06** | ext | Recuperar provenance/ordem de fill | baixo | **máximo** | **Resultado: sem recipe na planilha (negativo); row0 = hand-built constrained-random.** Ver [analysis/e1_groundtruth_keytable_audit_20260621](../../analysis/e1_groundtruth_keytable_audit_20260621/reports/final_e1_groundtruth_keytable_audit.md) | — |
| **B3** | Literal-payload via min-match length sweep | B | Colapsar 266 dígitos → ~4 anomalias + seed | baixo | alto | ~95% literais forçados sob um min_len | — |
| **A2** | Inventário homófono = f(frequência); re-derivar gate | A | Derivar o multiset; baixar gate 160,5 | baixo | alto | Regra 1-2 param reproduz 14 counts < custo raw | — |
| **B2** | Copy-source via length+history (+ switch earliest/latest) — ✅ **resolvido pelo Codex** | B | Colapsar canal de fonte | médio | médio | **Fonte = earliest em 200/208 (8 exceções) = 58 bits DADO o alvo; mas target-conditioned → não-derivável forward.** Source não é o bloqueador; o **target-stream** é. (target_conditioned_source_collapse) | F0-1 |
| **B1** | Corpus-nulo + benchmark compressor genérico — **✅ CONCLUÍDO 21/06** | B | Testar se B é LZ genérico | médio | **máximo** | **Resultado: brotli=8.384 bits (só +230 vs bespoke); shared-bank null reproduz copy-fraction 0,91≈0,93; 20/70 livros 100% dentro de outro. B = copy-paste message-free; bit-sweep = treadmill.** Ver [analysis/b1_null_corpus_compressor_audit_20260621](../../analysis/b1_null_corpus_compressor_audit_20260621/reports/final_b1_null_corpus_compressor_audit.md) | F0-1 |
| **E5** | Minerar entrevistas do autor (PortalTibia, Rookie) — **✅ CONCLUÍDO 21/06** | ext | Achar método de construção declarado | baixo | alto | **Resultado: nenhuma chave oficial jamais publicada; postura oficial = mistério (2009 piada) + "dicionários falsos" (2021 Buried Secrets); lore de criação = "great calculator assemble" (= B1). Sem statement de método do dev (gap).** Ver [analysis/e5_author_method_lore_audit_20260621](../../analysis/e5_author_method_lore_audit_20260621/reports/final_e5_author_method_lore_audit.md) | — |
| **E4** | Strings 469 externas (torg/mediavida) como holdout | ext | Validação out-of-sample do mapa | baixo | alto | Decode limpo ao alfabeto 14 / copy-fraction alta | — |
| **B5** | Holdout cego de descoberta-de-receita (Dijkstra existente) | B | O teste que promove ou mata o gerador | médio | **máximo** | Gerador generaliza, ou prova que nenhum generaliza | F0-1 |
| **A1** | Typed-layer (órbita→diagonal-E→residual) por predição holdout | A | Primeiro teste predição-based de row0 | baixo | alto | Predição off-diagonal heldout > 95º pct null | A2 |
| **B6** | Cobrar parse de zero-omitido (195 omissões) | B | Fechar grau de liberdade não-cobrado | baixo | médio | Regra render reproduz >90% das omissões | — |
| **B4** | Forward generative reach metric | B | Atacar circularidade target-aware | médio | alto | Reach >> nulo (ou ≈ nulo = irredutível) | F0-1, B1 |
| **A3** | Discriminador hand-built vs rule-generated (sintéticos) | A | Resolver meta-questão com instrumento positivo | médio | alto | Tabela real classificada P>0,9 em um cluster | A2 |
| **E3** | Teste de ordem externa pré-registrada (QWERTZ/alemão/lore) | A/ext | Converter escape-hatch em teste falsificável | médio | alto | Uma ordem sobrevive permutation null (ou tudo-null) | F0-1 |
| **A4** | Fill direcionado 100-células; assimetria como localizador | A | Explicar 39-ausente + 19/91 como evento de construção | médio | médio | Uma ordem+slip prediz unicamente {39,19,91} | — |
| **E6** | Calibração null-author (Paradox Tower / Avar Tar) | A/ext | Calibrar quão impressionante é 21/55 | médio | médio | Gibberish-baseline iguala ou não row0 | — |
| **E2** | Extração Tibia.pic / charset-glyph | A/ext | Derivar row0 de asset externo | alto | **alto (maior upside)** | 14 símbolos = slice de charset; ordem prediz ≥40/55 | E1 |
| **A-eye** | Re-rodar eye-pair com encoder 14-capable (não 3-4-classe) | A | Fechar eye-arity com teste adequadamente potente | alto | baixo | Modelo stalk+state prediz heldout > null | — |

---

## 8. Terra morta — o que NÃO refazer

Estes são NULLs controlados ou dead ground. O backlog **não deve re-litigar**:

- **Recuperação exata de células de row0 de busca interna** (saturado: 21/55 melhor, todos abaixo do lookup; 294.528 candidatos matrix + 1.248.362 quotient esgotados). *Como função coordenada→símbolo apenas* — não as rotas asset/ordem-externa/fill-direcionado.
- **German/MHG homofônico** (falsificado: 0% nas cribs inglesas).
- **Word-code book segmentation** (livros não USAM o word-code da camada de frase: 90871/97664/653/768 = 0/70).
- **Reduced-alphabet / abjad.**
- **BENNA/TELBENNA/ENNAI como lore externa** (são artefatos de decode internos; exact_external_bridge_count=0).
- **Demona/honeminas/magic-web seed hypotheses** (43153/34784/74032/45331 = 0 corpus hits; 3478 é comum/estrutural, não-probatório).
- **Ordem de livro arbitrária não-numérica** (random_04 é +521 bits *pior* após formula+descriptor completo).
- **Geradores source-free simples para as 5 dependências B** (0/5 promovidos).
- **~60 famílias de branch-selector de segmentation-parser** (gates 16-63, todos não-oracle-negativos sob holdout; o residual de 10-sítios precisa de ~79 bits de lookup, ponto).
- **Topologia física** (ordem numérica vence por 169,8 bits; ambos os testes de adjacência null p=0,146/0,722). *Demovido para watchlist, não backlog ativo.*
- **Sub-1-bit / sub-0,001-bit MDL micro-refinement** (substituição de fonte 0,0003-2 bits; repair-exhaustion sizes 3-22 todos piores).
- **As "clues fracas" Tridiag/Donina diagonal-E** (p=0,022-0,035 em 2-10 células = quase-certamente artefatos de comparação-múltipla; reclassificar para rejected, não re-promover).
- **Eye-arity como majority-vote 3-4-classe** (teto arquitetural ~26-32/55; já testado — só o re-teste 14-capable A-eye é novo).

---

## 9. Riscos e armadilhas

- **Pareidolia (sob controle, mas vigiar):** o instrumento decisivo é o **paid-anchor gate** — cobre o custo de *nomear* o rótulo, não só de flagar a célula. Toda "clue" que sobreviveu como positiva (diagonal-E, rare-singletons, 6↔9) vai a ~0 ou negativo sob ele. Qualquer fórmula row0 futura PRECISA passar este gate ou é descritiva.
- **Atividade-vs-progresso (o risco dominante ativo):** o pivot recriou o exato failure mode que a page-08 diagnosticou, lavado através do bom nome do Outcome Ledger. O Ledger é o **freio, não o motor** — captura falsos positivos mas não dá saída positiva. Sem a métrica gerativa da F0-1 e a stop-rule, os próximos 300 commits serão mais sub-bit gates.
- **Overfitting do compressor:** o bit-ladder recompensa qualquer truque de micro-codificação num corpus fixo; não distingue "procedimento do autor" de "compressor pós-hoc mais apertado". O bound não-monotônico (8.154 mais baixo coexiste com 8.343 como explicação de geração *pior*) é o tell: isto é ajustar um compressor, não descobrir um processo. **Cite os holdouts que falham acima do headline de 8.154.**
- **Contaminação de ground-truth:** o `gt-gate` de frase é circular (só 764 generaliza); `existing_mechanical_origin_model_v1` está listado *como fonte* no registro e depois "crosswalked" de volta para validar lore — a própria conclusão prévia do projeto sendo alimentada como corroboração externa. Qualquer ordem/crib externa precisa **predatar a análise** para ser admissível e custo-zero.
- **Reprodutibilidade apodrecida:** as tabelas canônicas citadas no §10 do report e nos source_refs do wiki **sumiram do DB ao vivo** (`row0_code_symbol_probe_books`, `rosetta_*` ausentes). O substrato agora vive em `sheet__digitcodemap_auto` / `sheet__booksdigitmodel_v118` / `sheet__phrasecribs_*`. Re-anchorar os docs antes de qualquer trabalho que dependa deles.

---

## 10. A única destrava real e estratégia de monitoramento

**O ground truth externo CipSoft é a única destrava genuína.** Tanto A quanto B têm assinaturas negativas convergentes (ambos saturam abaixo do lookup, ambos falham holdout/família), consistentes com **montagem manual target-aware**. Nenhum bit-count menor resolve isso. A condição de vitória realista para A é documental; para B, é uma crib atestada que passe o holdout.

**Caminho de maior EV, ordenado:**

1. **In-repo primeiro (custo-zero, hoje):** ler `bonelord_469_iter129.xlsx` — as sheets `GroundTruthSources_v121/122/129`, `ExternalGroundTruthCheck_v120`, `KeyTable`. Foi *inventariado mas nunca lido*. Se contém uma lista de ordem de fonte ou um histórico de reconstrução, a resposta pode estar sentada no repositório. **Este é o single highest-EV lead do projeto inteiro.**

2. **Fontes web já-identificadas (custo baixo):** o repo `s2ward/469` (timeline + issues), as entrevistas PortalTibia/Rookie do autor (Bednarzik), e as strings 469 externas (torg.pl 2007, mediavida 2020) — fetches que o pivot nunca consumiu e que podem mover `CODES_CONFIRMED_EXTERNALLY` / `GT_PHRASES_PASSING_EXTERNALLY` (atualmente só 2 cribs externas existem — o ponto evidencial mais fraco do projeto; qualquer crib nova tem alto valor marginal).

3. **Asset de cliente (esforço alto, maior upside para A):** extrair Tibia.pic (font bitmap charset) de um cliente pré-2010. Os 14 símbolos sendo um slice de charset glyph é a explicação não-testada mais plausível para o perfil de letras anti-inglês V-heavy/H-absent, e é a **única rota que poderia derivar row0 de um artefato externo** em vez de declará-lo exógeno.

**O que observar (monitoramento):**
- **A pista mais forte de provenance é o Chayenne 2009** (verificado: nenhum livro único contém ambos os blocos; string juntada ausente; coverage 0,918 a p=0,0005). É a *única* superfície externa demonstravelmente construída do corpus, e corrobora o modelo copy/assembly de um segundo ângulo público. A assimetria corpus-derived (Chayenne 0,918 vs Honeminas/SecretLibrary/YTC 0,000) sugere **um banco de módulos compartilhado + seeds por-superfície** — aponta a caça ao seed/cold-start.
- **Watchlist comunitária:** a thread OTLAND 2026 perseguindo a extração de Tibia.pic. Se alguém da comunidade publicar o charset ou uma crib atestada da CipSoft, isso destrava A.
- **Gatilho de reabertura:** qualquer ordem externa, charset, ou par string↔meaning que *predate* a análise. Esse é o único input admissível custo-zero sob o gate do próprio projeto.

> **Enquadramento final para o dono.** O projeto produziu um substrato mecânico exemplar e uma disciplina transferível. Mas confundiu um contador de bits descendente com progresso autoral. A fórmula provavelmente **não é uma função fechada** — é "uma pessoa com uma planilha e o hábito de copiar-colar". Provar isso rigorosamente (via corpus-nulo + irredutibilidade) é um resultado real e honrado pelo Ledger; persegui-lo via mais um micro-gate não é. Pare o sweep. Rode os controles decisivos. Leia a planilha.

---

## Adendo A — E1 EXECUTADO (2026-06-21)

> "Leia a planilha" foi executado no mesmo dia. Relatório completo + script reprodutível: [analysis/e1_groundtruth_keytable_audit_20260621](../../analysis/e1_groundtruth_keytable_audit_20260621/reports/final_e1_groundtruth_keytable_audit.md).

**Achado-chave:** o artefato primário `bonelord_469_iter129.xlsx` armazena a **tabela acabada** (`sheet__keytable` = o grid 10×10 que É o row0 canônico, **99/99 consistente** com o mapa) mas **nenhum recipe de construção** — nenhuma ordem, sequência de fill, charset, ou fonte externa. As abas "GroundTruth" são **registros de validação de decode externo** (wikis/fóruns), não provenance autoral. Varredura de nomes de tabela por `order/seed/charset/keyboard/alphabet/fill/origin/provenance` = vazio.

→ O lead de **maior EV** do backlog fecha **negativo no artefato primário**: não há fórmula escondida na planilha. A hipótese "fonte/ordem externa" cai de `BLOCKED` para `buscado-negativo`.

**O ganho real (parte que vale mais):** a tabela acabada foi interrogada diretamente (o discriminador A3/A4 no objeto real, com nulls de permutação):
- Simetria de par não-ordenado: **44/45** (único slip `19=I` vs `91=N`, os dois símbolos de maior inventário).
- Inventário ~ frequência interna: **Pearson 0,917 / Spearman 0,890** (insight A2 confirmado — o multiset é largamente derivável).
- **Nenhuma regra de coordenada** explica a colocação (todas as features aritméticas ≤0,73; `unordered_pair` 0,99 é só a simetria).
- **Placement-dado-restrições é ALEATÓRIO:** condicionado em simetria+inventário, a colocação nos 55 slots é indistinguível de preenchimento aleatório em **duas** estatísticas independentes (adjacência p=**0,334**; concentração-por-linha p=**0,624**). Único resíduo fraco = diagonal-E (p=0,020), que já colapsa sob o paid-anchor gate.

**Re-enquadramento da Fórmula A:** `row0_origin_frontier_saturated` deixa de ser "busca exausta sem achar fórmula" e vira **evidência positiva de que nenhuma fórmula existe além de {simetria + inventário-por-frequência + 1 slip de keying + leve hábito diagonal-E}** — i.e., **tabela feita à mão, frequency-seeded**. Vitória futura em A só por **evidência documental externa** (entrevista do autor / charset pré-datado), não por busca interna.

**Reconciliações registradas (confirmam críticas do plano):** (1) a órbita 6↔9 é **fraca na grade crua (20/36 = 0,56)**, contradizendo o "p~0,001" documentado — over-claim de §3.3; (2) o gate canônico recomputa para **157,5 bits** (vs 160,521 citado) — convenção de slot/label a reconciliar (F0-2).

**Estado do backlog após E1:** E1 ✅ · A2 promovido a "pronto para formalizar" · busca-de-fórmula row0 interna deve **fechar** com este negativo pré-registrado · E5 (entrevista) e E2 (Tibia.pic) tornam-se as **únicas** rotas vivas para a Fórmula A.

---

## Adendo B — B1 e E5 EXECUTADOS (2026-06-21)

Relatórios: [B1](../../analysis/b1_null_corpus_compressor_audit_20260621/reports/final_b1_null_corpus_compressor_audit.md) · [E5](../../analysis/e5_author_method_lore_audit_20260621/reports/final_e5_author_method_lore_audit.md).

### B1 — Fórmula B é montagem copy-paste message-free (treadmill quantificado)

- **Compressor genérico ~empata o bespoke:** `brotli -q11` = **8.384 bits** (só **+230** vs 8.154,68); raw lzma2/deflate headerless = 8.776/8.792 (+621/+637). ~77% da compressão sai de uma linha de código; o esforço bespoke de ~150 scripts adicionou ~3–8%, **zero do qual é regra de autoria** (0/5 derivadas). **Esteira quantificada.**
- **Copy-fraction é message-free:** null de banco-de-módulos sem mensagem atinge **0,911 ≈ 0,930** do real. Markov-ordem3 sozinho satura em ~19.300 bits (1,71/díg) — o templating cross-book carrega o resto, mas é **copy-paste, não língua**.
- **Mecanismo = copy-paste de passagens longas:** **20/70 livros 100% dentro de um único outro**; 35 cópias ≥100 dígitos (máx **303**). Núcleo autoral irredutível ≈ seed do book-0 (144 díg) + ~791 literais (~8%, quase-incompressíveis).
- **Gap metodológico real:** este controle nunca foi rodado — o bit-ladder competia com `brotli` sem ninguém medir. Qualquer claim de bits deve reportar o baseline genérico daqui pra frente.

### E5 — sem chave oficial; lore confirma "montagem"; sem statement de método

- **Nenhum par número↔significado oficial jamais publicado** (`CODES_CONFIRMED_EXTERNALLY` = 0 reconfirmado).
- **Postura oficial CipSoft:** entrevista Chayenne 2009 = piada respondida em 469; notícia **"Buried Secrets" 2021** = in-lore, **dicionários da linguagem são FALSOS**, um real "nunca encontrado" → autor sinaliza que as "traduções" são fakes.
- **Lore de criação = ponte com B1:** *You Cannot Even Imagine*: "assisted **the great calculator** to **assemble** the bonelords language"; + mathemagic, subjective viewer (render), mirror (reversão-invariância), blinking (homófonos). A lore codifica as **propriedades estruturais medidas** como flavor — sem prometer plaintext.
- **Corroboração externa do mecanismo:** TibiaSecrets article160 derivou mapa que **bate 13/13 com a KeyTable**; mantenedor do repo s2ward/469: *"I personally no longer believe that decryption is the way."*
- **Gaps E5:** (1) **nenhuma declaração pública do dev sobre o MÉTODO** (hand-table vs script vs RNG) — aparenta não existir; única peça que destravaria A documentalmente. (2) verbatim exato da notícia oficial 2021 e texto completo do livro não capturados (primários 403/anti-bot neste ambiente).

### Convergência (as duas fórmulas, fechadas no nível disponível)

| Evidência | Fórmula A (linguagem/row0) | Fórmula B (livros) |
|---|---|---|
| Estatística do corpus | hand-built, frequency-seeded, placement aleatório (E1) | copy-paste de banco, message-free (B1) |
| Lore in-game | mirror + subjective viewer + mathemagic (flavor das propriedades) | "great calculator assemble" (montagem) |
| Postura oficial | sem tabela símbolo↔sentido publicada | dicionários "falsos" (2021); sem mensagem confirmada |
| Comunidade | mesmo mapa 13/13; sem solução crível | "decryption is not the way" |

**Veredito consolidado:** ambas as fórmulas estão **caracterizadas até o limite do que evidência interna + pública permite**. (A) = tabela feita à mão frequency-seeded; (B) = montagem copy-paste de um banco compartilhado. Nenhuma é função fechada; nenhuma carrega mensagem recuperável. **A única destrava restante é uma declaração/chave oficial do dev — que E5 indica não existir publicamente.** Recomendação reforçada: **fechar as frentes internas A e B** com estes negativos pré-registrados; manter só o monitoramento de evidência oficial (watchlist) e, se houver apetite, E2 (Tibia.pic) como a única rota documental de upside para A.

---

## Adendo C — Incorporação dos commits do Codex (2026-06-21, `444ec4b8`→`fabcc331`)

11 commits paralelos (agente Codex) atacaram a **derivabilidade da recipe da Fórmula B** — e **confirmam independentemente** o veredito de B1 + a Fórmula Completa de Construção ([THE_book_construction_formula.md](../../analysis/book_construction_formula_20260621/reports/THE_book_construction_formula.md)). Todos com `Compression bound: unchanged_8154_676268`, `Row0: unchanged_exogenous`, `translation_delta: NONE`.

| Audit (Codex) | Resultado | Confirma |
|---|---|---|
| `generation_boundary_closure` | `0/5` geradores; piso **593 unidades**; bloqueador = **operation_skeleton** | "recipe = lista, não função" |
| **`skeleton_decoder_ambiguity`** | concedendo o skeleton, decoder ainda precisa de **3.434,227 bits** (10^1033,8); "não usável sem acesso ao texto-alvo" | **§5 da Fórmula (circularidade target-aware), provado com números** |
| **`target_conditioned_source_collapse`** (commit mais recente) | *dado o chunk-alvo*, fonte = earliest em **200/208** (8 exceções) = **58 bits** (p<0,0001); mas **target-conditioned** → source é downstream do target-stream, não bloqueador independente | confirma "fonte canônica = earliest" da Fórmula; o bloqueador real é o target-stream |
| `operation_type_sequence` | rejeitado (template posthoc 60/60, **0/5 holdout**) | op-type não-derivável |
| `operation_count` | rejeitado (40/60, **0/5 holdout**; clue audit-only −5 records) | op-count não-derivável |
| `operation_length_markov` / `_motif` / `_cutpoint_scaling` / `_cutpoint_lattice` / `_recursive_partition` | **todos rejeitados** (0/5 holdout) | op-length não-derivável |
| `literal_payload_reference_subcodec` *(uncommitted, foco atual do Codex)* | rejeitado (−30 bits no-mode → **+23 bits** com mode/source) | literal payload é input |

**Síntese da incorporação:** a busca paralela do Codex por um gerador source-free **falhou em 5+ famílias** e *consolidou a fronteira como fechada* — ou seja, a Fórmula Completa que dei (montagem por cópia + recipe irredutível + núcleo de ~170 dígitos) é agora **corroborada por um segundo agente independente**. Ajuste numérico fino: copy-source **colapsa para earliest em 200/208 = 58 bits dado o alvo** (target_conditioned_source_collapse, p<0,0001) — confirma a "fonte canônica = earliest" da Fórmula; só não é decodável forward (target-conditioned), então o bloqueador real é o **target-stream** (o próprio conteúdo), não a fonte. O `compression_bound` permanece **8.154,676268** — os 13 commits (até `fd34e3b3`) são **todos negativos/consolidação/clue**, o que (sob o Ledger gerativo da F0-1) é o desfecho correto: **confirmam irredutibilidade, não perseguem bits.** Recomendação inalterada e reforçada: **fechar a Fórmula B como resolvida** (procedimento + núcleo) e parar a busca de gerador source-free.

> Nota operacional: estes artefatos do Codex já estão **commitados** (`fabcc331`); meus relatórios (E1/B1/E5/Fórmula + este plano) seguem **não-commitados** na working tree, coexistindo sem conflito (arquivos distintos). As edições não-staged em `docs/wiki/13/18/README` pertencem ao Codex — não as toquei.
