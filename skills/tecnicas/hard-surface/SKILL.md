---
name: hard-surface
description: "Objetos manufaturados e rígidos (máquinas, armas, ferramentas, eletrônicos, equipamentos): receita com perfil_extrudado para a silhueta, caixa/cilindro chanfrados, cortar para recortes, espelhar e repetir."
---
# Hard surface

## Receita com as ferramentas (modo agente)
1. `iniciar_asset`. Defina as dimensões totais em metros e derive tudo delas.
2. **Corpo principal pela silhueta:** `perfil_extrudado` com o contorno de lado (plano YZ) ou de frente
   (plano XZ), pontos em ordem, com recortes e inclinações reais. Nunca uma `caixa` como corpo principal.
3. **Peças secundárias:** `caixa` (painéis, tampas) e `cilindro` (eixos, botões, canos), com chanfro.
4. **Recortes:** `cortar` para entradas de ar, furos, encaixes, telas embutidas.
5. **Simetria e repetição:** `espelhar` (lado esquerdo/direito), `repetir` (aletas, parafusos, teclas).
6. **Cabos e mangueiras:** `tubo_por_curva` com 3–5 pontos e uma leve curva.
7. Materiais (metal pintado + metal cru + borracha/plástico + `emissive` em luzes) e a conferência da
   skill de qualidade.

---

## Modo script (referência para quem escreve código bpy)

## Regra zero
Nada de "primitive stacking" (cubos e esferas escalados e espetados). Cada peça principal nasce de um perfil desenhado.

## Construção
1. **Perfil primeiro:** desenhe a silhueta 2D ponto a ponto com `bmesh` (lista de coordenadas), crie a face e extrude com `bmesh.ops.extrude_face_region` + `bmesh.ops.translate` na espessura real.
2. **Recortes:** use objetos cortadores com modificador `BOOLEAN` (`DIFFERENCE`, solver `EXACT`) para entradas de ar, furos, encaixes. Esconda os cortadores (`hide_render = True`, `hide_viewport = True`) e deixe-os na coleção do asset.
3. **Acabamento:** `BEVEL` (largura 1–3% da peça, `limit_method='ANGLE'`; segmentos conforme o alvo) seguido de `WEIGHTED_NORMAL`.
4. **Peças curvas:** lados conforme o alvo e o tamanho na tela (ver `topologia-e-orcamento`); nunca facetas visíveis numa peça grande.
5. **Detalhe de superfície:** sulcos de painel só nas divisões reais (porta, tampa, escotilha), por cortador booleano fino
   ou `inset_region` numa face escolhida; **nunca em grade** sobre a superfície inteira. Rebites e parafusos em fileiras
   ao longo de vigas e bordas (no alvo jogo, com poucos lados ou só no material).

## Proporção
Defina primeiro as dimensões totais em metros e derive cada peça delas. Peças secundárias têm tamanho proporcional à principal, não números soltos.
