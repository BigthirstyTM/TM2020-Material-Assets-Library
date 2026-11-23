"""Stage the targeted shader correction without editing an upload package."""
import bpy,argparse,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from shader_fidelity_adapters import decohill,water,waterwall,REVISION

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def identity(a):
    p=a.preview_ensure();d=a.asset_data
    def value(v):
        if isinstance(v,(str,int,float,bool)) or v is None:return v
        if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name]
        if hasattr(v,'items'):return {k:value(x) for k,x in v.items()}
        try:return [value(x) for x in v]
        except TypeError:return str(v)
    return dict(catalog=d.catalog_id,description=d.description,tags=sorted(t.name for t in d.tags),
      icon=hashlib.sha256(repr(p.image_pixels[:]).encode()).hexdigest(),export={k:value(v) for k,v in a.items() if not k.startswith('tm_')})

def graph(a):
    t=a.node_tree if hasattr(a,'node_tree') else a
    return repr(([(n.name,n.bl_idname,getattr(n,'operation',None),getattr(n,'blend_type',None),
      getattr(n,'uv_map',None),getattr(n,'layer_name',None),n.image.name if n.type=='TEX_IMAGE' and n.image else None,
      n.node_tree.name if n.type=='GROUP' and n.node_tree else None,
      [(s.identifier,str(getattr(s,'default_value',''))) for s in n.inputs]) for n in t.nodes],
      sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links)))

def main():
    parser=argparse.ArgumentParser()
    for k in ['source','inputs','output']:parser.add_argument('--'+k,type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    data=json.loads(args.inputs.read_text());source=root/'Trackmania2020_assets.blend';sourcehash=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    targets=['TM_PlatformDirt_DecoHill_asset','TM_PlatformDirt_DecoHill2_asset','TM_GlassWaterWall_asset','TM_Water_asset']+['TM_'+e+'_Water_asset' for e in ['BlueBay','GreenCoast','RedIsland','WhiteShore']]
    assert not any(m.get('tm_shader_fidelity_revision') for m in bpy.data.materials),'Already applied; use the recorded baseline.'
    assets={a.bl_rna.identifier+':'+a.name:a for coll in [bpy.data.materials,bpy.data.worlds,bpy.data.node_groups] for a in coll if a.asset_data}
    before={k:dict(identity=identity(a),graph=graph(a)) for k,a in assets.items()}
    # Resolve before changing the blend's directory, including old relative paths.
    for image in bpy.data.images:
        if image.source=='FILE' and image.filepath:image.filepath=bpy.path.abspath(image.filepath)
    support=[]
    def support_image(path,relative):
        dst=out/'Textures/PreviewSupport'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
        support.append(dict(path=dst.relative_to(out).as_posix(),sha256=sha(dst)))
        return bpy.data.images.load(str(dst),check_existing=False)
    def image_loader(record):
        def load(slot):
            desc=record['slots'][slot];filename=Path(desc['image'].replace('\\','/')).name
            path=root/'Textures/Stadium'/filename;assert path.is_file(),path
            im=bpy.data.images.load(str(path),check_existing=True)
            im.colorspace_settings.name='sRGB' if desc['usage']=='Color' else 'Non-Color'
            return im
        return load
    report=dict(revision=REVISION,source_sha256=sourcehash,decohill=[],water=[],waterwall=[])
    for name in targets[:2]:
        record=data['materials'][name];report['decohill'].append(decohill(bpy,bpy.data.materials[name],record,image_loader(record)))
    for env,settings in data['water'].items():
        name='TM_Water_asset' if env=='Stadium' else 'TM_'+env+'_Water_asset'
        image=support_image(Path(settings['fog']),Path('Water')/env/Path(settings['fog']).name)
        # These inputs supply RGB lookup data. Several native DDS files have
        # an all-zero unused alpha plane; do not premultiply their RGB by it.
        image.alpha_mode='NONE'
        report['water'].append(water(bpy,bpy.data.materials[name],env,image,settings))
    # Resolve the source Fresnel image through the native support inventory.
    existing=next((root/'Textures/_Native/SourceTextures').rglob('InvFresnelPC3.tga'))
    fresnel=support_image(existing,Path('WaterWall/InvFresnelPC3.tga'))
    record=data['materials']['TM_GlassWaterWall_asset']
    report['waterwall'].append(waterwall(bpy,bpy.data.materials['TM_GlassWaterWall_asset'],record,image_loader(record),fresnel))
    for k,a in assets.items():
        assert identity(a)==before[k]['identity'],('identity/export changed',k)
        if not (k.startswith('Material:') and a.name in targets):assert graph(a)==before[k]['graph'],('unrelated asset graph changed',k)
    assert len([m for m in bpy.data.materials if m.asset_data])==1119
    assert not any('tm_customization' in k for m in bpy.data.materials for k in m.keys())
    assert sha(source)==sourcehash,'Source changed during staging'
    for image in bpy.data.images:
        if image.source=='FILE' and image.filepath and not image.packed_file:assert Path(bpy.path.abspath(image.filepath)).is_file(),image.filepath
    # A full manifest makes reopened identity checks independent of process state.
    (out/'baseline.json').write_text(json.dumps(before,indent=2))
    report.update(targets=targets,support_files=support,asset_identities_preserved=True,unrelated_asset_graphs_preserved=True,
      counts=dict(materials=1119,worlds=sum(bool(w.asset_data) for w in bpy.data.worlds),source_groups=sum(bool(g.asset_data) for g in bpy.data.node_groups)))
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Trackmania2020_assets.blend'),compress=True,relative_remap=False)
    report['staged_sha256']=sha(out/'Trackmania2020_assets.blend');(out/'build-report.json').write_text(json.dumps(report,indent=2))
    print('SHADER_FIDELITY_STAGED',len(targets),flush=True);bpy.ops.wm.quit_blender()

if __name__=='__main__':main()
