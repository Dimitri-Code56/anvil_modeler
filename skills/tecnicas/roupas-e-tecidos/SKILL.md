---
name: roupas-e-tecidos
description: "Roupas, tecidos e panos (camisetas, calças, vestidos, capas, cortinas, bandeiras, toalhas): modelados SEPARADOS do corpo como molde de costura 2D e vestidos por simulação de tecido com costuras, para ter caimento e dobras reais."
---
# Roupas e tecidos

> **Ainda sem ferramenta própria.** No modo agente, siga o procedimento abaixo com `executar_python`
> (molde, costuras, simulação e congelamento) ou deixe a peça para o modo script.

Roupa nunca é feita "inflando" o corpo nem fundida nele: isso dá aspecto de massinha (sem caimento, sem
vinco, sem costura). Roupa é modelada à parte, como na confecção de verdade, e depois vestida.

## 1. Corpo primeiro (manequim)
- O personagem fica em **pose A** (braços a ~45°, pernas levemente afastadas). Sem isso as mangas e
  pernas da calça não conseguem envolver os membros na simulação.
- O corpo recebe o modificador `COLLISION` (`thickness_outer` ≈ 0.004–0.006 m, `cloth_friction` ≈ 5).
  Partes que ficarão cobertas podem ser simples, mas precisam ter o volume certo.

## 2. Molde de costura (painéis 2D)
- Cada peça é um conjunto de **painéis planos** com o contorno do molde real: camiseta = frente + costas
  em forma de T (mangas no ângulo da pose A); calça = 2 painéis por perna; saia = trapézios.
- Painéis em malha **uniforme** (grade preenchida dentro do contorno, ~1,5–2,5 cm entre vértices), nunca
  n-gons: a simulação precisa de densidade regular.
- **Posicione os painéis já curvados em volta do corpo** antes de simular (como os "arrangement points"
  dos programas de roupa): tronco como meia-elipse em volta do torso (frente em y < 0, costas em y > 0),
  manga como meio-cilindro em volta do eixo do braço, perna da calça em volta da perna. As costuras
  começam quase fechadas. Painel plano longe do corpo **não funciona** para membros finos: a costura
  puxa a frente contra as costas tão rápido que o tecido atravessa o braço e a manga cai solta.
- Folga de vestir: perímetro do molde ≈ perímetro do corpo + 10–15 % (camiseta), raio da manga ≈ raio
  do braço + 1,5 cm.

## 3. Costuras
- Costura = arestas soltas ligando os vértices de borda que se juntam (ombros, laterais, parte de baixo das
  mangas, entrepernas). Aberturas (gola, barra, punhos, cintura) **não** são costuradas.
- No `CLOTH`: `use_sewing_springs = True`, `sewing_force_max` ≈ 2–4 com painéis pré-posicionados
  (força alta faz o tecido atravessar o corpo).

## 4. Simulação
- Tecido leve (algodão): `mass` ≈ 0.15–0.3 kg, `tension/compression_stiffness` ≈ 15, `bending_stiffness`
  ≈ 0.5–2 (jeans: massa 0.4–0.6, bending 5–15), `quality` ≥ 8, gravidade ligada.
- Simule 40–80 quadros avançando `scene.frame_set(f)` um a um a partir do quadro inicial; depois
  **congele o resultado** (malha avaliada → mesh novo) e remova o modificador de tecido.
- `quality` ≥ 12 e `collision_settings.collision_quality` ≥ 3 para membros finos.
- **Verifique antes de aceitar:** nenhum vértice da roupa dentro do corpo (BVH, normal), mangas/pernas
  envolvendo o membro (vértices dos dois lados dele) e a peça apoiada onde deve (ombros, cintura).
  Referência do teste: camiseta de ~1.750 vértices, 60 quadros, ~30 s, 0 vértices atravessando.

## 5. Acabamento
- `SOLIDIFY` com espessura real (camiseta 2–3 mm, jeans 4–6 mm) e `SUBSURF` nível 1–2, sombreamento suave.
- Detalhes terciários que vendem a roupa: barra dobrada (faixa mais grossa na borda), gola canelada,
  pesponto (fileira de pequenos sulcos), bolsos, cós, botão/rebite, etiqueta. Cada um como peça separada
  ou região com material próprio.
- Materiais da biblioteca: `fabric` (algodão, malha), `leather`, e cores distintas para costuras/pespontos.

## 6. Tecidos soltos (cortina, bandeira, toalha, capa)
- Um painel em grade + pontos de fixação (vertex group com `pin_group` no `CLOTH`) + colisores do que o
  tecido toca (varão, chão, mesa); simule e congele do mesmo jeito.
