"""Disposable timeline previews. Run Blender with --factory-startup; no library files are saved."""
import argparse,bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--export',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--kind',choices=['water','animation','parallax'],required=True);p.add_argument('--trial',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);sys.path.insert(0,str(Path(__file__).resolve().parent))
from family_thumbnail_material import preview_copy
out=a.output.resolve();root=a.export.resolve()
report=json.loads((root/'build-report.json').read_text())
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.seed=17
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=192;scene.render.resolution_y=192;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.fps=24;scene.view_settings.view_transform='Standard'
scene.world=bpy.data.worlds.new('Gallery studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.55,.65,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
def point(obj,at):obj.rotation_euler=(Vector(at)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,0,40));cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam
kind=a.kind;name={'water':'TM_Water_asset','animation':'TM_TurboRoulette_Sign_asset','parallax':'TM_Stadium_Ad155Screen_asset'}[kind]
row=next(x for x in report['materials'] if x['name']==name)
with bpy.data.libraries.load(str(root/'host'/row['path']),link=False) as (src,dst):dst.materials=[name]
material=dst.materials[0]
if kind!='water':
 material,groups,fixture=preview_copy(material,flat=True)
 def unfreeze(tree):
  for node in tree.nodes:
   socket=node.inputs.get('Manual Frame (-1 = timeline)')
   if socket:socket.default_value=-1
   if node.type=='GROUP' and node.node_tree:unfreeze(node.node_tree)
 unfreeze(material.node_tree)
size=32 if kind=='water' else 2
bpy.ops.mesh.primitive_plane_add(size=size);obj=bpy.context.object;obj.data.uv_layers[0].name='BaseMaterial';obj.data.materials.append(material)
cam.data.ortho_scale=size
if kind=='parallax':
 # Centre-crop the 1.55:1 screen for a square, edge-to-edge website example.
 for loop in obj.data.uv_layers[0].data:
  loop.uv.x=.5+(loop.uv.x-.5)/1.55
 cam.data.ortho_scale=1.65
if kind=='water':
 cam.location=(0,-14,36);point(cam,(0,0,0));cam.data.ortho_scale=28
 for loc,power,scale in [((-12,8,18),2800,14),((15,-5,22),1800,10)]:
  bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='RECTANGLE';light.data.size=scale;light.data.size_y=scale/3;point(light,(0,0,0))
 bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-3));floor=bpy.context.object
 floor_mat=bpy.data.materials.new('Basin');floor_mat.diffuse_color=(.06,.24,.3,1);floor.data.materials.append(floor_mat)
folder=out/kind;folder.mkdir(exist_ok=True)
frames=([1,10,28] if a.trial else list(range(1,37))) if kind=='parallax' else ([1,13,25] if a.trial else list(range(1,25)))
for frame in frames:
 if kind=='parallax':
  angle=math.radians(32)*math.sin((frame-1)*2*math.pi/36)
  cam.location=(4*math.sin(angle),0,4*math.cos(angle));cam.rotation_euler=(0,angle,0)
 scene.frame_set(frame);scene.render.filepath=str(folder/f'{frame:03}.png');bpy.ops.render.render(write_still=True)
print('GALLERY_RENDER_COMPLETE',kind,flush=True)
