"""Reviewed concrete source corrections; native export contracts are preserved."""
import json
from material_preview_adapters import node,wire,math,vec,combine,depth_group
from shader_fidelity_adapters import sample,split,bc5,tangent_normal,rough_channels,clear_input,mix
from deco_ice_adapters import terrain,layered_ice,transform,hue,layout

REVISION='2026.11.23-native-surfaces-1'


def restore_ice_depth(bpy,m,record,images):
    t=m.node_tree
    layered_ice(bpy,m,record,images)
    uv=t.nodes['Ice BaseMaterial UV'].outputs[0]
    height=sample(t,'Native internal ice depth',images('SubsurfaceDepth'),uv)
    maximum=record['native_parameters']['SubsurfaceMaxDepth']['values'][0][0]
    depth=math(t,'MULTIPLY',split(t,height.outputs['Color'])[0],maximum,'Native sampled internal depth in meters')
    layer=t.nodes['Ice Internal Layer Preview']
    wire(t,depth,layer.inputs['Depth (meters)'])
    wire(t,uv,layer.inputs['UV'])
    for name in ['tex_D','tex_D_HueMask']:
        if t.nodes.get(name):wire(t,layer.outputs[0],t.nodes[name].inputs['Vector'])
    # Depth is not a displaced outer-surface height. The new surface adapter
    # bypasses the legacy Additional Height Detail/Bump nodes entirely.
    m['tm_native_ice_depth_role']='SubsurfaceDepth.R * SubsurfaceMaxDepth, internal UV depth only; no external bump.'


def source_specular(m):
    p=m.node_tree.nodes['Principled BSDF']
    clear_input(m.node_tree,p.inputs['Specular IOR Level'],.5)
    m['tm_specular_source_correction']='RoughMetal usage 36/37 contains roughness/metalness, not blue-channel F0. Removed B-to-Specular mapping; retain Blender standard dielectric IOR response (Specular IOR Level 0.5). Native game BRDF/lighting remains renderer-specific.'


def restore_screen_normal(m,images):
    image=images('Normal');assert image
    changed=[]
    def visit(t,seen):
        if t in seen:return
        seen.add(t)
        for n in t.nodes:
            if n.type=='TEX_IMAGE' and n.image and 'lightcells3_n' in n.image.filepath.lower():
                n.image=image;changed.append(n.name)
            # Do not mutate shared node groups: these screens keep their samples
            # in their material trees. A new layout must be reviewed explicitly.
    visit(m.node_tree,set());assert changed,m.name
    return changed


def grass_fence(bpy,m,record,images):
    t=m.node_tree;p=t.nodes['Principled BSDF']
    g=bpy.data.node_groups.new('TM Native GrassFence Surface','ShaderNodeTree')
    g.interface.new_socket(name='Surface',in_out='OUTPUT',socket_type='NodeSocketShader')
    out=node(g,'NodeGroupOutput','Native surface')
    geometry=node(g,'ShaderNodeNewGeometry','World position')
    xyz=split(g,geometry.outputs['Position']);world=combine(g,xyz[0],xyz[1])
    diffuse=sample(g,'Native Diffuse',images('Diffuse'),transform(g,world,record['slots']['Diffuse']))
    macro=sample(g,'Native GrassX2',images('GrassX2'),transform(g,world,record['slots']['GrassX2']))
    uv=node(g,'ShaderNodeUVMap','Authored fence UV');uv.uv_map='BaseMaterial'
    fence=sample(g,'Native FenceA',images('FenceA'),uv.outputs[0])
    # Pixel program: Diffuse * (GrassX2*2) * (FenceA.rgb*2).
    colour=vec(g,'SCALE',vec(g,'MULTIPLY',vec(g,'MULTIPLY',diffuse.outputs[0],macro.outputs[0]),fence.outputs[0]),4)
    surface=node(g,'ShaderNodeBsdfPrincipled','Two-sided grass fence')
    wire(g,colour,surface.inputs['Base Color']);surface.inputs['Roughness'].default_value=1
    # Native MSAA sample coverage is not a generic material alpha threshold.
    # Use a labelled deterministic preview cutout; do not restore noisy dither.
    cutoff=node(g,'ShaderNodeValue','Preview cutout threshold (not native AlphaRef units)');cutoff.outputs[0].default_value=.5
    alpha=math(g,'GREATER_THAN',fence.outputs['Alpha'],cutoff.outputs[0],'Preview binary fence silhouette')
    transparent=node(g,'ShaderNodeBsdfTransparent','Outside fence')
    result=node(g,'ShaderNodeMixShader','Fence cutout');wire(g,alpha,result.inputs[0]);wire(g,transparent.outputs[0],result.inputs[1]);wire(g,surface.outputs[0],result.inputs[2]);wire(g,result.outputs[0],out.inputs[0])
    n=node(t,'ShaderNodeGroup','Native GrassFence layers');n.node_tree=g;layout(g)
    output=next(n for n in t.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    wire(t,n.outputs[0],output.inputs['Surface']);m.use_backface_culling=False;m.surface_render_method='BLENDED';m.use_transparent_shadow=True
    m['tm_grass_fence_preview']='Native Diffuse * GrassX2 * FenceA RGB modulation and source FenceA alpha restored, double-sided deterministic cutout. VDepLight render target, geometry edge fade, mesh strip deformation, native MSAA alpha coverage and engine lighting remain unavailable in a standalone Blender material. Threshold .5 is a preview setting, not a conversion of AlphaRef 50.'


def track_borders(bpy,m,record,images):
    t=m.node_tree;p=t.nodes['Principled BSDF'];params=record['native_parameters']
    val=lambda key:params[key]['values'][0]
    uv=node(t,'ShaderNodeUVMap','TrackBorders BaseMaterial UV');uv.uv_map='BaseMaterial'
    outer=sample(t,'Native TrackBorders outer colour',images('BaseColorOp'),uv.outputs[0])
    mask=sample(t,'Native TrackBorders colour target mask',images('BaseColorHueMask'),uv.outputs[0])
    # BaseColorTarget vectors are selection controls, not literal green RGB.
    # Use the stored default colour table entry and label runtime selection.
    table=json.loads(m['tm_native_color_table'])['Colors']
    target_id=int(val('BaseColorTargetId')[0]);entry=table[target_id].lstrip('#')
    colour_target=tuple(int(entry[i:i+2],16)/255 for i in [0,2,4])+(1,)
    target=node(t,'ShaderNodeRGB','TrackBorders default colour-table target');target.outputs[0].default_value=colour_target
    colour=mix(t,'Native alpha-selected colour target',mask.outputs['Alpha'],outer.outputs[0],hue(t,mask.outputs[0],target.outputs[0]))
    rm=sample(t,'Native TrackBorders RoughMetal',images('RoughMetal'),uv.outputs[0]);rough,metal=rough_channels(t,rm.outputs[0],record['slots']['RoughMetal']['usage'])
    norm=tangent_normal(t,bc5(t,sample(t,'Native TrackBorders normal',images('Normal'),uv.outputs[0]).outputs[0]))
    height=sample(t,'Native TrackBorders height',images('Height'),uv.outputs[0])
    inner=node(t,'ShaderNodeGroup','TrackBorders planar native-depth preview');inner.node_tree=depth_group(bpy)
    wire(t,uv.outputs[0],inner.inputs['UV']);geo=node(t,'ShaderNodeNewGeometry','TrackBorders refraction plane');wire(t,geo.outputs['Normal'],inner.inputs['Normal'])
    wire(t,math(t,'MULTIPLY',split(t,height.outputs[0])[0],val('Meters_Depth')[0]),inner.inputs['Depth (meters)'])
    inner.inputs['Size (meters)'].default_value=(*val('Meters_UV')[:2],1)
    inner.inputs['Refract ratio'].default_value=val('RefractIndex')[0];inner.inputs['Double refraction'].default_value=val('DoubleRefract')[0]
    interior=sample(t,'Native TrackBorders MulInside',images('MulInside'),inner.outputs[0])
    wire(t,mix(t,'Preview outer opacity and interior',outer.outputs['Alpha'],interior.outputs[0],colour),p.inputs['Base Color'])
    emission=sample(t,'Native TrackBorders SI',images('SI'),uv.outputs[0]);si_mask=sample(t,'Native TrackBorders SI colour mask',images('SI_HueMask'),uv.outputs[0])
    si_target=node(t,'ShaderNodeRGB','TrackBorders default SI colour-table target');si_target.outputs[0].default_value=colour_target
    wire(t,mix(t,'Native SI colour target',si_mask.outputs['Alpha'],emission.outputs[0],hue(t,si_mask.outputs[0],si_target.outputs[0])),p.inputs['Emission Color'])
    clear_input(t,p.inputs['Emission Strength'],val('SelfIllum_Scale')[0]);wire(t,rough,p.inputs['Roughness']);wire(t,metal,p.inputs['Metallic']);wire(t,norm,p.inputs['Normal'])
    clear_input(t,p.inputs['Specular IOR Level'],.5);clear_input(t,p.inputs['Alpha'],1)
    m['tm_native_binding_resolution']='Stadium is the source texture family. Native material and effective export identity are the existing BlueBay_TrackBordersInWorld modifier; source inventory confirms this. No export link was changed.'
    m['tm_track_borders_preview']='Source outer D/R/N, native colour target masks, SI scale, height and internal image restored. Internal projection is a bounded planar Blender approximation of native interior composition, not exact native cube/intersection rendering. Runtime target-table selection and engine render-buffer composition remain approximate.'


def apply(bpy,m,record,images):
    flags=set(record['findings']);changes=[]
    if flags.intersection({'F02','F05','F06','F07','F08','F10'}):
        # Explicit slot maps also cover array-selected DetailsToDirt.
        terrain(bpy,m,record,images);changes.append('native projected/UV/Hue/macro roles')
        if 'F06' in flags:
            m['tm_unresolved_native_operations']=json.dumps(['Native Hue chroma/grey formula and stored TargetColor restored; projection normal bases, angular lookup, runtime colour customization and renderer lighting remain approximate.'])
    if flags.intersection({'F03','F04'}):restore_ice_depth(bpy,m,record,images);changes.append('native ice surface and sampled internal depth')
    if 'F09' in flags:track_borders(bpy,m,record,images);changes.append('resolved source identity and native border layers')
    if 'F11' in flags:changes.append(dict(screen_normal_nodes=restore_screen_normal(m,images)))
    if 'F12' in flags:grass_fence(bpy,m,record,images);changes.append('native fence surface layers and cutout')
    if 'F01' in flags:source_specular(m);changes.append('removed RoughMetal B-to-specular connection')
    m['tm_concrete_shader_revision']=REVISION
    m['tm_concrete_shader_fixes']=json.dumps(record['findings'])
    return dict(name=m.name,findings=record['findings'],changes=changes)
