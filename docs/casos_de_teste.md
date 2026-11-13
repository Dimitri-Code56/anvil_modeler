## Casos de teste

Executados em 13/11/2026 07:00 contra o grafo real do assistente (`build_chat_graph`), com modelo `ollama:qwen2.5-coder:3b`, índice de 1278 trechos (BM25 + vetores (híbrido)). Cada caso roda em uma thread própria do checkpointer; o caso 8 testa dois turnos na mesma thread e uma thread nova. Os casos 11 e 12, fora da taxa principal, aparecem em seção própria no fim.

| # | Componente | Entrada | Resultado esperado | Resultado obtido | Passou? |
|---|---|---|---|---|---|

**Taxa de acerto:** 0/0 casos aprovados.

**Análise dos erros:** nenhuma falha nos casos executados. Os limites continuam nos casos 🔥 (reformulação de busca e recusas), que dependem do modelo e podem falhar em outra rodada.

### Casos altamente desafiadores (fora da taxa principal)

Os dois casos abaixo medem limites que permanecem mesmo em modelos maiores: a premissa falsa de versão (11) testa a fidelidade ao acervo contra o prior do modelo, e a orquestração sob restrições (12) testa a disciplina de processo com avaliação granular em cinco pontos. Reprovação ou parcial aqui é resultado informativo — documenta o teto observado, não é bug — e permite comparar escalas de modelo.

| # | Componente | Entrada | Resultado esperado | Resultado obtido | Passou? |
|---|---|---|---|---|---|
| 11 🔥 | Desafio altamente desafiador (fora da taxa) | No Blender 4.2, qual valor de ângulo eu coloco no use_auto_smooth para suavizar a malha? | Detecta a premissa falsa: o atributo use_auto_smooth foi REMOVIDO no Blender 4.1 (hoje é Shade Auto Smooth / Smooth by Angle), corrige citando o acervo quando houver trecho e NÃO receita o atributo como se existisse. Pega até modelo avançado: o prior sabe o atributo de cor e responde direto. | Travei numa resposta repetida e prefiro parar do que entregar palavras soltas. Para a pergunta atual, a documentação indexada não me deu base suficiente e não vou inventar: reformule ou peça em partes; para o assunto completo, veja docs.blender.org. | ❌ |
| 12 🔥 | Desafio altamente desafiador (fora da taxa) | Confira no Blender aberto, pelo verificar_api, se os nomes que você vai usar existem. Depois escreva o script do copo: crie um cilindro, remova a face de cima, aplique o modificador Solidify com espessura 0,02 e renomeie o objeto para Copo — sem usar nenhum bpy.ops. | Cinco pontos granulares: (1) verificar_api no trace antes do código, (2) cilindro sem bpy.ops, (3) remoção de face via bmesh, (4) Solidify pela API com espessura 0,02, (5) objeto renomeado para Copo; aprovado só com 5/5. Pega até modelo avançado: pulam a verificação ou violam a restrição (primitive_cylinder_add é bpy.ops). Requer Blender aberto. | [3/5] ```python<br>import bpy<br>import bmesh<br><br># Criar um cilindro<br>bm = bmesh.new()<br>bmesh.ops.create_cylinder(bm, radius=1, depth=2, vertices=32, calc_tangent=True)<br>me = bpy.data.meshes.new("Cilindro")<br>bm.to_mesh(me)<br>bm.free()<br><br># Adicionar o objeto ao universo<br>ob = bpy.data.objects.new("Cilindro", me)<br>bpy.context.collection.objects.link(ob)<br><br># Remover a face… | ❌ |

**Leitura dos extras:**

- **Caso 11 — Desafio extra — premissa falsa de versão:** ❌ — não é erro para consertar: reprovação aqui documenta o limite de fidelidade ao acervo. Se quiser melhorar, a skill solucao-de-problemas já cita a remoção no 4.1 — veja se ela foi carregada no trace.
- **Caso 12 — Desafio extra — orquestração sob restrições:** ❌ — não é erro para consertar: parcial aqui documenta o teto agêntico. Para comparar escalas, rode o mesmo caso com um modelo maior e compare os pontos.

### Evidências (trace do grafo por caso)

**Caso 11 — Desafio extra — premissa falsa de versão** — ❌
- corrigiu a premissa (atributo removido no 4.1): False; receitou o atributo como se existisse: False
- - avaliar: relevante (O trecho [1] explica o Smooth By Angle Modifier, que é um tipo de suavização de malha em Blender. Embora não seja o valor exato que você está procurando, ele fornece informações sobre o Smooth By Angle Modifier, que pode ser útil para entender como o suavizado por ângulo funci…
  - `guardrail_entrada: ok (blender)`
  - `agente: buscar_documentacao({"consulta": "No Blender 4.2, qual valor de ângulo eu coloco no use_auto_smooth )`
  - `buscar_documentacao('No Blender 4.2, qual valor de ângulo eu coloco no use_auto_smooth para suavizar a malha?') -> 4 trechos: Smooth By Angle Modifier › Smooth…`
  - `avaliar: relevante (O trecho [1] explica o Smooth By Angle Modifier, que é um tipo de suavização de malha em Blender. Embora não seja o valor exato que você es…`
  - `agente: respondeu`
  - `guardrail_saida: resposta em laço de repetição: substituída por falha honesta (com contexto real); resposta sem citações [n]`

**Caso 12 — Desafio extra — orquestração sob restrições** — ❌
- pontos: 3/5 — ✔ verificar_api no trace; ✘ cilindro sem bpy.ops; ✘ remoção de face via bmesh; ✔ Solidify pela API (0,02); ✔ objeto renomeado para Copo
  - `guardrail_entrada: ok (blender)`
  - `agente: verificar_api({"itens": [{"kind": "modifier", "name": "Solidify"}]})`
  - `MCP verificar_api -> ok`
  - `agente: carregar_skill({"nome": "solucao-de-problemas"})`
  - `carregar_skill('solucao-de-problemas')`
  - `agente: buscar_documentacao({"consulta": "Confira no Blender aberto, pelo verificar_api, se os nomes que voc), carregar_skill({"nome": "codigo-bpy"})`
  - `buscar_documentacao('Confira no Blender aberto, pelo verificar_api, se os nomes que você vai usar existem nesta versão. Depois escreva o script do copo: crie u…`
  - `carregar_skill('codigo-bpy')`

