---
titulo: Cast Modifier
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/deform/cast.html
---

# Cast Modifier

The Cast modifier shifts the shape of a mesh, curve, surface or lattice, towards any of a few predefined shapes (sphere, cylinder, cuboid).
It is equivalent to the To Sphere tool in Edit Mode, and what other programs call “Spherify” or “Spherize”, but, as written above, it is not limited to casting to a sphere.

Tip
The Smooth Modifier is a good companion to Cast, since the cast shape sometimes needs smoothing to look nicer or even to fix shading artifacts.

Note
For performance reasons, this modifier only works with local coordinates. If the modified object looks wrong, you may need to apply its transformations, especially when casting to a cylinder.

## Options

The Cast modifier.

**Shape**

Menu to choose target shape of the projection: Sphere, Cylinder or Cuboid.
**Axis**

Toggle buttons to enable/disable the modifier in the X, Y, Z axes directions (X and Y only for Cylinder cast type, since the Z axis remains unaffected).
**Factor**

The factor to control blending between original and cast vertex positions.
It is a linear interpolation: 0.0 gives original coordinates (i.e. modifier has no effect), 1.0 casts to the target shape.
Values below 0.0 or above 1.0 exaggerate the deformation, sometimes in interesting ways.
**Radius**

If nonzero, this radius defines a sphere of influence. Vertices outside it are not affected by the modifier.
**Size**

Alternative size for the projected shape. If zero, it is defined by the initial shape and the control object, if any.
**Size from Radius**

If activated, calculate Size from Radius, for smoother results.
**Vertex Group**

If set, restrict the effect to only the vertices in that vertex group. This allows selective, real-time casting, by painting vertex weights.

** Invert**

Inverts the influence of the selected vertex group, meaning that the group now represents vertices that will not be deformed by the modifier.
The setting reverses the weight values of the group.
**Object**

The name of an object to control the effect. The location of this object’s origin defines the center of the projection. Also, its size and rotation transform the projected vertices.

Hint
Animating (keyframing) this control object also animates the modified object’s casting deformation.

## Example

Top: Suzanne without modifiers. Middle: Suzanne with each type of Cast Modifier (Sphere, Cylinder and Cuboid). Bottom: Same as above, but now only X axis is enabled. Sample blend-file.
