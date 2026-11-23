"""Stage reviewed shader fixes and refresh icons, without modifying the source."""
import argparse,hashlib,json,struct,sys,zlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_shader_fidelity import identity,graph,sha
from concrete_shader_adapters import apply,REVISION


def pixels(asset):
    return np.asarray(asset.preview_ensure().image_pixels[:],dtype=np.int64).astype(np.uint32).view(np.uint8).reshape(256,256,4)[::-1].copy()


def badge_mask(asset):
    mask=np.zeros((256,256),dtype=bool)
    for idx in range(len(json.loads(asset.get('tm_asset_effect_badges','[]')))):
        yy,xx=np.mgrid[:32,:32];rounded=np.hypot(np.maximum(abs(xx-15.5)-10,0),np.maximum(abs(yy-15.5)-10,0))<=5.5
        left=218-idx*36;mask[6:38,left:left+32]|=rounded
    return mask


def png(path,rgba):
    def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    # Asset previews store premultiplied RGBA; PNG stores straight RGB.
    rgba=rgba.copy();alpha=rgba[:,:,3].astype(np.float32)/255
    for channel in range(3):rgba[:,:,channel]=np.clip(rgba[:,:,channel].astype(np.float32)/np.maximum(alpha,1/255),0,255).astype(np.uint8)
    raw=b''.join(b'\x00'+row.tobytes() for row in rgba)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',256,256,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def main():
    p=argparse.ArgumentParser()
    for key in ['source','inputs','output']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--reuse-render-cache',action='store_true',help='Reuse identical previous render fixtures after a reviewed input-only correction.')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    data=json.loads(args.inputs.read_text());source=root/'Trackmania2020_assets.blend';sourcehash=sha(source)
    assert sourcehash==data['source_sha256'],'Source revision changed; review before rebuilding'
    targets=[r['name'] for r in data['materials']]
    bpy.ops.wm.open_mainfile(filepath=str(out/'graph-stage.blend' if args.resume else source),load_ui=False)
    assets={x.bl_rna.identifier+':'+x.name:x for c in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for x in c if x.asset_data}
    if not args.resume:
        baseline={k:dict(identity=identity(x),graph=graph(x),badges=x.get('tm_asset_effect_badges','')) for k,x in assets.items()}
        (out/'baseline.json').write_text(json.dumps(baseline,indent=2))
        for im in bpy.data.images:
            if im.source=='FILE' and im.filepath:im.filepath=bpy.path.abspath(im.filepath)
        image_index={};image_cache={};resolved=[]
        for path in (root/'Textures').rglob('*'):
            if path.is_file():image_index.setdefault(path.name.lower(),[]).append(path)
        def loader(record):
            def load(slot):
                d=record['slots'].get(slot,{});image=d.get('image')
                if not image:return None
                filename=Path(image.replace('\\','/')).name;env=record['source'].split('/')[0]
                for text in [image,d['resource']]:
                    for name in ['Stadium','BlueBay','GreenCoast','RedIsland','WhiteShore']:
                        if text.lower().replace('\\','/').startswith(name.lower()+'/'):env=name
                path=root/'Textures'/env/filename
                if not path.is_file():
                    candidates=image_index.get(filename.lower(),[])
                    assert candidates and (len(candidates)==1 or len({sha(x) for x in candidates})==1),('Missing/ambiguous',record['name'],slot,filename)
                    path=sorted(candidates,key=lambda x:len(str(x)))[0]
                space='sRGB' if d.get('usage')=='Color' and slot not in ['PyX2','PyHx2','PyH2','GrassX2','FenceA'] else 'Non-Color'
                # FenceA includes modulation RGB plus opacity. Both are data.
                key=(str(path),space)
                if key not in image_cache:
                    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=space;im.alpha_mode='CHANNEL_PACKED';image_cache[key]=im
                resolved.append(dict(material=record['name'],slot=slot,path=str(path),colour_space=space));return image_cache[key]
            return load
        changes=[]
        for r in data['materials']:
            changes.append(apply(bpy,bpy.data.materials[r['name']],r,loader(r)));print('ADAPTED',r['name'],r['findings'],flush=True)
        report=dict(revision=REVISION,source_sha256=sourcehash,targets=targets,changes=changes,resolved_slots=resolved,support_files=[])
        (out/'build-report.json').write_text(json.dumps(report,indent=2))
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'graph-stage.blend'),compress=True,relative_remap=False)
    else:
        baseline=json.loads((out/'baseline.json').read_text());report=json.loads((out/'build-report.json').read_text())
    scene=bpy.data.scenes.new('Native Surface Thumbnail Studio');bpy.context.window.scene=scene
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=scene.render.resolution_y=256;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    world=bpy.data.worlds.new('Native preview studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.46,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
    bpy.ops.mesh.primitive_plane_add(size=32);panel=bpy.context.object;panel.data.uv_layers[0].name='BaseMaterial'
    bpy.ops.object.camera_add(location=(0,-15,43));cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=36;scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-12,-10,25));light=bpy.context.object;light.data.energy=20000;light.data.shape='DISK';light.data.size=18;light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    thumbs=out/'renders';thumbs.mkdir(exist_ok=True);catalogue=out/'previews';catalogue.mkdir(exist_ok=True);badge_checks=[]
    for idx,name in enumerate(targets):
        m=bpy.data.materials[name];old=pixels(m);mask=badge_mask(m);panel.data.materials.clear();panel.data.materials.append(m);path=thumbs/(name+'.png')
        if not ((args.resume or args.reuse_render_cache) and path.is_file()):scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        with bpy.context.temp_override(id=m):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
        fresh=pixels(m);fresh[mask]=old[mask];m.preview.image_pixels=np.ascontiguousarray(fresh[::-1]).view(np.uint32).reshape(-1).view(np.int32).tolist()
        assert np.array_equal(pixels(m)[mask],old[mask]);png(catalogue/(m['tm_asset_id']+'.png'),fresh)
        badge_checks.append(dict(name=name,pixels=int(mask.sum()),preserved=True))
        m['tm_asset_preview_style']='Rendered Blender preview of reviewed native surface roles; existing badges retained.'
        m['tm_asset_preview_source']=REVISION
        (out/'progress.json').write_text(json.dumps(dict(phase='thumbnails',done=idx+1,total=len(targets),material=name)))
        print('THUMBNAIL',idx+1,len(targets),name,flush=True)
    for k,x in assets.items():
        current=identity(x);previous=baseline[k]['identity'].copy()
        if x.name in targets:current.pop('icon');previous.pop('icon')
        assert current==previous,('Identity/export changed',k)
        assert x.get('tm_asset_effect_badges','')==baseline[k]['badges']
        if x.name not in targets:assert graph(x)==baseline[k]['graph'],('Unrelated graph changed',k)
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
    for ob in list(scene.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.context.window.scene=next(s for s in bpy.data.scenes if s!=scene);bpy.data.scenes.remove(scene);bpy.data.worlds.remove(world)
    assert sha(source)==sourcehash
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/source.name),compress=True,relative_remap=False)
    report.update(staged_sha256=sha(out/source.name),badge_checks=badge_checks)
    (out/'build-report.json').write_text(json.dumps(report,indent=2));(out/'progress.json').write_text(json.dumps(dict(phase='staged',done=len(targets),total=len(targets))))
    print('CONCRETE_SHADERS_STAGED',flush=True);bpy.ops.wm.quit_blender()


if __name__=='__main__':main()
