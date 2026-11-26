"""Add the offline Materials Only HDRI Worlds without rewriting material bundles."""
import argparse,hashlib,json,shutil,sys,os
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from remote_materials_contract import contract,fingerprint
from build_remote_pilot import trees
from apply_shader_fidelity import sha
p=argparse.ArgumentParser()
for k in ['reference','output']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--verify',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();ref=a.reference.resolve()
types=('TEX_IMAGE','TEX_ENVIRONMENT')
def images(w):return {n.image for t in trees(w.node_tree) for n in t.nodes if n.type in types and n.image}
if a.verify:
 report=json.loads((out/'build-report.json').read_text());checks=[]
 for row in report['worlds']:
  path=out/'host'/row['path'];assert sha(path)==row['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
  targets=[w for w in bpy.data.worlds if w.asset_data];assert len(targets)==1 and targets[0].name==row['name'];w=targets[0]
  hashes={}
  for image in images(w):
   assert image.packed_file;hashes[image.name]=hashlib.sha256(image.packed_file.data).hexdigest();image.filepath='//not-present/'+image.name
   assert image.size[0]>0 and len(image.pixels)>0
  actual=contract(w,hashes,types);expected=json.loads((out/row['contract_path']).read_text())
  assert fingerprint(actual)==fingerprint(expected)==row['fingerprint'],w.name
  bpy.context.scene.world=w;assert bpy.context.scene.world==w
  checks.append(dict(name=w.name,id=row['id'],catalog=w.asset_data.catalog_id,packed_images=len(hashes),assigned_to_scene=True))
  print('REMOTE_WORLD_VERIFIED',w.name,flush=True)
 assert len(checks)==20 and sha(Path(report['source']))==report['source_sha256']
 proof=json.loads((ref/'verification.json').read_text());proof.update(worlds=20,world_checks=checks,files=len(report['bundles']),asset_count=845)
 (out/'verification.json').write_text(json.dumps(proof,indent=2));print('ALL_REMOTE_WORLDS_VERIFIED',flush=True)
else:
 (out/'host/materials').mkdir(parents=True,exist_ok=True);(out/'contracts').mkdir(exist_ok=True)
 report=json.loads((ref/'build-report.json').read_text());assert len(report['materials'])==825 and len(report['bundles'])==98
 for row in report['bundles']:
  source=ref/'host'/row['path'];dest=out/'host'/row['path']
  if not dest.exists():os.link(source,dest)
  assert sha(dest)==row['sha256']
 for row in report['materials']:shutil.copy2(ref/row['contract_path'],out/row['contract_path'])
 shutil.copy2(ref/'host/blender_assets.cats.txt',out/'host/blender_assets.cats.txt')
 assert sha(Path(report['source']))==report['source_sha256'];bpy.ops.wm.open_mainfile(filepath=report['source'],load_ui=False)
 worlds=sorted((w for w in bpy.data.worlds if w.asset_data),key=lambda w:w.name);assert len(worlds)==20
 for group in bpy.data.node_groups:
  if group.asset_data:group.asset_clear()
 report['worlds']=[];mapping_path=Path(__file__).resolve().parents[1]/'data/remote-world-bundles.json';mapping=json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
 for i,w in enumerate(worlds):
  hashes={}
  for image in images(w):
   assert image.source=='FILE'
   if not image.packed_file:image.filepath=bpy.path.abspath(image.filepath);image.pack()
   hashes[image.name]=hashlib.sha256(image.packed_file.data).hexdigest()
  data=contract(w,hashes,types);ident=w.get('tm_asset_id') or 'world-'+hashlib.sha256(w.name.encode()).hexdigest()[:24]
  # Preserve source IDs/properties. The listing can identify a World by name/catalog.
  bundle=mapping[w.name]['bundle_id'] if w.name in mapping else f'bundle-{99+i:04d}';relative='materials/'+bundle+'.blend';dest=out/'host'/relative
  bpy.data.libraries.write(str(dest),{w},path_remap='NONE',fake_user=True,compress=True)
  contract_path='contracts/'+ident+'.json';(out/contract_path).write_text(json.dumps(data))
  row=dict(name=w.name,id=ident,path=relative,sha256=sha(dest),bytes=dest.stat().st_size,contract_path=contract_path,fingerprint=fingerprint(data),bundle_id=bundle)
  report['worlds'].append(row);report['bundles'].append(dict(id=bundle,path=relative,sha256=row['sha256'],bytes=row['bytes'],worlds=[ident],fingerprint=row['fingerprint']))
  print('REMOTE_WORLD_EXPORTED',w.name,row['bytes'],flush=True)
 report.update(total_bytes=sum(r['bytes'] for r in report['bundles']),asset_count=845)
 (out/'build-report.json').write_text(json.dumps(report));assert sha(Path(report['source']))==report['source_sha256']
 print('REMOTE_WORLDS_ADDED',len(worlds),report['total_bytes'],flush=True)
