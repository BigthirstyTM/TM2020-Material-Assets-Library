"""Reject active material aliases whose native targets are absent from a reviewed PAK index."""
import argparse,json,re
from pathlib import Path

def canonical(path):
 path=path.replace('\\','/').lower().replace(':data:/projects/','').strip('/')
 for name in ['stadium','bluebay','greencoast','redisland','whiteshore']:path=path.replace(name+'/'+name+'/',name+'/')
 return path

def validate(inventory,materiallib,snapshot):
 inventory=json.loads(Path(inventory).read_text())['materials'];snapshot=json.loads(Path(snapshot).read_text());paths=set(snapshot['material_paths']);definitions={};library='';alias=''
 for line in Path(materiallib).read_text(encoding='utf-8-sig').splitlines():
  match=re.match(r'\s*DLibrary\s*\(([^)]+)\)',line)
  if match:library=match[1];alias=''
  match=re.match(r'\s*DMaterial\s*\(([^)]+)\)',line)
  if match:alias=match[1]
  match=re.match(r'\s*DLinkFull\s*\(([^)]+)\)',line)
  if match and alias:
   assert alias not in definitions,('Duplicate alias',alias)
   definitions[alias]=canonical(library+'/'+match[1]+'.Material.Gbx')
 active=[r for r in inventory if not r['preview_only']];checks=[]
 for row in active:
  alias=row['effective']['link'];assert alias and alias in definitions,('Active material has no export definition',row['name'],alias)
  target=definitions[alias];assert target in paths,('Active material points to absent native resource',row['name'],target)
  checks.append(dict(name=row['name'],alias=alias,target=target))
 return dict(materials=len(checks),native_file_existence_verified=True,reviewed_snapshot_utc=snapshot['reviewed_utc'],runtime_tested=False,checks=checks)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ['inventory','materiallib','report']:p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--snapshot',type=Path,default=Path(__file__).resolve().parents[1]/'data/native-material-paths.json')
 a=p.parse_args();proof=validate(a.inventory,a.materiallib,a.snapshot);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(proof,indent=2));print('ACTIVE_NATIVE_LINKS_VERIFIED',proof['materials'])
