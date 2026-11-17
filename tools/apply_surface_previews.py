"""Apply surface previews to the water-motion-2 source library using research inputs.

Run inside Blender with --factory-startup --background --python-exit-code 1.
Native resource JSON is an external research input, not a bundled game archive.
"""
import bpy,sys,json,hashlib,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from material_preview_adapters import *
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--native-resources',type=Path,required=True)
parser.add_argument('--blend-lookups',type=Path,required=True)
parser.add_argument('--output-directory',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
SOURCE=args.source.resolve();OUT=args.output_directory.resolve();OUT.mkdir(parents=True,exist_ok=True)
BY_PATH={r['path'].lower():r for r in json.loads(args.native_resources.read_text())['rows']}
LOOKUPS=json.loads(args.blend_lookups.read_text())
def shader_for(record):
    name=(record['details'].get('shader') or '').replace(chr(92),'/').split('/')[-1]
    name=name[:-4] if name.lower().endswith('.gbx') else name
    name=name[:-9]+'.Shader.Gbx' if name.lower().endswith('.material') else name
    return BY_PATH.get(('Techno3/Media/Shader/'+name).lower())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
assert not any(m.get('tm_surface_preview_revision') for m in bpy.data.materials),'Surface adapters are already installed; use the water-motion-2 baseline.'
assert bpy.data.materials['TM_Water_asset'].get('tm_water_animation_revision')=='2026.11.17-water-motion-2','Expected the smooth animated water baseline.'
def fingerprint(m):
    t=m.node_tree
    return repr(([(n.name,n.bl_idname,[(s.name,str(getattr(s,'default_value',''))) for s in n.inputs]) for n in t.nodes],[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links])) if t else ''
def identity(m):
    a=m.asset_data;p=m.preview_ensure()
    return (a.catalog_id,a.description,sorted(t.name for t in a.tags),hashlib.sha256(repr(p.image_pixels[:]).encode()).hexdigest(),{k:str(m[k]) for k in m.keys() if not k.startswith('tm_')})
initial={m.name:(identity(m),fingerprint(m)) for m in bpy.data.materials if m.asset_data}
report={k:[] for k in ['water','ice','terrain','glass','screens']};changed=set()
def record(f,m,**kw):report[f].append(dict(name=m.name,**kw));changed.add(m.name);m['tm_surface_preview_revision']='2026.11.17-surfaces-2'
def params(m):return json.loads(m.get('tm_native_parameters','{}'))
def pval(p,key,default):return p.get(key,{}).get('values',[default])[0]
def control(t,name,value):return scalar(t,name,value,(-800,1000))
clear=preview_surface_group(bpy);depth=depth_group(bpy)
for m in bpy.data.materials:
    if not m.asset_data:continue
    if m.name in ['TM_Water_asset']+['TM_'+e+'_Water_asset' for e in ['BlueBay','GreenCoast','RedIsland','WhiteShore']]:
        add_water_clarity(bpy,m,clear);record('water',m)
    src=BY_PATH.get(str(m.get('tm_native_resource','')).lower());shader=shader_for(src) if src else None
    shadername=src['details'].get('shader','') if src else ''
    t=m.node_tree;p=next((n for n in t.nodes if n.type=='BSDF_PRINCIPLED'),None) if t else None
    if not p:continue
    if 'PyPxzTLayered' in shadername and 'Ice' in m.name:
        native=params(m);maxdepth=pval(native,'SubsurfaceMaxDepth',[.1])[0];size=pval(native,'TextureSizeInMeters',[32,32]);opacity=pval(native,'SurfaceMaxOpacity',[.1])[0];color=pval(native,'SurfaceColor',[.9,.92,.99])
        tex=t.nodes.get('tex_D');height=t.nodes.get('Additional H');uv=t.nodes.get('UV Map')
        if tex is None or tex.image is None or uv is None:continue
        d=control(t,'Ice Internal Depth (meters)',maxdepth)
        if height and height.image:
            wire(t,uv.outputs['UV'],height.inputs[0]);d=math(t,'MULTIPLY',height.outputs['Color'],d)
        layer=node(t,'ShaderNodeGroup','Ice Internal Layer Preview',(-300,600));layer.node_tree=depth
        wire(t,uv.outputs['UV'],layer.inputs['UV']);geo=node(t,'ShaderNodeNewGeometry','Ice surface orientation');wire(t,geo.outputs['Normal'],layer.inputs['Normal']);wire(t,d,layer.inputs['Depth (meters)']);layer.inputs['Size (meters)'].default_value=(*size[:2],1)
        for name in ['tex_D','tex_D_HueMask']: 
            n=t.nodes.get(name)
            if n:wire(t,layer.outputs[0],n.inputs[0])
        # Decode each normal sample before mixing; keep native surface/mark selection.
        decoder=bpy.data.node_groups['TM BC5 XY to OpenGL Normal v1']
        for name in ['tex_N','tex_Pxyz_N']:
            texn=t.nodes.get(name)
            if not texn or not texn.image:continue
            links=list(texn.outputs['Color'].links)
            n=node(t,'ShaderNodeGroup','Ice BC5 '+name);n.node_tree=decoder;wire(t,texn.outputs['Color'],n.inputs['XY'])
            for l in links:wire(t,n.outputs['RGB Normal'],l.to_socket)
        surface=node(t,'ShaderNodeMixRGB','Ice Internal Color and Surface Tint',(1550,650))
        base=p.inputs['Base Color'].links[0].from_socket
        rough=p.inputs['Roughness'].links[0].from_socket if p.inputs['Roughness'].is_linked else .25
        wire(t,math(t,'MULTIPLY',rough,control(t,'Ice Surface Max Opacity (native)',opacity)),surface.inputs[0]);wire(t,base,surface.inputs[1]);surface.inputs[2].default_value=(*color[:3],1);wire(t,surface.outputs[0],p.inputs['Base Color'])
        # Native opacity is internal colour mixing, not mesh alpha or clear water.
        for l in list(p.inputs['Alpha'].links):t.links.remove(l)
        p.inputs['Alpha'].default_value=1;p.inputs['IOR'].default_value=1.31;p.inputs['Coat Weight'].default_value=.3;p.inputs['Coat Roughness'].default_value=.08;p.inputs['Subsurface Weight'].default_value=.08;p.inputs['Subsurface Radius'].default_value=(.12,.25,.4)
        m['tm_ice_preview']='Source depth and SurfaceMaxOpacity reconstruct internal layer UV and tint. Native opaque layered shader retained. BC5 normals corrected. IOR 1.31, coat and mild subsurface scattering are Blender preview assumptions; no background transparency is implied.'
        record('ice',m,max_depth=maxdepth,surface_opacity=opacity)
    if 'PyPxz' in shadername and t.nodes.get('TM World Geometry') and all(t.nodes.get(n) for n in ['DIVIDE','DIVIDE.001','DIVIDE.002']):
        addresses={a['name']:a['file'] for a in (shader or {}).get('details',{}).get('addresses',[])};addresses.update({a['name']:a['file'] for a in src['details'].get('slots',[])})
        def limits(key,default):
            ref=addresses.get(key,'').replace('\\','/').split('/')[-1].lower()
            row=next((r for r in LOOKUPS if Path(r['file']).name.lower()==ref),None)
            if not row:return default
            a,b=row['RealParams'];return (a/90,b/90) if row['IntParams'][2]==1 else (a,b)
        top=limits('ACosSmoothPy',(.45,.7));side=limits('ACosSmooth',(.3,.6))
        g=angular_weights(bpy,*top,*side);n=node(t,'ShaderNodeGroup','Terrain Angular Transition Controls',(-1200,1200));n.node_tree=g;wire(t,t.nodes['TM World Geometry'].outputs['Normal'],n.inputs['Normal'])
        for name,sock in zip(['DIVIDE','DIVIDE.001','DIVIDE.002'],n.outputs):
            for l in list(t.nodes[name].outputs[0].links):wire(t,sock,l.to_socket)
        m['tm_terrain_preview']='Native ACosSmoothInRange descriptor endpoints; Blender smoothstep of normalized acos angle approximates generated game LUT. Top and side controls independent. Existing world projections, texture scales, macro colour and normal bases preserved.'
        record('terrain',m,top_range=top,side_range=side)
    if m.name=='TM_CustomGlass_asset':
        native=params(m);rough=pval(native,'Roughness',[.05])[0]
        n=node(t,'ShaderNodeGroup','Glass Clarity and Refraction Preview',(650,650));n.node_tree=clear;n.inputs['Clarity'].default_value=.98;n.inputs['Roughness'].default_value=rough;n.inputs['IOR'].default_value=1.45
        geo=node(t,'ShaderNodeNewGeometry','Glass normal');wire(t,geo.outputs['Normal'],n.inputs['Normal']);wire(t,p.outputs[0],n.inputs['Physical surface'])
        tint=pval(native,'TargetColor',[.36862746,.35686275,.015686275]);n.inputs['Transmission tint'].default_value=tuple(1-v for v in tint[:3])+(1,)
        p.inputs['Base Color'].default_value=n.inputs['Transmission tint'].default_value
        for l in list(p.inputs['Base Color'].links):t.links.remove(l)
        p.inputs['Transmission Weight'].default_value=1
        for key,value in [('Roughness',rough),('IOR',1.45)]:
            s=control(t,'Glass '+key+' (preview)',value);wire(t,s,n.inputs[key]);wire(t,s,p.inputs[key])
        wire(t,n.outputs[0],next(q for q in t.nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output).inputs['Surface']);setup_transparency(m)
        m['tm_glass_preview']='GlassBasic compiled dual-source blend uses complementary per-channel transmittance. Preview uses 1-TargetColor tint, native roughness .05, Fresnel reflection and optional physical refraction. Runtime absorption strength and IOR are approximations.'
        record('glass',m)
    if m.get('tm_parallax_preview'):
        native=params(m);ratio=pval(native,'RefractIndex',[.8])[0];double=pval(native,'DoubleRefract',[0])[0]
        groups=[n for n in t.nodes if n.type=='GROUP' and n.node_tree and n.node_tree.name.startswith('TM Interior Screen Parallax Preview')]
        for old in groups:
            layer=node(t,'ShaderNodeGroup',old.name+' Refracted',old.location);layer.node_tree=depth
            wire(t,old.inputs['UV'].links[0].from_socket,layer.inputs['UV']);layer.inputs['Depth (meters)'].default_value=old.inputs['Depth'].default_value;layer.inputs['Size (meters)'].default_value=(1,1,1);layer.inputs['Refract ratio'].default_value=ratio;layer.inputs['Double refraction'].default_value=double
            # Interior layers refract through a planar panel; surface normal detail remains on the outer material.
            geo=node(t,'ShaderNodeNewGeometry','Screen refraction plane');wire(t,geo.outputs['Normal'],layer.inputs['Normal'])
            for l in list(old.outputs[0].links):wire(t,layer.outputs[0],l.to_socket)
        if groups:
            p.inputs['Coat Weight'].default_value=.25;p.inputs['Coat Roughness'].default_value=.05
            m['tm_screen_refraction_preview']='RefractIndex and DoubleRefract sourced from native parameters; native interior images, alpha composites, depth/meter ratios and outer UV corrections retained. Planar refracted tangent offset with bounded grazing angle approximates interior ray paths; native height ray marching/concave interiors not fully reproduced. Coat defaults are preview assumptions.'
            record('screens',m,layers=len(groups),refract_ratio=ratio,double_refraction=double)

for m in bpy.data.materials:
    if m.name in initial:
        assert identity(m)==initial[m.name][0],('asset identity changed',m.name)
        if m.name not in changed:assert fingerprint(m)==initial[m.name][1],('unrelated graph changed',m.name)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath:image.filepath=bpy.path.abspath(image.filepath)
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file and not Path(i.filepath).is_file()];assert not missing,missing
assert sum(bool(m.asset_data) for m in bpy.data.materials)==1119
assert sum(bool(g.asset_data) for g in bpy.data.node_groups)==42
report.update(revision='2026.11.17-surfaces-2',unchanged_graphs=len(initial)-len(changed),asset_identities_and_icons_preserved=True,missing_images=missing)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Surface-Improvements.blend'),compress=True,relative_remap=False)
(OUT/'build-report.json').write_text(json.dumps(report,indent=2))
print('SURFACE_IMPROVEMENTS_STAGED', {k:len(v) if isinstance(v,list) else v for k,v in report.items()},flush=True)

