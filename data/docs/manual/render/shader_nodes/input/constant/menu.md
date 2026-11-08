---
titulo: Menu Node
fonte: manual
versao_blender: 5.2
url: https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/constant/menu.html
---

# Menu Node

The Menu node outputs a menu value that can be used to control nodes that support menu sockets.
The available menu items are determined by the socket the node is connected to. When connected to a node with a predefined menu, the Menu node exposes the same list of options. Custom menus can also be created with the Menu Switch Node node and then used as the source for this node.

## Outputs

**Menu**

The selected menu value.
The available options are defined by the connected menu socket.
