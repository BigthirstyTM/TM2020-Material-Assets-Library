"""Build source-backed Preview only vista candidates and matched thumbnails."""
import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity, graph, sha
from apply_concrete_shaders import png
from material_preview_adapters import node, wire, math, vec, combine, setup_transparency
from shader_fidelity_adapters import sample, split, bc5, rough_channels, tangent_normal, mix, scalar_mix
from deco_ice_adapters import transform, hue, layout
import deco_ice_adapters
from projection_refresh_adapters import projected
from dyna_preview_adapters import source_si_uv

deco_ice_adapters.projected = projected


def main():
    p = argparse.ArgumentParser()
    for key in ['library', 'inputs', 'output']:
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = a.library.resolve(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    data = json.loads(a.inputs.read_text()); source = root / 'Trackmania2020_assets.blend'
    assert sha(source) == data['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    assets = {x.bl_rna.identifier + ':' + x.name: x for c in [bpy.data.materials, bpy.data.worlds, bpy.data.node_groups] for x in c if x.asset_data}
    baseline = {k: dict(identity=identity(x), graph=graph(x), badges=x.get('tm_asset_effect_badges', '')) for k, x in assets.items()}
    (out / 'baseline.json').write_text(json.dumps(baseline))
    for image in bpy.data.images:
        if image.source == 'FILE' and image.filepath:
            image.filepath = bpy.path.abspath(image.filepath)
    images = {}
    catalogs = (root / 'blender_assets.cats.txt').read_text(encoding='utf-8')
    cat_ids = {}
    for env in ['BlueBay', 'GreenCoast', 'RedIsland', 'WhiteShore']:
        path = 'Trackmania2020/08 Preview only/Vista candidates/' + env
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'tm2020-vista-candidates/' + env))
        assert path not in catalogs
        catalogs += f'\n{cid}:{path}:Vista candidates - {env}\n'; cat_ids[env] = cid
    changes = []
    for r in data['materials']:
        assert r['name'] not in bpy.data.materials, r['name']
        m = bpy.data.materials.new(r['name']); m.use_nodes = True; t = m.node_tree; bsdf = t.nodes['Principled BSDF']
        m.asset_mark(); m.asset_data.catalog_id = cat_ids[r['environment']]
        limitations = ['Untested in Trackmania; candidate source alias is disabled for export. Blender projection, normals and lighting are preview adapters.']
        def load(slot):
            desc = r['slots'].get(slot) or {}; path = desc.get('path')
            if not path:
                return None
            key = (path, desc.get('usage') == 'Color')
            if key not in images:
                image = bpy.data.images.load(path, check_existing=False)
                image.name = 'Vista source ' + Path(path).name + (' color' if key[1] else ' data')
                image.colorspace_settings.name = 'sRGB' if key[1] else 'Non-Color'
                image.alpha_mode = 'CHANNEL_PACKED'; images[key] = image
            return images[key]
        # Resolve all bitmap slots, including currently inactive shader branches.
        for slot in r['slots']:
            load(slot)
        uv = node(t, 'ShaderNodeUVMap', 'BaseMaterial UV'); uv.uv_map = 'BaseMaterial'
        primary = None
        if 'PyBaseColor' in r['slots'] or 'PxzBaseColor' in r['slots']:
            slots = r['slots']
            if 'PyBaseColor' not in slots:
                # The source is a side-projected + mesh-UV shader. Its side
                # texture is projected on the neutral top only for the preview.
                for role in ['BaseColor', 'RoughMetal', 'Normal']:
                    slots['Py' + role] = dict(slots['Pxz' + role])
                limitations.append('Side-projection shader: neutral top preview reuses its own side texture; native top/slope behavior still requires the vista mesh.')
            for prefix in ['Py', 'Pxz']:
                for role in ['RoughMetal', 'Normal']:
                    slots.setdefault(prefix + role, dict(usage='36', scale=[1, 1], translation=[0, 0], rotation=0))
            if 'TBaseColorBlend' in slots:
                slots['TBaseColor'] = slots['TBaseColorBlend']
            if r.get('array_angles'):
                for prefix in ['Py', 'Pxz']:
                    fields = slots[prefix + 'BaseColor']['array_fields']
                    if any(fields.get(k, 0) for k in ['U04', 'U05', 'U08', 'U09', 'U10']) or (fields['U02'], fields['U03']) != (fields['U06'], fields['U07']):
                        limitations.append(prefix + ': array matrix fields are retained; preview uses the recorded U02/U03 dimensions. Full native matrix reconstruction is pending.')
            deco_ice_adapters.terrain(bpy, m, r, load)
            control = t.nodes['Deco native layer controls']
            if r['options'].get('VertexAlpha') == 1:
                control.inputs['Use painted vertex alpha'].default_value = 1
                limitations.append('UV transition uses source texture alpha multiplied by Color vertex alpha. Missing Color attributes use Blender defaults.')
            else:
                control.inputs['Use painted vertex alpha'].default_value = 0
            if 'TOpacity' in slots:
                opacity = sample(t, 'Native TOpacity mesh mask', load('TOpacity'), uv.outputs[0])
                wire(t, opacity.outputs['Alpha'], bsdf.inputs['Alpha']); setup_transparency(m)
                limitations.append('Projected decal masked by its own TOpacity alpha; native decal depth/offset is not reproduced.')
            primary = load('TBaseColorOp') or load('TBaseColor') or load('PyBaseColor')
            # Decal silhouettes are clearer on a flat panel at the mask's
            # authored aspect ratio, rather than wrapped around a cube.
            style = 'flat-layered' if 'TOpacity' in slots else 'projected-block'
            if 'TOpacity' in slots: primary = load('TOpacity')
        elif 'PyDiffuse' in r['slots']:
            # Source Warp ground uses its own two projected diffuse samplers.
            geo = node(t, 'ShaderNodeNewGeometry', 'Warp source world coordinates')
            x, y, z = split(t, geo.outputs['Position']); nx, ny, nz = split(t, geo.outputs['Normal'])
            top_desc = r['slots']['PyDiffuse']; side_desc = r['slots']['PxzDiffuse']
            top = sample(t, 'Native PyDiffuse', load('PyDiffuse'), transform(t, combine(t, x, y), top_desc))
            setting = r['parameters']['PxzScaleTrans'][0]
            side_uv = vec(t, 'ADD', vec(t, 'MULTIPLY', combine(t, x, z), (setting[0], setting[1], 1)), (setting[2], setting[2], 0))
            side = sample(t, 'Native PxzDiffuse', load('PxzDiffuse'), side_uv)
            f = math(t, 'POWER', math(t, 'ABSOLUTE', nz), 4)
            wire(t, mix(t, 'Warp top and side preview', f, side.outputs[0], top.outputs[0]), bsdf.inputs['Base Color'])
            bsdf.inputs['Roughness'].default_value = 1
            primary = load('PyDiffuse'); style = 'projected-block'
            limitations.append('Warp ground: static source diffuse projection with recorded PxzScaleTrans. Native horizon/view warping and tangent normals remain unimplemented; this is not a working Warp replacement.')
        else:
            desc = r['slots'].get('BaseColorOp') or r['slots'].get('BaseColor'); assert desc, r['name']
            role = 'BaseColorOp' if 'BaseColorOp' in r['slots'] else 'BaseColor'
            color = sample(t, 'Native ' + role, load(role), uv.outputs[0])
            rough = sample(t, 'Native RoughMetal', load('RoughMetal'), uv.outputs[0])
            normal = sample(t, 'Native Normal', load('Normal'), uv.outputs[0])
            rm, metal = rough_channels(t, rough.outputs[0], r['slots']['RoughMetal']['usage'])
            wire(t, rm, bsdf.inputs['Roughness']); wire(t, metal, bsdf.inputs['Metallic'])
            wire(t, tangent_normal(t, bc5(t, normal.outputs[0])), bsdf.inputs['Normal'])
            base_color = color.outputs[0]
            target = (r['parameters'].get('BaseColorTarget') or [[0, 0, 0]])[0]
            if load('BaseColorHueMask') and any(target[:3]):
                mask = sample(t, 'Native BaseColorHueMask', load('BaseColorHueMask'), uv.outputs[0])
                base_color = mix(t, 'Source masked target color', mask.outputs['Alpha'], base_color, hue(t, mask.outputs[0], target[:3]))
            if 'BaseColorOp' in r['slots']:
                # This alpha is the surface/interior mask, not object opacity.
                base_color = vec(t, 'SCALE', base_color, color.outputs['Alpha'])
                if load('SI') and load('MulInside'):
                    si_uv = uv.outputs[0]
                    if load('Height') and all(k in r['parameters'] for k in ['Meters_Depth', 'Meters_UV', 'RefractIndex', 'DoubleRefract']):
                        si_uv = source_si_uv(t, si_uv, rough.outputs[0], normal.outputs[0], load('Height'), {k: v[0] for k, v in r['parameters'].items()})
                    si = sample(t, 'Native SI', load('SI'), si_uv)
                    inside = sample(t, 'Native MulInside', load('MulInside'), uv.outputs[0])
                    emission = vec(t, 'MULTIPLY', vec(t, 'SCALE', inside.outputs[0], inside.outputs['Alpha']), si.outputs[0])
                    emission = vec(t, 'SCALE', emission, math(t, 'SUBTRACT', 1, color.outputs['Alpha']))
                    wire(t, emission, bsdf.inputs['Emission Color'])
                    bsdf.inputs['Emission Strength'].default_value = r['parameters'].get('SelfIllum_Scale', [[0]])[0][0]
                limitations.append('CubeOut/DispIn: source surface, Hue and SI depth branch. Native foreground/secondary interior activation and view-dependent cubemap behavior are not fully reconstructed.')
            wire(t, base_color, bsdf.inputs['Base Color']); primary = load(role); style = 'flat-layered'
        assert primary and primary.size[0] and primary.size[1]
        m['tm_asset_id'] = r['id']; m['tm_vista_candidate_revision'] = data['revision']
        m['tm_vista_source'] = r['source']; m['tm_vista_shader'] = r['shader']; m['tm_vista_candidate_alias'] = r['alias']
        m['tm_native_parameters'] = json.dumps(r['parameters']); m['tm_vista_selectors'] = json.dumps(r['selectors'])
        m['tm_vista_options'] = json.dumps(r['options']); m['tm_vista_slots'] = json.dumps(r['slots'])
        m['tm_preview_only'] = True; m['tm_game_material_exportable'] = False; m['tm_vista_runtime_status'] = 'Not tested in game'
        m['tm_current_export_status'] = 'Preview only - untested vista candidate; candidate link retained as provenance only'
        m['tm_preview_limitations'] = json.dumps(limitations); m['tm_asset_effect_badges'] = json.dumps(['world_projection'] if style == 'projected-block' or 'TOpacity' in r['slots'] else [])
        m['MAT_PROPS_AS_JSON'] = json.dumps(dict(name=m.name, link=''))
        m.asset_data.description = ('Preview only - vista candidate, not tested in game. Source: ' + r['source'] + '. ' + ' '.join(limitations))[:1023]
        for tag in ['Preview only', 'Vista candidate', r['environment'], 'Evidence: decoded shader', 'Not tested in game']:
            m.asset_data.tags.new(tag)
        layout(t)
        changes.append(dict(name=m.name, id=r['id'], source=r['source'], shader=r['shader'], candidate_alias=r['alias'], environment=r['environment'],
            catalog='Trackmania2020/08 Preview only/Vista candidates/' + r['environment'], catalog_id=cat_ids[r['environment']],
            style=style, primary_image=primary.name, primary_path=primary.filepath, limitations=limitations))
        print('VISTA_MATERIAL_BUILT', len(changes), len(data['materials']), m.name, flush=True)

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
    for key, asset in assets.items():
        assert identity(asset) == baseline[key]['identity'], ('Existing identity changed', key)
        assert graph(asset) == baseline[key]['graph'], ('Existing graph changed', key)
    assert len([m for m in bpy.data.materials if m.asset_data]) == 1172
    # Relative image paths are written for the installed root, not the staging
    # directory. Verification and installation resolve against that intended root.
    for image in bpy.data.images:
        if image.source == 'FILE' and image.filepath and not image.packed_file:
            path = Path(bpy.path.abspath(image.filepath)).resolve(); assert path.is_relative_to(root) and path.is_file(), path
            image.filepath = '//' + path.relative_to(root).as_posix()
    (out / 'blender_assets.cats.txt').write_text(catalogs, encoding='utf-8')
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out / source.name), compress=True, relative_remap=False)
    report = dict(revision=data['revision'], source_sha256=data['source_sha256'], staged_sha256=sha(out / source.name), changes=changes,
        counts=dict(materials=1172, added=53, preview_only=352, materials_only=820, worlds=20), baseline_assets=len(baseline), game_started=False,
        materiallib_sha256=sha(root / 'MaterialLib.txt'), catalog_sha256=sha(out / 'blender_assets.cats.txt'))
    (out / 'build-report.json').write_text(json.dumps(report, indent=2))
    print('VISTA_CANDIDATES_STAGED', len(changes), report['staged_sha256'], flush=True)


if __name__ == '__main__':
    main()
