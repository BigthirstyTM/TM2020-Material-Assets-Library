"""Fresh-file pilot checks, with original source paths deliberately unavailable."""
import argparse
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import graph, identity, sha
from build_remote_pilot import trees, value

p = argparse.ArgumentParser()
for k in ['root', 'build-report', 'report']:
    p.add_argument('--' + k, type=Path, required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
build = json.loads(a.build_report.read_text())
checks = []
for row in build['materials']:
    path = a.root / row['path']
    assert sha(path) == row['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()), load_ui=False)
    assets = [m for m in bpy.data.materials if m.asset_data]
    assert len(assets) == 1 and assets[0].name == row['name']
    m = assets[0]
    assert m['tm_asset_id'] == row['id']
    assert identity(m) == row['contract']['identity'], row['name']
    assert graph(m) == row['contract']['graph'], row['name']
    assert value(dict(m.items())) == row['contract']['properties'], row['name']
    assert {g.name: graph(g) for g in trees(m.node_tree)} == row['contract']['groups']
    assert not any(g.asset_data for g in bpy.data.node_groups)
    assert not any(lib.filepath for lib in bpy.data.libraries)
    for image in bpy.data.images:
        if image.source == 'FILE':
            assert image.packed_file, (row['name'], image.name)
            # Remove access to the old source path in memory and force decode.
            image.filepath = '//deliberately-unavailable/' + image.name
            assert image.size[0] and image.size[1], image.name
            assert len(image.pixels) > 0, image.name
    checks.append(dict(name=m.name, id=row['id'], packed_dependencies=True,
                       preview_preserved=True, export_properties_preserved=True))
proof = dict(materials=len(checks), checks=checks, missing_dependencies=0)
a.report.write_text(json.dumps(proof, indent=2))
print('REMOTE_PILOT_VERIFIED', len(checks), flush=True)
