---
titulo: Geometry Nodes Modifier
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/geometry_nodes.html
---

# Geometry Nodes Modifier

The Geometry Nodes modifier creates a modifier with a node group which defines its functionality.
A new Geometry Nodes modifier with a new node group.
This modifier is supported by mesh, curve, text, and volume objects.

## Options

**Node Group**

A Node Group with the geometry input and output. Those are respectively what is received and passed to the previous and next modifier in the stack. See Nodes for all available nodes.
**Inputs**

A list of the node group’s inputs which can have unique values even if the group is shared among multiple modifiers.
If the input is connected to a Field socket, there will be a toggle to switch between using a single value for the input or using an attribute on the input geometry. Using an attribute for input means the value can be different for every element.
The attribute name used by default when using the node group in a modifier for the first time is defined in the node group inputs panel.

Note
The attribute domain and the data type used to access the attribute is defined by the node the input is connected to.

### Warnings

Nodes that show a warning message in the node editor will also show that message here.
Custom warning messages can be created using the Warning Node.

### Output Attributes

By connecting a field socket to the group output node, you can create custom Attributes from a Field output of any node in the node tree. The domain of the attribute must be specified in the group node’s output properties. Note, this does not work with Instanced Data.
The attribute name used by default when using the node group in a modifier for the first time is defined in the node group outputs panel.
This panel is hidden unless the output node has attribute sockets.

### Manage

Displays options for managing data within the node group,
The Manage panel can be hidden by disabling Show Manage Panel in the modifier’s header options. This controls whether the panel is shown for that specific modifier.
To disable the panel by default for new modifiers created from a node group asset, toggle Show Manage Panel Geometry Nodes in the node group’s properties.

#### Bake

**Bake Target**

Specifies where baked data should be stored. This can be overridden for individual bakes.

**Packed:**

The baked data is packed into the .blend file. So no separate file is necessary.
**Disk:**

The baked data is stored in a separate directory on disk.

**Bake Path**

Location on disk where the baked data for Simulation Zones and Bake Nodes are stored.

See also
Geometry Node Baking

#### Named Attributes

This panel displays information about all custom named attributes used by the node group. More information is available in the geometry nodes inspection page.

## Move to Nodes Operator

Creates a new geometry node tree with the name of the current node tree with `.wrapper` appended to the name. This operation moves all inputs and outputs from the old modifier into a new node group. In order for this operator to function, there must be a Group Input and a Group Output each with a Geometry socket attached to the node group. This action causes all Output Attributes to become Internal Dependencies utilizing the Store Named Attribute Node. All modifier “inputs” will then also become inputs of the newly created node group.
This operator is useful to easily allow a node tree to be reused in other trees or to mark it as an Asset to be reused in other projects.
