---
titulo: Volume to Mesh Modifier
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/volume_to_mesh.html
---

# Volume to Mesh Modifier

This modifier is the inverse of the Mesh to Volume modifier. It takes an existing volume object and converts one of its grids to a mesh. Only scalar grids (such as the density grid) can be converted.

Tip
To copy and move the generated mesh separately from the volume object, use a collection instance.

## Options

The Volume to Mesh modifier.

**Object**

The source volume object.
**Grid Name**

The name of the grid that will be converted. This has to be a scalar grid.
**Resolution Mode**

Mode for how the resolution of the final mesh is controlled.

**Grid**

This makes the resolution dependent on the resolution of the grid that is converted. Higher resolution grids result in a higher resolution mesh. In many cases, that is the most efficient mode.
**Voxel Amount**

Specifies the approximate resolution of the final mesh. The voxel size is adapted to the size of the entire volume.
**Voxel Size**

Use a fixed resolution that does not change when the volume changes.
**Threshold**

Voxels with a larger value are considered to be inside the mesh and all other voxels outside. The mesh will be generated on the boundary of inside and outside voxels. This is sometimes also called the “iso value”.
**Adaptivity**

This is similar to decimating the final to reduce resolution where it is not needed.
**Smooth Shading**

Enables smooth shading on the generated mesh.

## Example

Converting a cloud-shaped volume to a mesh.
