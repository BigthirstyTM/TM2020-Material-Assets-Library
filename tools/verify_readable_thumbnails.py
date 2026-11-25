"""Check specific regressions as well as the generic all-asset preservation proof."""
import bpy,json,sys
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_concrete_shaders import pixels
from apply_shader_fidelity import sha
p=Path(sys.argv[sys.argv.index('--')+1]).resolve();report=json.loads((p/'build-report.json').read_text());proof=json.loads((p/'verification.json').read_text());assert proof['staged_sha256']==report['staged_sha256']
assert report['counts']=={'A':843,'B':0,'C':13} and len(report['preserved'])==263
bpy.ops.wm.open_mainfile(filepath=str(p/'Trackmania2020_assets.blend'),load_ui=False)
changes={r['name']:r for r in report['changes']};clocks=[r for r in changes.values() if r['name'].startswith('TM_Chrono') and '-' in r['name']];assert len(clocks)==21
for row in clocks:
 assert row['fixture']['label'].startswith('STEP ') and row['fixture']['clock']['period']>0
 image=pixels(bpy.data.materials[row['name']]);assert np.count_nonzero(image[230:252,:,:3]>220)>100,row['name']
obstacles=[r for r in changes.values() if 'ItemObstacle' in r['name'] and 'ScreenPusherLevel' in r['name']];assert len(obstacles)==6
for row in obstacles:
 assert row['fixture']['label']=='LAST FRAME'
 assert row['fixture']['animation_frames']['TM Animated MulInside']==4
 assert row['fixture']['emission_gain']==10
for name in ['TM_ItemRamp_asset','TM_Pylon_asset']:
 data=pixels(bpy.data.materials[name])[45:210,45:210,:3];assert float(np.median(data))>85,(name,float(np.median(data)))
mods=[r for r in changes.values() if r['name'].startswith('TM_CustomMod')];assert len(mods)==14 and all(r['style']=='A' for r in mods)
assert all(r['name'].startswith('TM_Custom') and not r['name'].startswith('TM_CustomMod') and 'Glass' not in r['name'] for r in changes.values() if r['style']=='C')
assert 'TM_CustomGlass_asset' in report['preserved']
assert not any(g.name.startswith('Thumbnail only') for g in bpy.data.materials)
result=dict(revision=report['revision'],clock_labels=21,obstacle_last_frames=6,custommod_tiles=14,custom_detail_spheres=13,metal_tiles_readable=True,unchanged_previews=263)
(p/'readability-verification.json').write_text(json.dumps(result,indent=2));print('READABILITY_REGRESSIONS_VERIFIED',json.dumps(result),flush=True)
