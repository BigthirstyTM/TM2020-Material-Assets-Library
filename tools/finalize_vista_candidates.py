"""Independently reopen vista candidates, then optionally install with backups."""
import argparse
import datetime
import json
import os
import shutil
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity, graph, sha


def verify(path, root, stage, report, baseline):
    blend_path = path
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    blocks = {x.bl_rna.identifier + ':' + x.name: x for c in [bpy.data.materials, bpy.data.worlds, bpy.data.node_groups] for x in c if x.asset_data}
    assert set(baseline) <= set(blocks)
    for key, before in baseline.items():
        asset = blocks[key]
        assert identity(asset) == before['identity'], ('Existing identity mismatch', key)
        assert graph(asset) == before['graph'], ('Existing graph mismatch', key)
        assert asset.get('tm_asset_effect_badges', '') == before['badges']
    names = {r['name'] for r in report['changes']}
    assert len(names) == 53 and len(blocks) == len(baseline) + 53
    identifiers = [x.get('tm_asset_id') for x in blocks.values() if x.get('tm_asset_id')]
    assert len(identifiers) == len(set(identifiers)), 'Duplicate asset IDs'
    checks = []
    for row in report['changes']:
        m = bpy.data.materials[row['name']]
        assert m.asset_data and m.asset_data.catalog_id == row['catalog_id']
        assert m.get('tm_asset_id') == row['id']
        assert m.get('tm_preview_only') and not m.get('tm_game_material_exportable')
        assert not m.get('link') and not json.loads(m['MAT_PROPS_AS_JSON']).get('link')
        assert m.get('tm_vista_candidate_alias') == row['candidate_alias']
        assert m.get('tm_vista_runtime_status') == 'Not tested in game'
        assert tuple(m.preview_ensure().image_size) == (256, 256)
        assert identity(m)['icon'] == row['icon_sha256']
        assert row['render_rgb_mean'] > 8, ('Unreadable dark thumbnail', m.name)
        assert m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].is_linked
        checks.append(dict(name=m.name, id=row['id'], preview_only=True, export_link_disabled=True, icon_verified=True))
    missing = []
    for image in bpy.data.images:
        if image.source != 'FILE' or not image.filepath or image.packed_file:
            continue
        path = root / image.filepath[2:] if image.filepath.startswith('//') else Path(image.filepath)
        if not path.is_file(): missing.append(str(path))
    assert not missing, missing
    assert len([m for m in bpy.data.materials if m.asset_data]) == 1172
    assert len([w for w in bpy.data.worlds if w.asset_data]) == 20
    return dict(revision=report['revision'], sha256=sha(blend_path), materials=1172, added=53, worlds=20,
        preview_only=352, materials_only=820, missing_images=0, old_assets_preserved=len(baseline), checks=checks)


def main():
    p = argparse.ArgumentParser()
    for key in ['library', 'stage', 'state']:
        p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--install', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = a.library.resolve(); stage = a.stage.resolve(); out = a.state.resolve(); out.mkdir(exist_ok=True, parents=True)
    report = json.loads((stage / 'build-report.json').read_text()); baseline = json.loads((stage / 'baseline.json').read_text())
    staged = stage / 'Trackmania2020_assets.blend'; source = root / staged.name
    assert sha(staged) == report['staged_sha256']
    assert sha(source) == report['source_sha256'], 'Installed source changed; do not overwrite'
    assert sha(root / 'MaterialLib.txt') == report['materiallib_sha256']
    proof = verify(staged, root, stage, report, baseline)
    (out / 'verification.json').write_text(json.dumps(proof, indent=2))
    if not a.install:
        print('VISTA_CANDIDATES_VERIFIED', len(proof['checks']), flush=True); return
    catalogs = root / 'blender_assets.cats.txt'; staged_catalogs = stage / catalogs.name
    assert staged_catalogs.read_text(encoding='utf-8').startswith(catalogs.read_text(encoding='utf-8'))
    assert sha(staged_catalogs) == report['catalog_sha256']
    backup = out / 'backup' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S'); backup.mkdir(parents=True)
    shutil.copy2(source, backup / source.name); shutil.copy2(catalogs, backup / catalogs.name)
    pending = root / 'Trackmania2020_vista_candidates.pending.blend'; shutil.copy2(staged, pending)
    assert sha(source) == report['source_sha256']
    try:
        shutil.copy2(staged_catalogs, catalogs); os.replace(pending, source)
        installed = verify(source, root, stage, report, baseline)
        assert sha(root / 'MaterialLib.txt') == report['materiallib_sha256']
    except Exception:
        shutil.copy2(backup / source.name, source); shutil.copy2(backup / catalogs.name, catalogs)
        raise
    receipt = dict(revision=report['revision'], installed=str(source), sha256=sha(source), previous_sha256=report['source_sha256'],
        backup=str(backup), counts=report['counts'], new_materials=[r['name'] for r in report['changes']],
        materiallib_unchanged=True, remote_library_changed=False, release_packages_changed=False, game_started=False)
    (out / 'installed-verification.json').write_text(json.dumps(installed, indent=2))
    (out / 'installation.json').write_text(json.dumps(receipt, indent=2))
    print('VISTA_CANDIDATES_INSTALLED', receipt['sha256'], flush=True)


if __name__ == '__main__':
    main()
