---
name: veiculos
description: "Veículos (carros, motos, caminhões, buggies, naves): receita com perfil lateral extrudado para a carroceria, rodas com cilindros, caixas de roda por cortar, vidros, faróis e espelhamento."
---
# Veículos

## Proporções (carro de passeio)
Comprimento 4,0–4,6 m · largura 1,7–1,85 m · altura 1,4–1,5 m · entre-eixos ≈ 60 % do comprimento ·
roda 0,6–0,7 m de diâmetro · vão livre 0,15 m. Frente do carro em -Y.

## Receita: carro (modo agente)
1. `iniciar_asset`.
2. Carroceria: `perfil_extrudado` no plano YZ com a **silhueta lateral** (para-choque, capô, para-brisa
   inclinado, teto, vidro traseiro, porta-malas), espessura = largura, chanfro grande (0,03–0,06) para
   arredondar, `car_paint` com a cor pedida.
3. Caixas de roda: `cortar` com cilindro no eixo X (raio da roda + 4 cm) em cada eixo.
4. Rodas: pneu `cilindro` eixo X (raio 0,32, altura 0,2, `rubber`) + aro `cilindro` menor (`chrome`/`aluminum`),
   no eixo dianteiro e traseiro de um lado; `espelhar` em X.
5. Vidros: `perfil_extrudado` YZ com o recorte das janelas, um pouco mais estreito, `tinted_glass`.
6. Faróis e lanternas: `cilindro` eixo Y ou `caixa` fina com `emissive`; grade e para-choques: `caixa`
   `plastic`/`dark_metal`; retrovisores: `caixa` pequena + `espelhar`.
7. Conferência: rodas tocando o chão (z = raio), nada atravessando a carroceria.

---

## Modo script (referência para quem escreve código bpy)

## Proporções de referência (carro de passeio)
Comprimento 4.0–4.6 m · largura 1.7–1.85 m · altura 1.4–1.5 m · entre-eixos ≈ 60% do comprimento · roda 0.6–0.7 m de diâmetro · vão livre 0.15 m. Ajuste em proporção para outros tipos (SUV mais alto, esportivo mais baixo e largo, buggy com rodas grandes e chassi aberto).

## Construção
1. **Perfil lateral:** desenhe a silhueta lateral da carroceria em `bmesh` (capô, para-brisa, teto, traseira) e extrude na largura; arredonde os cantos em planta com bevel grande ou estreitando a face superior (taper) para não virar uma caixa.
2. **Simetria:** modele metade (x ≥ 0) e use `MIRROR` no eixo X; aplique antes de booleanas assimétricas.
3. **Vãos e cortes:** caixas de roda por booleana; linhas de porta e capô como sulcos de painel rasos.
4. **Rodas:** pneu = cilindro de 32 lados com bevel arredondado (ou torus achatado); aro afundado; cubo com raios ou furos por booleana em array circular. Material `rubber` no pneu, `chrome`/`aluminum` no aro.
5. **Vidros e luzes:** vidros como faces separadas levemente recuadas (`tinted_glass`); faróis e lanternas com material `emissive` fraco.
6. **Materiais:** carroceria `car_paint` (ou `painted_metal` para veículos de trabalho), partes baixas e grade `plastic`/`dark_metal`.
