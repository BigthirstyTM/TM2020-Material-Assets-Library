"""Fresh-file source, graph, icon preservation and projection render checks."""
import argparse,json,sys,warnings
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
warnings.filterwarnings('ignore',category=DeprecationWarning)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from apply_concrete_shaders import pixels,badge_mask
from projection_refresh_adapters import projected,REVISION
from shader_fidelity_adapters import interface
from material_preview_adapters import wire,vec

p=argparse.ArgumentParser()
for key in ['original','staged','inputs','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
data=json.loads(a.inputs.read_text());report=json.loads((a.staged/'build-report.json').read_text());baseline=json.loads((a.staged/'baseline.json').read_text());assert sha(a.original)==report['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(a.original.resolve()),load_ui=False)
badges={n:pixels(bpy.data.materials[n])[badge_mask(bpy.data.materials[n])].copy() for n in report['targets']}
bindings={m.name:{k:str(v) for k,v in m.items() if k.startswith(('tm_game_','tm_export_','tm_asset_id','tm_audit_native_link','tm_native_resource'))} for m in bpy.data.materials if m.asset_data}
image_settings={i.name:(i.colorspace_settings.name,i.alpha_mode) for i in bpy.data.images}
bpy.ops.wm.open_mainfile(filepath=str((a.staged/'Trackmania2020_assets.blend').resolve()),load_ui=False)
assets={x.bl_rna.identifier+':'+x.name:x for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in coll if x.asset_data};assert set(assets)==set(baseline)
for key,asset in assets.items():
 old=baseline[key]['identity'].copy();now=identity(asset)
 if asset.name in report['targets']:old.pop('icon');now.pop('icon')
 assert now==old,('Identity',key)
 if asset.name not in report['targets']:assert graph(asset)==baseline[key]['graph'],('Unrelated graph',key)
 assert asset.get('tm_asset_effect_badges','')==baseline[key]['badges']
for name,old in bindings.items():assert {k:str(v) for k,v in bpy.data.materials[name].items() if k.startswith(('tm_game_','tm_export_','tm_asset_id','tm_audit_native_link','tm_native_resource'))}==old
for name,old in badges.items():assert np.array_equal(pixels(bpy.data.materials[name])[badge_mask(bpy.data.materials[name])],old)
assert all((bpy.data.images[n].colorspace_settings.name,bpy.data.images[n].alpha_mode)==v for n,v in image_settings.items())
for r in data['coverage']:
 m=bpy.data.materials[r['name']];assert m['tm_exact_shader_resource']==r['shader'] and json.loads(m['tm_exact_shader_chain'])==r['chain']
missing=[]
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.filepath)
assert not missing,missing
for name in report['targets']:assert bpy.data.materials[name]['tm_projection_refresh_revision']==REVISION

# Exercise the SAME production projected() function with diagnostic source maps.
scene=bpy.data.scenes.new('Projection frame verification');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=16;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='OPEN_EXR';scene.view_settings.view_transform='Raw'
bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object
bpy.ops.object.camera_add(location=(0,0,5));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=1;scene.camera=cam
fixture=bpy.data.materials.new('Source projection diagnostic');fixture.use_nodes=True;t=fixture.node_tree;t.nodes.clear()
g,gi,go=interface(bpy,'Projection diagnostic',[],[('Normal','NodeSocketVector')])
r=dict(slots={k:dict(scale=[.25,.25],translation=[0,0],rotation=0,usage='36' if 'RoughMetal' in k else '31',image='diagnostic') for prefix in ['Py','Pxz'] for k in [prefix+'RoughMetal',prefix+'Normal']})
def image(value):
 im=bpy.data.images.new('Diagnostic data',width=1,height=1,float_buffer=True);im.colorspace_settings.name='Non-Color';im.pixels=[*value,1];im.update();return im
neutral=image((.992188/1.992188,.992188/1.992188,1));rm=image((.5,0,0))
result=projected(bpy,g,fixture,r,lambda role:neutral if 'Normal' in role else rm,colour=False);wire(g,result['normal'],go.inputs[0])
node=t.nodes.new('ShaderNodeGroup');node.node_tree=g;em=t.nodes.new('ShaderNodeEmission');dst=t.nodes.new('ShaderNodeOutputMaterial');wire(t,vec(t,'ADD',vec(t,'SCALE',node.outputs[0],.5),(.5,.5,.5)),em.inputs[0]);wire(t,em.outputs[0],dst.inputs[0]);ob.data.materials.append(fixture)
def capture(label):
 scene.render.filepath=str(out/(label+'.exr'));bpy.ops.render.render(write_still=True);im=bpy.data.images.load(scene.render.filepath,check_existing=False)
 return np.asarray(im.pixels[:],dtype=np.float32).reshape(16,16,4)[4:-4,4:-4,:3].mean(axis=(0,1))*2-1
tests=[]
def norm(v):v=np.asarray(v,dtype=float);return v/np.linalg.norm(v)
def bc5(v):
 xy=np.asarray(v[:2])*1.992188-.992188;f=.999999/max(np.dot(xy,xy),1);return np.array([xy[0]*f,xy[1]*f,np.sqrt(max(1-f*np.dot(xy,xy),0))])
for idx,direction in enumerate([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,2,3),(-2,1,.5)]):
 n=norm(direction);ob.rotation_euler=Vector(n).to_track_quat('Z','Y').to_euler();ob.scale=(1,1,1);ob.location=(0,0,0);cam.location=Vector(n)*5;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
 for node2 in g.nodes:
  if node2.type=='TEX_IMAGE' and 'Normal' in node2.name:node2.image=neutral
 got=capture('neutral-'+str(idx));error=float(np.max(abs(got-n)));assert error<.001,(idx,got.tolist(),n.tolist())
 tests.append(dict(test='neutral-normal-axis-'+str(idx),max_error=error))
 # Source side maps interpolate in packed space, then decode and orient.
 colours=[(.7,.3,1),(.35,.6,1),(.45,.65,1)]
 samples=[x for x in g.nodes if x.type=='TEX_IMAGE' and 'Normal' in x.name];assert len(samples)==3
 for node2,c in zip(samples,colours):node2.image=image(c)
 w=abs(n)**4;w/=sum(w);f=w[1]/max(w[0]+w[1],1e-8)
 side=bc5(np.array(colours[0])*(1-f)+np.array(colours[1])*f);top=bc5(colours[2])
 tt=np.array([1.,0,0])-n*n[0]
 if np.linalg.norm(tt)<1e-6:tt=np.array([0.,1,0])
 tt=norm(tt);tb=np.cross(n,tt);st=np.cross([0,0,1],n)
 if np.linalg.norm(st)<1e-6:st=np.array([0.,1,0])
 st=norm(st);sb=np.cross(st,n)
 expected=norm((st*side[0]+sb*side[1]+n*side[2])*(1-w[2])+(tt*top[0]+tb*top[1]+n*top[2])*w[2])
 got=capture('perturbed-'+str(idx));error=float(np.max(abs(got-expected)));assert error<.001,(idx,got.tolist(),expected.tolist())
 ob.location=(133,-71,24);ob.scale=(-2,3,.5);cam.location=ob.location+Vector(n)*5
 moved=capture('transformed-'+str(idx));transform_error=float(np.max(abs(moved-expected)));assert transform_error<.001,(idx,transform_error)
 tests.append(dict(test='packed-before-decode-basis-'+str(idx),max_error=error,translation_negative_nonuniform_scale_error=transform_error))
counts=dict(materials=sum(bool(m.asset_data) for m in bpy.data.materials),worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),source_groups=sum(bool(g.asset_data) for g in bpy.data.node_groups));assert counts==dict(materials=1119,worlds=20,source_groups=42)
proof=dict(revision=REVISION,staged_sha256=report['staged_sha256'],**counts,missing_images=0,badges_preserved=True,export_bindings_preserved=True,unrelated_graphs_preserved=True,image_settings_preserved=True,source_links_verified=len(data['coverage']),projection_render_tests=tests,game_started=False)
(out/'verification.json').write_text(json.dumps(proof,indent=2));print('PROJECTION_REFRESH_VERIFIED',flush=True)
