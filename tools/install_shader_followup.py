"""Install freshly verified shader adapters with a guarded local backup."""
import bpy,argparse,json,datetime,os,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from apply_dyna_previews import blocks
from verify_shader_followup import verify
from shader_followup_adapters import REVISION

def norm(x):
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 if hasattr(x,'items'):return {k:norm(v) for k,v in x.items()}
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [norm(v) for v in x]
 except TypeError:return str(x)

p=argparse.ArgumentParser()
for k in ['library','stage','state','inputs','documentation']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();stage=a.stage.resolve();out=a.state.resolve()
source=root/'Trackmania2020_assets.blend';staged=stage/source.name
report=json.loads((stage/'build-report.json').read_text());proof=json.loads((out/'verification.json').read_text());renders=json.loads((out/'render-tests/verification.json').read_text())
terrain=json.loads((out/'terrain-render-tests/verification.json').read_text())
assert report['revision']==proof['revision']==REVISION
assert sha(staged)==report['staged_sha256']==proof['sha256']==renders['source_sha256']
assert terrain['source_sha256']==proof['sha256'] and terrain['terrain_materials']==24 and len(terrain['results'])==48
assert sha(source)==report['source_sha256'],'Installed source changed; do not overwrite'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
original={k:{prop:norm(value) for prop,value in v.items()} for k,v in blocks().items()}
unchanged={n:sha(root/n) for n in ['MaterialLib.txt','blender_assets.cats.txt']}
bpy.ops.wm.open_mainfile(filepath=str(staged),load_ui=False)
current=blocks()
for k,props in original.items():
 now={prop:norm(value) for prop,value in current[k].items()}
 for prop,value in props.items():assert now[prop]==value,('Existing metadata changed',k,prop)
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:
  path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path
  im.filepath='//'+path.relative_to(root).as_posix()
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
shutil.copy2(source,backup/source.name)
pending=root/'Trackmania2020_shader_followup.pending.blend';assert not pending.exists(),'Inspect existing pending file'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(pending),compress=True,relative_remap=False)
verify(pending,stage,a.inputs.resolve(),out/'portable-verification.json')
assert sha(source)==report['source_sha256']
os.replace(pending,source)
try:verify(source,stage,a.inputs.resolve(),out/'installed-verification.json')
except Exception:
 shutil.copy2(source,out/'failed-installed.blend');shutil.copy2(backup/source.name,source);raise
assert all(sha(root/n)==digest for n,digest in unchanged.items())
doc=root/'Documentation/SHADER-FOLLOWUP.md'
if doc.exists():shutil.copy2(doc,backup/doc.name)
shutil.copy2(a.documentation,doc)
appendix=a.documentation.parent/'SHADER-FOLLOWUP-MATERIALS.md'
if appendix.exists():
 destination=doc.parent/appendix.name
 if destination.exists():shutil.copy2(destination,backup/destination.name)
 shutil.copy2(appendix,destination)
receipt=dict(revision=REVISION,installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],backup=str(backup),
 changed_materials=len(report['targets']),groups={k:len(v) for k,v in report['details'].items()},existing_metadata_preserved=True,
 unchanged_files=unchanged,public_packages_updated=False,remote_pilot_updated=False,game_started=False)
(out/'installation.json').write_text(json.dumps(receipt,indent=2));print('SHADER_FOLLOWUP_INSTALLED',receipt,flush=True)
