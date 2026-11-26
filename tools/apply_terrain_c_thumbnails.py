"""Render approved terrain C thumbnails without changing material graphs."""
import bpy,numpy as np,json,math,sys,ast,hashlib,argparse
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser()
for key in ['library','inputs','output']:parser.add_argument('--'+key,type=Path,required=True)
parser.add_argument('--sprite-directory',type=Path,help='Directory containing the hash-checked source atlas files in the input recipe.')
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);repo=Path(__file__).resolve().parents[1];root=a.library.resolve();out=a.output.resolve();out.mkdir(exist_ok=True,parents=True);source=root/'Trackmania2020_assets.blend';REVISION='2026.11.26-terrain-icons-c-1'
sys.path.insert(0,str(repo/'tools'))
from apply_concrete_shaders import pixels,png,badge_mask
from thumbnail_preview_pixels import read_saved_preview
from apply_shader_fidelity import identity,graph,sha
before=hashlib.file_digest(source.open('rb'),'sha256').hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()};(out/'baseline.json').write_text(json.dumps(baseline))
original={prop.identifier:set(getattr(bpy.data,prop.identifier)) for prop in bpy.data.bl_rna.properties if prop.type=='COLLECTION'}
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
scene=bpy.data.scenes.new('Terrain icon option studio');bpy.context.window.scene=scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=16;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='AgX';scene.view_settings.look='None';scene.view_settings.exposure=0
w=bpy.data.worlds.new('Neutral soft environment');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);w.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=w
atlas_images={}
module=ast.parse((repo/'tools/apply_thumbnail_styles.py').read_text())
for f in module.body:
 if isinstance(f,ast.FunctionDef) and f.name in ['aim','image_material','add_cards']:exec(compile(ast.Module(body=[f],type_ignores=[]),'<thumbnail helpers>','exec'),globals())
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam
for loc,size,energy in [((-20,-25,42),38,22000),((22,12,26),30,8000),((0,-38,12),34,1500)]:
 bpy.ops.object.light_add(type='AREA',location=loc);lo=bpy.context.object;lo.data.size=size;lo.data.energy=energy;aim(lo,(0,0,2))
bpy.ops.mesh.primitive_cube_add(size=2);tile=bpy.context.object;tile.scale=(12,12,11);tile.location.z=-5;tile.data.uv_layers[0].name='BaseMaterial';bevel=tile.modifiers.new('Soft edges','BEVEL');bevel.width=.12;bevel.segments=4

# Restore the original neutral ground and physical cast shadow.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-17.5));ground=bpy.context.object
matte=bpy.data.materials.new('Original neutral ground');matte.use_nodes=True;matte.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.14,.16,1);matte.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;ground.data.materials.append(matte)

def read_png(path):
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';a=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)[::-1];result=(np.clip(a,0,1)*255+.5).astype(np.uint8);bpy.data.images.remove(im);return result

def resize(a,w,h):
 ys=np.linspace(0,a.shape[0]-1,h).astype(int);xs=np.linspace(0,a.shape[1]-1,w).astype(int);return a[ys[:,None],xs[None,:]]

inputs=json.loads(a.inputs.read_text());targets=[r for r in inputs['targets'] if r.get('sprites')];assert len(targets)==37
for row in targets:
 if not Path(row['diffuse']['path']).is_absolute():row['diffuse']['path']=str(root/row['diffuse']['path'])
 for spr in row['sprites']:
  if not Path(spr['path']).is_absolute():
   assert a.sprite_directory,'Relative atlas paths require --sprite-directory'
   spr['path']=str(a.sprite_directory.resolve()/spr['path'])
  if spr.get('sha256'):assert sha(Path(spr['path']))==spr['sha256'],spr['path']
 assert row['name'] in bpy.data.materials and Path(row['diffuse']['path']).is_file()
 for spr in row['sprites']:assert Path(spr['path']).is_file()
previews=out/'previews';previews.mkdir(exist_ok=True);changes=[]
cam.location=(35,-45,30);aim(cam,(0,0,-3));cam.data.ortho_scale=60;cam.data.shift_x=-.08;cam.data.shift_y=.04
for i,row in enumerate(targets):
 m=bpy.data.materials[row['name']];saved=pixels(m);mask=badge_mask(m);tile.data.materials.clear();tile.data.materials.append(m)
 ob,mesh,materials=add_cards(m,row['sprites'],None)
 path=previews/(m['tm_asset_id']+'.png');scene.render.filepath=str(out/'render-current.png');bpy.ops.render.render(write_still=True);rgba=read_png(out/'render-current.png')
 im=bpy.data.images.load(row['diffuse']['path'],check_existing=False);raw=np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)[::-1];rgb=np.clip(raw[:,:,:3],0,1);rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055);flat=np.concatenate([(np.clip(rgb,0,1)*255).astype(np.uint8),np.full((*rgb.shape[:2],1),255,dtype=np.uint8)],axis=2);bpy.data.images.remove(im)
 rgba[6:90,6:90,:3]=(170,177,177);box=rgba[9:87,9:87];box[:,:,:3]=(54,61,65);h,w=flat.shape[:2];scale=min(78/w,78/h);fw,fh=max(1,round(w*scale)),max(1,round(h*scale));left,top=(78-fw)//2,(78-fh)//2;box[top:top+fh,left:left+fw]=resize(flat,fw,fh)
 rgba[mask]=saved[mask];png(path,rgba)
 # Set exact preview bytes: importing PNGs through Blender can introduce rounding.
 m.preview.image_pixels=np.ascontiguousarray(rgba[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
 assert np.array_equal(pixels(m),read_saved_preview(path)),m.name
 m['tm_asset_preview_style']='Terrain C: higher shaded block with source foliage, separate base-diffuse inset and physical ground shadow; original studio plus weak front fill.'
 m['tm_thumbnail_style_revision']=REVISION;m['tm_thumbnail_geometry_note']='Representative source-sprite cards on a 24x24x22 preview block; source diffuse inset preserves image aspect. Not native plant placement or density.'
 bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
 for material in materials:bpy.data.materials.remove(material)
 changes.append(dict(name=m.name,id=m['tm_asset_id'],style='terrain-C',diffuse=row['diffuse'],sprites=len(row['sprites'])))
 (out/'progress.json').write_text(json.dumps(dict(revision=REVISION,done=i+1,total=len(targets),material=m.name)))
 print('TERRAIN_ICON_COMPLETE',i+1,len(targets),m.name,flush=True)
# Remove the entire disposable studio and its helper datablocks.
bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene)
for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.scenes.remove(scene)
for prop in ['materials','worlds','meshes','cameras','lights','images','node_groups']:
 collection=getattr(bpy.data,prop)
 for block in list(collection):
  if block not in original[prop]:collection.remove(block,do_unlink=True)
for key,x in assets.items():assert graph(x)==baseline[key]['graph']
assert sha(source)==before
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report=dict(revision=REVISION,source_sha256=before,staged_sha256=sha(out/source.name),targets=[r['name'] for r in changes],changes=changes,counts={'terrain-C':len(changes)},preserved=[m.name for m in bpy.data.materials if m.asset_data and m.name not in {r['name'] for r in changes}])
(out/'build-report.json').write_text(json.dumps(report,indent=2));print('TERRAIN_ICONS_STAGED',flush=True)
