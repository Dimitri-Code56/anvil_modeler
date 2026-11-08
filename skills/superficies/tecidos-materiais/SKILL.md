---
name: tecidos-materiais
description: "Aparência de tecidos e couro (algodão, malha, jeans, lã, seda, cetim, lona, couro): trama em escala real, brilho de fibra (sheen), felpa, costuras e desgaste. Usar junto com roupas-e-tecidos (que cuida da forma)."
---
# Aparência de tecidos

> **Preset pronto (modo agente):** use `material="fabric"` em qualquer ferramenta (presets: `fabric`, `denim`, `leather`),
> com `cor` para o tom. O resto desta skill explica como ajustar ou montar o shader à mão no modo script.

A forma da roupa vem da skill `roupas-e-tecidos`; esta skill cuida de como o tecido **parece**. Tecido
sem estas camadas vira plástico fosco, que foi o problema das primeiras roupas.

## Camadas de todo tecido (Principled BSDF)
1. **Cor com variação:** ruído de baixa frequência (±5–8 % de valor), nunca cor chapada.
2. **Trama em escala real** (coordenadas do objeto, em metros): fio de algodão ≈ 0,3–0,5 mm, jeans
   (sarja) com diagonais a 45° a cada ≈ 1 mm, malha canelada com nervuras de 2–3 mm. Vai para cor e
   para bump (`Bump`, força 0,05–0,2).
3. **Brilho de fibra:** `Sheen Weight` 0,3–1,0 e `Sheen Roughness` 0,3–0,6 (é o que dá o "veludo" na
   borda das dobras). Roughness geral alta (0,7–0,95), exceto seda/cetim.
4. **Desgaste onde a peça sofre:** nó `Ambient Occlusion` ou curvatura para clarear arestas e escurecer
   dobras; jeans desbota nas coxas, joelhos e bordas; couro racha nas dobras.
5. **Costuras e pespontos:** linha de cor contrastante (geometria fina ou faixa na textura) seguindo as
   bordas dos painéis do molde.

## Receitas
| Tecido | Cor/trama | Roughness | Sheen | Extra |
|---|---|---|---|---|
| Algodão (camiseta) | malha fina, ruído suave | 0,85 | 0,5 | felpa leve na silhueta |
| Jeans | sarja 45°, fios azuis + brancos | 0,8 | 0,3 | desbote em relevos, pesponto mostarda |
| Lã / moletom | ruído grosso, fibras | 0,95 | 0,8 | displacement leve (fuzz) |
| Seda / cetim | quase lisa | 0,2–0,35 | 0,2 | `Anisotropic` 0,5–0,8 na direção da trama |
| Lona | trama quadrada grossa (1–2 mm) | 0,9 | 0,2 | bump forte |
| Couro | poros finos (ruído 300–600/m) + rugas | 0,45–0,65 | 0 | `Coat` 0,1–0,3 se envernizado |

## Regras
- Escala sempre em metros nas coordenadas do objeto (a biblioteca já faz isso): textura esticada
  denuncia CG na hora.
- Peças de roupa vizinhas têm materiais diferentes (camiseta ≠ calça ≠ cinto ≠ tênis).
- Em cel-shading, a trama some; mantenha só cor, pespontos e o contorno.
