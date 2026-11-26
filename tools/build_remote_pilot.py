"""Export an isolated, incrementally rebuilt remote-library pilot in Blender.

Never saves the source file or changes preferences. Each file contains one
material and its packed dependencies. This is a pilot, not a production build.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import graph, identity, sha

TARGETS = [
    'TM_Water_asset', 'TM_GlassWaterWall_asset', 'TM_CustomGlass_asset',
    'TM_CustomBricks_asset', 'TM_PlatformDirt_DecoHill_asset',
    'TM_PlatformDirt_DecoHill2_asset', 'TM_PlatformIce_DecoGrass_asset',
    'TM_Boost_Decal_asset', 'TM_ItemObstacle_asset',
    'TM_GreenCoast_VegetDryGrassA_asset', 'TM_Chrono-00-00-01_asset',
    'TM_Ad16x9Screen_asset',
]


def value(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, bpy.types.ID):
        return [v.bl_rna.identifier, v.name]
    if hasattr(v, 'items'):
        return {k: value(x) for k, x in v.items()}
    try:
        return [value(x) for x in v]
    except TypeError:
        return str(v)


def trees(root):
    found = set()

    def visit(tree):
        if tree in found:
            return
        found.add(tree)
        for node in tree.nodes:
            if node.type == 'GROUP' and node.node_tree:
                visit(node.node_tree)
    visit(root)
    return found


def main():
    p = argparse.ArgumentParser()
    for name in ['source', 'inventory', 'output', 'report']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--demo-update', action='store_true',
                   help='Change only pilot metadata on CustomBricks; never the source.')
    p.add_argument('--include-material', action='append', default=[],
                   help='Add a source material without rebuilding unchanged pilot files.')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = a.source.resolve()
    original_hash = sha(source)
    output = a.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    asset_dir = output / 'materials'
    asset_dir.mkdir(exist_ok=True)
    rows = {r['name']: r for r in json.loads(a.inventory.read_text())['materials']}
    targets = list(dict.fromkeys(TARGETS + a.include_material))
    state_path = a.report.parent / 'export-state.json'
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    # Hide dependency node-group assets from the pilot browser. Materials keep
    # their original asset identities; no duplicate source-resource entries.
    for group in bpy.data.node_groups:
        if group.asset_data:
            group.asset_clear()
    file_hashes = {}
    report = dict(source_sha256=original_hash, blender=bpy.app.version_string,
                  materials=[], changed=[], unchanged=[])
    next_state = {}
    for name in targets:
        material = bpy.data.materials[name]
        assert material.asset_data
        if a.demo_update and name == 'TM_CustomBricks_asset':
            material['tm_remote_pilot_demo_revision'] = 2
        dependencies = trees(material.node_tree)
        images = {node.image for tree in dependencies for node in tree.nodes
                  if node.type == 'TEX_IMAGE' and node.image}
        image_signatures = {}
        for image in images:
            if image.source == 'FILE':
                path = Path(bpy.path.abspath(image.filepath)).resolve()
                if not image.packed_file:
                    assert path.is_file(), path
                    file_hashes.setdefault(str(path), sha(path))
                    image_signatures[image.name] = file_hashes[str(path)]
                    image.filepath = str(path)
                    image.pack()
                else:
                    image_signatures[image.name] = hashlib.sha256(image.packed_file.data).hexdigest()
            else:
                assert image.source == 'GENERATED', (name, image.name, image.source)
                image_signatures[image.name] = list(image.size)
        contract = dict(identity=identity(material), graph=graph(material),
                        properties=value(dict(material.items())),
                        groups={g.name: graph(g) for g in dependencies},
                        images=image_signatures)
        fingerprint = hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
        ident = material['tm_asset_id']
        relative = 'materials/' + ident + '.blend'
        dest = output / relative
        old = previous.get(ident, {})
        if old.get('fingerprint') == fingerprint and dest.is_file() and sha(dest) == old.get('sha256'):
            report['unchanged'].append(relative)
        else:
            bpy.data.libraries.write(str(dest), {material}, path_remap='NONE',
                                     fake_user=True, compress=True)
            report['changed'].append(relative)
        record = dict(name=name, id=ident, path=relative, bytes=dest.stat().st_size,
                      sha256=sha(dest), fingerprint=fingerprint,
                      preview_only=rows[name].get('preview_only', False),
                      packed_images=len(images), contract=contract)
        report['materials'].append(record)
        next_state[ident] = dict(fingerprint=fingerprint, sha256=record['sha256'])
    # Keep original IDs/paths but omit empty catalogs from this small pilot.
    catalogs = source.parent / 'blender_assets.cats.txt'
    lines = catalogs.read_text(encoding='utf-8-sig').splitlines()
    entries = [line.split(':', 2) for line in lines
               if not line.startswith('#') and line.count(':') >= 2]
    used_ids = {bpy.data.materials[n].asset_data.catalog_id for n in targets}
    used_paths = [path for ident, path, simple in entries if ident in used_ids]
    retained = [':'.join(row) for row in entries
                if any(path == row[1] or path.startswith(row[1] + '/') for path in used_paths)]
    (output / catalogs.name).write_text('# Remote pilot catalogs\nVERSION 1\n' + '\n'.join(retained) + '\n')
    assert sha(source) == original_hash, 'Source changed while exporting pilot'
    report['total_bytes'] = sum(r['bytes'] for r in report['materials'])
    report['source_unchanged'] = True
    a.report.write_text(json.dumps(report, indent=2))
    state_path.write_text(json.dumps(next_state, indent=2))
    print('REMOTE_PILOT_EXPORTED', len(report['materials']), 'changed', len(report['changed']), flush=True)


if __name__ == '__main__':
    main()
