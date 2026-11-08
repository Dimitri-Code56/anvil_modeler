---
name: elpis-enemy-factions
description: Regras das facções e tiers de inimigos de Elpis (Saqueadores, Robôs da Cratera, Feras de Cristal, Tropas Corporativas; Swarm/Trooper/Elite-Boss) — modelagem no enemy_lib.py, escala, ponto fraco, comportamento e tiro telegrafado. Consultar SEMPRE antes de criar ou alterar inimigos, encontros ou chefes.
---

# Elpis — Facções e Tiers de Inimigos

Geração no Blender: `Projeto_Astronauta/Blender/enemy_lib.py` (`build_enemy(faccao, tier, ...)`, bípedes e
quadrúpedes, regras anti-lego da skill Grim-Comic: membros afunilados, sub-traje, assimetria, top-heavy,
gags e contorno de tinta). Export: `Unity/Assets/Art/Models/Mob_<FACCAO>_<TIER>/Mob_<FACCAO>_<TIER>.fbx`
com empties `WeaponSocket` e `WeakSpot_Core`. Escala do tier já vem assada no FBX.

## Facções (enum `Faccao` na Unity)
| Facção (jogo) | Código Blender / Unity | Visual | Fraqueza elemental | Traço |
|---|---|---|---|---|
| **Saqueadores** | `SUCATA` / `Faccao.Sucata` | sucata soldada, laranja, pneus, serras | — | corpo-a-corpo caótico |
| **Robôs da Cratera** | `ROBO_MINERADOR` / `RoboMinerador` | chassis amarelo-mineração, brocas, garras | Corrosivo ×1.6 | +20% vida, −10% velocidade |
| **Feras de Cristal** | `FERA_CRISTAL` / `FeraCristal` | quadrúpedes, cristais ciano, mandíbula ácida | Incendiário ×1.6 | +15% velocidade, −10% vida, sem tiro de longe |
| **Tropas Corporativas** | `CORPORATIVO` / `Corporativo` | armadura branca/azul limpa, escudo emissivo | Choque ×1.6 | +15% dano |

Cor de tiro/barra por facção: Sucata laranja, Robôs vermelho, Feras ciano, Corporativos azul.

## Tiers (enum `TierInimigo`)
| Tier | Escala | Papel | Base (nível 1) |
|---|---|---|---|
| **Swarm** | **0.75×** | corre e bate, em bando | 45 vida, 7 dano, 6.2 m/s |
| **Trooper** | **1.0×** | mantém 6.5–12 m, anda de lado, atira | 110 vida, 6 dano, 4.2 m/s |
| **Elite / Boss** | **1.6×** (chefe de fase: 1.7×) | tanque, pancada em área + rajadas | 900 vida, 22 dano, 2.6 m/s |

- Nível escala vida +18%/nível e dano +12%/nível.
- **Elite/Boss: ponto fraco brilhante NO DORSO** (`WeakSpot_Core`, esfera emissiva HDR + luz) — leva crítico ×2.
  O chefe tem barra de vida grande no topo da tela e ataque em área telegrafado (círculo vermelho → onda).

## Regras de combate
- **Tiro inimigo NUNCA é hitscan**: linha vermelha de aviso (0.55 s Trooper / 0.75 s Elite; segue o jogador
  na 1ª metade e TRAVA na 2ª) + `ProjetilInimigo` visível (21 m/s Trooper, 16 m/s Elite, maior).
  O dash atravessa projéteis (i-frames). Rajada do Elite = 1 aviso + 3 projéteis em leque.
- Spawn sempre com efeito (flash + faíscas) e colisores: cápsula do corpo + esfera no `WeakSpot_Core`.
- Trooper recebe uma arma do Arsenal no `WeaponSocket` (`CatalogoArmas.Criar`).
- Drops: Swarm 10%, Trooper 35%, Elite 100% (≥ Rara). Chefe de fase: 1 Rara/Épica + 1 Lendária garantidas.
- Estados elementais visíveis (EfeitosElementais): fogo, arco de choque para vizinho, poça ácida, gelo (5 acúmulos = bloco).
- Animação procedural (sem esqueleto): bob/inclinação, flash branco ao levar dano, tinta azul-gelo, empurrão (knockback).
