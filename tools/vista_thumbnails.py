"""Reusable vista thumbnail studio; saved material graphs are not modified."""
import json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from apply_concrete_shaders import png
from apply_shader_fidelity import identity

def render_previews(out, changes, data):
    # Render disposable thumbnail fixtures. Existing assets are never used as
    # templates, so no saved graph or preview is edited.
    originals = {prop: set(getattr(bpy.data, prop)) for prop in ['materials', 'worlds', 'meshes', 'cameras', 'lights', 'images', 'node_groups']}
    old_scene = bpy.context.window.scene
    scene = bpy.data.scenes.new('Vista candidate thumbnail studio'); bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 12; scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 2
    scene.render.resolution_x = scene.render.resolution_y = 256; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'None'
    scene.world = bpy.data.worlds.new('Vista thumbnail neutral environment'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.3, .3, .3, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
    def aim(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.camera_add(location=(35, -45, 30)); cam = bpy.context.object; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 60; aim(cam, (0, 0, -3)); scene.camera = cam
    for loc, size, energy in [((-20, -25, 42), 38, 22000), ((22, 12, 26), 30, 8000), ((0, -38, 12), 34, 1500)]:
        bpy.ops.object.light_add(type='AREA', location=loc); light = bpy.context.object; light.data.size = size; light.data.energy = energy; aim(light, (0, 0, 0))
    bpy.ops.mesh.primitive_cube_add(size=2); tile = bpy.context.object; tile.scale = (12, 12, 11); tile.location.z = -5; tile.data.uv_layers[0].name = 'BaseMaterial'
    colors = tile.data.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='CORNER')
    for c in colors.data: c.color = (1, 1, 1, 1)
    bevel = tile.modifiers.new('Thumbnail soft edges', 'BEVEL'); bevel.width = .12; bevel.segments = 3
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -17.5)); ground = bpy.context.object
    matte = bpy.data.materials.new('Vista thumbnail ground'); matte.use_nodes = True
    matte.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.12, .14, .16, 1); matte.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1; ground.data.materials.append(matte)
    bpy.ops.mesh.primitive_plane_add(size=2); panel = bpy.context.object; panel.data.uv_layers[0].name = 'BaseMaterial'
    previews = out / 'previews'; previews.mkdir(exist_ok=True)
    for n, change in enumerate(changes):
        m = bpy.data.materials[change['name']]
        physical = change['style'] == 'projected-block'
        tile.hide_render = not physical; panel.hide_render = physical; ground.hide_render = not physical
        if physical:
            tile.data.materials.clear(); tile.data.materials.append(m); cam.location = (35, -45, 30); cam.data.ortho_scale = 60; aim(cam, (0, 0, -3))
        else:
            copy = m.copy(); copy.asset_clear(); tt = copy.node_tree; pp = tt.nodes['Principled BSDF']; surface = tt.nodes['Material Output']
            emit = tt.nodes.new('ShaderNodeEmission'); emit.inputs['Strength'].default_value = 1
            if pp.inputs['Base Color'].is_linked: tt.links.new(pp.inputs['Base Color'].links[0].from_socket, emit.inputs['Color'])
            else: emit.inputs['Color'].default_value = pp.inputs['Base Color'].default_value
            final = emit.outputs[0]
            if pp.inputs['Alpha'].is_linked:
                transparent = tt.nodes.new('ShaderNodeBsdfTransparent'); blend = tt.nodes.new('ShaderNodeMixShader')
                tt.links.new(pp.inputs['Alpha'].links[0].from_socket, blend.inputs[0]); tt.links.new(transparent.outputs[0], blend.inputs[1]); tt.links.new(final, blend.inputs[2]); final = blend.outputs[0]
            tt.links.new(final, surface.inputs['Surface']); panel.data.materials.clear(); panel.data.materials.append(copy)
            im = bpy.data.images[change['primary_image']]; ratio = im.size[0] / im.size[1]
            panel.scale = (13 * min(1, ratio), 13 * min(1, 1 / ratio), 1)
            cam.location = (0, 0, 40); cam.data.ortho_scale = 26; aim(cam, (0, 0, 0))
            scene.view_settings.view_transform = 'Standard'
        scene.render.filepath = str(out / 'current.png'); bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(str(out / 'current.png'), check_existing=False); im.colorspace_settings.name = 'Non-Color'
        pixels = np.asarray(im.pixels[:], dtype=np.float32).reshape(256, 256, 4)[::-1]
        rgba = (np.clip(pixels, 0, 1) * 255 + .5).astype(np.uint8); bpy.data.images.remove(im)
        if physical:
            from terrain_thumbnail_inset import source_pixels, place_inset
            place_inset(rgba, source_pixels(bpy.data.images[change['primary_image']]))
        if json.loads(m['tm_asset_effect_badges']):
            badge_path = Path(__file__).resolve().parents[1] / 'docs/images/vista-world-projection.png'
            badge = bpy.data.images.load(str(badge_path), check_existing=False); badge.colorspace_settings.name = 'Non-Color'
            pixels = np.asarray(badge.pixels[:], dtype=np.float32).reshape(badge.size[1], badge.size[0], 4)[::-1]
            bpy.data.images.remove(badge)
            ys = np.linspace(0, pixels.shape[0] - 1, 32).astype(int); xs = np.linspace(0, pixels.shape[1] - 1, 32).astype(int)
            pixels = pixels[ys[:, None], xs[None, :]]; alpha = pixels[:, :, 3:4]
            box = rgba[6:38, 218:250]; box[:, :, :3] = np.rint(pixels[:, :, :3] * 255 * alpha + box[:, :, :3] * (1 - alpha)).astype(np.uint8)
        preview_path = previews / (m['tm_asset_id'] + '.png'); png(preview_path, rgba)
        m.preview_ensure().image_size = (256, 256)
        m.preview.image_pixels = np.ascontiguousarray(rgba[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
        m['tm_asset_preview_style'] = change['style']; m['tm_thumbnail_style_revision'] = data['revision']
        change['icon_sha256'] = identity(m)['icon']; change['preview_file'] = str(preview_path); change['render_rgb_mean'] = float(rgba[:, :, :3].mean())
        if not physical:
            panel.data.materials.clear(); bpy.data.materials.remove(copy)
        scene.view_settings.view_transform = 'AgX'
        (out / 'progress.json').write_text(json.dumps(dict(done=n + 1, total=len(changes), material=m.name)))
        print('VISTA_ICON_RENDERED', n + 1, len(changes), m.name, flush=True)
    bpy.context.window.scene = old_scene
    for obj in list(scene.objects): bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(scene)
    for prop, original in originals.items():
        coll = getattr(bpy.data, prop)
        for block in list(coll):
            if block not in original: coll.remove(block, do_unlink=True)
