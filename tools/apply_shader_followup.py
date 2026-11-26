"""Stage five shader-informed groups without changing publication packages."""
import bpy,argparse,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_dyna_previews import blocks,snapshot
from apply_shader_fidelity import sha
from shader_followup_adapters import REVISION,uv_contract,grass,depth,colour_masks
import deco_ice_adapters
from projection_refresh_adapters import projected

p=argparse.ArgumentParser()
for key in ['source','inputs','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
data=json.loads(a.inputs.read_text(encoding='utf-8'));source=a.source.resolve();root=source.parent
assert sha(source)==data['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
before={k:snapshot(v) for k,v in blocks().items()};(out/'baseline.json').write_text(json.dumps(before,indent=2))
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
files={}
for path in (root/'Textures').rglob('*'):
 if path.is_file():files.setdefault(path.name.lower(),[]).append(path)
loaded={};resolved=[]
def loader(r):
 def load(role):
  desc=r['slots'].get(role,{})
  if not desc.get('image'):return None
  filename=Path(desc['image'].replace('\\','/')).name;env=r['source'].split('/')[0]
  declared=desc.get('resource','').replace('\\','/').split('/')[0]
  exact=root/'Textures'/declared/filename
  direct=root/'Textures'/env/filename
  candidates=[exact] if exact.is_file() else [direct] if direct.is_file() else files.get(filename.lower(),[])
  assert candidates and len({sha(x) for x in candidates})==1,('Ambiguous texture',r['name'],role,filename)
  path=min(candidates,key=lambda p:len(str(p)));space='sRGB' if desc.get('usage')=='Color' and role not in ['PyHx2','PyH2'] else 'Non-Color'
  key=(str(path),space)
  if key not in loaded:
   im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=space;im.alpha_mode='CHANNEL_PACKED';loaded[key]=im
   resolved.append(dict(path=str(path),sha256=sha(path),colour_space=space))
  return loaded[key]
 return load
changes={};details={k:[] for k in ['uv','grass','depth','terrain','hue']}
def mark(m,group,detail):
 changes.setdefault(m.name,[]).append(group);details[group].append(dict(name=m.name,detail=detail))
 m['tm_shader_followup_revision']=REVISION
for name in data['uv']:
 m=bpy.data.materials[name];changed=uv_contract(m)
 if changed:mark(m,'uv',changed)
for r in data['grass']:
 m=bpy.data.materials[r['name']];mark(m,'grass',grass(m,r,loader(r)))
for r in data['depth']:
 m=bpy.data.materials[r['name']];mark(m,'depth',depth(m,r))
deco_ice_adapters.projected=projected
for r in data['terrain']:
 m=bpy.data.materials[r['name']];r['normal_frames']=True
 previous=m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
 controls={s.name:s.default_value for s in previous.inputs if s.name in ['Use painted vertex alpha','Fallback alpha']} if previous.type=='GROUP' else {}
 old_revision=m.get('tm_deco_ice_revision')
 old_roles=m.get('tm_deco_layer_roles')
 result=deco_ice_adapters.terrain(bpy,m,r,loader(r))
 if old_revision is not None:m['tm_deco_ice_revision']=old_revision
 if old_roles is not None:m['tm_deco_layer_roles']=old_roles
 for k,v in controls.items():m.node_tree.nodes[result['group']].inputs[k].default_value=v
 m['tm_array_source_followup']=json.dumps(dict(selectors=r['selectors'],slots=r['slots']))
 m['tm_array_followup_limit']='Static authored array dimensions, signed scales, rotation, offsets, selected images and cosine ranges. Standard bitmap transform convention and mapped Blender normal frames; native runtime buffers/projection not captured.'
 mark(m,'terrain',result)
for r in data['hue']:
 m=bpy.data.materials[r['name']];mark(m,'hue',colour_masks(bpy,m,r,loader(r)))
current=blocks()
for key,old in before.items():
 now=snapshot(current[key]);assert now['identity']==old['identity'],('Identity or preview changed',key)
 assert now['badges']==old['badges'],('Badges changed',key)
 if current[key].name not in changes:assert now['graph']==old['graph'] and now['outputs']==old['outputs'],('Unrelated graph changed',key)
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
# Keep previous private groups as provenance when a material now uses its
# extended copy. Blender otherwise drops zero-user groups while saving.
for key,g in blocks().items():
 if key in before and isinstance(g,bpy.types.NodeTree) and g.users==0:g.use_fake_user=True
assert sha(source)==data['source_sha256']
bpy.context.preferences.filepaths.save_version=0
dst=out/'Trackmania2020_assets.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True,relative_remap=False)
report=dict(revision=REVISION,source_sha256=data['source_sha256'],staged_sha256=sha(dst),targets=sorted(changes),changes=changes,details=details,resolved_images=resolved,support_files=[],game_started=False,public_packages_updated=False)
(out/'build-report.json').write_text(json.dumps(report,indent=2));print('SHADER_FOLLOWUP_STAGED',len(changes),{k:len(v) for k,v in details.items()},flush=True)
