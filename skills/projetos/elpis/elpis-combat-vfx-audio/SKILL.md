---
name: elpis-combat-vfx-audio
description: Regras do combate de Elpis — Arsenal de Elpis (tipos, raridades, 5 fabricantes, 7 slots), balística física única por arma (ElpisBallisticsEngine), VFX só com Mesh Particles 3D (ElpisVFXFactory) e áudio só via .wav em Resources/SFX (ElpisAudioManager). Consultar SEMPRE antes de criar armas, efeitos, sons, habilidades ou HUD de combate.
---

# Elpis — Combate, VFX e Áudio

## Arsenal de Elpis (Blender `asset_lib.py` → `Models/Armas/Elpis_<TIPO>_<RARIDADE>_*.fbx`)
- **5 tipos**: Pistola, Fuzil, Escopeta, Sniper, Laser. **5 raridades**: Comum, Incomum, Rara, Épica, Lendária
  (cores #8C9298, #2ECC71, #3498DB, #9B59B6, #E67E22). Lendárias: Cometinha, Maré Alta, Bocão, Olho de Elpis, Aurora.
- **7 sockets/slots de peça** no modelo (corpo, cano, mira, pente, coronha, acessório, núcleo/elemento);
  raridade adiciona camadas (Rara/Épica/Lendária têm peças e núcleo emissivo extra).
- **Elementos**: Incendiário #FF3300, Choque #00CCFF, Corrosivo #77FF00, Criogênico #66FFFF.
- **5 fabricantes** (nomes do jogo, nunca nomes de Borderlands):
  - **Cratera & Filhos** — broca: perfura 3 inimigos/coberturas finas, faísca de saída nas costas.
  - **Orbital Dinâmica** — combo (0–5) deixa o tiro mais reto e teleguiado; errar zera.
  - **Vácuo Vivo** — voo ondulado, regenera 1 bala/0.8 s, efeito elemental cresce no alvo.
  - **Retalho** — 1 ricochete real; bônus de pente sorteado na recarga (Tiro Duplo / Cadência +50% / Ricochete Explosivo).
  - **Ferrolho Pesado** — gyrojet: acelera, gruda, pisca 1 s e explode em área (3.5 m).

## Balística (ElpisBallisticsEngine + ElpisProjectile) — nada de bolinha genérica
- Pistola rápida (Rara = rajada de 2, Épica = 2 canos); Fuzil traçante + estojo ejetado (Épica = Tri-Cano em hélice);
  Escopeta 8–12 bagos com velocidade 85–115% + empurrão < 3 m; Sniper hitscan com linha que afina + anéis toroidais;
  Laser = feixe contínuo (Épica Prisma = 3 feixes, Lendária = 5), dano em tiques de 0.2 s.
- Projéteis sem Rigidbody: SphereCast do ponto anterior ao novo. Camada 2 (Ignore Raycast) = jogador e efeitos.
- Toda arma passa por `ContextoTiro` (boca calculada pelo tamanho do modelo na mão).

## VFX (ElpisVFXFactory) — REGRA: ZERO QUADRADOS
- **Todo `ParticleSystemRenderer` usa `renderMode = Mesh`** (esfera/cubo/cone) com material Unlit HDR
  (brilho) ou Simple Lit (fumaça/sucata com volume). Nunca billboard sem textura.
- Sistemas compartilhados só com `Emit`: Fumaça, Brasa, Fogo, Fragmento, Sucata, Bolha, Gelo, Gota, Faísca.
- Fogo de boca por fabricante, rastro por fabricante (`TrailElpis`), impacto por fabricante + assinatura elemental,
  explosão (esfera emissiva até o raio + fumaça preta + brasas + lens flare temporário + pulso de aberração).
- Um `TrailRenderer` por GameObject (usar filho). Cor HDR vai no MATERIAL; cor de vértice só controla alfa.
- Malhas procedurais: `Torus()`, `Cone()`; anéis/discos crescem com `FxCrescer`.

## Áudio (ElpisAudioManager) — só `.wav`
- Arquivos gerados por `Unity/setup_elpis_audio.py` (passa-baixa + saturação de válvula + reverb industrial) em
  `Assets/Resources/SFX/{Weapons,Impacts,Enemies,Movement,UI_Loot}`; variações `_01.._03`.
- Carregados com `Resources.Load` no Awake; 16 fontes de combate com `AudioLowPassFilter` 2200 Hz + 4 de interface.
- Cada toque sorteia variação e pitch 0.93–1.07; intervalo mínimo entre repetições do mesmo som.
- Nada de síntese em tempo real no C#.

## Mobilidade e HUD
- **Shift = dash** (5.2 m em 0.2 s, i-frames, 28 de energia). Sem tecla de correr: velocidade padrão 5.8 m/s.
- **Espaço = jato**; no ar, Espaço de novo = mergulho; ao tocar o chão = Slam (4 m, empurrão, dano).
- HUD Grim-Comic (HudArte/HUDJogo): centro limpo; status com retrato embaixo à esquerda, cartão de arma
  embaixo à direita, radar octogonal em cima à direita, ajuda recolhível (H) em cima à esquerda.
