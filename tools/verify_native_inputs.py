"""Reopen staged corrections; render controlled alpha fixtures and export via V2."""
import argparse
import dataclasses
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
import bpy
import addon_utils


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--export',action='store_true')
    parser.add_argument('--python-libs',type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.python_libs:sys.path.insert(0,str(args.python_libs.resolve()))
    root=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    addon_utils.enable('blendermania-addon',default_set=False)
    for handler in list(bpy.app.handlers.load_post):
        if handler.__module__.startswith('blendermania-addon'):bpy.app.handlers.load_post.remove(handler)
    bpy.ops.wm.open_mainfile(filepath=str(root/'Trackmania2020_assets.blend'),load_ui=False)
    report=json.loads((root/'corrections-report.json').read_text())
    names=[r['name'] for r in report['transitions']]
    images=[]
    for image in bpy.data.images:
        if image.source=='FILE' and image.filepath and not image.packed_file:
            path=Path(bpy.path.abspath(image.filepath));assert path.is_file(),path
            images.append(str(path))
    materials=[m for m in bpy.data.materials if m.asset_data]
    assert len(materials)==1119
    assert not any('tm_customization' in m for m in materials)
    for row in report['transitions']:
        m=bpy.data.materials[row['name']];tree=m.node_tree
        assert tree.nodes['Native vertex alpha: Color'].layer_name=='Color'
        assert m.link, m.name
        assert tree.nodes['Native blend: texture alpha * vertex alpha'].outputs[0].is_linked
        assert all(tree.nodes['Principled BSDF'].inputs[n].is_linked for n in ('Base Color','Roughness','Metallic','Normal'))
    for name in report['moved']:assert bpy.data.materials[name].get('tm_game_material_exportable') is False
    for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
    scene=bpy.context.scene
    if args.export:
        F=importlib.import_module('blendermania-addon.utils.Functions')
        C=importlib.import_module('blendermania-addon.utils.CustomImporter')
        props=F.get_global_props();props.LI_gameType='Trackmania2020';props.LI_exportFolderType='Custom'
        work=out/'Work/Items';work.mkdir(parents=True,exist_ok=True)
        props.ST_exportFolder_TM=work.as_posix();props.ST_materialLibPath=str(root/'MaterialLib.txt')
        props.CB_icon_overwriteIcons=False;props.CB_uv_genLightMap=False;props.CB_uv_fixLightMap=False;props.CB_uv_genBaseMaterialCubeMap=False
        for index,name in enumerate(names+['TM_PlatformDirt_DecoCliff_asset','TM_BlueBay_Sand_asset']):
            coll=bpy.data.collections.new('NativeInputs_'+str(index));scene.collection.children.link(coll)
            bpy.ops.mesh.primitive_cube_add(size=8,location=(0,0,4));ob=bpy.context.object
            for previous in list(ob.users_collection):previous.objects.unlink(ob)
            coll.objects.link(ob);ob.data.materials.append(bpy.data.materials[name]);ob.data.uv_layers[0].name='BaseMaterial';ob.data.uv_layers.new(name='LightMap',do_init=True)
            color=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
            for loop in ob.data.loops:color.data[loop.index].color=(.2,.6,.9,(loop.index%3)*.5)
            ob.data.color_attributes.active_color=color
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'Native-Inputs-Export.blend'),relative_remap=True)
        result=bpy.ops.view3d.tm_export_v2(scope='VISIBLE');assert result=={'FINISHED'},result
        deadline=time.monotonic()+300
        while any(t.is_alive() for t in C._CONVERT_THREADS):
            if time.monotonic()>deadline:raise TimeoutError('V2 export worker exceeded 300s')
            time.sleep(.2)
        updates=[]
        while not C._CONVERT_QUEUE.empty():
            entry=C._CONVERT_QUEUE.get()
            if len(entry)>3:
                r=entry[3];updates.append(dict(name=r.name_raw,failed=r.convert_has_failed,message=r.item_error_message,config=dataclasses.asdict(r.config),steps=[dict(title=s.title,additional_infos=list(s.additional_infos)) for s in r.convert_steps]))
        report=dict(operator=sorted(result),conversions=updates,items=[p.relative_to(out).as_posix() for p in out.rglob('*.Item.Gbx')],limitations=['Export conversion evidence; game appearance and baked shadows have not been independently validated.'])
        (out/'export-verification.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
        assert len(updates)==len(names)+2,(len(updates),len(names)+2)
        assert not any(r['failed'] for r in updates),updates
        assert len(report['items'])==len(names)+2
        print('NATIVE_INPUTS_V2_EXPORT_OK',len(updates),flush=True)
        return
    # A shader-factor render checks the actual attribute path, texture sampling,
    # blend direction and independence from vertex RGB in one orthographic image.
    material=bpy.data.materials[names[0]].copy();tree=material.node_tree
    emission=tree.nodes.new('ShaderNodeEmission')
    tree.links.new(tree.nodes['Native blend: texture alpha * vertex alpha'].outputs[0],emission.inputs['Color'])
    output=next(n for n in tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    tree.links.new(emission.outputs[0],output.inputs['Surface'])
    # Same UV coordinates across all squares. Different RGB on lower row.
    for row in range(2):
        for col,alpha in enumerate((0,.5,1)):
            bpy.ops.mesh.primitive_plane_add(size=2,location=(col*2.2,row*2.2,0))
            ob=bpy.context.object;ob.data.materials.append(material);ob.data.uv_layers[0].name='BaseMaterial'
            color=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
            for value in color.data:value.color=((1,0,0,alpha) if row==0 else (0,1,.7,alpha))
            ob.data.color_attributes.active_color=color
    bpy.ops.object.camera_add(location=(2.2,1.1,10));scene.camera=bpy.context.object;scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=7
    scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.use_denoising=False
    scene.render.resolution_x=700;scene.render.resolution_y=500;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='Raw';scene.render.image_settings.file_format='OPEN_EXR';scene.render.filepath=str(out/'alpha-factor.exr')
    bpy.ops.render.render(write_still=True)
    image=bpy.data.images.load(scene.render.filepath,check_existing=False);w,h=image.size;pixels=list(image.pixels)
    # Bilinear-free nearest sampling at corresponding surface UVs, away from edges.
    def at(col,row,dx=0,dy=0):
        x=round(w/2+(col*2.2-2.2+dx)*100);y=round(h/2+(row*2.2-1.1+dy)*100)
        return pixels[(y*w+x)*4]
    tests=[]
    for dx,dy in ((0,0),(.2,.2),(-.3,.1),(.3,-.25)):
        base=[at(c,0,dx,dy) for c in range(3)];rgb=[at(c,1,dx,dy) for c in range(3)]
        assert abs(base[0])<1e-5,base
        assert abs(base[1]-.5*base[2])<.005,base
        assert max(abs(a-b) for a,b in zip(base,rgb))<.005,(base,rgb)
        tests.append(dict(alpha0=base[0],alpha05=base[1],alpha1=base[2],rgb_variant=rgb))
    assert max(t['alpha1'] for t in tests)>.05,tests
    (out/'reopened-verification.json').write_text(json.dumps(dict(materials=len(materials),images=len(images),transitions=len(names),factor_samples=tests,missing_images=0,customization_badges=0),indent=2),encoding='utf-8')
    print('NATIVE_ALPHA_FACTOR_RENDER_OK',len(tests),flush=True)


if __name__=='__main__':main()
