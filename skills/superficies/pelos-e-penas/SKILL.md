---
name: pelos-e-penas
description: "Pelagem e plumagem de animais (pelo curto, médio e longo, padrões como manchas e listras, bigodes, penas): do pelo por material até fios de verdade, com direção e cor naturais."
---
# Pelos e penas

> **Preset pronto (modo agente):** use `material="fur_short"` em qualquer ferramenta (presets: `fur_short`),
> com `cor` para o tom. O resto desta skill explica como ajustar ou montar o shader à mão no modo script.

Escolha o nível pela distância e pelo comprimento do pelo. Nada de geometria de fios quando o material
resolve; nada de material liso quando o pelo é longo.

## Nível 1: pelo curto e rente (cavalo, gato de pelo curto, coelho visto de longe)
Só material + leve deslocamento, sem fios:
- `Sheen Weight` alto (0,8–1,0) e roughness 0,85–0,95: dá o "veludo" típico de pelo.
- **Fuzz na silhueta:** `Layer Weight`/`Fresnel` clareando e dessaturando a borda do objeto.
- **Direção:** bump com textura esticada no sentido do pelo (do focinho para a cauda, de cima para
  baixo nas patas): `Wave`/ruído com escala anisotrópica.
- Deslocamento leve (`Displace` 1–3 mm, ruído fino) para quebrar a superfície perfeita.

## Nível 2: pelo médio e longo (coelho de perto, raposa, cachorro, juba)
Fios de verdade:
- Prefira o sistema de cabelo por curvas da versão atual do Blender (objeto Curves + nós de geometria);
  se não existir, use partículas de cabelo (`ParticleSettings.type = 'HAIR'`). **Confira na
  documentação recuperada qual API existe nesta versão** antes de escrever o código.
- Parâmetros de partida: comprimento real (coelho 2–3 cm, raposa 4–6 cm), densidade alta em áreas
  visíveis, agrupamento (clump) 0,3–0,6, ondulação leve, pontas afinando.
- Direção por guias ou pelo campo do corpo (focinho → cauda); nunca fios saindo na normal pura (vira
  ouriço).
- Material de cabelo: `Principled Hair BSDF` (Cycles) ou Principled com anisotropia em EEVEE; melanina
  define a cor (0 = loiro/branco, 1 = preto).
- Mantenha uma camada de pelo por material por baixo (nível 1): onde os fios rareiam não aparece "pele
  de plástico".

## Cor e padrões
- **Agouti** (coelho selvagem, lebre): cada fio com raiz clara, faixa escura e ponta clara → no material,
  faixas finas de ruído misturando 3 tons.
- **Contrassombreamento:** barriga, peito e parte de baixo mais claros (gradiente pela altura Z do
  objeto). Quase todo mamífero e ave tem.
- Manchas (`Voronoi`/ruído com limiar), listras (`Wave` deformado por ruído), máscara facial com
  transição suave, não borda dura.

## Detalhes que vendem o animal
- **Bigodes/vibrissas:** curvas finas e afinando, saindo de pontos na região do focinho, levemente
  curvadas para baixo; claros e brilhantes.
- Tufos: orelhas, ponta da cauda, bochechas; pelo mais curto no focinho e nas patas.
- Rabo de algodão (coelho): pelo mais longo, mais claro e mais denso.

## Penas
- Corpo: material como no nível 1 com padrão de escamas sobrepostas (voronoi + gradiente) imitando
  penas de contorno.
- Penas de voo (rêmiges, cauda): geometria plana com a forma da pena (raque central + vexilo), em fileira
  sobreposta, cada uma levemente rotacionada; textura com barbas paralelas.
- Iridescência (pombos, beija-flores, pavão): `Thin Film` no Principled quando existir, ou cor
  dependente do ângulo via `Layer Weight`.
