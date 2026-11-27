"""Rebuild only bundles containing reviewed badge changes; retain stable memberships."""
import argparse,json,os,shutil,sys,hashlib
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha
from build_remote_pilot import trees
from remote_materials_contract import contract,fingerprint
p=argparse.ArgumentParser()
for k in ['reference','installation','inventory','audit','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);ref=a.reference.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);host=out/'host';host.mkdir(exist_ok=True)
receipt=json.loads(a.installation.read_text());source=Path(receipt['installed']);assert sha(source)==receipt['sha256']
report=json.loads((ref/'build-report.json').read_text());assert len(report['materials'])==873 and len(report['worlds'])==20 and len(report['bundles'])==122
allowed={r['name'] for r in json.loads(a.inventory.read_text())['materials'] if not r['preview_only']};assert {r['name'] for r in report['materials']}==allowed
targets={r['name'] for r in json.loads(a.audit.read_text())['materials']};assert len(targets)==86 and targets<=allowed
changed_paths={r['path'] for r in report['materials'] if r['name'] in targets};changed=[];reused=[]
for row in report['materials']+report['worlds']:
    dest=out/row['contract_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ref/row['contract_path'],dest)
if (ref/'compression.json').exists():shutil.copy2(ref/'compression.json',out/'compression.json')
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
for g in bpy.data.node_groups:
    if g.asset_data:g.asset_clear()
hashes={}
for bundle in report['bundles']:
    dest=host/bundle['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    if bundle['path'] not in changed_paths:
        if not dest.exists():os.link(ref/'host'/bundle['path'],dest)
        assert sha(dest)==bundle['sha256'];reused.append(bundle['id']);continue
    assert not dest.exists(),'Fresh export required; inspect state before resuming partial bundles'
    members=[r for r in report['materials'] if r['path']==bundle['path']];assert members
    contracts={}
    for row in members:
        m=bpy.data.materials[row['name']];assert m['tm_asset_id']==row['id']
        if m.name in targets:assert m['tm_game_colorpicker'] and 'color_picker' in json.loads(m['tm_asset_effect_badges'])
        # Blender has remapped this informational source path during a master
        # save. Preserve published spelling only when both resolve identically.
        if m.name not in targets:
            previous=json.loads((ref/row['contract_path']).read_text())
            for prop,old_path in previous['properties']['custom_properties'].items():
                if not prop.endswith('preview_source'):continue
                current=m.get(prop)
                if isinstance(old_path,str) and isinstance(current,str) and old_path and current and old_path!=current:
                    def resolved(value):
                        return ((source.parent/value[2:]) if value.startswith('//') else Path(value)).resolve()
                    assert resolved(old_path)==resolved(current) and resolved(current).is_file(),('Preview source changed',m.name,prop)
                    m[prop]=old_path
        image_hashes={}
        for tree in trees(m.node_tree):
            for node in tree.nodes:
                if node.type!='TEX_IMAGE' or not node.image:continue
                im=node.image
                if im.name not in hashes:
                    if im.source=='FILE':
                        if not im.packed_file:
                            path=Path(bpy.path.abspath(im.filepath));assert path.is_file();im.filepath=str(path);im.pack()
                        hashes[im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
                    else:assert im.source=='GENERATED';hashes[im.name]=None
                image_hashes[im.name]=hashes[im.name]
        data=contract(m,image_hashes);sig=fingerprint(data)
        # Bundled neighbours must retain exactly their published material contract.
        if m.name not in targets and sig!=row['fingerprint']:
            (out/'neighbour-actual.json').write_text(json.dumps(data,indent=2))
            (out/'neighbour-expected.json').write_text((ref/row['contract_path']).read_text())
            raise AssertionError(('Unexpected bundled neighbour change',m.name))
        (out/row['contract_path']).write_text(json.dumps(data));row['fingerprint']=sig;contracts[row['id']]=sig
    pending=dest.with_suffix('.pending.blend');bpy.data.libraries.write(str(pending),{bpy.data.materials[r['name']] for r in members},path_remap='NONE',fake_user=True,compress=True);pending.replace(dest)
    digest=sha(dest);size=dest.stat().st_size;bundle.update(sha256=digest,bytes=size,fingerprint=fingerprint(contracts))
    for row in members:row.update(sha256=digest,bytes=size)
    changed.append(bundle['id']);print('BADGE_BUNDLE_REBUILT',len(changed),len(changed_paths),bundle['id'],len(members),size,flush=True)
report.update(source=str(source),source_sha256=receipt['sha256'],revision=receipt['revision'],asset_count=893,total_bytes=sum(b['bytes'] for b in report['bundles']),source_unchanged=True,
              badge_update=dict(materials=sorted(targets),rebuilt_bundles=changed,reused_bundles=reused))
shutil.copy2(source.parent/'blender_assets.cats.txt',host/'blender_assets.cats.txt')
(out/'build-report.json').write_text(json.dumps(report));assert sha(source)==receipt['sha256']
print('INCREMENTAL_BADGE_REMOTE_READY',len(changed),len(reused),flush=True)
