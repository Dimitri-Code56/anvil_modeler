---
titulo: World Output Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/output/world.html
---

# World Output Node

The World Output node is used to output color information to the scene’s World.
To access this node, change the Shader Type in the header of the Shader Editor to World.

## Inputs

**Surface**

The appearance of the environment. Usually connected to a Background shader.
**Volume**

Used to add volumetric effects to the world. See the shaders Principled Volume, Volume Absorption, and Volume Scatter for more information.

Note
It’s not possible to have a Surface and a Volume at the same time: surfaces are assumed to be at an infinite distance from the camera, so they will always be fully occluded by the volume.

## Properties

**Target**

Render engine the input shaders are used for. By default, shaders are shared between Cycles and EEVEE – with multiple output nodes, a specialized shader setup can be created for each.

## Outputs

This node has no outputs.
