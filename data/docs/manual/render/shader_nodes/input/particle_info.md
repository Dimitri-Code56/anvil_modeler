---
titulo: Particle Info Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/particle_info.html
---

# Particle Info Node

Cycles Only
The Particle Info node can be used in the material node tree for objects that are used as the instancing objects, when you use Object or Collection Render mode of a particle system.
This node gives access to the data of the particle that spawned the object instance. It can be useful to give some variation to a single material assigned to multiple instances of instancing object.

Note
This node currently only supports parent particles. Info from child particles is not available.

## Inputs

This node has no inputs.

## Properties

This node has no properties.

## Outputs

**Index**

Index number of the particle (from 0 to number of particles).
**Random**

A random per-particle value in the range from 0 to 1. It can for example be used in combination with a color ramp, to randomize the particle color.
**Age**

Age of the particle in frames.
**Lifetime**

Total lifespan of the particle in frames.
**Location**

Location of the particle.
**Size**

Size of the particle.
**Velocity**

Velocity of the particle.
**Angular Velocity**

Angular velocity of the particle.
