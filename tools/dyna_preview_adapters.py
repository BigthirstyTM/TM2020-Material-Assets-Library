"""Texture-backed Dyna previews; no animation inferred from material names.

DispIn operations follow Block_TDSN_COut_DispIn_p variant 03: tangent
refraction, depth/metres-per-UV, roughness attenuation, eight height steps,
and MulInside * SI * (1-BaseColorOp.a). Native texture-array interiors,
lighting probes, display activation, exposure and deferred passes remain
renderer-specific. The existing flattened MulInside image is retained.
"""
from shader_fidelity_adapters import node,wire,math,vec,combine,split,bc5,clear_input,mix

REVISION='2026.11.26-dyna-preview-1'

def parameter(t,name,value):
    n=node(t,'ShaderNodeValue','Dyna source '+name);n.outputs[0].default_value=value
    n.label=name+' (native material)';return n.outputs[0]

def base_material_uv(t):
    t.nodes['UV Map'].uv_map='BaseMaterial'
    t.nodes['Normal Map'].uv_map='BaseMaterial'

def height_uv(t,uv,image,shift):
    def height(coords,index):
        n=node(t,'ShaderNodeTexImage','Dyna SI height sample '+str(index))
        n.image=image;n.interpolation='Linear';wire(t,coords,n.inputs['Vector'])
        return split(t,n.outputs['Color'])[0]
    step=vec(t,'SCALE',shift,.125);coords=uv;level=0.;h=height(coords,0)
    # Fixed eight-step trace, matching the shader's 1/8 increments. Once a
    # crossing is found subsequent nodes preserve that first crossing.
    for i in range(8):
        active=math(t,'LESS_THAN',level,h)
        candidate=vec(t,'ADD',coords,step)
        coords=mix(t,'Dyna SI trace step '+str(i+1),active,coords,candidate)
        level=math(t,'ADD',level,math(t,'MULTIPLY',active,.125))
        h=height(coords,i+1)
    before=vec(t,'SUBTRACT',coords,step)
    hb=height(before,'previous')
    after_delta=math(t,'SUBTRACT',h,level)
    before_delta=math(t,'SUBTRACT',hb,math(t,'SUBTRACT',level,.125))
    denom=math(t,'SUBTRACT',after_delta,before_delta)
    fraction=math(t,'DIVIDE',after_delta,denom)
    result=vec(t,'SUBTRACT',coords,vec(t,'SCALE',step,fraction))
    # At zero height no trace occurs; avoid extrapolating behind the surface.
    return mix(t,'Dyna SI first crossing',math(t,'GREATER_THAN',level,0),uv,result)

def source_si_uv(t,uv,rough_colour,normal_colour,height_image,values):
    geo=node(t,'ShaderNodeNewGeometry','Dyna view direction')
    tangent=node(t,'ShaderNodeTangent','Dyna BaseMaterial tangent');tangent.direction_type='UV_MAP';tangent.uv_map='BaseMaterial'
    bitangent=vec(t,'CROSS_PRODUCT',geo.outputs['Normal'],tangent.outputs['Tangent'])
    incident=vec(t,'SCALE',geo.outputs['Incoming'],-1)
    v=combine(t,vec(t,'DOT_PRODUCT',incident,tangent.outputs['Tangent']),
      vec(t,'DOT_PRODUCT',incident,bitangent),vec(t,'DOT_PRODUCT',incident,geo.outputs['Normal']))
    n=bc5(t,normal_colour);dot=vec(t,'DOT_PRODUCT',n,v)
    eta=parameter(t,'RefractIndex',values['RefractIndex'][0])
    double=parameter(t,'DoubleRefract',values['DoubleRefract'][0])
    k=math(t,'SUBTRACT',1,math(t,'MULTIPLY',math(t,'MULTIPLY',eta,eta),
      math(t,'SUBTRACT',1,math(t,'MULTIPLY',dot,dot))))
    root=math(t,'SQRT',math(t,'MAXIMUM',k,0))
    refracted=vec(t,'SUBTRACT',vec(t,'SCALE',v,eta),vec(t,'SCALE',n,math(t,'ADD',math(t,'MULTIPLY',eta,dot),root)))
    refracted=vec(t,'SCALE',refracted,math(t,'GREATER_THAN',k,-.0000001))
    rx,ry,rz=split(t,refracted)
    exit_k=math(t,'SUBTRACT',1,math(t,'DIVIDE',math(t,'SUBTRACT',1,math(t,'MULTIPLY',rz,rz)),math(t,'MULTIPLY',eta,eta)))
    exit_scale=math(t,'DIVIDE',math(t,'GREATER_THAN',exit_k,-.0000001),eta)
    use_double=math(t,'GREATER_THAN',double,.5)
    exit_direction=mix(t,'Dyna parallel-interface exit',use_double,refracted,vec(t,'SCALE',refracted,exit_scale))
    ex,ey,_=split(t,exit_direction)
    rough=split(t,rough_colour)[0]
    attenuation=math(t,'SUBTRACT',1,math(t,'POWER',rough,4))
    depth=parameter(t,'Meters_Depth',values['Meters_Depth'][0])
    mx=parameter(t,'Meters_UV X',values['Meters_UV'][0]);my=parameter(t,'Meters_UV Y',values['Meters_UV'][1])
    shift=combine(t,math(t,'MULTIPLY',ex,math(t,'DIVIDE',depth,mx)),math(t,'MULTIPLY',ey,math(t,'DIVIDE',depth,my)),0)
    shift=vec(t,'SCALE',shift,attenuation)
    return height_uv(t,uv,height_image,shift)

def dispin(m,values):
    t=m.node_tree;p=t.nodes['Principled BSDF'];base_material_uv(t);uv=t.nodes['UV Map'].outputs['UV']
    d=t.nodes['tex_D'];r=t.nodes['tex_R'];normal=t.nodes['tex_N']
    # Historical node names are swapped: tex_I is MulInside, tex_L is SI.
    inside=t.nodes['tex_I'];si=t.nodes['tex_L'];height=t.nodes['tex_H']
    assert 'WarpLight' in si.image.name and 'WarpLight' in inside.image.name
    shifted=source_si_uv(t,d.inputs['Vector'].links[0].from_socket,r.outputs['Color'],normal.outputs['Color'],height.image,values)
    wire(t,shifted,si.inputs['Vector']);wire(t,uv,inside.inputs['Vector'])
    interior=vec(t,'SCALE',inside.outputs['Color'],inside.outputs['Alpha'])
    emission=vec(t,'MULTIPLY',interior,si.outputs['Color'])
    emission=vec(t,'SCALE',emission,math(t,'SUBTRACT',1,d.outputs['Alpha']))
    wire(t,emission,p.inputs['Emission Color'])
    wire(t,parameter(t,'SelfIllum_Scale',values['SelfIllum_Scale'][0]),p.inputs['Emission Strength'])
    # BaseColorOp.a masks surface reflection and the emissive interior; this
    # is an opaque composite, not object transparency.
    base=p.inputs['Base Color'].links[0].from_socket
    wire(t,vec(t,'SCALE',base,d.outputs['Alpha']),p.inputs['Base Color'])
    clear_input(t,p.inputs['Alpha'],1)
    m['tm_dyna_preview_limit']='Flattened single MulInside layer; engine lightmaps/probes, texture-array room projection and exposure are not reproduced.'
    return dict(material=m.name,operation='Native SI height trace and opaque interior multiplication',height_steps=8,parameters=values)

def selfillum(m):
    t=m.node_tree;p=t.nodes['Principled BSDF']
    base_material_uv(t)
    wire(t,t.nodes['UV Map'].outputs['UV'],t.nodes['tex_I'].inputs['Vector'])
    clear_input(t,p.inputs['Alpha'],1)
    m['tm_dyna_preview_limit']='Native SI scale 2.5 retained; engine prelight, display/night factors and exposure are scene approximations.'
    return dict(material=m.name,operation='Use BaseMaterial UV for SI; opaque native render state; preserve SI scale 2.5')

def emission_uv(m):
    t=m.node_tree
    base_material_uv(t)
    wire(t,t.nodes['UV Map'].outputs['UV'],t.nodes['tex_I'].inputs['Vector'])
    return dict(material=m.name,operation='Use explicit BaseMaterial UV for SelfIllum; retain native emission scale 20')
