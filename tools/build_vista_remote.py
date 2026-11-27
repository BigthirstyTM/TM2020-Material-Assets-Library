"""Append four stable vista bundles, reusing all published material/HDRI bytes."""
import bpy,argparse,datetime,json,os,shutil,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from build_remote_pilot import trees
from remote_materials_contract import contract,fingerprint
p=argparse.ArgumentParser()
for k in ['reference','installation','inventory','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);ref=a.reference.resolve();out=a.output.resolve();out.mkdir(exist_ok=True,parents=True);host=out/'host';host.mkdir(exist_ok=True)
receipt=json.loads(a.installation.read_text());source=Path(receipt['installed']);assert sha(source)==receipt['sha256']
report=json.loads((ref/'build-report.json').read_text());assert len(report['materials'])==820 and len(report['worlds'])==20 and len(report['bundles'])==118
inventory=json.loads(a.inventory.read_text())['materials'];allowed={r['name'] for r in inventory if not r['preview_only']};new=allowed-{r['name'] for r in report['materials']};assert len(new)==53
for bundle in report['bundles']:
 src=ref/'host'/bundle['path'];dest=host/bundle['path'];dest.parent.mkdir(exist_ok=True,parents=True)
 if not dest.exists():os.link(src,dest)
 assert sha(dest)==bundle['sha256']
for r in report['materials']+report['worlds']:
 dest=out/r['contract_path'];dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(ref/r['contract_path'],dest)
if (ref/'compression.json').exists():shutil.copy2(ref/'compression.json',out/'compression.json')
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
for g in bpy.data.node_groups:
 if g.asset_data:g.asset_clear()
hashes={}
for index,env in enumerate(['BlueBay','GreenCoast','RedIsland','WhiteShore'],119):
 members=[bpy.data.materials[n] for n in sorted(new) if bpy.data.materials[n]['tm_vista_source'].startswith(env+'/')];assert members
 rows=[];contracts={};ident=f'bundle-{index:04d}';relative='materials/'+ident+'.blend';dest=host/relative
 for m in members:
  image_hashes={}
  for tree in trees(m.node_tree):
   for node in tree.nodes:
    if node.type!='TEX_IMAGE' or not node.image:continue
    im=node.image
    if im.name not in hashes:
     if im.source=='FILE':
      if not im.packed_file:
       path=Path(bpy.path.abspath(im.filepath));assert path.is_file();im.filepath=str(path);im.pack()
      hashes[im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
     else:assert im.source=='GENERATED';hashes[im.name]=None
    image_hashes[im.name]=hashes[im.name]
  data=contract(m,image_hashes);sig=fingerprint(data);mid=m['tm_asset_id'];cp='contracts/'+mid+'.json';(out/cp).write_text(json.dumps(data));contracts[mid]=sig
  rows.append(dict(name=m.name,id=mid,path=relative,fingerprint=sig,contract_path=cp,bundle_id=ident))
 pending=dest.with_suffix('.pending.blend');bpy.data.libraries.write(str(pending),set(members),path_remap='NONE',fake_user=True,compress=True);pending.replace(dest)
 digest=sha(dest);size=dest.stat().st_size
 report['bundles'].append(dict(id=ident,path=relative,sha256=digest,bytes=size,materials=[r['id'] for r in rows],fingerprint=fingerprint(contracts)))
 for r in rows:r.update(sha256=digest,bytes=size)
 report['materials'].extend(rows);print('VISTA_BUNDLE_BUILT',env,len(rows),size,flush=True)
report.update(source=str(source),source_sha256=receipt['sha256'],revision=receipt['revision'],asset_count=893,total_bytes=sum(b['bytes'] for b in report['bundles']),vista_update=dict(added=sorted(new),old_payloads_reused=118,new_bundles=4),source_unchanged=True)
assert len(report['materials'])==873 and {r['name'] for r in report['materials']}==allowed
shutil.copy2(source.parent/'blender_assets.cats.txt',host/'blender_assets.cats.txt');(out/'build-report.json').write_text(json.dumps(report));assert sha(source)==receipt['sha256']
print('VISTA_REMOTE_INCREMENTAL_READY',report['total_bytes'],flush=True)
