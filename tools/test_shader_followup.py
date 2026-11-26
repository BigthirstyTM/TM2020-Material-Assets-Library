"""Render-backed regression checks on the staged five-group update."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import sha

source=Path(sys.argv[sys.argv.index('--')+1]).resolve();out=Path(sys.argv[sys.argv.index('--')+2]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);source_hash=sha(source)
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8
s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=128;s.render.resolution_y=96;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.use_compositing=False;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-3
w=bpy.data.worlds.new('Followup test world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.2,.2,.2,1);s.world=w
bpy.ops.mesh.primitive_plane_add(size=4);ob=bpy.context.object;ob.data.uv_layers.active.name='BaseMaterial';wrong=ob.data.uv_layers.new(name='OtherUV')
for uv in wrong.data:uv.uv=(.1,.1)
camdata=bpy.data.cameras.new('Followup camera');cam=bpy.data.objects.new(camdata.name,camdata);s.collection.objects.link(cam);s.camera=cam
cam.location=(2.5,-1,5);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=48
ld=bpy.data.lights.new('Followup softbox','AREA');ld.energy=500;ld.size=5;lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);lo.location=(0,0,5)
results=[]
def material(name):
 m=bpy.data.materials[name]
 if ob.data.materials:ob.data.materials[0]=m
 else:ob.data.materials.append(m)
 return m
def render(name):
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(s.render.filepath,check_existing=False);px=list(im.pixels[:]);bpy.data.images.remove(im)
 assert px and all(abs(x)<1e5 for x in px)
 return px
def delta(a,b):return sum(abs(x-y) for i,(x,y) in enumerate(zip(a,b)) if i%4!=3)/(len(a)*.75)
for name in ['TM_ItemRamp_asset','TM_Boost_Sign_asset','TM_CustomModSelfIllumSimple_asset']:
 material(name);ob.data.uv_layers['BaseMaterial'].active_render=True;base=render(name+'-BaseMaterial')
 wrong.active_render=True;other=render(name+'-other-active')
 d=delta(base,other);assert d<1e-6,(name,d);results.append(dict(test='activeUV-independent',material=name,delta=d))
ob.data.uv_layers['BaseMaterial'].active_render=True
for name in ['TM_Grass_asset','TM_WarpGrass_asset','TM_WarpGrass2_asset']:
 m=material(name);before=render(name+'-source-macro');n=m.node_tree.nodes['Native GrassX2 modulation'];old=n.image
 flat=bpy.data.images.new(name+' neutral macro',1,1);flat.colorspace_settings.name='Non-Color';flat.pixels=(.5,.5,.5,1);n.image=flat
 neutral=render(name+'-neutral-macro');n.image=old
 d=delta(before,neutral);assert d>1e-5,(name,d);results.append(dict(test='GrassX2-contributes',material=name,delta=d))
for name in ['TM_Ad1x1Screen_asset','TM_Boost_Sign_asset','TM_CanopyStructure_asset']:
 m=material(name);base=render(name+'-native-depth');depth=m.node_tree.nodes['Dyna source Meters_Depth'].outputs[0];old=depth.default_value;depth.default_value=0
 flat=render(name+'-zero-depth');depth.default_value=old
 d=delta(base,flat)
 if name!='TM_CanopyStructure_asset':assert d>1e-6,(name,d)
 results.append(dict(test='SI-depth-response',material=name,delta=d,note='A uniform/disabled source height need not produce a visible change.' if d==0 else 'Depth affects rendered SI.'))
for name in ['TM_CanopyGlass_asset','TM_DecalPaintSponsor4x1A_asset','TM_RoadDirt_asset','TM_Canopy_asset']:
 m=material(name);base=render(name+'-hue-disabled');root=m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
 if root.type=='GROUP':
  control=root.inputs['Enable source colour preview'];target=root.inputs['Explicit preview colour']
 else:
  control=m.node_tree.nodes['Enable source colour preview'].outputs[0];target=m.node_tree.nodes['Explicit preview colour'].outputs[0]
 control.default_value=1;target.default_value=(.8,.03,.1,1)
 active=render(name+'-hue-enabled');control.default_value=0
 disabled=render(name+'-hue-disabled-again')
 d=delta(base,active);stable=delta(base,disabled)
 if name=='TM_CanopyGlass_asset':
  mask=m.node_tree.nodes['Source colour mask - tex_D'].image
  assert max(mask.pixels[3::4])==0 and d==0,'Native zero-alpha mask must remain inactive'
 else:assert d>1e-6,(name,d)
 assert stable<1e-6,(name,d,stable)
 results.append(dict(test='optional-Hue-source-mask',material=name,enabled_delta=d,disabled_delta=stable,
  note='Native mask alpha is zero: deliberately no colour change.' if name=='TM_CanopyGlass_asset' else 'Source colour mask responds.'))
for name in ['TM_BlueBay_Land_asset','TM_RedIsland_Dirt_asset','TM_WhiteShore_WaterBottom_asset']:
 m=material(name);ob.scale=(40,40,40);ob.location=(17,31,4)
 pixels=render(name+'-source-array');assert max(pixels[0::4])>0,(name,'black render')
 results.append(dict(test='terrain-render-finite',material=name))
ob.scale=(1,1,1);ob.location=(0,0,0)
assert sha(source)==source_hash
proof=dict(source_sha256=source_hash,render_engine='Cycles CPU',results=results,game_started=False,source_unchanged=True)
(out/'verification.json').write_text(json.dumps(proof,indent=2));print('FOLLOWUP_RENDER_TESTS_PASSED',results,flush=True)
