"""Render numeric contracts for the reviewed cosine blend and rotated colour frame."""
import argparse,json,math,sys,warnings
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
warnings.filterwarnings('ignore',category=DeprecationWarning)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from projection_refresh_adapters import projected
from material_preview_adapters import wire
from shader_fidelity_adapters import interface
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=scene.render.resolution_y=16;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='OPEN_EXR'
bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=.001;scene.camera=cam
def image(name,values):
 im=bpy.data.images.new(name,width=4,height=4,float_buffer=True);im.colorspace_settings.name='Non-Color';im.pixels=[v for pixel in values for v in pixel];im.update();return im
side=image('Coordinate fixture',[(x/3,y/3,.1,1) for y in range(4) for x in range(4)])
top=image('Top fixture',[(.2,.4,.6,1)]*16);neutral=image('Neutral',[(.4980392,.4980392,1,1)]*16)
slots={prefix+role:dict(scale=[1/size,1/size],translation=[0,0],rotation=0,usage=usage,image='fixture') for prefix,size in [('Py',32),('Pxz',64)] for role,usage in [('BaseColor','Color'),('RoughMetal','37'),('Normal','31')]}
record=dict(slots=slots,array_angles=dict(top=[40,50],side=[25,43]))
def setup(record,top_image):
 mat=bpy.data.materials.new('Diagnostic material');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear()
 g,gi,go=interface(bpy,'Production projection diagnostic',[],[('Colour','NodeSocketColor')])
 def images(role):return (top_image if role.startswith('Py') else side) if 'BaseColor' in role else neutral
 result=projected(bpy,g,mat,record,images);wire(g,result['colour'],go.inputs[0])
 for n in g.nodes:
  if n.type=='TEX_IMAGE':n.interpolation='Closest'
 node=t.nodes.new('ShaderNodeGroup');node.node_tree=g;em=t.nodes.new('ShaderNodeEmission');dst=t.nodes.new('ShaderNodeOutputMaterial')
 wire(t,node.outputs[0],em.inputs[0]);wire(t,em.outputs[0],dst.inputs[0]);ob.data.materials.clear();ob.data.materials.append(mat)
 return mat
tests=[]
def capture(label,n,pos,expected):
 n=Vector(n).normalized();ob.location=pos;ob.rotation_euler=n.to_track_quat('Z','Y').to_euler()
 cam.location=ob.location+n*5;cam.rotation_euler=(-n).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(out/(label+'.exr'));bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(scene.render.filepath,check_existing=False);rgb=np.asarray(im.pixels[:]).reshape(16,16,4)[4:-4,4:-4,:3]
 error=float(np.max(abs(rgb-np.asarray(expected))));assert error<.001,(label,error,expected,rgb.mean(axis=(0,1)).tolist())
 tests.append(dict(test=label,max_error=error))
def smooth(value,angles):
 lo,hi=sorted(math.cos(math.radians(a)) for a in angles);f=min(1,max(0,(value-lo)/(hi-lo)));return f*f*(3-2*f)
def checker(uv):return np.array([int((uv[0]%1)*4)/3,int((uv[1]%1)*4)/3,.1])
setup(record,top)
pos=np.array([13.5,19.5,7.5])
for idx,direction in enumerate([(1,0,0),(0,1,0),(1,1,0),(1,2,.2),(2,1,.2),(1,1,3),(1,1,1),(-1,-1,0),(0,0,1),(0,0,-1)]):
 n=np.array(direction,dtype=float);n/=np.linalg.norm(n)
 tz=smooth(abs(n[2]),[40,50]);sf=1-smooth(abs(n[0])/max(np.linalg.norm(n[:2]),1e-8),[25,43])
 x=checker([pos[1]*(1 if n[0]>0 else -1)/64,pos[2]/64]);y=checker([-pos[0]*(1 if n[1]>0 else -1)/64,pos[2]/64])
 expected=(x*(1-sf)+y*sf)*(1-tz)+np.array([.2,.4,.6])*tz
 capture('array-cosine-'+str(idx),direction,pos,expected)
record.pop('array_angles');record['slots']['PyBaseColor']['scale']=[1/128,1/128];record['slots']['PyBaseColor']['rotation']=72
setup(record,side)
theta=math.radians(72);matrix=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])/128
for idx,pos in enumerate([(13.5,19.5,7.5),(113,-37,11),(-37,72,3),(-100,-60,24)]):
 capture('lake-colour-rotation-'+str(idx),(0,0,1),pos,checker(matrix@np.array(pos[:2])))
(out/'verification.json').write_text(json.dumps(dict(tests=tests,source='Production projected() with diagnostic textures; scalar shader blend and bitmap-coordinate CPU fixtures',game_started=False),indent=2))
print('RECONCILED_PROJECTION_FORMULAS_VERIFIED',len(tests),flush=True)
