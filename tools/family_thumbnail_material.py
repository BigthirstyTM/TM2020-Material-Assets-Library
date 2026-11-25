"""Disposable thumbnail shader copies: never change the asset's production graph."""
import json
import bpy
import numpy as np


def preview_copy(material,flat=True,zoom=1,native_emission=False):
    copy=material.copy();copy.asset_clear();copy.name='Thumbnail only - '+material.name
    groups=[];trees={};fixture={};clock=json.loads(material.get('tm_v7g_preview_fixture','{}')).get('fixture_clock')
    animation=json.loads(material.get('tm_v7d_preview_detail','{}'))
    states={r['node']:r['frame'] for r in animation.get('manual_frames',[])}
    if clock:
        states={n.name:clock['frame'] for n in material.node_tree.nodes if n.type=='GROUP' and n.inputs.get('Manual Frame (-1 = timeline)')}
        period=clock['period'];label=f'{period:g} s' if period<60 else f'{period/60:g} min' if period<3600 else f'{period/3600:g} h'
        fixture.update(clock=clock,label='STEP '+label.upper())
    elif states:
        fixture.update(animation_frames=states,label='LAST FRAME' if 'ItemObstacle' in material.name else '')
    def duplicate(tree):
        for node in list(tree.nodes):
            if node.type=='GROUP' and node.node_tree:
                original=node.node_tree
                if original not in trees:
                    clone=original.copy();clone.asset_clear();trees[original]=clone;groups.append(clone);duplicate(clone)
                node.node_tree=trees[original]
            if node.name in states and node.inputs.get('Manual Frame (-1 = timeline)'):
                socket=node.inputs['Manual Frame (-1 = timeline)']
                for link in list(socket.links):tree.links.remove(link)
                socket.default_value=states[node.name]
            if zoom!=1:
                outputs=[]
                if node.type=='TEX_COORD':outputs=[node.outputs[k] for k in ['UV','Generated','Object']]
                elif node.type=='UVMAP':outputs=[node.outputs['UV']]
                elif node.type=='NEW_GEOMETRY':outputs=[node.outputs['Position']]
                for output in outputs:
                    links=list(output.links)
                    if not links:continue
                    scale=tree.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=zoom;tree.links.new(output,scale.inputs[0]);target=scale.outputs[0]
                    if node.type=='UVMAP' or (node.type=='TEX_COORD' and output.name in ['UV','Generated']):
                        add=tree.nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=((1-zoom)/2,)*3;tree.links.new(target,add.inputs[0]);target=add.outputs[0]
                    for link in links:tree.links.new(target,link.to_socket)
            if not flat:continue
            if node.type in ['BSDF_PRINCIPLED','BSDF_DIFFUSE','BSDF_GLOSSY','BSDF_ANISOTROPIC','BSDF_GLASS','BSDF_REFRACTION']:
                color=node.inputs.get('Base Color') or node.inputs.get('Color');emission=tree.nodes.new('ShaderNodeEmission')
                def wire(src,dst):
                    if src.is_linked:tree.links.new(src.links[0].from_socket,dst)
                    else:dst.default_value=src.default_value
                wire(color,emission.inputs['Color']);surface=emission.outputs[0]
                if node.type=='BSDF_PRINCIPLED':
                    emitted=node.inputs['Emission Color'];strength=node.inputs['Emission Strength']
                    active=strength.is_linked or strength.default_value>0
                    if active:
                        # Display emissive design without camera-exposure bloom or
                        # the native luminance multiplier obliterating its colors.
                        if not color.is_linked and emitted.is_linked:
                            wire(emitted,emission.inputs['Color'])
                        else:
                            mix=tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='LIGHTEN';mix.inputs[0].default_value=1
                            wire(color,mix.inputs[1]);wire(emitted,mix.inputs[2])
                            if states or native_emission:
                                scale=tree.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=min(30,max(1,strength.default_value))
                                if emitted.is_linked:tree.links.new(emitted.links[0].from_socket,scale.inputs[0])
                                else:scale.inputs[0].default_value=emitted.default_value[:3]
                                tree.links.new(scale.outputs[0],mix.inputs[2]);fixture['emission_gain']=scale.inputs[3].default_value
                            tree.links.new(mix.outputs[0],emission.inputs['Color'])
                    alpha=node.inputs['Alpha']
                    if alpha.is_linked or alpha.default_value<1:
                        transparent=tree.nodes.new('ShaderNodeBsdfTransparent');mix=tree.nodes.new('ShaderNodeMixShader');wire(alpha,mix.inputs[0]);tree.links.new(transparent.outputs[0],mix.inputs[1]);tree.links.new(surface,mix.inputs[2]);surface=mix.outputs[0]
                for output in node.outputs:
                    if output.type=='SHADER':
                        for link in list(output.links):tree.links.new(surface,link.to_socket)
                tree.nodes.remove(node)
            elif node.type=='EMISSION':
                for link in list(node.inputs['Strength'].links):tree.links.remove(link)
                node.inputs['Strength'].default_value=1
    duplicate(copy.node_tree)
    return copy,groups,fixture

# Compact, deterministic footer alphabet. No external font or renderer dependency.
FONT={
 '0':['01110','10001','10011','10101','11001','10001','01110'],
 '1':['00100','01100','00100','00100','00100','00100','01110'],
 '2':['01110','10001','00001','00010','00100','01000','11111'],
 '3':['11110','00001','00001','01110','00001','00001','11110'],
 '4':['00010','00110','01010','10010','11111','00010','00010'],
 '5':['11111','10000','10000','11110','00001','00001','11110'],
 '6':['01110','10000','10000','11110','10001','10001','01110'],
 '7':['11111','00001','00010','00100','01000','01000','01000'],
 '8':['01110','10001','10001','01110','10001','10001','01110'],
 '9':['01110','10001','10001','01111','00001','00001','01110'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'P':['11110','10001','10001','11110','10000','10000','10000'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'I':['01110','00100','00100','00100','00100','00100','01110'],
 'N':['10001','11001','10101','10011','10001','10001','10001'],
 'H':['10001','10001','10001','11111','10001','10001','10001'],
 'L':['10000','10000','10000','10000','10000','10000','11111'],
 'A':['01110','10001','10001','11111','10001','10001','10001'],
 'F':['11111','10000','10000','11110','10000','10000','10000'],
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 '.':['00000','00000','00000','00000','00000','00110','00110'],
 ' ':['00000']*7,
}

def add_footer(rgba,text):
    scale=3 if len(text)<=13 else 2;width=len(text)*6*scale-scale
    rgba[226:256]=[26,30,34,255];left=(256-width)//2
    for i,char in enumerate(text):
        bits=np.array([[c=='1' for c in row] for row in FONT[char]],dtype=bool)
        bits=np.repeat(np.repeat(bits,scale,0),scale,1);y=230 if scale==3 else 234;x=left+i*6*scale
        block=rgba[y:y+bits.shape[0],x:x+bits.shape[1]];block[bits]=[235,239,243,255]
