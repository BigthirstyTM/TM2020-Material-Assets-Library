"""Refresh embedded materials in release example copies, preserving their meshes."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_concrete_shaders import pixels,png

p=argparse.ArgumentParser();p.add_argument('--staging',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--previews',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);stage=a.staging.resolve();source=a.source.resolve();previews=a.previews.resolve();previews.mkdir(exist_ok=True,parents=True)
proof={}
for edition in ['materials-only','complete']:
    root=stage/edition;library=root/'Trackmania2020_assets.blend'
    bpy.ops.wm.open_mainfile(filepath=str(library),load_ui=False)
    names={m['tm_asset_id']:m.name for m in bpy.data.materials if m.asset_data}
    for m in bpy.data.materials:
        if m.asset_data:png(previews/(m['tm_asset_id']+'.png'),pixels(m))
    # Keep the offline catalogue synchronized with the actual saved previews.
    import shutil
    for row in json.loads((root/'materials.json').read_text()):shutil.copy2(previews/(row['id']+'.png'),root/'Catalogue/previews'/(row['id']+'.png'))
    checks=[]
    for path in sorted((root/'Examples').glob('*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
        old_materials=[m for m in bpy.data.materials if m.get('tm_asset_id') in names]
        wanted=[names[m['tm_asset_id']] for m in old_materials]
        with bpy.data.libraries.load(str(library),link=False) as (src,dst):dst.materials=wanted
        new_materials=dst.materials
        for old,new in zip(old_materials,new_materials):
            assert new and new['tm_asset_id']==old['tm_asset_id'];old.user_remap(new);bpy.data.materials.remove(old)
            new.name=names[new['tm_asset_id']]
            control=new.node_tree.nodes.get('Deco native layer controls')
            if control and any(ob.type=='MESH' and any(slot.material==new for slot in ob.material_slots) and ob.data.color_attributes.get('Color') for ob in bpy.data.objects):control.inputs['Use painted vertex alpha'].default_value=1
        bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
        image_paths=[]
        for im in bpy.data.images:
            if im.source!='FILE' or not im.filepath or im.packed_file:continue
            resolved=Path(bpy.path.abspath(im.filepath)).resolve()
            assert resolved.is_file(),resolved
            if resolved.is_relative_to(root):relative=resolved.relative_to(root)
            else:
                relative=resolved.relative_to(source)
                candidate=root/relative;assert candidate.is_file(),candidate
                with candidate.open('rb') as f:one=hashlib.file_digest(f,'sha256').hexdigest()
                with resolved.open('rb') as f:two=hashlib.file_digest(f,'sha256').hexdigest()
                assert one==two,(resolved,candidate)
            im.filepath='//../'+relative.as_posix();image_paths.append(relative.as_posix())
        bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True,relative_remap=False)
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
        for im in bpy.data.images:
            if im.source=='FILE' and im.filepath and not im.packed_file:
                resolved=Path(bpy.path.abspath(im.filepath)).resolve();assert resolved.is_relative_to(root) and resolved.is_file(),resolved
        checks.append(dict(example=path.name,replaced_materials=len(new_materials),images=len(image_paths),portable=True))
        print('EXAMPLE_REFRESHED',edition,path.name,flush=True)
    proof[edition]=checks
(stage/'refreshed-examples.json').write_text(json.dumps(proof,indent=2));print('RELEASE_EXAMPLES_REFRESHED',flush=True)
