"""Reviewed source-local light-tube and opt-in masked-Hue preview operations."""
from material_preview_adapters import node,wire,math,vec,combine
from shader_fidelity_adapters import interface,sample,mix
from deco_ice_adapters import hue,layout

def apply(bpy,m,r,images):
 t=m.node_tree;p=t.nodes['Principled BSDF']
 def image(record,slot):return images(slot)
 if 'LightTube' in r['name']:
  scale=lambda key:r['parameters'][key]['values'][0][0]
  g,i,o=interface(bpy,'P2 Native light-tube emission',[
   ('BaseMaterial UV','NodeSocketVector',None),('Geometry normal','NodeSocketVector',None),('To camera','NodeSocketVector',None),
   ('SelfIllumScale','NodeSocketFloat',scale('SelfIllumScale')),('SelfIllumScaleRefract','NodeSocketFloat',scale('SelfIllumScaleRefract')),
   ('Preview global HDR gain','NodeSocketFloat',1),('Preview night multiplier','NodeSocketFloat',1)], [('Emission','NodeSocketColor')])
  ordinary=sample(g,'Source SelfIllum',image(r,'SelfIllum'),i.outputs['BaseMaterial UV'])
  refracted=sample(g,'Source SelfIllumRefract',image(r,'SelfIllumRefract'),i.outputs['BaseMaterial UV'])
  angle=math(g,'MINIMUM',math(g,'MAXIMUM',vec(g,'DOT_PRODUCT',vec(g,'NORMALIZE',i.outputs['Geometry normal']),vec(g,'NORMALIZE',i.outputs['To camera'])),0),1)
  gradient=sample(g,'Source 1D RefractGradient',image(r,'RefractGradient'),combine(g,angle,.5));gradient.extension='EXTEND'
  light=vec(g,'ADD',vec(g,'SCALE',ordinary.outputs[0],i.outputs['SelfIllumScale']),vec(g,'SCALE',vec(g,'MULTIPLY',gradient.outputs[0],refracted.outputs[0]),i.outputs['SelfIllumScaleRefract']))
  if scale('NightOnly_SelfIllum')>.5:light=vec(g,'SCALE',light,i.outputs['Preview night multiplier'])
  wire(g,vec(g,'SCALE',light,i.outputs['Preview global HDR gain']),o.inputs[0]);layout(g)
  n=node(t,'ShaderNodeGroup','P2 recovered light-tube emission');n.node_tree=g
  uv=node(t,'ShaderNodeUVMap','Prototype BaseMaterial UV');uv.uv_map='BaseMaterial';wire(t,uv.outputs[0],n.inputs['BaseMaterial UV'])
  geo=node(t,'ShaderNodeNewGeometry','Prototype geometry');wire(t,geo.outputs['Normal'],n.inputs['Geometry normal'])
  # Position is transformed to camera space; reverse the vector to point at camera.
  camera=node(t,'ShaderNodeVectorTransform','World position in camera');camera.vector_type='POINT';camera.convert_from='WORLD';camera.convert_to='CAMERA';wire(t,geo.outputs['Position'],camera.inputs[0])
  to_world=node(t,'ShaderNodeVectorTransform','Camera direction in world');to_world.vector_type='VECTOR';to_world.convert_from='CAMERA';to_world.convert_to='WORLD'
  wire(t,vec(t,'SCALE',camera.outputs[0],-1),to_world.inputs[0]);wire(t,to_world.outputs[0],n.inputs['To camera'])
  wire(t,n.outputs[0],p.inputs['Emission Color']);wire(t,1,p.inputs['Emission Strength'])
  m['tm_p2_limit']='Recovered material-local emission branch. Preview global HDR gain=1; scene lighting/activation are not inferred. Small native refraction scale=0 retained.'
 else:
  original=p.inputs['Base Color'].links[0].from_socket
  g,i,o=interface(bpy,'P2 source masked hue', [('Original colour','NodeSocketColor',(1,1,1,1)),('UV','NodeSocketVector',None),('Explicit preview target','NodeSocketColor',(.1,.4,.8,1)),('Enable recovered hue preview','NodeSocketFloat',0)], [('Colour','NodeSocketColor')])
  mask=sample(g,'Source BaseColorHueMask',image(r,'BaseColorHueMask'),i.outputs['UV'])
  weight=math(g,'MULTIPLY',mask.outputs['Alpha'],i.outputs['Enable recovered hue preview'])
  wire(g,mix(g,'Native mask alpha and target chroma',weight,i.outputs['Original colour'],hue(g,mask.outputs[0],i.outputs['Explicit preview target'])),o.inputs[0]);layout(g)
  n=node(t,'ShaderNodeGroup','P2 opt-in recovered masked hue');n.node_tree=g;wire(t,original,n.inputs['Original colour'])
  uv=node(t,'ShaderNodeUVMap','Prototype BaseMaterial UV');uv.uv_map='BaseMaterial';wire(t,uv.outputs[0],n.inputs['UV']);wire(t,n.outputs[0],p.inputs['Base Color'])
  m['tm_p2_limit']='Exact local mask/chroma formula; runtime palette selection not established. Disabled by default. Explicit preview target is illustrative, not a recovered game default.'
 m['tm_secondary_preview_revision']='2026.11.23-projection-sources-1'
 return m
