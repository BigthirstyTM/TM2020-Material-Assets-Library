"""Stage or verify a source-backed Dyna update, preserving asset/export contracts."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from dyna_preview_adapters import REVISION,dispin,selfillum,emission_uv

SOURCE_SHA='5beae29fb0ee589180052d4d2032ba2e67898f8f48121810ec2dbb8aa1ae44b7'

def blocks():
    return {a.bl_rna.identifier+':'+a.name:a for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for a in coll}

def snapshot(a):
    t=a.node_tree if hasattr(a,'node_tree') else a
    outputs=repr([(n.name,[(s.identifier,str(getattr(s,'default_value',''))) for s in n.outputs]) for n in t.nodes]) if t else ''
    return dict(identity=identity(a) if a.asset_data else None,graph=graph(a) if t else None,outputs=outputs,
      badges=str(a.get('tm_asset_effect_badges','')))

def verify(stage,source,out):
    report=json.loads((stage/'build-report.json').read_text());before=json.loads((stage/'baseline.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    current=blocks();assert set(current)==set(before),'Datablock membership changed'
    for k,a in current.items():
        now=snapshot(a);old=before[k]
        assert now['identity']==old['identity'],('Asset identity/export/icon mismatch',k)
        assert now['badges']==old['badges'],('Badges changed',k)
        if a.name not in report['graph_targets']:
            assert now['graph']==old['graph'] and now['outputs']==old['outputs'],('Unrelated graph changed',k)
    missing=[];resolved=0
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath and not im.packed_file:
            if not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.filepath)
            resolved+=1
    assert not missing,missing
    assert sum(bool(m.asset_data) for m in bpy.data.materials)==1119
    for name in report['targets']:assert bpy.data.materials[name]['tm_dyna_revision']==REVISION
    for name in report['graph_targets']:
        t=bpy.data.materials[name].node_tree;p=t.nodes['Principled BSDF']
        if 'SpeedometerLight' in name:
            assert t.nodes['tex_I'].inputs['Vector'].links[0].from_node.name=='UV Map'
            continue
        assert not p.inputs['Alpha'].is_linked and p.inputs['Alpha'].default_value==1
        if name!='TM_WarpLight_Dyna_asset':
            assert 'Dyna SI first crossing' in t.nodes
            # No old constant mix may bypass the material's MulInside layer.
            assert p.inputs['Emission Color'].links[0].from_node.name!='Add _D Alpha'
    proof=dict(revision=REVISION,sha256=sha(source),materials=1119,datablocks=len(current),
      identities_export_icons_badges_preserved=True,unrelated_graphs_preserved=True,missing_images=0,images_checked=resolved)
    out.write_text(json.dumps(proof,indent=2));print('DYNA_REOPEN_VERIFIED',proof,flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--audit',type=Path)
    p.add_argument('--stage',type=Path,required=True);p.add_argument('--verify',type=Path)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);stage=a.stage.resolve();stage.mkdir(parents=True,exist_ok=True)
    if a.verify:verify(stage,a.source.resolve(),a.verify.resolve());return
    assert sha(a.source)==SOURCE_SHA,'Installed master changed; rebase before staging'
    bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),load_ui=False)
    assert not any(m.get('tm_dyna_revision') for m in bpy.data.materials)
    before={k:snapshot(v) for k,v in blocks().items()}
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
    audit=json.loads(a.audit.read_text());rows={r['name']:r for r in audit['materials']}
    targets=[n for n in rows if 'Experimental_' not in n]
    changes=[];graph_targets=[]
    for name in targets:
        m=bpy.data.materials[name];record=rows[name]['source'];assert record
        m['tm_dyna_revision']=REVISION
        m['tm_dyna_source_path']=record['path']
        m['tm_dyna_source_sha256']=record.get('sha256','')
        m['tm_dyna_shader']=record['details'].get('shader','')
        m['tm_dyna_suffix_note']='Dyna is an engine variant name, not a guarantee of animation or a different visible shader.'
        if name in ['TM_WarpLight_asset','TM_WarpLightRay_asset','TM_WarpLightRay_Dyna_asset']:
            values={x['name']:x['values'][0] for x in record['details']['pixel']}
            changes.append(dispin(m,values));graph_targets.append(name)
        elif name=='TM_WarpLight_Dyna_asset':
            changes.append(selfillum(m));graph_targets.append(name)
        elif 'SpeedometerLight' in name:
            changes.append(emission_uv(m));graph_targets.append(name)
    (stage/'baseline.json').write_text(json.dumps(before,indent=2))
    report=dict(revision=REVISION,source_sha256=SOURCE_SHA,targets=targets,graph_targets=graph_targets,changes=changes,
      support_files=[],game_started=False,game_render_verified=False)
    bpy.context.preferences.filepaths.save_version=0
    dst=stage/'Trackmania2020_assets.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True,relative_remap=False)
    report['staged_sha256']=sha(dst);(stage/'build-report.json').write_text(json.dumps(report,indent=2))
    print('DYNA_STAGED',graph_targets,flush=True)

if __name__=='__main__':main()
