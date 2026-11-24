"""Render approved A/B/C asset previews without changing production shaders."""
import argparse,json,math,sys,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,png,badge_mask
from thumbnail_preview_pixels import read_saved_preview
from thumbnail_lighting import without_studio_reflections

REVISION='2026.11.24-thumbnail-styles-2'
p=argparse.ArgumentParser()
for k in ['library','sprites','output']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--sample',action='store_true');p.add_argument('--only-style',choices=['A','B','C']);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
root=a.library.resolve();out=a.output.resolve();out.mkdir(exist_ok=True,parents=True);renders=out/'previews';renders.mkdir(exist_ok=True)
source=root/'Trackmania2020_assets.blend';source_hash=sha(source)
assert source_hash=='3d22c92a767c3439a494a5694477451090799e606d0fa1ed0d29d561b82da8d1','Reconcile current installed source before rendering.'
sprite_inputs=json.loads(a.sprites.read_text());routes={r['name']:r for r in sprite_inputs['targets'] if r['sprites']}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
if not a.sample:(out/'baseline.json').write_text(json.dumps(baseline,indent=2))
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
original={prop.identifier:set(getattr(bpy.data,prop.identifier)) for prop in bpy.data.bl_rna.properties if prop.type=='COLLECTION'}
helpers=[];atlas_images={}
def aim(o,target=(0,0,0)):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.data.scenes.new('Approved thumbnail studio');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.use_denoising=True;scene.cycles.seed=31;scene.cycles.transparent_max_bounces=16
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.render.film_transparent=False
matte_compositor=without_studio_reflections(scene)
world=bpy.data.worlds.new('Neutral thumbnail studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);scene.world=world
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam
lights=[]
for loc,size in [((-20,-25,42),38),((22,12,26),30)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.size=size;aim(light);lights.append(light)
bpy.ops.mesh.primitive_plane_add(size=27);panel=bpy.context.object;panel.data.uv_layers[0].name='BaseMaterial'
bpy.ops.mesh.primitive_cube_add(size=2);tile=bpy.context.object;tile.scale=(12,12,6);tile.data.uv_layers[0].name='BaseMaterial';bev=tile.modifiers.new('Soft edges','BEVEL');bev.width=.12;bev.segments=4
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=13);sphere=bpy.context.object;sphere.data.uv_layers[0].name='BaseMaterial'
for face in sphere.data.polygons:face.use_smooth=True
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-15));ground=bpy.context.object
matte=bpy.data.materials.new('Neutral matte for preview fixture');matte.use_nodes=True
matte.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.14,.16,1);matte.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;ground.data.materials.append(matte)
scratch=bpy.data.materials.new('Preview pixel reader');card_objects=[]
def diffuse_image(m):
 n=m.node_tree.nodes.get('tex_D') if m.node_tree else None
 return n.image if n and n.type=='TEX_IMAGE' else None
def cutout_source(m):
 name=m.name.lower()
 if not any(t in name for t in ['veget','trees2','forestsprite','grassfence','decalgrass']):return None
 if any(t in name for t in ['bark','trunk']):return None
 im=diffuse_image(m)
 if not im or not im.size[0] or im.channels<4:return None
 raw=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(raw);alpha=raw[3::4]
 if np.mean(alpha<.2)>.05 and np.mean(alpha>.5)>.01:return im
 return None
def image_material(im):
 material=bpy.data.materials.new('Source sprite preview only');material.use_nodes=True;n=material.node_tree.nodes;n.clear();l=material.node_tree.links
 tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP'
 diffuse=n.new('ShaderNodeBsdfDiffuse');l.new(tex.outputs['Color'],diffuse.inputs['Color'])
 transparent=n.new('ShaderNodeBsdfTransparent');cut=n.new('ShaderNodeMath');cut.operation='GREATER_THAN';cut.inputs[1].default_value=.35;l.new(tex.outputs['Alpha'],cut.inputs[0])
 mix=n.new('ShaderNodeMixShader');l.new(cut.outputs[0],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(diffuse.outputs[0],mix.inputs[2]);output=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],output.inputs['Surface'])
 return material
def add_cards(m,sprites,direct):
 definitions=[]
 for r in sprites:
  path=r['path'];assert Path(path).is_file(),path
  if path not in atlas_images:
   im=bpy.data.images.load(path,check_existing=False);im.alpha_mode='CHANNEL_PACKED';atlas_images[path]=im
  e=r['entry'];u=int(e['U05'])/int(e['U03']);v=int(e['U06'])/int(e['U04']);du=int(e['U07'])/int(e['U03']);dv=int(e['U08'])/int(e['U04'])
  definitions.append((atlas_images[path],(u,v,du,dv),du/dv))
 if direct:definitions=[(direct,(0,0,1,1),direct.size[0]/direct.size[1])]
 cards=[]
 for j,(im,uvbox,ratio) in enumerate(definitions):
  mat=image_material(im);cards.append(mat)
 positions=[(-7,-6),(-1,-7),(6,-5),(-8,1),(-1,0),(7,2),(-6,7),(1,7),(7,8)] if not direct else [(-5,1),(5,4)]
 vertices=[];faces=[];coords=[];indices=[]
 for idx,(x,y) in enumerate(positions):
  j=idx%len(definitions);im,(u,v,du,dv),ratio=definitions[j];height=(4.8 if not direct else 10);width=min(8,height*ratio);center=Vector((x,y,6.03))
  for yaw in [math.atan2(35,45),math.atan2(35,45)+math.pi/2]:
   side=Vector((math.cos(yaw),math.sin(yaw),0))*width/2;up=Vector((0,0,height));start=len(vertices)
   vertices.extend([center-side,center+side,center+side+up,center-side+up]);faces.append((start,start+1,start+2,start+3));coords.append([(u,v),(u+du,v),(u+du,v+dv),(u,v+dv)]);indices.append(j)
 mesh=bpy.data.meshes.new('Native sprite thumbnail mesh');mesh.from_pydata(vertices,[],faces)
 for mat in cards:mesh.materials.append(mat)
 uv=mesh.uv_layers.new(name='UVMap')
 for face,uvs,index in zip(mesh.polygons,coords,indices):
  face.material_index=index
  for loop,coord in zip(face.loop_indices,uvs):uv.data[loop].uv=coord
 ob=bpy.data.objects.new('Vegetation standing on preview tile',mesh);scene.collection.objects.link(ob)
 return ob,mesh,cards
preserve={'Runtime input symbol','Collision function symbol','Technical source view','Name label','Native editor icon','Animation source frame'}
targets=[];skipped=[]
for m in bpy.data.materials:
 if not m.asset_data:continue
 direct=cutout_source(m)
 if m.name.startswith('TM_Custom'):style='C'
 elif m.name in routes or direct:style='B'
 elif m.get('tm_current_preview_type') in preserve or m.get('tm_asset_preview_type') in ['Collision only','Invisible / NotCollidable']:skipped.append(m.name);continue
 else:style='A'
 targets.append(dict(name=m.name,id=m['tm_asset_id'],style=style,direct_image=direct.name if direct else None))
overall_counts={s:sum(r['style']==s for r in targets) for s in 'ABC'}
if a.only_style:
 skipped.extend(r['name'] for r in targets if r['style']!=a.only_style);targets=[r for r in targets if r['style']==a.only_style]
sample_names=['TM_BlueBay_CliffPxz_asset','TM_PlatformIce_DecoHill2_asset','TM_Water_asset','TM_GlassWaterWall_asset','TM_RedIsland_RockToDirt_asset','TM_BlueBay_Deco_asset','TM_GreenCoast_Grass_asset','TM_WhiteShore_Land_asset','TM_CustomGlass_asset','TM_PlatformDirt_DecoHill2_asset','TM_RedIsland_VegetGrassDry_asset']
if a.sample:targets=[r for r in targets if r['name'] in sample_names]
targets.sort(key=lambda r:(0 if r['name'] in sample_names else 1,r['name']))
(out/('sample-targets.json' if a.sample else 'targets.json')).write_text(json.dumps(dict(revision=REVISION,source_sha256=source_hash,targets=targets,preserved=skipped),indent=2))
changes=[];start=time.monotonic()
for idx,row in enumerate(targets):
 m=bpy.data.materials[row['name']];style=row['style'];old=pixels(m);mask=badge_mask(m);path=renders/(row['id']+'.png');proof_path=path.with_suffix('.json')
 key=sha(a.sprites)+source_hash+style+REVISION
 if path.is_file() and proof_path.is_file() and json.loads(proof_path.read_text()).get('cache_key')==key and json.loads(proof_path.read_text()).get('sha256')==sha(path):
  cached=read_saved_preview(path);m.preview_ensure().image_pixels=np.ascontiguousarray(cached[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
 else:
  for ob in [panel,tile,sphere]:ob.hide_render=True;ob.data.materials.clear()
  active=panel if style=='A' else tile if style=='B' else sphere;active.hide_render=False;active.data.materials.append(matte if row['direct_image'] else m)
  scene.compositing_node_group=matte_compositor if style=='A' else None
  scene.cycles.use_denoising=style!='A'
  scene.cycles.samples=16 if style=='A' else 24;scene.view_settings.exposure=-.1 if style=='A' else 0
  scene.view_settings.look='AgX - Medium High Contrast' if style=='A' else 'None'
  world.node_tree.nodes['Background'].inputs[1].default_value=.65
  lights[0].data.energy=22000;lights[1].data.energy=8000
  cam.location=(0,-7,43) if style=='A' else (35,-45,36) if style=='B' else (29,-39,26)
  aim(cam,(0,0,3) if style=='B' else (0,0,0));cam.data.ortho_scale=30 if style=='A' else 44 if style=='B' else 32
  created=None
  if style=='B':created=add_cards(m,routes.get(m.name,{}).get('sprites',[]),bpy.data.images.get(row['direct_image']) if row['direct_image'] else None)
  scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  with bpy.context.temp_override(id=m):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
  if created:
   ob,mesh,materials=created;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
   for mat in materials:bpy.data.materials.remove(mat)
 fresh=pixels(m);fresh[mask]=old[mask];m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist();png(path,fresh)
 assert np.array_equal(pixels(m)[mask],old[mask]);proof_path.write_text(json.dumps(dict(cache_key=key,sha256=sha(path),style=style)))
 m['tm_asset_preview_style']={'A':'A: softer top view, medium high contrast, direct studio-lamp reflections removed from the thumbnail.','B':'B: shaded tile with source vegetation standing on its top surface.','C':'C: Custom material rendered on a smooth sphere.'}[style]
 m['tm_thumbnail_style_revision']=REVISION
 if style=='B':m['tm_thumbnail_geometry_note']='Representative source-sprite cards on a preview tile; not native placement or density.'
 changes.append(row);(out/'progress.json').write_text(json.dumps(dict(revision=REVISION,sample=a.sample,done=idx+1,total=len(targets),material=m.name,style=style,elapsed_seconds=round(time.monotonic()-start))))
 if idx%20==0:print('THUMBNAILS',idx+1,len(targets),m.name,flush=True)
# Remove only studio/helper datablocks created by this process.
bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene)
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.scenes.remove(scene)
for prop in ['materials','worlds','meshes','cameras','lights','images','node_groups']:
 collection=getattr(bpy.data,prop)
 for x in list(collection):
  if x not in original[prop]:collection.remove(x,do_unlink=True)
for key,x in assets.items():
 assert graph(x)==baseline[key]['graph'],key
 assert x.get('tm_asset_effect_badges','')==baseline[key]['badges'],key
 before=baseline[key]['identity'].copy();after=identity(x)
 if x.name in {r['name'] for r in changes}:before.pop('icon');after.pop('icon')
 assert before==after,key
assert sha(source)==source_hash
report=dict(revision=REVISION,source_sha256=source_hash,targets=[r['name'] for r in changes],changes=changes,preserved=skipped,counts={s:sum(r['style']==s for r in changes) for s in 'ABC'},overall_counts=overall_counts,support_files=[])
if not a.sample:
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False);report['staged_sha256']=sha(out/source.name)
(out/('sample-report.json' if a.sample else 'build-report.json')).write_text(json.dumps(report,indent=2));print('THUMBNAIL_STYLES_READY',json.dumps(report['counts']),flush=True)
