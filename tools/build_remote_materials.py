"""Export all Materials Only assets as independent packed, incrementally reusable files."""
import argparse,hashlib,json,sys,shutil,datetime
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from build_remote_pilot import trees
from remote_materials_contract import contract,fingerprint

p=argparse.ArgumentParser()
for k in ['source','inventory','output']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--only',action='append',help='Bounded export for contract/reuse testing.')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=a.source.resolve();out=a.output.resolve();host=out/'host';(host/'materials').mkdir(parents=True,exist_ok=True);(out/'contracts').mkdir(exist_ok=True)
source_hash=sha(source);inventory={r['name']:r for r in json.loads(a.inventory.read_text())['materials']}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
targets=sorted((m for m in bpy.data.materials if m.asset_data and not inventory[m.name]['preview_only']),key=lambda x:x.name)
assert len(targets)==825
if a.only:
 targets=[m for m in targets if m.name in a.only];assert len(targets)==len(a.only)
for g in bpy.data.node_groups:
 if g.asset_data:g.asset_clear()
state_path=out/'export-state.json';previous=json.loads(state_path.read_text()) if state_path.exists() else {};state=dict(previous)
hashes={};report=dict(source=str(source),source_sha256=source_hash,materials=[],changed=[],unchanged=[],revision='2026.11.26-thumbnail-shadow-lift-1')
for i,m in enumerate(targets):
 images={n.image for tree in trees(m.node_tree) for n in tree.nodes if n.type=='TEX_IMAGE' and n.image};image_hashes={}
 for im in images:
  if im.source=='FILE':
   if im.packed_file:im_hash=hashlib.sha256(im.packed_file.data).hexdigest()
   else:
    path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file(),path
    key=str(path)
    if key not in hashes:hashes[key]=sha(path)
    im_hash=hashes[key];im.filepath=str(path);im.pack()
   image_hashes[im.name]=im_hash
  else:
   assert im.source=='GENERATED',(m.name,im.name,im.source);image_hashes[im.name]=None
 data=contract(m,image_hashes);sig=fingerprint(data);ident=m['tm_asset_id'];relative='materials/'+ident+'.blend';dest=host/relative;old=previous.get(ident,{})
 if old.get('fingerprint')==sig and dest.is_file() and sha(dest)==old.get('sha256'):report['unchanged'].append(relative)
 else:
  pending=dest.with_suffix('.pending.blend');bpy.data.libraries.write(str(pending),{m},path_remap='NONE',fake_user=True,compress=True);pending.replace(dest);report['changed'].append(relative)
 contract_path='contracts/'+ident+'.json';(out/contract_path).write_text(json.dumps(data))
 row=dict(name=m.name,id=ident,path=relative,bytes=dest.stat().st_size,sha256=sha(dest),fingerprint=sig,contract_path=contract_path)
 report['materials'].append(row);state[ident]=dict(fingerprint=sig,sha256=row['sha256'])
 state_path.write_text(json.dumps(state));(out/'build-report.json').write_text(json.dumps(report))
 (out/'build-status.json').write_text(json.dumps(dict(pid=__import__('os').getpid(),phase='exporting',done=i+1,total=len(targets),material=m.name,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))
 print('REMOTE_MATERIAL_EXPORTED',i+1,len(targets),m.name,row['bytes'],flush=True)
shutil.copy2(source.parent/'blender_assets.cats.txt',host/'blender_assets.cats.txt')
assert sha(source)==source_hash
report.update(total_bytes=sum(r['bytes'] for r in report['materials']),source_unchanged=True)
(out/'build-report.json').write_text(json.dumps(report));(out/'build-status.json').write_text(json.dumps(dict(phase='complete',materials=len(targets),bytes=report['total_bytes'])));print('REMOTE_MATERIALS_EXPORTED',len(targets),report['total_bytes'],flush=True)
