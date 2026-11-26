"""Reviewed projected normals and independent source texture transforms."""
from material_preview_adapters import node,wire,math,vec,combine
from shader_fidelity_adapters import sample,split,bc5,rough_channels,mix
from deco_ice_adapters import transform,tex,hue
import math as M

REVISION='2026.11.23-projection-sources-1'

def projected(bpy,g,m,record,images,hue_target=None,colour=True):
    slots=record['slots'];geo=node(g,'ShaderNodeNewGeometry','Source projected geometry')
    normal=vec(g,'NORMALIZE',geo.outputs['Normal']);pos=split(g,geo.outputs['Position']);n=split(g,normal)
    signs=[math(g,'SUBTRACT',math(g,'MULTIPLY',math(g,'GREATER_THAN',v,0),2),1) for v in n]
    coords=[combine(g,math(g,'MULTIPLY',pos[1],signs[0]),pos[2]),combine(g,math(g,'MULTIPLY',pos[0],math(g,'MULTIPLY',signs[1],-1)),pos[2]),combine(g,pos[0],pos[1])]
    old=m.node_tree.nodes.get('Terrain Angular Transition Controls')
    if record.get('array_angles'):
        def weight(value,angles):
            low,high=sorted(M.cos(M.radians(a)) for a in angles)
            f=math(g,'MINIMUM',math(g,'MAXIMUM',math(g,'DIVIDE',math(g,'SUBTRACT',value,low),high-low),0),1)
            return math(g,'MULTIPLY',math(g,'MULTIPLY',f,f),math(g,'SUBTRACT',3,math(g,'MULTIPLY',2,f)))
        wz=weight(math(g,'ABSOLUTE',n[2]),record['array_angles']['top'])
        horizontal=math(g,'SQRT',math(g,'ADD',math(g,'MULTIPLY',n[0],n[0]),math(g,'MULTIPLY',n[1],n[1])))
        side=math(g,'SUBTRACT',1,weight(math(g,'DIVIDE',math(g,'ABSOLUTE',n[0]),math(g,'MAXIMUM',horizontal,1e-8)),record['array_angles']['side']))
        wx=math(g,'MULTIPLY',math(g,'SUBTRACT',1,wz),math(g,'SUBTRACT',1,side));wy=math(g,'MULTIPLY',math(g,'SUBTRACT',1,wz),side)
    elif old:
        weights=node(g,'ShaderNodeGroup','Retained native angle-range interpolation');weights.node_tree=old.node_tree
        for a,b in zip(old.inputs,weights.inputs):
            if hasattr(b,'default_value'):b.default_value=a.default_value
        wire(g,normal,weights.inputs['Normal']);wx,wy,wz=weights.outputs
    else:
        raw=[math(g,'POWER',math(g,'ABSOLUTE',v),4) for v in n];total=math(g,'ADD',math(g,'ADD',raw[0],raw[1]),raw[2]);wx,wy,wz=[math(g,'DIVIDE',v,total) for v in raw]
    # Side texture channels are mixed before BC5 decode, as in compiled code.
    side_factor=math(g,'DIVIDE',wy,math(g,'MAXIMUM',math(g,'ADD',wx,wy),1e-8))
    values={k:[] for k in ['colour','rough','metal','encoded_normal']}
    for axis,coord in enumerate(coords):
        prefix='Py' if axis==2 else 'Pxz'
        def read(role,fallback):
            key=prefix+role;return tex(g,images,key,transform(g,coord,slots[key]),fallback)
        if colour:
            c=read('BaseColor',(.5,.5,.5))
            if hue_target is not None:c=hue(g,c,hue_target)
            if axis==2 and slots.get('PyX2',{}).get('image'):
                macro=tex(g,images,'PyX2',transform(g,coord,slots['PyX2']),(.5,.5,.5))
                height_role='PyHx2' if slots.get('PyHx2',{}).get('image') else 'PyH2' if slots.get('PyH2',{}).get('image') else None
                if height_role:
                    # Native H2/Hx2 modulation uses height, not the horizontal plane.
                    hc=transform(g,combine(g,pos[2],pos[2]),slots[height_role]);height=tex(g,images,height_role,hc,(.5,.5,.5))
                    macro=vec(g,'SCALE',vec(g,'MULTIPLY',macro,height),4)
                else:macro=vec(g,'SCALE',macro,2)
                c=vec(g,'MULTIPLY',c,macro)
            values['colour'].append(c)
        r,metal=rough_channels(g,read('RoughMetal',(.6,0,0)),slots[prefix+'RoughMetal']['usage'])
        values['rough'].append(r);values['metal'].append(metal);values['encoded_normal'].append(read('Normal',(.4980392,.4980392,1)))
    def scalar(a,b,f):return math(g,'ADD',a,math(g,'MULTIPLY',f,math(g,'SUBTRACT',b,a)))
    def blended(k):
        v=values[k]
        if k in ['rough','metal']:return scalar(scalar(v[0],v[1],side_factor),v[2],wz)
        return mix(g,'Source side then top '+k,wz,mix(g,'Source side '+k,side_factor,v[0],v[1]),v[2])
    # Source normal frames are tangent to the actual surface, including slopes.
    # The old adapter added XY perturbations directly to the world normal.
    top_tangent=vec(g,'SUBTRACT',(1,0,0),vec(g,'SCALE',normal,n[0]))
    top_tangent=mix(g,'Top tangent pole fallback',math(g,'LESS_THAN',vec(g,'LENGTH',top_tangent),1e-6),top_tangent,(0,1,0,1));top_tangent=vec(g,'NORMALIZE',top_tangent)
    top_bitangent=vec(g,'CROSS_PRODUCT',normal,top_tangent)
    side_tangent=vec(g,'CROSS_PRODUCT',(0,0,1),normal)
    side_tangent=mix(g,'Side tangent pole fallback',math(g,'LESS_THAN',vec(g,'LENGTH',side_tangent),1e-6),side_tangent,(0,1,0,1));side_tangent=vec(g,'NORMALIZE',side_tangent)
    side_bitangent=vec(g,'CROSS_PRODUCT',side_tangent,normal)
    def orient(encoded,tangent,bitangent,desc):
        x,y,z=split(g,bc5(g,encoded))
        if record.get('normal_frames'):
            # UV=S*R*position: orient perturbations by the inverse rotation
            # and signed axes. Magnitudes retain the authored normal strength.
            angle=M.radians(desc.get('rotation',0));c=M.cos(angle);s=M.sin(angle)
            sx,sy=[1 if v>=0 else -1 for v in desc.get('scale',[1,1])]
            xx=math(g,'ADD',math(g,'MULTIPLY',x,c*sx),math(g,'MULTIPLY',y,s*sy))
            y=math(g,'ADD',math(g,'MULTIPLY',x,-s*sx),math(g,'MULTIPLY',y,c*sy));x=xx
        return vec(g,'ADD',vec(g,'ADD',vec(g,'SCALE',tangent,x),vec(g,'SCALE',bitangent,y)),vec(g,'SCALE',normal,z))
    side_encoded=mix(g,'Native side packed-normal mix',side_factor,*values['encoded_normal'][:2])
    world_normal=vec(g,'NORMALIZE',mix(g,'Native tangent-frame top-side normal mix',wz,orient(side_encoded,side_tangent,side_bitangent,slots['PxzNormal']),orient(values['encoded_normal'][2],top_tangent,top_bitangent,slots['PyNormal'])))
    return dict(colour=blended('colour') if colour else None,rough=blended('rough'),metal=blended('metal'),normal=world_normal)
