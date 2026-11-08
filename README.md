# 🔨 Anvil Modeler

Agente em **LangGraph** que transforma **descrição + concept art** em modelos 3D no **Blender**,
operando o Blender de verdade pelo **MCP** e verificando o próprio resultado por render.

Genérico por padrão (um carro, uma casa, uma cadeira), com padrão de qualidade alto: nada de
low-poly nem peças primitivas empilhadas. Regras de um projeto específico (ex.: o jogo Elpis)
entram como uma camada opcional.

Trabalho da Unidade II (RAG agêntico, MCP, skills, memória e guardrails).

## Arquitetura

![Grafo do harness](docs/grafo_harness.png)

_Gerado com `python scripts/desenhar_grafo.py` (LangGraph `draw_mermaid_png`). Linhas tracejadas = arestas condicionais._

```
descrição ─► concept ─► plan ─► verify_api ─► retrieve ─► code ─► guard ─► execute ─► render ─► evaluate
             (SDXL      (spec +  (nomes conferidos (docs do   (Claude) (AST)   (MCP)     (MCP)    (juiz visual)
              local)    plano    ao vivo no        que faltou)    ▲                                  │
                        de API)  Blender, via MCP)                └──────── reprovado e iter < N ────┘
```

| Peça do trabalho | Onde está |
|---|---|
| **LangGraph** | `src/anvil_modeler/graph.py`, `nodes.py`, `state.py` |
| **MCP** | `blender.py` — sessão stdio com o MCP do Blender (executar código, render, busca na doc) |
| **Verificação de API ao vivo** | nó `verify_api`: o planner lista o que o código vai usar (modificadores, nós, operadores, enums) e o Blender aberto confirma, pelo MCP, se existe nesta versão e com que nomes; o gerador recebe essa ficha |
| **RAG agêntico** | nó `retrieve`: documentação do `bpy` buscada a partir das consultas do planner e do que a verificação não encontrou |
| **Skills** | `skills/` em camadas, no formato das skills do Claude (`skills.py`) — ver abaixo |
| **Biblioteca de materiais** | `blender_lib.py` — injetada no Blender antes de cada script |
| **Guardrails** | `guardrails.py` — validação AST antes de rodar código no Blender |
| **Memória** | estado do grafo com histórico de tentativas (`attempts`) + `runs/<id>/run.json` |
| **Interface** | `app/streamlit_app.py` |
| **Avaliação** | `experiments/run_benchmark.py` — comparativo com e sem harness |

### Modos (o comparativo)

| Modo | Planner + skills | RAG | Loop de verificação |
|---|---|---|---|
| `baseline` | – | – | – (uma tentativa) |
| `skills_only` | ✔ | ✔ | – |
| `loop_only` | – | – | ✔ |
| `full` | ✔ | ✔ | ✔ |

Todos os modos usam o mesmo modelo, o mesmo concept e o mesmo juiz.

## Modelos locais (Ollama)

```powershell
pip install -e ".[local]"
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5vl:7b
```
**Ollama no WSL, Anvil no Windows:** o Anvil precisa rodar no Windows (junto do Blender e do MCP);
o Ollama pode ficar no WSL servindo a API. No WSL: `OLLAMA_HOST=0.0.0.0:11434 ollama serve`.
No Windows, teste `curl http://localhost:11434/api/tags`; se não responder, use o IP do WSL
(`hostname -I` no WSL) em `ANVIL_OLLAMA_URL`.

Configure o provedor por papel no `.env` (ver `.env.example`): gerador, juiz e tarefas rápidas podem
ser locais, pela API ou misturados. Atenção: o **juiz** e o planner com concept precisam de um modelo
**com visão**; o planner precisa seguir JSON Schema. Modelos pequenos erram mais nomes de API, e é aí
que o `verify_api` mais ajuda.

## Skills em camadas

```
skills/
├── base/qualidade-visual       sempre: silhueta, 3 camadas de forma, nada de low-poly/blocos
├── tecnicas/                   o planner escolhe pela FORMA do objeto
│   ├── hard-surface  organico  arquitetura  veiculos  props-e-mobilia  roupas-e-tecidos
├── superficies/                o planner escolhe pelo que o objeto É FEITO
│   ├── tecidos-materiais  pele  pelos-e-penas  escamas-e-carapacas
├── materiais/biblioteca-pbr    sempre: como usar anvil_material / anvil_assign / anvil_outline
├── estilos/                    um, escolhido pelo usuário (padrão: realista)
│   ├── realista  cel-shading
└── projetos/elpis/             opcional (--project elpis): regras do jogo, com prioridade
```

O planner vê só o **catálogo** (nome + descrição) das técnicas, das superfícies e do projeto ativo e escolhe as
relevantes; só o conteúdo delas vai para o gerador de código. Para criar uma skill nova, basta
uma pasta com `SKILL.md` (frontmatter `name` e `description`) na camada certa.

**Materiais:** o gerador não escreve nós de shader; chama `anvil_material("car_paint",
color=(0.8, 0.1, 0.1))`. Os 22 presets (metais, vidros, borracha, madeira, tijolo, telha,
concreto, tecido…) se adaptam ao estilo. Para conferir visualmente, rode
`experiments/teste_materiais.py` dentro do Blender (cena temporária, não mexe na sua).

## Setup (Windows)

```powershell
cd Documents\anvil_modeler
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pip install -e ".[imagegen]"   # opcional: gerador de concept local (SDXL-Turbo, ~6-8 GB VRAM)
copy .env.example .env         # coloque sua ANTHROPIC_API_KEY
copy config\mcp_servers.json.example config\mcp_servers.json
```

**`config/mcp_servers.json`**: copie o `command` e os `args` do servidor do Blender que já está
no Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`, chave `mcpServers`).
O Blender precisa estar aberto com o add-on do MCP ativo.

> O harness cria as coleções `ANVIL_<asset>` (limpa a cada tentativa) e `ANVIL_STAGE`
> (câmera e sol), troca o mundo da cena pelo estúdio `ANVIL_WORLD` e ajusta a resolução.
> No render, o que não é do asset fica escondido e é restaurado depois; nada fora da coleção
> do asset é apagado. Mesmo assim, prefira um `.blend` dedicado aos testes.

Sem GPU? Use `ANVIL_IMAGE_BACKEND=none` (só descrição) ou passe um concept pronto com `--concept`.

## Uso

```powershell
# uma rodada pelo terminal
anvil "Sedan vermelho de quatro portas com rodas de liga leve" --name carro --mode full
anvil "Caixote de suprimentos da base lunar" --name caixote --style cel-shading --project elpis

# interface
streamlit run app/streamlit_app.py

# comparativo sem harness vs com harness
python experiments/run_benchmark.py --modes baseline full --only carro_sedan casa_terrea
python experiments/run_benchmark.py --repeats 3          # todos os assets e modos

# testes dos guardrails
pytest
```

Cada rodada salva em `runs/<run_id>/`: concept, render de cada iteração, `run.json` e `final_code.py`.
O benchmark gera `results.csv`, `results.json` e `grid.png` (assets × modos).

## Métricas do comparativo

- **Técnicas**: iterações, erros de execução/guardrail.
- **Geometria** (extraídas do Blender): objetos, faces, `raw_boxes` (objetos com ≤6 faces, indício
  de *primitive stacking*), modificadores, materiais, arestas não-manifold.
- **Visual**: `loop_score` (nota do juiz dentro do loop) e `blind_score` (nova avaliação, sem saber
  o modo). `human_score` fica vazio para vocês preencherem às cegas.

⚠️ No modo `full` o modelo otimiza contra o mesmo juiz que dá a nota, então o `blind_score` tende a
favorecer o loop. Para o relatório, use `human_score` como métrica principal ou um
`ANVIL_JUDGE_MODEL` diferente do gerador.

## Começo rápido (para quem clonou)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,local]"
cp .env.example .env            # escolha a opção A (local, grátis) ou B (sua chave de API)
python -m pytest -q             # confere a instalação, sem gastar nada
streamlit run app/chat.py       # chat de dúvidas sobre o Blender (o índice da documentação já vem no repositório)
```
- **Sem chave de API:** use a opção A do `.env` (Ollama + `ollama pull qwen2.5-coder:7b`).
- **Sem Ollama:** use a opção B com a sua chave; a busca da documentação funciona só com BM25.
- **Modelagem no Blender:** veja a seção abaixo (Blender aberto com o add-on MCP, `config/mcp_servers.json`).

## Como rodar (WSL + Ollama + Blender no Windows)

### 1. Pré-requisitos (uma vez só)

**Blender (Windows)**
- Blender 5.x com o add-on oficial **Blender MCP** (Blender Lab) instalado e ativado.
- Com o Blender aberto, inicie o servidor do add-on. Ele escuta em `localhost:9876`.

**Rede do WSL enxergando o Windows**
Em `C:\Users\<voce>\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```
Depois rode `wsl --shutdown` no PowerShell e abra o WSL de novo.

**Ollama (no WSL)**
```bash
ollama pull qwen2.5-coder:7b
sudo systemctl edit ollama
```
No editor, entre os comentários:
```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
```
Salve e aplique:
```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
systemctl show ollama --property=Environment --no-pager | tr ' ' '\n' | grep OLLAMA
```

**Projeto** (só na primeira vez; se a `.venv-wsl` já existe, pule e vá para o passo 3)
```bash
cd ~/anvil_modeler
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install --upgrade pip
pip install -e ".[dev,local]"
pip install -e ~/blender_mcp/mcp        # servidor MCP da comunidade (blender-mcp)
cp .env.example .env
```

### 2. `.env` para modelo local

```env
ANVIL_PROVIDER=ollama
ANVIL_FAST_PROVIDER=ollama
ANVIL_MODEL=qwen2.5-coder:7b
ANVIL_FAST_MODEL=qwen2.5-coder:7b
ANVIL_OLLAMA_URL=http://localhost:11434
ANVIL_JUDGE=off
ANVIL_IMAGE_BACKEND=none
ANVIL_NUM_CTX=8192
ANVIL_MAX_ITERS=3
ANVIL_RENDER_RES=768
ANVIL_STYLE=realista
```

### 2b. `.env` para a API (Haiku)

```env
ANVIL_PROVIDER=anthropic
ANVIL_FAST_PROVIDER=anthropic
ANVIL_MODEL=claude-haiku-5-5
ANVIL_FAST_MODEL=claude-haiku-5-5
ANVIL_JUDGE=off
ANVIL_IMAGE_BACKEND=none
ANVIL_USD_BRL=5.5          # opcional: mostra o custo também em reais
```
A chave vai só no terminal, nunca no repositório:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Ao final de cada run, o `anvil` mostra os tokens e o custo do asset (o `run.json` guarda o mesmo em
`usage.cost_usd`). Preços em `config.py` (`PRICES`); para outro modelo, `ANVIL_PRICE="entrada,saida"` em US$ por milhão.

### 3. Antes de cada sessão

```bash
cd ~/anvil_modeler && source .venv-wsl/bin/activate
# Blender aberto, com o servidor do add-on ligado
python -c "import socket; socket.create_connection(('localhost', 9876), 3); print('Blender OK')"
```

### 4. Testar as ferramentas (servidor `anvil-tools`)

```bash
python scripts/testar_ferramentas.py
```
O script lista as ferramentas pelo MCP, monta uma mesinha de teste e renderiza em `runs/agente/`.

### 5. Rodar o agente

```bash
anvil "<descrição>" --name <nome> --mode <modo> [--style realista|cel-shading] [--project elpis] [--sem-juiz]
```

| Modo | O que liga |
|---|---|
| `baseline` | só o modelo, sem harness |
| `skills_only` | skills, sem loop de correção |
| `loop_only` | loop de correção, sem skills |
| `full` | harness completo: plano, verify_api, skills, guardrails e loop |
| `agente` | plano + o modelo monta o asset chamando as ferramentas do `anvil-tools`, peça por peça (sem escrever código) |

**Comparativo com e sem harness:**
```bash
anvil "uma cadeira de madeira" --name cadeira --mode baseline --sem-juiz
anvil "uma cadeira de madeira" --name cadeira --mode full --sem-juiz
anvil "uma cadeira de madeira" --name cadeira --mode agente --sem-juiz
```

No modo agente, cada chamada aparece no log como `[agente] caixa({...}) -> ok`, e o `final_code.py` do run guarda a sequência de chamadas. O limite de rodadas é `ANVIL_AGENT_STEPS` (padrão 40).

Alvo da modelagem (`ANVIL_ALVO` ou `--alvo`):
- **jogo** (padrão): orçamento de tempo real (ex.: móvel 1–5 mil triângulos, personagem 15–40 mil);
- **completo**: render/portfólio, mais denso (ex.: personagem 100 mil–1 milhão).
O orçamento vai para o prompt, o `run.json` registra `tris` e `orcamento`, e o `anvil` avisa se passar ou ficar abaixo.

O modo agente tem dois perfis (`ANVIL_PERFIL` ou `--perfil`):
- **fraco** (padrão com Ollama): ferramentas prontas (caixa, revolucao, tubo_por_curva...) e o harness confere a
  geometria, sobe peças abaixo do chão, cobra peças que faltam e bloqueia loops;
- **forte** (padrão com a API): o modelo escreve o próprio bpy com `executar_python` e confere quando quiser
  (`listar_objetos`, `conferir`, `metricas`, `verificar_api`); fica só o guardrail de segurança.

**Saídas:**
- No Blender, na coleção `ANVIL_<nome>_<modo>`. Cada modo fica deslocado para não sobrepor os outros.
- Em `runs/<nome>_<modo>_<data>/`: `run.json` (iterações, métricas e tokens), `final_code.py` e os renders.

### 6. Desenhar o grafo

```bash
python scripts/desenhar_grafo.py     # gera docs/grafo_harness.png
```

### 7. Problemas comuns

| Sintoma | Causa e correção |
|---|---|
| `ConnectionRefusedError` na porta 9876 | Blender fechado, servidor do add-on desligado ou WSL sem `networkingMode=mirrored`. |
| Erro de autenticação "Bearer " vazio | O `.env` não existe (você editou o `.env.example`). Rode `cp .env.example .env`. |
| `ollama ps` mostra parte na CPU | Diminua `ANVIL_NUM_CTX` (6144 ou 4096), rode `ollama stop qwen2.5-coder:7b` e tente de novo. Deixe o viewport do Blender em Solid. |
| `address already in use` ao rodar `ollama serve` | O serviço já está rodando; não precisa iniciar. |
| `anvil: error: --name` | O `--name` é obrigatório. |
| Render "Nenhum objeto renderizável" | O script não criou nada: veja o erro do guard/execute no log e o `final_code.py`. |

## Assistente de perguntas sobre o Blender (RAG agêntico + chat)

Chat em Streamlit que responde dúvidas sobre o Blender 5.2 com base na documentação oficial, citando as fontes.

```
START → guardrail_entrada ─(bloqueado)→ END
             ▼
          agente ──► ferramentas ──(buscou)──► avaliar ─(relevante)─► agente
             │       (buscar_documentacao,         │
             │        carregar_skill,         (não serve, até 2x)
             │        verificar_api via MCP)       ▼
             ▼                                 reescrever ──► avaliar
      guardrail_saida → END
```

- **RAG agêntico:** o agente decide quando buscar; o nó `avaliar` julga se os trechos respondem; se não, `reescrever`
  refaz a busca com os termos da documentação (em inglês), no máximo 2 vezes.
- **Índice híbrido:** BM25 (nomes exatos como `BevelModifier.segments`) + vetores do `nomic-embed-text` (sentido),
  unidos por Reciprocal Rank Fusion. Embeddings locais no Ollama (a Anthropic não tem modelo de embeddings).
- **Skills (`skills/assistente/`):** `responder-com-fontes` (sempre), `codigo-bpy` e `solucao-de-problemas`
  (o agente carrega pelo catálogo com `carregar_skill`).
- **MCP:** `verificar_api` do servidor próprio `anvil-tools` confere nomes da API no Blender aberto (opcional).
- **Guardrails:** entrada (regras contra injeção/pedido de segredos + classificador de tema); saída (remove chaves,
  avisa sobre código perigoso, garante a lista de fontes).
- **Memória:** checkpointer SQLite do LangGraph (`data/memoria.sqlite`), uma thread por conversa.
- **Modelo:** o mais barato (`ANVIL_RAG_MODEL`, padrão = `ANVIL_FAST_MODEL`, ex. Haiku); dá para usar o qwen local
  com `ANVIL_RAG_PROVIDER=ollama ANVIL_RAG_MODEL=qwen2.5-coder:7b`.

### Como rodar
```bash
pip install -e ".[dev,local]"                 # dependências novas (numpy, sqlite checkpointer)
sudo systemctl start ollama && ollama pull nomic-embed-text
python scripts/preparar_docs.py               # baixa a documentação (já feito: data/docs, 290 páginas)
python scripts/indexar_docs.py                # pedaços + embeddings -> data/index
python scripts/avaliar_rag.py                 # acerto@3 e MRR: BM25 x vetorial x híbrida (grátis)
python scripts/avaliar_rag.py --agentico      # + laço avaliar/reescrever (custa centavos)
streamlit run app/chat.py                     # o chat
```

## Limitações conhecidas

- **Humanos:** massas fundidas por remesh dão aspecto de "massinha" e rosto estranho (vale da
  estranheza). Roupas já usam molde + simulação de tecido (`roupas-e-tecidos`), mas corpo e rosto
  ficam para uma etapa própria, provavelmente partindo de um corpo base pronto (ex.: MPFB/MakeHuman).
- As skills de `superficies/` ainda não foram validadas em teste de modelagem.

## Roadmap

- [ ] Primeira rodada do benchmark (caixote, porta, capacete)
- [ ] Biblioteca de exemplos aprovados como RAG adicional (few-shot de scripts que funcionaram)
- [ ] Exportar `.glb` para a Unity
- [ ] Rodar o gerador de código com modelo local (Ollama) e comparar com a API
