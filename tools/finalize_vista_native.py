"""Reopen, verify and atomically install the promoted vista library with rollback."""
import bpy,addon_utils,json,sys,shutil,datetime,os,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
base=Path.cwd();root=Path(r'C:/Users/micph/Documents/Trackmania/Items/_BlenderAssets');out=base/'build/vista-native';stage=out/'stage';source=root/'Trackmania2020_assets.blend';staged=stage/source.name
report=json.loads((stage/'build-report.json').read_text());baseline=json.loads((stage/'baseline.json').read_text());promoted={r['name']:r for r in report['promoted']};fixed=set(report['projection_fixed'])
assert sha(source)==report['source_sha256'];assert sha(staged)==report['staged_sha256']
addon_utils.enable('blendermania-addon',default_set=False)
bpy.ops.wm.open_mainfile(filepath=str(staged),load_ui=False)
inventory=json.loads((base/'TM2020-Material-Assets-Library/data/source-materials.json').read_text());inventory_by_name={r['name']:r for r in inventory['materials']}
serialize=importlib.import_module('blendermania-addon.utils.Materials').save_mat_props_json
for name,r in promoted.items():
 m=bpy.data.materials[name];old=inventory_by_name[name]
 m.physicsId=old['collision']['physics'];m.gameplayId=old['collision']['gameplay'];m.link=r['alias'];serialize(m)
 old.update(preview_only=False,effective=dict(link=r['alias']),catalog=r['catalog'],preview_type='Native-linked vista material',usage_tags=['BaseMaterial UV','Game checked: vista fixture'],preview_limitations=r['preview_limitations'],runtime_check=report['game_evidence'])
 old['usage']=[x for x in old['usage'] if not x.startswith('Preview only')];old.pop('preview_only_reason',None)
 if name in fixed:old['thumbnail_revision']=report['revision']
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and im.filepath.startswith('//'):assert (root/im.filepath[2:]).is_file(),im.filepath
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(staged),compress=True,relative_remap=False)
report['staged_sha256']=sha(staged);(stage/'build-report.json').write_text(json.dumps(report,indent=2))
(stage/'source-materials.json').write_text(json.dumps(inventory,indent=2)+'\n')
def verify(path):
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);checks=[]
 blocks={x.bl_rna.identifier+':'+x.name:x for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in coll if x.asset_data}
 assert set(blocks)==set(baseline)
 for key,x in blocks.items():
  old=baseline[key];assert x.get('tm_asset_id')==old['id'] and x.get('tm_asset_effect_badges','')==old['badges'],key
  if x.name not in promoted:assert identity(x)==old['identity'] and graph(x)==old['graph'],key
  else:
   r=promoted[x.name];assert x.link==r['alias'] and json.loads(x['MAT_PROPS_AS_JSON'])['link']==r['alias']
   assert not x['tm_preview_only'] and x['tm_game_material_exportable'] and 'Preview only' not in x.asset_data.description
   if x.name not in fixed:assert graph(x)==old['graph'] and identity(x)['icon']==old['identity']['icon'],key
   assert x.preview_ensure().image_size[:]==(256,256)
   checks.append(dict(name=x.name,alias=x.link,physics=x.physicsId,gameplay=x.gameplayId,icon_verified=True))
 mats=[m for m in bpy.data.materials if m.asset_data];worlds=[w for w in bpy.data.worlds if w.asset_data];assert len(mats)==1172 and len(worlds)==20
 assert sum(not row['preview_only'] for row in inventory['materials'])==873 and sum(row['preview_only'] for row in inventory['materials'])==299
 for row in inventory['materials']:
  if not row['preview_only']:assert bpy.data.materials[row['name']].link==row['effective']['link'],row['name']
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and not im.packed_file:assert (root/im.filepath[2:]).is_file() if im.filepath.startswith('//') else Path(im.filepath).is_file(),im.filepath
 return dict(revision=report['revision'],sha256=sha(path),materials=1172,materials_only=873,preview_only=299,worlds=20,promoted=checks,projection_fixed=sorted(fixed),old_assets_preserved=len(blocks)-53,missing_images=0)
proof=verify(staged);(out/'verification.json').write_text(json.dumps(proof,indent=2))
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
for p in [source,root/'blender_assets.cats.txt']:shutil.copy2(p,backup/p.name)
assert sha(root/'MaterialLib.txt')==report['materiallib_sha256'];assert sha(source)==report['source_sha256']
pending=root/'Trackmania2020_vista_native.pending.blend';shutil.copy2(staged,pending)
try:
 shutil.copy2(stage/'blender_assets.cats.txt',root/'blender_assets.cats.txt');os.replace(pending,source);installed=verify(source)
except Exception:
 for p in backup.iterdir():shutil.copy2(p,root/p.name)
 raise
(out/'installed-verification.json').write_text(json.dumps(installed,indent=2));receipt=dict(revision=report['revision'],installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],backup=str(backup.resolve()),materials_only=873,preview_only=299,worlds=20,promoted=53,projection_fixed=6,materiallib_unchanged=True,remote_changed=False,offline_packages_changed=False)
(out/'installation.json').write_text(json.dumps(receipt,indent=2));shutil.copy2(stage/'source-materials.json',base/'TM2020-Material-Assets-Library/data/source-materials.json')
print('VISTA_NATIVE_INSTALLED_AND_VERIFIED',receipt['sha256'],flush=True)
