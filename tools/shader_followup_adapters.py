"""Source-informed UV, grass, SI-depth, array and optional Hue adapters."""
from pathlib import Path
import json
from material_preview_adapters import node,wire,vec,combine,math
from shader_fidelity_adapters import sample,split,interface,mix
from deco_ice_adapters import transform,hue
from dyna_preview_adapters import source_si_uv

REVISION='2026.11.26-shader-followup-1'

def uv_contract(m):
    changes=[];t=m.node_tree
    for n in t.nodes:
        if n.type in ['UVMAP','NORMAL_MAP'] and not n.uv_map:
            n.uv_map='BaseMaterial';changes.append(n.name)
    # Explicitly connect file samplers that otherwise fall back to active UVs.
    # Generated/projected inputs already have a Vector link and are untouched.
    for n in t.nodes:
        if n.type=='TEX_IMAGE' and n.image and not n.inputs['Vector'].is_linked:
            uv=node(t,'ShaderNodeUVMap','Source BaseMaterial sampler UV');uv.uv_map='BaseMaterial'
            wire(t,uv.outputs[0],n.inputs['Vector']);changes.append(n.name+':Vector')
    return changes

def grass(m,r,images):
    t=m.node_tree;p=t.nodes['Principled BSDF'];geo=node(t,'ShaderNodeNewGeometry','Native GrassX2 world projection')
    x,y,_=split(t,geo.outputs['Position'])
    uv=transform(t,combine(t,x,y),r['slots']['GrassX2'])
    tx=sample(t,'Native GrassX2 modulation',images('GrassX2'),uv)
    original=p.inputs['Base Color'].links[0].from_socket
    wire(t,vec(t,'MULTIPLY',original,vec(t,'SCALE',tx.outputs[0],2)),p.inputs['Base Color'])
    return dict(role='GrassX2',scale=r['slots']['GrassX2']['scale'],rotation=r['slots']['GrassX2']['rotation'],translation=r['slots']['GrassX2']['translation'])

def depth(m,r):
    t=m.node_tree;d=t.nodes['tex_D'];normal=t.nodes['tex_N'];rough=t.nodes['tex_R'];height=t.nodes['tex_H'];si=t.nodes['tex_L']
    assert all(n.image for n in [d,normal,rough,si]),m.name
    if not height.image:
        assert not r['slots'].get('Height',{}).get('resource'),r['name']
        # Explicit null native height binding: do not invent a height image.
        wire(t,d.inputs['Vector'].links[0].from_socket,si.inputs['Vector'])
        return dict(mode='Native null height: no invented relief',parameters=r['parameters'])
    # Keep MulInside framing, atlas/frame selection, hue and emission composition.
    # Only the SI sampler's former generic parallax coordinates are replaced.
    uv=d.inputs['Vector'].links[0].from_socket
    coords=source_si_uv(t,uv,rough.outputs[0],normal.outputs[0],height.image,r['parameters'])
    wire(t,coords,si.inputs['Vector'])
    return {k:r['parameters'][k] for k in ['Meters_Depth','Meters_UV','RefractIndex','DoubleRefract']}

def _mask(t,base,mask_image,uv,enabled,target):
    destinations=[l.to_socket for l in base.outputs['Color'].links]
    mask=sample(t,'Source colour mask - '+base.name,mask_image,uv)
    result=mix(t,'Source optional masked Hue - '+base.name,
      math(t,'MULTIPLY',enabled,mask.outputs['Alpha']),base.outputs['Color'],hue(t,mask.outputs[0],target))
    for socket in destinations:wire(t,result,socket)

def colour_masks(bpy,m,r,images):
    t=m.node_tree;p=t.nodes['Principled BSDF'];roles=[]
    for role,desc in r['slots'].items():
        if 'HueMask' not in role or not desc.get('image'):continue
        base_role=role.replace('HueMask','');base=r['slots'].get(base_role,{})
        if base.get('image'):roles.append((role,Path(base['image'].replace('\\','/')).name.lower()))
    root=p.inputs['Base Color'].links[0].from_node
    if root.type=='GROUP':
        original=root.node_tree;g=original.copy();root.node_tree=g
        control=g.interface.new_socket(name='Enable source colour preview',in_out='INPUT',socket_type='NodeSocketFloat');control.default_value=0;control.min_value=0;control.max_value=1
        target=g.interface.new_socket(name='Explicit preview colour',in_out='INPUT',socket_type='NodeSocketColor');target.default_value=(1,1,1,1)
        inp=next(n for n in g.nodes if n.type=='GROUP_INPUT')
        enabled=inp.outputs[control.name];colour=inp.outputs[target.name]
        root.inputs[control.name].default_value=0;root.inputs[target.name].default_value=(1,1,1,1)
        work=g
    else:
        enabled_node=node(t,'ShaderNodeValue','Enable source colour preview');enabled_node.outputs[0].default_value=0
        colour_node=node(t,'ShaderNodeRGB','Explicit preview colour');colour_node.outputs[0].default_value=(1,1,1,1)
        enabled=enabled_node.outputs[0];colour=colour_node.outputs[0];work=t
    installed=[];seen=set()
    for role,filename in roles:
        for n in list(work.nodes):
            if n.type!='TEX_IMAGE' or not n.image:continue
            if Path(n.image.filepath.replace('\\','/')).name.lower()!=filename:continue
            if not n.outputs['Color'].is_linked:continue
            if n.name in seen:continue
            # Projected groups name their separate native roles explicitly.
            base_role=role.replace('HueMask','')
            if work!=t and n.name.startswith('Native ') and not n.name.startswith('Native '+base_role):continue
            uv=n.inputs['Vector'].links[0].from_socket if n.inputs['Vector'].is_linked else None
            if uv is None:
                u=node(work,'ShaderNodeUVMap','Mask BaseMaterial UV');u.uv_map='BaseMaterial';uv=u.outputs[0]
            _mask(work,n,images(role),uv,enabled,colour);installed.append(dict(role=role,node=n.name));seen.add(n.name)
    assert installed,('No source colour samples found',m.name,roles)
    m['tm_colour_preview_limit']='Recovered mask-alpha/chroma formula. Disabled by default; explicit white preview target is user input, not a decoded game palette. Native target selectors retained separately.'
    return installed
