"""Cluster material dependencies into small stable, texture-sharing bundles."""
import argparse,heapq,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-mb',type=int,default=512);p.add_argument('--max-materials',type=int,default=32)
a=p.parse_args();audit=json.loads(a.audit.read_text());rows=audit['rows'];weights={p:Path(p).stat().st_size for r in rows for p in r['paths']};limit=a.max_mb*1024*1024
clusters={i:dict(ids={r['id']},paths=set(r['paths'])) for i,r in enumerate(rows)};heap=[];next_id=len(rows)
def size(paths):return sum(weights[p] for p in paths)
def candidate(i,j):
 x,y=clusters[i],clusters[j]
 if len(x['ids'])+len(y['ids'])>a.max_materials:return
 shared=x['paths']&y['paths'];saved=size(shared)
 if saved<128*1024 or size(x['paths']|y['paths'])>limit:return
 heapq.heappush(heap,(-saved,i,j))
for i in clusters:
 for j in range(i):candidate(j,i)
while heap:
 saved,i,j=heapq.heappop(heap)
 if i not in clusters or j not in clusters:continue
 x,y=clusters.pop(i),clusters.pop(j);clusters[next_id]=dict(ids=x['ids']|y['ids'],paths=x['paths']|y['paths'])
 for k in list(clusters):
  if k!=next_id:candidate(k,next_id)
 next_id+=1
# Amortise very small files without turning large independent materials into
# unrelated downloads. The initial map is persisted and reused by the exporter.
small=sorted((k for k,v in clusters.items() if size(v['paths'])<=4*1024*1024),key=lambda k:sorted(clusters[k]['ids']))
bins=[]
for key in small:
 item=clusters.pop(key)
 for b in bins:
  if len(b['ids'])+len(item['ids'])<=a.max_materials and size(b['paths']|item['paths'])<=32*1024*1024:
   b['ids']|=item['ids'];b['paths']|=item['paths'];break
 else:bins.append(item)
groups=list(clusters.values())+bins;groups.sort(key=lambda g:sorted(g['ids']))
names={r['id']:r['name'] for r in rows};bundles=[]
for i,g in enumerate(groups):bundles.append(dict(id=f'bundle-{i+1:04d}',materials=sorted(g['ids']),names=sorted(names[x] for x in g['ids']),raw_texture_bytes=size(g['paths'])))
assert len({m for b in bundles for m in b['materials']})==len(rows)
report=dict(materials=len(rows),bundle_count=len(bundles),max_raw_mb=a.max_mb,max_materials=a.max_materials,individual_raw_bytes=audit['per_material_total_bytes'],bundled_raw_bytes=sum(x['raw_texture_bytes'] for x in bundles),bundles=bundles)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2));print('BUNDLE_PLAN',a.max_mb,'MB',len(bundles),'bundles',round(report['bundled_raw_bytes']/1e9,3),'GB raw vs',round(report['individual_raw_bytes']/1e9,3),flush=True)
