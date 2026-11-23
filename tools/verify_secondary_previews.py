"""Fresh-file numeric render checks of recovered local operations."""
import argparse,json,sys,warnings
warnings.filterwarnings('ignore',category=DeprecationWarning)
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from material_preview_adapters import wire
from apply_shader_fidelity import sha
parser=argparse.ArgumentParser()
for key in ['library','secondary','output']:parser.add_argument('--'+key,type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
source=args.library.resolve();source_hash=sha(source)
proof={'materials':[dict(name=r['name'],prototype=r['name']) for r in json.loads(args.secondary.read_text())['targets']]}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
scene=bpy.data.scenes.new('P2 formula verification');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=16;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='OPEN_EXR'
bpy.ops.mesh.primitive_plane_add(size=2);plane=bpy.context.object
bpy.ops.object.camera_add(location=(0,0,5));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=2
def colour_image(name,values):
 im=bpy.data.images.new(name,width=len(values),height=1,float_buffer=True);im.colorspace_settings.name='Non-Color';im.pixels=[v for pixel in values for v in pixel];im.update();return im
def capture(material,label,expected):
 plane.data.materials.clear();plane.data.materials.append(material);scene.render.filepath=str(OUT/(label+'.exr'));bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(scene.render.filepath,check_existing=False);rgb=np.asarray(im.pixels[:],dtype=np.float32).reshape(16,16,4)[3:-3,3:-3,:3]
 difference=float(np.max(abs(rgb-np.array(expected))))
 assert difference<.0005,(label,difference,rgb.mean(axis=(0,1)).tolist(),expected)
 return dict(test=label,max_error=difference,expected=expected)
def emission_fixture(group):
 m=bpy.data.materials.new('Formula fixture');m.use_nodes=True;t=m.node_tree;t.nodes.clear();n=t.nodes.new('ShaderNodeGroup');n.node_tree=group.copy()
 em=t.nodes.new('ShaderNodeEmission');out=t.nodes.new('ShaderNodeOutputMaterial');wire(t,n.outputs[0],em.inputs[0]);wire(t,em.outputs[0],out.inputs[0]);return m,n
tests=[]
for record in proof['materials']:
 mat=bpy.data.materials[record['prototype']]
 if 'LightTube' in mat.name:
  group=mat.node_tree.nodes['P2 recovered light-tube emission'].node_tree;m,n=emission_fixture(group);g=n.node_tree
  n.inputs['BaseMaterial UV'].default_value=(.5,.5,0);n.inputs['Geometry normal'].default_value=(0,0,1)
  g.nodes['Source SelfIllum'].image=colour_image('I',[(.1,.2,.3,1)])
  g.nodes['Source SelfIllumRefract'].image=colour_image('IR',[(.7,.6,.5,1)])
  gradient=[(.1,.2,.3,1),(.2,.3,.4,1),(.3,.4,.5,1),(.4,.5,.6,1)]
  g.nodes['Source 1D RefractGradient'].image=colour_image('G',gradient);g.nodes['Source 1D RefractGradient'].interpolation='Closest'
  for direction,index in [((1,0,0),0),((.8,0,.6),2),((0,0,1),3),((0,0,-1),0)]:
   n.inputs['To camera'].default_value=direction
   scale=n.inputs['SelfIllumScaleRefract'].default_value
   expected=[a*1.5+b*c*scale for a,b,c in zip([.1,.2,.3],[.7,.6,.5],gradient[index])]
   tests.append(capture(m,record['name']+'-angle-'+str(index)+'-'+str(direction[2]),expected))
  assert abs(n.inputs['SelfIllumScaleRefract'].default_value-(.2 if 'Big' in mat.name else 0))<1e-6
 else:
  group=mat.node_tree.nodes['P2 opt-in recovered masked hue'].node_tree;m,n=emission_fixture(group);g=n.node_tree
  assert n.inputs['Enable recovered hue preview'].default_value==0
  n.inputs['Original colour'].default_value=(.2,.3,.4,1);n.inputs['Explicit preview target'].default_value=(.4,.2,.6,1)
  for enable,alpha in [(0,1),(1,0),(1,.5),(1,1)]:
   n.inputs['Enable recovered hue preview'].default_value=enable
   g.nodes['Source BaseColorHueMask'].image=colour_image('Mask',[(.2,.8,.4,alpha)])
   weight=enable*alpha;expected=[a*(1-weight)+b*weight for a,b in zip([.2,.3,.4],[.32,.22,.42])]
   tests.append(capture(m,record['name']+'-enable'+str(enable)+'-alpha'+str(alpha),expected))
assert len(tests)==24
assert sha(source)==source_hash
(OUT/'verification.json').write_text(json.dumps(dict(status='24 integrated source-formula render checks passed',tests=tests,input_file_unchanged=True,input_sha256=source_hash,game_started=False),indent=2))
print('P2_PROTOTYPES_VERIFIED',len(tests),flush=True)
