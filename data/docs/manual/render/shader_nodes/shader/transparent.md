---
titulo: Transparent BSDF
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/transparent.html
---

# Transparent BSDF

The Transparent BSDF is used to add transparency without refraction, passing straight through the surface, as if there were no geometry there. Useful with alpha maps, for example. This shader affects light paths somewhat differently than other BSDFs. Note that only pure white transparent shaders are completely transparent.

## Inputs

**Color**

Color of the surface, or physically speaking, the probability for each wavelength that light is blocked or passes straight through the surface.

## Properties

This node has no properties.

## Outputs

**BSDF**

Standard shader output.

## Examples

   |
Transparent shader (pure white).     |
Transparent shader behavior.      |
Transparent shader (gray).     |
