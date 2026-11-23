"""Stage reviewed native input/export corrections without changing the installed source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import uuid

import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from material_preview_adapters import node, wire, math, vec, combine

REVISION = '2026.11.23-native-inputs-1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def graph(material):
    tree = material.node_tree
    return repr(([(n.name, n.bl_idname, [(s.identifier, str(getattr(s, 'default_value', ''))) for s in n.inputs]) for n in tree.nodes],
                 [(l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in tree.links])) if tree else ''


def mix(tree, name, factor, base, overlay):
    n = node(tree, 'ShaderNodeMixRGB', name)
    wire(tree, factor, n.inputs[0])
    wire(tree, (base, base, base, 1) if isinstance(base, (int,float)) else base, n.inputs[1])
    wire(tree, overlay, n.inputs[2])
    return n.outputs[0]


def add_transition(material, contract, source, resources):
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    descriptor = resources[contract['source'].lower()]['details']
    selectors = next(c['fields'] for c in descriptor['chunks'] if c['id']==0x0903A015)
    replacements=[]
    for channel,slot in (('D','BaseColor'),('R','RoughMetal'),('N','Normal')):
        array=resources[contract['slots'][slot].replace('\\','/').lower()]['details']
        for axis in range(3):
            field='U03' if axis==2 else 'U02'
            filename=selectors[field]+'_'+channel+'.dds'
            assert any(r['file'].replace('\\','/').split('/')[-1].lower()==filename.lower() for r in array['namedRefs']),filename
            path=source/'Textures'/contract['source'].split('/')[0]/filename
            assert path.is_file(),path
            sample=tree.nodes.get('tex_'+channel+(' World '+str(axis) if axis else ''))
            assert sample is not None,(material.name,channel,axis)
            old=sample.image.filepath
            image=bpy.data.images.load(str(path),check_existing=True)
            image.filepath='//'+path.relative_to(source).as_posix()
            if channel!='D':image.colorspace_settings.name='Non-Color'
            sample.image=image
            sample['native_layer_field']=field;sample['native_layer_name']=selectors[field]
            if Path(old.replace('\\','/')).name!=filename:replacements.append(dict(node=sample.name,old=old,new=image.filepath))
    uv = node(tree, 'ShaderNodeUVMap', 'Native overlay UV: BaseMaterial', (-1000, 1200))
    uv.uv_map = 'BaseMaterial'
    color = node(tree, 'ShaderNodeVertexColor', 'Native vertex alpha: Color', (-1000, 1500))
    color.layer_name = 'Color'
    textures = {}
    for slot in ('TBaseColorOp', 'TRoughMetal', 'TNormal'):
        native = contract['slots'][slot].replace('\\', '/')
        descriptor = resources[native.lower()]['details']
        filename = descriptor['image'].replace('\\', '/').split('/')[-1]
        path = source / 'Textures' / native.split('/')[0] / filename
        assert path.is_file(), path
        image = bpy.data.images.load(str(path), check_existing=True)
        image.filepath = '//' + path.relative_to(source).as_posix()
        if slot != 'TBaseColorOp':
            image.colorspace_settings.name = 'Non-Color'
        sample = node(tree, 'ShaderNodeTexImage', 'Native overlay ' + slot, (-750, 1200 - len(textures)*250))
        sample.image = image
        wire(tree, uv.outputs['UV'], sample.inputs['Vector'])
        textures[slot] = sample
    factor = math(tree, 'MULTIPLY', textures['TBaseColorOp'].outputs['Alpha'], color.outputs['Alpha'], 'Native blend: texture alpha * vertex alpha')
    for name, overlay in [('Base Color', textures['TBaseColorOp'].outputs['Color'])]:
        socket = principled.inputs[name]
        base = socket.links[0].from_socket if socket.is_linked else tuple(socket.default_value)
        wire(tree, mix(tree, 'Native transition ' + name, factor, base, overlay), socket)
    split = node(tree, 'ShaderNodeSeparateColor', 'Native overlay roughness/metal channels')
    wire(tree, textures['TRoughMetal'].outputs['Color'], split.inputs[0])
    native_r = resources[contract['slots']['TRoughMetal'].replace('\\','/').lower()]['details']
    usage = str(native_r['usage'])
    assert usage in ('36', '37'), usage
    channels = (0, 1) if usage == '36' else (1, 0)
    for name, channel in zip(('Roughness', 'Metallic'), channels):
        socket = principled.inputs[name]
        base = socket.links[0].from_socket if socket.is_linked else socket.default_value
        wire(tree, mix(tree, 'Native transition ' + name, factor, base, split.outputs[channel]), socket)
    # Recover BC5 XY with the native scale/bias, then let Blender build the
    # tangent basis. World normal interpolation remains a renderer adapter.
    xy = node(tree, 'ShaderNodeSeparateXYZ', 'Native overlay encoded normal')
    wire(tree, textures['TNormal'].outputs['Color'], xy.inputs[0])
    x = math(tree, 'SUBTRACT', math(tree, 'MULTIPLY', xy.outputs[0], 1.992188), .992188)
    y = math(tree, 'SUBTRACT', math(tree, 'MULTIPLY', xy.outputs[1], 1.992188), .992188)
    z = math(tree, 'SQRT', math(tree, 'MAXIMUM', math(tree, 'SUBTRACT', 1, math(tree, 'ADD', math(tree,'MULTIPLY',x,x), math(tree,'MULTIPLY',y,y))), 0))
    encoded = vec(tree, 'ADD', vec(tree, 'SCALE', combine(tree, x, y, z), .5), (.5,.5,.5))
    normal = node(tree, 'ShaderNodeNormalMap', 'Native overlay tangent normal')
    normal.uv_map = 'BaseMaterial'
    wire(tree, encoded, normal.inputs['Color'])
    socket = principled.inputs['Normal']
    if socket.is_linked:
        base = socket.links[0].from_socket
    else:
        base = node(tree, 'ShaderNodeNewGeometry', 'Native base normal').outputs['Normal']
    blended = mix(tree, 'Native transition world normals', factor, base, normal.outputs['Normal'])
    wire(tree, vec(tree, 'NORMALIZE', blended), socket)
    material['tm_shader_source'] = contract['source']
    material['tm_transition_revision'] = REVISION
    material['tm_transition_formula'] = 'mix(projected base, UV overlay, overlay texture alpha * Color vertex alpha)'
    material['tm_transition_limit'] = 'Compiled family branch recovered; existing projected base and Blender normal interpolation remain renderer approximations.'
    material['tm_unresolved_native_operations'] = json.dumps(['Exact runtime permutation, projection weighting, terrain microdetail and renderer normal response remain unverified.'])
    return dict(name=material.name, source=contract['source'], usage=usage, formula=material['tm_transition_formula'],base_layer_replacements=replacements)


def main():
    p = argparse.ArgumentParser()
    for key in ('source', 'output', 'contracts', 'resources', 'inventory'):
        p.add_argument('--'+key, type=Path, required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    source, out = args.source.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert source != out
    contracts = json.loads(args.contracts.read_text(encoding='utf-8'))
    resources = {r['path'].lower():r for r in json.loads(args.resources.read_text(encoding='utf-8'))['rows']}
    inventory = json.loads(args.inventory.read_text(encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=str(source/'Trackmania2020_assets.blend'), load_ui=False)
    materials = {m.name:m for m in bpy.data.materials if m.asset_data}
    original = {n:(m['tm_asset_id'], graph(m), m.asset_data.catalog_id, hashlib.sha256(repr(m.preview_ensure().image_pixels[:]).encode()).hexdigest()) for n,m in materials.items()}
    cats = {}
    for line in (source/'blender_assets.cats.txt').read_text(encoding='utf-8-sig').splitlines():
        fields = line.split(':',2)
        if len(fields)==3 and not line.startswith('#'):cats[fields[0]]=fields[1]
    moved=[]
    warp = {'TM_Warp'+name+'_asset' for name in ('Ceiling','Details','Glass','Technic','Wall2','Wall')}
    for row in inventory['materials']:
        if 'ColorBlindness' not in row['name'] and row['name'] not in warp:continue
        material=materials[row['name']]
        path='Trackmania2020/08 Preview only/Conditional variants/Color blindness' if 'ColorBlindness' in row['name'] else 'Trackmania2020/08 Preview only/Unsupported Warp originals'
        cid=str(uuid.uuid5(uuid.NAMESPACE_URL,'tm2020-assets/'+path))
        cats[cid]=path
        material.asset_data.catalog_id=cid
        material['tm_game_material_exportable']=False
        material['tm_preview_only_reason']='Game setting selects the alternate palette; the link exports the ordinary base material.' if 'ColorBlindness' in row['name'] else 'Original Warp link reported broken; use '+row['name'].replace('_asset','_WithLightmap_asset')+'.'
        material.asset_data.description='Preview only. '+material['tm_preview_only_reason']+' '+(material.asset_data.description or '')
        if 'Preview only' not in {t.name for t in material.asset_data.tags}:material.asset_data.tags.new('Preview only')
        row['catalog']=path
        row['preview_only']=True
        row['usage'].insert(0,'Preview only. '+material['tm_preview_only_reason'])
        moved.append(row['name'])
    assert len(moved)==21, moved
    transitions=[]
    for contract in contracts:
        if contract['asset_id'] and contract['vertex_alpha'] and (contract['shader_family'] or '').endswith('PyPxz_Ids_Tex.Material.gbx'):
            material=materials[contract['name']]
            transitions.append(add_transition(material,contract,source,resources))
            row=next(r for r in inventory['materials'] if r['name']==material.name)
            row['usage'].append('Native transition layer: paint alpha of the active Color colour attribute (0 = projected base; 1 = UV overlay weighted by texture alpha). RGB does not control this blend. Keep BaseMaterial and LightMap UV maps.')
            material.asset_data.description += ' Vertex alpha: Color alpha 0 selects the projected base; alpha 1 adds the native UV overlay through its texture alpha.'
    changed={t['name'] for t in transitions}
    for name,material in materials.items():
        previous=original[name]
        assert previous[0]==material['tm_asset_id']
        assert previous[3]==hashlib.sha256(repr(material.preview_ensure().image_pixels[:]).encode()).hexdigest()
        if name not in changed:assert previous[1]==graph(material),name
        if name not in moved:assert previous[2]==material.asset_data.catalog_id,name
    # Use an explicit reviewed family allowlist. Mixed/default UV inputs and
    # missing exact shaders are not cleared on the basis of a material name.
    projected_families={'Tech3 Block PyPxz_Ids.Material.gbx','Tech3 Block PyPxz_Hue.Material.gbx'}
    uv_aliases={c['alias'] for c in contracts if c['classification']=='projected' and (c['shader_family'] or '').split('\\')[-1] in projected_families}
    uv_aliases.add('PlatformDirt_DecoCliff')
    color_aliases={c['alias'] for c in contracts if c['add_color0']}
    edits=[]
    text=(source/'MaterialLib.txt').read_text(encoding='utf-8-sig')
    def patch(match):
        block=match[0];alias=match[1];before=block
        if alias in uv_aliases and re.search(r'DUvLayer\s*\(\s*Lightmap\s*,',block,re.I):
            block=re.sub(r'^\s*DUvLayer\s*\(\s*BaseMaterial\s*,\s*\d+\s*\)[ \t]*\n','',block,flags=re.M)
            block=re.sub(r'(DUvLayer\s*\(\s*Lightmap\s*,\s*)\d+',r'\g<1>0',block,flags=re.I)
        if alias in color_aliases and not re.search(r'DColor0\s*\(',block):
            block=block.rstrip()+'\n    \tDColor0     ()\n\n'
        if before!=block:edits.append(dict(alias=alias,uv_changed=alias in uv_aliases,color0_added=alias in color_aliases))
        return block
    text=re.sub(r'DMaterial\(([^)]+)\).*?(?=DMaterial\(|DLibrary\(|\Z)',patch,text,flags=re.S)
    (out/'MaterialLib.txt').write_text(text,encoding='utf-8')
    used={cats[b.asset_data.catalog_id] for coll in (bpy.data.materials,bpy.data.worlds,bpy.data.node_groups) for b in coll if b.asset_data}
    cats={cid:path for cid,path in cats.items() if any(u==path or u.startswith(path+'/') for u in used)}
    (out/'blender_assets.cats.txt').write_text('# Stable asset catalogs; empty subtrees omitted.\nVERSION 1\n\n'+'\n'.join(cid+':'+path+':'+path.replace('/','-') for cid,path in sorted(cats.items(),key=lambda x:x[1]))+'\n',encoding='utf-8')
    # Inventory keeps native links even when availability is restricted.
    for row in inventory['materials']:
        row['preview_only']=cats[materials[row['name']].asset_data.catalog_id].startswith('Trackmania2020/08 Preview only')
    (out/'source-materials.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Trackmania2020_assets.blend'),compress=True,relative_remap=False)
    report=dict(revision=REVISION,source_sha256=sha(source/'Trackmania2020_assets.blend'),staged_sha256=sha(out/'Trackmania2020_assets.blend'),moved=moved,transitions=transitions,materiallib_edits=edits,materials=len(materials),preview_only=sum(r['preview_only'] for r in inventory['materials']),identities_and_icons_preserved=True,unrelated_graphs_preserved=True)
    (out/'corrections-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('CORRECTIONS_STAGED',len(moved),len(transitions),len(edits),flush=True)


if __name__=='__main__':main()
