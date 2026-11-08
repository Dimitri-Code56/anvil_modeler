---
titulo: Color Attribute Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/vertex_color.html
---

# Color Attribute Node

The Color Attribute node provides access to Color Attributes as well as their alpha value.

## Inputs

This node has no inputs.

## Properties

**Color Attribute**

The target Color Attribute. The listed Color Attributes are those of the mesh of the active object. If the active object has no mesh, a warning will be displayed. If the property is marked in red, it means the Color Attribute is not available in the mesh of the active object, but it may be available in other meshes of objects that share this material!

## Outputs

**Color**

Standard color output.
**Alpha**

Alpha value.
