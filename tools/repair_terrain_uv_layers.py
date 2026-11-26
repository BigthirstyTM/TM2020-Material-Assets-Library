"""Bounded restoration, fresh-file verification and guarded local installation."""
import argparse,datetime,json,os,shutil,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_dyna_previews import blocks,snapshot
from apply_shader_fidelity import sha
from apply_concrete_shaders import pixels,badge_mask
from terrain_thumbnail_inset import ancestors
from terrain_uv_layers import restore,REVISION

SOURCE_SHA='8a56547ef99ffd0449d2d2dc6b661641c0d148bd9d405f6b798d5789aab572bd'

def properties(x):
 def norm(v):
  if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name]
  if hasattr(v,'items'):return {k:norm(q) for k,q in v.items()}
  if isinstance(v,(str,int,float,bool)) or v is None:return v
  try:return [norm(q) for q in v]
  except TypeError:return str(v)
 return {k:norm(v) for k,v in x.items()}

def verify(source,state,output,baseline_source=None):
 before=json.loads((state/'baseline.json').read_text());report=json.loads((state/'build-report.json').read_text());targets=set(report['targets'])
 if baseline_source:
  assert sha(baseline_source)==report['source_sha256']
  bpy.ops.wm.open_mainfile(filepath=str(baseline_source),load_ui=False)
  # Socket signatures differ between Blender versions. Compare both saved
  # libraries with the same reader instead of comparing a 5.2 graph to 5.3 RNA.
  before={k:dict(snapshot=snapshot(v),properties=properties(v)) for k,v in blocks().items()}
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);current=blocks();assert set(before)<=set(current)
 for key,old in before.items():
  x=current[key];now=snapshot(x);ident=now['identity'];prior=old['snapshot']['identity']
  if x.name in targets:
   assert {k:v for k,v in ident.items() if k!='icon'}=={k:v for k,v in prior.items() if k!='icon'},key
   saved=np.load(state/'original-previews'/f'{x.name}.npy');mask=badge_mask(x);assert np.array_equal(pixels(x)[mask],saved[mask]),key
  else:assert ident==prior and now['graph']==old['snapshot']['graph'] and now['outputs']==old['snapshot']['outputs'],key
  assert now['badges']==old['snapshot']['badges'],key
  props=properties(x)
  for k,v in old['properties'].items():
   if x.name in targets and k in ['tm_asset_preview_style','tm_thumbnail_style_revision','tm_thumbnail_geometry_note']:continue
   assert props[k]==v,(key,k)
 for name in targets:
  m=bpy.data.materials[name];assert m['tm_terrain_uv_revision']==REVISION
  g=m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node.node_tree
  o=next(n for n in g.nodes if n.type=='GROUP_OUTPUT' and n.is_active_output)
  factor=g.nodes['Source T opacity x vertex alpha']
  input_node=next(n for n in g.nodes if n.type=='GROUP_INPUT')
  for sampler in ['Native TBaseColorOp - mesh UV only','Restored TRoughMetal - mesh UV only','Restored TNormal - mesh UV only']:
   link=g.nodes[sampler].inputs['Vector'].links[0];assert link.from_node==input_node and link.from_socket.name=='BaseMaterial UV',(name,sampler,'Unexpected extra UV transform')
  for channel,texture in [('Base Color','Native TBaseColorOp - mesh UV only'),('Roughness','Restored TRoughMetal - mesh UV only'),('Metallic','Restored TRoughMetal - mesh UV only'),('Normal','Restored TNormal - mesh UV only')]:
   nodes=ancestors(o.inputs[channel].links[0].from_socket)
   assert g.nodes[texture] in nodes and factor in nodes,(name,channel)
  assert all(g.nodes[n].image.alpha_mode=='CHANNEL_PACKED' for n in ['Native TBaseColorOp - mesh UV only','Restored TRoughMetal - mesh UV only','Restored TNormal - mesh UV only'])
 missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and im.filepath and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()];assert not missing,missing
 assert sum(bool(m.asset_data) for m in bpy.data.materials)==1119
 proof=dict(revision=REVISION,sha256=sha(source),blender=bpy.app.version_string,targets=len(targets),asset_count=1119,old_datablocks_preserved=len(before),missing_images=0,unrelated_graphs_icons_metadata_preserved=True,badges_preserved=True)
 output.write_text(json.dumps(proof,indent=2));print('TERRAIN_UV_VERIFIED',proof,flush=True);return proof

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['stage','verify','install'])
 for k in ['library','state','source']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--baseline-source',type=Path,help='Read pinned original with this Blender version for cross-version checks.')
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();state=a.state.resolve();source=a.source.resolve();state.mkdir(parents=True,exist_ok=True)
 if a.mode=='verify':verify(source,state,state/('cross-version-verification.json' if a.baseline_source else 'verification.json'),a.baseline_source.resolve() if a.baseline_source else None);return
 if a.mode=='install':
  report=json.loads((state/'build-report.json').read_text());proof=json.loads((state/'verification.json').read_text());renders=json.loads((state/'render-tests/verification.json').read_text())
  assert sha(source)==proof['sha256'] and renders['source_sha256']==report['staged_sha256'] and renders['materials']==15
  master=root/'Trackmania2020_assets.blend';assert sha(master)==SOURCE_SHA
  verify(source,state,state/'preinstall-verification.json')
  unchanged={n:sha(root/n) for n in ['MaterialLib.txt','blender_assets.cats.txt']}
  for im in bpy.data.images:
   if im.source=='FILE' and im.filepath and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path;im.filepath='//'+path.relative_to(root).as_posix()
  backup=state/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True);shutil.copy2(master,backup/master.name)
  pending=root/'Trackmania2020_terrain_uv.pending.blend';assert not pending.exists()
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(pending),compress=True,relative_remap=False)
  verify(pending,state,state/'portable-verification.json');assert sha(master)==SOURCE_SHA;os.replace(pending,master)
  try:verify(master,state,state/'installed-verification.json')
  except Exception:shutil.copy2(master,state/'failed-installed.blend');shutil.copy2(backup/master.name,master);raise
  assert all(sha(root/n)==v for n,v in unchanged.items())
  docs=Path(__file__).resolve().parents[1]/'docs'
  for name in ['TERRAIN-UV-LAYERS.md','THUMBNAIL-STYLES.md','SHADER-FOLLOWUP.md']:
   destination=root/'Documentation'/name;destination.parent.mkdir(exist_ok=True)
   if destination.exists():shutil.copy2(destination,backup/name)
   shutil.copy2(docs/name,destination)
  receipt=dict(revision=REVISION,installed=str(master),sha256=sha(master),previous_sha256=SOURCE_SHA,backup=str(backup),materials=15,public_packages_updated=False,remote_pilot_updated=False,game_started=False,unchanged_files=unchanged)
  (state/'installation.json').write_text(json.dumps(receipt,indent=2));print('TERRAIN_UV_INSTALLED',receipt,flush=True);return
 assert sha(source)==SOURCE_SHA
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 before={k:dict(snapshot=snapshot(v),properties=properties(v)) for k,v in blocks().items()};(state/'baseline.json').write_text(json.dumps(before))
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
 data=json.loads((Path(__file__).resolve().parents[1]/'data/shader-followup-inputs.json').read_text());rows=[r for r in data['terrain'] if 'TBaseColorOp' in r['slots']];assert len(rows)==15
 preview=state/'original-previews';preview.mkdir(exist_ok=True);loaded={};resolved=[];changes=[]
 for r in rows:
  m=bpy.data.materials[r['name']];np.save(preview/f'{m.name}.npy',pixels(m))
  def load(role):
   desc=r['slots'][role];env=desc['resource'].replace('\\','/').split('/')[0];filename=Path(desc['image'].replace('\\','/')).name;path=root/'Textures'/env/filename;assert path.is_file(),path
   space='sRGB' if role=='TBaseColorOp' else 'Non-Color';key=(str(path),space)
   if key not in loaded:
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=space;im.alpha_mode='CHANNEL_PACKED';loaded[key]=im;resolved.append(dict(path=str(path),sha256=sha(path),colour_space=space))
   return loaded[key]
  changes.append(restore(bpy,m,r,load))
 for key,old in before.items():
  now=snapshot(blocks()[key]);assert now['identity']==old['snapshot']['identity'],key
  if blocks()[key].name not in {r['name'] for r in rows}:assert now==old['snapshot'],key
 (state/'targets.json').write_text(json.dumps([r['name'] for r in rows]))
 assert sha(source)==SOURCE_SHA
 bpy.context.preferences.filepaths.save_version=0;dst=state/'Trackmania2020_assets.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True,relative_remap=False)
 report=dict(revision=REVISION,source_sha256=SOURCE_SHA,staged_sha256=sha(dst),targets=[r['name'] for r in rows],changes=changes,resolved_images=resolved)
 (state/'build-report.json').write_text(json.dumps(report,indent=2));print('TERRAIN_UV_STAGED',len(rows),flush=True)

if __name__=='__main__':main()
