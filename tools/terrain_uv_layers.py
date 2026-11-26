"""Restore native TBaseColorOp composition after existing projected layers."""
from material_preview_adapters import wire,math,vec
from shader_fidelity_adapters import sample,scalar_mix,mix,bc5,tangent_normal,rough_channels
REVISION='2026.11.26-terrain-uv-layers-1'

def restore(bpy,m,record,images):
 t=m.node_tree;surface=t.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
 assert surface.type=='GROUP',m.name
 original=surface.node_tree;g=original.copy();g.name='TM Restored UV detail - '+m.name;surface.node_tree=g
 if original.users==0:original.use_fake_user=True
 i=next(n for n in g.nodes if n.type=='GROUP_INPUT');o=next(n for n in g.nodes if n.type=='GROUP_OUTPUT' and n.is_active_output)
 base={key:o.inputs[key].links[0].from_socket for key in ['Base Color','Roughness','Metallic','Normal']}
 assert not any(n.name.startswith('Native TBaseColor') for n in g.nodes),'Refuse a second UV colour layer'
 # Compiled vertex passes authored UV unchanged; pixel samples t5/t6/t7
 # directly. Texture descriptor scales are editor mapping hints, not another
 # runtime transform (WhiteShore's 1/32 hint otherwise hides its whole mask).
 uv=i.outputs['BaseMaterial UV']
 d=sample(g,'Native TBaseColorOp - mesh UV only',images('TBaseColorOp'),uv)
 r=sample(g,'Restored TRoughMetal - mesh UV only',images('TRoughMetal'),uv)
 n=sample(g,'Restored TNormal - mesh UV only',images('TNormal'),uv)
 alpha=scalar_mix(g,i.outputs['Use painted vertex alpha'],i.outputs['Fallback alpha'],i.outputs['Painted alpha'])
 f=math(g,'MULTIPLY',d.outputs['Alpha'],alpha,'Source T opacity x vertex alpha')
 rough,metal=rough_channels(g,r.outputs[0],record['slots']['TRoughMetal']['usage'])
 normal=tangent_normal(g,bc5(g,n.outputs[0]),uv='BaseMaterial')
 for key,overlay in [('Base Color',d.outputs[0]),('Roughness',rough),('Metallic',metal),('Normal',normal)]:
  blended=mix(g,'Restored UV blend - '+key,f,base[key],overlay) if key in ['Base Color','Normal'] else scalar_mix(g,f,base[key],overlay)
  wire(g,vec(g,'NORMALIZE',blended) if key=='Normal' else blended,o.inputs[key])
 wire(g,f,o.inputs['Layer weight'])
 m['tm_terrain_uv_revision']=REVISION;m['tm_terrain_uv_source']=record['slots']['TBaseColorOp']['resource']
 return dict(name=m.name,group=g.name,retained_group=original.name,colour=record['slots']['TBaseColorOp']['image'],blend='TBaseColorOp.alpha * selected vertex alpha',uv='BaseMaterial')
