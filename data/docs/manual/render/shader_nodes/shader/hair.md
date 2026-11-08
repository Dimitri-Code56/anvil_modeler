---
titulo: Hair BSDF
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/shader/hair.html
---

# Hair BSDF

Cycles Only
The Hair BSDF node is used to add shading for Hair.

## Inputs

**Color**

Color of the hair.
**Offset**

Controls the way the light is rotated (angular shift) for the reflection/transmission.
Reflection Offset.
Transmission Offset.
**Roughness U/V**

Controls the roughness in the direction light is skewed, and perpendicular to it.

   |
Roughness when using the Reflection Component.     |
Roughness when using the Transmission Component.
**Tangent**

Input tangent.

## Properties

**Component**

There are two components that can be used to control the look of the hair. Usually you are going to want each of these and use a Mix Node.

**Reflection:**

The light that bounces off the surface of the hair.
**Transmission:**

The light that passes through the hair and exits on the other side.
With Mix node: 0 is full Reflection, 1 is full Transmission.

## Outputs

**BSDF**

Standard shader output.
