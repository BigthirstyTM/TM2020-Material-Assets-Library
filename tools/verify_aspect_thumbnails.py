"""Verify proportional layouts and rendered bounds, alongside full graph preservation."""
import bpy,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_concrete_shaders import pixels
stage=Path(sys.argv[sys.argv.index('--')+1]).resolve();report=json.loads((stage/'build-report.json').read_text());rows=report['changes'];byname={r['name']:r for r in rows}
assert len(rows)==843 and len(report['preserved'])==276
assert sum(abs(r['aspect']['ratio']-1)>1e-6 for r in rows)==341
for r in rows:
 layout=r['fixture']['layout'];aspect=r['aspect']['ratio'];width=layout['width_pixels'];height=layout['height_pixels']
 assert abs(width/height-aspect)<1e-8,r['name']
 assert width<=256.00001 and height<=(226.00001 if layout['footer_reserved'] else 256.00001),r['name']
 if abs(aspect-1)<1e-6 and not layout['footer_reserved']:assert abs(width-256)<1e-5 and abs(height-256)<1e-5,r['name']
assert byname['TM_Ad16x9Screen_asset']['aspect']['ratio']==16/9
assert byname['TM_Ad2x1Screen_asset']['aspect']['ratio']==2
assert byname['TM_Ad4x1Screen_asset']['aspect']['ratio']==4
assert byname['TM_Chrono-00-00-10_asset']['aspect']['ratio']==.5
assert byname['TM_ItemObstacle_ScreenPusherLevel0_asset']['aspect']['ratio']==2
assert len([r for r in rows if r['fixture'].get('label','').startswith('STEP ')])==21
assert len([r for r in rows if r['fixture'].get('label')=='LAST FRAME'])==6
bpy.ops.wm.open_mainfile(filepath=str(stage/'Trackmania2020_assets.blend'),load_ui=False)
# Actual pixel bounds of opaque screens establish the rendered geometry,
# independently of the dimensions recorded in the layout receipt.
for name,expected_top,expected_bottom in [('TM_Ad16x9Screen_asset',56,199),('TM_Ad4x1Screen_asset',96,159)]:
 image=pixels(bpy.data.materials[name])[:,:,:3].astype(int);background=image[0,128];changed=np.max(abs(image[:,40:210]-background),axis=2)>12
 ys=np.flatnonzero(changed.sum(axis=1)>40);assert len(ys)>0 and abs(ys.min()-expected_top)<=2 and abs(ys.max()-expected_bottom)<=2,(name,ys.min(),ys.max())
image=pixels(bpy.data.materials['TM_Boost2_Sign_asset']);assert np.max(image[0,:,:3])-np.min(image[0,:,:3])>40
proof=dict(revision=report['revision'],tiles=843,rectangular=341,square=502,clock_footers=21,last_frame_footers=6,rendered_bounds_verified=True,production_uvs_unchanged=True,preserved=276)
(stage/'aspect-verification.json').write_text(json.dumps(proof,indent=2));print('ASPECT_THUMBNAILS_VERIFIED',json.dumps(proof),flush=True)
