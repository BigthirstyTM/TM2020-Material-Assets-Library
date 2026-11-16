"""Build portable editions with Blender. See docs/MAINTAINING.md."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:])


def main():
    a = args()
    a.output = a.output.resolve()
    source = a.source.resolve()
    inventory = json.loads(a.inventory.read_text(encoding='utf-8'))['materials']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
    # Metadata can also carry source-image references. Relocate those alongside
    # the actual image datablocks without changing native game material links.
    def relocate_properties(group):
        for key in list(group.keys()):
            value = group[key]
            if isinstance(value, str):
                for prefix in (str(source.parent) + '\\', source.parent.as_posix() + '/',
                               str(source.parent).replace('\\', '\\\\') + '\\\\'):
                    value = value.replace(prefix, '//')
                group[key] = value
            elif hasattr(value, 'keys'):
                relocate_properties(value)
    for collection in (bpy.data.materials, bpy.data.worlds, bpy.data.node_groups, bpy.data.images):
        for block in collection:
            relocate_properties(block)
    by_name = {m.name: m for m in bpy.data.materials if m.asset_data}
    assert set(by_name) == {m['name'] for m in inventory}
    preview = {r['name'] for r in inventory if not r['effective']['link']}
    assert len(preview) == 272, len(preview)
    source_images = {}
    for image in bpy.data.images:
        if image.source != 'FILE' or not image.filepath or image.packed_file:
            continue
        path = Path(bpy.path.abspath(image.filepath)).resolve()
        assert path.is_file(), path
        # Preserve the source layout under Textures; reject external dependencies.
        relative = path.relative_to(source.parent)
        assert relative.parts[0] == 'Textures', relative
        image.filepath = '//' + relative.as_posix()
        source_images[relative.as_posix()] = str(path)
    shared = set(w for w in bpy.data.worlds if w.asset_data)
    shared.update(g for g in bpy.data.node_groups if g.asset_data)
    for edition in ('materials-only', 'complete'):
        output = a.output / edition
        output.mkdir(parents=True, exist_ok=True)
        selected = {m for name, m in by_name.items() if edition == 'complete' or name not in preview}
        bpy.data.libraries.write(str(output / 'Trackmania2020_assets.blend'), selected | shared,
                                 path_remap='NONE', fake_user=True, compress=True)
        cats = []
        for line in (source.parent / 'blender_assets.cats.txt').read_text(encoding='utf-8').splitlines():
            parts = line.split(':', 2)
            if len(parts) == 3 and (parts[1].startswith('Preview only') or parts[1].startswith('Trackmania2020/08 Preview only')):
                if edition == 'materials-only':
                    continue
                if parts[1].startswith('Preview only'):
                    parts[1] = 'Trackmania2020/08 Preview only' + parts[1][len('Preview only'):]
                parts[2] = parts[1].replace('/', '-')
                line = ':'.join(parts)
            cats.append(line)
        (output / 'blender_assets.cats.txt').write_text('\n'.join(cats) + '\n', encoding='utf-8')
        rows = []
        for row in inventory:
            if row['name'] not in {m.name for m in selected}:
                continue
            rows.append({k: row.get(k) for k in ('id', 'name', 'preview_type', 'usage', 'usage_tags', 'native_link')}
                        | dict(preview_only=row['name'] in preview,
                               catalog=row['catalog'].replace('Preview only', 'Trackmania2020/08 Preview only', 1),
                               physics=row.get('collision', {}).get('physics', ''),
                               gameplay=row.get('collision', {}).get('gameplay', ''),
                               conditional='ColorBlind' in row['name']))
        (output / 'materials.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
        (output / 'build-source.json').write_text(json.dumps(dict(edition=edition,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            blender=bpy.app.version_string, materials=len(selected), preview_only=len(preview) if edition == 'complete' else 0,
            worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),
            node_groups=sum(bool(g.asset_data) for g in bpy.data.node_groups)), indent=2), encoding='utf-8')
    (a.output / 'source-images.json').write_text(json.dumps(source_images, indent=2), encoding='utf-8')
    print('PORTABLE_LIBRARIES_WRITTEN', flush=True)


if __name__ == '__main__':
    main()
