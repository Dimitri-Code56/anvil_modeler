---
titulo: Refraction BSDF
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/refraction.html
---

# Refraction BSDF

The Refraction BSDF is used to add glossy refraction with sharp or microfacet distribution, used for materials that transmit light. For best results this node should be considered as a building block and not be used on its own, but rather mixed with a glossy node using a Fresnel factor. Otherwise it will give quite dark results at the edges for glossy refraction.

## Inputs

**Color**

Color of the surface, or physically speaking, the probability that light is refracted for each wavelength.
**Roughness**

Influences sharpness of the refraction; perfectly sharp at 0.0 and smoother with higher values.
**Normal**

Normal used for shading; if nothing is connected the default shading normal is used.

## Properties

**Distribution**

Microfacet distribution to use.

**GGX:**

GGX microfacet distribution.
**Beckmann:**

Cycles Only Beckmann microfacet distribution.

## Outputs

**BSDF**

Standard shader output.

## Examples

Refraction Shader.
