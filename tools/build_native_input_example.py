"""Create an editable, source-textured vertex-alpha example (no exported item)."""
import argparse
from pathlib import Path
import sys
import bpy

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--render',type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
root=args.source.resolve();target=args.output.resolve();target.parent.mkdir(parents=True,exist_ok=True)
names=['TM_BlueBay_TransitionRocksToLand_asset','TM_GreenCoast_CliffTransitionToGrass_asset','TM_RedIsland_RockToDirt_asset','TM_WhiteShore_WaterShoreRocky_asset']
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
with bpy.data.libraries.load(str(root/'Trackmania2020_assets.blend'),link=False) as (src,dst):dst.materials=names.copy()
scene=bpy.context.scene

def label(text,x,y,size=.5):
    curve=bpy.data.curves.new(text,'FONT');curve.body=text;curve.size=size;curve.extrude=0
    ob=bpy.data.objects.new(text,curve);scene.collection.objects.link(ob);ob.location=(x,y,.05)
    material=bpy.data.materials.get('Example label')
    if material is None:
        material=bpy.data.materials.new('Example label');material.use_nodes=True
        p=material.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.05,.05,.05,1)
    ob.data.materials.append(material)

for row,name in enumerate(names):
    for column,alpha in enumerate((0,.5,1)):
        bpy.ops.mesh.primitive_plane_add(size=4,location=(column*5+9,(3-row)*5,0))
        ob=bpy.context.object;ob.name=name.removeprefix('TM_').removesuffix('_asset')+' alpha '+str(alpha)
        ob.data.materials.append(bpy.data.materials[name]);ob.data.uv_layers[0].name='BaseMaterial';ob.data.uv_layers.new(name='LightMap',do_init=True)
        color=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
        for value in color.data:value.color=(1,1,1,alpha)
        ob.data.color_attributes.active_color=color
    label(name.removeprefix('TM_').removesuffix('_asset').replace('_','\n'),-3,(3-row)*5,.48)
for column,alpha in enumerate((0,.5,1)):label('Color alpha = '+str(alpha),column*5+7,18,.52)
label('Native transition layers',-3,20,.9)
label('Alpha 0: projected base. Alpha 1: UV overlay through texture alpha.',-3,-3.3,.44)
world=bpy.data.worlds.new('Neutral example lighting');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.8,.8,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
bpy.ops.object.light_add(type='AREA',location=(8,5,15));bpy.context.object.data.energy=1500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=10
bpy.ops.object.camera_add(location=(9,8.5,35));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=29
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
bpy.context.preferences.filepaths.save_version=0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True,relative_remap=True)
if args.render:
    scene.render.image_settings.file_format='PNG';scene.render.filepath=str(args.render.resolve());bpy.ops.render.render(write_still=True)
print('NATIVE_INPUT_EXAMPLE_WRITTEN',str(target),flush=True)
