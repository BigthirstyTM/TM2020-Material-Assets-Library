"""Reopen and render meaningful mapping, alpha, depth and animation checks."""
import bpy,argparse,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
report=json.loads((root/'build-report.json').read_text());baseline=json.loads((root/'baseline.json').read_text())
assets={a.bl_rna.identifier+':'+a.name:a for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for a in coll if a.asset_data}
assert set(assets)==set(baseline)
for k,a in assets.items():
    current=identity(a)
    assert current==baseline[k]['identity'],('reopened asset identity changed',k,{field:(baseline[k]['identity'].get(field),value) for field,value in current.items() if baseline[k]['identity'].get(field)!=value})
    if a.name not in report['targets']:assert graph(a)==baseline[k]['graph'],('reopened unrelated graph changed',k)
images=[]
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath and not im.packed_file:
        path=Path(bpy.path.abspath(im.filepath));assert path.is_file(),path;images.append(str(path))
for name in report['targets']:
    m=bpy.data.materials[name]
    assert m.get('tm_shader_fidelity_revision')==report['revision']
    if 'Water' in name:assert m.surface_render_method=='BLENDED',name
for name in report['targets'][:2]:
    t=bpy.data.materials[name].node_tree
    for key in ['Fidelity TBaseColor','Fidelity TRoughMetal','Fidelity TNormal']:
        assert t.nodes[key].inputs[0].links[0].from_node.uv_map=='BaseMaterial'
    for channel in ['D','R','N']:
        for suffix in ['', ' World 1',' World 2']:
            n=t.nodes['tex_'+channel+suffix]
            assert 'DecoHillDirtPy_' in n.image.filepath
            assert tuple(n.inputs[0].links[0].from_node.inputs[1].default_value)==(.03125,.03125,1)
    assert t.nodes['Principled BSDF'].inputs['Alpha'].default_value==1

def reset():
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.render.resolution_x=450;scene.render.resolution_y=220;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='OPEN_EXR';scene.render.film_transparent=False
    return scene

def plane(m,x=0,y=0,alpha=1,rgb=(.2,.6,.9)):
    bpy.ops.mesh.primitive_plane_add(size=2,location=(x,y,0));ob=bpy.context.object
    ob.data.uv_layers[0].name='BaseMaterial';ob.data.materials.append(m)
    if alpha is not None:
        color=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
        for c in color.data:c.color=(*rgb,alpha)
        ob.data.color_attributes.active_color=color
    return ob

def camera(scene,center=(3.3,1.1,0),scale=9):
    bpy.ops.object.camera_add(location=(center[0],center[1],10));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=scale

def emission(material,socket):
    t=material.node_tree;n=t.nodes.new('ShaderNodeEmission');t.links.new(socket,n.inputs['Color'])
    output=next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);t.links.new(n.outputs[0],output.inputs['Surface'])

def render(scene,label):
    scene.render.filepath=str(out/(label+'.exr'));bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(scene.render.filepath,check_existing=False);w,h=im.size
    a=np.asarray(im.pixels[:]).reshape(h,w,4).copy();bpy.data.images.remove(im);assert np.isfinite(a).all(),label
    return a

def at(a,x,y,center=(3.3,1.1),scale=9):
    h,w=a.shape[:2];px=round(w*(.5+(x-center[0])/scale));py=round(h*(.5+(y-center[1])/(scale*h/w)))
    return a[py,px,:3]

tests=[]
for name in report['targets'][:2]+['TM_GlassWaterWall_asset']:
    s=reset();m=bpy.data.materials[name].copy()
    if 'DecoHill' in name:
        socket=m.node_tree.nodes['Fidelity texture alpha x vertex alpha'].outputs[0]
        m.node_tree.nodes['Fidelity vertex alpha control'].inputs['Use painted vertex alpha'].default_value=1
    else:
        socket=m.node_tree.nodes['WaterWall Source Layers Preview'].outputs['Foam amount']
        m.node_tree.nodes['WaterWall Source Layers Preview'].inputs['Use painted vertex alpha'].default_value=1
    emission(m,socket)
    for row in range(2):
        for col,alpha in enumerate([0,.5,1,None]):plane(m,col*2.2,row*2.2,alpha,(1,0,0) if row==0 else (0,1,.7))
    camera(s);a=render(s,name+'-alpha')
    samples=[]
    for dx,dy in [(0,0),(.24,.18),(-.3,-.22)]:
        vals=[float(at(a,c*2.2+dx,dy)[0]) for c in range(4)]
        second=[float(at(a,c*2.2+dx,2.2+dy)[0]) for c in range(4)]
        assert abs(vals[0])<1e-5,(name,vals)
        assert abs(vals[1]-.5*vals[2])<.002,(name,vals)
        assert abs(vals[3])<.002,('Blender missing Color is zero in painted mode',name,vals)
        assert max(abs(v-w) for v,w in zip(vals,second))<.002,('RGB must not affect alpha blend',name,vals,second)
        samples.append(vals)
    assert max(v[2] for v in samples)>.005,(name,samples)
    # Default preview explicitly supplies the game's no-COLOR-input alpha 1.
    key='Fidelity vertex alpha control' if 'DecoHill' in name else 'WaterWall Source Layers Preview'
    m.node_tree.nodes[key].inputs['Use painted vertex alpha'].default_value=0
    fallback=render(s,name+'-fallback')
    fallback_vals=[float(at(fallback,c*2.2,0)[0]) for c in range(4)]
    assert max(fallback_vals)-min(fallback_vals)<.002,(name,fallback_vals)
    assert fallback_vals[3]>.005,(name,fallback_vals)
    tests.append(dict(material=name,alpha_samples=samples))

depths=[]
for row in report['water']:
    s=reset();original=bpy.data.materials[row['name']];m=original.copy();node=m.node_tree.nodes['Water Depth Colour - Source-informed Preview']
    assert node.node_tree.nodes['Native fog colour source'].image.alpha_mode=='NONE'
    emission(m,node.outputs['Fog amount'])
    for col,depth in enumerate([0,3,9]):
        copy=m.copy();copy.node_tree.nodes[node.name].inputs['Water depth (meters, preview)'].default_value=depth
        plane(copy,col*2.2)
    camera(s,center=(2.2,0,0));a=render(s,row['environment']+'-depth')
    vals=[float(at(a,c*2.2,0,center=(2.2,0))[0]) for c in range(3)]
    assert vals[0]<1e-5 and 0<vals[1]<vals[2]<1,vals
    depths.append(dict(environment=row['environment'],depths=[0,3,9],fog=vals))

# Read the evaluated animated UVs rather than merely checking driver strings.
s=reset();m=bpy.data.materials['TM_GlassWaterWall_asset'].copy();n=m.node_tree.nodes['WaterWall Source Layers Preview']
emission(m,n.outputs['UV 0']);plane(m);camera(s,center=(0,0,0),scale=3)
s.frame_set(1);first=render(s,'waterwall-uv-frame1');s.frame_set(7);later=render(s,'waterwall-uv-frame7')
before=at(first,0,0,center=(0,0),scale=3);after=at(later,0,0,center=(0,0),scale=3)
seconds=6*s.render.fps_base/s.render.fps
expected=(.01*math.sin(2*math.pi*seconds/4),(seconds*1)%1)
assert abs(float(after[0]-before[0])-expected[0])<.001
assert abs(float(after[1]-before[1])-expected[1])<.001

# Actual Eevee surfaces, with a contrasting scene behind the water, also catch
# missing images, non-finite normals and completely invisible transmission.
actual=[]
for name in ['TM_PlatformDirt_DecoHill_asset','TM_PlatformDirt_DecoHill2_asset','TM_Water_asset','TM_GlassWaterWall_asset']:
    s=reset();s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=16;s.eevee.use_raytracing=False
    s.render.resolution_x=480;s.render.resolution_y=360;s.view_settings.view_transform='AgX';s.render.image_settings.file_format='PNG'
    m=bpy.data.materials[name];ob=plane(m);ob.scale=(1.5,1.5,1)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.4));floor=bpy.context.object
    checker=bpy.data.materials.new('Backdrop '+name);checker.use_nodes=True;t=checker.node_tree;c=t.nodes.new('ShaderNodeTexChecker');c.inputs['Scale'].default_value=4;c.inputs['Color1'].default_value=(.8,.05,.01,1);c.inputs['Color2'].default_value=(.03,.6,.18,1)
    t.links.new(c.outputs[0],t.nodes['Principled BSDF'].inputs['Base Color']);floor.data.materials.append(checker)
    s.world=bpy.data.worlds.new('Studio '+name);s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.4,.6,1)
    bpy.ops.object.light_add(type='AREA',location=(0,-2,5));bpy.context.object.data.energy=600;bpy.context.object.data.size=4
    bpy.ops.object.camera_add(location=(2.5,-3.5,5));s.camera=bpy.context.object;s.camera.rotation_euler=(Vector((0,0,0))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=5
    arrays=[]
    for frame in ([1,7] if name in ['TM_Water_asset','TM_GlassWaterWall_asset'] else [1]):
        s.frame_set(frame);s.render.filepath=str(out/(name+'-frame'+str(frame)+'.png'));bpy.ops.render.render(write_still=True)
        im=bpy.data.images.load(s.render.filepath,check_existing=False);a=np.asarray(im.pixels[:]).copy();bpy.data.images.remove(im);assert np.isfinite(a).all();arrays.append(a)
    change=float(np.mean(abs(arrays[1]-arrays[0]))) if len(arrays)>1 else None
    if change is not None:assert change>1e-6,(name,change)
    actual.append(dict(material=name,frames=len(arrays),animation_difference=change))

result=dict(revision=report['revision'],staged_sha256=report['staged_sha256'],materials=report['counts']['materials'],assets=len(assets),images=len(images),missing_images=0,
  asset_identities_and_export_settings_preserved=True,unrelated_asset_graphs_preserved=True,alpha=tests,water_depth=depths,
  waterfall_uv=dict(seconds=seconds,observed=(after-before).tolist(),expected=expected),surface_renders=actual,game_runtime_validation=False)
(out/'verification.json').write_text(json.dumps(result,indent=2))
print('SHADER_FIDELITY_VERIFIED',len(tests),len(depths),flush=True);bpy.ops.wm.quit_blender()
