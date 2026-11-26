"""Select an identification inset from the material's active colour graph."""
import bpy,numpy as np

def ancestors(socket,seen=None):
 seen=set() if seen is None else seen
 node=socket.node
 if node in seen:return seen
 seen.add(node)
 for inp in node.inputs:
  for link in inp.links:ancestors(link.from_socket,seen)
 return seen

def active_diffuse(material):
 p=material.node_tree.nodes['Principled BSDF'];assert p.inputs['Base Color'].is_linked,material.name
 surface=p.inputs['Base Color'].links[0].from_node
 if surface.type=='GROUP':
  output=next(n for n in surface.node_tree.nodes if n.type=='GROUP_OUTPUT' and n.is_active_output)
  reachable=set()
  for link in output.inputs['Base Color'].links:ancestors(link.from_socket,reachable)
  choices=[n for n in reachable if n.type=='TEX_IMAGE' and n.image]
  t=[n for n in choices if n.name.startswith('Native TBaseColor - mesh UV only')]
  use=surface.inputs.get('Use painted vertex alpha');fallback=surface.inputs.get('Fallback alpha')
  enabled=not (use and fallback and use.default_value==0 and fallback.default_value==0)
  if t and enabled:
   assert len(t)==1;return t[0].image,dict(role='TBaseColor: active UV decoration',node=t[0].name,group=surface.name)
  py=[n for n in choices if n.name=='Native PyBaseColor']
  assert len(py)==1,(material.name,[n.name for n in choices])
  return py[0].image,dict(role='PyBaseColor: active projected top',node=py[0].name,group=surface.name)
 reachable=ancestors(p.inputs['Base Color'].links[0].from_socket)
 n=material.node_tree.nodes.get('tex_D');assert n and n in reachable and n.image,material.name
 return n.image,dict(role='BaseColor: active legacy projected top',node=n.name,group=None)

def source_pixels(image):
 # Read encoded RGB once. Do not apply another sRGB conversion or multiply by
 # the source alpha: alpha is a layer mask, not transparency of this RGB inset.
 im=bpy.data.images.load(bpy.path.abspath(image.filepath),check_existing=False)
 try:
  im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';w,h=im.size
  assert w and h,image.name
  buffer=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(buffer);raw=buffer.reshape(h,w,4)[::-1]
  rgba=(np.clip(raw,0,1)*255+.5).astype(np.uint8);rgba[:,:,3]=255
  return rgba
 finally:bpy.data.images.remove(im)

def place_inset(rgba,source):
 rgba[6:90,6:90,:3]=(170,177,177);box=rgba[9:87,9:87];box[:,:,:3]=(54,61,65)
 h,w=source.shape[:2];scale=min(78/w,78/h);fw,fh=max(1,round(w*scale)),max(1,round(h*scale));left,top=(78-fw)//2,(78-fh)//2
 ys=np.linspace(0,h-1,fh).astype(int);xs=np.linspace(0,w-1,fw).astype(int)
 box[top:top+fh,left:left+fw]=source[ys[:,None],xs[None,:]]
 return rgba
