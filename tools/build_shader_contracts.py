"""Derive material input contracts from decoded native descriptors."""
import argparse
import json
from pathlib import Path
import re


def canonical(value):
    value = value.replace('\\', '/').lower()
    if ':data:/projects/' in value:
        value = value.split(':data:/projects/', 1)[1]
    return value.removesuffix('.gbx').removesuffix('.material')


def build(resources, inventory, materiallib):
    indexed = {canonical(row['path']): row for row in resources['rows']}
    definitions = {}
    collection = ''
    for block in re.split(r'(?=DLibrary\(|DMaterial\()', materiallib):
        match = re.match(r'DLibrary\(([^)]+)\)', block)
        if match:
            collection = match[1]
        match = re.match(r'DMaterial\(([^)]+)\)', block)
        if match:
            definitions[match[1]] = dict(collection=collection,
                link=(re.search(r'DLinkFull\s*\(([^)]+)\)', block).group(1) if re.search(r'DLinkFull\s*\(([^)]+)\)', block) else ''),
                uv=re.findall(r'DUvLayer\s*\(\s*([^,]+),\s*(\d+)\s*\)', block),
                color0=bool(re.search(r'DColor0\s*\(', block)))
    contracts = []
    items = list(inventory['materials'])
    aliases = {m.get('effective', {}).get('link') for m in items}
    for alias, definition in definitions.items():
        if alias not in aliases:
            link = definition['link'].replace('\\', '/')
            if link.lower().startswith('media/'):
                link = definition['collection'] + '/' + link
            items.append(dict(name=alias, id=None, native_link=link, effective=dict(link=alias)))
    for item in items:
        source = indexed.get(canonical(item.get('native_link') or ''))
        if not source:
            continue
        details = source['details']
        shaderpath = (details.get('shader') or '').replace('.Material.', '.Shader.').replace('.material.', '.Shader.')
        shaderpath = shaderpath.replace('/Material/', '/Shader/').replace('\\Material\\', '\\Shader\\')
        shader = indexed.get(canonical(shaderpath))
        # An unavailable exact shader is unresolved; never substitute a PC/LM variant.
        if not shader:
            shader = dict(path=None, details={})
        addresses = {row['name']: row for row in shader['details'].get('addresses', [])}
        slots = {row['name']: row['file'] for row in details.get('slots') or []}
        options = {}
        for chunk in details.get('chunks') or []:
            fields = chunk.get('fields', {})
            for value in fields.get('U04', []) if isinstance(fields.get('U04'), list) else []:
                if isinstance(value, dict) and isinstance(value.get('U01'), str):
                    options[value['U01']] = value.get('U02')
        relevant = [address for name, address in addresses.items()
            if name not in ('PreLightGenTx', 'PreLightGenTy', 'PreLightGenTz', 'ACosSmooth', 'ACosSmoothPy')]
        uv = any(row.get('generate') == 'NoGenerate' for row in relevant)
        projected = any('World' in row.get('generate', '') for row in relevant)
        classification = 'mixed' if uv and projected else 'uv' if uv else 'projected' if projected else 'unresolved'
        alias = item.get('effective', {}).get('link', '')
        current = definitions.get(alias, {})
        vertex_alpha = options.get('VertexAlpha') == 1
        contracts.append(dict(name=item['name'], asset_id=item['id'], alias=alias,
            source=source['path'], shader=shader['path'], shader_family=details.get('shader'),
            options=options, classification=classification, vertex_alpha=vertex_alpha,
            relevant_addresses=[dict(name=row['name'], generate=row.get('generate'),
                use_bitmap_scale=row.get('UseBitmapTcScale'), file=slots.get(row['name'], row.get('file'))) for row in relevant],
            slots=slots, current=current,
            proposed_uv=[['Lightmap','0']] if classification == 'projected' else None,
            add_color0=vertex_alpha and not current.get('color0', False),
            evidence='Decoded native material overrides and shader address generators; runtime lightmap validation remains separate.'))
    return contracts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--materiallib', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    contracts = build(json.loads(args.resources.read_text(encoding='utf-8')),
        json.loads(args.inventory.read_text(encoding='utf-8')), args.materiallib.read_text(encoding='utf-8-sig'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contracts, indent=2), encoding='utf-8')
    from collections import Counter
    print('SHADER_CONTRACTS', len(contracts), dict(Counter(row['classification'] for row in contracts)),
        'missing_color0', sum(row['add_color0'] for row in contracts))
