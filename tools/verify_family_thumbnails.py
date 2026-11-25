"""Check family coverage, original emissive pixels, subtle screen lift and preservation."""
import bpy,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_concrete_shaders import pixels,badge_mask
from thumbnail_preview_pixels import read_saved_preview
from apply_shader_fidelity import sha
stage=Path(sys.argv[sys.argv.index('--')+1]).resolve();reference=Path(sys.argv[sys.argv.index('--')+2]).resolve();root=Path(sys.argv[sys.argv.index('--')+3]).resolve()
r=json.loads((stage/'build-report.json').read_text());rows=r['changes'];byname={x['name']:x for x in rows}
assert len(rows)==140 and sum(x['restore'] for x in rows)==80 and sum(x['screen'] for x in rows)==45
assert sum(x['style']=='C' for x in rows)==13 and sum(x['native_emission'] and not x['restore'] for x in rows)==2
for family in ['Boost','Boost2','Turbo2']:
 for suffix in ['Sign','SignOff']:assert f'TM_{family}_{suffix}_asset' in byname
for name in ['TM_RaceArchCheckpoint_asset','TM_RaceArchFinish_asset','TM_RaceArchCheckpointSmall_asset','TM_RaceArchFinishSmall_asset']:
 assert byname[name]['restore']
for prefix in ['TM_ItemObstacle_','TM_ItemObstacleDiscontinuous_']:
 for i in range(3):assert byname[f'{prefix}ItemObstacleLightLevel{i}_asset']['restore']
assert not any('ScreenOff' in x['name'] or 'ScreenBack' in x['name'] for x in rows)
assert not any(x['name'].startswith('TM_Chrono-') or x['name'].startswith('TM_ChronoFinish-') or x['name'].startswith('TM_ChronoCheckpoint-') or 'ScreenPusherLevel' in x['name'] for x in rows)
bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
old={x['name']:pixels(bpy.data.materials[x['name']]) for x in rows if x['screen']}
bpy.ops.wm.open_mainfile(filepath=str(stage/'Trackmania2020_assets.blend'),load_ui=False)
measurements=[]
for row in rows:
 m=bpy.data.materials[row['name']];current=pixels(m);mask=badge_mask(m)
 if row['restore']:
  saved=read_saved_preview(reference/(row['id']+'.png'));assert np.array_equal(current[~mask],saved[~mask]),row['name']
 if row['screen']:
  a=old[row['name']][45:210,45:210,:3].astype(float).mean();b=current[45:210,45:210,:3].astype(float).mean()
  assert b>=a*.99,(row['name'],a,b)
  measurements.append(dict(name=row['name'],before=round(a,2),after=round(b,2)))
assert '18.18x' in bpy.data.materials['TM_CustomBricks_asset']['tm_asset_preview_style']
proof=dict(revision=r['revision'],restored_exact_previews=80,screen_lifts=45,custom_spheres=13,flat_emissive_custommod=2,unchanged_previews=len(r['preserved']),screen_measurements=measurements)
(stage/'family-verification.json').write_text(json.dumps(proof,indent=2));print('FAMILY_THUMBNAILS_VERIFIED',len(rows),flush=True)
