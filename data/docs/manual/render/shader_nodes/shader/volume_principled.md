---
titulo: Principled Volume
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/volume_principled.html
---

# Principled Volume

The Principled Volume shader combines all volume shading components into a single easy to use node. Volumes like smoke and fire can be rendered with a single shader node, which includes scattering, absorption and blackbody emission.

## Inputs

**Color**

Volume scattering color.
**Color Attribute**

Volume grid for coloring the volume. Use “color” for smoke simulations.
**Density**

Density of the volume.
**Density Attribute**

Volume grid to define the density, typically “density”.
**Anisotropy**

Backward or forward scattering direction.
**Absorption Color**

Volume shadow color tint.
**Emission Strength**

Amount of light to emit.
**Emission Color**

Emission color tint.
**Blackbody Intensity**

Blackbody emission for fire. Set to 1 for physically accurate intensity.
**Blackbody Tint**

Color tint for blackbody emission.
**Temperature**

Temperature in kelvin for blackbody emission, higher values emit more.
**Temperature Attribute**

Volume grid to define the temperature, typically “temperature”.

## Properties

This node has no properties.

## Outputs

**Volume**

The Volume Shader output must be plugged into the Volume Input of the Material or World Output node.

## Examples
