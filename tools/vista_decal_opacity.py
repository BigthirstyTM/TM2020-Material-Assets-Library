"""Native TOpacity contract: red channel times mesh vertex alpha, not bitmap alpha."""
from material_preview_adapters import node, wire, math


def connect_opacity(material, texture, vertex_alpha):
    tree = material.node_tree
    channels = node(tree, 'ShaderNodeSeparateColor', 'Native TOpacity red channel')
    channels.mode = 'RGB'
    wire(tree, texture.outputs['Color'], channels.inputs['Color'])
    # Blender returns zero for a missing Color attribute. Native item vertices
    # have an alpha value; use opaque vertices by default on ordinary Blender
    # meshes, with an explicit switch for authored Color attributes.
    painted = node(tree, 'ShaderNodeValue', 'Use Color vertex alpha for decal opacity')
    painted.outputs[0].default_value = 0
    vertex = math(tree, 'ADD', math(tree, 'SUBTRACT', 1, painted.outputs[0]),
                  math(tree, 'MULTIPLY', painted.outputs[0], vertex_alpha))
    opacity = math(tree, 'MULTIPLY', channels.outputs['Red'], vertex,
                   name='Native decal opacity times vertex alpha')
    wire(tree, opacity, tree.nodes['Principled BSDF'].inputs['Alpha'])
