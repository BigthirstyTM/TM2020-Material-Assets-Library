"""Reopen the staged library and verify UV layers, asset identities and native math."""
import bpy,sys,json,argparse,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from deco_ice_adapters import hue,REVISION
from material_preview_adapters import wire
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=json.loads((root/'build-report.json').read_text());baseline=json.loads((root/'baseline.json').read_text())
assert sha(a.original)==report['source_sha256'],'Original library changed'
bpy.ops.wm.open_mainfile(filepath=str(a.original.resolve()),load_ui=False)
def badge_digest(m):
 import hashlib
 pixels=np.asarray(m.preview_ensure().image_pixels[:],dtype=np.int64).astype(np.uint32).view(np.uint8).reshape(256,256,4)[::-1]
 mask=np.zeros((256,256),dtype=bool)
 for idx in range(len(json.loads(m.get('tm_asset_effect_badges','[]')))):
  yy,xx=np.mgrid[:32,:32];rounded=np.hypot(np.maximum(abs(xx-15.5)-10,0),np.maximum(abs(yy-15.5)-10,0))<=5.5;left=218-idx*36;mask[6:38,left:left+32]|=rounded
 return hashlib.sha256(pixels[mask].tobytes()).hexdigest()
original_badges={name:badge_digest(bpy.data.materials[name]) for name in report['targets']}
needed=set();visited=set()
def image_dependencies(tree):
 if tree in visited:return
 visited.add(tree)
 for q in tree.nodes:
  if q.type=='TEX_IMAGE' and q.image:needed.add(q.image.name)
  if q.type=='GROUP' and q.node_tree:image_dependencies(q.node_tree)
for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups]:
 for asset in coll:
  if asset.asset_data and asset.name not in report['targets']:image_dependencies(asset.node_tree if hasattr(asset,'node_tree') else asset)
original_images={im.name:(im.colorspace_settings.name,im.alpha_mode) for im in bpy.data.images if im.name in needed and im.source=='FILE' and im.filepath}
bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
assert all(badge_digest(bpy.data.materials[name])==digest for name,digest in original_badges.items()),'Saved badge pixels changed'
differences=[(name,settings,(bpy.data.images[name].colorspace_settings.name,bpy.data.images[name].alpha_mode) if name in bpy.data.images else 'missing') for name,settings in original_images.items() if name not in bpy.data.images or (bpy.data.images[name].colorspace_settings.name,bpy.data.images[name].alpha_mode)!=settings]
assert not differences,('Existing image settings changed',differences)
assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
assert set(assets)==set(baseline)
for k,x in assets.items():
 current=identity(x);old=baseline[k]['identity'].copy()
 if x.name in report['targets']:
  assert current['icon']!=old['icon'],('Thumbnail unchanged',x.name);current.pop('icon');old.pop('icon')
 assert current==old,('Metadata/export mismatch',k)
 assert x.get('tm_asset_effect_badges','')==baseline[k]['badges']
 if x.name not in report['targets']:assert graph(x)==baseline[k]['graph'],('Unrelated graph changed',k)
images=[]
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath;images.append(im.filepath)
mixed=[]
for name in report['targets']:
 m=bpy.data.materials[name];assert m['tm_deco_ice_revision']==REVISION
 n=m.node_tree.nodes.get('Deco native layer controls')
 if n:
  assert n.inputs['BaseMaterial UV'].links[0].from_node.uv_map=='BaseMaterial'
  d=n.node_tree.nodes.get('Native TBaseColor - mesh UV only')
  if d:
   assert d.image and d.inputs['Vector'].links[0].from_node.type=='GROUP_INPUT'
   assert d.inputs['Vector'].links[0].from_socket.name=='BaseMaterial UV'
   assert n.inputs['Fallback alpha'].default_value==1 and n.inputs['Use painted vertex alpha'].default_value==0
   mixed.append(name)
  for q in n.node_tree.nodes:
   if q.type=='TEX_IMAGE' and q.name in ['Native PyX2','Native PyHx2']:assert q.image.colorspace_settings.name=='Non-Color'
 n=m.node_tree.nodes.get('Ice native surface and internal layers')
 if n:
  assert m.node_tree.nodes['tex_D'].image,'Missing internal ice colour'
  assert n.inputs['Internal colour'].is_linked
  assert not any(q.type in ['ATTRIBUTE','VERTEX_COLOR'] for q in n.node_tree.nodes)
  sample=n.node_tree.nodes['Native TAlpha'];splitter=next(l.to_node for l in sample.outputs[0].links if l.to_node.type=='SEPXYZ')
  assert splitter.outputs[0].is_linked and not splitter.outputs[1].is_linked,'TAlpha must use native R channel'
assert len(mixed)==14,len(mixed)
# Render the actual shader graph's decoded Hue arithmetic on known RGB inputs.
s=bpy.data.scenes.new('Native Hue verification');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.use_denoising=False
s.render.resolution_x=s.render.resolution_y=16;s.render.resolution_percentage=100;s.view_settings.view_transform='Raw';s.render.image_settings.file_format='OPEN_EXR'
bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object
bpy.ops.object.camera_add(location=(0,0,5));s.camera=bpy.context.object;s.camera.data.type='ORTHO';s.camera.data.ortho_scale=1
m=bpy.data.materials.new('Hue math fixture');m.use_nodes=True;ob.data.materials.append(m);t=m.node_tree
rgb=t.nodes.new('ShaderNodeRGB');target=t.nodes.new('ShaderNodeRGB');e=t.nodes.new('ShaderNodeEmission');wire(t,hue(t,rgb.outputs[0],target.outputs[0]),e.inputs['Color']);wire(t,e.outputs[0],t.nodes['Material Output'].inputs['Surface'])
tests=[]
for idx,(v,c) in enumerate([((.2,.8,.1),(.3,1,.2)),((.7,.2,.4),(0,1,0)),((.5,.5,.5),(.9,.6,.3))]):
 rgb.outputs[0].default_value=(*v,1);target.outputs[0].default_value=(*c,1)
 chroma=max(v[1]-.5*(v[0]+v[2]),0);expected=np.clip(chroma*np.array(c)+(v[1]-chroma)*np.mean(c),0,1)
 path=out/('hue-'+str(idx)+'.exr');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);im=bpy.data.images.load(str(path),check_existing=False)
 actual=np.asarray(im.pixels[:]).reshape(16,16,4)[8,8,:3];assert np.max(abs(actual-expected))<.002,(actual,expected)
 tests.append(dict(input=v,target=c,actual=actual.tolist(),expected=expected.tolist()));bpy.data.images.remove(im)
uv_tests=[]
ob.data.uv_layers[0].name='BaseMaterial'
s.render.resolution_x=s.render.resolution_y=32;s.camera.data.ortho_scale=2
def capture(label):
 path=out/(label+'.exr');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);im=bpy.data.images.load(str(path),check_existing=False)
 pixels=np.asarray(im.pixels[:]).reshape(32,32,4)[:,:,:3].copy();bpy.data.images.remove(im);return pixels
for name in ['TM_DecoHill_asset','TM_PlatformDirt_DecoHill2_asset']:
 mat=bpy.data.materials[name].copy();mat.asset_clear();ob.data.materials.clear();ob.data.materials.append(mat);nt=mat.node_tree;n=nt.nodes['Deco native layer controls'];n.node_tree=n.node_tree.copy();ng=n.node_tree
 wire(ng,ng.nodes['Native TBaseColor - mesh UV only'].outputs['Color'],next(q for q in ng.nodes if q.type=='GROUP_OUTPUT').inputs['Base Color'])
 em=nt.nodes.new('ShaderNodeEmission');wire(nt,n.outputs['Base Color'],em.inputs['Color']);wire(nt,em.outputs[0],next(q for q in nt.nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output).inputs['Surface'])
 ob.location=(0,0,0);ob.scale=(1,1,1);s.camera.location=(0,0,5);s.camera.data.ortho_scale=2
 original=capture(name+'-uv-small')
 ob.location=(300,50,0);ob.scale=(4,4,4);s.camera.location=(300,50,5);s.camera.data.ortho_scale=8
 enlarged=capture(name+'-uv-large-translated');difference=float(np.max(abs(original-enlarged)));assert difference<.003,(name,difference)
 assert float(original.max()-original.min())>.05,'UV colour fixture must contain a visible pattern'
 wire(nt,n.outputs['Layer weight'],em.inputs['Color']);enlarged=capture(name+'-alpha-one')
 color=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for v in color.data:v.color=(1,0,0,.5)
 n.inputs['Use painted vertex alpha'].default_value=1
 half=capture(name+'-alpha-half');assert np.max(abs(half-.5*enlarged))<.003
 for v in color.data:v.color=(0,1,1,0)
 zero=capture(name+'-alpha-zero');assert np.max(abs(zero))<.002
 n.inputs['Use painted vertex alpha'].default_value=0
 fallback=capture(name+'-alpha-fallback');assert np.max(abs(fallback-enlarged))<.003
 uv_tests.append(dict(name=name,world_translation_and_scale_difference=difference,painted_alpha_half_zero_and_fallback=True,weight_range=[float(original.min()),float(original.max())]))
counts=dict(materials=sum(bool(x.asset_data) for x in bpy.data.materials),worlds=sum(bool(x.asset_data) for x in bpy.data.worlds),source_groups=sum(bool(x.asset_data) for x in bpy.data.node_groups))
assert counts==dict(materials=1119,worlds=20,source_groups=42),counts
proof=dict(revision=REVISION,staged_sha256=sha(root/'Trackmania2020_assets.blend'),**counts,missing_images=0,images_resolved=len(images),audited_materials=len(report['targets']),mixed_uv_families=mixed,hue_render_tests=tests,uv_render_tests=uv_tests,metadata_preserved=True,unrelated_graphs_preserved=True,existing_image_settings_preserved=True)
(out/'verification.json').write_text(json.dumps(proof,indent=2));print('DECO_ICE_VERIFIED',flush=True);bpy.ops.wm.quit_blender()
