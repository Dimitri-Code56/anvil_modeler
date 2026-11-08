---
titulo: Edge Split Modifier
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/edge_split.html
---

# Edge Split Modifier

The Edge Split modifier splits, duplicates edges within a mesh, breaking ‘links’ between faces around those split edges.
The edges to split can be determined from the edge angle (i.e. angle between faces forming that edge), and/or edges marked as Sharp.
Splitting an edge affects vertex normal generation at that edge, making the edge appear sharp. It can also be used for manual control of the smoothing process, where the user defines which edges should appear smooth or sharp (see Mesh Smoothing for other ways to do this). If desired, both modes can be active at once.

Note
This modifier is kept mostly for historical/compatibility reasons. Everything it can do in shading, and much more, can now be achieved using custom normals.
Unless you really need the topology changes it generates, it is not advised to use it in new projects.

Note
Splitting edges can also be performed manually in Edit Mode.

## Options

The Edge Split modifier.

**Edge Angle**

When enabled, an edge will be split if the angle between its two adjacent faces is greater than the Split Angle.

**Split Angle**

On 0: all edges are split. On 180: no edges are split.
**Sharp Edges**

When enabled, edges will be split if they were marked as sharp.

Note
Non-manifold edges will always be split.

## Examples

   |
Flat shading.     |
Smooth shading.      |
Smooth shading with Edge Split.     |
Smooth shading with Edge Split and Subdivision Surface.
