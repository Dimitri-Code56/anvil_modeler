---
titulo: Sheen BSDF
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/sheen.html
---

# Sheen BSDF

Cycles Only
The Sheen BSDF is used to add reflection to materials that have micro surface details such as cloth or dust. This shader is intended to be layered on top of other shaders such as dielectric or metallic shader setups.

## Inputs

**Color**

Color of the surface, or physically speaking, the probability that light is reflected for each wavelength.
**Roughness**

Controls the amount of color that is reflected back to the camera, higher values reflect more color and can give a dusty appearance, while lower values look fuzzy and darker.
**Normal**

Normal used for shading; if nothing is connected the default shading normal is used.

## Properties

**Distribution**

Sheen shading model.

**Ashikhmin:**

Classic Ashikhmin velvet, used in Blender versions prior to 4.0
**Microfiber:**

Microflake-based model of multiple scattering between normal-oriented fibers.

## Outputs

**BSDF**

Standard shader output.

## Examples

   |
The Sheen shader example.     |
The Sheen shader behavior.
