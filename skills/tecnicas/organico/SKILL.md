---
name: organico
description: "Formas orgânicas (animais, criaturas, rochas, troncos, almofadas, comida): receita com massa_organica (elipsoides sobrepostos fundidos e suavizados), olhos, focinho, bigodes e textura de superfície."
---
# Orgânico

## Receita: animal (modo agente)
1. `iniciar_asset`.
2. Liste as massas anatômicas com medidas reais: tronco, peito, quadril/ancas, pescoço, cabeça,
   focinho/bochechas, orelhas, pernas, patas, cauda.
3. Corpo: **uma** chamada de `massa_organica` com todas essas massas (elipsoides com `centro`, `raios`,
   `rotacao_graus`). Elas precisam se **sobrepor 20–40 %** para fundir; uma parte solta vira bolha.
   `textura` 0,002–0,004 para relevo de pelo; material `fur_short` (ou `skin`/`scales`) com a cor.
4. Barriga/peito claros (contrassombreamento): outra `massa_organica` menor, um pouco para fora do
   corpo, com cor mais clara.
5. Detalhes: olhos (`massa_organica` com 1 parte pequena, `plastic` quase preto), nariz (`skin` rosado),
   interior das orelhas (massa fina na frente da orelha, `skin` rosado), bigodes (`tubo_por_curva`, raio 0,0006,
   saindo do focinho e curvando para baixo), cauda.
6. Conferência: silhueta reconhecível de lado e de frente, patas apoiadas em z = 0.

## Receita: rocha / tronco (modo agente)
Rocha: 3–6 elipsoides achatados e irregulares numa `massa_organica`, `textura` maior (1–2 % do tamanho),
`stone`. Tronco: elipsoides alongados em sequência (ou `revolucao` com perfil irregular) + galhos com
`tubo_por_curva`, `wood`.

---

## Modo script (referência para quem escreve código bpy)

1. **Massa base contínua:**
   - Criaturas e corpos: `Skin Modifier` sobre um grafo de vértices (esqueleto) com raios variáveis por vértice (`skin_vertices[0].data[i].radius`), ou metaballs (`bpy.data.metaballs`) para massas arredondadas.
   - Rochas: icosfera subdividida deformada com `Displace` (textura `VORONOI` ou `CLOUDS`) em escala grande + pequena.
   - Troncos e galhos: curvas Bezier com `bevel_depth` e `taper_object`, ou skin modifier.
2. **Converter e unificar:** converta para mesh e aplique `REMESH` (`mode='VOXEL'`, `voxel_size` ≈ 1–3% da altura) para fundir as partes sem costura.
3. **Detalhe:** `Displace` com textura procedural fraca para poros, rugas ou lascas.
4. **Otimizar:** `DECIMATE` (`COLLAPSE`, ratio 0.3–0.6) para uso em jogo; `shade_smooth`.
5. **Assimetria natural:** use `random` com semente fixa para variar raios e posições em 5–15%. Nada orgânico é perfeitamente simétrico.
