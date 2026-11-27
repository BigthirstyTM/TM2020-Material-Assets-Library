"""Promote runtime-loaded vista assets while preserving preceding asset contracts."""
import bpy,addon_utils,argparse,json,sys,datetime,shutil,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from vista_array_mapping import descriptor_transform
from vista_thumbnails import render_previews
import deco_ice_adapters
from projection_refresh_adapters import projected
REVISION='2026.11.27-vista-native-1'
p=argparse.ArgumentParser()
for k in ['library','inputs','prior-report','runtime','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
source=root/'Trackmania2020_assets.blend';source_sha=sha(source)
assert source_sha=='41b3d9905064a38ee7a9e0858532ff262fc28ed746b089cc1464e559b84f6c6d'
runtime=a.runtime.read_text();assert 'vista-audit-20261127-2 COMPLETE' in runtime
for i in range(53):assert f'SOURCE {i} fid=true material=true' in runtime and f'ITEM {i} model=true' in runtime
addon_utils.enable('blendermania-addon',default_set=False)
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
recipes=json.loads(a.inputs.read_text());prior=json.loads(a.prior_report.read_text());names={r['name'] for r in recipes['materials']}
assets={x.bl_rna.identifier+':'+x.name:x for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in coll if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),id=x.get('tm_asset_id'),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
(out/'baseline.json').write_text(json.dumps(baseline))
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
catalogs=(root/'blender_assets.cats.txt').read_text(encoding='utf-8');cat_rows=[line.split(':',2) for line in catalogs.splitlines() if line.count(':')==2 and not line.startswith('#')]
cat_by_path={r[1]:r[0] for r in cat_rows};changes=[];mapping=[]
deco_ice_adapters.projected=projected
for r in recipes['materials']:
 m=bpy.data.materials[r['name']];assert m.asset_data and m['tm_preview_only'];assert m['tm_vista_candidate_alias']==r['alias']
 changed=False
 for key,desc in r['slots'].items():
  f=desc.get('array_fields')
  if not f:continue
  transform=descriptor_transform(f,side=key.startswith('Pxz'))
  if any(desc.get(k)!=v for k,v in transform.items()):changed=True
  desc.update(transform)
 if changed:
  def load(key):
   desc=r['slots'].get(key,{})
   if not desc.get('path'):return None
   path=Path(desc['path']).resolve()
   im=next((im for im in bpy.data.images if im.source=='FILE' and im.filepath and Path(im.filepath).resolve()==path and (im.colorspace_settings.name=='sRGB')==(desc.get('usage')=='Color')),None)
   assert im,key
   return im
  old=m.node_tree.nodes['Deco native layer controls'];group=old.node_tree;m.node_tree.nodes.remove(old)
  deco_ice_adapters.terrain(bpy,m,r,load)
  m.node_tree.nodes['Deco native layer controls'].inputs['Use painted vertex alpha'].default_value=float(r['options'].get('VertexAlpha')==1)
  if group.users==0:bpy.data.node_groups.remove(group)
  m['tm_vista_slots']=json.dumps(r['slots']);mapping.append(m.name)
  changes.append(dict(next(x for x in prior['changes'] if x['name']==m.name)))
 limitations=[x for x in json.loads(m['tm_preview_limitations']) if 'array matrix fields' not in x and not x.startswith('Untested in Trackmania')]
 limitations.insert(0,'Native source and linked test item loaded in Trackmania; user visually confirmed the 53-material fixture. Blender lighting and projection remain preview adapters.')
 m['tm_preview_limitations']=json.dumps(limitations);m['tm_preview_only']=False;m['tm_game_material_exportable']=True
 m['tm_vista_runtime_status']='Loaded native source and linked item; user visually confirmed fixture'
 m['tm_current_export_status']='Native link enabled after vista fixture game check';m['tm_vista_candidate_revision']=REVISION
 m.link=r['alias'];m['MAT_PROPS_AS_JSON']=json.dumps(dict(name=m.name,link=r['alias']))
 path='Trackmania2020/04 Environments/'+r['environment']
 # Use the existing native environment catalog, preserving its established UUID.
 matches=[(k,v) for k,v in cat_by_path.items() if k.endswith('/'+r['environment']) and 'Preview only' not in k]
 assert len(matches)==1,(r['environment'],matches)
 path,cid=matches[0];m.asset_data.catalog_id=cid
 m.asset_data.description=('Native-linked vista material. Tested source + embedded item; visually confirmed by user. Source: '+r['source']+'. '+' '.join(limitations))[:1023]
 for tag in list(m.asset_data.tags):
  if tag.name in ['Preview only','Vista candidate','Not tested in game']:m.asset_data.tags.remove(tag)
 m.asset_data.tags.new('Game checked: vista fixture')
 r.update(catalog=path,preview_limitations=limitations)
assert len(mapping)==6,mapping
render_previews(out,changes,dict(revision=REVISION))
# No old asset graphs, export flags, badges or icons can change outside the named candidates.
for key,x in assets.items():
 before=baseline[key];assert x.get('tm_asset_id')==before['id'];assert x.get('tm_asset_effect_badges','')==before['badges']
 if x.name not in names:assert identity(x)==before['identity'] and graph(x)==before['graph'],key
 elif x.name not in mapping:assert graph(x)==before['graph'] and identity(x)['icon']==before['identity']['icon'],key
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path;im.filepath='//'+path.relative_to(root).as_posix()
# Retire only the four empty candidate catalogs; no existing catalog UUID changes.
catalogs='\n'.join(line for line in catalogs.splitlines() if not any(':Trackmania2020/08 Preview only/Vista candidates/'+env+':' in line for env in ['BlueBay','GreenCoast','RedIsland','WhiteShore']))+'\n'
(out/'blender_assets.cats.txt').write_text(catalogs,encoding='utf-8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report=dict(revision=REVISION,source_sha256=source_sha,staged_sha256=sha(out/source.name),materials=1172,materials_only=873,preview_only=299,worlds=20,promoted=recipes['materials'],projection_fixed=mapping,changes=changes,materiallib_sha256=sha(root/'MaterialLib.txt'),game_evidence='53 FID preloads + 53 embedded linked item models; user visually confirmed all worked. No driving/physics verdict.',user_confirmation=True)
(out/'build-report.json').write_text(json.dumps(report,indent=2))
print('VISTA_NATIVE_STAGED',len(names),mapping,flush=True)
