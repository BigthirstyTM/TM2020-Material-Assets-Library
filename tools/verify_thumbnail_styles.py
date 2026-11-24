"""Fresh-file checks of icon-only changes against their installed baseline."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,badge_mask
from thumbnail_preview_pixels import read_saved_preview
p=argparse.ArgumentParser()
for k in ['library','staged','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();stage=a.staged.resolve()
report=json.loads((stage/'build-report.json').read_text());baseline=json.loads((stage/'baseline.json').read_text());targets=set(report['targets'])
assert sha(root/'Trackmania2020_assets.blend')==report['source_sha256']
assert sha(stage/'Trackmania2020_assets.blend')==report['staged_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
badges={m.name:(badge_mask(m),pixels(m)) for m in bpy.data.materials if m.asset_data}
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return (v.bl_rna.identifier,v.name)
 if hasattr(v,'items'):return {k:value(x) for k,x in v.items()}
 return [value(x) for x in v]
metadata={m.name:{k:value(v) for k,v in m.items() if k not in ['tm_asset_preview_style','tm_thumbnail_style_revision','tm_thumbnail_geometry_note']} for m in bpy.data.materials if m.asset_data}
groups={g.name:graph(g) for g in bpy.data.node_groups}
bpy.ops.wm.open_mainfile(filepath=str(stage/'Trackmania2020_assets.blend'),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data};assert set(assets)==set(baseline)
for key,x in assets.items():
 assert graph(x)==baseline[key]['graph'],key
 assert x.get('tm_asset_effect_badges','')==baseline[key]['badges'],key
 old=baseline[key]['identity'].copy();now=identity(x)
 if x.name in targets:old.pop('icon');now.pop('icon')
 assert old==now,key
 if x.name in badges:
  mask,original=badges[x.name];assert np.array_equal(pixels(x)[mask],original[mask]),key
  assert {k:value(v) for k,v in x.items() if k not in ['tm_asset_preview_style','tm_thumbnail_style_revision','tm_thumbnail_geometry_note']}==metadata[x.name],key
  if x.name in targets:assert x['tm_thumbnail_style_revision']==report['revision']
for name,old in groups.items():assert graph(bpy.data.node_groups[name])==old,name
counts=[sum(bool(x.asset_data) for x in c) for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]];assert counts==[1119,20,42]
ids=[x.get('tm_asset_id') for x in assets.values() if x.get('tm_asset_id')];assert len(set(ids))==len(ids)
missing=[]
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve()
  if not path.is_file():missing.append(str(path))
  assert path.is_relative_to(root),('Unexpected helper dependency',path)
assert not missing,missing
assert not any(s.name=='Approved thumbnail studio' for s in bpy.data.scenes)
for row in report['changes']:
 m=bpy.data.materials[row['name']]
 actual=pixels(m);expected=read_saved_preview(stage/'previews'/(row['id']+'.png'));mask=badge_mask(m)
 # Badge bytes are checked exactly against the original library above.
 assert np.array_equal(actual[~mask],expected[~mask]),('Saved thumbnail mismatch',m.name)
 if row['style']=='B':assert 'source-sprite' in m['tm_thumbnail_geometry_note']
proof=dict(revision=report['revision'],staged_sha256=report['staged_sha256'],materials=1119,worlds=20,groups=42,missing_images=0,graphs_preserved=len(assets),all_node_groups_preserved=len(groups),badges_preserved=True,source_metadata_preserved=True,icons_updated=len(targets),counts=report['counts'],preserved=len(report['preserved']))
a.output.write_text(json.dumps(proof,indent=2));print('THUMBNAIL_STYLES_VERIFIED',json.dumps(proof),flush=True)
