---
name: codigo-bpy
description: "Quando o usuário pede um script Python para o Blender (bpy/bmesh): padrões que funcionam fora do modo de edição, nomes conferidos na documentação e código seguro."
---
# Escrever código bpy

- **Confira os nomes.** Antes de usar um tipo de modificador, nó, entrada de nó ou propriedade, busque na
  documentação da API (ex.: "BevelModifier", "ShaderNodeBsdfPrincipled inputs"). Se a ferramenta `verificar_api`
  estiver disponível, use-a para conferir no Blender aberto.
- **Criar malha sem modo de edição:** `bm = bmesh.new()` → `bmesh.ops.create_cube(bm, size=1)` ou
  `bm.verts.new(...)`/`bm.faces.new(...)` → `me = bpy.data.meshes.new(nome)` → `bm.to_mesh(me); bm.free()` →
  `ob = bpy.data.objects.new(nome, me)` → `bpy.context.collection.objects.link(ob)`.
- **Editar malha existente:** `bm = bmesh.new(); bm.from_mesh(ob.data)` ... `bm.to_mesh(ob.data); bm.free()`.
  Evite `bmesh.from_edit_mesh` e operadores `bpy.ops.mesh.*` de edição, que exigem o modo de edição.
- **Modificadores:** `m = ob.modifiers.new(name="Bevel", type="BEVEL")`; ajuste as propriedades pelo nome da API.
- **Materiais:** `mat = bpy.data.materials.new(nome); mat.use_nodes = True`; ache o nó pelo tipo
  (`next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`) e as entradas pelo nome do socket.
- **Primitivas com tamanho diferente por eixo:** crie com `size=1` e ajuste `ob.scale = (x, y, z)`; `size`
  aceita um número só.
- **Segurança:** nada de `os`, `subprocess`, `open()` em arquivos do sistema, salvar/abrir .blend ou apagar
  objetos que não foram criados pelo script.
- Entregue o script completo em um bloco ```python``` e explique em 2–3 linhas o que ele faz.
