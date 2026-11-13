# Revisão de código — Anvil Modeler (Avaliação da Unidade II)

Revisão feita requisito a requisito contra o enunciado da tarefa, com a suíte rodando
(`python -m pytest`) antes e depois das mudanças.

## Veredito geral

**Os 7 requisitos da tarefa já estavam implementados e funcionando** (23 testes originais
passando). Esta revisão corrigiu 4 lacunas reais, completou o que faltava para o relatório
(10 casos de teste automatizados, diagrama do grafo do chat, função de cada nó no README) e
acrescentou 6 testes novos. Nada do que já funcionava foi reescrito.

## O que foi corrigido

### 1. Ferramentas chamadas e skills carregadas agora aparecem em TODA resposta (requisito 7)
Antes elas só apareciam dentro do expander "Como cheguei nesta resposta", que some quando o
toggle "Mostrar o caminho do agente" é desligado — e o enunciado pede a exibição em cada
resposta. Agora cada resposta traz a linha compacta `🔧 Ferramentas: … — Skills: …` sempre, e o
expander continua com o trace detalhado (com as buscas feitas).
**Arquivo:** `app/chat.py` (novas `_ferramentas_usadas` e `mostrar`).

### 2. Guardrail de saída remove tokens reais de provedores (requisito 6 — vazamento de dados)
O regex de segredo só cobria `sk-ant-…` e o padrão genérico `api_key=…`. Agora cobre também
OpenAI (`sk-…`/`sk-proj-…`), AWS (`AKIA…`), GitHub (`ghp_…`/`gho_…`/…), Google (`AIza…`) e
Slack (`xox…`), além de `secret=`/`token=`/`senha=`.
**Arquivo:** `src/anvil_modeler/rag/assistente.py` (`SEGREDO`).
**Teste novo:** `test_segredos_de_provedores_removidos`.

### 3. Guardrail de entrada cobre sequestro de papel (requisito 6 — prompt injection)
Novos padrões de injeção: "assuma o papel de", "act as", "você é agora…", e
"mostre/revele o conteúdo do arquivo/prompt/sistema". Continua bloqueando ANTES de chamar o
modelo (sem gastar tokens) — o teste novo prova isso (`rec.llm.calls == 0`).
**Arquivo:** `src/anvil_modeler/rag/assistente.py` (`INJECAO`).
**Teste novo:** `test_sequestro_de_papel_bloqueado_sem_chamar_o_modelo`.

### 4. Citações agrupadas "[1, 2]" agora contam como fontes
O parser só entendia `[1]`; com `[1, 2]` a resposta caía no fallback das 3 primeiras fontes,
que pode listar trechos não citados. Agora o guardrail de saída aceita `[1]`, `[2]` e `[1, 2]`.
**Arquivo:** `src/anvil_modeler/rag/assistente.py` (`guardrail_saida`).
**Teste novo:** `test_citacoes_agrupadas_sao_aceitas`.

### 5. Diagrama do grafo do assistente
`scripts/desenhar_grafo.py` gerava só o PNG do harness. O agente da tarefa é o assistente de
chat — agora o script gera também `docs/grafo_chat.png` (mesma técnica, `draw_mermaid_png`,
sem Blender e sem gastar API).

## O que foi acrescentado

### `scripts/executar_testes.py` — os 10 casos de teste exigidos no relatório
- **Cobertura:** RAG agêntico (1–3), skills `codigo-bpy` e `solucao-de-problemas` (4–5), MCP
  próprio `anvil-tools` (6), MCP da comunidade `blender-mcp` (7), memória entre turnos (8) e
  guardrails (9–10). Desafiadores: 2 (gíria fora da doc), 3 (assunto fora do acervo), 9 (injeção)
  e 10 (fora de escopo + script destrutivo) — 4 casos no limite do agente.
- **Como funciona:** cada caso roda contra o `build_chat_graph` real, com thread própria do
  checkpointer (o caso 8 usa duas threads de propósito); a checagem é automática a partir do
  trace e dos metadados que o grafo já produz (skills carregadas, chamadas MCP, fontes, bloqueios,
  `check_code` nos blocos de código).
- **Sem Blender:** os casos 6 e 7 saem como "não executado" com o motivo, e não entram na taxa.
- **Saídas:** `docs/casos_de_teste.md` (tabela entrada/esperado/obtido/aprovado + taxa de acerto +
  análise dos erros + evidências) e `data/avaliacao_casos.json` (respostas completas e trace —
  material para o vídeo).
- **Uso:** `python scripts/executar_testes.py` (ou `--casos 2,9,10`). Custa centavos com Haiku.

### `tests/test_chat_extra.py` — 6 testes novos (29 no total)
Isolamento de threads e continuidade na mesma thread (memória), skills/ferramentas nos metadados
da resposta final (o que a interface exibe), segredos de provedores removidos, sequestro de papel
bloqueado sem chamar o modelo, e citações agrupadas aceitas.

### `README.md`
- Participantes no topo (marcadores 【preencher nome】 para trocar antes do push);
- Tabela "Função de cada nó" dos dois grafos (assistente e harness) com as arestas resumidas;
- Linha dos casos de teste na tabela de componentes; seção "Casos de teste" com o comando e o
  local para colar a tabela gerada;
- Passo 7 do "Como rodar" atualizado (casos de teste) e passo 6 menciona os dois PNGs.

### `.gitignore`
`data/testes_memoria.sqlite*` e `data/avaliacao_casos.json` (saídas do script de testes).

## Como aplicar no repositório

1. Copie os arquivos deste pacote sobre os do repositório (os caminhos são idênticos).
2. Troque os 【preencher nome】 no `README.md`.
3. `pip install -e ".[dev,local]" && python -m pytest -q` — deve dar **29 passed**.
4. Configure `config/mcp_servers.json` (exemplo: `config/mcp_servers.json.example`), abra o
   Blender com a ponte MCP, e rode `python scripts/executar_testes.py` com o `.env` configurado.
   Depois cole o `docs/casos_de_teste.md` gerado na seção "Casos de teste" do README.

## O que foi verificado e NÃO precisou de mudança

- **Requisito 1 (grafo próprio):** os dois agentes são `StateGraph` com estado, nós e arestas
  definidos por vocês — nada de `create_react_agent`.
- **Requisito 2 (RAG agêntico):** o modelo decide buscar, o nó `avaliar` julga os trechos e o
  `reescrever` refaz a busca até 2 vezes; a origem dos documentos está informada
  (`data/docs/CREDITOS.md` — manual e API oficial do Blender 5.2, com URL e licença).
- **Requisito 3 (MCP):** servidor próprio (`anvil-tools`, FastMCP, 17 ferramentas de alto nível)
  e da comunidade (`blender-mcp`) configurados e usados de verdade.
- **Requisito 4 (skills):** catálogo na mensagem de sistema, carregamento sob demanda via
  `carregar_skill`, skills multi-etapas que não duplicam ferramenta nenhuma.
- **Requisito 5 (memória):** checkpointer SQLite com uma thread por conversa, que sobrevive a
  reiniciar o Streamlit; `_historico` manda só o necessário para o contexto.
- **Requisito 6 (guardrails):** entrada (injeção, segredos, fora de escopo, mensagem longa) e
  saída (segredos, código perigoso, citações/fontes) como nós do grafo — e ainda o guardrail de
  código AST no `guard` do harness e no `executar_python` do servidor próprio.
- Detalhes de robustez já bem resolvidos: prompt de sistema fixo dentro da pergunta (evita o erro
  de assinatura de thinking da API), retry sem thinking, resposta vazia com 2ª tentativa, anti-loop
  no modo agente, teto de custo, consertos previsíveis de AST, adoção de objetos criados fora da
  coleção do asset.
