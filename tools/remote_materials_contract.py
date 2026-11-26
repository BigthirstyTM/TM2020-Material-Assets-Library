"""Stable contracts for remote material files, including shader/driver state."""
import hashlib,json
import bpy
from apply_shader_fidelity import identity
from build_remote_pilot import trees,value

def rna(item,seen=None):
 seen=set() if seen is None else seen
 key=item.as_pointer()
 if key in seen:return {'reference':item.bl_rna.identifier,'name':getattr(item,'name','')}
 seen=seen|{key};data={}
 for prop in item.bl_rna.properties:
  name=prop.identifier
  if name in {'rna_type','id_data','node','preview'} or (prop.is_readonly and prop.type!='POINTER'):continue
  try:v=getattr(item,name)
  except (AttributeError,RuntimeError):continue
  if isinstance(v,bpy.types.ID):data[name]=[v.bl_rna.identifier,v.name]
  elif isinstance(v,bpy.types.bpy_struct):data[name]=rna(v,seen)
  elif prop.type=='COLLECTION':data[name]=[rna(x,seen) for x in v]
  else:
   try:data[name]=value(v)
   except (TypeError,ValueError):continue
 try:data['custom_properties']=value(dict(item.items()))
 except (TypeError,AttributeError):pass
 return data

def animation(block):
 ad=block.animation_data
 if ad is None:return None
 # Current library uses drivers and no keyframed actions. Refuse silent reuse
 # if a future source introduces an action until its full contract is defined.
 assert ad.action is None,('Keyframed action requires contract support',block.name)
 assert not ad.nla_tracks,('NLA requires contract support',block.name)
 return dict(settings=rna(ad),drivers=[dict(settings=rna(fc),driver=rna(fc.driver),
  variables=[dict(settings=rna(v),targets=[rna(t) for t in v.targets]) for v in fc.driver.variables],
  keyframes=[rna(k) for k in fc.keyframe_points],modifiers=[rna(m) for m in fc.modifiers]) for fc in ad.drivers])

def contract(material,image_hashes,image_node_types=('TEX_IMAGE',)):
 groups={}
 for tree in sorted(trees(material.node_tree),key=lambda x:x.name):
  groups[tree.name]=dict(nodes=[dict(properties=rna(n),inputs=[rna(s) for s in n.inputs],outputs=[rna(s) for s in n.outputs]) for n in tree.nodes],
   links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links),
   interface=[rna(x) for x in tree.interface.items_tree],properties=value(dict(tree.items())),animation=animation(tree))
 images={n.image for t in trees(material.node_tree) for n in t.nodes if n.type in image_node_types and n.image}
 return dict(identity=identity(material),properties=rna(material),animation=animation(material),groups=groups,
  images={im.name:dict(hash=image_hashes[im.name],source=im.source,colour_space=im.colorspace_settings.name,
    alpha_mode=im.alpha_mode,generated_type=im.generated_type,generated_color=list(im.generated_color),size=list(im.size)) for im in sorted(images,key=lambda x:x.name)})

def fingerprint(data):return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
