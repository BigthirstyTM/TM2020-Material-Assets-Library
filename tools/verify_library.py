"""Open a relocated edition in a fresh Blender process and verify dependencies."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy

p = argparse.ArgumentParser()
p.add_argument('--library', type=Path, required=True)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=str(a.library.resolve()), load_ui=False)
root = a.library.resolve().parent
rows = json.loads((root / 'materials.json').read_text(encoding='utf-8'))
expected = {r['name'] for r in rows}
actual = {m.name for m in bpy.data.materials if m.asset_data}
assert actual == expected, (actual - expected, expected - actual)
images = []
for image in bpy.data.images:
    if image.source != 'FILE' or not image.filepath or image.packed_file:
        continue
    assert image.filepath.startswith('//'), (image.name, image.filepath)
    resolved = Path(bpy.path.abspath(image.filepath)).resolve()
    relative = resolved.relative_to(root).as_posix()
    assert resolved.is_file(), relative
    images.append(relative)
for mat in bpy.data.materials:
    if mat.asset_data:
        mat.preview_ensure()
        assert mat.preview and mat.preview.image_size[0] > 0, mat.name
catalog_ids = {line.split(':', 1)[0] for line in (root / 'blender_assets.cats.txt').read_text(encoding='utf-8').splitlines() if ':' in line and not line.startswith('#')}
for collection in (bpy.data.materials, bpy.data.worlds, bpy.data.node_groups):
    for asset in collection:
        if asset.asset_data:
            assert asset.asset_data.catalog_id in catalog_ids, (asset.name, asset.asset_data.catalog_id)
report = dict(materials=len(actual), worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),
              node_groups=sum(bool(g.asset_data) for g in bpy.data.node_groups),
              external_images=sorted(set(images)),
              library_sha256=hashlib.sha256(a.library.read_bytes()).hexdigest(),
              relative_paths=True, icons_present=True, catalog_ids_valid=True)
a.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('RELOCATED_LIBRARY_OK', len(actual), len(set(images)), flush=True)
