"""Fresh-file contracts, packed data, previews and native links for every material."""
import argparse,hashlib,json,sys,datetime,struct
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from remote_materials_contract import contract,fingerprint
from apply_shader_fidelity import sha
from build_remote_pilot import trees
p=argparse.ArgumentParser();p.add_argument('--export',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.export.resolve();build=json.loads((out/'build-report.json').read_text());checks=[];volumes=[]
for i,row in enumerate(build['materials']):
 path=out/'host'/row['path'];assert sha(path)==row['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
 materials=[m for m in bpy.data.materials if m.asset_data];assert len(materials)==1 and materials[0].name==row['name']
 m=materials[0];assert m['tm_asset_id']==row['id'];assert not any(g.asset_data for g in bpy.data.node_groups);assert not bpy.data.libraries
 expected=json.loads((out/row['contract_path']).read_text());hashes={};images={n.image for t in trees(m.node_tree) for n in t.nodes if n.type=='TEX_IMAGE' and n.image}
 for im in images:
  if im.source=='FILE':
   assert im.packed_file,(m.name,im.name);hashes[im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
   # In-memory only: prove the image decodes without its original file path.
   im.filepath='//unavailable/'+im.name
   if expected['images'][im.name]['size']==[0,0]:
    # Preserve the one existing native 3D DDS resource without claiming
    # Blender can decode it as a 2D image. Reject any newly broken texture.
    data=im.packed_file.data;assert data[:4]==b'DDS ' and struct.unpack_from('<I',data,112)[0]&0x200000
    assert hashes[im.name]==expected['images'][im.name]['hash'];volumes.append(dict(material=m.name,image=im.name,limitation='Existing native volume DDS; no Blender 2D decode'))
   else:assert im.size[0]>0 and len(im.pixels)>0
  else:hashes[im.name]=None
 actual=contract(m,hashes)
 if fingerprint(actual)!=fingerprint(expected):
  (out/'contract-mismatch.json').write_text(json.dumps(dict(name=m.name,expected=expected,actual=actual)))
  raise AssertionError(('Saved material contract differs',m.name))
 assert fingerprint(actual)==row['fingerprint']
 checks.append(dict(name=m.name,id=row['id'],sha256=row['sha256'],packed_images=len(images)))
 if i%10==0:(out/'verification-progress.json').write_text(json.dumps(dict(done=i+1,total=len(build['materials']),material=m.name)))
 print('REMOTE_MATERIAL_VERIFIED',i+1,len(build['materials']),m.name,flush=True)
assert sha(Path(build['source']))==build['source_sha256']
(out/'verification.json').write_text(json.dumps(dict(materials=len(checks),source_sha256=build['source_sha256'],checks=checks,missing_images=0,pre_existing_volume_texture_limitations=volumes,preview_only=0,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2));print('ALL_REMOTE_MATERIALS_VERIFIED',len(checks),flush=True)
