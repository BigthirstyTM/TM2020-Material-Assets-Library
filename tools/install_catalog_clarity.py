"""Install a verified catalog update with checked inputs and rollback copies."""
import argparse,datetime,json,os,shutil,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
p=argparse.ArgumentParser()
for k in ['library','staged','output','documentation']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();stage=a.staged.resolve();out=a.output.resolve()
report=json.loads((stage/'build-report.json').read_text());proof=json.loads((out/'verification.json').read_text());baseline=json.loads((stage/'baseline.json').read_text())
assert proof['staged_sha256']==report['staged_sha256'] and proof['missing_images']==0 and proof['examples_verified']==4
source=root/'Trackmania2020_assets.blend';assert sha(source)==report['source_sha256']
assert sha(stage/source.name)==report['staged_sha256']
for row in report['support_files']:
 assert sha(root/row['path'])==row['previous_sha256'],row['path']
 assert sha(stage/row['path'])==row['sha256'],row['path']
bpy.ops.wm.open_mainfile(filepath=str(stage/source.name),load_ui=False)
icons={x.name:identity(x)['icon'] for x in bpy.data.materials if x.asset_data}
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path
  im.filepath='//'+path.relative_to(root).as_posix()
portable=out/'portable';portable.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(portable/source.name),compress=True,relative_remap=False)
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
files=[dict(path=source.name,source=portable/source.name,previous_sha256=report['source_sha256'])]+[dict(path=r['path'],source=stage/r['path'],previous_sha256=r['previous_sha256']) for r in report['support_files']]
files.append(dict(path='Documentation/CATALOG-CLARITY.md',source=a.documentation/'CATALOG-CLARITY.md',previous_sha256=None))
for row in files:
 dst=root/row['path']
 if row['previous_sha256']:assert sha(dst)==row['previous_sha256'],row['path']
 if dst.exists():
  saved=backup/row['path'];saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
 row['existed']=dst.exists()
installed=[]
try:
 for row in files:
  dst=root/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);pending=dst.with_name(dst.name+'.catalog-clarity-pending');shutil.copy2(row['source'],pending);os.replace(pending,dst);installed.append(row)
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 counts=[sum(bool(x.asset_data) for x in c) for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]];assert counts==[1119,20,42]
 resolved=0
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path;resolved+=1
 for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
  for x in coll:
   if not x.asset_data:continue
   key=x.bl_rna.identifier+':'+x.name;assert graph(x)==baseline[key]['graph'];assert x.get('tm_asset_effect_badges','')==baseline[key]['badges']
   old=baseline[key]['identity'].copy();now=identity(x)
   if x.name in report['targets']:old.pop('icon');now.pop('icon')
   if x.name==report['quarantine']:
    for k in ['catalog','description','tags','export']:old.pop(k);now.pop(k)
   assert old==now,key
 for name,digest in icons.items():assert identity(bpy.data.materials[name])['icon']==digest,name
 for row in report['support_files']:assert sha(root/row['path'])==row['sha256']
 for row in report['support_files']:
  if not row['path'].endswith('.blend'):continue
  bpy.ops.wm.open_mainfile(filepath=str(root/row['path']),load_ui=False)
  for prop in bpy.data.bl_rna.properties:
   if prop.type=='COLLECTION':assert not any(getattr(x,'asset_data',None) for x in getattr(bpy.data,prop.identifier))
 receipt=dict(revision=report['revision'],installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],backup=str(backup),missing_images=0,images_resolved=resolved,counts=counts,targets=len(report['targets']),duplicate_example_markers_removed=proof['duplicate_example_markers_removed'],release_packages_changed=False,files=[dict(path=r['path'],sha256=sha(root/r['path'])) for r in files])
 (out/'installation.json').write_text(json.dumps(receipt,indent=2));print('CATALOG_CLARITY_INSTALLED',receipt['sha256'],flush=True)
except BaseException:
 for row in reversed(installed):
  dst=root/row['path']
  if row['existed']:shutil.copy2(backup/row['path'],dst)
  else:dst.unlink(missing_ok=True)
 raise
