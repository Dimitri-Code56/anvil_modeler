---
name: qualidade-visual
description: "Padrão de qualidade obrigatório para qualquer asset (silhueta reconhecível, três camadas de forma, nada de low-poly ou peças empilhadas) e a conferência final com listar_objetos, metricas e renderizar."
---
# Padrão de qualidade visual (vale para TODO asset)

## Conferência obrigatória antes de terminar (modo agente)
1. `listar_objetos`: confira cada peça contra as medidas reais da receita. Peças que deveriam se tocar
   precisam se tocar (posição ± metade da dimensão encostando na vizinha). Nada flutuando, nada
   atravessando de forma visível, tudo apoiado em z = 0 ou em outra peça.
2. `metricas`: `raw_boxes` deve ser 0 (as ferramentas já chanfram; não passe `chanfro=0`), `nonmanifold_edges` 0,
   `materials` ≥ 3 em objetos com várias peças.
3. `renderizar` e compare com o pedido: os traços identificadores aparecem na silhueta?
4. Se algo estiver errado, corrija com `remover` + nova chamada, em vez de empilhar peças por cima.

---

## Modo script (referência para quem escreve código bpy)

O objetivo é que o modelo seja reconhecido de imediato e pareça feito por um artista, não montado com blocos.

## 1. Proibido
- **Primitive stacking:** cubos, esferas e cilindros escalados e espetados uns nos outros como peça final. Primitivas só servem de ponto de partida para ser editadas (perfil, extrude, bevel, booleana, subdivisão).
- **Low-poly / blocado:** superfícies que deveriam ser curvas aparecendo facetadas; cilindros e esferas visíveis com poucos lados; arestas vivas em tudo.
- **Formas genéricas:** um "carro" que é uma caixa sobre quatro discos, uma "casa" que é um cubo com um prisma em cima.

## 2. Silhueta primeiro
- Antes de detalhar, a silhueta (o contorno em preto contra o fundo) tem que gritar o que o objeto é, vista de frente, de lado e em 3/4.
- Liste os **traços identificadores** do objeto (o que faz um carro parecer carro: linha de cintura, para-brisa inclinado, caixas de roda, faróis; uma casa: telhado com beiral, portas e janelas com moldura, base) e garanta que cada um aparece na geometria, não só na cor.
- Contornos com variação: curvas que mudam de raio, cantos chanfrados de larguras diferentes, recortes e saliências. Linhas retas e paralelas por toda parte deixam o objeto sem vida.

## 3. Hierarquia de formas
- **Primárias:** os volumes grandes, com proporções corretas em metros.
- **Secundárias:** peças que quebram os volumes grandes (molduras, para-choques, alças, beirais, junções).
- **Terciárias:** detalhes pequenos que dão escala e acabamento (parafusos, sulcos de painel, frisos, puxadores, dobradiças, costuras).
- Todo asset precisa das três camadas. Detalhe concentrado onde o olho vai (frente, topo, pontos de contato), áreas de descanso entre eles.

## 4. Densidade e acabamento
- Bevel nas arestas que pegam luz (largura proporcional à peça), com `WEIGHTED_NORMAL`. Sombreamento: `shade_smooth`
  com arestas vivas marcadas, salvo se o projeto pedir outra coisa (ex.: placas em flat shading no Elpis).
- Superfícies curvas sem facetas visíveis: o número de lados e o nível de `SUBSURF` dependem do alvo e do tamanho
  na tela (ver `topologia-e-orcamento`).
- **Se a skill de um projeto definir uma regra diferente desta, siga o projeto.**
- Peças com espessura real, encostando ou encaixando umas nas outras. Nada flutuando, nada atravessando de forma visível.
- Use materiais diferentes para separar as peças (ver biblioteca de materiais).

## 5. Autoverificação antes de terminar o script
Pergunte: alguém reconheceria isto só pela silhueta? Tem as três camadas de forma? Alguma parte ainda é um primitivo cru? Se sim, refine essa parte.
