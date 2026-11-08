---
name: escamas-e-carapacas
description: "Superfícies biológicas duras ou escamosas (répteis, peixes, anfíbios, insetos, crustáceos, cascos, conchas, chifres, ossos): escamas em escala certa, carapaça de quitina, umidade e iridescência."
---
# Escamas, carapaças e superfícies duras biológicas

> **Preset pronto (modo agente):** use `material="scales"` em qualquer ferramenta (presets: `scales`),
> com `cor` para o tom. O resto desta skill explica como ajustar ou montar o shader à mão no modo script.

## Escamas (répteis)
- `Voronoi` com saída de distância até a borda → sulco entre escamas no bump/deslocamento, cor mais
  escura no sulco.
- **Tamanho varia pelo corpo:** escamas maiores no dorso e na barriga (placas), menores na cabeça, nas
  articulações e nos dedos. Use mais de uma escala misturada por região.
- Escamas um pouco elevadas no centro (perfil abaulado), não planas.
- Padrões (faixas, losangos, manchas) por cima, alinhados ao eixo do corpo.
- Roughness 0,4–0,7; troca de pele deixa áreas mais foscas e claras.

## Peixes
- Escamas **sobrepostas** (voronoi alongado + gradiente em cada célula, como telhas), menores na direção
  da cabeça.
- Camada brilhante e úmida: `Coat` 0,5–1,0 com roughness baixa; ventre prateado e iridescente
  (`Thin Film`, se existir na versão), dorso mais escuro (contrassombreamento).
- Nadadeiras: membrana fina e translúcida (subsurface ou transmissão parcial) com raios em geometria ou
  textura.

## Anfíbios e superfícies úmidas
- Pele lisa com glândulas (pontos em relevo), `Coat` alto, roughness 0,15–0,3, subsurface leve.

## Quitina e carapaças (insetos, crustáceos)
- Placas rígidas separadas por juntas (geometria segmentada, como hard-surface orgânico).
- `Coat` 0,3–0,8, roughness 0,2–0,4; cor em camadas (mais escura nas bordas das placas);
  besouros metálicos com `Thin Film`/iridescência.
- Crustáceos: textura granulada (ruído fino no bump), cor viva no dorso e clara embaixo.

## Cascos, chifres, conchas, ossos
- Cascos e chifres: anéis de crescimento (`Wave` ao longo do comprimento), fibras longitudinais, mais
  escuros e lisos na ponta.
- Conchas: anéis concêntricos de crescimento, interior em madrepérola (iridescente, roughness baixa).
- Osso: cor creme irregular, poroso nas pontas, roughness 0,6–0,8, subsurface fraco.
