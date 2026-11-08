---
titulo: Mask Modifier
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/mask.html
---

# Mask Modifier

The Mask modifier allows vertices of an object to be hidden dynamically based on vertex groups.

## Options

**Mode**

The Mask Modifier can hide parts of a mesh based on two different modes, selectable from this select menu.

**Vertex Group**

Hides all vertices not included in the chosen vertex group.

 The Mask modifier in Vertex Group mode.   |      |
**Armature**

When in Pose Mode, vertices belonging to the vertex group associated with the active bone (same names) will be visible. Vertices not in that group will be hidden.

 The Mask modifier in Armature mode.   |      |
**Smooth**

When using Vertex Group Mode, use weights to cut faces at the weight contour. This option will result in a mask that has smoother removing the sharp edges along the mask edges.
**Invert**

Normally, vertices belonging to the selected vertex group (or group associated with the active pose bone) will be shown. The Invert toggle allows you to reverse this behavior, instead only showing vertices which do not belong to the vertex group.
**Threshold**

Hides vertices with weights less than or equal to this value.
