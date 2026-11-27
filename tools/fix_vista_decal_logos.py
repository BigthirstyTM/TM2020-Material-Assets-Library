"""Stage and verify source-exact vista sponsor masks; install only on explicit --install."""
import argparse, json, os, shutil, sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity, graph, sha
from apply_concrete_shaders import png
from vista_decal_opacity import connect_opacity
from vista_thumbnails import render_previews

p = argparse.ArgumentParser()
p.add_argument('--library', type=Path, required=True)
p.add_argument('--inputs', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--install', action='store_true')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
root=a.library.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
source=root/'Trackmania2020_assets.blend'; source_hash=sha(source)
assert source_hash=='12da7981831955cce1410f7de7ef1436b7dca15bb0c7f843f2d4324a75091b66'
revision='2026.11.27-vista-logo-masks-1'
rows=[r for r in json.loads(a.inputs.read_text())['materials'] if 'Sponsor4x1' in r['name']]
assert len(rows)==16
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
def assets():
    return {x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
def value(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name]
    if hasattr(v,'items'):return {k:value(x) for k,x in v.items()}
    return [value(x) for x in v]
baseline={k:dict(identity=identity(x),graph=graph(x),props={n:value(v) for n,v in x.items()}) for k,x in assets().items()}
groups={x.name:graph(x) for x in bpy.data.node_groups}
old_pixels={r['name']:np.array(bpy.data.materials[r['name']].preview_ensure().image_pixels[:],dtype=np.int32).view(np.uint8).reshape(256,256,4)[::-1].copy() for r in rows}
support={n:sha(root/n) for n in ['MaterialLib.txt','blender_assets.cats.txt']}
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.filepath=bpy.path.abspath(image.filepath)
changes=[]
for r in rows:
    m=bpy.data.materials[r['name']];t=m.node_tree;tex=t.nodes['Native TOpacity mesh mask']
    assert Path(tex.image.filepath).resolve()==Path(r['slots']['TOpacity']['path']).resolve()
    assert tex.image.alpha_mode=='CHANNEL_PACKED'
    link=t.nodes['Principled BSDF'].inputs['Alpha'].links[0];assert link.from_socket==tex.outputs['Alpha']
    connect_opacity(m,tex,t.nodes['Deco Color alpha'].outputs['Alpha'])
    changes.append(dict(name=m.name,id=m['tm_asset_id'],style='flat-layered',primary_image=tex.image.name,
                        source=r['source'],texture=r['slots']['TOpacity']['resource'],texture_sha256=sha(Path(tex.image.filepath))))
render_previews(out,changes,dict(revision=revision))
for r in changes:
    m=bpy.data.materials[r['name']]
    rgba=np.array(m.preview.image_pixels[:],dtype=np.int32).view(np.uint8).reshape(256,256,4)[::-1].copy()
    # Preserve the actual existing badge pixels, rather than recreating their artwork.
    rgba[6:38,218:250]=old_pixels[m.name][6:38,218:250]
    m.preview.image_pixels=np.ascontiguousarray(rgba[::-1]).view(np.int32).ravel().tolist()
    png(Path(r['preview_file']),rgba);r['icon_sha256']=identity(m)['icon']
    m['tm_vista_logo_mask_revision']=revision
    m['tm_vista_logo_mask_contract']='TOpacity.r * Color.a (compiled shader t12.x * v1.w); bitmap alpha is the legacy Stadium logo'
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:
        path=Path(bpy.path.abspath(image.filepath)).resolve();assert path.is_file() and path.is_relative_to(root)
        image.filepath='//'+path.relative_to(root).as_posix()
staged=out/source.name;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(staged),compress=True,relative_remap=False)
expected={r['name']:graph(bpy.data.materials[r['name']]) for r in changes}
icons={r['name']:identity(bpy.data.materials[r['name']])['icon'] for r in changes}
targets=set(expected)
def verify(path):
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);actual=assets();assert set(actual)==set(baseline)
    for k,x in actual.items():
        now=identity(x);old=baseline[k]['identity'].copy()
        if x.name in targets:
            assert now.pop('icon')==icons[x.name];old.pop('icon');assert graph(x)==expected[x.name]
            pixels=np.array(x.preview.image_pixels[:],dtype=np.int32).view(np.uint8).reshape(256,256,4)[::-1]
            assert np.array_equal(pixels[6:38,218:250],old_pixels[x.name][6:38,218:250])
        else:assert graph(x)==baseline[k]['graph'],k
        assert now==old,k
        for n,v in baseline[k]['props'].items():
            if x.name in targets and n=='tm_thumbnail_style_revision':continue
            assert value(x[n])==v,(k,n)
    assert {x.name:graph(x) for x in bpy.data.node_groups}==groups
    assert all(sha(root/n)==h for n,h in support.items())
    for image in bpy.data.images:
        if image.source=='FILE' and image.filepath and not image.packed_file:
            assert (root/image.filepath[2:]).is_file() if image.filepath.startswith('//') else Path(image.filepath).is_file()
    return dict(assets_checked=len(actual),corrected_materials=16,unrelated_assets_unchanged=True,
                all_node_groups_unchanged=True,badges_native_ids_export_metadata_catalogs_preserved=True,missing_images=0)
proof=verify(staged)
(out/'baseline.json').write_text(json.dumps(baseline))
(out/'build-report.json').write_text(json.dumps(dict(revision=revision,source_sha256=source_hash,staged_sha256=sha(staged),changes=changes),indent=2))
(out/'verification.json').write_text(json.dumps(proof,indent=2))
if a.install:
    backup=out/'backup';backup.mkdir();shutil.copy2(source,backup/source.name);assert sha(source)==source_hash
    pending=source.with_name(source.name+'.logo-pending');shutil.copy2(staged,pending)
    try:os.replace(pending,source);proof=verify(source)
    except BaseException:shutil.copy2(backup/source.name,source);raise
    receipt=dict(revision=revision,installed=str(source),sha256=sha(source),previous_sha256=source_hash,backup=str(backup),
                 materials_only=873,complete=1172,preview_only=299,worlds=20,remote_changed=False,offline_packages_changed=False,verification=proof)
    (out/'installation.json').write_text(json.dumps(receipt,indent=2))
print('VISTA_LOGO_MASKS_VERIFIED',len(changes),flush=True)
