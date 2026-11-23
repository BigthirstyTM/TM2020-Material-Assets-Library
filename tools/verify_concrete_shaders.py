"""Fresh-file preservation and render checks for the concrete shader refresh."""
import argparse,json,sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,badge_mask
from concrete_shader_adapters import REVISION
from material_preview_adapters import wire

p=argparse.ArgumentParser()
for key in ['source','original','inputs','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);stage=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=json.loads((stage/'build-report.json').read_text());baseline=json.loads((stage/'baseline.json').read_text());inputs=json.loads(a.inputs.read_text())
assert sha(a.original)==report['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(a.original.resolve()),load_ui=False)
badges={n:pixels(bpy.data.materials[n])[badge_mask(bpy.data.materials[n])].copy() for n in report['targets']}
native_identity={m.name:{k:str(v) for k,v in m.items() if k.startswith(('tm_game_','tm_export_','tm_asset_id','tm_audit_native_link','tm_native_resource'))} for m in bpy.data.materials if m.asset_data}
needed=set();visited=set()
def dependencies(tree):
    if not tree or tree in visited:return
    visited.add(tree)
    for n in tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:needed.add(n.image.name)
        if n.type=='GROUP':dependencies(n.node_tree)
for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
    for asset in coll:
        if asset.asset_data and asset.name not in report['targets']:dependencies(asset.node_tree if hasattr(asset,'node_tree') else asset)
image_settings={im.name:(im.colorspace_settings.name,im.alpha_mode) for im in bpy.data.images if im.source=='FILE' and im.name in needed}
bpy.ops.wm.open_mainfile(filepath=str(stage/'Trackmania2020_assets.blend'),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
assert set(assets)==set(baseline)
assert all({k:str(v) for k,v in bpy.data.materials[name].items() if k.startswith(('tm_game_','tm_export_','tm_asset_id','tm_audit_native_link','tm_native_resource'))}==before for name,before in native_identity.items()),'Native binding/asset identity changed'
for k,x in assets.items():
    current=identity(x);old=baseline[k]['identity'].copy()
    if x.name in report['targets']:current.pop('icon');old.pop('icon')
    assert current==old,('Metadata/export mismatch',k)
    assert x.get('tm_asset_effect_badges','')==baseline[k]['badges']
    if x.name not in report['targets']:assert graph(x)==baseline[k]['graph'],('Unrelated graph changed',k)
for name,old in badges.items():assert np.array_equal(pixels(bpy.data.materials[name])[badge_mask(bpy.data.materials[name])],old),('Badge pixels',name)
assert all((bpy.data.images[name].colorspace_settings.name,bpy.data.images[name].alpha_mode)==value for name,value in image_settings.items()),'Existing image settings changed'
images=[]
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath;images.append(im.filepath)
structural=[]
for r in inputs['materials']:
    m=bpy.data.materials[r['name']];t=m.node_tree;flags=set(r['findings']);assert m['tm_concrete_shader_revision']==REVISION
    p=t.nodes['Principled BSDF']
    if 'F01' in flags:assert not p.inputs['Specular IOR Level'].is_linked and p.inputs['Specular IOR Level'].default_value==.5
    if flags.intersection({'F02','F05','F06','F07','F08','F10'}):
        group=p.inputs['Base Color'].links[0].from_node;assert group.type=='GROUP';g=group.node_tree
        for role in ['PyBaseColor','PxzBaseColor','PyRoughMetal','PxzRoughMetal','PyNormal','PxzNormal']:
            expected=r['slots'].get(role,{}).get('image')
            if expected:assert any(n.type=='TEX_IMAGE' and n.image and Path(n.image.filepath.replace('\\','/')).name.lower()==Path(expected.replace('\\','/')).name.lower() for n in g.nodes),(m.name,role)
        if 'F06' in flags:assert tuple(group.inputs['Hue target (native default)'].default_value[:3])==tuple(np.float32(r['native_parameters']['TargetColor']['values'][0][:3]))
        if 'TBaseColor' in r['slots']:
            assert group.inputs['Fallback alpha'].default_value==1 and group.inputs['Use painted vertex alpha'].default_value==0
            assert group.inputs['BaseMaterial UV'].links[0].from_node.uv_map=='BaseMaterial'
    if flags.intersection({'F03','F04'}):
        group=t.nodes['Ice native surface and internal layers'];g=group.node_tree
        assert not any(n.type in ['ATTRIBUTE','VERTEX_COLOR'] for n in g.nodes)
        sample=g.nodes['Native TAlpha'];sep=next(l.to_node for l in sample.outputs[0].links if l.to_node.type=='SEPXYZ')
        assert sep.outputs[0].is_linked and not sep.outputs[1].is_linked
        depth=t.nodes['Native sampled internal depth in meters'];assert t.nodes['Ice Internal Layer Preview'].inputs['Depth (meters)'].links[0].from_node==depth
        assert t.nodes['Native internal ice depth'].image
    if 'F11' in flags:
        assert any(n.type=='TEX_IMAGE' and n.image and Path(n.image.filepath).name.lower()=='lightcells_n.dds' for n in t.nodes)
        assert not any(n.type=='TEX_IMAGE' and n.image and 'lightcells3_n' in n.image.filepath.lower() for n in t.nodes)
    if 'F12' in flags:
        g=t.nodes['Native GrassFence layers'].node_tree
        assert all(g.nodes[n].image for n in ['Native Diffuse','Native GrassX2','Native FenceA'])
        assert not m.use_backface_culling and m.surface_render_method=='BLENDED'
    structural.append(dict(name=m.name,findings=r['findings'],passed=True))

# Render UV invariance and alpha contract through actual corrected layer groups.
scene=bpy.data.scenes.new('Concrete layer verification');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=scene.render.resolution_y=32;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='OPEN_EXR'
bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object;ob.data.uv_layers[0].name='BaseMaterial'
bpy.ops.object.camera_add(location=(0,0,5));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2
def capture(label):
    path=out/(label+'.exr');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);im=bpy.data.images.load(str(path),check_existing=False)
    result=np.asarray(im.pixels[:]).reshape(32,32,4)[:,:,:3].copy();bpy.data.images.remove(im);return result
tests=[]
for name in ['TM_RoadDirt_asset','TM_RedIsland_DetailsToDirt_asset']:
    original=bpy.data.materials[name];m=original.copy();m.asset_clear();t=m.node_tree;group=t.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node;group.node_tree=group.node_tree.copy();g=group.node_tree
    # Isolate the authored UV overlay colour to detect accidental world tiling.
    output=next(n for n in g.nodes if n.type=='GROUP_OUTPUT')
    wire(g,g.nodes['Native TBaseColor - mesh UV only'].outputs[0],output.inputs['Base Color'])
    em=t.nodes.new('ShaderNodeEmission');wire(t,group.outputs['Base Color'],em.inputs['Color']);wire(t,em.outputs[0],next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output).inputs['Surface'])
    ob.data.materials.clear();ob.data.materials.append(m);ob.location=(0,0,0);ob.scale=(1,1,1);scene.camera.location=(0,0,5);scene.camera.data.ortho_scale=2
    first=capture(name+'-uv-small');ob.location=(300,50,0);ob.scale=(4,4,4);scene.camera.location=(300,50,5);scene.camera.data.ortho_scale=8
    second=capture(name+'-uv-translated-large');difference=float(np.max(abs(first-second)));assert difference<.003,(name,difference)
    wire(t,group.outputs['Layer weight'],em.inputs['Color']);group.inputs['Use painted vertex alpha'].default_value=0;full=capture(name+'-fallback')
    colour=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
    for v in colour.data:v.color=(1,0,0,.5)
    group.inputs['Use painted vertex alpha'].default_value=1;half=capture(name+'-alpha-half');assert np.max(abs(half-.5*full))<.003
    for v in colour.data:v.color=(0,1,1,0)
    zero=capture(name+'-alpha-zero');assert np.max(abs(zero))<.002
    tests.append(dict(name=name,uv_world_scale_invariance=difference,alpha_half_zero_and_rgb_independence=True))

counts=dict(materials=sum(bool(m.asset_data) for m in bpy.data.materials),worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),source_groups=sum(bool(g.asset_data) for g in bpy.data.node_groups))
assert counts==dict(materials=1119,worlds=20,source_groups=42),counts
proof=dict(revision=REVISION,staged_sha256=sha(stage/'Trackmania2020_assets.blend'),**counts,missing_images=0,structural_checks=structural,render_tests=tests,existing_badges_preserved=True,export_metadata_preserved=True,unrelated_graphs_preserved=True,existing_image_settings_preserved=True,game_started=False)
(out/'verification.json').write_text(json.dumps(proof,indent=2));print('CONCRETE_SHADERS_VERIFIED',flush=True);bpy.ops.wm.quit_blender()
