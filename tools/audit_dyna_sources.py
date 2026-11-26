"""Audit Dyna names without inferring animation or exportability from the suffix."""
import argparse, hashlib, json
from pathlib import Path

def key(path):
    return path.replace('\\', '/').lower().replace(':data:/projects/', '')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inventory',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); index={}
    for path in a.inventory:
        for row in json.loads(path.read_text())['rows']:
            index.setdefault(key(row['path']),row)
    source=Path(__file__).resolve().parents[1]/'data/source-materials.json'
    materials=json.loads(source.read_text())['materials']
    names={m['name'] for m in materials if 'Dyna' in m['name']}
    names.update('TM_'+n+'_asset' for n in ['SpeedometerLight','WarpDetails','WarpDetails_WithLightmap','WarpLight','WarpLightRay'])
    rows=[]
    for m in materials:
        if m['name'] not in names:continue
        root=key(m['native_link'])+'.material.gbx'
        row=index.get(root);chain=[];seen=set()
        def visit(r):
            k=key(r['path'])
            if k in seen:return
            seen.add(k);chain.append(r)
            links=list(r.get('refs',[]));shader=r.get('details',{}).get('shader')
            if shader:links.append(shader)
            for link in links:
                lk=key(link)
                candidates=[lk, key(str(Path(r['path']).parent.parent))+ '/'+lk]
                for candidate in candidates:
                    child=index.get(candidate)
                    if child and candidate.endswith(('.material.gbx','.shader.gbx')):
                        visit(child);break
        if row:visit(row)
        rows.append(dict(name=m['name'],native_link=m['native_link'],source_found=bool(row),
          source=row,chain=chain,classification='Engine template: runtime inputs not reproduced' if 'Experimental_' in m['name'] else 'Concrete texture-backed material'))
    byname={r['name']:r for r in rows};equivalent=[]
    for left,right in [('SpeedometerLight','SpeedometerLight_Dyna'),('WarpDetails_Dyna','WarpDetails_WithLightmap')]:
        l=byname['TM_'+left+'_asset']['source'];r=byname['TM_'+right+'_asset']['source']
        equivalent.append(dict(left=left,right=right,parsed_details_equal=l['details']==r['details'],
          payload_hashes_equal=l.get('sha256')==r.get('sha256'),note='Equal parsed settings do not establish equal unparsed flags or engine routing.'))
    out=dict(inventory_hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in a.inventory},
      dyna_count=sum('Dyna' in r['name'] for r in rows),materials=rows,equivalence=equivalent,
      game_started=False,game_render_verified=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2))
    print('DYNA_SOURCE_AUDIT',out['dyna_count'],len(rows),equivalent)

if __name__=='__main__':main()
