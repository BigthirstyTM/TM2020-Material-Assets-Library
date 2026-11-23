"""Install a verified, portable local update with a recoverable backup."""
import bpy,argparse,datetime,hashlib,json,os,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

parser=argparse.ArgumentParser()
for k in ['library','staged','verification','documentation','output']:parser.add_argument('--'+k,type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
root=args.library.resolve();stage=args.staged.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=json.loads((stage/'build-report.json').read_text());proof=json.loads(args.verification.read_text())
assert proof['revision']==report['revision'] and proof['materials']==1119 and proof['missing_images']==0
assert args.verification.stat().st_mtime >= (stage/'Trackmania2020_assets.blend').stat().st_mtime,'Verification predates this build.'
if 'staged_sha256' in proof:assert proof['staged_sha256']==report['staged_sha256']
source=root/'Trackmania2020_assets.blend'
assert sha(source)==report['source_sha256'],'Installed library changed after staging; do not overwrite it.'
assert sha(stage/source.name)==report['staged_sha256'],'Staged library changed after verification.'
unchanged={name:sha(root/name) for name in ['MaterialLib.txt','blender_assets.cats.txt']}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup=out/'backup'/stamp;backup.mkdir(parents=True)
shutil.copy2(source,backup/source.name)
support=[]
for row in report['support_files']:
    src=stage/row['path'];dst=root/row['path'];assert sha(src)==row['sha256']
    if dst.exists():
        saved=backup/row['path'];saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);support.append(row)
bpy.ops.wm.open_mainfile(filepath=str(stage/source.name),load_ui=False)
staged_icons={name:identity(bpy.data.materials[name])['icon'] for name in report['targets']}
for image in bpy.data.images:
    if image.source!='FILE' or not image.filepath or image.packed_file:continue
    path=Path(bpy.path.abspath(image.filepath)).resolve();assert path.is_file(),path
    if path.is_relative_to(stage):relative=path.relative_to(stage)
    else:relative=path.relative_to(root)
    assert (root/relative).is_file(),relative
    image.filepath='//'+relative.as_posix()
portable=out/'portable';portable.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(portable/source.name),compress=True,relative_remap=False)
docs=[]
for name in ['PROJECTED-SURFACES.md','SOURCE-RESOLUTION.md']:
    src=args.documentation/name;dst=root/'Documentation'/name
    if dst.exists():
        saved=backup/'Documentation'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
    shutil.copy2(src,dst);docs.append(name)
pending=root/'Trackmania2020_projection_refresh.pending.blend';shutil.copy2(portable/source.name,pending)
assert sha(source)==report['source_sha256'],'Installed library changed during preparation.'
os.replace(pending,source)
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
resolved=[]
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:
        path=Path(bpy.path.abspath(image.filepath)).resolve();assert path.is_relative_to(root) and path.is_file(),path;resolved.append(str(path))
assert len([m for m in bpy.data.materials if m.asset_data])==1119
assert all(bpy.data.materials[name].get('tm_projection_refresh_revision')==report['revision'] for name in report['targets'])
assert all(identity(bpy.data.materials[name])['icon']==digest for name,digest in staged_icons.items()),'Installed previews changed'
baseline=json.loads((stage/'baseline.json').read_text())
for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
    for a in coll:
        if not a.asset_data:continue
        key=a.bl_rna.identifier+':'+a.name
        current=identity(a);previous=baseline[key]['identity'].copy()
        if a.name in report['targets']:
            current.pop('icon');previous.pop('icon')
        assert current==previous,('installed identity/export mismatch',key)
        assert a.get('tm_asset_effect_badges','')==baseline[key]['badges']
        if a.name not in report['targets']:assert graph(a)==baseline[key]['graph'],('installed unrelated graph mismatch',key)
assert all(sha(root/name)==value for name,value in unchanged.items())
receipt=dict(revision=report['revision'],installed=str(source),sha256=sha(source),previous_sha256=report['source_sha256'],backup=str(backup),
  changed_materials=report['targets'],support_files=support,documentation=docs,images_resolved=len(resolved),missing_images=0,
  unchanged_files=unchanged,release_packages_changed=False)
(out/'installation.json').write_text(json.dumps(receipt,indent=2))
print('PROJECTION_REFRESH_INSTALLED',receipt['sha256'],flush=True);bpy.ops.wm.quit_blender()
