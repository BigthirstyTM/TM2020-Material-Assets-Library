"""Fresh-process preservation and source-parameter checks for the five groups."""
import bpy,argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_dyna_previews import blocks,snapshot
from apply_shader_fidelity import sha
from shader_followup_adapters import REVISION

def verify(source,stage,inputs,out):
 report=json.loads((stage/'build-report.json').read_text());before=json.loads((stage/'baseline.json').read_text());data=json.loads(inputs.read_text(encoding='utf-8'))
 bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);current=blocks();targets=set(report['targets'])
 assert set(before)<=set(current),('Original datablock missing',sorted(set(before)-set(current)))
 for k,old in before.items():
  a=current[k];now=snapshot(a)
  assert now['identity']==old['identity'],('Identity/export/icon changed',k)
  assert now['badges']==old['badges'],('Badges changed',k)
  if a.name not in targets:assert now['graph']==old['graph'] and now['outputs']==old['outputs'],('Unrelated graph changed',k)
 for k,a in current.items():
  if k not in before:assert not a.asset_data,('New public asset unexpectedly introduced',k)
 for name in targets:assert bpy.data.materials[name]['tm_shader_followup_revision']==REVISION
 for r in report['details']['uv']:
  m=bpy.data.materials[r['name']]
  for n in m.node_tree.nodes:
   if n.type in ['UVMAP','NORMAL_MAP']:assert n.uv_map,('UV still implicit',m.name,n.name)
 for r in report['details']['grass']:
  t=bpy.data.materials[r['name']].node_tree
  assert t.nodes['Native GrassX2 modulation'].image
 for r in report['details']['depth']:
  t=bpy.data.materials[r['name']].node_tree
  if 'mode' in r['detail']:continue
  assert 'Dyna SI first crossing' in t.nodes
  for key in ['Meters_Depth','RefractIndex','DoubleRefract']:
   assert abs(t.nodes['Dyna source '+key].outputs[0].default_value-r['detail'][key][0])<1e-5
 for r in report['details']['hue']:
  m=bpy.data.materials[r['name']];t=m.node_tree;root=t.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
  if root.type=='GROUP':assert root.inputs['Enable source colour preview'].default_value==0
  else:assert t.nodes['Enable source colour preview'].outputs[0].default_value==0
 missing=[];count=0
 for im in bpy.data.images:
  if im.source=='FILE' and im.filepath and not im.packed_file:
   count+=1
   if not Path(bpy.path.abspath(im.filepath)).is_file():missing.append(im.filepath)
 assert not missing,missing
 assert sum(bool(m.asset_data) for m in bpy.data.materials)==1119
 proof=dict(revision=REVISION,sha256=sha(source),materials=1119,changed_materials=len(targets),groups={k:len(v) for k,v in report['details'].items()},missing_images=0,images_checked=count,identities_export_icons_badges_preserved=True,unrelated_graphs_preserved=True)
 out.write_text(json.dumps(proof,indent=2));print('SHADER_FOLLOWUP_VERIFIED',proof,flush=True)
 return proof

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ['source','stage','inputs','output']:p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);verify(a.source.resolve(),a.stage.resolve(),a.inputs.resolve(),a.output.resolve())
