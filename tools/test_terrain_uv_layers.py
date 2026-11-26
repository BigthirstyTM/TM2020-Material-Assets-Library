"""Render restored layers against their retained original projection on mesh UVs."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from material_preview_adapters import wire,node

p=argparse.ArgumentParser()
for k in ['source','state']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--output',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);state=a.state.resolve();out=a.output.resolve() if a.output else state/'render-tests';out.mkdir(exist_ok=True);source=a.source.resolve()
report=json.loads((state/'build-report.json').read_text());assert sha(source)==report['staged_sha256'];bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
scene=bpy.data.scenes.new('UV layer regression studio');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=128;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='16';scene.view_settings.view_transform='Raw';scene.view_settings.look='None'
bpy.ops.mesh.primitive_plane_add(size=24,location=(0,0,6));plane=bpy.context.object;plane.data.uv_layers[0].name='BaseMaterial'
col=plane.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
bpy.ops.object.camera_add(location=(0,0,40));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=24;scene.camera=cam

def render(m,filename):
 plane.data.materials.clear();plane.data.materials.append(m);path=out/filename;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';buffer=np.empty(128*128*4,dtype=np.float32);im.pixels.foreach_get(buffer);bpy.data.images.remove(im);return buffer.reshape(128,128,4)[:,:,:3].copy()

results=[]
for row in report['changes']:
 source_m=bpy.data.materials[row['name']];m=source_m.copy();t=m.node_tree;g=t.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
 emission=node(t,'ShaderNodeEmission','Regression colour without lighting');wire(t,g.outputs['Base Color'],emission.inputs['Color']);output=next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);wire(t,emission.outputs[0],output.inputs['Surface'])
 restored=g.node_tree;g.node_tree=bpy.data.node_groups[row['retained_group']];baseline=render(m,source_m['tm_asset_id']+'-before.png');g.node_tree=restored
 g.inputs['Use painted vertex alpha'].default_value=0;g.inputs['Fallback alpha'].default_value=0;zero=render(m,source_m['tm_asset_id']+'-off.png')
 g.inputs['Fallback alpha'].default_value=1;full=render(m,source_m['tm_asset_id']+'-after.png')
 g.inputs['Fallback alpha'].default_value=.5;half=render(m,source_m['tm_asset_id']+'-half.png')
 errors=dict(disabled=float(np.max(np.abs(zero-baseline))),half=float(np.max(np.abs(half-(zero+full)*.5))))
 assert errors['disabled']<.0001,(m.name,errors)
 # Raw 16-bit emissive output preserves the linear interpolation equation.
 assert errors['half']<.001,(m.name,errors)
 difference=float(np.mean(np.abs(full-baseline)));assert difference>.0001,(m.name,'UV layer remains invisible',difference)
 g.inputs['Use painted vertex alpha'].default_value=1
 for alpha,expected in [(0,zero),(.5,half),(1,full)]:
  for c in col.data:c.color=(1,1,1,alpha)
  painted=render(m,source_m['tm_asset_id']+f'-vertex-{alpha}.png');err=float(np.max(np.abs(painted-expected)));assert err<.0001,(m.name,alpha,err)
 results.append(dict(name=source_m.name,mean_colour_change=difference,errors=errors,vertex_alpha_equivalence=True))
 bpy.data.materials.remove(m);(out/'progress.json').write_text(json.dumps(dict(done=len(results),total=15,material=source_m.name)));print('UV_RENDER_CHECK_PASSED',len(results),source_m.name,difference,flush=True)
assert sha(source)==report['staged_sha256']
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(source),blender=bpy.app.version_string,materials=len(results),renders=len(results)*7,results=results),indent=2));print('ALL_TERRAIN_UV_RENDER_CHECKS_PASSED',flush=True)
