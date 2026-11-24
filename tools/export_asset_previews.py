"""Export the saved material thumbnails for a full package's offline catalogue."""
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_concrete_shaders import pixels,png
from apply_shader_fidelity import sha
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()),load_ui=False);rows=[]
for m in bpy.data.materials:
 if not m.asset_data:continue
 path=a.output/(m['tm_asset_id']+'.png');png(path,pixels(m));rows.append(dict(name=m.name,id=m['tm_asset_id'],sha256=sha(path)))
(a.output/'source-preview-manifest.json').write_text(json.dumps(dict(source_sha256=sha(a.source),materials=rows),indent=2));print('SAVED_PREVIEWS_EXPORTED',len(rows),flush=True)
