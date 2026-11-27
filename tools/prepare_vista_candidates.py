"""Prepare source-backed, untested vista preview recipes without modifying assets."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from vista_array_mapping import descriptor_transform


def canonical(value):
    return (value or '').replace('\\', '/').lower().replace(':data:/projects/', '')


def main():
    p = argparse.ArgumentParser()
    for key in ['native-workspace', 'library', 'candidates', 'output']:
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    texture_files = [x for x in (a.library / 'Textures').rglob('*') if x.is_file()]
    ix = {}
    for relative in ['downloads/strict-native-data/resources.json', 'logs/v6/native-structures/resources.json', 'logs/experimental/resources/resources.json']:
        for row in json.loads((a.native_workspace / relative).read_text(encoding='utf-8-sig'))['rows']:
            key = canonical(row['path'])
            if key not in ix or len(json.dumps(row.get('details', {}))) > len(json.dumps(ix[key].get('details', {}))):
                ix[key] = row

    def resource(ref, owner):
        key = canonical(ref)
        choices = [key, canonical(owner.split('/')[0] + '/Media/' + ref), canonical(str(Path(owner).parent / ref))]
        for choice in choices:
            if choice in ix:
                return ix[choice]
        raise KeyError((ref, owner))

    def bitmap(ref, owner):
        if not ref:
            return None
        row = resource(ref, owner)
        d = dict(row['details'])
        result = dict(resource=row['path'], **d)
        if d.get('image'):
            image = d['image'].replace('\\', '/')
            env = image.split('/')[0] if '/media/' in image.lower() else row['path'].split('/')[0]
            path = a.library / 'Textures' / env / Path(image).name
            if not path.is_file():
                suffix = env.lower() + '/media/texture/image/' + Path(image).name.lower()
                matches = [x for x in texture_files if x.as_posix().lower().endswith(suffix)]
                assert matches, (row['path'], path)
                hashes = {hashlib.sha256(x.read_bytes()).hexdigest() for x in matches}
                assert len(hashes) == 1, ('Ambiguous source image', matches)
                path = matches[0]
            assert path.is_file(), (row['path'], path)
            result['path'] = str(path.resolve())
        return result

    recipes = []
    for candidate in json.loads(a.candidates.read_text()):
        native = resource(candidate['path'], candidate['path'])
        d = native['details']
        parent = resource(d['shader'], native['path'])
        shader_refs = [r for r in parent.get('refs', []) if r.lower().endswith('.shader.gbx')]
        assert len(shader_refs) == 1, parent['path']
        shader = resource(shader_refs[0], parent['path'])
        sd = shader['details']
        refs = {r['name']: r.get('file') for r in sd.get('addresses', [])}
        refs.update({r['name']: r.get('file') for r in d.get('slots') or []})
        slots = {name: bitmap(ref, native['path']) for name, ref in refs.items() if ref and name not in ['PreLightGenTx', 'PreLightGenTy', 'PreLightGenTz']}
        params = {}
        for stage in ['vertex', 'pixel']:
            for row in d.get(stage) or []:
                params[row['name']] = row['values']
        for shader_pass in sd.get('passes') or []:
            for stage in ['vertex', 'pixel']:
                for value in (shader_pass.get(stage) or {}).get('constants') or []:
                    params.setdefault(value['name'], value.get('values'))
        selectors = next((c['fields'] for c in d.get('chunks') or [] if c['id'] == 0x0903A015), {})
        options = {v['U01']: v['U02'] for c in d.get('chunks') or [] for v in c['fields'].get('U04', []) if isinstance(c['fields'].get('U04'), list) and isinstance(v, dict)}
        arrays = {}
        for name, desc in list(slots.items()):
            if not desc or not desc.get('array'):
                continue
            image_array = resource(desc['array'], desc['resource'])
            arrays[name] = dict(descriptor=desc, image_array=image_array)
        if arrays:
            for prefix, selector_key in [('Py', 'U03'), ('Pxz', 'U02')]:
                selector = selectors.get(selector_key)
                assert selector, (candidate['path'], selectors)
                for role in ['BaseColor', 'RoughMetal', 'Normal']:
                    source = arrays[role]
                    layer = next(v for v in source['image_array']['details']['layers'] if v['U01'] == selector)
                    desc = source['descriptor']
                    filename = selector + desc['arraySuffix'] + '.dds'
                    env = native['path'].split('/')[0]
                    path = a.library / 'Textures' / env / filename
                    assert path.is_file(), path
                    # Retain authoring fields and use separate native top/side
                    # transforms, corroborated by reflected game layer values.
                    slots[prefix + role] = dict(resource=desc['resource'], path=str(path.resolve()), image=filename,
                        usage=desc['usage'], **descriptor_transform(layer, side=prefix == 'Pxz'),
                        array_selector=selector, array_fields=layer)
            for role, field in [('PyX2', 'U04'), ('PyH2', 'U05')]:
                selector = selectors.get(field)
                if selector:
                    source = arrays[role]
                    layer = next(v for v in source['image_array']['details']['layers'] if v['U01'] == selector)
                    filename = selector + source['descriptor']['arraySuffix'] + '.dds'
                    path = a.library / 'Textures' / native['path'].split('/')[0] / filename
                    assert path.is_file(), path
                    slots[role] = dict(resource=source['descriptor']['resource'], path=str(path.resolve()), image=filename,
                        usage=source['descriptor']['usage'], **descriptor_transform(layer),
                        array_selector=selector, array_fields=layer)
                else:
                    slots.pop(role, None)
            angles = dict(top=[slots['PyBaseColor']['array_fields']['U11'], slots['PyBaseColor']['array_fields']['U12']],
                side=[slots['PxzBaseColor']['array_fields']['U13'], slots['PxzBaseColor']['array_fields']['U14']])
        else:
            angles = None
        aliases = candidate['aliases']
        assert aliases
        alias = next((x for x in aliases if x.startswith(candidate['environment'] + '_')), aliases[0])
        recipes.append(dict(name='TM_' + alias + '_asset', alias=alias, source=native['path'], source_sha256=native.get('sha256'),
            environment=candidate['environment'], shader=shader['path'], shader_details=sd, parent=parent['path'], slots=slots,
            parameters=params, selectors=selectors, options=options, arrays=arrays, array_angles=angles,
            id='mat-' + hashlib.sha256(canonical(native['path']).encode()).hexdigest()[:24]))
    assert len(recipes) == 53 and len({r['name'] for r in recipes}) == 53
    source = a.library / 'Trackmania2020_assets.blend'
    result = dict(revision='2026.11.27-vista-candidates-1', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), materials=recipes)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('VISTA_RECIPES', len(recipes), collections.Counter(r['shader'] for r in recipes))


if __name__ == '__main__':
    main()
