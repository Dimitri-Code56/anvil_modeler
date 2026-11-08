---
titulo: Brightness/Contrast Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/color/bright_contrast.html
---

# Brightness/Contrast Node

## Inputs

**Image**

Standard color input.
**Brightness**

An additive-type factor by which to increase the overall brightness of the image. Use a negative number to darken an image.
**Contrast**

A scaling type factor by which to make brighter pixels brighter, but keeping the darker pixels dark. Higher values make details stand out. Use a negative number to decrease the overall contrast in the image.

## Outputs

**Image**

Standard color output.

## Notes

It is possible that this node will put out a value set that has values beyond the normal range, i.e. values greater than one and less than zero. If you will be using the output to mix with other images in the normal range, you should clamp the values using the Map Value node (with the Min and Max enabled), or put through a Color Ramp node (with all normal defaults).
Clamp the values to normal range.
Either of these nodes will scale the values back to normal range. In the example image, we want to intensify the specular pass. The bottom thread shows what happens if we do not clamp the values; the specular pass has a value much less than one in the dark areas; when added to the medium gray, it makes black. Passing the brightened image through either the Map Value or the Color Ramp node produces the desired effect.

## Example

A basic example.
