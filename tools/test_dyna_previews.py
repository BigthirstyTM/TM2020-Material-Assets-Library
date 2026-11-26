"""Bounded CPU render checks for the actual staged material graph."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha

source=Path(sys.argv[sys.argv.index('--')+1]).resolve()
out=Path(sys.argv[sys.argv.index('--')+2]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
source_hash=sha(source)
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=160;scene.render.resolution_y=120;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.use_compositing=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-3
world=bpy.data.worlds.new('Dyna validation world');world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.08,.08,.08,1)
scene.world=world
bpy.ops.mesh.primitive_plane_add(size=4)
plane=bpy.context.object;plane.data.uv_layers.active.name='BaseMaterial'
# A deliberately different active UV verifies the material uses BaseMaterial,
# including its emissive map, rather than accidentally taking the first map.
wrong=plane.data.uv_layers.new(name='UnrelatedUV')
for uv in wrong.data:uv.uv=(.1,.1)
plane.data.uv_layers.active_index=1
wrong.active_render=True
camera=bpy.data.cameras.new('Dyna validation camera');cam=bpy.data.objects.new('Dyna validation camera',camera)
scene.collection.objects.link(cam);scene.camera=cam;cam.location=(2.5,-1,5)
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();camera.lens=48
ld=bpy.data.lights.new('Dyna validation softbox','AREA');ld.energy=150;ld.size=5
lo=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(lo);lo.location=(0,0,5)

def render(name):
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
    # Render Result may be released by headless Blender after writing: read the
    # actual saved artifact to compare the visible pixels.
    im=bpy.data.images.load(scene.render.filepath,check_existing=False)
    pixels=list(im.pixels[:]);bpy.data.images.remove(im)
    assert pixels and all(abs(x)<1e5 for x in pixels)
    return pixels

def delta(a,b):return sum(abs(x-y) for i,(x,y) in enumerate(zip(a,b)) if i%4!=3)/(len(a)*.75)

m=bpy.data.materials['TM_WarpLightRay_Dyna_asset'];plane.data.materials.append(m)
t=m.node_tree
baseline=render('ray-native-composite')
depth=t.nodes['Dyna source Meters_Depth'].outputs[0];old_depth=depth.default_value;depth.default_value=0
flat=render('ray-zero-depth');depth.default_value=old_depth
si=t.nodes['tex_I'];old_image=si.image
black=bpy.data.images.new('Dyna validation black interior',1,1);black.pixels=(0,0,0,1);si.image=black
masked=render('ray-black-interior');si.image=old_image
scene.frame_set(45);later=render('ray-frame-45')
effects=dict(depth_mean_pixel_delta=delta(baseline,flat),interior_mean_pixel_delta=delta(baseline,masked),
  frame_mean_pixel_delta=delta(baseline,later))
assert effects['depth_mean_pixel_delta']>1e-6,effects
assert effects['interior_mean_pixel_delta']>1e-4,effects
assert effects['frame_mean_pixel_delta']<1e-6,effects
plane.data.materials[0]=bpy.data.materials['TM_SpeedometerLight_Dyna_asset']
speed=render('speedometer-dyna')
plane.data.uv_layers['BaseMaterial'].active_render=True
speed_uv=render('speedometer-explicit-base-uv')
plane.data.materials[0]=bpy.data.materials['TM_SpeedometerLight_asset']
speed_pair=render('speedometer-counterpart')
plane.data.materials[0]=bpy.data.materials['TM_WarpDetails_Dyna_asset']
details=render('warp-details-dyna')
plane.data.materials[0]=bpy.data.materials['TM_WarpDetails_WithLightmap_asset']
details_pair=render('warp-details-with-lightmap')
effects.update(speedometer_other_active_uv_delta=delta(speed,speed_uv),
  speedometer_pair_delta=delta(speed_uv,speed_pair),warp_details_pair_delta=delta(details,details_pair))
assert effects['speedometer_other_active_uv_delta']<1e-6,effects
assert effects['speedometer_pair_delta']<1e-6,effects
assert effects['warp_details_pair_delta']<1e-6,effects
assert sha(source)==source_hash,'Test mutated source file'
proof=dict(source_sha256=source_hash,render_engine='Cycles CPU',samples=8,resolution=[160,120],effects=effects,
  native_composition_responds_to_inside=True,native_depth_changes_preview=True,no_invented_time_animation=True,
  game_started=False,game_render_comparison=False)
(out/'render-verification.json').write_text(json.dumps(proof,indent=2))
print('DYNA_RENDER_CHECKS_PASSED',proof,flush=True)
