"""Blender preview adapters; controls do not change native export parameters."""
def node(t,typ,name,loc=(0,0)):
    n=t.nodes.new(typ);n.name=n.label=name;n.location=loc;return n
def wire(t,value,socket):
    if hasattr(value,'node'):t.links.new(value,socket)
    else:socket.default_value=value
def scalar(t,name,value,loc=(0,0)):
    n=node(t,'ShaderNodeValue',name,loc);n.outputs[0].default_value=value;return n.outputs[0]
def math(t,op,a,b=None,name=None):
    n=node(t,'ShaderNodeMath',name or op);n.operation=op;wire(t,a,n.inputs[0])
    if b is not None:wire(t,b,n.inputs[1])
    return n.outputs[0]
def preview_surface_group(bpy):
    g=bpy.data.node_groups.new('TM Clear Surface Preview v1','ShaderNodeTree')
    specs=[('Normal','NodeSocketVector',None),('Physical surface','NodeSocketShader',None),('Clarity','NodeSocketFloat',.92),('Roughness','NodeSocketFloat',.08),('IOR','NodeSocketFloat',1.333),('Physical refraction','NodeSocketFloat',0),('Transmission tint','NodeSocketColor',(1,1,1,1))]
    for name,typ,default in specs:
        s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=typ)
        if default is not None:s.default_value=default
        if name in ['Clarity','Physical refraction','Roughness']:s.min_value=0;s.max_value=1
    g.interface.new_socket(name='Surface',in_out='OUTPUT',socket_type='NodeSocketShader')
    i=node(g,'NodeGroupInput','Preview settings',(-600,0));o=node(g,'NodeGroupOutput','Surface',(600,0))
    transparent=node(g,'ShaderNodeBsdfTransparent','Light passing through surface',(-100,-150))
    wire(g,i.outputs['Transmission tint'],transparent.inputs['Color'])
    reflection=node(g,'ShaderNodeBsdfGlossy','Surface reflection',(-100,150));wire(g,i.outputs['Normal'],reflection.inputs['Normal']);wire(g,i.outputs['Roughness'],reflection.inputs['Roughness'])
    fresnel=node(g,'ShaderNodeFresnel','View-angle reflection',(-350,300));wire(g,i.outputs['Normal'],fresnel.inputs['Normal']);wire(g,i.outputs['IOR'],fresnel.inputs['IOR'])
    opacity=math(g,'SUBTRACT',1,math(g,'MULTIPLY',i.outputs['Clarity'],math(g,'SUBTRACT',1,fresnel.outputs[0])),'Reflection and clarity')
    realtime=node(g,'ShaderNodeMixShader','Realtime transparent preview',(150,100));wire(g,opacity,realtime.inputs[0]);wire(g,transparent.outputs[0],realtime.inputs[1]);wire(g,reflection.outputs[0],realtime.inputs[2])
    mode=node(g,'ShaderNodeMixShader','Optional physical refraction',(380,0));wire(g,i.outputs['Physical refraction'],mode.inputs[0]);wire(g,realtime.outputs[0],mode.inputs[1]);wire(g,i.outputs['Physical surface'],mode.inputs[2]);wire(g,mode.outputs[0],o.inputs[0])
    g['tm_preview_limit']='Realtime mode transmits background rays without bending. Physical mode uses the original transmission BSDF and needs Eevee ray tracing, or Cycles. IOR/clarity defaults are preview assumptions, not recovered runtime constants.'
    return g
def setup_transparency(m):
    m.surface_render_method='DITHERED'
    m.use_raytrace_refraction=True
    m.use_transparent_shadow=True
    m.thickness_mode='SLAB'
def add_water_clarity(bpy,m,group):
    t=m.node_tree;p=t.nodes['Principled BSDF'];out=next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    old=out.inputs['Surface'].links[0].from_socket
    n=node(t,'ShaderNodeGroup','Water Clarity and Refraction Preview',(650,600));n.node_tree=group;n.width=280
    normal=p.inputs['Normal'].links[0].from_socket
    wire(t,normal,n.inputs['Normal']);wire(t,old,n.inputs['Physical surface'])
    p.inputs['Roughness'].default_value=.08;p.inputs['IOR'].default_value=1.333;p.inputs['Transmission Weight'].default_value=1
    for key,value in [('Roughness',.08),('IOR',1.333)]:
        control=scalar(t,'Water '+key+' (preview)',value,(250,850 if key=='Roughness' else 950))
        wire(t,control,n.inputs[key]);wire(t,control,p.inputs[key])
    wire(t,n.outputs[0],out.inputs['Surface']);setup_transparency(m)
    m['tm_water_surface_preview']='Realtime transparent + Fresnel reflection preview, visible through horizontal water in Eevee Material Preview without scene ray tracing. Optional Physical refraction uses the transmission BSDF. Clarity .92, roughness .08 and IOR 1.333 are adjustable preview defaults, not recovered game constants.'
    return n

def vec(t,op,a,b=None):
    n=node(t,'ShaderNodeVectorMath',op);n.operation=op;wire(t,a,n.inputs[0])
    if b is not None:wire(t,b,n.inputs['Scale'] if op=='SCALE' else n.inputs[1])
    return n.outputs['Value' if op in ['DOT_PRODUCT','DISTANCE','LENGTH'] else 'Vector']

def combine(t,x,y,z=0):
    n=node(t,'ShaderNodeCombineXYZ','Vector');
    for s,v in zip(n.inputs,[x,y,z]):wire(t,v,s)
    return n.outputs[0]

def smooth(t,x,lo,hi):
    n=node(t,'ShaderNodeMapRange','Smooth angular transition');n.interpolation_type='SMOOTHSTEP';n.clamp=True
    wire(t,x,n.inputs['Value']);wire(t,lo,n.inputs['From Min']);wire(t,hi,n.inputs['From Max']);return n.outputs[0]

def angular_weights(bpy,lo,hi,side_lo,side_hi):
    g=bpy.data.node_groups.new('TM Terrain Angular Blend Preview','ShaderNodeTree')
    for name,typ,d in [('Normal','NodeSocketVector',None),('Top transition start','NodeSocketFloat',lo),('Top transition end','NodeSocketFloat',hi),('Side transition start','NodeSocketFloat',side_lo),('Side transition end','NodeSocketFloat',side_hi)]:
        s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=typ)
        if d is not None:s.default_value=d
    for name in ['X weight','Y weight','Z weight']:g.interface.new_socket(name=name,in_out='OUTPUT',socket_type='NodeSocketFloat')
    i=node(g,'NodeGroupInput','Native angle range');o=node(g,'NodeGroupOutput','Projection weights')
    sep=node(g,'ShaderNodeSeparateXYZ','World normal');wire(g,i.outputs['Normal'],sep.inputs[0])
    ax=[math(g,'ABSOLUTE',s) for s in sep.outputs]
    # ACosSmoothInRange descriptors store angular ranges. Curve shape and normalized
    # angle convention are an explicit Blender reconstruction, not captured LUT pixels.
    angle=math(g,'MULTIPLY',math(g,'ARCCOSINE',math(g,'MINIMUM',ax[2],1)),2/3.141592653589793)
    side=math(g,'SQRT',math(g,'ADD',math(g,'MULTIPLY',ax[0],ax[0]),math(g,'MULTIPLY',ax[1],ax[1])))
    azimuth=math(g,'MULTIPLY',math(g,'ARCCOSINE',math(g,'MINIMUM',math(g,'DIVIDE',ax[0],math(g,'MAXIMUM',side,1e-6)),1)),2/3.141592653589793)
    sides=smooth(g,angle,i.outputs['Top transition start'],i.outputs['Top transition end'])
    y=smooth(g,azimuth,i.outputs['Side transition start'],i.outputs['Side transition end'])
    for v,s in zip([math(g,'MULTIPLY',sides,math(g,'SUBTRACT',1,y)),math(g,'MULTIPLY',sides,y),math(g,'SUBTRACT',1,sides)],o.inputs):wire(g,v,s)
    return g

def depth_group(bpy):
    g=bpy.data.node_groups.new('TM Refracted Layer Preview v1','ShaderNodeTree')
    specs=[('UV','NodeSocketVector',(0,0,0)),('Normal','NodeSocketVector',None),('Depth (meters)','NodeSocketFloat',.025),('Size (meters)','NodeSocketVector',(32,32,1)),('Refract ratio','NodeSocketFloat',1),('Double refraction','NodeSocketFloat',0)]
    for name,typ,d in specs:
        s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=typ)
        if d is not None:s.default_value=d
    g.interface.new_socket(name='UV',in_out='OUTPUT',socket_type='NodeSocketVector')
    i=node(g,'NodeGroupInput','Native depth controls');o=node(g,'NodeGroupOutput','Subsurface UV')
    geo=node(g,'ShaderNodeNewGeometry','View');tan=node(g,'ShaderNodeTangent','BaseMaterial tangent');tan.direction_type='UV_MAP';tan.uv_map='BaseMaterial'
    normal=i.outputs['Normal'];bi=vec(g,'CROSS_PRODUCT',geo.outputs['Normal'],tan.outputs[0])
    refr=node(g,'ShaderNodeVectorMath','Refract view into surface');refr.operation='REFRACT';wire(g,vec(g,'SCALE',geo.outputs['Incoming'],-1),refr.inputs[0]);wire(g,normal,refr.inputs[1]);wire(g,i.outputs['Refract ratio'],refr.inputs[2])
    direction=refr.outputs[0]
    denominator=math(g,'MAXIMUM',math(g,'ABSOLUTE',vec(g,'DOT_PRODUCT',direction,geo.outputs['Normal'])),.05)
    # Project refracted view into tangent UV axes; cap grazing angles to keep previews finite.
    d=math(g,'DIVIDE',i.outputs['Depth (meters)'],denominator)
    undo=math(g,'ADD',1,math(g,'MULTIPLY',i.outputs['Double refraction'],math(g,'SUBTRACT',math(g,'DIVIDE',1,i.outputs['Refract ratio']),1)))
    xy=combine(g,vec(g,'DOT_PRODUCT',direction,tan.outputs[0]),vec(g,'DOT_PRODUCT',direction,bi))
    offset=vec(g,'DIVIDE',vec(g,'SCALE',xy,math(g,'MULTIPLY',d,undo)),i.outputs['Size (meters)'])
    wire(g,vec(g,'ADD',i.outputs['UV'],offset),o.inputs[0])
    g['tm_preview_limit']='Source-informed tangent refraction and depth projection; planar approximation, not the native iterative height ray marcher. Grazing denominator bounded at 0.05.'
    return g
