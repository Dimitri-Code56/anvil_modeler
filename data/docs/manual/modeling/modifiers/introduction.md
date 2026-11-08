---
titulo: Introduction
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/modeling/modifiers/introduction.html
---

# Introduction

Modifiers are automatic operations that affect an object’s geometry in a non-destructive way. With modifiers, you can perform many effects automatically that would otherwise be too tedious to do manually (such as subdivision surfaces) and without affecting the base geometry of your object.
They work by changing how an object is displayed and rendered, but not the geometry which you can edit directly. You can add several modifiers to a single object to form The Modifier Stack and Apply a modifier if you wish to make its changes permanent.
They can be added to the active object using the Add Modifier operator, the “Add Modifier” button at the top of Modifiers tab in the Properties Editor, or using Shift-A in the same tab. New modifiers are always added at the bottom of the stack (i.e. will be applied last).
There are many built-in modifiers but Blender also allows users to make their own modifiers through Geometry Nodes.

## Categories

There are four categories of built-in modifiers:

**Edit**

Similar to the Deform modifiers (see below), however, they usually do not directly affect the geometry of the object, but some other data, such as vertex groups.
**Generate**

Constructive/destructive modifiers that will affect the whole Topology of the mesh. They can change the general appearance of the object, or add new geometry to it…
**Deform**

Unlike Generate ones above, these modifiers only change the shape of an object, without altering its topology.
**Simulate**

Represent physics simulations. In most cases, they are automatically added to the modifiers stack whenever a Particle System or Physics simulation is enabled. Their only role is to define the position in the modifier stack from which is taken the base data for the simulation they represent. As such, they typically have no properties, and are controlled by settings exposed in separate sections of the Properties Editor.
You will also notice a category called “Hair”, this category comes from a bundled Asset Library that is distributed with Blender. See Hair Nodes for more information.
Users can make their own categories by making geometry node groups assets and assigning them to a Asset Catalog. This catalog name will be the category name. If a user creates a catalog with the same name as one of the built-in categories the node group will be added to the bottom of the corresponding menu.
Node Groups that are non-assets or that do not belong to a category will be available in the “Unassigned” sub-menu.

Note
Geometry Node Groups must have the Modifier property enabled for the node group to show up in the Add Modifier menu.

## Interface

Each modifier’s interface shares the same basic components, see Fig. Panel layout (Subdivision Surface as an example)..
Panel layout (Subdivision Surface as an example).
At the top is the panel header. The icons each represent different settings for the modifier (left to right):

** /  Expand**

Collapse modifier to show only the header and not its options.
**Type**

An icon as a quick visual reference of the modifier’s type.

**Name**

Every modifier has a unique name per object. Two modifiers on one object must have unique names, but two modifiers on different objects can have the same name. The default name is based on the modifier type.

** On Cage Meshes**

Depends on the previous setting, if enabled, the modified geometry can also be edited directly, instead of the original one.

Warning
While it shows edited items in their final, modified positions, you are still editing original data.
In situations where the positions diverge it can lead to confusing behavior, so you may wish to disable it in those cases.
It’s also worth noting that some features don’t use the cage positions including:
-
Snap targets, such as snapping to vertex.
-
The transform gizmo uses the original positions.

** Apply On Spline Curves Surfaces Text**

Apply the whole modifier stack up to and including that one on the curve or surface control points, instead of their tessellated geometry.

Note
By default, curves, texts and surfaces are always converted to mesh-like geometry before the modifier stack is evaluated on them.

** Edit Mode**

Display the modified geometry in Edit Mode, as well as the original geometry which you can edit.

** /  Realtime**

Toggle visibility of the modifier’s effect in the 3D Viewport.

** /  Render**

Toggle visibility of the modifier’s effect in the render.

Note
The Square, Triangle and Surface icons may not be available, depending on the type of object and modifier.

**Extras**

**Apply Ctrl-A**

Makes the modifier “real”: converts the object’s geometry to match the applied modifier’s results, and deletes the modifier.
When applying a modifier to an object that shares Object Data between multiple objects, the object must first be made a Single User which can be performed by confirming the pop-up message.
Note, modifiers cannot be applied to Empty object types, use Visual Geometry as Mesh instead.

Warning
Applying a modifier that is not first in the stack will ignore the stack order (it will be applied as if it was the first one), and may produce undesired results.

**Apply as Shape Key**

Stores the result of that modifier in a new relative shape key and then deletes the modifier from the modifier stack. This is only available with modifiers that do not affect the topology (typically, Deform modifiers only).

Note
Even though it should work with any geometry type that supports shape keys, currently it will only work with meshes.
**Save as Shape Key**

Stores the result of that modifier in a new relative shape key and keeps the modifier in the modifier stack. This is only available with modifiers that do not affect the topology (typically, Deform modifiers only).

**Duplicate Shift-D**

Creates a duplicate of the modifier just below current one in the stack.

**Copy to Selected**

Copies the modifier from the Active object to all selected objects.

**Move to First/Last**

Moves the modifier to the first or last position in the modifier stack.

**Pin to Last**

Keeps the modifier at the end of the modifier stack. When a modifier is pinned, a pin icon will be displayed on the right side of the panel’s header.
**Move to Nodes**

Converts the existing Geometry Nodes Modifier node tree to a group node to be reused in other node trees. See Move to Nodes Operator for more information.
This operator is only available for the Geometry Nodes Modifier.

**Delete X, Delete**

Delete the modifier.
** (Move)**

Move the modifier up/down in the stack, changing the evaluation order of the modifiers.
A modifier is not movable if Pin to Last is enabled.
Below this header, all of the options unique to each modifier will be displayed.

Tip
Use Alt to affect all selected objects at once when performing operators such as add, apply, remove, and move to index.
See Multi-Object Editing for more information.

### The Modifier Stack

Modifiers are a series of non-destructive operations which can be applied on top of an object’s geometry. You can apply them in almost any order. This kind of functionality is often referred to as a “modifier stack” and is also found in several other 3D applications.
In a modifier stack, the order in which modifiers are applied has an effect on the result. Therefore the modifiers can be re-arranged by clicking  (grip icon) in the top right, and moving the selected modifier up or down. For example, the image below shows Subdivision Surface and Mirror modifiers that have switched places.

 Modifier Stack example.   |
The Mirror modifier is the last item in the stack and the result looks like two surfaces.     |
The Subdivision Surface modifier is the last item in the stack and the result is a single merged surface.
Modifiers are calculated from top to bottom in the stack. In this example, the desired result (on right) is achieved by first mirroring the object, and then calculating the subdivision surface.

#### Active Modifier

A modifier in the stack can be selected to mark it as Active, the active modifier displays an outline around the modifier’s panel. To set an active modifier, select an area of the modifier’s panel background, the modifier’s icon, or, select a modifier in the Outliner.
The active modifier is used by the Geometry Node Editor to determine which node group is being modified.

## Example

In this example a simple subdivided cube has been transformed into a rather complex object using a stack of modifiers.
Download example file.
