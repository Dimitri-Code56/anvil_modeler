---
titulo: RGB Curves Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/color/rgb_curves.html
---

# RGB Curves Node

The RGB Curves Node performs level adjustments on each color channel.

## Inputs

**Image/Color**

Standard color input.
**Factor**

Controls the amount of influence the node exerts on the image.
**Black Level Compositor Only**

Defines the input color that should be mapped to black.
**White Level Compositor Only**

Defines the input color that should be mapped to white.

Tip
To define the black and white levels, use the eyedropper to select a color sample of a displayed image.

## Properties

**Tone Compositor Only**

**Standard:**

The Combined curve is applied to each channel individually, which may result in a change of hue.
**Filmlike:**

Keeps the hue constant.
**Channel**

The curve to show.

**C:**

Combined
**R:**

Red
**G:**

Green
**B:**

Blue
**Curve**

A Bézier curve that maps each input level (X axis) to an output level (Y axis). For the curve controls, see Curve widget.

## Outputs

**Image/Color**

Standard color output.

## Examples

Below are some common curves you can use to achieve desired effects.
From left to right: 1. Lighten shadows 2. Negative 3. Decrease contrast 4. Posterize.

### Color Correction using Curves

Color correction with curves.
In this example, the image has too much red in it, so we run it through an RGB Curves node and reduce the Red channel.
The documentation for the Mix Color Node has an additional example about fixing overexposure.

### Color Correction using Black/White Levels

Color correction with Black/White Levels.
Manually adjusting the RGB curves for color correction can be difficult. Another option for color correction is to use the Black and White Levels instead, which really might be their main purpose.
In this example, the White Level is set to the color of a bright spot of the sand in the background, and the Black Level to the color in the center of the fish’s eye. To do this efficiently it is best to bring up the Image Editor showing the original input image. You can then use the levels’ color picker to easily choose the appropriate colors from the input image, zooming into pixel level if necessary. The result can be fine-tuned with the R, G, and B curves like in the previous example.
The curve for C is used to compensate for the increased contrast that is a side effect of setting Black and White Levels.

### Effects

Changing colors by inverting the red channel.
