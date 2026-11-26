"""Prepare GitHub Pages metadata + Releases payloads for the Materials Only pilot."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

p = argparse.ArgumentParser()
for name in ['workspace', 'host', 'inventory', 'output']:
    p.add_argument('--' + name, type=Path, required=True)
a = p.parse_args()
out = a.output.resolve()
assert not (out / 'plan.json').exists(), 'Already prepared; inspect state before rebuilding'
repo = 'BigthirstyTM/TM2020-Material-Assets-Library'
tag = 'remote-materials-only-pilot-v0.1.0'
base = 'https://bigthirstytm.github.io/TM2020-Material-Assets-Library/'
remote_url = base + 'remote/materials-only/'
release_base = 'https://github.com/' + repo + '/releases/download/' + tag + '/'
site = out / 'site'
library = site / 'remote/materials-only'
assets = out / 'assets'
extension = out / 'extension'
for directory in [library / '_v1', assets, extension]:
    directory.mkdir(parents=True, exist_ok=True)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


host = a.host.resolve()
inventory = {r['name']: r for r in json.loads(a.inventory.read_text())['materials']}
page = json.loads((host / '_v1/assets-00000.json').read_text())
selected = [x for x in page['assets'] if not inventory[x['name']].get('preview_only', True)]
assert len(selected) == 12
paths = {name for item in selected for name in item['files']}
files = [item for item in page['files'] if item['path'] in paths]
assert len(files) == len(selected)
payloads = []
for item in files:
    source = host / item['path']
    digest = sha(source)
    assert item['hash'].split(':', 1)[1] == digest
    name = source.stem + '.' + digest[:16] + '.blend'
    target = assets / name
    os.link(source, target)
    item['url'] = release_base + name
    payloads.append(dict(name=name, sha256=digest, bytes=source.stat().st_size,
                         library_path=item['path']))
for item in selected:
    thumb = item['thumbnail']
    source = host / thumb['url']
    digest = sha(source)
    assert thumb['hash'].split(':', 1)[1] == digest
    ident = inventory[item['name']]['id']
    relative = 'thumbnails/' + ident + '.' + digest[:16] + '.webp'
    dest = library / relative
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(source, dest)
    thumb['url'] = relative
page.update(asset_count=len(selected), file_count=len(files), assets=selected, files=files)
write_json(library / '_v1/assets-00000.json', page)
index = json.loads((host / '_v1/asset-index.json').read_text())
used_ids = {x['meta']['catalog_id'] for x in selected}
used_paths = {x['path'] for x in index['catalogs'] if set(x['uuids']) & used_ids}
index['catalogs'] = [x for x in index['catalogs']
                     if any(v == x['path'] or v.startswith(x['path'] + '/') for v in used_paths)]
assert not any('Preview only' in x['path'] for x in index['catalogs'])
index.update(asset_count=len(selected), file_count=len(files),
             asset_size_bytes=sum(x['size_in_bytes'] for x in files),
             pages=[dict(url='_v1/assets-00000.json',
                         hash='SHA256:' + sha(library / '_v1/assets-00000.json'))])
write_json(library / '_v1/asset-index.json', index)
meta = dict(name='TM2020 Materials Only (Pilot)',
            contact=dict(name='BigthirstyTM', url='https://github.com/' + repo),
            api_versions=dict(v1=dict(url='_v1/asset-index.json',
                                     hash='SHA256:' + sha(library / '_v1/asset-index.json'))))
write_json(library / '_asset-library-meta.json', meta)
extension_name = 'tm2020_materials_only-0.1.0.zip'
(extension / 'blender_manifest.toml').write_text(f'''schema_version = "1.0.0"
id = "tm2020_materials_only"
version = "0.1.0"
name = "TM2020 Materials Only (Pilot)"
tagline = "Trackmania materials with incremental remote downloads"
maintainer = "BigthirstyTM"
type = "asset-library"
blender_version_min = "5.3.0"
license = ["SPDX:LicenseRef-TM2020-Game-Assets"]
website = "{base}"

[asset_library]
remote_url = "{remote_url}"

[permissions]
scripts = "Preview animations use timeline driver expressions"
''', encoding='utf-8')
(extension / 'LICENSE.txt').write_text(
    'Trackmania game assets remain the property of Ubisoft/Nadeo and their respective owners. '
    'This pilot does not grant a broader redistribution license and is not CC0. '
    'LicenseRef-TM2020-Game-Assets records these restrictions, not a grant of rights.\n')
(site / '.nojekyll').write_text('')
(site / 'index.html').write_text(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>TM2020 Materials Only — Remote Pilot</title>
<style>body{{font:18px/1.6 system-ui;max-width:820px;margin:60px auto;padding:0 24px;background:#171c22;color:#e5ecf2}}a{{color:#8bcfff}}code{{color:#ffd16b}}h1{{line-height:1.2}}</style>
<h1>TM2020 Materials Only — Remote Pilot</h1>
<p>A small online library for Blender 5.3 and newer. This pilot includes <strong>12 materials</strong>; it is not yet the full Materials Only collection.</p>
<p><a href="{release_base}{extension_name}">Download the library extension ZIP</a></p>
<ol><li>In Blender, enable Online Access.</li><li>Open Preferences → Get Extensions → Install from Disk and select the ZIP.</li>
<li>Under Preferences → Asset Libraries, enable <strong>TM2020 Materials Only (Pilot)</strong>.</li>
<li>Select that library in an Asset Browser. Materials download when needed; no local server is required.</li></ol>
<p>To download the whole pilot, clear search/catalog filters, select all thumbnails and choose Download Assets.
Use Refresh Remote Listing to retrieve new listings. Existing materials in your scene are not automatically replaced.</p>
<p><strong>Update trial:</strong> CustomBricks intentionally has a yellow/black Blender preview and an UPDATE 02 thumbnail. Its native game link is unchanged.</p>
<p>This public extension contains Materials Only entries. Experimental and Preview only entries are reserved for DEV evaluation and are not included here.</p>
<p>Blendermania and its MaterialLib setup are separate. MaterialLib.txt is not bundled with this extension; use your Blendermania setup for export.</p>
<p>Thumbnail badges describe material features; see the <a href="https://github.com/{repo}/blob/main/docs/BADGES.md">short badge legend</a>.
Native-linked does not guarantee identical game appearance or runtime behavior.</p>
<p>Prefer an offline package? The <a href="https://github.com/{repo}/releases/tag/v1.0.0-materials-only">existing full Materials Only ZIP release</a> remains available.</p>
<p>Trackmania resources remain the property of Ubisoft/Nadeo and their respective owners. This independent project does not relicense game assets as CC0.</p>
</html>''', encoding='utf-8')
notes = f'''Materials Only remote-library pilot for Blender 5.3+.

Install **{extension_name}** through Preferences → Get Extensions → Install from Disk, then enable **TM2020 Materials Only (Pilot)** under Asset Libraries.

This is a 12-material pilot, not the full collection. Individual `.blend` files are hosted here for Blender's downloader; users only need the extension ZIP. No local server is required.

CustomBricks deliberately uses a yellow/black preview and UPDATE 02 icon for the update trial. Existing scene materials are not automatically replaced. Preview only/experimental assets are excluded. Blendermania and MaterialLib are supplied separately.

Instructions: {base}
Remote library: {remote_url}
Full offline Materials Only packages remain available separately.
'''
(out / 'release-notes.md').write_text(notes, encoding='utf-8')
write_json(out / 'plan.json', dict(repo=repo, tag=tag, pages_branch='remote-library',
           pages_url=base, library_url=remote_url, assets=payloads,
           materials=[x['name'] for x in selected], excluded_preview_only=1,
           extension_name=extension_name, source_host=str(host)))
print('GITHUB_MATERIALS_ONLY_PILOT_PREPARED', len(selected), flush=True)
