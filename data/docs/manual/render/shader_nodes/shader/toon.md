---
titulo: Toon BSDF
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/toon.html
---

# Toon BSDF

Cycles Only
The Toon BSDF is used to create Diffuse and Glossy materials with cartoon light effects.

## Inputs

**Color**

Color of the surface, or physically speaking, the probability that light is reflected for each wavelength.
**Size**

Parameter between 0.0 and 1.0 that gives an angle of reflection between 0° and 90°.
**Smooth**

This value specifies an angle over which a smooth transition from full to no reflection happens.
**Normal**

Normal used for shading; if nothing is connected the default shading normal is used.

## Properties

**Component**

The material component to base the toon effect.

**Diffuse:**

Use shading based on the Diffuse BSDF.
**Glossy:**

Use shading based on the Glossy BSDF for specular reflection.

## Outputs

**BSDF**

Standard shader output.

## Examples

Example of Toon Shader.
