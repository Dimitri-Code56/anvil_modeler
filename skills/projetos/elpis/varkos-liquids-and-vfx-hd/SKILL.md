---
name: varkos-liquids-and-vfx-hd
description: Pipeline de Shaders URP (HLSL) para líquidos estilizados (ácido, lama, plasma) e Sistemas de Partículas Grim-Comic (Borderlands/Alienation style). Proíbe retângulos retos no chão, Voronoi estático e Default-Particle esfumaçada.
---

# Pipeline HD para Líquidos, Ácido e Partículas Grim-Comic (Varkos)

## REGRA 1: PROIBIDO "FITA RETANGULAR" E VORONOI GEOMÉTRICO EM LÍQUIDOS
Nunca crie um rio ou poça como um `Quad` retangular liso com textura Voronoi pura. Todo corpo líquido exige **Shader HLSL Customizado (`VarkosStylizedLiquid.shader`) + Malha de Margem Orgânica**:

### 1. Anatomia do Shader de Ácido/Líquido URP (`VarkosStylizedLiquid.shader`)
Escreva um shader URP Unlit/Lit customizado em HLSL com `CameraDepthTexture` ativo contendo 4 camadas matemáticas:
1. **Domain-Warped Dual Scrolling Noise (Fim das linhas retas de Voronoi):**
   - Distorça as coordenadas UV com uma onda senoidal + ruído turbulento (`uv += sin(uv.yx * 6.0 + _Time.y * 1.5) * 0.08`) ANTES de calcular o padrão celular!
   - Some duas camadas de ruído orgânico movendo-se em velocidades e direções diferentes (`pan1` e `pan2`) para criar movimento viscoso real.
2. **Posterização Cel-Shaded (3 Faixas de Cor Duras com `smoothstep` curto):**
   - **Fundo Profundo Viscoso:** Verde-pântano escuro (`#0A2E12`) para dar peso e contraste.
   - **Corpo Bioluminescente Médio:** Verde-tóxico saturado (`#1FAF2C`).
   - **Crista / Espuma Corrosiva (`Step` duro):** Verde-limão/amarelo ácido hiper-brilhante (`#9EFF1A`, HDR `intensity = 2.2`) com uma linha fina de contorno escuro (`#051408`) separando a espuma do líquido!
3. **Espuma de Borda por Profundidade (`SceneDepth Intersection Foam`):**
   - Compare `LinearEyeDepth` do `_CameraDepthTexture` com a profundidade do vértice (`screenPos.w`).
   - Onde a distância até o chão/pedras for menor que `0.45m`, desenhe uma **faixa sólida e crocante de espuma verde-clara borbulhante** nas margens! Isso elimina o corte reto contra o terreno.
4. **Vertex Displacement (Ondulação e Bolhas 3D):**
   - Desloque `positionOS.y` dos vértices com ondas suaves para a superfície do ácido subir e descer fisicamente.

### 2. Geometria de Rios e Poças (Fim do Retângulo Reto)
- **Malha Subdividida com Borda Irregular:** O plano do rio deve ter subdivisões para o Vertex Displacement funcionar e suas bordas laterais devem fazer curvas sinuosas.
- **Bancos de Rocha e Lodo nas Margens (`Riverbank Rock Borders`):** Sempre posicione fileiras de rochas lunares baixas, crostas de lodo escuro e raízes ao longo das duas margens do rio de ácido para esconder 100% a borda externa da malha!

---

## REGRA 2: SISTEMA DE PARTÍCULAS GRIM-COMIC (PROIBIDO `Default-Particle` BORRADO)
No estilo Grim-Comic, fogo, plasma, ácido e fumaça NUNCA usam círculos com degradê gaussiano suave.

### 1. Texturas Procedurais Crisp / Hard-Edge (`VarkosVFXTextureGenerator.cs`)
Gere em código texturas `128x128` com **recorte duro (`smoothstep(0.45, 0.52)`) e anel de contorno escuro**:
- **Bolhas de Ácido (`Tex_AcidBubble`):** Círculo com interior verde-escuro translúcido, meia-lua de brilho especular branco no topo e borda verde-neon dura que estoura num anel dentado.
- **Splat / Gota Corrosiva (`Tex_AcidSplat`):** Silhueta orgânica de mancha de tinta com contorno preto de 2px.
- **Impacto / Explosão Comic (`Tex_StarburstImpact`):** Estrela pontiaguda assimétrica de 7-9 pontas (centro branco puro `HDR`, meio amarelo/laranja e borda vermelha/preta dura).
- **Fumaça Cel-Shaded (`Tex_ToonSmoke`):** Nuvem estilizada com 3 tons chapados de cinza/roxo escuro e borda nítida (nunca fumaça esfumaçada transparente padrão).

### 2. Composição Obrigatória de Efeitos (4 Camadas por VFX)
Todo efeito de tiro, impacto ou ambiente deve combinar:
1. **Core Mesh / Billboard Duro:** Núcleo branco incandescente cercado pela cor do elemento (Verde para Ácido, Ciano para Plasma, Laranja para Balístico) + `TrailRenderer` afunilado com textura cortada.
2. **Debris 3D Físicos (Fragmentos Sólidos):** Em impactos e explosões, emita **cubos/prismas 3D pequenos (`RenderMode = Mesh`)** quicando no chão com gravidade real.
3. **Shockwave Ring (Anel de Expansão no Chão):** Um quad horizontal que cresce rápido em `0.15s` no ponto de impacto.
4. **Vapor / Brasa Ascendente:** No rio de ácido, adicione um `ParticleSystem` contínuo emitindo:
   - **Bolhas 3D/Billboards duros** que nascem no ácido, crescem por `0.8s` e estouram em micro-gotas;
   - **Nuvens baixas de vapor tóxico verde-esmeralda** subindo lentamente com iluminação `PointLight` verde suave.

## NO PROJETO (onde fica cada coisa)
- Shader: `Assets/Art/Shaders/VarkosStylizedLiquid.shader` (`Varkos/StylizedLiquid`, fila Transparent para ler a profundidade;
  exige `Depth Texture` ligada no URP Asset — ligada no `PC_RPAsset`).
- Texturas recortadas: `VarkosVFXTextureGenerator` (bolha, respingo, estrela de impacto, fumaça toon, anel de choque) — geradas
  em código, filtro bilinear, alpha binário (o material usa Alpha Clip, então a borda sai dura mesmo com MSAA).
- Efeitos: `VarkosVFX` (Bolha, Vapor, Estrela, Anel, Detritos, Respingo, ImpactoComic, ImpactoAcido) — sistemas reaproveitados.
- Rio/lagoas e margens: `VarkosLeste` (fita com borda sinuosa + rochas e crostas de lodo nas margens, livre embaixo das pontes).
