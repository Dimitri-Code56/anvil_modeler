---
name: varkos-global-lighting-and-atmosphere
description: Regras de Iluminação Global URP para Varkos. Proíbe alteração artificial da cor da luz solar por região e define o Ciclo F5 e o Trilight Ambient.
---
# Padrão de Iluminação Global de Varkos

1. **Sol/Lua Único e Fixo para o Mundo Inteiro:** NUNCA altere a cor da `Directional Light` com base na posição `(X, Z)` do jogador. O mundo aberto possui uma única atmosfera coesa de Varkos. As variações visuais dos biomas devem vir exclusivamente da modelagem do terreno, das rochas 3D e dos materiais PBR.
2. **Ciclo de Iluminação F5:**
   - **Dia:** Direcional clara (`#FFF8EB`, Intensity 1.5), Ambient Trilight suave (Sky `#687A8D`, Equator `#4D5B69`, Ground `#343D47`).
   - **Entardecer:** Direcional âmbar suave (`#FF9E5E`, Intensity 1.25).
   - **Noite Lunar:** Direcional azul-prateada (`#8FB8E6`, Intensity 0.9).
3. **Luzes locais mais fortes que o mundo:** lanterna do Bigorna ×1.8 (alcance ×1.25) e faróis/holofotes/postes ×1.6 (`VarkosLuzLocal`) — o sol/lua fica ~15% mais baixo para os focos de luz dominarem a leitura.
4. **Pós-Processamento URP Obrigatório:** SSAO ativado (`Intensity 1.6`, `Radius 0.35`) e Bloom configurado (`Threshold 0.9`, `Intensity 0.85`) para garantir o sombreamento de contato e o brilho atmosférico nos cristais, armas e faróis.

## No projeto (onde fica cada coisa)
- Presets do F5: `PlanetDayNightCycle.Presets` em `Scripts/Jogo/VarkosSessao.cs` (Dia é o índice 0 = padrão).
- Quem aplica sol/ambiente/neblina: `AjusteVisualAplicador` (usa o preset ativo no mundo aberto; o asset `AjusteVisual` fica intocado).
- `VarkosRegionalAtmosphere`: troca por região DESLIGADA (`Ativo => false`); só cria as lâmpadas âmbar locais do forte.
- Sombras: `VarkosShadowBudget` deixa no máximo 3 luzes secundárias com sombra (shadow atlas 4096 garantido por `Editor/VarkosShadowAtlasFix.cs`, que também ajusta a SSAO).
- Bloom/contraste/vinheta do mundo aberto: `AjusteVisualAplicador` (bloco `EstiloGrim.Aberto`). Interiores (bunkers) mantêm a penumbra própria.
