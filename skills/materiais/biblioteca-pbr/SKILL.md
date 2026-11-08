---
name: biblioteca-pbr
description: "Como escolher materiais: presets PBR da biblioteca (metais, vidros, madeira, construção, tecidos, pele, pelo, escamas) passados às ferramentas por material e cor, ou à função anvil_material no modo script."
---
# Biblioteca de materiais

## Com as ferramentas (modo agente)
Toda ferramenta que cria peça aceita `material` (nome do preset) e `cor` ([r, g, b] de 0 a 1). Para trocar
depois: `aplicar_material(nome, material, cor)`.

| Grupo | Presets | Use em |
|---|---|---|
| Metais | `car_paint`, `painted_metal`, `worn_metal`, `steel`, `chrome`, `aluminum`, `dark_metal` | carrocerias, máquinas, ferragens |
| Transparentes | `glass`, `tinted_glass` | janelas, vidros de carro, garrafas |
| Sintéticos | `rubber`, `plastic` | pneus, puxadores, carcaças |
| Construção | `brick`, `concrete`, `plaster`, `roof_tile`, `stone`, `wood` | paredes, telhados, pisos, móveis |
| Tecidos | `fabric`, `denim`, `leather` | estofados, roupas, cintos |
| Biológicos | `fur_short`, `skin`, `scales`, `foliage`, `soil` | animais, pele, répteis, plantas, terreno |
| Luz | `emissive` | faróis, telas, visores |

Regras: material = do que a peça é feita de verdade; ao menos 3 materiais por objeto com várias
peças; peças vizinhas com materiais ou tons diferentes; a cor pedida pelo usuário vai em `cor`.

## No modo script
`anvil_material` e `anvil_assign` JÁ estão carregadas: **nunca as redefina**, só chame:
`mat = anvil_material("wood", color=(0.5, 0.3, 0.2))` e `anvil_assign(obj, mat)`.

---

## Modo script (referência para quem escreve código bpy)

As funções abaixo JÁ ESTÃO DEFINIDAS no Blender quando o seu script roda. Não escreva nós de shader à mão; use a biblioteca. Ela se adapta sozinha ao estilo escolhido.

```python
mat = anvil_material(preset, color=None, name=None, metallic=None, roughness=None)
anvil_assign(obj, mat, face_indices=None)   # objeto inteiro ou só algumas faces
anvil_outline(obj, thickness=0.01)          # contorno preto (estilo cel-shading)
```

## Presets
| Grupo | Presets |
|---|---|
| Metais | `car_paint`, `painted_metal`, `worn_metal`, `steel`, `chrome`, `aluminum`, `dark_metal` |
| Transparentes | `glass`, `tinted_glass` |
| Sintéticos | `rubber`, `plastic` |
| Construção | `brick`, `concrete`, `plaster`, `roof_tile`, `stone`, `wood` |
| Tecidos | `fabric`, `leather` |
| Natureza | `soil`, `foliage`, `stone`, `wood` |
| Luz | `emissive` (faróis, telas, visores) |

## Regras
- Pense no material **real** de cada peça: carroceria de carro = `car_paint` com a cor pedida; pneus = `rubber`; aros = `chrome`/`aluminum`; vidros = `glass`/`tinted_glass`; paredes = `brick`/`plaster`; telhado = `roof_tile`; esquadrias = `wood`/`aluminum`.
- Use `color=(r, g, b)` (0 a 1) para dar a cor pedida pelo usuário; para variar o mesmo preset em peças diferentes, passe também um `name` diferente.
- Todo asset tem pelo menos 3 materiais distintos separando suas peças.
- Para uma peça de um objeto só com material diferente (ex.: sulcos escuros), use `face_indices` com os índices das faces criadas no `bmesh`.
