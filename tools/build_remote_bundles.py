"""Export stable shared-texture bundles without changing material contracts."""
import argparse, datetime, hashlib, json, shutil, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from build_remote_pilot import trees
from remote_materials_contract import contract, fingerprint

p=argparse.ArgumentParser()
for key in ['reference','plan','output']: p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=a.output.resolve();host=out/'host';(host/'materials').mkdir(parents=True,exist_ok=True);(out/'contracts').mkdir(exist_ok=True)
reference=json.loads((a.reference/'build-report.json').read_text());plan=json.loads(a.plan.read_text())
source=Path(reference['source']);assert sha(source)==reference['source_sha256']
assert len(reference['materials'])==plan['materials']==825
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
materials={m['tm_asset_id']:m for m in bpy.data.materials if m.asset_data}
rows={r['id']:r for r in reference['materials']}
assert set(materials)==set(rows)
for group in bpy.data.node_groups:
 if group.asset_data:group.asset_clear()
hashes={}
for m in materials.values():
 for tree in trees(m.node_tree):
  for node in tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   im=node.image
   if im.name in hashes:continue
   if im.source=='FILE':
    if not im.packed_file:
     path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file(),path
     im.filepath=str(path);im.pack()
    hashes[im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
   else:assert im.source=='GENERATED';hashes[im.name]=None
report={k:reference[k] for k in ['source','source_sha256','revision']};report.update(materials=[],bundles=[],bundle_plan=str(a.plan.resolve()))
state_path=out/'export-state.json';previous=json.loads(state_path.read_text()) if state_path.exists() else {};state={}
for i,bundle in enumerate(plan['bundles']):
 members=[materials[ident] for ident in bundle['materials']];contracts={}
 for m in members:
  ident=m['tm_asset_id'];old=rows[ident];data=contract(m,hashes)
  assert fingerprint(data)==old['fingerprint'],m.name
  shutil.copy2(a.reference/old['contract_path'],out/old['contract_path']);contracts[ident]=old['fingerprint']
 sig=fingerprint(contracts);relative='materials/'+bundle['id']+'.blend';dest=host/relative;old=previous.get(bundle['id'],{})
 if not (old.get('fingerprint')==sig and dest.is_file() and sha(dest)==old.get('sha256')):
  pending=dest.with_suffix('.pending.blend');bpy.data.libraries.write(str(pending),set(members),path_remap='NONE',fake_user=True,compress=True);pending.replace(dest)
 digest=sha(dest);size=dest.stat().st_size
 report['bundles'].append(dict(id=bundle['id'],path=relative,sha256=digest,bytes=size,materials=bundle['materials'],fingerprint=sig))
 for m in members:
  row=dict(rows[m['tm_asset_id']]);row.update(path=relative,sha256=digest,bytes=size,bundle_id=bundle['id']);report['materials'].append(row)
 state[bundle['id']]=dict(fingerprint=sig,sha256=digest);state_path.write_text(json.dumps(state))
 (out/'build-report.json').write_text(json.dumps(report));(out/'build-status.json').write_text(json.dumps(dict(phase='exporting',done=i+1,total=len(plan['bundles']),bytes=sum(r['bytes'] for r in report['bundles']))))
 print('BUNDLE_EXPORTED',i+1,len(plan['bundles']),bundle['id'],len(members),size,flush=True)
shutil.copy2(a.reference/'host/blender_assets.cats.txt',host/'blender_assets.cats.txt')
assert sha(source)==reference['source_sha256']
report.update(total_bytes=sum(r['bytes'] for r in report['bundles']),source_unchanged=True)
(out/'build-report.json').write_text(json.dumps(report));(out/'build-status.json').write_text(json.dumps(dict(phase='complete',materials=825,bundles=len(plan['bundles']),bytes=report['total_bytes'])))
print('ALL_BUNDLES_EXPORTED',report['total_bytes'],flush=True)
