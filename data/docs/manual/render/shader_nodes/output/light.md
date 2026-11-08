---
titulo: Light Output Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/output/light.html
---

# Light Output Node

The Light Output node defines the final shader used by a Light object.
It is used to control how a light emits energy in the scene using shader nodes. Currently, light shaders are only supported by the Cycles render engine. When evaluated in other contexts or renderers, the node has no effect.
See Nodes for more information about using shader nodes with lights.

## Inputs

**Surface**

Shader defining the emitted light. Typically this is an Emission shader, which controls the light’s color and intensity. Only emission-based shading affects lighting; other shader types have no effect when connected to a light.

## Properties

**Target**

Specifies which render engine the connected shader applies to.

**All:**

The shader is used by all render engines.
**Cycles:**

The shader is only used when rendering with Cycles.
**EEVEE:**

The shader is only used when rendering with EEVEE.
Using multiple Light Output nodes with different targets allows creating renderer-specific light setups.

## Outputs

This node has no outputs.
