---
name: pele
description: "Pele sem pelos (humana e animal: nariz, patas, orelhas por dentro, lábios, focinho; também olhos e unhas): subsurface, variação de cor por região, poros e oleosidade."
---
# Pele, olhos e unhas

> **Preset pronto (modo agente):** use `material="skin"` em qualquer ferramenta (presets: `skin`),
> com `cor` para o tom. O resto desta skill explica como ajustar ou montar o shader à mão no modo script.

Pele com material de plástico parece boneco de cera ou massinha. Pele precisa de luz passando por
dentro e de variação.

## Pele
1. **Subsurface (luz por dentro):** `Subsurface Weight` 0,1–0,3, `Subsurface Radius` ≈ (1,0; 0,35; 0,2)
   (vermelho espalha mais), `Subsurface Scale` ≈ 0,005–0,02 m (orelhas e nariz deixam a luz atravessar).
2. **Cor por região:** mais avermelhada em nariz, bochechas, orelhas, lábios, dedos; mais amarelada na
   testa; mais escura em dobras. Use gradientes pela posição do objeto ou atributo de cor de vértice,
   nunca uma cor única.
3. **Poros e microrrelevo:** ruído/voronoi muito fino (300–800 por metro) no bump, força baixa (0,03–0,1).
   Animais: textura de couro no nariz (voronoi "células") e almofadas das patas.
4. **Oleosidade:** roughness 0,35–0,5 na zona T e lábios, 0,55–0,7 no resto.
5. Animais sem pelo nas áreas certas: interior das orelhas (rosado, translúcido), nariz (úmido,
   roughness 0,2–0,3), almofadas das patas (escuras, ásperas).

## Olhos
- Globo com córnea **transparente e brilhante** por cima da íris (roughness ≈ 0, IOR 1,376); íris com
  fibras radiais e anel escuro na borda; pupila preta; esclera levemente amarelada/rosada, nunca branco
  puro. Animais: olho quase todo escuro, com reflexo bem marcado.
- Umidade: linha brilhante na borda da pálpebra inferior.

## Unhas e garras
- Queratina: cor mais clara na ponta, roughness 0,3–0,5, `Coat` leve; garras de animais escurecem na base.

## Regras
- A pele das partes visíveis ganha mais detalhe; a coberta por roupa/pelo pode ser simples.
- Humanos ficam para uma etapa própria (com corpo base pronto); esta skill vale desde já para animais.
