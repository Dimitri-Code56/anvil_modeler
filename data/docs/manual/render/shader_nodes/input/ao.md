---
titulo: Ambient Occlusion Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/ao.html
---

# Ambient Occlusion Node

The Ambient Occlusion node computes how much the hemisphere above the shading point is occluded. This can be used for procedural texturing, for example to add weathering effects to corners only.
For Cycles, this is an expensive shader and can slow down render significantly. If render time is a concern, using Pointiness from the Geometry node or baking Ambient Occlusion will result in faster renders.

Note

**Cycles Only**

**The Ambient Occlusion node will not produce a valid result when:**

-
The object is either a Caustic caster or Caustic receiver while the scene contains an active Caustic caster, Caustic receiver, and Shadow Caustic Light.
-
Open Shading Language is active while using the OptiX rendering backend.

See also
The Ambient Occlusion pass gives occlusion factors across the whole render for use in compositing.

## Inputs

**Color**

Tint for AO output color.
**Distance**

Distance up to which other objects are considered to occlude the shading point.
**Normal**

Normal used for ambient occlusion; if nothing is connected the default shading normal is used.

## Properties

**Samples**

Number of samples to use for ray-traced ambient occlusion sampling. Keep as low as possible for optimal performance.
**Inside**

Detect convex rather than concave shapes, by computing occlusion inside mesh.
**Only Local Cycles Only**

Only detect occlusion from the object itself, and not others.

## Outputs

**Color**

Ambient occlusion with color tint.
**AO**

Ambient occlusion factor without color tint.

## Example

White AO shader.
