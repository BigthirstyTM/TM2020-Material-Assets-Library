"""Resolve actual ancestor references, never guessed PC/LM shader names."""
import argparse,json,hashlib
from pathlib import Path
parser=argparse.ArgumentParser()
for key in ['native_workspace','audit','snapshot','library','output']:parser.add_argument('--'+key.replace('_','-'),type=Path,required=True)
args=parser.parse_args()
OLD=args.native_workspace.resolve();OUT=args.output.resolve();OUT.parent.mkdir(parents=True,exist_ok=True)

def canon(p):
 p=(p or '').replace('\\','/').lower().replace(':data:/projects/','')
 for env in ['stadium','bluebay','greencoast','redisland','whiteshore']:p=p.replace(env+'/'+env+'/',env+'/')
 return p
ix={}
for f in ['downloads/strict-native-data/resources.json','logs/v6/native-structures/resources.json','logs/experimental/resources/resources.json']:
 for r in json.loads((OLD/f).read_text(encoding='utf-8-sig'))['rows']:
  key=canon(r['path'])
  if key not in ix or len(json.dumps(r['details']))>len(json.dumps(ix[key]['details'])):ix[key]=r
def resolve(path,seen=()):
 key=canon(path)
 if key in seen or key not in ix:return None,list(seen)+[key]
 row=ix[key];chain=list(seen)+[key]
 if row['details'].get('kind')=='shader':return row,chain
 direct=row['details'].get('shader')
 if direct:return resolve(direct,chain)
 refs=[r for r in row.get('refs') or [] if r.lower().endswith(('.shader.gbx','.material.gbx'))]
 candidates=[]
 for ref in refs:
  ref=canon(ref)
  options=[ref,canon(str(Path(row['path']).parent.parent/ref))]
  matches=[v for v in options if v in ix]
  if len(set(matches))==1:candidates.append(matches[0])
 if len(set(candidates))==1:return resolve(candidates[0],chain)
 return None,chain
audit=json.loads(args.audit.read_text())['materials']
snap=json.loads(args.snapshot.read_text());props={r['name']:r['properties'] for r in snap['materials']}
coverage=[];targets=[];deferred=[];conflicts=[]
for row in audit:
 if not row['native_material']:continue
 desc,chain=resolve(row['native_material'])
 if not desc:continue
 native=ix[canon(row['native_material'])]['details'];slots={s['name']:s['file'] for s in desc['details'].get('addresses',[])}
 for ancestor in reversed(chain[:-1]):slots.update({s['name']:s['file'] for s in ix[ancestor]['details'].get('slots') or []})
 detailed={}
 for role,ref in slots.items():
  d=ix.get(canon(ref),{}).get('details',{})
  detailed[role]=dict(resource=ref,**{k:d.get(k) for k in ['image','usage','scale','translation','rotation']})
 link=dict(name=row['name'],source=row['native_material'],shader=desc['path'],chain=chain,newly_resolved=not bool(row['shader']),previous_shader=row['shader'])
 if row['shader'] and canon(row['shader'])!=canon(desc['path']):
  conflicts.append(link);continue
 coverage.append(link)
 shader=canon(desc['path']);eligible=('pypxz_hue' in shader or 'pypxztdiffspecnorm_pyx2hx2' in shader or 'pypxzdiff_spec_norm pc3' in shader)
 required=['PyBaseColor','PyRoughMetal','PyNormal','PxzBaseColor','PxzRoughMetal','PxzNormal']
 if eligible and all(detailed.get(k,{}).get('image') for k in required):
  assert all(detailed[k]['usage'] in ['36','37'] for k in ['PyRoughMetal','PxzRoughMetal'])
  if not all((detailed[k].get('rotation') or 0)==0 and min(detailed[k]['scale'])>0 for k in required):
   deferred.append(dict(name=row['name'],reason='Rotated/negative bitmap frame requires separate source-basis adapter.'));continue
  if detailed.get('TBaseColor',{}).get('image') is None and detailed.get('TBaseColorOp',{}).get('image'):detailed['TBaseColor']=detailed.pop('TBaseColorOp')
  targets.append(dict(name=row['name'],source=row['native_material'],shader=shader,slots=detailed,native_parameters=json.loads(props[row['name']].get('tm_native_parameters','{}'))))
source=args.library
payload=dict(revision='2026.11.23-projection-sources-1',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),materials=targets,coverage=coverage,deferred=deferred,conflicts=conflicts,
 limitations=['Array per-layer transform fields require further semantic decoding; array graphs are not rebuilt using array-wide unit-scale guesses.','Five legacy screen aliases remain unresolved; native export links are retained.','Existing angular lookup interpolation is retained and remains approximate.'])
OUT.write_text(json.dumps(payload,indent=2))
print('PROJECTED_TARGETS',len(targets),'EXACT_CHAINS',len(coverage),'NEW',sum(x['newly_resolved'] for x in coverage))
