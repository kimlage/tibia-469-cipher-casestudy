# Auditoria de reabertura do 469 — caminhos mecânicos, semânticos, lore e backlog

**Data:** 2026-06-24  
**Repo auditado:** `kimlage/tibia-469-cipher-casestudy`  
**Tipo:** auditoria de reabertura / backlog executável  
**Escopo:** revisar o estado público do projeto, separar frentes semanticamente fechadas de frentes mecanicamente ainda produtivas, reinterpretar a lore sem transformar lore em “tradução”, e propor próximos testes com critérios de promoção.

> Esta auditoria não substitui o relatório final. Ela assume o relatório final e os addendums como base factual, e pergunta: **o que ainda pode avançar sem cair de novo em pareidolia, overfit ou retrabalho?**

---

## 0. Veredito curto

A reabertura **sem nova evidência externa** não deve tentar “traduzir os 70 livros” novamente. Essa frente está fechada por três motivos independentes:

1. A camada dos livros é mecanicamente resolvida como `2 dígitos -> 14 símbolos`, mas essa camada falha como linguagem natural.
2. A maior parte do corpus é melhor explicada como recombinação/cópia de módulos numéricos já renderizados do que como mensagem cifrada.
3. O que sobra como residual não se comporta como texto, nem como canal de homófonos, nem como alemão/inglês reduzido, nem como word-code das frases.

A reabertura produtiva deve trocar a pergunta:

```text
"qual é a tradução?"
```

por:

```text
"qual é o gerador/compilador mecânico que produz, valida ou classifica 469,
e que tipo de evidência externa poderia ligar esse gerador a significado?"
```

A frente viva não é uma “tradução direta”; é uma combinação de:

- **descobrir a origem da tabela row0 / matriz 10x10**;
- **transformar o gerador de cópia/fita em parser fechado**, sem oráculo do texto-alvo;
- **classificar strings externas oficiais ou semi-oficiais**;
- **obter uma âncora externa CipSoft/in-game**: número→texto, livro→texto ou tabela símbolo→significado;
- **usar a lore como especificação de mecanismo**, não como glossário.

---

## 1. Base factual usada

Esta auditoria revisita principalmente:

- `README.md`
- `docs/469_final_report.md`
- `docs/wiki/01..18`
- `analysis/audit_20260609/`
- `analysis/lore_audit_20260618/`
- `analysis/mechanism_model_20260618/`
- `analysis/generator_search_20260618/`
- `analysis/eye_model_20260619/`
- `analysis/inspiration_model_20260620/`
- `analysis/language_comparanda_20260620/`
- `analysis/physical_topology_20260620/`
- `analysis/authorial_mechanism_20260620/`
- auditorias mecânicas posteriores em `analysis/*_20260621`, `analysis/*_20260622`, `analysis/*_20260623`

Limitação desta auditoria: ela é uma auditoria documental e estratégica sobre artefatos públicos commitados. Ela **não reexecuta** a SQLite operacional de 1 GB nem todos os scripts. Quando este documento diz “teste”, significa um teste de reabertura: a hipótese é confrontada contra os resultados já commitados, os bloqueios metodológicos, os controles e as lacunas explícitas. Para virar resultado novo, cada item do backlog abaixo deve ganhar script, dados, controles e decisão própria.

---

## 2. Estado aceito: o que realmente foi resolvido

### 2.1 Há pelo menos duas camadas, não uma língua única

O projeto separou duas superfícies:

```text
Camada A — frases/NPC/polls:
  word-code de grupos variáveis
  pequeno codebook
  validação interna, não CipSoft-confirmada

Camada B — 70 livros:
  stream fixo de códigos de 2 dígitos
  99 códigos usados
  14 símbolos internos
  row0 reconstrói 70/70 livros
```

Essa separação é essencial. Tentar forçar a camada de frases sobre os livros foi uma das fontes de miragens. O resultado honesto é:

- as frases dão poucos anchors úteis;
- o codebook de frases não é uma chave dos livros;
- o “be a wit than be a fool” é análise comunitária/Knightmare, não ground truth oficial;
- a camada dos livros compartilha alguns números curtos, mas no livro eles se comportam como códigos/símbolos, não como word-codes.

### 2.2 A mecânica row0 está aceita

O substrato aceito é:

```text
raw digits
-> reinserção de zeros omitidos
-> split em pares de 2 dígitos
-> mapa global código->símbolo
-> 14 símbolos internos
```

Pontos estabilizados:

- 70 livros;
- 11.263 dígitos;
- 5.729 símbolos;
- alfabeto interno `*ABCEFILNORSTV`;
- 99/100 códigos presentes, `39` ausente;
- reconstrução 70/70;
- anchors estruturais `34=B`, `78=E`, `67=A`;
- quase todos os pares reversos preservam símbolo;
- 54/55 classes de pares não ordenados são puras;
- conflito real `{19,91}` com `19=I`, `91=N`;
- órfão/superfície dirigida envolvendo `93` porque `39` falta.

Isso é uma solução mecânica parcial robusta. O ponto não resolvido é **por que a matriz recebeu esses labels**.

### 2.3 A camada dos livros não passa por linguagem

Os disqualifiers principais permanecem:

- distribuição de símbolos incompatível com língua natural;
- flat/uniforme é “menos ruim” que inglês/alemão/espanhol;
- F/V altos demais e R/O quase ausentes;
- abjad/redução alfabética não salva;
- substituição ancorada em B/E/A não gera prosa;
- residual deduplicado não vira linguagem;
- o sinal “alemão-like” foi localizado em motivos repetidos, não em texto;
- homófonos são determinados por segmentos/chunks, não escolhidos livremente por ocorrência;
- 70 livros são mais bem descritos por cópia/recombinação do que por mensagem.

### 2.4 A parte mais viva hoje é mecânica, não semântica

O projeto passou de:

```text
"procurar plaintext"
```

para:

```text
"descrever o processo de fabricação"
```

Modelo mecânico atual em camadas:

```text
row0 code table
+ unordered pair / mirror geometry
+ directed render exceptions
+ homophone classes
+ module/tape chunks
+ copied/spliced book assembly
+ zero omission render layer
+ parser/control streams still partially external
```

O melhor resultado recente não é “texto”; é compressão/geração parcial dos dígitos. Isso é valioso porque pode revelar a fórmula de produção, mesmo se os livros nunca tiverem significado lexical.

---

## 3. Auditoria completa das frentes já tentadas

A tabela abaixo separa as frentes por hipótese, teste já realizado, estado e condição real de reabertura.

| Frente | Hipótese original | Evidência/teste já feito | Estado | Pode reabrir? |
|---|---|---|---|---|
| Word-code das frases aplicado aos livros | livros usam os mesmos grupos variáveis das frases | códigos longos não aparecem; códigos curtos aparecem como pares row0, sem enriquecimento de word-code | fechada como tradução | só com novo gloss oficial ligando livro a palavra |
| Homophonic substitution 2 dígitos -> letras | cada par representa uma letra/homófono | row0 reconstrói símbolos, mas símbolos não são linguagem; split-half EN/DE falha | fechada semanticamente | não como plaintext; sim como origem de tabela |
| Alemão/MHG | livros codificam alemão antigo/moderno | soluções externas falham em cribs; corpus não tem perfil de língua | fechada | apenas como controle positivo/negativo |
| Inglês reduzido / abjad / 13-14 símbolos | símbolos são alfabeto reduzido | random merge supera reduções linguísticas; topologia de frequências inválida | fechada | só se houver script intermediário comprovado por controle externo |
| Anagramas / self-anagram / semi-English | existe prosa escondida em rearranjos | sinais são templating/cópia; per-book não sustenta | fechada | não reabrir sem cribs oficiais |
| Mathemagic / aritmética direta | códigos obedecem fórmula numérica simples | dezenas de tabelas e famílias `mathemagic_*` resultam `NO_PLAINTEXT`/`STRUCTURAL_ONLY` | fechada como tradução | reabrir apenas como gerador/indexador |
| BENNA/TELBENNA/ENNAI | strings são vocabulário Bonelord | sem atestação externa; artefatos internos do decodebase | fechada | não reabrir como palavra |
| Known plaintext via phrase cribs | usar frases para quebrar livros | data-starved/circular; codebook não é CipSoft-confirmado | fechada | só com CipSoft/in-game gloss |
| Kharos como holdout | sequência externa valida decoder | refutada como paste-up/cópia de material de livros + poucos dígitos novos | fechada como crib | útil só como compatibilidade/cópia |
| Chayenne 2009 | resposta numérica contém chave | reaproveita substrings de livros; joke/non-answer; módulo secundário | fechada como tradução | útil como prova de reuso de módulos |
| Your True Colour 2012 | string oficial pode destravar | genuinamente novel, mas 21 dígitos é curto e sem gloss; compatível mas não discriminativo | watchlist/classificador | sim, como caso externo a classificar |
| Secret Library `74032 45331` | novo livro externo pode ser crib | confirmado como externo e não glosado; zero hits nos 70 livros | watchlist/classificador | sim, se ganhar gloss ou contexto oficial |
| Homophone selection channel | escolha de homófono carrega mensagem | escolhas determinísticas por segmento/chunk; canal por ocorrência fechado | fechada | não como mensagem; sim como pista de lexicon/render |
| Zero omission side channel | omit/retain zero codifica bits | previsível por contexto; capacidade residual não produz conteúdo | fechada como canal | sim como render layer |
| Module/copy grammar | livros são recombinação | fortemente confirmado; MDL favorece recombinação | aceito | principal frente mecânica |
| Pair/mirror geometry | tabela vem de pares não ordenados | 54/55 pureza; 86/88 reversos iguais; exceções localizadas | aceito parcial | sim: origem da matriz ainda aberta |
| `6<->9` automorphism | dígitos 6 e 9 são quase equivalentes | sinal fraco, robusto, não generativo | pista fraca | sim, como quotient/orbit generator |
| E-priority / diagonal E | E tem camada geométrica local | sinais locais reais, mas não tabela inteira | pista local | sim, como subcamada da matriz |
| Frequency-weighted homophone inventory | número de células por símbolo segue frequência interna | correlação alta; apportionment não fecha counts exatos | pista forte de inventário | sim |
| Eye/blink arity | 5 olhos -> 10 eventos -> 55 células | aridade elegante; K5/5x2 falham labels | mecanismo-only | sim, se usar dinâmica/blink sequence e não só grafo estático |
| D&D/Beholder rays | 10 canais inspiram dígitos | weak clue; não prova intenção ou labels | controle/prior | sim, com custo e controles |
| Knightmare/quest mechanisms | mecanismo autoral de puzzle explica fabricação | útil como ontologia/prior; não prova intento privado | prior | sim, como classificação de mecanismos |
| Excalibug | rota linguística Bonelord bloqueada | sem prompt/answer/gloss oficial | bloqueada | só se aparecer fonte oficial |
| Topologia física | shelf/tile/order codifica leitura | fontes públicas não têm slot/ordem suficientes; testes negativos | bloqueada parcial | sim, com manifesto limpo |
| Jekhr/Orcish/etc. | 469 pode ser script intermediário | registradas como comparanda/controles, não chave | benchmark | sim, primeiro recuperar controles |
| Parser/latent-state generator | fórmula real é parser/copy-state | rota mais promissora; ainda teacher-forced/external fields | ativa | sim, principal backlog mecânico |
| Source-free skeleton | gerar op skeleton sem alvo | múltiplas famílias falham; atlas ainda externo | não promovido | sim apenas via latent state conjunto |
| Target digit process | dígitos têm processo prev2 e surpresa em fronteiras | pista real de boundary pruning, não gerador | pista | sim, acoplar a parser fechado |
| Copy hint stream | escolher source por ranking/hints | lower bound útil; bucket structure falha | dependência residual | sim, precisa copy-continuation state |
| Static tie policies/source choice | remover source field por regra simples | políticas estáticas falham; source choice ainda declarado | não promovido | reabrir só com estado/selector pago |
| Lore-number masks | `1`, `3478`, Honeminas, `74032/45331` como masks | controles rejeitam | fechada | não repetir sem nova variável |

Conclusão da tabela: a maioria das frentes semânticas está fechada. As frentes ainda vivas são quase todas de **origem, geração, validação, classificação externa e aquisição de ground truth**.

---

## 4. Reinterpretação da lore por frente

### 4.1 Great Calculator / “assemble language”

Interpretação antiga perigosa:

```text
Great Calculator sabe a tradução.
```

Interpretação mais produtiva:

```text
Great Calculator é uma metáfora de compilador/assembler.
```

A palavra-chave é “assemble”: a evidência mecânica mostra que os livros são montados por módulos, fitas, cópia e renderização. Então a lore não precisa apontar para uma frase escondida; ela pode estar descrevendo o processo de fabricação.

**Teste de reabertura:**  
Tratar “assemble language” como especificação de pipeline:

```text
inventário
-> seleção de símbolos
-> tabela de pares
-> chunks/fita
-> renderização com homófonos
-> omissão de zero
-> livros
```

**Já feito parcialmente:** sim, a stack mecânica atual implementa boa parte disso.

**Ainda não fechado:** transformar o parser em gerador sem oráculo. O mistério vivo é menos “qual palavra significa X?” e mais “qual programa mínimo emite esses dígitos?”.

### 4.2 Honeminas / Tridiag / Donina / Red Light / Magic Web

Interpretação antiga perigosa:

```text
as fórmulas são dicionário, chave aritmética ou plaintext.
```

Interpretação produtiva:

```text
as fórmulas são famílias de indexadores, seletores, gates, vetores, estados ou máscaras de renderização.
```

O projeto já fechou máscaras simples de lore-number e aritmética direta. Portanto não vale repetir “3478 como chave”. O que ainda pode valer é uma reinterpretação em nível de **controle de processo**:

```text
Magic Web / teleport / gate
-> seleção de fonte/destino
-> copy source
-> copy length
-> boundary hazard
-> state transitions
```

**Teste novo proposto:**  
Criar uma taxonomia de operações da lore:

| Motivo | Feature mecânica candidata |
|---|---|
| gate/portal | boundary/open/close |
| teleport | copy jump/source |
| coordinate/vector | source address / target offset |
| red light | exception/priority mask |
| tridiag | diagonal/triangular pair feature |
| formula | declared rule or cost model |
| web | graph of copy dependencies |

Depois, testar essas features **não contra plaintext**, mas contra:

- `op_type`;
- `copy_length`;
- `copy_source_exception`;
- `boundary hazard`;
- `literal/copy transitions`;
- `row0` local E/diagonal layers.

**Critério de promoção:** reduzir bits em holdout e vencer controles de permutação, sem usar label alvo como feature.

### 4.3 Pair / mirror / subjective viewer

Esta é uma das melhores pontes entre lore e mecânica porque row0 é quase uma tabela de pares não ordenados. A inversão `ab <-> ba` quase sempre preserva o símbolo.

Interpretação produtiva:

```text
o “viewer” não lê texto; ele escolhe a orientação/renderização de uma célula par.
```

Isso explica:

- por que a tabela parece não ordenada;
- por que existe uma superfície ordenada renderizada;
- por que o conflito `19/91` importa;
- por que `39` ausente e `93` órfão são metadados da superfície, não erro aleatório.

**Caminho ainda vivo:**  
Modelar a origem da matriz como:

```text
base unordered-pair worksheet
+ orientation/render exceptions
+ 6<->9 quotient
+ local E priority
+ frequency-weighted inventory
```

Não tentar gerar a tabela inteira de uma fórmula aritmética única. Tentar gerar por camadas.

### 4.4 Secret Library `74032 45331`

Status:

- confirmado como âncora externa não glosada;
- não ocorre nos 70 livros;
- não é crib;
- é curto demais/sem significado.

Interpretação produtiva:

```text
não é tradução; é amostra externa para classificar a família geradora.
```

Testes úteis:

1. Parse row0 com omissão de zero permitida?
2. Usa inventário 99-code?
3. Tem compatibilidade com `6<->9` quotient?
4. Compartilha homophone classes?
5. Parece string fabricada pelo mesmo pipeline ou apenas “numeric style”?
6. Se aparecem novos livros da Secret Library, a sequência de mesas/locais forma topologia externa?

**Critério de avanço real:** só vira semanticamente útil com texto oficial associado.

### 4.5 Your True Colour 2012

Status:

- string oficial e novel;
- curta;
- sem gloss;
- não discrimina suficientemente.

Interpretação produtiva:

```text
amostra oficial curta para classificador de origem, não para tradução.
```

Backlog:

- manter como `external_official_short_holdout`;
- testar todo novo gerador contra ela;
- não usar para treinar;
- aceitar apenas classificações probabilísticas: `same_row0`, `same_render`, `same_style_only`, `out_of_family`.

### 4.6 Chayenne

Status:

- public answer com material numérico real;
- melhor lida como reuso de módulos;
- não é resposta semântica.

Interpretação produtiva:

```text
Chayenne valida que material 469 público podia ser composto por colagem de substrings já existentes.
```

Uso futuro:

- holdout de módulo/cópia;
- teste de boundary split;
- controle contra string externa puramente inventada.

Não usar como glossário.

### 4.7 Eye/blink / cinco olhos

A hipótese elegante:

```text
5 olhos -> C(5,2)=10 eventos -> dois eventos -> 55 células não ordenadas
```

Isso encaixa perfeitamente com a escala row0. O problema: os testes K5 e 5x2 falharam em gerar labels.

Interpretação produtiva:

```text
a lore dos olhos pode explicar a aridade/domínio, não necessariamente os labels.
```

Caminho de reabertura:

- abandonar K5 estático como labeler;
- procurar **ordem temporal de blink**, não apenas pares;
- testar sequências de eventos: central/periférico, abertura/fechamento, simetria esquerda-direita, “viewer subjective”;
- exigir sprites/fontes oficiais ou in-game text que indique mapeamento.

Sem fonte externa, olho/blink é mecanismo-only.

### 4.8 D&D / Beholder rays

Interpretação produtiva:

```text
10 eye rays podem inspirar os 10 dígitos, mas não provam nem intent nem labels.
```

Uso seguro:

- prior de ordem dos dígitos;
- controle de “dez canais”;
- comparandum de aridade.

Não usar como prova autoral sem fonte.

### 4.9 Excalibug

Status atual:

```text
blocked_waiting_for_official_source
```

Reabrir apenas se aparecer:

- prompt oficial em Bonelord;
- resposta oficial;
- gloss de NPC;
- texto in-game que relacione Excalibug a 469 numeric.

Até lá, Excalibug é watchlist.

### 4.10 Paradox Tower / Spirit Grounds / Evil Mastermind / Avar Tar

Esses são mais úteis como **controles** que como chaves.

- Paradox Tower: comparandum de livros/riddles/mirror.
- Spirit Grounds/Gate Keeper: controle negativo de “língua estranha + gate”.
- Evil Mastermind fake dictionaries: alerta anti-overfit.
- Avar Tar: negativo para cobertura por módulos.

Isso é valioso porque evita redescobrir falsas pistas.

### 4.11 First Dragon / Dreadeye / Wydrin/Wyrdin / Minotaur mages

Interpretação segura:

```text
watchlist e contexto, não evidência.
```

O uso correto é monitorar se algum futuro texto oficial fornece:

- número 469;
- gloss;
- symbol table;
- phrase translation;
- book-to-text pair;
- instruction that constrains reader/order/viewer.

Sem isso, não promover.

---

## 5. Hipóteses testadas nesta auditoria

### H-A: “Ainda existe tradução direta nos 70 livros”

**Teste de reabertura:**  
Para reabrir, a hipótese precisa sobreviver a pelo menos uma destas condições:

1. vencer os disqualifiers linguísticos;
2. explicar por que recombinação MDL vence linguagem;
3. produzir prosa em holdout;
4. usar ground truth oficial;
5. reduzir descrição sem overfit.

**Resultado:** falha.  
Nenhuma dessas condições aparece nos artefatos atuais.

**Decisão:** não reabrir tradução direta.

### H-B: “A phrase layer pode ser a chave dos livros”

**Teste:**  
Verificar se word-codes das frases aparecem/agrupam/enriquecem nos livros ou se `3478`, `67`, `0`, etc. funcionam como anchors semânticos.

**Resultado:** falha como chave.  
Os códigos relevantes ou não aparecem, ou aparecem como pares row0 com explicação mecânica. `3478` é estrutural (`34|78 = B,E`) e curto demais para provar palavra.

**Decisão:** phrase layer permanece útil como camada separada e possível seed/watchlist, não como decoder.

### H-C: “A lore reabre significado”

**Teste:**  
Separar lore em quatro classes:

```text
ground truth
mechanism
numeric anchor
control/watchlist
```

Só a primeira reabre semântica.

**Resultado:** nenhuma fonte revisitada fornece ground truth. A lore melhora o modelo mecânico, especialmente assembly, pair/mirror, fórmula/gate e aridade dos olhos.

**Decisão:** reabrir lore apenas como mecanismo.

### H-D: “A fórmula existe, mas não é plaintext”

**Teste:**  
Confrontar os avanços mecânicos: module/tape/LZ/parser, row0, zero render, pair geometry, source/length parser.

**Resultado:** passa.  
Esta é a frente viva. Há forte compressibilidade e vários componentes com validação parcial. O bloqueio é transformar atlas/receita com campos externos em parser autoral fechado.

**Decisão:** principal rota P0/P1.

### H-E: “A matriz row0 tem uma origem compacta”

**Teste:**  
Verificar se algum candidato gera os 55 labels com custo menor que lookup e controle positivo.

**Resultado:** ainda não.  
Há pistas locais (`6<->9`, E-priority, diagonal, inventory frequency, mirror/render), mas nada gera a tabela inteira.

**Decisão:** reabrir como busca por **camadas** e não fórmula única.

### H-F: “Topologia física pode destravar ordem ou parser”

**Teste:**  
Verificar se fontes públicas têm `book_id -> tile -> shelf -> slot -> orientation -> version`.

**Resultado:** não.  
Fontes públicas ajudam, mas não têm granularidade/proveniência suficiente. Testes atuais não promovem topologia.

**Decisão:** reabrir só com manifest limpo e direitos/proveniência.

### H-G: “Jekhr/Orcish/etc. podem ser chave intermediária”

**Teste:**  
Antes de aplicar a 469, o método precisa recuperar controles conhecidos.

**Resultado:** ainda benchmark/control, não chave.

**Decisão:** reabrir como harness de validação contra falso positivo.

### H-H: “Música/Sargam/Morse/Braille/códigos humanos podem estar faltando”

**Teste de reabertura:**  
Uma nova família de códigos humanos só entra se:

1. tiver fonte/lore que a justifique;
2. recuperar controles positivos próprios;
3. vencer controles aleatórios;
4. reduzir MDL;
5. não usar plaintext flexível.

**Resultado:** não há evidência no estado público principal de que isso já seja um caminho promovido. Sem âncora, é uma classe P3 de benchmark/controle, não frente principal.

**Decisão:** manter como baixa prioridade, com gates duros, para evitar nova temporada de pareidolia.

---

## 6. O verdadeiro gargalo atual

O gargalo mudou ao longo do projeto:

```text
2024/early 2026:
  encontrar letras/palavras

2026-06-01:
  provar se os livros são linguagem

2026-06-09/10:
  fechar canais residuais

2026-06-18..23:
  explicar fabricação mecânica

agora:
  derivar gerador sem oráculo ou obter ground truth externo
```

O gargalo atual é duplo:

### 6.1 Origem da row0

Ainda não sabemos por que as 55 classes de pares receberam esses símbolos. O lookup funciona, mas a origem autoral da tabela segue exógena.

Sinais úteis:

- unordered/mirror geometry;
- `6<->9` quase simetria;
- E diagonal/local layer;
- inventory frequency allocation;
- directed exceptions `19/91`, missing `39`, orphan `93`;
- zero render relation with `i>=j`;
- eye/blink arity.

Nenhum desses, sozinho, é fórmula.

### 6.2 Parser/generator sem target oracle

A fórmula de compressão atual ainda usa dependências externas:

- seed/material inicial;
- book lengths;
- operation skeleton;
- copy source;
- copy length;
- literal payload;
- control streams.

O projeto já reduziu e estabilizou bastante, mas o parser fechado ainda não emite os livros sem saber o alvo. A auditoria mais recente localiza o problema em copy-state/copy-continuation/source-length, não em mais um teste de boundary simples.

---

## 7. Próximos caminhos priorizados

### P0 — Manter a regra de ground truth oficial

**Objetivo:** impedir retrabalho semântico e capturar qualquer evidência externa real.

**Implementar:**

- `docs/watchlist/official_469_watchlist.md` atualizado;
- `analysis/external_469_string_classifier_20260624/`;
- um registry de strings externas com campos:

```yaml
id:
source_url:
source_type: official|in_game|community|mirror|unknown
date_seen:
exact_digits:
has_gloss: true|false
gloss_text:
row0_parse:
zero_omission_parse:
same_inventory:
module_overlap:
classification:
allowed_use:
blocked_use:
```

**Promove se:**

- há número→texto oficial;
- ou book→texto oficial;
- ou symbol table oficial;
- ou uma string externa longa, oficial e com gloss suficiente para holdout.

**Não promove se:**

- é só número sem gloss;
- é fansite sem fonte;
- é espelho do corpus;
- é solução comunitária sem passar cribs/controles.

### P0 — Reescrever a busca como “programa que emite 469”

**Objetivo:** abandonar “tradução” interna e buscar um gerador mínimo.

**Backlog executável:**

1. Consolidar a fórmula atual em um único `current_generator_state.md`.
2. Separar explicitamente:
   - `learned/scored components`;
   - `declared dependencies`;
   - `encoder-side oracles`;
   - `decoder-side rules`;
   - `target-aware choices`.
3. Criar scoreboard:

```text
row0_origin_delta
closed_loop_exact_books
closed_loop_true_prefix_survival
declared_dependency_bits
external_dependency_fields
copy_source_external_bits
literal_payload_external_bits
book_length_external_bits
```

4. Parar micro-sweeps que economizam menos que o custo de descrição do próprio seletor.

**Promove se:**

- reduz dependências declaradas;
- melhora closed-loop survival;
- produz pelo menos alguns livros não triviais sem target oracle;
- vence shuffled/random controls.

### P1 — Row0 origin por camadas, não fórmula única

**Hipótese nova/ajustada:**

```text
row0 = inventory pressure
     + unordered pair worksheet
     + mirror render
     + local E layer
     + 6<->9 quotient
     + directed exception layer
     + symbol allocation/fill
```

**Por que isso é diferente do que já falhou:**  
Muitas buscas tentaram gerar a tabela inteira de uma vez. A proposta aqui é tratar os sinais aceitos/fracos como subcamadas pagas e exigir que cada camada reduza custo com controles.

**Experimentos:**

1. `row0_layered_mdl_20260624.py`
   - Baseline: raw 55-cell lookup.
   - Add layer 1: homophone inventory counts from symbol frequency.
   - Add layer 2: unordered/mirror domain.
   - Add layer 3: E-priority local rule.
   - Add layer 4: `6<->9` quotient.
   - Add layer 5: directed exceptions.
   - Add layer 6: paid residual fill.

2. Controls:
   - label shuffle;
   - row-preserving shuffle;
   - column-preserving shuffle;
   - inventory-preserving shuffle;
   - exception-set shuffle;
   - same-cost grammar controls.

3. Acceptance:
   - total MDL below lookup;
   - not only exact-hit count;
   - survives best-of-search correction;
   - predicts held-out cells/layers if possible.

**Risco:** virar lookup disfarçado.  
**Mitigação:** pagar cada selector e rodar controles de gramática.

### P1 — `6<->9` quotient como worksheet-base

**Estado atual:** sinal fraco, robusto, não generativo.

**Nova formulação:**

```text
Dígitos base: 0,1,2,3,4,5,Q,7,8
Q renderiza para 6 ou 9
45-cell base worksheet
+ split metadata para 9 órbitas não singletons
+ exception metadata
```

**Experimentos:**

- gerar primeiro labels do worksheet base sem olhar split;
- depois prever splits;
- testar se as exceções `06/09`, `16/19`, `36/39`, `68/89` caem de regra independente;
- comparar contra uma matriz aleatória com mesmo inventário e mesma simetria.

**Promove se:**

- reduz custo total de labels + split metadata;
- não depende de saber símbolos das exceções para escolher exceções;
- vence global, row, column, inventory-preserving controls.

### P1 — E-layer como subprograma real

A E-layer é localmente forte, mas não destrava a matriz inteira. A forma segura de usar:

```text
derive E cells first
then freeze them
then ask whether residual non-E labels become simpler
```

**Experimento:**

- gastar custo da E rule;
- remover E do alvo;
- testar residual de 40/46 células com:
  - quotient order;
  - inventory pressure;
  - pair graph;
  - row/column balance;
  - pair context;
  - symbol frequency allocation.

**Promove se:** o residual fica significativamente mais barato que um lookup residual.  
**Não promove se:** o ganho todo vem dos anchors E.

### P1 — Parser fechado com copy-continuation state

A auditoria recente sugere que boundary detection simples está saturada. O problema está em copiar corretamente material prévio.

**Hipótese:**

```text
469 generator = seed books + latent control stream + copy-continuation state
```

Não:

```text
target text known -> choose best copy/literal segmentation
```

**Experimentos prioritários:**

1. `closed_loop_copy_continuation_parser.py`
   - Estado:
     - current book position;
     - previous copy end;
     - active source candidate;
     - copy age/continuation length;
     - boundary hazard;
     - coarse type:length bucket;
   - Emissões:
     - literal digit;
     - start copy;
     - continue copy;
     - stop copy.
   - Treino:
     - prefix books only.
   - Teste:
     - future books, no teacher forcing.

2. `copy_candidate_inventory_recall.py`
   - medir se o candidato correto está no beam antes de rankear;
   - se não está, o problema é candidate generation;
   - se está, o problema é scoring/ranking.

3. `copy_state_rescue_replay.py`
   - transformar rescues em features;
   - clusterizar rescues por tipo de falha;
   - perguntar se há poucos modos latentes.

**Promove se:**

- true prefix survival > 0 de forma estável;
- pelo menos 1 livro não trivial aparece no beam sem rescue;
- copy-span coverage cresce muito além da política simples;
- bits pagos menores que raw/uniform e controles.

### P1 — Transformar Chayenne/YTC/Secret em classificador externo

Hoje esses itens estão em relatórios separados. Um próximo avanço é ter um classificador único:

```text
external string
-> row0 compatibility
-> zero omission compatibility
-> module overlap
-> tape overlap
-> homophone inventory
-> quotient/mirror consistency
-> same-generator probability
-> allowed use
```

**Casos iniciais:**

- `78567 34334 989 135 65142` (YTC 2012);
- `74032 45331` (Secret Library);
- Chayenne numeric answer;
- Kharos sequence;
- Avar Tar negative control;
- random same-length controls.

**Promove se:**

- classificador distingue YTC/Chayenne de random;
- não confunde Avar Tar;
- não chama Secret Library de “key” sem gloss;
- fornece categoria útil para futuras strings.

### P1 — Topologia limpa

A topologia só reabre se o projeto obtiver dados que hoje faltam:

```text
book text/prefix -> x/y/z -> object/bookcase -> slot/read order -> version/provenance
```

**Backlog:**

1. Manter `clean_topology_contract_template.csv`.
2. Tentar capturar dados in-game atuais com screenshots/observação manual, mas registrar:
   - servidor;
   - data;
   - coordenada;
   - container;
   - ordem de leitura;
   - texto exato;
   - versão.
3. Separar:
   - topologia atual;
   - topologia histórica;
   - community mirror;
   - authoring provenance.

**Promove se:**

- >=20 livros totais e >=10 derivados entram no harness;
- leave-container holdouts positivos;
- feature de topologia reduz bits de `coarse_control`, `op_type` ou `copy_hint_rank_bucket`;
- vence permutações.

### P2 — Comparanda de línguas Tibia antes de 469

**Objetivo:** evitar falso positivo em “script intermediário”.

**Procedimento:**

1. Implementar harness para Jekhr/Deepling:
   - written glyph/symbol -> Latin/pronunciation -> vocabulary/meaning.
2. Testar Orcish, Chakoya, Gharonk, Elven, KAPLAR, spell formulae.
3. Só depois aplicar transformações análogas a row0.

**Promove se:**

- recupera controles conhecidos;
- vence shuffled labels e random conlang lexica;
- reduz MDL;
- produz algo testável em holdout.

**Sem isso:** não aplicar a 469.

### P2 — Sargam/música/Morse/Braille como controles, não como aposta

Essas famílias podem ser úteis por um motivo: elas são **códigos humanos de baixa aridade** com transformações intermediárias. Mas são perigosas porque geram muita pareidolia.

**Uso permitido:**

- benchmark negativo;
- teste de pipeline;
- controle de false positives;
- comparação de compressão.

**Uso bloqueado:**

- mapear símbolos a notas/letras até aparecer frase;
- escolher escala depois de ver saída;
- aceitar saída “parecida” com palavra.

**Critério de abertura real:**

- fonte/lore que cite som, canto, nota, ritmo, blink temporal ou spell formula;
- recuperação de controles;
- holdout;
- custo pago.

### P2 — Phrase layer como seed mecânico, não semantic key

A busca por “phrase seed” não apareceu como frente óbvia no estado público lido nesta auditoria, embora várias buscas de lore-seed/PRNG já tenham sido realizadas. A forma segura de reabrir seria mínima:

```text
phrase codebook codes
-> seed/order/inventory prior
-> row0 layer or generator control
```

Não:

```text
phrase codebook -> livro traduzido
```

**Experimento:**

- usar apenas códigos atestados/reconstruídos com confidence label;
- gerar ordens de símbolos/dígitos/pair cells;
- comparar contra lore seeds já testados e random same-length;
- pagar custo de escolher seed.

**Promove se:** melhora row0 layered MDL ou generator control sob controles.  
**Provavelmente falha:** se repetir lore-number mask/seed PRNG já rejeitados.

---

## 8. Backlog executável

### P0.1 — Criar `external_469_string_classifier`

**Path sugerido:**

```text
analysis/external_469_string_classifier_20260624/
  README.md
  external_string_registry.yaml
  classify_external_string.py
  reports/final_external_string_classifier.md
```

**Entradas iniciais:**

- YTC 2012;
- Secret Library `74032 45331`;
- Chayenne;
- Kharos;
- Avar Tar;
- random controls.

**Saídas:**

```yaml
row0_parse_status:
zero_omission_status:
module_overlap_score:
tape_overlap_score:
homophone_inventory_score:
same_generator_class:
semantic_authority:
allowed_use:
```

### P0.2 — Criar `current_formula_boundary.md`

**Objetivo:** consolidar o estado mecânico atual em uma página curta que responda:

- qual é o melhor bound atual?
- quais campos ainda são externos?
- quais campos são encoder-side?
- quais são decoder-side?
- quais têm parser parcial?
- qual é o próximo blocker?

Isso evita que micro-auditorias obscureçam o objetivo.

### P0.3 — Congelar regra anti-pareidolia para novas frentes

Toda frente nova precisa preencher:

```yaml
hypothesis:
prior_source:
target:
training_data:
holdout:
controls:
mdl_cost:
promotion_gate:
blocked_uses:
expected_failure_mode:
```

Sem isso, não entra.

### P1.1 — Row0 layered MDL

**Pergunta:** as pistas fracas juntas batem lookup?

**Features iniciais:**

- unordered-pair geometry;
- `6<->9` quotient;
- E diagonal/priority;
- inventory frequency allocation;
- directed exception layer;
- zero-render shared predicate;
- homophone context clustering.

**Controles obrigatórios:**

- label shuffle;
- inventory-preserving shuffle;
- row/column preserving;
- exception-set shuffle;
- grammar best-of-search penalty.

### P1.2 — Closed-loop copy-continuation parser

**Pergunta:** o parser consegue emitir livros sem target teacher forcing?

**Meta inicial realista:**

- não exigir 70/70;
- buscar true-prefix survival > 0;
- buscar 1 livro não trivial no beam;
- medir recall do copy candidate set.

**Hard cases citados nos relatórios:**

- livros `53`, `51`, `35`, `58`;
- book `66` como caso de sparse parser;
- book `65` como stress de path instability;
- books `26`, `34`, `49` como instabilidades residuais em modos neutralizados.

### P1.3 — Copy-candidate generation antes de ranking

**Pergunta:** o source correto sequer está no beam?

Separar:

```text
candidate_generation_recall
vs
candidate_ranking_accuracy
```

Se recall é baixo, nenhum scoring simples salva. Se recall é alto, testar priors.

### P1.4 — Coarse control + composition + copy hint integration

O melhor candidato de controle hoje parece estar na decomposição:

```text
type:length_bucket
+ composition index
+ literal payload
+ copy hint rank
```

**Próximo teste:** integrar isso ao parser fechado, não apenas a ledger separada.

### P1.5 — Topologia limpa

**Path sugerido:**

```text
analysis/clean_topology_acquisition_20260624/
  clean_topology_contract.csv
  source_notes.md
  topology_v9_integration_report.md
```

**Critério mínimo para rodar harness:**

- 20 livros totais;
- 10 derivados;
- rights/provenance claros.

### P2.1 — Tibia language benchmark harness

**Path sugerido:**

```text
analysis/tibia_language_benchmark_harness_20260624/
```

**Primeiro alvo:** Jekhr/Deepling.  
**Objetivo:** provar que o método recupera uma língua Tibia conhecida antes de tentar 469.

### P2.2 — Phrase-seed mechanical audit

**Pergunta:** os códigos da phrase layer servem como seed mecânico?

**Cuidado:** provavelmente parcialmente coberto por lore-seed searches. Rodar primeiro uma busca de duplicidade nos scripts/relatórios.

### P2.3 — Eye/blink temporal model

**Pergunta:** o erro dos modelos K5/5x2 foi usar estática em vez de dinâmica?

**Dados necessários:**

- sprites oficiais ou capturas;
- frames/blinks;
- ordem temporal;
- central/peripheral state;
- source confidence.

Sem isso, não promover.

### P3.1 — Human-code comparanda

Morse, Braille, música/Sargam, runas, keypad, seven-segment etc. entram só como controles com custo pago. Não são prioridade.

---

## 9. O que explicitamente não fazer mais

Não gastar ciclos em:

- tradução direta dos 70 livros;
- novas substituições símbolo→letra sem cribs externos;
- German/MHG “mais uma vez”;
- anagramas ou frases semi-English;
- BENNA/TELBENNA/ENNAI como vocabulário;
- word-code das frases aplicado aos livros;
- lore-number masks simples;
- PRNG/hash sem evidência e sem MDL;
- usar unglossed numeric anchors como se fossem gloss;
- aceitar fansite/community solution sem controles;
- escolher método depois de ver palavras bonitas.

Regra prática:

```text
Se o output parece texto mas não sobrevive holdout/controle/MDL, é pareidolia.
Se o output reduz bits e reconstrói dígitos, é mecânico.
Se o output vem de CipSoft/in-game com gloss, é ground truth.
```

---

## 10. Métricas de progresso recomendadas

Substituir “atividade” por métricas:

| Métrica | Move tradução? | Move fórmula? | Observação |
|---|---:|---:|---|
| `official_gt_count` | sim | sim | número→texto/livro→texto/symbol table |
| `new_external_string_classified` | talvez | sim | sem gloss é só classificação |
| `row0_layered_mdl_delta` | não direto | sim | precisa vencer lookup + controles |
| `closed_loop_exact_books` | não direto | sim | principal métrica parser |
| `true_prefix_survival_rate` | não direto | sim | early signal para parser |
| `copy_candidate_recall` | não direto | sim | separa pruning de ranking |
| `declared_dependency_bits` | não direto | sim | deve cair sem target oracle |
| `external_dependency_fields` | não direto | sim | manter ledger |
| `topology_clean_coverage` | talvez | sim | só com provenance |
| `known_language_controls_recovered` | não | sim | valida métodos intermediários |
| `semantic_translation_delta` | sim | não necessariamente | hoje permanece zero |

---

## 11. Estratégia de 30/60/90 dias

### 30 dias — organizar o campo

1. Criar classificador de strings externas.
2. Consolidar fórmula atual e dependências.
3. Criar row0 layered MDL baseline.
4. Criar template de hipótese para novas frentes.
5. Abrir issues P0/P1 com gates.

### 60 dias — atacar os dois gargalos reais

1. Rodar row0 layered MDL.
2. Rodar closed-loop copy-continuation parser em hard cases.
3. Medir copy-candidate recall.
4. Integrar coarse control + copy hint em parser.
5. Rodar classificador em YTC/Secret/Chayenne/Kharos/Avar Tar.

### 90 dias — buscar evidência externa ou fechar nova fronteira

1. Atualizar watchlist oficial/in-game.
2. Tentar obter manifesto topológico limpo.
3. Rodar benchmark de línguas Tibia.
4. Decidir se:
   - row0 origin avançou;
   - parser closed-loop tem sobrevivência;
   - external strings classificam família;
   - alguma frente P2 merece P1.

---

## 12. Conclusão

O mistério não está “sem caminho”. Ele está sem caminho **semântico interno**.

A hipótese mais honesta hoje é:

```text
469 livros = artefato numérico fabricado por processo mecânico,
com atmosfera/lore matemática,
não corpus linguístico traduzível por substituição.
```

Mas ainda há dois mistérios reais:

1. **Qual foi a fórmula/receita original da matriz row0?**
2. **Qual programa fechado emite os livros sem usar o texto-alvo como oráculo?**

E há uma condição que pode mudar tudo:

```text
novo ground truth CipSoft/in-game
```

Portanto o plano correto não é “tentar mais traduções”. É:

- proteger o projeto contra pareidolia;
- transformar lore em features mecânicas testáveis;
- reduzir dependências externas do gerador;
- classificar toda string externa oficial;
- vigiar por ground truth real;
- e só chamar algo de tradução quando houver autoridade semântica.

Se existe uma “solução” restante, ela provavelmente é uma **solução de fabricação/validação**, não uma frase escondida em inglês ou alemão.
