"""Verify combined edition contents, native bindings, current graphs and examples."""
import argparse,json,sys
from pathlib import Path
import bpy,addon_utils
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph
from concrete_shader_adapters import REVISION
p=argparse.ArgumentParser()
for key in ['staging','source','inputs']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);stage=a.staging.resolve();source=a.source.resolve();inputs=json.loads(a.inputs.read_text())
inventory=json.loads((Path(__file__).resolve().parents[1]/'data/source-materials.json').read_text())['materials'];expected={r['name']:r for r in inventory}
quarantined={'TM_16x9ScreenOff_asset','TM_Ad16x9Screen_asset','TM_PodiumScreen16x9_asset','TM_WarpScreen16x9B_asset','TM_WarpScreen16x9C_asset'}
assert all(expected[name]['preview_only'] and not expected[name]['effective']['link'] for name in quarantined)
addon_utils.enable('blendermania-addon',default_set=False)
for handler in list(bpy.app.handlers.load_post):
    if handler.__module__.startswith('blendermania-addon'):bpy.app.handlers.load_post.remove(handler)
bpy.ops.wm.open_mainfile(filepath=str(source/'Trackmania2020_assets.blend'),load_ui=False)
original={m.name:dict(identity=identity(m),graph=graph(m)) for m in bpy.data.materials if m.asset_data}
proof={}
for edition,count,groupcount in [('materials-only',sum(not r['preview_only'] for r in inventory),0),('complete',len(inventory),42)]:
    root=stage/edition;bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
    mats=[m for m in bpy.data.materials if m.asset_data];assert len(mats)==count
    assert sum(bool(g.asset_data) for g in bpy.data.node_groups)==groupcount
    materiallib=(root/'MaterialLib.txt').read_bytes()
    assert b'DMaterial(Stadium_ItemFlag)' not in materiallib
    assert b'DMaterial(ItemFlagNoAnim)' in materiallib and b'DMaterial(Stadium_ItemFlagNoAnim)' in materiallib
    for name in quarantined:assert ('DMaterial('+name.removeprefix('TM_').removesuffix('_asset')+')').encode() not in materiallib
    if edition=='materials-only':assert not ({m.name for m in mats}&quarantined)
    else:
        for name in quarantined:
            m=bpy.data.materials[name];assert not m.link and not json.loads(m['MAT_PROPS_AS_JSON'])['link'] and not m['tm_game_material_exportable']
            assert m.get('tm_export_binding_status')=='preview_only_missing_native_material' and 'Preview only' in m.asset_data.description
    changed=0
    for m in mats:
        assert m.link==expected[m.name]['effective']['link'],m.name
        if m.name=='TM_ItemFlag_animated_asset':
            assert m.link==m.get('link')==json.loads(m['MAT_PROPS_AS_JSON'])['link']==m.get('tm_game_material_path')==''
            assert m.get('tm_game_material_exportable') is False and expected[m.name]['preview_only']
        assert 'tm_customization' not in m
        if edition=='materials-only':assert not expected[m.name]['preview_only']
        # Path relocation changes image strings, not saved preview pixels.
        assert identity(m)['icon']==original[m.name]['identity']['icon'],('Saved thumbnail',m.name)
        assert graph(m)==original[m.name]['graph'],('Portable graph differs',m.name)
        if m.name in {r['name'] for r in inputs['materials']}:
            assert m['tm_concrete_shader_revision']==REVISION;changed+=1
            if 'F01' in json.loads(m['tm_concrete_shader_fixes']):assert not m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].is_linked
    assert bpy.data.materials['TM_Water_asset']['tm_shader_fidelity_revision']=='2026.11.23-shader-fidelity-1'
    assert bpy.data.materials['TM_DecoHill_asset']['tm_deco_ice_revision']=='2026.11.23-deco-ice-1'
    scenes=[]
    for path in sorted((root/'Examples').glob('*.blend')):
        bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
        for prop in bpy.data.bl_rna.properties:
            if prop.type=='COLLECTION':assert not any(getattr(x,'asset_data',None) for x in getattr(bpy.data,prop.identifier)),('Duplicate example asset',path)
        for im in bpy.data.images:
            if im.source=='FILE' and im.filepath and not im.packed_file:
                resolved=Path(bpy.path.abspath(im.filepath)).resolve();assert resolved.is_relative_to(root) and resolved.is_file(),resolved
        for m in bpy.data.materials:
            if m.get('tm_asset_id') in {r['id'] for r in inventory}:
                name=next(r['name'] for r in inventory if r['id']==m['tm_asset_id'])
                if name in {r['name'] for r in inputs['materials']}:assert m['tm_concrete_shader_revision']==REVISION
                if name=='TM_Water_asset':assert m['tm_shader_fidelity_revision']=='2026.11.23-shader-fidelity-1'
        scenes.append(path.name)
    proof[edition]=dict(materials=count,source_groups=groupcount,corrected_materials=changed,current_saved_icons=True,native_links_preserved=True,previous_water_and_deco_updates_included=True,portable_current_examples=scenes)
(stage/'combined-edition-verification.json').write_text(json.dumps(proof,indent=2));print('COMBINED_EDITIONS_VERIFIED',json.dumps(proof),flush=True)
