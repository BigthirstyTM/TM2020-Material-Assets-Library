"""Choose thumbnail proportions from the displayed source image or atlas frame."""
import bpy,struct
from pathlib import Path


def image_dimensions(image):
    # Read encoded headers: querying Image.size decodes every candidate DDS,
    # needlessly allocating gigabytes just to obtain its width and height.
    path=Path(bpy.path.abspath(image.filepath))
    if path.is_file():
        with path.open('rb') as f:data=f.read(32)
        if data[:4]==b'DDS ':
            height,width=struct.unpack_from('<II',data,12);return width,height
        if data[:8]==b'\x89PNG\r\n\x1a\n':return struct.unpack_from('>II',data,16)
        if path.suffix.lower() in ['.tga','.targa'] and len(data)>=18:return struct.unpack_from('<HH',data,12)
    return tuple(image.size)


def aspect_record(material):
    nodes=material.node_tree.nodes if material.node_tree else []
    candidates=[n for n in nodes if n.type=='TEX_IMAGE' and n.image]
    byname={n.name:n for n in candidates};selected=None;reason='procedural square'
    # A manually selected atlas frame is an image region, not the whole sheet.
    atlas=byname.get('tex_I')
    if atlas and atlas.inputs[0].is_linked:
        group=atlas.inputs[0].links[0].from_node
        if group.type=='GROUP' and group.inputs.get('Manual Frame (-1 = timeline)'):
            for n in group.node_tree.nodes:
                if n.type=='VECT_MATH' and n.operation=='MULTIPLY' and n.inputs[0].is_linked:
                    link=n.inputs[0].links[0]
                    if link.from_node.type=='GROUP_INPUT' and link.from_socket.name=='UV' and not n.inputs[1].is_linked:
                        scale=n.inputs[1].default_value
                        if scale[0]>0 and scale[1]>0:
                            encoded_width,encoded_height=image_dimensions(atlas.image);width=encoded_width*scale[0];height=encoded_height*scale[1]
                            return dict(ratio=width/height,width=width,height=height,image=atlas.image.name,reason='active atlas cell',uv_cell=[scale[0],scale[1]])
    if atlas and (material.get('tm_current_preview_type')=='Composed screen' or 'Screen' in material.name):
        selected=atlas;reason='screen image layer (not the square LED/detail layer)'
    if selected is None and material.get('tm_current_preview_type')=='Source texture':
        expected=material.get('tm_asset_preview_source','').replace('\\','/').lower()
        selected=next((n for n in candidates if bpy.path.abspath(n.image.filepath).replace('\\','/').lower()==expected),None)
        if selected:reason='recorded source texture'
    if selected is None:
        selected=byname.get('tex_D') or byname.get('tex_I') or (candidates[0] if candidates else None)
        if selected:reason='primary color image'
    if selected:
        width,height=image_dimensions(selected.image)
        if width<=0 or height<=0:return dict(ratio=1,width=1,height=1,image=selected.image.name,reason='unreadable image dimensions; square fallback')
        return dict(ratio=width/height,width=width,height=height,image=selected.image.name,reason=reason)
    return dict(ratio=1,width=1,height=1,image=None,reason=reason)


def fit_panel(panel,record,footer=False,size=27):
    # The camera renders a square. Reserve the footer without cropping its image.
    available_height=size*(226/256 if footer else 1)
    width=min(size,available_height*record['ratio']);height=width/record['ratio']
    panel.scale=(width/size,height/size,1)
    panel.location=(0,(size-available_height)/2,0)
    return dict(width_pixels=width/size*256,height_pixels=height/size*256,footer_reserved=footer)
