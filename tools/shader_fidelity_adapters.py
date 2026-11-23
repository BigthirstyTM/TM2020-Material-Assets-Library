"""Source-informed renderer adapters. Native export contracts stay untouched."""
import math as pymath
from pathlib import Path
from material_preview_adapters import node,wire,math,vec,combine,setup_transparency

REVISION='2026.11.23-shader-fidelity-1'

def mix(t,name,factor,a,b):
    n=node(t,'ShaderNodeMixRGB',name)
    for s,v in zip(n.inputs,[factor,a,b]):wire(t,v,s)
    return n.outputs[0]

def scalar_mix(t,f,a,b):
    return math(t,'ADD',a,math(t,'MULTIPLY',f,math(t,'SUBTRACT',b,a)))

def clear_input(t,s,value):
    for l in list(s.links):t.links.remove(l)
    s.default_value=value

def clock(t,name):
    n=node(t,'ShaderNodeValue',name)
    d=n.outputs[0].driver_add('default_value').driver
    d.expression='(frame-1)*fps_base/max(fps,1)'
    for key,path in [('fps','render.fps'),('fps_base','render.fps_base')]:
        v=d.variables.new();v.name=key;v.type='CONTEXT_PROP'
        v.targets[0].context_property='ACTIVE_SCENE';v.targets[0].data_path=path
    return n.outputs[0]

def split(t,s):
    n=node(t,'ShaderNodeSeparateXYZ','Components');wire(t,s,n.inputs[0]);return list(n.outputs)

def sample(t,name,image,uv):
    n=node(t,'ShaderNodeTexImage',name);n.image=image;n.interpolation='Linear'
    wire(t,uv,n.inputs['Vector']);return n

def bc5(t,s):
    c=split(t,s)
    x=math(t,'SUBTRACT',math(t,'MULTIPLY',c[0],1.992188),.992188)
    y=math(t,'SUBTRACT',math(t,'MULTIPLY',c[1],1.992188),.992188)
    length2=math(t,'ADD',math(t,'MULTIPLY',x,x),math(t,'MULTIPLY',y,y))
    inv=math(t,'DIVIDE',.999999,math(t,'MAXIMUM',length2,1))
    z=math(t,'SQRT',math(t,'MAXIMUM',math(t,'SUBTRACT',1,math(t,'MULTIPLY',inv,length2)),0))
    return combine(t,math(t,'MULTIPLY',x,inv),math(t,'MULTIPLY',y,inv),z)

def tangent_normal(t,s,uv='BaseMaterial'):
    n=node(t,'ShaderNodeNormalMap','Recovered BC5 tangent normal');n.uv_map=uv
    wire(t,vec(t,'ADD',vec(t,'SCALE',s,.5),(.5,.5,.5)),n.inputs['Color'])
    return n.outputs['Normal']

def rough_channels(t,image_socket,usage):
    n=node(t,'ShaderNodeSeparateColor','Native roughness / metal');wire(t,image_socket,n.inputs[0])
    assert usage in ('36','37'),usage
    return (n.outputs[0],n.outputs[1]) if usage=='36' else (n.outputs[1],n.outputs[0])

def decohill(bpy,m,record,images):
    t=m.node_tree;p=t.nodes['Principled BSDF']
    # Retain the existing angular/world-normal adapter, but give it the projected
    # image family. The old generic pass incorrectly projected the T images.
    for channel,slot in [('D','PyBaseColor'),('R','PyRoughMetal'),('N','PyNormal')]:
        for suffix in ['', ' World 1',' World 2']:
            n=t.nodes['tex_'+channel+suffix];n.image=images(slot)
            mapping=n.inputs['Vector'].links[0].from_node
            assert mapping.type=='VECT_MATH' and mapping.operation=='MULTIPLY',mapping.name
            scale=record['slots']['PyBaseColor']['scale']
            clear_input(t,mapping.inputs[1],(*scale,1))
        old=t.nodes.get('Apply _'+channel+' pxyz')
        if old:clear_input(t,old.inputs[0],1)
    macro=t.nodes['Additional Macro Color']
    clear_input(t,macro.inputs[0],0)
    top=t.nodes['tex_D World 2'].outputs['Color']
    destinations=[l.to_socket for l in top.links]
    modulation=node(t,'ShaderNodeMixRGB','Fidelity Py-only macro modulation');modulation.blend_type='MULTIPLY';modulation.inputs[0].default_value=1
    wire(t,top,modulation.inputs[1]);wire(t,t.nodes['Additional Macro Times Two'].outputs[0],modulation.inputs[2])
    for s in destinations:wire(t,modulation.outputs[0],s)
    # Existing macro operation now affects only the projected branch; the new
    # UV overlay is combined after it, matching the compiled operation order.
    uv=node(t,'ShaderNodeUVMap','Fidelity overlay UV: BaseMaterial');uv.uv_map='BaseMaterial'
    color=node(t,'ShaderNodeVertexColor','Fidelity vertex alpha: Color');color.layer_name='Color'
    control,ci,co=interface(bpy,'TM Explicit Vertex Alpha Preview',[
      ('Painted alpha','NodeSocketFloat',1),('Use painted vertex alpha','NodeSocketFloat',0),('Fallback alpha','NodeSocketFloat',1)], [('Alpha','NodeSocketFloat')])
    wire(control,scalar_mix(control,ci.outputs['Use painted vertex alpha'],ci.outputs['Fallback alpha'],ci.outputs['Painted alpha']),co.inputs[0])
    alpha=node(t,'ShaderNodeGroup','Fidelity vertex alpha control',(-400,900));alpha.node_tree=control;alpha.width=280
    wire(t,color.outputs['Alpha'],alpha.inputs['Painted alpha'])
    d=sample(t,'Fidelity TBaseColor',images('TBaseColor'),uv.outputs[0])
    r=sample(t,'Fidelity TRoughMetal',images('TRoughMetal'),uv.outputs[0])
    n=sample(t,'Fidelity TNormal',images('TNormal'),uv.outputs[0])
    f=math(t,'MULTIPLY',d.outputs['Alpha'],alpha.outputs[0],'Fidelity texture alpha x vertex alpha')
    rough,metal=rough_channels(t,r.outputs[0],record['slots']['TRoughMetal']['usage'])
    normals=tangent_normal(t,bc5(t,n.outputs[0]))
    for key,s in [('Base Color',d.outputs[0]),('Roughness',rough),('Metallic',metal),('Normal',normals)]:
        dst=p.inputs[key];base=dst.links[0].from_socket if dst.is_linked else dst.default_value
        if isinstance(base,(float,int)):base=(base,base,base,1)
        blended=mix(t,'Fidelity overlay '+key,f,base,s)
        wire(t,vec(t,'NORMALIZE',blended) if key=='Normal' else blended,dst)
    clear_input(t,p.inputs['Alpha'],1)
    m['tm_shader_fidelity_revision']=REVISION
    m['tm_decohill_preview']='Projected Py/Pxz terrain, macro modulation on the projected branch, then BaseMaterial UV T layer. Native blend = T texture alpha * Color vertex alpha. Existing angular/world-normal adapter remains a Blender approximation.'
    return dict(name=m.name,formula='mix(projected_with_macro, UV_overlay, T.alpha * Color.alpha)',uv='BaseMaterial')

def interface(bpy,name,specs,outputs):
    g=bpy.data.node_groups.new(name,'ShaderNodeTree')
    for key,typ,value in specs:
        s=g.interface.new_socket(name=key,in_out='INPUT',socket_type=typ)
        if value is not None:s.default_value=value
    for key,typ in outputs:g.interface.new_socket(name=key,in_out='OUTPUT',socket_type=typ)
    return g,node(g,'NodeGroupInput','Preview controls'),node(g,'NodeGroupOutput','Surface')

def shadows(t,surface):
    path=node(t,'ShaderNodeLightPath','Clear preview shadows')
    transparent=node(t,'ShaderNodeBsdfTransparent','Shadow passthrough')
    n=node(t,'ShaderNodeMixShader','Preview shadow handling')
    wire(t,path.outputs['Is Shadow Ray'],n.inputs[0]);wire(t,surface,n.inputs[1]);wire(t,transparent.outputs[0],n.inputs[2])
    return n.outputs[0]

def water(bpy,m,env,image,settings):
    specs=[('Normal','NodeSocketVector',None),('Water depth (meters, preview)','NodeSocketFloat',3),
      ('Fog distance (meters)','NodeSocketFloat',settings.get('max_depth') or 6),('Fog density (preview)','NodeSocketFloat',.12),
      ('Fog image slice (preview)','NodeSocketFloat',.5),('Tint per meter (preview)','NodeSocketColor',(.84,.95,.97,1)),
      ('Use depth attribute','NodeSocketFloat',0),('Roughness','NodeSocketFloat',.08),('IOR','NodeSocketFloat',1.333)]
    raw=settings.get('generator_real_params',[])
    # Explicit approximation: interpreting the first three generator values as
    # per-metre transmission is a preview model, not a decoded kind-51 formula.
    tint=raw[:3] if len(raw)>=3 else [.78,.88,.72]
    specs=[(k,typ,tuple(tint)+(1,) if k=='Tint per meter (preview)' else v) for k,typ,v in specs]
    g,i,o=interface(bpy,'TM Depth-coloured Water Preview - '+env,specs,[('Surface','NodeSocketShader'),('Fog amount','NodeSocketFloat'),('Path length','NodeSocketFloat')])
    geo=node(g,'ShaderNodeNewGeometry','View direction')
    attr=node(g,'ShaderNodeAttribute','Optional TM_WaterDepth');attr.attribute_name='TM_WaterDepth'
    depth=math(g,'MAXIMUM',scalar_mix(g,i.outputs['Use depth attribute'],i.outputs['Water depth (meters, preview)'],attr.outputs['Fac']),0)
    refr=node(g,'ShaderNodeVectorMath','Refracted water path');refr.operation='REFRACT'
    wire(g,vec(g,'SCALE',geo.outputs['Incoming'],-1),refr.inputs[0]);wire(g,i.outputs['Normal'],refr.inputs[1]);wire(g,math(g,'DIVIDE',1,i.outputs['IOR']),refr.inputs[2])
    cosine=math(g,'MAXIMUM',math(g,'ABSOLUTE',vec(g,'DOT_PRODUCT',refr.outputs[0],i.outputs['Normal'])),.1)
    distance=math(g,'DIVIDE',depth,cosine)
    x=math(g,'MINIMUM',math(g,'DIVIDE',distance,math(g,'MAXIMUM',i.outputs['Fog distance (meters)'],.001)),1)
    # The DDS layout is not the processed runtime array. A selectable image
    # slice with its long axis used for depth is an explicit preview adapter.
    uv=combine(g,x,i.outputs['Fog image slice (preview)']) if image.size[0]>=image.size[1] else combine(g,i.outputs['Fog image slice (preview)'],x)
    fog=sample(g,'Native fog colour source',image,uv);fog.extension='EXTEND'
    opacity=math(g,'SUBTRACT',1,math(g,'POWER',pymath.e,math(g,'MULTIPLY',distance,math(g,'MULTIPLY',i.outputs['Fog density (preview)'],-1))))
    transmission=split(g,i.outputs['Tint per meter (preview)'])
    tinted=combine(g,*[math(g,'POWER',math(g,'MAXIMUM',math(g,'MINIMUM',c,1),.00001),distance) for c in transmission])
    tr=node(g,'ShaderNodeBsdfTransparent','Depth-dependent coloured transmission');wire(g,tinted,tr.inputs['Color'])
    emission=node(g,'ShaderNodeEmission','Source-informed underwater colour');wire(g,fog.outputs[0],emission.inputs['Color'])
    body=node(g,'ShaderNodeMixShader','Depth fog and transmitted scene');wire(g,opacity,body.inputs[0]);wire(g,tr.outputs[0],body.inputs[1]);wire(g,emission.outputs[0],body.inputs[2])
    reflection=node(g,'ShaderNodeBsdfGlossy','Animated water reflection');wire(g,i.outputs['Normal'],reflection.inputs['Normal']);wire(g,i.outputs['Roughness'],reflection.inputs['Roughness'])
    f=node(g,'ShaderNodeFresnel','Water view angle');wire(g,i.outputs['Normal'],f.inputs['Normal']);wire(g,i.outputs['IOR'],f.inputs['IOR'])
    surface=node(g,'ShaderNodeMixShader','Water reflection over depth colour');wire(g,f.outputs[0],surface.inputs[0]);wire(g,body.outputs[0],surface.inputs[1]);wire(g,reflection.outputs[0],surface.inputs[2])
    wire(g,shadows(g,surface.outputs[0]),o.inputs[0]);wire(g,opacity,o.inputs[1]);wire(g,distance,o.inputs[2])
    t=m.node_tree;old=t.nodes['Water Clarity and Refraction Preview']
    n=node(t,'ShaderNodeGroup','Water Depth Colour - Source-informed Preview',(950,650));n.node_tree=g;n.width=330
    for key in ['Normal','Roughness','IOR']:
        src=old.inputs[key];wire(t,src.links[0].from_socket if src.is_linked else src.default_value,n.inputs[key])
    out=next(q for q in t.nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output);wire(t,n.outputs['Surface'],out.inputs['Surface']);setup_transparency(m)
    m['tm_shader_fidelity_revision']=REVISION
    m['tm_water_depth_preview']='Native fog image and depth/refraction composition roles; adjustable manual depth or TM_WaterDepth float attribute. DDS slice, fog opacity, per-metre tint interpretation and scattering illumination are Blender approximations; kind-51 generation and active runtime arrays are not fully recovered. Existing smooth animation retained. Realtime transmission does not bend background rays.'
    g['tm_preview_limit']=m['tm_water_depth_preview']
    return dict(name=m.name,environment=env,stored_collection_parsed=settings['collection_parsed'],depth_default=3,tint_per_meter=tint,fog_distance=n.inputs['Fog distance (meters)'].default_value)

def waterwall(bpy,m,record,images,fresnel_image):
    t=m.node_tree;params=__import__('json').loads(m['tm_native_parameters'])
    native=lambda k:params[k]['values'][0][0]
    native_keys=['Y0_Speed','Y1_Speed','X0_Period','X0_Scale','Normal1_Weight']
    specs=[('UV','NodeSocketVector',None),('Seconds','NodeSocketFloat',0),('Speed multiplier','NodeSocketFloat',1),('Vertex alpha','NodeSocketFloat',1),('Use painted vertex alpha','NodeSocketFloat',0),('Fallback alpha','NodeSocketFloat',1)]
    specs += [(k,'NodeSocketFloat',native(k)) for k in ['Y0_Speed','Y1_Speed','X0_Period','X0_Scale','Normal1_Weight']]
    g,i,o=interface(bpy,'TM WaterWall Source Layers',specs,[('Surface','NodeSocketShader'),('Foam amount','NodeSocketFloat'),('UV 0','NodeSocketVector'),('UV 1','NodeSocketVector')])
    alpha=scalar_mix(g,i.outputs['Use painted vertex alpha'],i.outputs['Fallback alpha'],i.outputs['Vertex alpha'])
    seconds=math(g,'MULTIPLY',i.outputs['Seconds'],i.outputs['Speed multiplier'])
    uv=split(g,i.outputs['UV'])
    x=math(g,'ADD',uv[0],math(g,'MULTIPLY',i.outputs['X0_Scale'],math(g,'SINE',math(g,'DIVIDE',math(g,'MULTIPLY',seconds,2*pymath.pi),math(g,'MAXIMUM',i.outputs['X0_Period'],.001)))))
    y=[math(g,'ADD',uv[1],math(g,'FRACT',math(g,'MULTIPLY',seconds,i.outputs[k]))) for k in ['Y0_Speed','Y1_Speed']]
    uvs=[combine(g,x,y[0]),combine(g,uv[0],y[1])]
    trans=sample(g,'Native RGB transmittance',images('Transmittance'),uvs[0])
    rough=sample(g,'Native roughness metal',images('RoughMetal'),uvs[0])
    foam=sample(g,'Native foam opacity',images('FoamOpacity'),uvs[0])
    normals=[bc5(g,sample(g,'Native flowing normal '+str(j),images('Normal'),s).outputs[0]) for j,s in enumerate(uvs)]
    normal=vec(g,'ADD',normals[0],vec(g,'SCALE',vec(g,'SUBTRACT',normals[1],normals[0]),i.outputs['Normal1_Weight']))
    xyz=split(g,normal);strength=math(g,'MULTIPLY',alpha,1.001)
    normal=vec(g,'NORMALIZE',combine(g,math(g,'MULTIPLY',xyz[0],strength),math(g,'MULTIPLY',xyz[1],strength),xyz[2]))
    normal=tangent_normal(g,normal)
    geo=node(g,'ShaderNodeNewGeometry','WaterWall view')
    dot=math(g,'MINIMUM',math(g,'ABSOLUTE',vec(g,'DOT_PRODUCT',normal,geo.outputs['Incoming'])),1)
    lookup=sample(g,'Native Fresnel lookup',fresnel_image,combine(g,dot,dot));lookup.extension='EXTEND'
    f=node(g,'ShaderNodeSeparateColor','Native Fresnel green');wire(g,lookup.outputs[0],f.inputs[0]);f=f.outputs['Green']
    op=math(g,'MINIMUM',math(g,'MAXIMUM',math(g,'MULTIPLY',foam.outputs['Color'],alpha),0),1,'Native foam x vertex alpha')
    coefficient=math(g,'MULTIPLY',math(g,'SUBTRACT',1,f),math(g,'SUBTRACT',1,op))
    tr=node(g,'ShaderNodeBsdfTransparent','Coloured scene transmission');wire(g,vec(g,'SCALE',trans.outputs[0],coefficient),tr.inputs['Color'])
    reflected=node(g,'ShaderNodeBsdfGlossy','WaterWall reflection');wire(g,normal,reflected.inputs['Normal'])
    r,_=rough_channels(g,rough.outputs[0],record['slots']['RoughMetal']['usage']);wire(g,r,reflected.inputs['Roughness'])
    lit=node(g,'ShaderNodeBsdfDiffuse','Lit white foam');wire(g,normal,lit.inputs['Normal'])
    weighted=[]
    for name,weight,shader in [('Fresnel reflection',f,reflected.outputs[0]),('Vertex painted foam',op,lit.outputs[0])]:
        n=node(g,'ShaderNodeMixShader',name);wire(g,weight,n.inputs[0]);wire(g,shader,n.inputs[2]);weighted.append(n.outputs[0])
    add=node(g,'ShaderNodeAddShader','Reflection and foam');wire(g,weighted[0],add.inputs[0]);wire(g,weighted[1],add.inputs[1])
    result=node(g,'ShaderNodeAddShader','WaterWall colour composition');wire(g,add.outputs[0],result.inputs[0]);wire(g,tr.outputs[0],result.inputs[1])
    wire(g,shadows(g,result.outputs[0]),o.inputs[0]);wire(g,op,o.inputs[1]);wire(g,uvs[0],o.inputs[2]);wire(g,uvs[1],o.inputs[3])
    n=node(t,'ShaderNodeGroup','WaterWall Source Layers Preview',(1000,600));n.node_tree=g;n.width=320
    uvnode=node(t,'ShaderNodeUVMap','WaterWall BaseMaterial UV');uvnode.uv_map='BaseMaterial';wire(t,uvnode.outputs[0],n.inputs['UV'])
    vertex=node(t,'ShaderNodeVertexColor','WaterWall Color alpha');vertex.layer_name='Color';wire(t,vertex.outputs['Alpha'],n.inputs['Vertex alpha'])
    wire(t,clock(t,'WaterWall seconds - active scene'),n.inputs['Seconds'])
    output=next(q for q in t.nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output);wire(t,n.outputs['Surface'],output.inputs['Surface']);setup_transparency(m)
    m['tm_shader_fidelity_revision']=REVISION
    m['tm_waterwall_preview']='Recovered two UV flows, sinusoidal horizontal displacement, normal layer weight, vertex-alpha normal strength, foam-alpha product, native Fresnel lookup and RGB transmission coefficient. Blender reflection, lit foam and straight-through scene transmission approximate engine lighting/render targets. No generic fixed alpha.'
    return dict(name=m.name,native_parameters={k:native(k) for k in native_keys},transmission='T.rgb * (1-Fresnel) * (1-FoamOpacity*Color.alpha)')
