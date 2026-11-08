---
name: elpis-vehicles-openworld
description: Regras de veículos e mundo aberto cooperativo do Projeto Astronauta (Elpis) — hierarquia de peças no Blender, proporção isométrica, iluminação tática veicular, assentos coop, física arcade e animação procedural na Unity. Consultar SEMPRE antes de modelar, exportar, configurar ou programar motos, carros/rovers, hoverbikes, naves/dropships ou mapas abertos.
---

# Elpis — Veículos e Mundo Aberto Cooperativo

Visual: **Grim-Comic Tático** (contorno de nanquim, chanfros, penumbra cortada por faróis) e animação **100% procedural**
(nada de esqueleto nem clipes: tudo gira/inclina por código). Pipeline: Blender (MCP no notebook) →
`Projeto_Astronauta/Blender/vehicle_lib.py` → `Unity/Assets/Art/Models/Veiculos/<Veiculo_X>.fbx` → Unity 6 URP.

## 1. Hierarquia obrigatória no Blender
Convenção: **frente = −Y, topo = +Z, raiz (Empty) no chão** no centro entre as rodas.
```
Veiculo_X                      raiz
  Chassis_Body                 carroceria (tudo que não gira)
    Steer_Front                (moto) garfo + guidão — esterça
      Wheel_F                  roda dianteira
    Wheel_R | Wheel_FL/FR/RL/RR  rodas individuais (pivô no eixo, eixo = X)
    Thruster_L/R(/Rear) | Thruster_FL/FR/RL/RR   turbinas (pivô no centro: basculam em X)
    Turret_Base                anel giratório (pivô no centro do anel)
      Turret_Barrel            cano (pivô no munhão) → filho marcador Muzzle na ponta
    Ramp_Rear                  rampa (pivô na dobradiça)
  Seat_Driver, Seat_Gunner, Seat_Passenger      marcadores (Empties)
  Headlight_L/R (ou _C), Taillight_L/R (ou _C), Exhaust_*, Spotlight_1..4, Muzzle
```
- No `vehicle_lib.py`: `parte(nome, pai, pivô)` cria a parte (Empty com `["parte"]`), `marcador()` os Empties
  (`["marcador"]`), e cada peça de malha é filha da parte com nome `<Parte>__<peça>`.
- **No FBX todas as partes e marcadores ficam no 1º nível** (o exportador com bake_space_transform só converte os
  eixos de quem está direto na raiz — filhos aninhados chegavam na Unity com Y/Z trocados e as rodas enterradas).
  A Unity refaz a hierarquia pelo nome (`ElpisVehicleController.RefazerHierarquia`: Wheel_F/Headlight_C→Steer_Front,
  Turret_Barrel→Turret_Base, Muzzle→Turret_Barrel, Exhaust_XX→Thruster_XX). Sempre conferir reimportando o FBX.
- `export_veiculo(R)`: **uma malha por parte** (peças juntas no espaço do pivô), marcadores preservados,
  nomes limpos (sem `.001`), contorno de prévia desligado (a Unity tem o próprio). `export_todos()` exporta os 4.
- Toda peça passa por `fin()`: BEVEL 1 segmento (0.01–0.03) + SOLIDIFY invertido preto (−0.01 a −0.035, mais grosso
  em peças grandes). Materiais `cel_mat` chapados (a Unity converte para o toon); emissivos = cor HDR.
- Importador: pasta `Veiculos` com contorno 2.5 px e malhas legíveis (MeshCollider da nave em tempo de execução).

## 2. Proporção isométrica (leitura de cima)
- **Rodas largas fora da carroceria** (open-wheel); para-lamas curtos só em cima. Pneus com cravos (`A.wheel`).
- Cabines **semi-abertas** (gaiola de tubos) ou para-brisa **angular** escuro; bancos e volante visíveis de cima.
- Silhueta em cunha (`A.prism` / `A.tbox` afunilado), **nunca cubo reto**; chanfros obrigatórios; faixas de perigo
  amarelas/pretas e números/prefixos em estêncil.
- Escala de referência: Bigorna ≈ 1.85 m. Moto ~2.6 m, buggy ~4 m (rodas Ø1.1), dropship ~13 m com baia de 2.6 m.
- Faccão/fabricante define o visual: Retalho = sucata enferrujada + serras; Orbital = branco/marinho + neon ciano;
  Javali (militar) = oliva + quebra-mato com espetos; Valquíria = casco claro gasto + faixas laranja.

## 3. Iluminação tática veicular (Grim-Comic Tático)
- **Faróis duplos** (ou único na moto): `SpotLight` `range = 26`, ângulo 46° (54° no farol único), intensidade 16
  (9 com o veículo vazio = luz de estacionamento), **`shadows = Hard`, força 0.9** (sombra só a < 30 m do Bigorna).
- **`FachoChao`** (facho no chão): leque de 13 m com 9 raios na altura do peito — **para em obstáculos**; cada
  vértice é colado no terreno por raio; atualiza a cada 2 quadros. Aditivo quente, alfa ~0.16.
- **Lanternas traseiras** vermelhas emissivas + Point 3 m (acendem mais no freio/ré).
- **Escapamentos** (`Exhaust_*`): fumaça 3D (mesh particles) ao acelerar; **fogo** no turbo; hover = jato ciano.
- Dropship: 4 holofotes do ventre apontados para o chão (2 com sombra) + **cone volumétrico** aditivo do tamanho
  da altura; luz azul nos jatos; poeira em anel quando está a < 14 m do chão.

## 4. Mecânica cooperativa e controles
- **Assentos**: Motorista (dirige: WASD na direção da tela, SHIFT turbo, ESPAÇO freio de mão/drift, BOTÃO DIR.
  aríete); Artilheiro (`Seat_Gunner`: torreta 360°, CLIQUE dispara); Garupa (`Seat_Passenger`: atira com a própria arma).
  **Solo**: com o artilheiro vazio, a torreta segue a mira do motorista e o clique dispara. Moto sem torreta: o
  motorista atira com a arma. `F` troca de assento, `E` entra/sai (sai pelo lado livre).
- Entrada: `[E]` perto do veículo (se não houver arma no chão por perto); o Bigorna fica preso ao assento
  (`JogadorAstronauta.veiculo`), Dash/Slam/Ombrada ficam desligados lá dentro.
- **Vazio = cobertura pesada**: colisores na camada normal bloqueiam tiros + `NavMeshObstacle` (carve parado);
  faróis continuam acesos projetando luz no terreno. **Ocupado**: colisores na camada 2 (tiros passam e acertam quem
  está dentro). Preparado para mais jogadores: cada `Assento` guarda o ocupante; só o jogador local lê o teclado.

## 5. Física arcade + animação procedural (`ElpisVehicleController`)
- Objeto do veículo = `Rigidbody` + `BoxCollider` (caixa do chassi, do eixo para cima) + filho **"Modelo"** (FBX).
  A frente é detectada pelos faróis (o modelo é girado 180° se vier invertido).
- **Suspensão por raio** em cada roda: mola `k = m·g / (n·curso/2)` + amortecedor crítico ~0.55 → em repouso a roda
  fica exatamente na posição modelada. Hover: 4 colchões de empuxo. Rotação X/Z congelada (estável); a inclinação é visual.
- Tração na direção do veículo, **aderência lateral** (drift = aderência baixa), giro em Y proporcional à velocidade.
- Visual: rodas giram (`v / raio`), sobem/descem com a mola e as da frente esterçam (Steer_Front na moto);
  **Buggy**: chassi arfa/rola com a aceleração (±6°); **Moto/Hover**: rolagem nas curvas até **35°** (+15% no drift);
  modelo acompanha a normal do chão; turbinas do hover basculam com acelerador/curva; hover flutua (bob).
- **Aríete / atropelamento**: OverlapBox na frente acima de 5 m/s; dano = vel × 2.4 (× 2.5 no aríete) × massa/600,
  empurrão para frente/lado/cima, faíscas, "ATROPELADO!"; barris explodem. Aríete (B.DIR): impulso + 0.6 s, recarga 5 s.
- Turbo (SHIFT): ×1.55 vel. máx. por 1.4 s, recarga 4 s, gasta 18 de energia.
- Drift (ESPAÇO): faíscas e poeira nas rodas traseiras quando a derrapagem lateral passa de 2.5 m/s.
- Torreta: base gira 360° (220°/s), cano só arfagem (−12° a +30°) com coice; usa `ElpisBallisticsEngine.Disparar`
  com uma arma Épica de fuzil (9 tiros/s).

## 6. Os veículos atuais
| Veículo | Tipo | Assentos | Destaques |
|---|---|---|---|
| **Cortadora** (Retalho) | Moto | motorista + garupa | rodas-serra, V-twin, escapes que cospem fogo, 30 m/s, rolagem 35°, drift |
| **Vento Solar** (Orbital) | Hover | motorista | turbinas de anel neon basculantes, 34 m/s, sem aríete |
| **Javali de Ferro** | Buggy 4x4 | motorista + artilheiro | suspensão independente, quebra-mato com espetos (aríete), torreta no teto |
| **Valquíria de Elpis** | Dropship VTOL | passageiros na baia | 4 turbinas basculantes, rampa traseira, holofotes volumétricos |

## 7. Dropship (`ElpisDropship`)
- **Chegando**: desce de 38 m (vindo 26 m de trás) em 7.5 s com freio no fim e balanço; turbinas na vertical.
- **Pousada**: rampa abre até encostar no chão (ângulo calculado pela altura da dobradiça), passageiros desembarcam
  sozinhos, `[E]` na rampa/baia = **extração** (`aoExtrair`).
- **Partindo**: rampa fecha, turbinas basculam até 65° e ela sobe acelerando para frente.
- Colisão: MeshCollider no casco e na rampa (dá para subir e entrar na baia); corpo cinemático.

## 8. Mundo aberto (`MundoAbertoGenerator`, menu "Criar Mundo Aberto (veículos)")
- Planície de 360 m — **chão NUNCA plano** (mesmas regras da elpis-level-design, versão própria e leve para mapa grande;
  nome "Solo_Aberto", sem o ElpisGroundGenerator):
  relevo em 4 camadas (colinas, ondulação média, calombos, grão fino) + **mesas** com paredões + **~26 crateras** com
  beiço elevado; células de 2 m facetadas com diagonal alternada; **4 materiais por triângulo** (regolito, regolito
  claro em manchas, fundo de cratera escuro, rocha nas encostas > ~37°) com **detalhe de regolito em espaço de mundo**
  (T_Regolito_Detalhe + normal); raios de ejeção claros nas crateras grandes, trilhas de pneu até os objetivos,
  queimados em volta de acampamentos/destroços; pedras facetadas (icosaedro amassado, base achatada) em afloramentos
  e nas bordas das crateras; **pedregulhos ancorando todo objeto** + 2600 de cascalho solto (sem colisão).
- Marcos: nave antiga acidentada fumegando na cratera do acidente, broca abandonada, torres de antena com luz
  piscando, painéis solares, oleoduto quebrado atravessando o mapa (cobertura longa), destroços espalhados.
- Rochas facetadas combinadas numa malha (com colisão), monólitos de navegação, **rampas de salto** com faixa de perigo,
  ruínas com lâmpadas de gaiola, trilhas de postes até os objetivos, pouso marcado por luzes de emergência.
- Acampamentos por facção com guarnição de **sentinelas** (acordam ao ver o Bigorna), reforço de Elite no primeiro
  abate, baú Épico ao limpar. HUD: objetivo + distância/seta para cada acampamento e para a nave.
- Inserção: o Bigorna começa a bordo da Valquíria (câmera desce junto); veículos estacionados ao lado do pouso.
- NavMesh assado em tempo de execução enquanto a nave desce (esconde o engasgo).
- **Luz de céu aberto (Sol/Lua)**: mundo aberto NÃO usa a penumbra Grim — `MundoAbertoGenerator.Ativo` liga o bloco
  "Mundo aberto — luz de Sol/Lua" do AjusteVisual: sol/lua 1.35 branco-frio a 48°/−38° (sombras longas na diagonal,
  força 0.72), ambiente #3A485C, piso de luz 0.18, névoa leve #29334A densidade 0.0045, céu visível; inimigos com cor
  cheia (sem silhueta). Faróis e lanterna continuam, mas como reforço — a luz principal é o céu.
