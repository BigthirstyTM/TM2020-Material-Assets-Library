"""Remove quarantined assets from their stable remote bundle; reuse every other payload."""
import argparse,json,os,shutil,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from remote_materials_contract import fingerprint
p=argparse.ArgumentParser()
for key in ['reference','installation','inventory','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);ref=a.reference.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
receipt=json.loads(a.installation.read_text());source=Path(receipt['installed']);assert sha(source)==receipt['sha256']
inventory=json.loads(a.inventory.read_text())['materials'];allowed={r['name'] for r in inventory if not r['preview_only']};quarantined=set(receipt['quarantined']);assert len(allowed)==820
report=json.loads((ref/'build-report.json').read_text());original={r['id']:r for r in report['materials']};remove={r['id'] for r in report['materials'] if r['name'] in quarantined};assert len(remove)==5
report['materials']=[r for r in report['materials'] if r['id'] not in remove];assert {r['name'] for r in report['materials']}==allowed
affected=[];reused=[]
for bundle in report['bundles']:
 src=ref/'host'/bundle['path'];dest=out/'host'/bundle['path'];dest.parent.mkdir(parents=True,exist_ok=True)
 if set(bundle.get('materials',[]))&remove:
  ids=[i for i in bundle['materials'] if i not in remove];assert ids
  bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False);materials=[m for m in bpy.data.materials if m.asset_data and m.name in allowed]
  assert {m['tm_asset_id'] for m in materials}==set(ids)
  for m in bpy.data.materials:
   if m.name in quarantined:assert m not in materials
  bpy.data.libraries.write(str(dest),set(materials),path_remap='NONE',fake_user=True,compress=True)
  bundle.update(materials=ids,sha256=sha(dest),bytes=dest.stat().st_size,fingerprint=fingerprint({i:original[i]['fingerprint'] for i in ids}));affected.append(bundle['id'])
  for row in report['materials']:
   if row['path']==bundle['path']:row.update(sha256=bundle['sha256'],bytes=bundle['bytes'])
 else:
  if not dest.exists():os.link(src,dest)
  assert sha(dest)==bundle['sha256'];reused.append(bundle['id'])
for row in report['materials']+report.get('worlds',[]):
 dest=out/row['contract_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ref/row['contract_path'],dest)
shutil.copy2(source.parent/'blender_assets.cats.txt',out/'host/blender_assets.cats.txt')
if (ref/'compression.json').exists():shutil.copy2(ref/'compression.json',out/'compression.json')
report.update(source=str(source),source_sha256=receipt['sha256'],revision=receipt['revision'],asset_count=len(report['materials'])+len(report.get('worlds',[])),total_bytes=sum(r['bytes'] for r in report['bundles']),quarantine=dict(removed=sorted(quarantined),rebuilt_bundles=affected,reused_bundles=reused),source_unchanged=True)
assert len(affected)==1 and len(reused)==117
(out/'build-report.json').write_text(json.dumps(report));print('QUARANTINE_REMOTE_EXPORT_READY',len(report['materials']),len(report.get('worlds',[])),affected,len(reused),flush=True)
