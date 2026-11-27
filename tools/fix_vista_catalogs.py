"""Correct only the 53 vista catalog IDs, with reopened preservation checks."""
import argparse,datetime,json,os,shutil,sys,uuid
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha,identity,graph
from vista_catalogs import material_catalog
p=argparse.ArgumentParser()
for k in ['installation','output','inventory']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
old=json.loads(a.installation.read_text());source=Path(old['installed']);root=source.parent;assert sha(source)==old['sha256']
revision='2026.11.27-vista-catalogs-1';inventory=json.loads(a.inventory.read_text());names={r['name'] for r in json.loads((Path.cwd()/'build/vista-native/stage/build-report.json').read_text())['promoted']}
assert len(names)==53
catalogs=(root/'blender_assets.cats.txt').read_text(encoding='utf-8');by_path={p[1]:p[0] for line in catalogs.splitlines() if len(p:=line.split(':',2))==3 and not line.startswith('#')}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
def blocks():return {x.bl_rna.identifier+':'+x.name:x for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in coll if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),id=x.get('tm_asset_id'),badges=x.get('tm_asset_effect_badges','')) for k,x in blocks().items()}
changes=[]
for row in inventory['materials']:
 if row['name'] not in names:continue
 m=bpy.data.materials[row['name']];env=m['tm_vista_source'].split('/')[0];path=material_catalog(m.name,env)
 if path not in by_path:
  cid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://bigthirstytm.github.io/TM2020-Material-Assets-Library/catalog/'+path));by_path[path]=cid;catalogs+='\n'+cid+':'+path+':'+path.replace('/','-')+'\n'
 changes.append(dict(name=m.name,old_catalog=row['catalog'],catalog=path,catalog_id=by_path[path]));m.asset_data.catalog_id=by_path[path];row['catalog']=path
assert len(changes)==53
staged=out/source.name;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(staged),compress=True,relative_remap=False)
by_uuid={v:k for k,v in by_path.items()};changed={r['name']:r for r in changes}
def verify(path):
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);actual=blocks();assert set(actual)==set(baseline)
 for k,x in actual.items():
  before=baseline[k];now=identity(x)
  if x.name in changed:
   assert now['catalog']==changed[x.name]['catalog_id'];now['catalog']=before['identity']['catalog']
  assert now==before['identity'] and graph(x)==before['graph'] and x.get('tm_asset_id')==before['id'] and x.get('tm_asset_effect_badges','')==before['badges'],k
  path=by_uuid[x.asset_data.catalog_id]
  if isinstance(x,bpy.types.Material):assert '/06 HDRI World Moods' not in path,k
  elif isinstance(x,bpy.types.World):assert path.startswith('Trackmania2020/06 HDRI World Moods/'),k
 return dict(assets_checked=len(actual),catalogs_changed=53,all_graphs_icons_badges_ids_preserved=True,materials_in_hdri=0,worlds_outside_hdri=0)
proof=verify(staged);backup=out/'backup';backup.mkdir(exist_ok=True)
for name in [source.name,'blender_assets.cats.txt']:shutil.copy2(root/name,backup/name)
shutil.copy2(a.inventory,backup/'source-materials.json')
assert sha(source)==old['sha256']
try:
 pending=root/(source.name+'.catalog-pending');shutil.copy2(staged,pending);os.replace(pending,source);(root/'blender_assets.cats.txt').write_text(catalogs,encoding='utf-8');proof=verify(source)
except Exception:
 for name in [source.name,'blender_assets.cats.txt']:shutil.copy2(backup/name,root/name)
 raise
(out/'blender_assets.cats.txt').write_text(catalogs,encoding='utf-8');a.inventory.write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
receipt=dict(revision=revision,installed=str(source),sha256=sha(source),previous_sha256=old['sha256'],backup=str(backup),materials_only=873,preview_only=299,worlds=20,catalogs_changed=53,changes=changes)
(out/'installation.json').write_text(json.dumps(receipt,indent=2));(out/'verification.json').write_text(json.dumps(proof,indent=2));(out/'baseline.json').write_text(json.dumps(baseline))
print('VISTA_CATALOGS_INSTALLED_VERIFIED',receipt['sha256'],flush=True)
