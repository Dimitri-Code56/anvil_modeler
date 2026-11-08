---
name: elpis-level-design
description: Regras de level design do Projeto Astronauta (Elpis) — chão com relevo e placas, detritos ancorando objetos, paredes baixas ao sul para a câmera isométrica, iluminação de alto contraste estilo Alienation, interiores Grim-Comic Tático (penumbra + lanterna com sombra + silhuetas), Hub Central e mapas lineares com portões de combate. Consultar SEMPRE antes de gerar bioma, cenário, fase, base interna, hub ou iluminação.
---

# Elpis — Level Design

Jogo: shooter isométrico Borderlands 2 + brutalidade Warhammer + comédia. Protagonista: **Bigorna**.
Pipeline: Blender (MCP no notebook do Dimitri, nunca na VM) → FBX → Unity 6 (URP 17, Input System, Forward+).
Pastas: `Projeto_Astronauta/Blender` (asset_lib.py, enemy_lib.py, biome_*.py) e `Projeto_Astronauta/Unity`.

## 1. Chão — PROIBIDO plano liso
- Todo chão é uma malha com relevo: ruído de Perlin nos vértices (`y += Perlin(x*0.1, z*0.1) * 0.4`)
  + crateras rasas nas zonas de combate + bacias rebaixadas (−0.3 m) com beiço de rocha nas poças de ácido.
- O objeto do chão deve ter **"Terreno"** no nome (ou no pai): o `ElpisGroundGenerator` acha sozinho e aplica
  relevo, piso modular, pedras, decalques, poças vivas e scatter. A malha precisa ser legível (Read/Write).
- Piso modular industrial (`PisoIndustrial.cs`) só nas áreas quase planas (normal.y > 0.93):
  placas de blindagem chanfradas de 2 m (3 tons escuros + parafusos), **grades** sobre fosso escuro
  (às vezes calor laranja embaixo) e **valas de cabos** em linhas (guia com faixa de perigo + 3 cabos).
  ~1/3 do chão fica como rocha exposta (máscara de ruído). Nunca cobrir crateras, poças ou rampas.
- Decalques colados no relevo (blend Multiply, +2–3 cm, sem z-fight): óleo, rachaduras, marcas de pneu.

## 2. Ancoragem com detritos (`GroundScatterManager`)
- Todo objeto que toca o chão (trilho, contêiner, torre, broca, base) recebe aglomerados de pedregulhos
  facetados + entulho; pé de paredão (terreno sobe > 0.9 m em 1.4 m) também.
- Cabos grossos serpenteando (anéis amarelos + conectores), carcaças meio enterradas
  (canos, vigas I, caixas desmontadas, cascos de drone). Tudo combinado em 1 malha por material, camada 2,
  sem colisão (não bloqueia tiro nem NavMesh).

## 3. Câmera isométrica e paredes
- Câmera iso: inclinação 48°, FOV 28, distância 24. Em fases lineares que andam para **+Z**, usar `isoGiro ≈ 30`
  (câmera ao sul-sudoeste olhando para o norte).
- **Paredes ao SUL e OESTE (lado da câmera): muretas baixas (≤ 1.2 m).** Paredões altos (4–6 m) só ao NORTE/LESTE.
- Nada alto entre a câmera e o Bigorna; telhados proibidos (simular "subterrâneo" com escuridão, não com teto).

## 4. Iluminação estilo Alienation (alto contraste)
- Ambiente MUITO escuro (Trilight ≈ céu 0.12/0.135/0.19, equador 0.075, chão 0.035), sol fraco e frio (0.8).
  Quem ilumina são as **luzes locais fortes**: holofotes laranja (Spot ≥ 6 intensidade, alcance ≥ 12 → ganham
  feixe volumétrico + lens flare automáticos), poças de ácido (#66FF00, 7+, alcance 12+), barris/postes laranja,
  cristais ciano.
- Marcadores que os sistemas automáticos reconhecem: `Luz_Holofote_N` (com Spot filho), `Luz_Acido_N`.
- Pós (`GraphicsPolisher`): ACES, contraste +34, Bloom limiar 1.05 / intensidade 3.2 (só HDR estoura),
  vinheta 0.34, split toning ciano/laranja, aberração cromática 0.12 com pulsos em explosão/slam/dash.
- Atmosfera (`ElpisAtmosphereParticles`): poeira, fagulhas (mais em combate), esporos nas poças, névoa baixa.
- Emissivos que devem brilhar precisam de cor HDR > 1 (ácido, tiros, núcleos lendários, LEDs).

## 4b. Referência Alienation — 5 elementos obrigatórios (`AlienationAtmosphereUpgrader`)
1. **Lanterna tática no Bigorna** (`TacticalFlashlight`): Spot real na boca da arma (48°, alcance 16, intensidade 6,
   #D8F0FF, sombras) inclinada para bater no chão a 7–9 m + **cone volumétrico** aditivo de 9 m (2 camadas,
   alfa sumindo até a ponta) + **laser de mira** fino (cor do elemento > raridade Rara+ > vermelho-rosa) com ponto no impacto.
2. **Névoa fria de profundidade**: `FogMode.ExponentialSquared`, densidade **0.022**, cor **#1A2228** (mina) ou
   **#162836** (externo/criogênico). Ambiente e sol em tons **frios azulados**; inimigos, brilhos e tiros ficam
   **quentes** (vermelho/laranja) para contrastar contra o chão frio.
3. **Dunas de poeira lunar** (`DustDrifts`): montes chanfrados achatados cor de rególito (mais claros que o piso)
   encostados nas bases de contêineres, vagões, caminhões, pneus, pilares e torres — mais e maiores a barlavento.
   No **caminho central** do jogador: faixa de piso mais escura e gasta + **pegadas** + **sulcos de pneu afundados**.
4. **Composição diagonal**: coberturas grandes (vagões, caminhões de mineração, contêineres) giradas **25°–40°**
   formando gargalos diagonais; **Point Lights #FF6622** escondidas embaixo de veículos tombados e em frestas
   (alcance ~5, luz indireta quente iluminando a poeira).
5. **Vento** (`WindParticles`): cinza/neve espacial em **traços esticados** (malha de cubo alongado alinhada à
   velocidade — nunca billboard) com vento diagonal constante (~2.6, −0.35, 1.5 m/s); a poeira global segue o vento.

## 4c. Interiores (`Indoor / Complexos`) — estilo próprio "Grim-Comic Tático"
Interiores são **claustrofóbicos**: nada de luz global iluminando todas as salas. Quem dá a visão é a
**lanterna da arma**; o resto são pontos quentes de emergência. Ligado por `BaseInimigaGenerator.Interna = true`
(o `AjusteVisualAplicador`, a `TacticalFlashlight`, as `LuzesCenario` e o `Inimigo` mudam de regra sozinhos).
Valores ajustáveis no AjusteVisual, bloco **"Interiores — Grim-Comic Tático"**.

1. **Sol desligado (penumbra tática real)**
   - Directional Light com `intensity = 0.12` (quase zero, mas ainda marca as bandas do toon: não achatar).
   - Ambiente Trilight frio profundo **#0D131C** (equador ×0.8, chão ×0.55) → SH atualizado; piso de luz do
     shader `_PisoLuzForca` ≈ **0.03** (fora: 0.25); névoa escura #05070A, densidade ~0.012; fundo da câmera = névoa.
   - Fora da lanterna tudo fica em ~15% de brilho: só brilham **frisos de neon** das paredes, **barris**,
     **olhos/visores** dos inimigos, LEDs e o ponto fraco dos Elites.
2. **Lanterna da arma = visão principal**
   - Spot `range = 18`, `spotAngle = 52`, `intensity = 14`, **`shadows = Hard`, `shadowStrength = 0.9`**,
     a 1.2 m de altura, inclinada só ~4° para baixo (alcança portas e o fundo das salas).
   - Facho no chão: leque de **10 m / 50°** com **um Raycast por coluna (11 raios, altura do peito)** — o facho
     **para** em paredes, caixas e inimigos em vez de atravessar.
   - Luz "acima do Bigorna" fraca (≈0.6) só para não perder o personagem.
3. **Luzes de parede curtas e contidas**
   - Gaiola/emergência/painel: `range` **3.5–4.5**; luz posicionada ≥0.45 m à frente da parede.
   - **Orçamento de sombras**: só as 4 luzes de parede mais próximas do Bigorna (<14 m) ganham `Shadows.Hard`
     (sombra = não vaza para a sala vizinha); as outras ficam sem sombra (custo: 6 renders por luz pontual).
   - **20% das luzes de parede com flicker contínuo** (`Mathf.PerlinNoise`) + quedas quase a zero: instalação atacada.
   - Calhas fluorescentes: **~70% queimadas** (só o tubo cinza, sem luz); as acesas a ~35% e alcance ≤ 6.5.
   - Giroflex de portão: alcance ≤ 7. Núcleos/reatores: ilha pequena (alcance ~8).
   - Centro dos corredores fica **escuro** — é o espaço da lanterna.
4. **Silhueta dos inimigos no escuro**
   - Fora do cone da lanterna: corpo quase preto (≈0.06), emissão zero, só **olhos/visor emissivos** +
     **contorno preto** + **rim frio** (#6699FF, força ~0.5).
   - Quando o cone da lanterna bate (cone + alcance + sem parede no meio, `TacticalFlashlight.Iluminacao`),
     a armadura quente **acende inteira** (fade rápido ao acender, lento ao apagar). Colado no Bigorna (<2.2 m) fica meio aceso.
   - Ponto fraco do Elite brilha sempre.
5. **Arquitetura interna** (padrão `BaseInimigaGenerator`)
   - Planta em grade de 1 m: salas retangulares + portas. Paredes do fundo (norte/leste) **4.2 m** com friso de
     neon e colunas a cada 6 m; entre salas **2.4 m**; lado da câmera (sul/oeste) **1.1 m**. Sem teto.
   - Mistura de ritmos: **salas amplas** (arena: portões trancam, alarme, ondas + reforços + Elite),
     **corredores lineares** com muita cobertura em zigue-zague, **salas laterais opcionais** com **baús [E]**
     (Incomum→Épico), emboscadas e eventos (tanques de contenção estourando).
   - Guardas **parados** que acordam ao ver o Bigorna (linha de visão), ao levar dano ou com o grito de um colega.
   - Portas automáticas deslizando para dentro da parede; HUD com sala atual, objetivo e "SALAS x/y · BAÚS x/y".
6. **Névoa de salas (não se vê o que tem na sala onde você não está)**
   - Só a sala do Bigorna aparece. As outras ganham um **véu preto no chão** (fade 0.25 s) e escondem móveis,
     luzes, baús, inimigos (sem barra de vida) e loot — as colisões continuam. As paredes ficam como silhueta.
   - Cada porta mostra, do lado de cá, **setas âmbar ">>" pulsando no chão** + o **nome da sala** do outro lado
     (ou **"???"** se ainda não visitada), só quando o Bigorna está a < 9 m.
   - Ao sair de uma sala ela volta a ficar escondida (mesmo já explorada).

## 4d. Exteriores no estilo Grim-Comic Tático (um pouco mais claro)
- Mesma regra dos interiores (lanterna 18/52/14 com sombra dura e facho que para em obstáculos, inimigos em
  silhueta com rim frio), só que mais claro: sol **0.35**, ambiente **#1A2533**, piso de luz **0.07**,
  névoa #0D121A densidade 0.009, corpo do inimigo no escuro **0.16**, luz acima do Bigorna 1.0, cenários assados ×0.6.
- Fora, inimigos dentro do miolo de uma luz forte do cenário (holofote, poça de ácido, poste: intensidade ≥ 4,
  alcance ≥ 8) também aparecem meio acesos.
- Liga/desliga no AjusteVisual: `grimExteriores` (bloco "Exteriores — Grim-Comic Tático").
- **Exceção: mundo aberto** = luz de sol/lua de verdade (ver skill elpis-vehicles-openworld §8). Penumbra escura
  só faz sentido em locais fechados/subterrâneos e em fases lineares de mina; céu aberto precisa enxergar longe.

## 5. Hub Central (futuro)
- Cena `Hub_Central` (pátio da base operacional): sem combate, iluminação mais quente.
- Estações: vendedor de armas (Arsenal de Elpis), baú de loot, painel de missões (escolher bioma/fase),
  garagem do Rover (viagem), mural de facções. Saída: plataforma de inserção para cada fase.
- Botão "Voltar ao Hub" das fases carrega `Hub_Central` se ela estiver no Build Settings.

## 6. Mapas lineares (padrão `LinearRunGenerator`)
- Progressão em **+Z** com zonas conectadas por **Portões de Laser (`CombatGate`)**:
  1. Começo: safe zone + holofote quente + Rover atrás do Bigorna + 2 armas iniciais de fabricantes diferentes.
     (Coberturas sempre em diagonal 25–40°, nunca alinhadas aos eixos.)
  2. Meio A: aberto, cobertura (vagões, pneus, trilhos); entrar trava o portão de trás e inicia o encontro.
  3. Meio B: fechado/estreito, escuro (luz do sol cai para ~0.15), ácido + cristais, barris explosivos.
  4. Fim: arena do chefe + extração (pilar ciano, `E` para sair) e tela de Missão Cumprida com estatísticas.
- Portão abre só quando todos os inimigos do encontro morrem (som + efeito). Ao travar, NavMeshObstacle carve.
- NavMesh gerado em tempo de execução DEPOIS do relevo e do piso (esperar 2–3 frames).
- Inimigos nascem com flash/faíscas, nunca dentro do campo de visão imediato do jogador sem aviso.
