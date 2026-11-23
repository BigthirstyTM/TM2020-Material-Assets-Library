"""Build the reviewed local projection/source refresh with matched previews."""
import bpy,argparse,json,sys,warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings('ignore',category=DeprecationWarning)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,badge_mask,png
from projection_refresh_adapters import projected,REVISION
import deco_ice_adapters
from secondary_preview_adapters import apply as secondary

p=argparse.ArgumentParser()
for key in ['library','inputs','secondary','output']:p.add_argument('--'+key,type=Path,required=True)
p.add_argument('--resume',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
data=json.loads(a.inputs.read_text());sec=json.loads(a.secondary.read_text());source=root/'Trackmania2020_assets.blend'
assert sha(source)==data['source_sha256']
targets=[r['name'] for r in data['materials']]+[r['name'] for r in sec['targets']]
if not a.resume:
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
 baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
 (out/'baseline.json').write_text(json.dumps(baseline,indent=2))
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
 files={};cache={};resolved=[]
 for path in (root/'Textures').rglob('*'):
  if path.is_file():files.setdefault(path.name.lower(),[]).append(path)
 def loader(record):
  def load(slot):
   d=record['slots'].get(slot,{});ref=d.get('image')
   if not ref:return None
   filename=Path(ref.replace('\\','/')).name;env=record['source'].split('/')[0];direct=root/'Textures'/env/filename
   candidates=[direct] if direct.is_file() else files.get(filename.lower(),[])
   assert candidates and len({sha(x) for x in candidates})==1,('Resolve image provenance',record['name'],slot,filename)
   path=min(candidates,key=lambda x:len(str(x)));space='sRGB' if d.get('usage')=='Color' and slot not in ['PyX2','PyH2','PyHx2'] else 'Non-Color'
   key=(str(path),space)
   if key not in cache:
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=space;im.alpha_mode='CHANNEL_PACKED';cache[key]=im
   resolved.append(dict(material=record['name'],role=slot,path=str(path),sha256=sha(path),colour_space=space));return cache[key]
  return load
 deco_ice_adapters.projected=projected
 for r in data['materials']:
  m=bpy.data.materials[r['name']];deco_ice_adapters.terrain(bpy,m,r,loader(r));m['tm_projection_refresh_revision']=REVISION
  m['tm_projection_refresh_limit']='Source-selected independent texture transforms, pre-decode packed side-normal blend and surface-tangent normal frames. Existing top/side angular interpolation and mapped Blender coordinates remain preview adapters.'
 for r in sec['targets']:
  m=bpy.data.materials[r['name']];secondary(bpy,m,r,loader(r));m['tm_projection_refresh_revision']=REVISION
 for r in data['coverage']:
  m=bpy.data.materials[r['name']];m['tm_exact_shader_resource']=r['shader'];m['tm_exact_shader_chain']=json.dumps(r['chain']);m['tm_exact_shader_provenance']='Explicit native material ancestor reference chain; resolved offline, not inferred by replacing Material with Shader in a filename.'
 report=dict(revision=REVISION,source_sha256=data['source_sha256'],targets=targets,projected_targets=[r['name'] for r in data['materials']],secondary_targets=[r['name'] for r in sec['targets']],new_source_links=[r for r in data['coverage'] if r['newly_resolved']],resolved_slots=resolved,support_files=[])
 (out/'build-report.json').write_text(json.dumps(report,indent=2));bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'graph-stage.blend'),compress=True,relative_remap=False)
else:
 bpy.ops.wm.open_mainfile(filepath=str(out/'graph-stage.blend'),load_ui=False);report=json.loads((out/'build-report.json').read_text())
 baseline=json.loads((out/'baseline.json').read_text())

scene=bpy.data.scenes.new('Projection review thumbnail studio');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
w=bpy.data.worlds.new('Projection studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.46,1);w.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=w
bpy.ops.mesh.primitive_cube_add(size=28);cube=bpy.context.object
bevel=cube.modifiers.new('Rounded preview edges','BEVEL');bevel.width=3;bevel.segments=3
bpy.ops.object.camera_add(location=(37,-48,38));camera=bpy.context.object;camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=48;scene.camera=camera
bpy.ops.object.light_add(type='AREA',location=(-20,-20,38));light=bpy.context.object;light.data.energy=24000;light.data.size=25;light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
thumbs=out/'renders';thumbs.mkdir(exist_ok=True);previews=out/'previews';previews.mkdir(exist_ok=True)
checks=[]
for idx,name in enumerate(targets):
 m=bpy.data.materials[name];old=pixels(m);mask=badge_mask(m);cube.data.materials.clear();cube.data.materials.append(m);path=thumbs/(name+'.png')
 if not(a.resume and path.exists()):scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 with bpy.context.temp_override(id=m):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
 fresh=pixels(m);fresh[mask]=old[mask];m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
 assert np.array_equal(pixels(m)[mask],old[mask]);png(previews/(m['tm_asset_id']+'.png'),fresh)
 m['tm_asset_preview_source']=REVISION;m['tm_asset_preview_style']='Rendered material on a rounded three-dimensional sample, showing top/side projection; established badges preserved.'
 checks.append(dict(name=name,badge_pixels_preserved=True));(out/'progress.json').write_text(json.dumps(dict(phase='thumbnails',done=idx+1,total=len(targets),material=name)))
 print('THUMBNAIL',idx+1,len(targets),name,flush=True)
for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
 for asset in coll:
  if not asset.asset_data:continue
  key=asset.bl_rna.identifier+':'+asset.name;current=identity(asset);previous=baseline[key]['identity'].copy()
  if asset.name in targets:current.pop('icon');previous.pop('icon')
  assert current==previous,('Identity changed',key)
  if asset.name not in targets:assert graph(asset)==baseline[key]['graph'],('Unrelated graph changed',key)
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene);bpy.data.scenes.remove(scene);bpy.data.worlds.remove(w)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report.update(staged_sha256=sha(out/source.name),badge_checks=checks);(out/'build-report.json').write_text(json.dumps(report,indent=2))
print('PROJECTION_REFRESH_STAGED',flush=True)
