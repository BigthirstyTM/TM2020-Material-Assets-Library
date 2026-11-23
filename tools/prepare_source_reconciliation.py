"""Reconcile descriptor dependencies and select conservative offline projection fixes."""
import argparse,json,hashlib,collections
from pathlib import Path
parser=argparse.ArgumentParser()
for key in ['native-workspace','prior-inputs','audit','library','output']:parser.add_argument('--'+key,type=Path,required=True)
args=parser.parse_args()
OLD=args.native_workspace.resolve();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
def canon(p):
 p=(p or '').replace('\\','/').lower().replace(':data:/projects/','')
 for env in ['stadium','bluebay','greencoast','redisland','whiteshore']:p=p.replace(env+'/'+env+'/',env+'/')
 return p
ix={};versions=collections.defaultdict(list)
for f in ['downloads/strict-native-data/resources.json','logs/v6/native-structures/resources.json','logs/experimental/resources/resources.json']:
 for r in json.loads((OLD/f).read_text(encoding='utf-8-sig'))['rows']:
  key=canon(r['path']);versions[key].append(dict(inventory=f,sha256=r.get('sha256')))
  if key not in ix or len(json.dumps(r['details']))>len(json.dumps(ix[key]['details'])):ix[key]=r
def shader_edges(key):
 return [canon(r) for r in ix.get(key,{}).get('refs',[]) if r.lower().endswith('.shader.gbx')]
def route(root,target):
 queue=[(root,[root])];seen=set()
 while queue:
  k,path=queue.pop(0)
  if k==target:return path
  if k in seen:continue
  seen.add(k);queue.extend((ref,path+[ref]) for ref in shader_edges(k))
 return None
inputs=json.loads(args.prior_inputs.read_text());results=[]
for r in inputs['conflicts']:
 root=canon(r['shader']);previous=canon(r['previous_shader']);path=route(root,previous)
 back=route(previous,root)
 common=set(shader_edges(root))&set(shader_edges(previous))
 kind='referenced_subshader' if path else 'old_descriptor_references_root' if back else 'sibling_descriptor' if common else 'unrelated_or_unresolved'
 results.append(dict(**r,classification=kind,dependency_path=path,reverse_path=back,common_references=sorted(common),root_sha256=ix[root].get('sha256'),previous_sha256=ix.get(previous,{}).get('sha256'),root_versions=versions[root]))
(OUT/'conflicts.json').write_text(json.dumps(results,indent=2))
print('CONFLICTS',dict(collections.Counter(r['classification'] for r in results)))
for r in results:
 if r['classification']!='referenced_subshader':print(r['name'],r['classification'])

root=args.library.resolve()
audit=json.loads(args.audit.read_text())['materials']
conflicts=results
base=inputs
materials=[];deferred=[];matrix_evidence=[]
for r in audit:
 if not r.get('shader') or 'pypxz_ids' not in r['shader'].lower() or 'Experimental' in r['name']:continue
 native=ix[canon(r['native_material'])];env=native['path'].split('/')[0]
 sel=next(x['fields'] for x in native['details']['chunks'] if x['id']==0x0903A015)
 array=ix[canon(env+'/Media/Texture Array/Image Array/TerrainLayers_DNRM.ImageArray.Gbx')]
 layers={v['U01']:v for v in array['details']['layers']};py=layers[sel['U03']];side=layers[sel['U02']]
 reasons=[]
 for label,v in [('top',py),('side',side)]:
  if any(v['U'+str(i).zfill(2)]!=0 for i in [4,5,8,9,10]):reasons.append(label+': nonzero rotation/offset fields require separate matrix/basis reconstruction')
  if (v['U02'],v['U03'])!=(v['U06'],v['U07']):reasons.append(label+': distinct top/side dimension fields remain outside the reviewed equal-dimension subset')
  if min(v['U02'],v['U03'],v['U06'],v['U07'])<=0:reasons.append(label+': nonpositive dimensions')
 macro=None
 if sel['U04']:
  ma=ix[canon(env+'/Media/Texture Array/Image Array/TerrainLayers_X2.ImageArray.Gbx')]
  macro=next(v for v in ma['details']['layers'] if v['U01']==sel['U04'])
  if any(macro['U'+str(i).zfill(2)]!=0 for i in [4,5,8,9,10]) or min(macro['U02'],macro['U03'])<=0:reasons.append('macro: nonzero rotation/offset or signed scale')
 if sel['U05']:reasons.append('height-array matrix packing not reconstructed')
 if reasons:
  deferred.append(dict(name=r['name'],reasons=reasons,selectors=sel,top=py,side=side));continue
 slots={}
 for prefix,selector,v in [('Py',sel['U03'],py),('Pxz',sel['U02'],side)]:
  for role,suffix,usage in [('BaseColor','D','Color'),('RoughMetal','R','37'),('Normal','N','31')]:
   filename=selector+'_'+suffix+'.dds';path=root/'Textures'/env/filename;assert path.is_file(),path
   slots[prefix+role]=dict(resource=array['path'],image='Image/'+filename,usage=usage,scale=[1/v['U02'],1/v['U03']],translation=[0,0],rotation=0,array_selector=selector,array_fields=v)
 if macro:
  filename=sel['U04']+'_X2.dds';assert (root/'Textures'/env/filename).is_file()
  slots['PyX2']=dict(resource=ma['path'],image='Image/'+filename,usage='Color',scale=[1/macro['U02'],1/macro['U03']],translation=[0,0],rotation=0,array_selector=sel['U04'],array_fields=macro)
 materials.append(dict(name=r['name'],source=native['path'],shader=r['shader'],slots=slots,array_angles=dict(top=[py['U11'],py['U12']],side=[side['U13'],side['U14']]),selectors=sel,family='reviewed equal-dimension unrotated array subset'))
lake=next(r for r in audit if r['name']=='TM_RedIsland_LakeBottom_asset');n=ix[canon(lake['native_material'])];link=next(r for r in base['coverage'] if r['name']==lake['name']);shader=ix[canon(link['shader'])]
refs={v['name']:v['file'] for v in shader['details']['addresses']};refs.update({v['name']:v['file'] for v in n['details']['slots']});slots={}
for role,ref in refs.items():
 d=ix.get(canon(ref),{}).get('details',{})
 slots[role]=dict(resource=ref,**{k:d.get(k) for k in ['image','usage','scale','translation','rotation']})
for key in ['PyNormal','PxzNormal']:
 assert slots[key]['rotation']==0 and min(slots[key]['scale'])>0,'A rotated normal basis is not reviewed here'
materials.append(dict(name=lake['name'],source=n['path'],shader=link['shader'],slots=slots,family='independent rotated colour bitmap; unrotated normal frames'))
payload=dict(revision='2026.11.23-source-reconciliation-1',source_sha256=hashlib.file_digest((root/'Trackmania2020_assets.blend').open('rb'),'sha256').hexdigest(),materials=materials,coverage=conflicts,deferred_arrays=deferred,
 limitations=['Native runtime array buffers are not captured; only positive, equal-dimension, zero-rotation/offset rows are adapted. Static material selectors are retained; no runtime array ID overrides are inferred.','Mapped Blender frames and the standard bitmap rotation convention remain preview adapters.','Five legacy screen aliases remain unresolved; do not substitute nearby aspect ratios.'])
(OUT/'inputs.json').write_text(json.dumps(payload,indent=2))
print('GRAPH_TARGETS',len(materials),'SOURCE_ROOTS',len(conflicts),'DEFERRED_ARRAYS',len(deferred))
for r in materials:print(r['name'])
