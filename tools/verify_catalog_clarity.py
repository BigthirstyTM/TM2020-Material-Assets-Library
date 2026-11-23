"""Fresh-file preservation checks for the catalog clarity update."""
import argparse,json,sys,re
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,badge_mask
p=argparse.ArgumentParser()
for k in ['library','staged','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);stage=a.staged.resolve();root=a.library.resolve()
report=json.loads((stage/'build-report.json').read_text());baseline=json.loads((stage/'baseline.json').read_text())
assert sha(stage/'Trackmania2020_assets.blend')==report['staged_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
badges={m.name:(badge_mask(m),pixels(m)) for m in bpy.data.materials if m.asset_data}
example_baseline={}
for row in report['support_files']:
 if not row['path'].endswith('.blend'):continue
 bpy.ops.wm.open_mainfile(filepath=str(root/row['path']),load_ui=False)
 example_baseline[row['path']]=dict(graphs={m.name:graph(m) for m in bpy.data.materials},objects=sorted(o.name for o in bpy.data.objects),scenes=sorted(s.name for s in bpy.data.scenes))
bpy.ops.wm.open_mainfile(filepath=str(stage/'Trackmania2020_assets.blend'),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
assert set(assets)==set(baseline)
ids=[x.get('tm_asset_id') for x in assets.values() if x.get('tm_asset_id')];assert len(ids)==len(set(ids))
missing=[]
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.filepath)
assert not missing,missing
for key,x in assets.items():
 assert graph(x)==baseline[key]['graph'],key
 assert x.get('tm_asset_effect_badges','')==baseline[key]['badges'],key
 old=baseline[key]['identity'].copy();new=identity(x)
 if x.name in report['targets']:
  old.pop('icon');new.pop('icon')
 if x.name==report['quarantine']:
  for k in ['catalog','description','tags','export']:old.pop(k);new.pop(k)
 assert old==new,key
 if x.name in badges:
  mask,original=badges[x.name];assert np.array_equal(pixels(x)[mask],original[mask]),key
flag=bpy.data.materials[report['quarantine']]
assert not flag['link'] and not flag['tm_game_material_path'] and not flag['tm_game_material_exportable']
assert flag.asset_data.catalog_id==report['quarantine_catalog_id']
counts=[sum(bool(x.asset_data) for x in c) for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]]
assert counts==[1119,20,42],counts
before=(root/'MaterialLib.txt').read_bytes();after=(stage/'MaterialLib.txt').read_bytes()
lines=before.splitlines(keepends=True);start=next(i for i,l in enumerate(lines) if re.match(rb'\s*DMaterial\(Stadium_ItemFlag\)',l));end=next(i for i in range(start+1,len(lines)) if re.match(rb'\s*D(?:Material|Library)\(',lines[i]))
assert after==b''.join(lines[:start]+lines[end:])
assert b'DMaterial(ItemFlagNoAnim)' in after and b'DMaterial(Stadium_ItemFlagNoAnim)' in after
cleared=0
for row in report['support_files']:
 assert sha(stage/row['path'])==row['sha256']
 if not row['path'].endswith('.blend'):continue
 bpy.ops.wm.open_mainfile(filepath=str(stage/row['path']),load_ui=False)
 for prop in bpy.data.bl_rna.properties:
  if prop.type=='COLLECTION':assert not any(getattr(x,'asset_data',None) for x in getattr(bpy.data,prop.identifier)),row['path']
 old=example_baseline[row['path']]
 now=dict(graphs={m.name:graph(m) for m in bpy.data.materials},objects=sorted(o.name for o in bpy.data.objects),scenes=sorted(s.name for s in bpy.data.scenes))
 if old!=now:
  (stage/'example-difference.json').write_text(json.dumps(dict(path=row['path'],before=old,after=now),indent=2))
 assert old==now,row['path']
 assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
 cleared+=len(row['cleared'])
proof=dict(revision=report['revision'],staged_sha256=report['staged_sha256'],materials=counts[0],worlds=counts[1],groups=counts[2],missing_images=0,graphs_preserved=len(assets),badges_preserved=True,duplicate_example_markers_removed=cleared,targets=len(report['targets']),examples_verified=4,materiallib_only_animated_alias_removed=True)
a.output.write_text(json.dumps(proof,indent=2));print('CATALOG_CLARITY_VERIFIED',json.dumps(proof),flush=True)
