---
titulo: Volume Info Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/volume_info.html
---

# Volume Info Node

The Volume Info node provides information about Smoke Domains.

## Inputs

This node has no inputs.

## Properties

This node has no properties.

## Outputs

**Color**

Gives the color of the smoke inside the Fluid Domain. The color and vector outputs are the same. The Factor output is an average of the channels.
**Density**

Gives a scalar defining the density of any smoke inside the Fluid Domain.
**Flame**

Gives a scalar defining the density of any fire inside the Fluid Domain. All three outputs are the same.
**Temperature**

Gives a scalar defining the temperature of the volume. Values in the range 0 - 1 map to 0 - 1000 kelvin. This may be used to render physically-based fire with the Blackbody or Principled Volume shaders. All three outputs are the same.

## Example

Smoke density.
Computing the color of fire using the Blackbody node. Since the Blackbody node expects its input in Kelvin, the temperature output has to be remapped first.
