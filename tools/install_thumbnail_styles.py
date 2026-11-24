"""Install verified icon-only library update with a backup and rollback."""
import argparse,datetime,json,os,shutil,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
p=argparse.ArgumentParser()
for k in ['library','staged','documentation','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();stage=a.staged.resolve();out=a.output.resolve();source=root/'Trackmania2020_assets.blend'
report=json.loads((stage/'build-report.json').read_text());proof=json.loads((stage/'verification.json').read_text());baseline=json.loads((stage/'baseline.json').read_text())
assert proof['revision']==report['revision'] and proof['staged_sha256']==report['staged_sha256'] and proof['missing_images']==0
assert sha(source)==report['source_sha256'] and sha(stage/source.name)==report['staged_sha256']
unchanged={p.relative_to(root).as_posix():sha(p) for p in [root/'MaterialLib.txt',root/'blender_assets.cats.txt']+list(root.rglob('*.blend')) if p!=source}
bpy.ops.wm.open_mainfile(filepath=str(stage/source.name),load_ui=False)
icons={m.name:identity(m)['icon'] for m in bpy.data.materials if m.asset_data}
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path;im.filepath='//'+path.relative_to(root).as_posix()
portable=out/'portable';portable.mkdir(exist_ok=True,parents=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(portable/source.name),compress=True,relative_remap=False)
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
docs=['THUMBNAIL-STYLES.md','CATALOG-CLARITY.md','BADGES.md']
files=[(source,portable/source.name)]+[(root/'Documentation'/name,a.documentation/name) for name in docs]
existed={str(dst):dst.exists() for dst,src in files}
for dst,src in files:
 assert src.is_file(),src
 if dst.exists():
  saved=backup/dst.relative_to(root);saved.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(dst,saved)
assert sha(source)==report['source_sha256']
installed=[]
try:
 for dst,src in files:
  dst.parent.mkdir(parents=True,exist_ok=True);pending=dst.with_name(dst.name+'.thumbnail-pending');shutil.copy2(src,pending);os.replace(pending,dst);installed.append(dst)
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data};assert set(assets)==set(baseline)
 for key,x in assets.items():
  assert graph(x)==baseline[key]['graph'],key
  assert x.get('tm_asset_effect_badges','')==baseline[key]['badges'],key
  old=baseline[key]['identity'].copy();now=identity(x)
  if x.name in report['targets']:old.pop('icon');now.pop('icon')
  assert old==now,key
 for name,digest in icons.items():assert identity(bpy.data.materials[name])['icon']==digest,name
 resolved=0
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root);resolved+=1
 assert all(sha(root/name)==digest for name,digest in unchanged.items())
 receipt=dict(revision=report['revision'],installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],backup=str(backup),counts=report['counts'],icons_updated=len(report['targets']),preserved=len(report['preserved']),missing_images=0,images_resolved=resolved,unchanged_support=unchanged,documentation=docs,release_packages_changed=False)
 (out/'installation.json').write_text(json.dumps(receipt,indent=2));print('THUMBNAIL_STYLES_INSTALLED',receipt['sha256'],flush=True)
except BaseException:
 for dst in reversed(installed):
  if existed[str(dst)]:shutil.copy2(backup/dst.relative_to(root),dst)
  else:dst.unlink(missing_ok=True)
 raise
