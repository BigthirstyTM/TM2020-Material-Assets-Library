"""Exact material catalog paths; environment names also occur under HDRI."""
ROOTS={'BlueBay':'02 BlueBay','GreenCoast':'03 GreenCoast','RedIsland':'04 RedIsland','WhiteShore':'05 WhiteShore'}
def material_catalog(name,environment):
    root='Trackmania2020/'+ROOTS[environment]+'/Materials/'
    category='Decals and signs' if 'DecalPaint' in name else 'Other materials' if any(s in name for s in ('StructureInWorld','TrackBorders','TrackWall')) else 'Terrain'
    return root+category

def validate_listing_catalogs(index,assets,inventory):
    by_uuid={uid:c['path'] for c in index['catalogs'] for uid in c['uuids']}
    expected={r['name']:r['catalog'] for r in inventory}
    errors=[]
    for asset in assets:
        path=by_uuid.get(asset['meta']['catalog_id'])
        if asset['id_type']=='MATERIAL':
            if not path or '/06 HDRI World Moods' in path or path!=expected.get(asset['name']):errors.append((asset['name'],path,expected.get(asset['name'])))
        elif asset['id_type']=='WORLD':
            if not path or not path.startswith('Trackmania2020/06 HDRI World Moods/'):errors.append((asset['name'],path,'HDRI World Moods'))
        else:errors.append((asset['name'],path,'Unsupported asset type'))
    assert not errors,('Invalid asset catalog assignments',errors)
    return {'assets_checked':len(assets),'materials_in_hdri':0,'worlds_outside_hdri':0,'inventory_catalogs_match':True}
