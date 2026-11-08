---
titulo: White Noise Texture Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/textures/white_noise.html
---

# White Noise Texture Node

The White Noise Texture node returns a random number based on an input Seed. The seed can be a number, a 2D vector, a 3D vector, or a 4D vector; depending on the Dimensions property. The output number ranges between zero and one.

## Inputs

The inputs are dynamic, they become available if needed depending on the node properties.

**Vector**

Vector used as seed in 2D, 3D, and 4D dimensions.
**W**

Value used as seed in 1D and 4D dimensions.

## Properties

**Dimensions**

The dimensions of the space to evaluate the noise in.

**1D:**

The W input is used as seed.
**2D:**

The X and Y components of the Vector input are used as seed.
**3D:**

The Vector input is used as seed.
**4D:**

Both the Vector input and the W input are used as seed.

## Outputs

**Value**

Output random value.
**Color**

Output random color.

## Notes

The slightest difference in seed values would result in completely different outputs. Consequently, bad precision may have significant impact on the output. Usually, we can mitigate this issue by:
-
Eliminating the problematic seed value. If the problematic seed value is constant, it should be eliminated by choosing a lower dimension or multiplying it by zero.
-
Adding an arbitrary value to the seed. The issue might only happen at certain boundaries, like unit boundaries, so simply adding an arbitrary value might solve the issue.
-
Taking the absolute value of the seed. In computing, zero may be positive or negative, so taking the absolute values unifies the zero into a single value.

   |
Precision issue due to signed zeros on the Z axis.     |
Mitigating the issue by eliminating the Z axis.      |
Mitigating the issue by adding an arbitrary value.     |
Mitigating the issue by taking the absolute value.

## Examples

Generating cell noise using the Snap vector operation and the White Noise node.
