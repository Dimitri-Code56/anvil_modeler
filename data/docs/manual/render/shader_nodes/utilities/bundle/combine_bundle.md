---
titulo: Combine Bundle Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/utilities/bundle/combine_bundle.html
---

# Combine Bundle Node

The Combine Bundle node creates a new Bundle from multiple input values. Each input becomes an element of the bundle, identified by its socket name. Values can be accessed in other parts of the node tree using the Separate Bundle

## Inputs

The node can contain an arbitrary number of input sockets. Each socket can be given a custom name and type. Supported types include (but not limited to):
-
Geometry
-
Objects
-
Values (e.g. float, integer, boolean, vector, color)
-
Fields
-
Nested Bundles

## Properties

Properties are available in the Node tab of the Sidebar.

**Sync Sockets**

Updates the current node to match the socket signature of the connected nodes. Use this after renaming, adding, or removing sockets.
**Define Signature**

Locks the current item list and types to stabilize interfaces when publishing node groups. When enabled, adding/removing items is disabled until the option is turned off.

### Bundle Items

**List of bundle items**

Displays one entry per element in the bundle. Double-click to rename.

**Add Item**

Add a new socket to the bundle.
**Remove Item**

Delete the selected socket.
**Type**

The data type for the selected item (e.g. Float, Vector, Geometry, Object, Bundle). For value types, a default value control is shown and used when the socket is unlinked.

## Outputs

**Bundle**

The resulting bundle containing all defined inputs.
