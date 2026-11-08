---
name: topologia-e-orcamento
description: "Orçamento de polígonos por alvo (jogo em tempo real ou modelagem completa para render), o que gasta polígono, regras de malha limpa e o fluxo de trabalho em etapas com conferência visual."
---
# Topologia, orçamento de polígonos e fluxo de trabalho

> O alvo e o orçamento desta modelagem vêm no topo das instruções. Gaste polígono onde a silhueta e a câmera veem.

## 1. Os dois alvos
- **jogo** (tempo real, Unity, câmera isométrica): cada triângulo custa em todo quadro. Silhueta forte com
  poucos polígonos; detalhe pequeno vira material/cor, não geometria. Referência PC/console (mobile ≈ 5x menos):
  prop 0,5–5 mil · hard surface/orgânico 1–10 mil · construção 2–20 mil · veículo 10–40 mil · personagem 15–40 mil
  (+ 5–15 mil para cabelo, roupa e acessórios).
- **completo** (render, portfólio, impressão): densidade a serviço da forma; bevels arredondados, SUBSURF,
  detalhe terciário em geometria. Faixas que mantêm o Blender fluido: prop 5–100 mil · hard surface 20–200 mil ·
  veículo e personagem 100 mil–1 milhão.
- O orçamento conta **triângulos da malha final** (depois dos modificadores). Um quad = 2 triângulos.

## 2. O que gasta polígono (e quanto)
- `SUBSURF`: cada nível multiplica as faces por 4 (nível 2 = 16x). jogo: evite, ou nível 1 só em peças curvas
  grandes; completo: nível 2 em formas macias.
- `BEVEL`: segmentos x arestas. jogo: 1–2 segmentos, `limit_method='ANGLE'` (só as arestas que importam);
  completo: 2–4 segmentos.
- Cilindros e esferas: lados conforme o tamanho NA TELA. jogo: 8–12 em peças pequenas, 16–24 nas grandes;
  completo: 24–48. Se o projeto definir outro número, siga o projeto.
- `ARRAY` e cópias: multiplicam tudo; parafuso repetido 40 vezes com 32 lados pesa mais que o corpo inteiro.
  jogo: rebites e parafusos de 6–8 lados, ou só no material.
- `REMESH` voxel: densidade = (tamanho / voxel_size)². jogo: depois aplique `DECIMATE` (ratio 0,2–0,5).
- Gaste onde o olho vai (frente, topo, rosto, mãos, pontos de contato); economize atrás, embaixo e dentro.

## 3. Malha limpa (vale para os dois alvos)
- Escala e rotação aplicadas (`bpy.ops.object.transform_apply(scale=True, rotation=True)` ou malha criada já no
  tamanho certo); origem na base da peça, onde ela apoia.
- Normais para fora (`bmesh.ops.recalc_face_normals`); vértices duplicados fundidos (`bmesh.ops.remove_doubles`,
  dist 0,0001).
- Malha fechada (manifold), sem faces internas escondidas e sem faces sobrepostas no mesmo plano (piscam no render).
- Quads onde a malha vai deformar ou receber SUBSURF (personagem, tecido); n-gons só em superfícies planas de
  hard surface; nada de triângulos longos e finos em áreas curvas.
- Peças separadas só quando são peças reais (ou precisam de outro material/animação); o que é fundido na vida real
  pode ser uma malha só.
- Cortadores de booleana escondidos no render; no alvo jogo, booleana aplicada e a malha limpa depois.
- Nomes descritivos (`perna_fe`, `capacete`, `visor`).

## 4. Fluxo em etapas (com conferência visual)
1. **Blocagem:** volumes primários com as medidas reais e a silhueta; `renderizar` e confira proporção e leitura.
2. **Formas secundárias:** peças que quebram os volumes (molduras, placas, juntas); `renderizar` de novo.
3. **Terciárias e acabamento:** detalhes, bevel, materiais; `metricas` para conferir triângulos contra o orçamento.
4. Corrija o que o render mostrou antes de seguir para a próxima etapa: detalhe em cima de forma errada é desperdício.
