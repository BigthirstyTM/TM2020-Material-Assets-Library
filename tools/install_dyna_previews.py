"""Install only a freshly verified Dyna stage, with guarded replacement/backup."""
import argparse,datetime,json,os,shutil,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_dyna_previews import blocks,verify
from apply_shader_fidelity import sha
from dyna_preview_adapters import REVISION

def norm(x):
    if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
    if hasattr(x,'items'):return {k:norm(v) for k,v in x.items()}
    if isinstance(x,(str,int,float,bool)) or x is None:return x
    try:return [norm(v) for v in x]
    except TypeError:return str(x)

p=argparse.ArgumentParser()
for k in ['library','stage','state','documentation']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();stage=a.stage.resolve();out=a.state.resolve()
source=root/'Trackmania2020_assets.blend';staged=stage/source.name
report=json.loads((stage/'build-report.json').read_text())
proof=json.loads((out/'verification.json').read_text());render=json.loads((out/'render-tests/render-verification.json').read_text())
assert report['revision']==proof['revision']==REVISION
assert proof['sha256']==render['source_sha256']==report['staged_sha256']==sha(staged)
assert sha(source)==report['source_sha256'],'Installed master changed; do not overwrite'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
original={k:{prop:norm(value) for prop,value in v.items()} for k,v in blocks().items()}
unchanged={n:sha(root/n) for n in ['MaterialLib.txt','blender_assets.cats.txt']}
bpy.ops.wm.open_mainfile(filepath=str(staged),load_ui=False)
for k,v in blocks().items():
    now={prop:norm(value) for prop,value in v.items()}
    for prop,value in original[k].items():assert now[prop]==value,('Existing metadata changed',k,prop)
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath and not im.packed_file:
        path=Path(bpy.path.abspath(im.filepath)).resolve()
        assert path.is_file() and path.is_relative_to(root),path
        im.filepath='//'+path.relative_to(root).as_posix()
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=out/'backup'/stamp;backup.mkdir(parents=True)
shutil.copy2(source,backup/source.name)
pending=root/'Trackmania2020_dyna.pending.blend'
assert not pending.exists(),'Inspect existing pending file before retry'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(pending),compress=True,relative_remap=False)
verify(stage,pending,out/'portable-verification.json')
assert sha(source)==report['source_sha256'],'Installed master changed during preparation'
os.replace(pending,source)
try:verify(stage,source,out/'installed-verification.json')
except Exception:
    shutil.copy2(source,out/'failed-installed.blend');shutil.copy2(backup/source.name,source)
    raise
for n,digest in unchanged.items():assert sha(root/n)==digest
doc=root/'Documentation/DYNA-MATERIALS.md'
if doc.exists():shutil.copy2(doc,backup/doc.name)
shutil.copy2(a.documentation,doc)
receipt=dict(revision=REVISION,installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],
  backup=str(backup),graph_targets=report['graph_targets'],metadata_targets=report['targets'],
  unchanged_files=unchanged,documentation=str(doc),existing_metadata_preserved=True,
  public_packages_updated=False,remote_pilot_updated=False,game_started=False)
(out/'installation.json').write_text(json.dumps(receipt,indent=2))
print('DYNA_INSTALLED',receipt,flush=True)
