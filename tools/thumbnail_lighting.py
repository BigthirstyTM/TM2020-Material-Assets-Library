"""Thumbnail-only Cycles compositing; production material shaders stay intact."""
import bpy

def without_studio_reflections(scene):
    layer=scene.view_layers[0]
    layer.use_pass_glossy_direct=True
    layer.use_pass_glossy_color=True
    layer.cycles.denoising_store_passes=True
    scene.cycles.use_denoising=False
    tree=bpy.data.node_groups.new('Thumbnail studio highlight removal','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    scene.compositing_node_group=tree
    nodes=tree.nodes;links=tree.links
    render=nodes.new('CompositorNodeRLayers');render.scene=scene
    multiply=nodes.new('ShaderNodeMix');multiply.data_type='RGBA';multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    links.new(render.outputs['Glossy Direct'],multiply.inputs[6]);links.new(render.outputs['Glossy Color'],multiply.inputs[7])
    subtract=nodes.new('ShaderNodeMix');subtract.data_type='RGBA';subtract.blend_type='SUBTRACT';subtract.inputs[0].default_value=1
    links.new(render.outputs['Image'],subtract.inputs[6]);links.new(multiply.outputs[2],subtract.inputs[7])
    denoise=nodes.new('CompositorNodeDenoise');links.new(subtract.outputs[2],denoise.inputs['Image'])
    for role in ['Normal','Albedo']:
        links.new(render.outputs['Denoising '+role],denoise.inputs[role])
    output=nodes.new('NodeGroupOutput');links.new(denoise.outputs['Image'],output.inputs['Image'])
    return tree
