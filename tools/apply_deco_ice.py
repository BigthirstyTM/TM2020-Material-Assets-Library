"""Stage and render source-informed Deco/PlatformIce corrections."""
import bpy,sys,json,hashlib,argparse,math,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from deco_ice_adapters import terrain,layered_ice,uv_surface,REVISION

p=argparse.ArgumentParser()
for k in ['source','inputs','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
source=root/'Trackmania2020_assets.blend';sourcehash=sha(source)
assert sourcehash=='9ee4fd07c15531c912ae9022a3cdafac17d9a55506d555a9a10a53e3629f00c5','Unexpected installed revision'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
records=json.loads(a.inputs.read_text());targets=[r['name'] for r in records]
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
paths=list((root/'Textures').rglob('*'));index={}
for path in paths:
 if path.is_file():index.setdefault(path.name.lower(),[]).append(path)
resolved=[];image_cache={}
def loader(record):
 def load(slot):
  d=record['slots'].get(slot,{});image=d.get('image')
  if not image:return None
  filename=Path(image.replace('\\','/')).name
  env=record['source'].split('/')[0];resource=d['resource'].replace('\\','/');explicit=image.replace('\\','/')
  for name in ['Stadium','BlueBay','GreenCoast','RedIsland','WhiteShore']:
   if explicit.lower().startswith(name.lower()+'/'):env=name;break
   if resource.lower().startswith(name.lower()+'/'):env=name
  path=root/'Textures'/env/filename
  if not path.is_file():
   candidates=index.get(filename.lower(),[])
   assert candidates and (len(candidates)==1 or len({sha(x) for x in candidates})==1),('Ambiguous or missing image',record['name'],slot,env,filename,[str(x) for x in candidates]);path=sorted(candidates,key=lambda x:len(str(x)))[0]
  # Macro values multiply by two: byte 128 is neutral .5, not sRGB .216.
  space='sRGB' if d.get('usage')=='Color' and slot not in ['PyX2','PyHx2'] else 'Non-Color'
  key=(str(path),space)
  if key not in image_cache:
   im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=space;im.alpha_mode='CHANNEL_PACKED';image_cache[key]=im
  im=image_cache[key]
  resolved.append(dict(material=record['name'],slot=slot,path=str(path),array_selector=d.get('array_selector')))
  return im
 return load
changes=[]
for record in records:
 m=bpy.data.materials[record['name']];load=loader(record);shader=record['shader']
 if 'pypxztlayered' in shader:r=layered_ice(bpy,m,record,load)
 elif 'pypxz' in shader:r=terrain(bpy,m,record,load)
 else:r=uv_surface(m,record,load)
 changes.append(r);print('ADAPTED',r,flush=True)

# Dedicated preview scene: authored UV 0..1 on a 32 m panel, lit consistently.
scene=bpy.data.scenes.new('Deco Ice Thumbnail Studio');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Deco preview studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.46,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
bpy.ops.mesh.primitive_plane_add(size=32);panel=bpy.context.object;panel.data.uv_layers[0].name='BaseMaterial'
bpy.ops.object.camera_add(location=(0,-15,43));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=36;scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-12,-10,25));light=bpy.context.object;light.data.energy=20000;light.data.shape='DISK';light.data.size=18
light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
thumbs=out/'thumbnails';thumbs.mkdir(exist_ok=True)
badge_checks=[]
for name in targets:
 m=bpy.data.materials[name];preview=m.preview_ensure();old=np.asarray(preview.image_pixels[:],dtype=np.int64).astype(np.uint32).view(np.uint8).reshape(256,256,4)[::-1].copy()
 panel.data.materials.clear();panel.data.materials.append(m);path=thumbs/(name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(str(path),check_existing=False);pixels=np.asarray(im.pixels[:],dtype=np.float32).reshape(256,256,4)
 # Blender image pixels are linear, while preview pixels are display encoded.
 # Composite preserved badge pixels through a temporary sRGB image conversion.
 badge=json.loads(m.get('tm_asset_effect_badges','[]'));mask=np.zeros((256,256),dtype=bool)
 for idx in range(len(badge)):
  yy,xx=np.mgrid[:32,:32];rounded=np.hypot(np.maximum(abs(xx-15.5)-10,0),np.maximum(abs(yy-15.5)-10,0))<=5.5
  left=256-6-32-idx*36;mask[6:38,left:left+32]|=rounded
 # PNG composite via stdlib codec helper supplied by Pillow in catalog Python later;
 # use preview packed bytes directly, keeping the freshly rendered corners.
 with bpy.context.temp_override(id=m):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
 fresh=np.asarray(m.preview.image_pixels[:],dtype=np.int64).astype(np.uint32).view(np.uint8).reshape(256,256,4)[::-1].copy()
 fresh[mask]=old[mask]
 packed=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1)
 m.preview.image_pixels=packed.view(np.int32).tolist()
 check=np.asarray(m.preview.image_pixels[:],dtype=np.int64).astype(np.uint32).view(np.uint8).reshape(256,256,4)[::-1]
 assert np.array_equal(check[mask],old[mask]),name
 badge_checks.append(dict(name=name,badge_pixels=int(mask.sum()),preserved=True));bpy.data.images.remove(im)
 m['tm_asset_preview_style']='Rendered native-layer Blender preview; existing effect badges retained.'
 m['tm_asset_preview_source']='Native role adapters '+REVISION
 print('THUMBNAIL',name,flush=True)

for k,x in assets.items():
 current=identity(x);previous=baseline[k]['identity'].copy()
 if x.name in targets:current.pop('icon');previous.pop('icon')
 assert current==previous,('Asset metadata changed',k)
 assert x.get('tm_asset_effect_badges','')==baseline[k]['badges']
 if x.name not in targets:assert graph(x)==baseline[k]['graph'],('Unrelated graph',k)
assert sha(source)==sourcehash
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
# Remove the render fixture and its material references before saving the library.
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene);bpy.data.scenes.remove(scene);bpy.data.worlds.remove(world)
(out/'baseline.json').write_text(json.dumps(baseline,indent=2))
report=dict(revision=REVISION,source_sha256=sourcehash,targets=targets,changes=changes,resolved_slots=resolved,support_files=[],badge_checks=badge_checks)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report['staged_sha256']=sha(out/source.name);(out/'build-report.json').write_text(json.dumps(report,indent=2));print('DECO_ICE_STAGED',flush=True);bpy.ops.wm.quit_blender()
