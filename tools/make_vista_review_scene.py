"""Create a non-asset Blender review scene for all 53 untested vista candidates."""
import argparse
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
for key in ['library', 'report', 'output', 'receipt']:
    p.add_argument('--' + key, type=Path, required=True)
p.add_argument('--runtime-verified', action='store_true')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
report = json.loads(a.report.read_text())
bpy.ops.wm.open_mainfile(filepath=str(a.library / 'Trackmania2020_assets.blend'), load_ui=False)
for image in bpy.data.images:
    if image.filepath and image.source == 'FILE': image.filepath = bpy.path.abspath(image.filepath)
scene = bpy.data.scenes.new('Vista materials - game load checked' if a.runtime_verified else 'Vista candidates - NOT tested in game'); bpy.context.window.scene = scene
scene.world = bpy.data.worlds.new('Vista review neutral environment'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
scene.render.engine = 'CYCLES'; scene.cycles.samples = 16
for env_index, env in enumerate(['BlueBay', 'GreenCoast', 'RedIsland', 'WhiteShore']):
    rows = [r for r in report['changes'] if r['environment'] == env]
    for i, row in enumerate(rows):
        x = (i % 4) * 36; y = -env_index * 140 - (i // 4) * 31
        physical = row['style'] == 'projected-block'
        if physical:
            bpy.ops.mesh.primitive_cube_add(size=2, location=(x, y, 6)); obj = bpy.context.object; obj.scale = (10, 10, 6)
        else:
            bpy.ops.mesh.primitive_plane_add(size=2, location=(x, y, 1)); obj = bpy.context.object; obj.scale = (12, 8, 1)
        obj.name = row['name']; obj.data.uv_layers[0].name = 'BaseMaterial'
        colors = obj.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
        for color in colors.data: color.color = (1, 1, 1, 1)
        material = bpy.data.materials[row['name']].copy(); material.asset_clear(); obj.data.materials.append(material)
        obj['vista_candidate'] = row['name']; obj['native_alias' if a.runtime_verified else 'candidate_link_NOT_enabled'] = row['candidate_alias']
        bpy.ops.object.text_add(location=(x - 12, y - 13, 1)); text = bpy.context.object
        text.data.body = row['name'].removeprefix('TM_').removesuffix('_asset'); text.data.size = .8
for loc in [(45, -40, 100), (45, -320, 100), (45, -460, 100)]:
    bpy.ops.object.light_add(type='AREA', location=loc); light = bpy.context.object; light.data.energy = 12000; light.data.size = 90
bpy.ops.object.camera_add(location=(135, -290, 510)); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 630
cam.rotation_euler = (Vector((50, -255, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); scene.camera = cam
scene['instructions'] = 'All 53 candidates are Preview only. Inspect in Material Preview or Rendered shading. No game tests performed. Source aliases are provenance only, not enabled export links.'
if a.runtime_verified:
    scene['instructions'] = 'All 53 vista materials have native source and linked-item game load checks plus user visual confirmation. Export links are enabled in the production library. Blender projection, Warp/CubeOut view effects and lighting retain documented preview limits. This scene has no asset marks.'

a.output.parent.mkdir(parents=True, exist_ok=True)
bpy.data.libraries.write(str(a.output.resolve()), {scene}, path_remap='RELATIVE', fake_user=True, compress=True)
bpy.ops.wm.open_mainfile(filepath=str(a.output.resolve()), load_ui=False)
objects = [o for o in bpy.data.objects if o.get('vista_candidate')]
assert len(objects) == 53
assert all(o.data.materials and o.data.uv_layers.get('BaseMaterial') and o.data.color_attributes.get('Color') for o in objects)
assert not any(m.asset_data for m in bpy.data.materials), 'Review scene must not duplicate library assets'
assert not any(w.asset_data for w in bpy.data.worlds)
assert all(Path(bpy.path.abspath(i.filepath)).is_file() for i in bpy.data.images if i.source == 'FILE' and i.filepath and not i.packed_file)
a.receipt.write_text(json.dumps(dict(scene=str(a.output.resolve()), assigned_materials=53, uv_and_color_attributes_verified=True,
    no_duplicate_asset_marks=True, missing_images=0, runtime_verified=a.runtime_verified), indent=2))
print('VISTA_REVIEW_SCENE_VERIFIED', len(objects), flush=True)
