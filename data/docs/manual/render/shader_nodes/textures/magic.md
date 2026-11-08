---
titulo: Magic Texture Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/magic.html
---

# Magic Texture Node

The Magic Texture node is used to add a psychedelic color texture. It can be used for “Thin Film Interference” if you assign a Reflection Texture Coordinate to the Vector input and use a relatively high Turbulence. The RGB components are generated independently with a sine formula.

## Inputs

**Vector**

Texture coordinate to sample texture at; defaults to Generated texture coordinates if the socket is left unconnected.
**Scale**

Scale of the texture.
**Distortion**

Amount of distortion.

## Properties

**Depth**

Number of iterations.

## Outputs

**Color**

Texture color output.
**Factor**

Texture intensity output.

## Examples

Magic texture: Depth 10, Distortion 2.0.
