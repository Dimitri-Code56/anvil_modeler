---
name: cel-shading
description: "Estilo de quadrinhos/cel shading (tipo Borderlands): formas um pouco exageradas, contorno preto e sombreamento em faixas chapadas."
---
# Estilo cel-shading
- A geometria segue o mesmo padrão de qualidade (silhueta, três camadas de forma). O estilo é do sombreamento, não uma desculpa para simplificar a malha.
- Formas levemente exageradas: peças importantes um pouco maiores, cantos chanfrados largos, silhueta mais marcada.
- A biblioteca de materiais gera sombreamento em faixas quando `ANVIL_STYLE = "cel-shading"`.
- Aplique `anvil_outline(obj)` nos objetos principais para o contorno preto (casco invertido).
- Cores fortes e poucas por peça; contraste entre peças vizinhas.
