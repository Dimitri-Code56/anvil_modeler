---
name: props-e-mobilia
description: "Móveis e objetos do dia a dia (cadeiras, mesas, estantes, luminárias, caixas, utensílios): receitas passo a passo com as ferramentas e medidas ergonômicas reais."
---
# Props e mobília

## Medidas ergonômicas
Assento 0,43–0,46 m · mesa 0,74–0,76 m · bancada 0,9 m · prateleira 0,3–0,4 m de profundidade ·
madeira de móvel 18–40 mm · perna de cadeira 35–45 mm · tubo de metal 20–30 mm.

## Receita: cadeira (modo agente)
1. `iniciar_asset`.
2. Pernas da frente: `revolucao` (torneada; perfil [raio, altura] de 0 a 0,45) ou `cilindro`, em
   (±0,18; -0,18; …). `espelhar` em X para o outro lado.
3. Pernas de trás: mais altas se sobem até o encosto (0,9 m), em (±0,18; 0,18). `espelhar` em X.
4. Assento: `perfil_extrudado` no plano XY (vista de cima, cantos da frente arredondados), espessura
   0,035, com o centro em z = 0,45 + metade da espessura.
5. Travessas: `caixa` entre as pernas, a ~0,15–0,2 m do chão.
6. Encosto: `perfil_extrudado` no plano XZ para a travessa de cima (curva) e `caixa` + `repetir` para as
   ripas, levemente inclinadas (rotação X de -5 a -10°).
7. Materiais (`wood` em dois tons; `fabric`/`leather` se estofado, com `suavizar`) e conferência.

## Receita: mesa (modo agente)
Tampo `caixa` com chanfro (ou `perfil_extrudado` XY se for redondo/recortado), 4 pernas como na cadeira
indo até a face de baixo do tampo, saia (caixas finas sob o tampo, recuadas 5 cm da borda).

## Receita: luminária de mesa (modo agente)
Altura total 0,40–0,55 m.
1. Pé: `revolucao` com perfil de disco baixo ([[0,0],[0.09,0],[0.09,0.015],[0.07,0.025],[0.015,0.03],[0,0.03]]),
   posicao [0,0,0], `dark_metal` ou `painted_metal`.
2. Haste: `tubo_por_curva` raio 0,008 saindo do centro do pé (z = 0,03) e subindo em curva:
   [[0,0,0.03],[0,0,0.2],[0,0.05,0.35],[0,0.15,0.42]], `steel`/`chrome`.
3. Cúpula: `cilindro` em cone (raio 0,09 embaixo, raio_topo 0,025, altura 0,10) com o topo encostado na
   ponta da haste: posicao [0, 0.15, 0.37] (centro = ponta da haste menos metade da altura), `painted_metal` com cor.
4. Lâmpada: `massa_organica` com 1 parte (centro [0, 0.15, 0.33], raios [0.025, 0.025, 0.025]) dentro da cúpula, `emissive`.
5. Interruptor ou fio (opcional): `caixa` pequena no pé; `tubo_por_curva` fino saindo por trás.

## Receita: vaso / garrafa / caneca (modo agente)
Corpo: `revolucao` com o perfil de fora [raio, altura] de baixo para cima (vaso: base estreita, barriga larga,
gargalo estreito, boca um pouco aberta). Caneca: perfil de cilindro com borda e fundo; alça com
`tubo_por_curva` em forma de C encostada na lateral (raio 0,007).

## Receita: estante / armário (modo agente)
Laterais e tampo como `caixa` (18 mm), prateleiras com `caixa` + `repetir` em Z, fundo fino; portas com
`caixa` e puxador `cilindro`/`revolucao`.

---

## Modo script (referência para quem escreve código bpy)

## Medidas ergonômicas
Assento 0.43–0.46 m · mesa 0.74–0.76 m · bancada 0.9 m · estante (prateleira) 0.3–0.4 m de profundidade · maçaneta a 1.0 m · degrau de escada portátil 0.25 m.

## Construção
1. **Pense em como é fabricado:** cada peça real (perna, travessa, tampo, encosto, gaveta) é um objeto ou região própria com espessura real (madeira 18–40 mm, metal tubular 20–30 mm).
2. **Encaixes:** peças se tocam ou se sobrepõem levemente; nada flutuando. Use bevel pequeno (2–5 mm) em todas as arestas: arestas perfeitamente vivas denunciam CG.
3. **Curvas:** encostos e assentos estofados com subdivisão (`SUBSURF` nível 2) sobre uma base de poucos polígonos, ou perfil Bezier extrudado.
4. **Repetição:** pernas, puxadores e parafusos repetidos com `ARRAY` ou duplicando dados de malha (linked) para manter consistência.
5. **Materiais:** madeira `wood`, estofado `fabric`/`leather`, metal `steel`/`painted_metal`, plásticos `plastic`.
