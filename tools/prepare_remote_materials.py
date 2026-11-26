"""Prepare production remote indexes and a native asset-library extension repository."""
import argparse,hashlib,html,json,os,shutil,subprocess,urllib.parse
from pathlib import Path

p=argparse.ArgumentParser()
for k in ['export','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();root=a.export.resolve();host=root/'host';out=a.output.resolve();site=out/'site';assets=out/'assets';extension=out/'extension'
repo='BigthirstyTM/TM2020-Material-Assets-Library';tag='materials-library-extension-v1.0.0';base='https://bigthirstytm.github.io/TM2020-Material-Assets-Library/'
remote_url=base+'remote/tm2020-materials/';library=site/'remote/tm2020-materials';name='Trackmania 2020 - Materials Library';extension_id='trackmania_2020_materials_library';version='1.0.0';zip_name=extension_id+'-'+version+'.zip'
for d in [library/'_v1',assets,extension,site/'extensions']:d.mkdir(parents=True,exist_ok=True)
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
build=json.loads((root/'build-report.json').read_text());proof=json.loads((root/'verification.json').read_text());assert len(build['materials'])==proof['materials']==825 and proof['missing_images']==0
materials_by_name={r['name']:r for r in build['materials']};rows={r['path']:r for r in build.get('bundles',build['materials'])};index=json.loads((host/'_v1/asset-index.json').read_text());all_assets=[];payloads=[];pages=[];seen=set()
for entry in index['pages']:
 page=json.loads((host/entry['url']).read_text())
 for file in page['files']:
  row=rows[file['path']];assert file['hash']=='SHA256:'+row['sha256'];filename=row['id']+'.'+row['sha256'][:16]+'.blend';target=assets/filename
  if not target.exists():os.link(host/row['path'],target)
  assert sha(target)==row['sha256'];file['url']='https://github.com/'+repo+'/releases/download/'+tag+'/'+filename
  if filename not in seen:payloads.append(dict(name=filename,path=row['path'],sha256=row['sha256'],bytes=row['bytes']));seen.add(filename)
 for material in page['assets']:
  assert material['id_type']=='MATERIAL';all_assets.append(material)
  thumb=material['thumbnail'];source=host/urllib.parse.unquote(thumb['url']);digest=sha(source);assert thumb['hash']=='SHA256:'+digest
  ident=materials_by_name[material['name']]['id'];relative='thumbnails/'+ident+'.'+digest[:16]+'.webp';dest=library/relative;dest.parent.mkdir(exist_ok=True)
  shutil.copy2(source,dest);thumb['url']=relative
 path=library/entry['url'];path.parent.mkdir(exist_ok=True);write(path,page);pages.append(dict(url=entry['url'],hash='SHA256:'+sha(path)))
assert len(all_assets)==825 and len(payloads)==len(rows) and {m['name'] for m in all_assets}==set(materials_by_name)
used={m['meta']['catalog_id'] for m in all_assets};paths={c['path'] for c in index['catalogs'] if set(c['uuids'])&used}
index['catalogs']=[c for c in index['catalogs'] if any(path==c['path'] or path.startswith(c['path']+'/') for path in paths)]
assert not any('Preview only' in c['path'] for c in index['catalogs'])
index.update(pages=pages,asset_count=825,file_count=len(rows),asset_size_bytes=sum(r['bytes'] for r in rows.values()));write(library/'_v1/asset-index.json',index)
write(library/'_asset-library-meta.json',dict(name=name,contact=dict(name='BigthirstyTM',url='https://github.com/'+repo),api_versions=dict(v1=dict(url='_v1/asset-index.json',hash='SHA256:'+sha(library/'_v1/asset-index.json')))))
(extension/'blender_manifest.toml').write_text(f'''schema_version = "1.0.0"
id = "{extension_id}"
version = "{version}"
name = "{name}"
tagline = "Trackmania materials with efficient remote downloads"
maintainer = "BigthirstyTM"
type = "asset-library"
blender_version_min = "5.3.0"
license = ["SPDX:LicenseRef-TM2020-Game-Assets"]
website = "{base}"

[asset_library]
remote_url = "{remote_url}"

[permissions]
scripts = "Material previews use timeline driver expressions"
''',encoding='utf-8')
(extension/'LICENSE.txt').write_text('Trackmania game assets remain the property of Ubisoft/Nadeo and their respective owners. This extension does not grant broader rights to those assets and is not CC0. LicenseRef-TM2020-Game-Assets records the existing rights statements.\n',encoding='utf-8')
(extension/'README.md').write_text(f'''# {name}

Asset library extension for Blender 5.3 and newer. 825 Materials Only entries.
Enable Online Access, install this extension and enable the library under
Preferences > Asset Libraries. Select it in the Asset Browser. Materials download
on demand, including packed textures. No terminal or local server is needed.

Refresh Remote Listing checks the current asset listing. Downloaded materials
are cached by Blender. To download everything, clear search/catalog filters,
select all assets and choose Download Assets. Updating the library does not
replace materials already appended to a scene. Disable the earlier pilot
library if installed to avoid confusing duplicate entries.

Complete-only / Preview only entries and MaterialLib.txt are excluded. Blendermania
supplies its own export setup. Existing offline packages remain available.
Install page: {base}
''',encoding='utf-8')
extension_repo=site/'extensions';query=urllib.parse.urlencode(dict(repository=base+'extensions/index.json',blender_version_min='5.3.0'));drag_url=base+'extensions/'+zip_name+'?'+query
samples=[]
for wanted in ['TM_CustomBricks_asset','TM_Water_asset','TM_PlatformDirt_DecoHill_asset','TM_RedIsland_DetailsToDirt_asset','TM_ItemRamp_asset','TM_PlatformIce_DecoGrass_asset']:
 m=next(x for x in all_assets if x['name']==wanted);samples.append(f'<figure><img loading="lazy" src="remote/tm2020-materials/{html.escape(m["thumbnail"]["url"])}" alt="{html.escape(wanted)}"><figcaption>{html.escape(wanted.removeprefix("TM_").removesuffix("_asset").replace("_"," "))}</figcaption></figure>')
total=sum(r['bytes'] for r in rows.values())
(site/'index.html').write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name} — Blender 5.3</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#151b21;color:#e8edf2;font:17px/1.65 system-ui,sans-serif}}main{{max-width:1080px;margin:auto;padding:64px 28px}}h1{{font-size:clamp(2.2rem,5vw,3.7rem);line-height:1.12;max-width:850px;letter-spacing:-.045em}}h2{{line-height:1.25}}a{{color:#9fd4ff}}.kicker{{color:#90c4ae;font-weight:650;letter-spacing:.08em;text-transform:uppercase;font-size:.8rem}}.lede{{max-width:750px;color:#bfcbd7;font-size:1.15rem}}.button{{display:inline-block;background:#d2f29c;color:#15221c;padding:16px 25px;border-radius:9px;font-weight:750;text-decoration:none;cursor:grab;box-shadow:0 5px 24px #0003}}.button:active{{cursor:grabbing}}.meta{{color:#aebac6;font-size:.9rem}}.actions{{display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin:26px 0 12px}}section{{margin-top:46px}}.gallery{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:30px 0}}figure{{margin:0}}figure img{{width:100%;border-radius:8px;background:#263039}}figcaption{{font-size:.75rem;line-height:1.35;color:#bdc9d4;margin-top:8px}}.panel{{background:#202a33;border:1px solid #35434f;border-radius:12px;padding:22px 28px}}li{{margin-bottom:10px}}code{{overflow-wrap:anywhere;color:#c6e99d}}details{{margin:20px 0}}summary{{cursor:pointer;font-weight:650}}footer{{border-top:1px solid #34404a;padding-top:25px;margin-top:48px;font-size:.85rem;color:#9facb8}}button{{background:#304557;color:#edf6ff;border:1px solid #4b6375;border-radius:6px;padding:8px 12px;cursor:pointer}}@media(max-width:700px){{.gallery{{grid-template-columns:repeat(3,1fr)}}main{{padding:38px 20px}}}}</style></head>
<body><main><p class="kicker">Asset library extension · Blender 5.3+</p><h1>{name}</h1><p class="lede">825 Trackmania materials in Blender's Asset Browser. Browse first, download what you need, and download updated material bundles when updates arrive.</p>
<div class="actions"><a id="install" class="button" draggable="true" href="{html.escape(drag_url)}">Drag into Blender to install ↗</a><a href="https://github.com/{repo}/releases/tag/{tag}">View extension release</a></div>
<p class="meta">First installation is a small extension ZIP. Materials download in small bundles that share packed textures. Windows, macOS and Linux · Blender 5.3 or newer.</p>
<div class="gallery">{''.join(samples)}</div>
<section class="panel"><h2>Install in Blender</h2><ol><li>Open Blender <strong>5.3 or newer</strong> and enable <strong>Online Access</strong> in Preferences → System.</li><li>Drag the green install button from this page into Blender. If prompted, confirm adding the extension repository and installing the library. Blender may ask you to drag the button again after adding the repository.</li><li>Under Preferences → Asset Libraries, enable <strong>{name}</strong> if needed. Select it in an Asset Browser.</li></ol><p>No PowerShell, local server or full-library download is required.</p></section>
<section><h2>Download and refresh</h2><p>Apply an asset to download its small material bundle and shared packed textures. A bundle may contain several related materials, reducing duplicate downloads. For the whole collection, clear the Asset Browser's search and catalog filters, select all assets and choose <strong>Download Assets</strong>. All material files currently total approximately <strong>{total/1e9:.2f} GB</strong>; Blender's local cache also needs space.</p><p>Use <strong>Refresh Remote Listing</strong> to discover updates, then download changed assets. Only changed bundles need downloading again; unchanged bundles remain reusable. Materials already appended to an open project keep their current version until you replace them.</p></section>
<details><summary>Manual installation and repository URL</summary><p><a href="{base}extensions/{zip_name}">Download the extension ZIP</a>, then use Preferences → Get Extensions → Install from Disk.</p><p>To browse this extension from Get Extensions, add our repository:</p><p><code id="repo">{base}extensions/index.json</code> <button type="button" onclick="navigator.clipboard.writeText(document.getElementById('repo').textContent).then(()=>this.textContent='Copied')">Copy URL</button></p></details>
<section><h2>Materials Only</h2><p>This extension contains the 825 native-linked material assets. Complete-only / Preview only entries and HDRI World assets are excluded. Blendermania and its MaterialLib setup are supplied separately. The earlier pilot can be disabled to avoid duplicate library entries.</p><p><a href="https://github.com/{repo}/blob/main/docs/BADGES.md">Thumbnail badge legend</a> · <a href="https://github.com/{repo}/releases/tag/v1.0.0-materials-only">Offline Materials Only ZIPs</a> · <a href="{base}pilot/">Earlier pilot</a></p></section>
<footer>Trackmania resources remain the property of Ubisoft/Nadeo and their respective owners. Native links and Blender previews do not guarantee identical in-game appearance or runtime behaviour. This independent project is not affiliated with Ubisoft/Nadeo.</footer></main>
<script>document.getElementById('install').addEventListener('dragstart',function(e){{const u=this.href;e.dataTransfer.setData('text/uri-list',u);e.dataTransfer.setData('text/plain',u);e.dataTransfer.effectAllowed='copy';}});</script></body></html>''',encoding='utf-8')
(site/'.nojekyll').write_text('');(site/'.gitattributes').write_text('* -text\n')
(out/'release-notes.md').write_text(f'''# {name}

**Asset Library Extension for Blender 5.3 and newer** · 825 Materials Only assets.

Install page with drag-and-drop button: {base}

Download **{zip_name}** to install manually through Preferences → Get Extensions → Install from Disk. This small ZIP registers the remote library; the `.blend` files below are downloaded by Blender as needed. You do not need to download them manually.

The complete collection is approximately {total/1e9:.2f} GB when every material file is downloaded. The collection uses shared-texture bundles; selecting one material downloads its containing bundle. Bundles include their required packed textures. Refresh Remote Listing retrieves updates; updating a few materials requires only the affected bundles, rather than the entire library. Existing scene materials are not automatically replaced.

Content based on the verified `2026.11.26-thumbnail-shadow-lift-1` collection: latest terrain transitions, water previews, icons and existing badges/native links. No Complete-only / Preview only entries, HDRI Worlds, or MaterialLib.txt. Blendermania supplies its own export setup. Offline ZIP releases and the earlier pilot remain available separately.
''',encoding='utf-8')
write(out/'plan.json',dict(repo=repo,tag=tag,title=name+' — Asset Library Extension for Blender 5.3',pages_branch='remote-library',pages_url=base,library_url=remote_url,extension_id=extension_id,extension_name=zip_name,library_name=name,version=version,source_revision=build['revision'],source_sha256=build['source_sha256'],file_count=len(rows),materials=list(materials_by_name),assets=payloads,total_bytes=total,drag_url=drag_url,repository_url=base+'extensions/index.json',source_export=str(root)))
print('FULL_REMOTE_SITE_PREPARED',len(payloads),total,flush=True)
