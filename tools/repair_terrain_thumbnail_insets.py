"""Repair terrain inset selection, retaining all artwork outside the inset."""
import bpy,numpy as np,json,argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,png,badge_mask
from thumbnail_preview_pixels import read_saved_preview
from terrain_thumbnail_inset import active_diffuse,source_pixels,place_inset
p=argparse.ArgumentParser()
for k in ['library','inputs','output']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);source=root/'Trackmania2020_assets.blend';before=sha(source);REV='2026.11.26-terrain-insets-2'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()};(out/'baseline.json').write_text(json.dumps(baseline))
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
inputs=json.loads(a.inputs.read_text());targets=inputs['targets'];assert len(targets)==37;changes=[];previews=out/'previews';previews.mkdir(exist_ok=True)
outside=np.ones((256,256),dtype=bool);outside[6:90,6:90]=False
for row in targets:
 m=bpy.data.materials[row['name']];old=pixels(m);fresh=old.copy();im,evidence=active_diffuse(m);path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_relative_to(root)
 place_inset(fresh,source_pixels(im));assert np.array_equal(fresh[outside],old[outside]);assert np.array_equal(fresh[badge_mask(m)],old[badge_mask(m)])
 png(previews/(m['tm_asset_id']+'.png'),fresh);m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist();assert np.array_equal(pixels(m),read_saved_preview(previews/(m['tm_asset_id']+'.png')))
 old_source=row['diffuse']['path'];relative=path.relative_to(root).as_posix();row['diffuse']=dict(path=relative,**evidence)
 m['tm_thumbnail_style_revision']=REV;m['tm_asset_preview_style']='Terrain C: shaded higher block with source foliage and ground shadow; inset from active UV decoration or projected-top shader input.'
 m['tm_thumbnail_geometry_note']='Representative source sprites and block; inset identifies an active source RGB layer, not the complete material or every projected side. Original block artwork retained.'
 changes.append(dict(name=m.name,id=m['tm_asset_id'],style='terrain-C',old_source=old_source,new_source=relative,source_changed=old_source.replace(chr(92),'/')!=relative,evidence=evidence,outside_inset_preserved=True))
for key,x in assets.items():assert graph(x)==baseline[key]['graph']
assert sha(source)==before;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report=dict(revision=REV,source_sha256=before,staged_sha256=sha(out/source.name),targets=[r['name'] for r in changes],changes=changes,counts={'terrain-insets':37},preserved=[m.name for m in bpy.data.materials if m.asset_data and m.name not in {r['name'] for r in changes}])
(out/'build-report.json').write_text(json.dumps(report,indent=2));inputs['revision']=REV;(out/'corrected-inputs.json').write_text(json.dumps(inputs,indent=2));print('INSETS_REPAIRED',sum(r['source_changed'] for r in changes),len(changes),flush=True)
