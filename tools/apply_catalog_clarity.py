"""Stage thumbnail clarification, duplicate example-asset cleanup and flag quarantine."""
import argparse,json,sys,uuid,re
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,png,badge_mask

p=argparse.ArgumentParser()
for key in ['library','inputs','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
data=json.loads(a.inputs.read_text());source=root/'Trackmania2020_assets.blend';assert sha(source)==data['source_sha256']
revision=data['revision'];bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
(out/'baseline.json').write_text(json.dumps(baseline,indent=2))
for image in bpy.data.images:
 if image.source=='FILE' and image.filepath:image.filepath=bpy.path.abspath(image.filepath)
helper_images=[];cache={}
def rgba(path):
 if path not in cache:
  im=bpy.data.images.load(path,check_existing=False);helper_images.append(im);im.alpha_mode='CHANNEL_PACKED'
  w,h=im.size;arr=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(arr);cache[path]=np.clip(arr.reshape(h,w,4)[::-1]*255,0,255).astype(np.uint8)
 return cache[path]
def resize(image,w,h):
 ys=np.linspace(0,image.shape[0]-1,h);xs=np.linspace(0,image.shape[1]-1,w);y0=ys.astype(int);x0=xs.astype(int);y1=np.minimum(y0+1,image.shape[0]-1);x1=np.minimum(x0+1,image.shape[1]-1)
 fy=(ys-y0)[:,None,None];fx=(xs-x0)[None,:,None]
 return np.clip((image[y0[:,None],x0[None,:]]*(1-fx)+image[y0[:,None],x1[None,:]]*fx)*(1-fy)+(image[y1[:,None],x0[None,:]]*(1-fx)+image[y1[:,None],x1[None,:]]*fx)*fy,0,255).astype(np.uint8)
def overlay(dst,src,left,top):
 h,w=src.shape[:2];alpha=src[:,:,3:4].astype(float)/255;dst[top:top+h,left:left+w,:3]=(src[:,:,:3]*alpha+dst[top:top+h,left:left+w,:3]*(1-alpha)).astype(np.uint8)
def contain(src,w,h):
 scale=min(w/src.shape[1],h/src.shape[0]);return resize(src,max(1,round(src.shape[1]*scale)),max(1,round(src.shape[0]*scale)))
def crop_alpha(src):
 yy,xx=np.where(src[:,:,3]>12)
 return src[yy.min():yy.max()+1,xx.min():xx.max()+1] if len(xx) else src
renders=out/'previews';renders.mkdir(exist_ok=True);changes=[]
for r in data['targets']:
 if r['style']=='sphere':continue
 m=bpy.data.materials[r['name']];old=pixels(m);fresh=np.full((256,256,4),(55,62,65,255),dtype=np.uint8)
 raw=rgba(r['diffuse']['path'])
 if r['style']=='sprite-cutout':raw=crop_alpha(raw)
 image=contain(raw,256,256)
 if r['style']=='sprite-cutout':overlay(fresh,image,(256-image.shape[1])//2,(256-image.shape[0])//2)
 else:
  image=image.copy();image[:,:,3]=255;fresh[(256-image.shape[0])//2:(256+image.shape[0])//2,(256-image.shape[1])//2:(256+image.shape[1])//2]=image
 for idx,s in enumerate(r['sprites']):
  atlas=rgba(s['path']);e=s['entry'];h,w=atlas.shape[:2]
  x0=round(int(e['U05'])/int(e['U03'])*w);x1=round((int(e['U05'])+int(e['U07']))/int(e['U03'])*w)
  y0=h-round((int(e['U06'])+int(e['U08']))/int(e['U04'])*h);y1=h-round(int(e['U06'])/int(e['U04'])*h)
  sprite=crop_alpha(atlas[y0:y1,x0:x1]);sprite=contain(sprite,94,112);assert sprite[:,:,3].max()>30,(r['name'],s['entry']['U01'])
  overlay(fresh,sprite,10+idx*103,246-sprite.shape[0])
 mask=badge_mask(m);fresh[mask]=old[mask]
 m.preview_ensure().image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
 assert np.array_equal(pixels(m)[mask],old[mask]);png(renders/(r['id']+'.png'),fresh)
 m['tm_asset_preview_style']='Native diffuse texture with source atlas vegetation cutouts; existing badges retained.' if r['sprites'] else 'Native sprite alpha silhouette; existing badges retained.' if r['style']=='sprite-cutout' else 'Flat base diffuse texture; existing badges retained.'
 m['tm_asset_preview_source']=r['diffuse']['path'];m['tm_catalog_clarity_revision']=revision
 if r['sprites']:m['tm_thumbnail_sprite_sources']=json.dumps([{k:s[k] for k in ['atlas_source','model','dataset','entry']} for s in r['sprites']])
 changes.append(dict(name=m.name,style=r['style'],badges_preserved=True))
for im in helper_images:bpy.data.images.remove(im)
cache.clear()

scene=bpy.data.scenes.new('Custom sphere thumbnail studio');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Custom thumbnail studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.46,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=14);sphere=bpy.context.object;sphere.data.uv_layers[0].name='BaseMaterial'
for face in sphere.data.polygons:face.use_smooth=True
bpy.ops.object.camera_add(location=(31,-39,24));camera=bpy.context.object;camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=34;scene.camera=camera
bpy.ops.object.light_add(type='AREA',location=(-20,-20,38));light=bpy.context.object;light.data.energy=24000;light.data.size=25;light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
for idx,r in enumerate(x for x in data['targets'] if x['style']=='sphere'):
 m=bpy.data.materials[r['name']];old=pixels(m);sphere.data.materials.clear();sphere.data.materials.append(m);path=renders/(r['id']+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 with bpy.context.temp_override(id=m):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
 fresh=pixels(m);mask=badge_mask(m);fresh[mask]=old[mask];m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist();png(path,fresh)
 assert np.array_equal(pixels(m)[mask],old[mask]);m['tm_asset_preview_style']='Rendered Custom material on a smooth sphere; existing badges retained.';m['tm_catalog_clarity_revision']=revision
 changes.append(dict(name=m.name,style='sphere',badges_preserved=True));(out/'progress.json').write_text(json.dumps(dict(phase='custom spheres',done=idx+1,total=28,material=m.name)))
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene);bpy.data.scenes.remove(scene);bpy.data.worlds.remove(world)

flag=bpy.data.materials[data['quarantine']];reason=data['quarantine_reason']
flag['tm_flag_previous_export_state']=json.dumps({k:str(flag[k]) for k in ['link','MAT_PROPS_AS_JSON','tm_game_material_path','tm_export_binding_status','tm_current_export_status','tm_current_runtime_status'] if k in flag})
flag['link']='';flag['tm_game_material_path']='';props=json.loads(flag.get('MAT_PROPS_AS_JSON','{}'));props['name']=flag.name;props['link']='';flag['MAT_PROPS_AS_JSON']=json.dumps(props)
flag['tm_game_material_exportable']=False;flag['tm_preview_only_reason']=reason;flag['tm_export_binding_status']='preview_only_reported_runtime_issue';flag['tm_current_export_status']='Preview only - user-reported load/placement crash';flag['tm_current_runtime_status']='user_reported_crash_not_isolated';flag['tm_current_export_evidence']=reason
catalog_path='Trackmania2020/08 Preview only/Reported runtime issues';catalog_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'tm2020-assets/'+catalog_path));flag.asset_data.catalog_id=catalog_id
flag.asset_data.description='Preview only. '+reason+' Use ItemFlagNoAnim for a static alternative.'
if 'Preview only' not in {t.name for t in flag.asset_data.tags}:flag.asset_data.tags.new('Preview only')
cats=(root/'blender_assets.cats.txt').read_bytes();cats+=('\n'+catalog_id+':'+catalog_path+':Reported runtime issues\n').encode();(out/'blender_assets.cats.txt').write_bytes(cats)
lines=(root/'MaterialLib.txt').read_bytes().splitlines(keepends=True);start=next(i for i,l in enumerate(lines) if re.match(rb'\s*DMaterial\(Stadium_ItemFlag\)',l));end=next(i for i in range(start+1,len(lines)) if re.match(rb'\s*D(?:Material|Library)\(',lines[i]));(out/'MaterialLib.txt').write_bytes(b''.join(lines[:start]+lines[end:]))
for key,asset in assets.items():
 assert graph(asset)==baseline[key]['graph'],('Unexpected shader change',key)
 assert asset.get('tm_asset_effect_badges','')==baseline[key]['badges']
 old=baseline[key]['identity'].copy();now=identity(asset)
 if asset.name in {r['name'] for r in data['targets']}:old.pop('icon');now.pop('icon')
 if asset==flag:
  for k in ['catalog','description','tags','export']:old.pop(k);now.pop(k)
 assert now==old,('Unexpected identity change',key)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report=dict(revision=revision,source_sha256=data['source_sha256'],staged_sha256=sha(out/source.name),targets=[r['name'] for r in data['targets']],changes=changes,quarantine=flag.name,quarantine_catalog_id=catalog_id,quarantine_catalog_path=catalog_path,support_files=[])
for ex in data['examples']:
 path=root/ex['path'];assert sha(path)==ex['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
 before={m.name:graph(m) for m in bpy.data.materials};cleared=[]
 for prop in bpy.data.bl_rna.properties:
  if prop.type!='COLLECTION':continue
  for asset in getattr(bpy.data,prop.identifier):
   if getattr(asset,'asset_data',None):cleared.append(asset.name);asset.asset_clear()
 for image in bpy.data.images:
  if image.source=='FILE' and image.filepath:
   image.filepath=bpy.path.abspath(image.filepath)
   if not image.packed_file:assert Path(image.filepath).is_file(),image.filepath
 bpy.ops.file.pack_all()
 for m in bpy.data.materials:
  assert graph(m)==before[m.name]
  m.use_fake_user=True
 dest=out/ex['path'];dest.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True,relative_remap=False)
 report['support_files'].append(dict(path=ex['path'],sha256=sha(dest),previous_sha256=ex['sha256'],cleared=cleared))
for name in ['MaterialLib.txt','blender_assets.cats.txt']:report['support_files'].append(dict(path=name,sha256=sha(out/name),previous_sha256=sha(root/name)))
(out/'build-report.json').write_text(json.dumps(report,indent=2));print('CATALOG_CLARITY_STAGED',len(changes),flush=True)
