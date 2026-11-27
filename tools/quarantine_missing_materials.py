"""Quarantine the five audited missing native links, with preservation and backup checks."""
import argparse,datetime,json,os,re,shutil,sys,uuid
from pathlib import Path
import bpy,addon_utils
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha

REVISION='2026.11.27-missing-material-quarantine-1'
NAMES={'TM_16x9ScreenOff_asset','TM_Ad16x9Screen_asset','TM_PodiumScreen16x9_asset','TM_WarpScreen16x9B_asset','TM_WarpScreen16x9C_asset'}
p=argparse.ArgumentParser()
for key in ['library','inventory','audit','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
source=root/'Trackmania2020_assets.blend';expected='461e1fd8d6b6a26e68bd99af305c1cb0e6e3e9ca0fbf2f0776f23fbf9ae94a30';assert sha(source)==expected
audit=json.loads(a.audit.read_text());broken={r['name']:r for r in audit['materials'] if 'library:target_absent' in r['issues']};assert set(broken)==NAMES
addon_utils.enable('blendermania-addon',default_set=False)
for h in list(bpy.app.handlers.load_post):
 if h.__module__.startswith('blendermania-addon'):bpy.app.handlers.load_post.remove(h)
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
def assets():return {x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
before={k:dict(identity=identity(v),graph=graph(v),badges=v.get('tm_asset_effect_badges',''),link=getattr(v,'link',None)) for k,v in assets().items()}
assert len([m for m in bpy.data.materials if m.asset_data])==1119
catalog='Trackmania2020/08 Preview only/Missing native materials';cid=str(uuid.uuid5(uuid.NAMESPACE_URL,'tm2020-assets/'+catalog));reason='Native game material target is absent from the current game archives. Original preview retained; no replacement material or texture selected.'
for name in sorted(NAMES):
 m=bpy.data.materials[name];assert m.link==broken[name]['alias'];m['tm_missing_native_previous_export']=json.dumps(dict(alias=m.link,game_path=m.get('tm_game_material_path',''),serialized=m.get('MAT_PROPS_AS_JSON','')))
 m['tm_missing_native_target']=broken[name]['materiallibs']['library'][0]['target'];m['tm_missing_native_quarantine_revision']=REVISION
 m.link='';m['link']='';m['tm_game_material_path']='';m['tm_game_material_exportable']=False
 payload=json.loads(m.get('MAT_PROPS_AS_JSON','{}'));payload.update(name=name,link='');m['MAT_PROPS_AS_JSON']=json.dumps(payload)
 m['tm_preview_only_reason']=reason;m['tm_export_binding_status']='preview_only_missing_native_material';m['tm_current_export_status']='Preview only - missing native game material';m['tm_current_export_evidence']=reason;m['tm_current_runtime_status']='user_reported_red_missing_target' if name=='TM_16x9ScreenOff_asset' else 'missing_target_confirmed_from_current_archives'
 m.asset_data.catalog_id=cid;m.asset_data.description='Preview only. '+reason
 if 'Preview only' not in {t.name for t in m.asset_data.tags}:m.asset_data.tags.new('Preview only')
def verify():
 current=assets();assert set(current)==set(before)
 for key,m in current.items():
  previous=before[key];assert graph(m)==previous['graph'],('Shader changed',key)
  assert m.get('tm_asset_effect_badges','')==previous['badges'];now=identity(m);prior=previous['identity'].copy()
  if m.name in NAMES:
   assert not m.link and not json.loads(m['MAT_PROPS_AS_JSON'])['link'] and not m['tm_game_material_exportable'];assert m.asset_data.catalog_id==cid
   for field in ['catalog','description','tags','export']:now.pop(field);prior.pop(field)
  else:assert getattr(m,'link',None)==previous['link'],key
  assert now==prior,('Unrelated identity/thumbnail changed',key)
 for image in bpy.data.images:
  if image.source=='FILE' and image.filepath and not image.packed_file:assert Path(bpy.path.abspath(image.filepath)).is_file(),image.filepath
 return dict(assets=len(current),materials=sum(bool(m.asset_data) for m in bpy.data.materials),worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),graphs_unchanged=True,all_icons_and_badges_unchanged=True,missing_images=0)
verify();pending=root/'Trackmania2020_missing_materials.pending.blend';assert not pending.exists()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(pending),compress=True,relative_remap=False)
bpy.ops.wm.open_mainfile(filepath=str(pending),load_ui=False);proof=verify()
catalogs=(root/'blender_assets.cats.txt').read_text(encoding='utf-8-sig');assert cid not in catalogs;catalogs+='\n'+cid+':'+catalog+':Missing native materials\n'
aliases={r['alias'] for r in broken.values()}
def clean_definitions(path):
 lines=path.read_bytes().splitlines(keepends=True);keep=[];removed=[];skip=False
 for line in lines:
  match=re.match(rb'\s*D(Material|Library)\s*\(([^)]+)\)',line)
  if match:
   skip=match[1]==b'Material' and match[2].decode() in aliases
   if skip:removed.append(match[2].decode())
  if not skip:keep.append(line)
 assert set(removed)==aliases,(path,removed)
 return b''.join(keep)
files={root/'MaterialLib.txt':clean_definitions(root/'MaterialLib.txt'),root/'blender_assets.cats.txt':catalogs.encode('utf-8')}
for version in ['5.2','5.3']:
 path=Path.home()/f'AppData/Roaming/Blender Foundation/Blender/{version}/scripts/addons/blendermania-addon/assets/materials/MaterialLib.txt'
 if path.is_file():files[path]=clean_definitions(path)
inventory=json.loads(a.inventory.read_text());assert len(inventory['materials'])==1119
for row in inventory['materials']:
 if row['name'] in NAMES:row.update(preview_only=True,catalog=catalog,preview_only_reason=reason);row['effective']['link']=''
assert sum(not r['preview_only'] for r in inventory['materials'])==820
(out/'source-materials.json').write_text(json.dumps(inventory,indent=2)+'\n');(out/'baseline.json').write_text(json.dumps(before,indent=2))
assert sha(source)==expected
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
shutil.copy2(source,backup/source.name)
for i,path in enumerate(files):shutil.copy2(path,backup/(str(i)+'-'+path.name))
try:
 os.replace(pending,source)
 for path,data in files.items():
  temp=path.with_name(path.name+'.quarantine-pending');temp.write_bytes(data);os.replace(temp,path)
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);verify()
except Exception:
 shutil.copy2(backup/source.name,source)
 for i,path in enumerate(files):shutil.copy2(backup/(str(i)+'-'+path.name),path)
 raise
receipt=dict(revision=REVISION,installed=str(source),sha256=sha(source),previous_sha256=expected,backup=str(backup),quarantined=sorted(NAMES),catalog_id=cid,catalog_path=catalog,counts={'materials_only':820,'complete':1119,'preview_only':299,'worlds':20},preservation=proof,materiallib_files=[str(x) for x in files if x.name=='MaterialLib.txt'],source_inventory=str(out/'source-materials.json'),public_packages_updated=False,game_started=False)
(out/'installation.json').write_text(json.dumps(receipt,indent=2));print('MISSING_MATERIALS_QUARANTINED',json.dumps(receipt),flush=True)
