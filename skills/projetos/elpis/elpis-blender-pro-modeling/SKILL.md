---
name: elpis-blender-pro-modeling
description: Pipeline profissional de modelagem procedural e escultura via Python (bpy/bmesh) no Blender. Proíbe "Primitive Stacking" (empilhar cubos/esferas simples) e exige técnicas de Tech Art: Silhueta BMesh, Cortes Booleanos (CSG), Escultura Orgânica (Skin/Metaballs + Voxel Remesh + Displace), Sulcos de Painéis e Proporções Anatômicas Reais sob Armaduras Pesadas.
---

# Pipeline Profissional de Modelagem Procedural no Blender (`bpy` & `bmesh`)

## REGRA ZERO: PROIBIDO "PRIMITIVE STACKING" (SÍNDROME DO BONECO DE NEVE)
NUNCA construa personagens, armas, veículos ou monstros apenas adicionando `primitive_cube_add` ou `primitive_uv_sphere_add` escalados e espetados uns nos outros. Todo modelo deve usar uma ou mais das **5 Técnicas de Tech Art** abaixo:

## 1. Modelagem de Superfície Dura por Perfil `bmesh` + Cortes Booleanos (CSG)
Em vez de cubos esticados, desenhe a silhueta 2D exata com coordenadas `(x, y)` via `bmesh`, extrude, aplique conicidade (*Taper*) e use objetos cortadores (`Boolean Modifier` com `DIFFERENCE`) para entalhar entradas de ar, cavidades de visor, sulcos de painéis e furos reais em canos:
- Use `bmesh.ops.extrude_face_region` em perfis poligonais desenhados ponto a ponto.
- Use `BOOLEAN` (`DIFFERENCE` / `UNION` com solver `FAST` ou `EXACT`) seguido de `BEVEL` (2 segmentos, `limit_method='ANGLE'`) e `WEIGHTED_NORMAL`.
- Cilindros de peças principais (rodas, turbinas, canos, brocas, jatos) devem ter entre `16` e `24` lados (proibido usar 6 ou 8 lados em peças curvas grandes).

## 2. Escultura Orgânica e Anatômica (`Skin Modifier` / `Metaballs` + `Voxel Remesh` + `Displace`)
Para corpos orgânicos, monstros (Xeno-Feras), raízes e rochas:
1. Crie a estrutura base fundida usando `Metaballs` (`bpy.data.metaballs`) para massas musculares contínuas OU `Skin Modifier` sobre um grafo de vértices com raios anatômicos variáveis (`M_SkinVert.radius`).
2. Converta para `MESH` e aplique o modificador `REMESH` (`mode='VOXEL'`, `voxel_size=0.03`) para gerar uma malha contínua sem costuras secas.
3. Aplique `Displace Modifier` com texturas procedurais (`VORONOI` ou `MUSGRAVE`) para criar carapaças, músculos ou rocha lascada, seguido de `Decimate` (`COLLAPSE`) para otimizar para a Unity.

## 3. Anatomia Humana Real + Armadura "Warhammer / Power Armor" (Proporção Heroica)
Personagens humanoides (como o Bigorna e soldados) NUNCA devem ter membros de blocos retos (estilo Roblox/Minecraft):
- **Base Anatômica Real (8 Cabeças / Proporção Heroica):**
  - Membros com conicidade natural (*Taper*): coxa mais grossa no quadril afunilando no joelho; panturrilha com curva muscular alta afunilando no tornozelo; antebraço mais largo perto do cotovelo e fino no pulso.
  - Torso em "V" (ombros largos, caixa torácica arqueada, cintura marcada e estreita).
- **Medidas em unidades de cabeça (u = altura total / 8; personagem de 1,85 m → u ≈ 0,23 m), z a partir do chão:**

  | Marco | Masculino heroico | Feminino heroico |
  |---|---|---|
  | Topo da cabeça / queixo | 8u / 7u | 8u / 7u |
  | Linha dos ombros | 6,6u | 6,7u |
  | Peito (mamilos) / cintura (umbigo) | 6u / 5u | 6u / 5,1u |
  | Virilha (meio do corpo) / joelho / tornozelo | 4u / 2u / 0,3u | 4u / 2u / 0,3u |
  | Largura dos ombros (deltoides) | 2,3–2,5u | 1,9–2,1u |
  | Largura da cintura / do quadril | 1,3u / 1,5u | 1,1u / 1,7–1,8u |
  | Cotovelo / pulso (braço caído) | na cintura / na virilha | na cintura / na virilha |
  | Largura do pescoço | 0,6u | 0,45u |

  Feminino: mesma altura em u, ombros mais estreitos que o quadril, cintura bem marcada, membros mais finos, mesma
  massa de armadura (a armadura dela não é "menor", só acompanha outro corpo). A armadura soma 10–25% de volume por cima
  da silhueta; nunca substitui a anatomia por baixo.
- **A Grandeza vem da Armadura Sobreposta (Camada Externa):**
  - Modele a armadura como **cascas chanfradas independentes com espessura real** montadas *por cima* da silhueta anatômica humana:
    - **Ombreiras Colossais (Pauldrons):** Curvas abobadadas em múltiplas camadas com borda reforçada saliente (*Trim* metálico), posicionadas acima da linha natural do ombro.
    - **Gorjal / Colarinho Blindado (Gorget):** Arco de aço alto que envolve o pescoço e protege o queixo.
    - **Grevas e Manoplas (Greaves & Gauntlets):** Canelas blindadas amplas estilo *Space Marine* com joelheiras angulares salientes e pistões hidráulicos nos tornozelos; luvas com placas no dorso da mão e dedos articulados.
    - **Mochila Propulsora Dorsal (Power Pack):** Bloco de reator pesado nas costas com duas turbinas anguladas para fora.

## 4. Hélices, Rosca de Broca, Molas e Cabos (`Screw` & `Curves`)
- Para brocas, molas de suspensão e bobinas: use `Screw Modifier` (`angle=radians(360*turns)`, `screw_offset=length`).
- Para mangueiras hidráulicas, escapamentos e cabos: use curvas `Bezier` com `bevel_depth`.

## 5. Sulcos de Painéis FUNCIONAIS e 5 Materiais
- O contorno `Solidify` só desenha a silhueta externa. Linhas de quadrinho DENTRO das placas existem só onde há uma divisão real
  (porta, tampa de motor, separação do cockpit, escotilha): sulco estreito (0.02–0.03 m) e raso (0.02–0.03 m) feito por
  cortador booleano fino (`material_mode='TRANSFER'`, cortador com o material preto/borracha) — o fundo e as paredes do sulco
  saem pintados de preto. Ver a seção 6: NUNCA em grade.
- Todo modelo complexo deve dividir suas faces em **5 materiais distintos**:
  1) `Mat_Primary_Paint` (Cor principal), 2) `Mat_Secondary_DarkMetal` (Chassi/juntas/undersuit), 3) `Mat_Raw_Steel` (Bordas/parafusos/pistões/lâminas), 4) `Mat_Matte_Rubber` (Pneus/cabos/selos) e 5) `Mat_Emissive_Accent` (Visores/faróis/jatos).

## 6. PROIBIDO "Grid/Waffle Paneling" + Lei 70/20/10 de Superfície
- **PROIBIDO aplicar `bmesh.ops.inset_individual` (ou `create_paneled_hull`) em grades regulares de faces** (bisect a cada N metros
  + inset em todas as faces). Isso gera visual de colcha de retalhos / azulejo de banheiro — blindagem militar sci-fi não é ladrilho.
- **Lei 70/20/10:**
  - **70%** da lataria = **placas grandes, limpas e em Flat Shading** (`face.smooth = False`) para a cor da pintura respirar.
  - **20%** = volumes estruturais salientes que quebram a silhueta (costelas/arcos externos, vigas, carenagens, corcundas, caudas).
  - **10%** = micro-detalhe (rebites em fileira ao longo de costelas/vigas, grelhas, parafusos, luzes).
  - Sulcos de painel em **no máximo 15–20% das arestas**, só em divisões funcionais reais (porta lateral, tampa do motor,
    separação do cockpit, escotilha de manutenção).
- **Normais limpas:** placas blindadas e chanfros SEMPRE em Flat Shading (cor sólida pura, sem manchas de gradiente).
  `smooth` só nas paredes laterais de cilindros (rodas, turbinas, canos, chaminés), SEMPRE com `Edge Split` / arestas `Sharp`
  acima de 30° (a tampa e as quinas continuam retas). Faces criadas por booleanas herdam o sombreamento do cortador: cortador
  também em flat.

## 7. Silhueta por VOLUMES (nunca "caixa de sapato")
- Um casco de uma peça só, reto da frente até atrás, é proibido mesmo com loft/afunilamento. Divida o corpo em **3–5 volumes com
  larguras e alturas diferentes** que se leem de cima (câmera isométrica). Ex. dropship (Valkyrie/Pelican):
  1. **Cockpit em degrau**: mais estreito (~60% da largura da baia) e mais baixo que o teto, projetado à frente, queixo
     chanfrado para baixo, torreta/sensor sob o nariz, para-brisa em 3 vidros escuros com vigas grossas.
  2. **Baia de carga** larga com **costelas blindadas externas** (4 arcos chanfrados em metal escuro abraçando o casco) sobre
     chapas laterais limpas com a faixa de identificação da facção.
  3. **Corcunda dorsal** (reator/motor) com grelhas inclinadas e chaminés anguladas para trás + **cauda dupla** (H/V) acima da rampa.
  4. **Asas com planta chanfrada** (perfil desenhado ponto a ponto em XY, extrudado em Z) segurando as naceles, com anéis de
     reforço em aço bruto, bocal de exaustão detalhado e luzes de navegação nas pontas.
- O degrau entre volumes já é uma linha de quadrinho natural — prefira degraus de volume a sulcos.
