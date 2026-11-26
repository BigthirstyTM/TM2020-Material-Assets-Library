"""Explicit Py/Pxz/T and layered-ice preview roles; no export-link changes."""
import json,math as M
from material_preview_adapters import node,wire,math,vec,combine
from shader_fidelity_adapters import interface,mix,scalar_mix,sample,split,bc5,tangent_normal,rough_channels,clear_input

REVISION='2026.11.23-deco-ice-1'

def constant(t,value):
    n=node(t,'ShaderNodeRGB','Native fallback');n.outputs[0].default_value=(*value[:3],1);return n.outputs[0]

def transform(t,uv,desc):
    s=desc.get('scale',[1,1]);angle=M.radians(desc.get('rotation',0));c=M.cos(angle);sn=M.sin(angle)
    xy=split(t,uv)
    if angle:uv=combine(t,math(t,'SUBTRACT',math(t,'MULTIPLY',xy[0],c),math(t,'MULTIPLY',xy[1],sn)),math(t,'ADD',math(t,'MULTIPLY',xy[0],sn),math(t,'MULTIPLY',xy[1],c)))
    return vec(t,'ADD',vec(t,'MULTIPLY',uv,(*s[:2],1)),(*desc.get('translation',[0,0])[:2],0))

def tex(t,images,slot,uv,fallback):
    image=images(slot)
    return sample(t,'Native '+slot,image,uv).outputs[0] if image else constant(t,fallback)

def hue(t,rgb,target):
    # Compiled PyPxz_Hue: chroma=max(G-.5*(R+B),0), grey=G-chroma.
    r,g,b=split(t,rgb);tr,tg,tb=split(t,target)
    chroma=math(t,'MAXIMUM',math(t,'SUBTRACT',g,math(t,'MULTIPLY',math(t,'ADD',r,b),.5)),0)
    grey=math(t,'SUBTRACT',g,chroma)
    mean=math(t,'MULTIPLY',math(t,'ADD',math(t,'ADD',tr,tg),tb),1/3)
    out=[math(t,'MINIMUM',math(t,'MAXIMUM',math(t,'ADD',math(t,'MULTIPLY',chroma,c),math(t,'MULTIPLY',grey,mean)),0),1) for c in [tr,tg,tb]]
    return combine(t,*out)

def layout(g):
    levels={n:0 for n in g.nodes}
    for _ in range(len(g.nodes)):
        changed=False
        for l in g.links:
            if levels[l.to_node]<=levels[l.from_node]:levels[l.to_node]=levels[l.from_node]+1;changed=True
        if not changed:break
    counts={}
    for n in g.nodes:
        level=levels[n];row=counts.get(level,0);counts[level]=row+1;n.location=(220*level,-190*row)

def projected(bpy,g,m,record,images,hue_target=None,colour=True):
    slots=record['slots'];geo=node(g,'ShaderNodeNewGeometry','World projection geometry')
    pos=split(g,geo.outputs['Position']);normal=split(g,geo.outputs['Normal'])
    signs=[math(g,'SUBTRACT',math(g,'MULTIPLY',math(g,'GREATER_THAN',n,0),2),1) for n in normal]
    coords=[combine(g,math(g,'MULTIPLY',pos[1],signs[0]),pos[2]),combine(g,math(g,'MULTIPLY',pos[0],math(g,'MULTIPLY',signs[1],-1)),pos[2]),combine(g,pos[0],math(g,'MULTIPLY',pos[1],signs[2]))]
    previous=m.node_tree.nodes.get('Terrain Angular Transition Controls')
    if previous:
        w=node(g,'ShaderNodeGroup','Native angle endpoints - Blender interpolation');w.node_tree=previous.node_tree
        for old,new in zip(previous.inputs,w.inputs):
            if hasattr(new,'default_value'):new.default_value=old.default_value
        wire(g,geo.outputs['Normal'],w.inputs['Normal']);weights=list(w.outputs)
    else:
        weights=[math(g,'POWER',math(g,'ABSOLUTE',n),4) for n in normal];total=math(g,'ADD',math(g,'ADD',weights[0],weights[1]),weights[2]);weights=[math(g,'DIVIDE',v,total) for v in weights]
    result={k:[] for k in ['colour','rough','metal','perturb']}
    for axis,coord in enumerate(coords):
        prefix='Py' if axis==2 else 'Pxz'
        key=prefix+('BaseColor' if colour else 'RoughMetal')
        desc=slots[key];uv=transform(g,coord,desc)
        if colour:
            c=tex(g,images,prefix+'BaseColor',uv,(.5,.5,.5))
            if hue_target is not None:c=hue(g,c,hue_target)
            if axis==2 and 'PyX2' in slots:
                x2=tex(g,images,'PyX2',transform(g,coords[2],slots['PyX2']),(.5,.5,.5))
                hdesc=slots.get('PyHx2',{})
                height=transform(g,combine(g,pos[2],pos[2]),hdesc)
                hx=tex(g,images,'PyHx2',height,(.5,.5,.5)) if 'PyHx2' in slots else tex(g,images,'PyH2',transform(g,coords[2],slots['PyH2']),(.5,.5,.5)) if 'PyH2' in slots else constant(g,(.5,.5,.5))
                c=vec(g,'MULTIPLY',c,vec(g,'SCALE',vec(g,'MULTIPLY',x2,hx),4))
            result['colour'].append(vec(g,'SCALE',c,weights[axis]))
        rm=tex(g,images,prefix+'RoughMetal',uv,(.6,0,0))
        r,metal=rough_channels(g,rm,slots[prefix+'RoughMetal'].get('usage','36'))
        result['rough'].append(math(g,'MULTIPLY',r,weights[axis]));result['metal'].append(math(g,'MULTIPLY',metal,weights[axis]))
        n=bc5(g,tex(g,images,prefix+'Normal',uv,(.5,.5,1)));nx,ny,_=split(g,n)
        dx=math(g,'MULTIPLY',nx,signs[axis])
        delta=combine(g,0,dx,ny) if axis==0 else combine(g,math(g,'MULTIPLY',dx,-1),0,ny) if axis==1 else combine(g,nx,math(g,'MULTIPLY',ny,signs[2]),0)
        result['perturb'].append(vec(g,'SCALE',delta,weights[axis]))
    def sumvec(values):return vec(g,'ADD',vec(g,'ADD',values[0],values[1]),values[2])
    return dict(colour=sumvec(result['colour']) if colour else None,
      rough=math(g,'ADD',math(g,'ADD',*result['rough'][:2]),result['rough'][2]),
      metal=math(g,'ADD',math(g,'ADD',*result['metal'][:2]),result['metal'][2]),
      normal=vec(g,'NORMALIZE',vec(g,'ADD',geo.outputs['Normal'],sumvec(result['perturb']))))

def connect_surface(t,p,n):
    for key in ['Base Color','Roughness','Metallic','Normal']:wire(t,n.outputs[key],p.inputs[key])
    clear_input(t,p.inputs['Alpha'],1);clear_input(t,p.inputs['Specular IOR Level'],.5)

def terrain(bpy,m,record,images):
    colour_slot='TBaseColorOp' if 'TBaseColorOp' in record['slots'] else 'TBaseColor'
    mixed=colour_slot in record['slots'];is_hue='pypxz_hue' in record['shader']
    params=json.loads(m.get('tm_native_parameters','{}'));target=params.get('TargetColor',{}).get('values',[[1,1,1]])[0][:3]
    specs=[('BaseMaterial UV','NodeSocketVector',None),('Painted alpha','NodeSocketFloat',1),('Use painted vertex alpha','NodeSocketFloat',0),('Fallback alpha','NodeSocketFloat',1)]
    if is_hue:specs.append(('Hue target (native default)','NodeSocketColor',(*target,1)))
    g,i,o=interface(bpy,'TM Deco Layers - '+m.name,specs,[(k,'NodeSocketVector' if k=='Normal' else 'NodeSocketFloat' if k in ['Roughness','Metallic','Layer weight'] else 'NodeSocketColor') for k in ['Base Color','Roughness','Metallic','Normal','Layer weight']])
    base=projected(bpy,g,m,record,images,i.outputs['Hue target (native default)'] if is_hue else None)
    values={'Base Color':base['colour'],'Roughness':base['rough'],'Metallic':base['metal'],'Normal':base['normal']}
    if mixed:
        d=sample(g,'Native '+colour_slot+' - mesh UV only',images(colour_slot),i.outputs['BaseMaterial UV'])
        r=tex(g,images,'TRoughMetal',i.outputs['BaseMaterial UV'],(.6,0,0));rough,metal=rough_channels(g,r,record['slots']['TRoughMetal']['usage'])
        normal=tangent_normal(g,bc5(g,tex(g,images,'TNormal',i.outputs['BaseMaterial UV'],(.5,.5,1))))
        alpha=scalar_mix(g,i.outputs['Use painted vertex alpha'],i.outputs['Fallback alpha'],i.outputs['Painted alpha'])
        f=math(g,'MULTIPLY',d.outputs['Alpha'],alpha,'Native T alpha x selected vertex alpha')
        values['Base Color']=mix(g,'Projected colour then UV decoration',f,base['colour'],d.outputs[0])
        values['Roughness']=scalar_mix(g,f,base['rough'],rough);values['Metallic']=scalar_mix(g,f,base['metal'],metal)
        values['Normal']=vec(g,'NORMALIZE',mix(g,'World and tangent normal blend',f,base['normal'],normal))
    else:
        f=0
    for k,v in values.items():wire(g,v,o.inputs[k])
    wire(g,f,o.inputs['Layer weight']);layout(g)
    t=m.node_tree;n=node(t,'ShaderNodeGroup','Deco native layer controls',(1100,1000));n.node_tree=g;n.width=310
    uv=node(t,'ShaderNodeUVMap','Deco BaseMaterial UV');uv.uv_map='BaseMaterial';wire(t,uv.outputs[0],n.inputs['BaseMaterial UV'])
    c=node(t,'ShaderNodeVertexColor','Deco Color alpha');c.layer_name='Color';wire(t,c.outputs['Alpha'],n.inputs['Painted alpha'])
    connect_surface(t,t.nodes['Principled BSDF'],n)
    m['tm_deco_ice_revision']=REVISION
    m['tm_deco_layer_roles']='Explicit projected Py/Pxz and Py-only macro; T layer uses BaseMaterial UV with texture alpha * selected vertex alpha. Native Hue-family chroma/grey reconstruction applied where used. Projection normal bases, angle interpolation, runtime array selection and matrix orientation remain renderer approximations.'
    return dict(name=m.name,family='mixed UV decoration' if mixed else 'projected hue' if is_hue else 'projected',group=n.name)

def layered_ice(bpy,m,record,images):
    t=m.node_tree;p=t.nodes['Principled BSDF'];slots=record['slots']
    # Repair a missing internal image, and use authored BaseMaterial UV for the
    # internal depth adapter and all T inputs. Do not gate inner colour by alpha.
    for name,slot in [('tex_D','SubsurfaceBaseColor'),('tex_D_HueMask','SubsurfaceBaseColorHueMask'),('Additional H','SubsurfaceDepth')]:
        if t.nodes.get(name) and images(slot):t.nodes[name].image=images(slot)
    for q in t.nodes:
        if q.type=='UVMAP':q.uv_map='BaseMaterial'
    inner=t.nodes['Apply _D Hue'];inner_socket=next(s for s in inner.outputs if s.type=='RGBA')
    params=json.loads(m['tm_native_parameters']);value=lambda key:params[key]['values'][0]
    g,i,o=interface(bpy,'TM Layered Ice - '+m.name,[('BaseMaterial UV','NodeSocketVector',None),('Internal colour','NodeSocketColor',(1,1,1,1)),('Surface colour','NodeSocketColor',(*value('SurfaceColor')[:3],1)),('Surface max opacity','NodeSocketFloat',value('SurfaceMaxOpacity')[0])],[(k,'NodeSocketVector' if k=='Normal' else 'NodeSocketFloat' if k in ['Roughness','Metallic','Layer weight'] else 'NodeSocketColor') for k in ['Base Color','Roughness','Metallic','Normal','Layer weight']])
    base=projected(bpy,g,m,record,images,colour=False)
    # sample r5.w, ..., t7.yzwx selects source R in destination W.
    mask=tex(g,images,'TAlpha',i.outputs['BaseMaterial UV'],(0,0,0));f=split(g,mask)[0]
    r,metal=rough_channels(g,tex(g,images,'TRoughMetal',i.outputs['BaseMaterial UV'],(.6,0,0)),slots['TRoughMetal']['usage'])
    rough=scalar_mix(g,f,base['rough'],r);met=scalar_mix(g,f,base['metal'],metal)
    normal=tangent_normal(g,bc5(g,tex(g,images,'TNormal',i.outputs['BaseMaterial UV'],(.5,.5,1))))
    normal=vec(g,'NORMALIZE',mix(g,'Projected ice and UV surface marks',f,base['normal'],normal))
    colour=mix(g,'Native internal colour and surface tint',math(g,'MULTIPLY',rough,i.outputs['Surface max opacity']),i.outputs['Internal colour'],i.outputs['Surface colour'])
    for key,s in [('Base Color',colour),('Roughness',rough),('Metallic',met),('Normal',normal),('Layer weight',f)]:wire(g,s,o.inputs[key])
    layout(g);n=node(t,'ShaderNodeGroup','Ice native surface and internal layers',(1100,1000));n.node_tree=g;n.width=310
    uv=node(t,'ShaderNodeUVMap','Ice BaseMaterial UV');uv.uv_map='BaseMaterial';wire(t,uv.outputs[0],n.inputs['BaseMaterial UV']);wire(t,inner_socket,n.inputs['Internal colour']);connect_surface(t,p,n)
    m['tm_deco_ice_revision']=REVISION
    m['tm_ice_layer_roles']='Subsurface base colour/depth uses authored BaseMaterial UV through the existing planar depth adapter. Projected R/N and UV surface R/N blend through TAlpha (without vertex alpha). Surface tint = combined roughness * SurfaceMaxOpacity. Blender internal depth and normals remain approximations.'
    return dict(name=m.name,family='layered ice',group=n.name)

def uv_surface(m,record,images):
    t=m.node_tree;mapping=[('tex_D','BaseColorA' if 'BaseColorA' in record['slots'] else 'BaseColor'),('tex_R','RoughMetal'),('tex_N','Normal'),('tex_D_HueMask','BaseColorHueMask')]
    repaired=[]
    for name,slot in mapping:
        n=t.nodes.get(name);im=images(slot)
        if n and im:
            if n.image!=im:repaired.append(name)
            n.image=im
    for n in t.nodes:
        if n.type=='UVMAP':n.uv_map='BaseMaterial'
    clear_input(t,t.nodes['Principled BSDF'].inputs['Specular IOR Level'],.5)
    m['tm_deco_ice_revision']=REVISION
    return dict(name=m.name,family='UV decal' if 'decalgeom' in record['shader'] else 'UV surface',repaired_images=repaired)
