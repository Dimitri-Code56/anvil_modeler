---
titulo: Vector Rotate Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/utilities/vector/vector_rotate.html
---

# Vector Rotate Node

The Vector Rotate Node provides the ability to rotate a vector around a pivot point (Center).

## Inputs

**Vector**

Vector to be rotated.
**Center**

Point to rotate around.
**Axis**

Axis to rotate around.
**Angle**

Angle to rotate the input vector by.
**Rotation**

When Type is set to Euler, rotate the input vector by these angles around the X, Y, then Z axes in that order.

## Properties

**Type**

The type of angle input.

**X/Y/Z Axis:**

Rotates the vector around the defined axis and the amount of rotation is defined by the Angle input.
**Axis Angle:**

Rotates the vector around an arbitrary axis defined by the Axis input vector. The amount of rotation is defined by the Angle input.
**Euler:**

Rotates the vector about a center point defined by the Center input vector. The amount of rotation on each axis is defined by the Rotation input vector.
**Invert**

Inverts the rotation angle.

## Outputs

**Vector**

The rotated vector.

## Examples

Vector Rotate node example.
