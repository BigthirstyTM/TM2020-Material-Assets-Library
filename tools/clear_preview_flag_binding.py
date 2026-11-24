"""Clear both custom and RNA link storage on the already quarantined flag."""
import argparse,datetime,json,os,shutil,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
p=argparse.ArgumentParser()
for k in ['library','output','receipt']:p.add_argument('--'+k,type=Path,required=True)
p.add_argument('--expected-sha',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
root=a.library.resolve();out=a.output.resolve();out.mkdir(exist_ok=True,parents=True);source=root/'Trackmania2020_assets.blend';assert sha(source)==a.expected_sha
# Blender keeps registered RNA values separately from ordinary ID properties.
# Register only the existing add-on field; do not load the user's add-on/UI.
bpy.types.Material.link=bpy.props.StringProperty(name='Link',default='')
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
baseline={key:(identity(x),graph(x)) for key,x in assets.items()};links={m.name:m.link for m in bpy.data.materials if m.asset_data}
flag_name='TM_ItemFlag_animated_asset';flag=bpy.data.materials[flag_name];assert flag.get('tm_game_material_exportable') is False
assert flag.get('link')=='' and json.loads(flag['MAT_PROPS_AS_JSON'])['link']=='' and flag.get('tm_game_material_path')==''
assert flag.link=='Stadium_ItemFlag',flag.link
flag.link='';assert flag.link=='' and flag.get('link')==''
portable=out/source.name;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(portable),compress=True,relative_remap=False)
backup=out/'backup'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True);shutil.copy2(source,backup/source.name)
old_receipt=a.receipt.read_bytes();(backup/'installation.json').write_bytes(old_receipt)
assert sha(source)==a.expected_sha
pending=source.with_name(source.name+'.flag-rna-pending');shutil.copy2(portable,pending);os.replace(pending,source)
try:
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
 for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
  for x in coll:
   if x.asset_data:
    key=x.bl_rna.identifier+':'+x.name;assert (identity(x),graph(x))==baseline[key],key
 for m in bpy.data.materials:
  if m.asset_data:assert m.link==('' if m.name==flag_name else links[m.name]),m.name
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file() and path.is_relative_to(root),path
 receipt=json.loads(old_receipt);receipt['sha256']=sha(source);receipt['additional_corrections']=[dict(material='TM_ItemFlag_animated_asset',correction='Clear stale registered RNA link; custom and JSON links were already empty.',previous_rna_link='Stadium_ItemFlag',rna_link='',previous_sha256=a.expected_sha,backup=str(backup))]
 a.receipt.write_text(json.dumps(receipt,indent=2));(out/'verification.json').write_text(json.dumps(dict(installed_sha256=receipt['sha256'],rna_link='',raw_link='',json_link='',other_links_preserved=True,asset_graphs_icons_metadata_preserved=True,backup=str(backup)),indent=2));print('FLAG_RNA_BINDING_CLEARED',receipt['sha256'],flush=True)
except BaseException:
 shutil.copy2(backup/source.name,source);a.receipt.write_bytes(old_receipt);raise
