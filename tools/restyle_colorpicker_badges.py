"""Restyle existing colorpicker badges, restoring their pristine background first."""
import argparse, json, os, shutil, sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity, graph, sha
from apply_concrete_shaders import pixels, png

p=argparse.ArgumentParser()
for k in ['installation','audit','badge','output']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--install',action='store_true')
p.add_argument('--pristine',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
old=json.loads(a.installation.read_text());source=Path(old['installed']);root=source.parent
assert sha(source)==old['sha256'];audit=json.loads(a.audit.read_text());rows=audit['materials'];targets={r['name']:r for r in rows}
assert len(targets)==86 and all(not r['preview_only'] for r in rows)
audit['revision']='2026.11.27-colorpicker-red-brush-1'
assert sha(a.pristine)=='d6404cfc336092c6a24fc3e45b1e38b39f904bd0bd87e8d8d9a0dbb25e8e6cfa'
bpy.ops.wm.open_mainfile(filepath=str(a.pristine.resolve()),load_ui=False)
clean_icons={n:pixels(bpy.data.materials[n]).copy() for n in targets}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
def assets():return {x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
def val(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name]
    if hasattr(v,'items'):return {k:val(x) for k,x in v.items()}
    return [val(x) for x in v]
baseline={k:dict(identity=identity(x),graph=graph(x),props={n:val(v) for n,v in x.items()}) for k,x in assets().items()}
groups={g.name:graph(g) for g in bpy.data.node_groups};support={n:sha(root/n) for n in ['MaterialLib.txt','blender_assets.cats.txt']}
image=bpy.data.images.load(str(a.badge.resolve()),check_existing=False);image.colorspace_settings.name='Non-Color'
badge=np.array(image.pixels[:],dtype=np.float32).reshape(32,32,4)[::-1];bpy.data.images.remove(image)
original={n:pixels(bpy.data.materials[n]) for n in targets};expected={};changes=[]
for name,r in targets.items():
    m=bpy.data.materials[name];assert m['tm_asset_id']==r['id'];badges=json.loads(m.get('tm_asset_effect_badges','[]'))
    assert badges.count('color_picker')==1
    left=218-36*badges.index('color_picker');rgba=original[name].copy();box=rgba[6:38,left:left+32];box[:]=clean_icons[name][6:38,left:left+32];alpha=badge[:,:,3:4]
    box[:,:,:3]=np.rint(badge[:,:,:3]*255*alpha+box[:,:,:3]*(1-alpha)).astype(np.uint8)
    box[:,:,3]=np.rint(badge[:,:,3]*255+box[:,:,3]*(1-badge[:,:,3])).astype(np.uint8)
    m.preview_ensure().image_pixels=np.ascontiguousarray(rgba[::-1]).view(np.int32).ravel().tolist()
    m['tm_colorpicker_badge_revision']=audit['revision']
    expected[name]=identity(m);changes.append(dict(name=name,id=r['id'],badge_position=[left,6,32,32],previous_badges=badges,icon_sha256=expected[name]['icon']))
    path=out/'previews'/(r['id']+'.png');path.parent.mkdir(exist_ok=True);png(path,rgba)
staged=out/source.name;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(staged),compress=True,relative_remap=False)
positions={r['name']:r['badge_position'][0] for r in changes}
def verify(path):
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);blocks=assets();assert set(blocks)==set(baseline)
    for key,x in blocks.items():
        before=baseline[key];assert graph(x)==before['graph'],key
        now=identity(x)
        if x.name in targets:
            assert now==expected[x.name],key
            old=before['identity'].copy();old['icon']=now['icon'];assert now==old
            badges=json.loads(x['tm_asset_effect_badges']);assert badges==json.loads(before['props']['tm_asset_effect_badges'])
            mask=np.zeros((256,256),dtype=bool);left=positions[x.name];mask[6:38,left:left+32]=True
            assert np.array_equal(pixels(x)[~mask],original[x.name][~mask]),('Unrelated preview pixels changed',x.name)
            for n,v in before['props'].items():
                if n=='tm_colorpicker_badge_revision':
                    assert x[n]==audit['revision'];continue
                assert val(x[n])==v,(key,n)
        else:
            assert now==before['identity'] and {n:val(v) for n,v in x.items()}==before['props'],key
    assert {g.name:graph(g) for g in bpy.data.node_groups}==groups
    assert all(sha(root/n)==digest for n,digest in support.items())
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath and not im.packed_file:
            assert (root/im.filepath[2:]).is_file() if im.filepath.startswith('//') else Path(im.filepath).is_file(),im.filepath
    return dict(assets_checked=len(blocks),badges_restyled=86,all_graphs_unchanged=True,existing_badge_pixels_preserved=True,
                outside_new_badge_pixels_unchanged=True,native_ids_export_catalogs_preserved=True,all_node_groups_unchanged=True,missing_images=0)
proof=verify(staged);(out/'baseline.json').write_text(json.dumps(baseline));(out/'verification.json').write_text(json.dumps(proof,indent=2))
report=dict(revision=audit['revision'],source_sha256=old['sha256'],staged_sha256=sha(staged),changes=changes,counts=dict(materials_only=873,complete=1172,preview_only=299,worlds=20))
(out/'build-report.json').write_text(json.dumps(report,indent=2))
if a.install:
    backup=out/'backup';backup.mkdir();shutil.copy2(source,backup/source.name);assert sha(source)==old['sha256']
    pending=source.with_name(source.name+'.colorpicker-pending');shutil.copy2(staged,pending)
    try:os.replace(pending,source);proof=verify(source)
    except BaseException:shutil.copy2(backup/source.name,source);raise
    receipt=dict(revision=audit['revision'],installed=str(source),sha256=sha(source),previous_sha256=old['sha256'],backup=str(backup),
        materials_only=873,complete=1172,preview_only=299,worlds=20,badges_restyled=86,remote_changed=False,offline_packages_changed=False,verification=proof)
    (out/'installation.json').write_text(json.dumps(receipt,indent=2))
print('RED_BRUSH_BADGES_VERIFIED',86,flush=True)
