---
titulo: Wireframe Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/wireframe.html
---

# Wireframe Node

The Wireframe node is used to retrieve the edges of an object as it appears to Cycles. As meshes are triangulated before being processed by Cycles, topology will always appear triangulated when viewed with the Wireframe node.

## Inputs

This node has no inputs.

## Properties

**Pixel Size**

When enabled, the size of edge lines is set in screen space.
**Size**

Thickness of the edge lines.

## Outputs

**Factor**

Black-and-white mask showing white lines representing edges according to the object’s Topology.

## Examples

Using the Wireframe node to showcase the topology of a mesh.
