"""Lift dark identification artwork without modifying production materials."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,png,badge_mask
from thumbnail_preview_pixels import read_saved_preview

p=argparse.ArgumentParser()
for key in ['library','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.library.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);source=root/'Trackmania2020_assets.blend'
expected='0390ebf6f67debbbbfbc88a49c64ff6826431c45cf9d801ac0d8859526e28c6c';assert sha(source)==expected
revision='2026.11.26-thumbnail-shadow-lift-1';bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()};(out/'baseline.json').write_text(json.dumps(baseline))
targets=['TM_ItemObstacleLight_asset','TM_RedIsland_Water_asset','TM_WhiteShore_WaterBottom_asset']+sorted(m.name for m in bpy.data.materials if m.asset_data and m.name.startswith('TM_ItemLampLight'))
assert len(targets)==6,targets
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
previews=out/'previews';previews.mkdir(exist_ok=True);changes=[]
for name in targets:
 m=bpy.data.materials[name];old=pixels(m);fresh=old.copy();rgb=old[:,:,:3].astype(np.float32)/255;lum=rgb@np.array([.2126,.7152,.0722]);weight=np.clip((.5-lum)/.3,0,1)[:,:,None]
 # Local shadow lift fades towards midtones; highlights remain unchanged.
 # Deep blacks gain a small floor; encoded texture contrast stays visible.
 lifted=np.clip(rgb**.8+(18/255)*(1-rgb)**4,0,1)
 fresh[:,:,:3]=np.rint(np.clip(rgb+weight*(lifted-rgb),0,1)*255).astype(np.uint8)
 mask=badge_mask(m);fresh[mask]=old[mask];assert np.array_equal(fresh[mask],old[mask]);assert np.any(fresh!=old),name
 path=previews/(m['tm_asset_id']+'.png');png(path,fresh);png(previews/(m['tm_asset_id']+'-before.png'),old)
 m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist();assert np.array_equal(pixels(m),read_saved_preview(path))
 m['tm_thumbnail_style_revision']=revision
 m['tm_asset_preview_style']=m.get('tm_asset_preview_style','Identification preview')+'; selective gentle shadow lift for dark artwork.'
 changes.append(dict(name=name,id=m['tm_asset_id'],style='shadow-lift',mean_lift=float(np.mean(fresh[:,:,:3].astype(float)-old[:,:,:3])),maximum_lift=int(np.max(fresh[:,:,:3].astype(int)-old[:,:,:3]))))
for k,x in assets.items():assert graph(x)==baseline[k]['graph']
assert sha(source)==expected;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
report=dict(revision=revision,source_sha256=expected,staged_sha256=sha(out/source.name),targets=targets,changes=changes,counts={'shadow-lift':len(targets)},preserved=[m.name for m in bpy.data.materials if m.asset_data and m.name not in targets])
(out/'build-report.json').write_text(json.dumps(report,indent=2));print('SELECTED_ICONS_LIGHTENED',targets,flush=True)
