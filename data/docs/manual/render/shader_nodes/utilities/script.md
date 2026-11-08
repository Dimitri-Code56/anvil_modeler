---
titulo: Script Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/utilities/script.html
---

# Script Node

Cycles Only
The Script Node allows you to load and use custom shaders written in Open Shading Language (OSL) within the Cycles renderer. This node acts as a bridge between OSL shader code and the node-based material system in Blender.
Each Script node represents a single OSL shader, with its inputs and outputs defined by the parameters in the shader script. These shaders can be stored directly within the blend-file or referenced externally.
This feature is ideal for technical artists and shader developers who need fine-grained control over shading behavior beyond what the standard shader nodes provide.

Note
The Script node is only evaluated if Open Shading Language is enabled.

Tip
For use in production, we suggest to use a node group to wrap shader script nodes, and link that into other blend-files. This makes it easier to make changes to the node afterwards as sockets are added or removed, without having to update the script nodes in all files.

## Properties

**Mode**

How to link to OSL shaders.

**Internal:**

A text data-block is used to store the OSL shader, and the OSO bytecode is stored in the node itself. This is useful for distributing a blend-file with everything packed into it.

** Script Node Update**

Reloads the text file data-block, creating new inputs and outputs if needed.
**External:**

Used to specify a `.osl` file from a drive, and this will then be automatically compiled into a `.oso` file in the same directory. It is also possible to specify a path to a `.oso` file, which will then be used directly, with compilation done manually by the user. The third option is to specify just the module name, which will be looked up in the shader search path.
The shader search path is located in the same place as the scripts or configuration path, under:
Linux:
```
$HOME/.config/blender/5.2/shaders/
```

Windows:
```
C:\Users\$user\AppData\Roaming\Blender Foundation\Blender\5.2\shaders\
```

macOS:
```
/Users/$USER/Library/Application Support/Blender/5.2/shaders/
```
