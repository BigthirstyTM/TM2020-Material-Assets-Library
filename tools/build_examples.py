"""Create a small editable usage scene for each portable edition."""
import argparse
from pathlib import Path
import sys
import bpy

p = argparse.ArgumentParser()
p.add_argument('--staging', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
staging = a.staging.resolve()
for edition in ('materials-only', 'complete'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    root = staging / edition
    names = ['TM_RoadTech_asset', 'TM_RoadDirt_asset', 'TM_CustomIce_asset']
    with bpy.data.libraries.load(str(root / 'Trackmania2020_assets.blend'), link=False) as (source, target):
        assert set(names) <= set(source.materials)
        target.materials = names.copy()
    for index, name in enumerate(names):
        collection = bpy.data.collections.new(name.removeprefix('TM_').removesuffix('_asset') + ' Example')
        bpy.context.scene.collection.children.link(collection)
        bpy.ops.mesh.primitive_cube_add(size=2, location=(index * 3, 0, 1))
        ob = bpy.context.object
        ob.name = 'Sample_' + name.removeprefix('TM_').removesuffix('_asset')
        for old in list(ob.users_collection):
            old.objects.unlink(ob)
        collection.objects.link(ob)
        ob.data.materials.append(bpy.data.materials[name])
        ob.data.uv_layers[0].name = 'BaseMaterial'
        ob.data.uv_layers.new(name='LightMap', do_init=True)
    for image in bpy.data.images:
        if image.source == 'FILE' and image.filepath and not image.packed_file:
            path = Path(bpy.path.abspath(image.filepath)).resolve()
            # Library append remaps relative image paths to absolute paths.
            relative = path.relative_to(root)
            assert path.is_file(), path
            image.filepath = '//../' + relative.as_posix()
    output = root / 'Examples'
    output.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'Material-Usage.blend'), compress=True)
    print('EXAMPLE_WRITTEN', edition, flush=True)
