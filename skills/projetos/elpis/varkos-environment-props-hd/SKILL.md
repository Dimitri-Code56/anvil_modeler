---
name: varkos-environment-props-hd
description: Pipeline de alta densidade geométrica para Arquitetura Sci-Fi Industrial, Paredes, Rampas, Postes, Lanternas e Props de Cobertura no Blender (bpy/bmesh). Proíbe cunhas lisas, cubos esticados e postes de cilindro único.
---

# Pipeline HD para Arquitetura e Props de Ambiente (Padrão Varkos)

Complementa `elpis-blender-pro-modeling` (regras 6 e 7: zero waffle grid, lei 70/20/10, flat shading, silhueta por volumes).
Ferramentas: `Blender/props_ambiente.py` (biblioteca de props), `props_hd.py` (treliça, barras/caixas em lote, pistão, export plano),
`elpis_greeble_kit.py` (5 materiais, Solidify de contorno, rebites em lote, booleana MANIFOLD, contagem rápida no depsgraph).
Saída: `Unity/Assets/Art/Models/Varkos_Props/Cenario/*.fbx`. Pivô na base, centro do módulo; frente (−Y no Blender) = +Z na Unity.

## REGRA ZERO: PROIBIDO "BLOCOS DE CIMENTO" E "CUNHAS LISAS"
NUNCA modele uma parede como um cubo escalado, uma rampa como um prisma triangular liso ou um poste como um cilindro espetado num cubo. Todo prop de ambiente deve exibir **3 Camadas Construtivas Reais**:
1. **Esqueleto Estrutural (`Mat_Secondary_DarkMetal`):** Vigas em "I" (I-Beams), treliças em "X", colunas de sustentação chanfradas e sapatas parafusadas no chão.
2. **Placas de Revestimento e Pisos (`Mat_Primary_Paint` / `Mat_Raw_Steel`):** Chapas grossas sobrepostas com chanfro de 45° nas quinas, Flat Shading limpo (70% de área limpa, zero Waffle Grid!), faixas de perigo amarelo/preto nos rodapés e grelhas antiderrapantes reais.
3. **Infraestrutura e Micro-Detalhes (`Mat_Matte_Rubber` + `Mat_Emissive_Accent`):** Conduítes elétricos curvos (`Bezier`), caixas de disjuntores laterais, alças de içamento, parafusos sextavados nos apoios e luminárias blindadas com grade de proteção (*cage*).

---

## ESPECIFICAÇÕES TÉCNICAS POR CATEGORIA DE ASSET

### 1. Paredes e Muralhas Modulares (`4.000` a `8.000` tris por módulo)
- **Perfil Transversal em "C" ou Trapézio Escalonado (Nunca Reto):**
  - **Base Pesada (Rodapé Balístico de 0.6m):** Mais larga que o topo, chanfrada a 45°, com sapatas de ancoragem parafusadas no solo e faixa de perigo amarelo/preto.
  - **Corpo Central:** Recuado em relação aos pilares laterais, dividido em 2 ou 3 grandes placas blindadas assimétricas com sulcos profundos (`panel grooves` pretos), rebites nos cantos e 2 tubulações horizontais (`Bezier` ou cilindros de 16 lados) presas por abraçadeiras metálicas.
  - **Contrafortes / Pilares Laterais:** Vigas verticais salientes a cada 4m com chanfros, olhais de guindaste no topo e caixa elétrica lateral.
  - **Topo / Cornija Técnica:** Borda superior chanfrada com calha de cabos e friso emissivo de status.

### 2. Rampas de Salto e Acesso (`3.500` a `6.500` tris)
- **Proibido Cunha Maciça Lisa:** Uma rampa industrial é uma estrutura aberta por baixo e tratorada por cima!
- **Superfície de Rodagem:** Piso composto por **chapas de aço com nervuras antiderrapantes 3D reais** (tiras horizontais ou espinha de peixe em `Mat_Raw_Steel`) + **2 guias laterais altas (Guardrails / Meios-fios chanfrados)** pintadas com faixas de alerta para guiar as rodas dos veículos.
- **Estrutura Inferior Visível:** Embaixo da rampa, modele vigas em "I" diagonais, treliças metálicas cruzadas em "X" e pistões hidráulicos ou cavaletes pesados apoiados em sapatas no chão.

### 3. Postes, Torres de Iluminação e Lanternas/Luminárias (`2.500` a `6.000` tris)
- **Postes de Luz Táticos (`Prop_LightPole_HD`):**
  - **Base Octogonal Blindada (`0.8m` de altura):** Bloco de concreto/aço chanfrado com 4 aletas de reforço triangular (*gussets*), caixa de força com manômetro/alavanca lateral e cabo grosso saindo para o chão.
  - **Mastro Composto:** Coluna treliçada ou tubo telescópico escalonado (mais grosso na base, afinando em 3 estágios com anéis de flange parafusados) + escada marinheiro lateral ou degraus de manutenção + cabo de energia subindo preso por braçadeiras.
  - **Cabeça de Iluminação Dupla/Tripla:** Braço angular em "T" ou "Y" segurando **2 a 3 Refletores Industriais Individuais** (carcaça traseira aletada para dissipação térmica, aba direcional *barn-doors*, lente frontal em `Mat_Emissive_Accent` e grade fina de proteção frontal).
- **Lanternas de Parede, Sinalizadores de Chão e Balizadores (`800` a `2.000` tris):**
  - *Sinalizadores Lunares (`Prop_GroundBeacon_HD`):* Base tripé ou hexágono pesado de aço com garras cravadas no solo, bateria lateral, gaiola de proteção metálica (*roll-cage* de 4 hastes) envolvendo o domo luminoso central vermelho/âmbar.
  - *Luminárias de Bunker (`Prop_WallLight_HD`):* Base chanfrada parafusada na parede + tubo de LED blindado protegido por grade metálica arqueada.

### 4. Containers, Caixas de Cobertura e Barricadas (`2.000` a `5.000` tris)
- **Containers Sci-Fi:** Paredes com ondulação trapezoidal real (chapa corrugada modelada via `bmesh`, não parede lisa!), vigas de quina salientes com furos de trava (*twist-locks*), portas traseiras duplas com 4 barras de tranca verticais, alavancas e painel numérico lateral.
- **Barricadas e Muretas de Cobertura (`1.1m` de altura):** Placas balísticas anguladas em "V" invertido com frestas de tiro chanfradas (Booleana), apoios traseiros em cantoneira, alças laterais de transporte e marcas de desgaste.

## NA UNITY
- Os cenários de Varkos são montados por código (`VarkosMapa`, `VarkosNorte`…): cada peça HD entra como instância do FBX
  (campos `prefab*` preenchidos pelo `MundoAbertoBuilder`), escalada no comprimento quando o trecho não é múltiplo do módulo.
- Colisor: `MeshCollider` estático nos filhos de malha (rampas, muros, contêineres); efeitos e luzes na camada 2.
- Luz real (sem sombra) criada pelo código no marcador `Luz` de postes e sinalizadores — sombra só na lanterna e nos faróis.
