"""Fresh-file checks of root/pass provenance and unchanged earlier source chains."""
import argparse,collections,json,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser()
for key in ['library','inputs','prior-inputs','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);data=json.loads(a.inputs.read_text());prior=json.loads(a.prior_inputs.read_text())
bpy.ops.wm.open_mainfile(filepath=str(a.library.resolve()),load_ui=False)
for r in prior['coverage']+data['coverage']:
 m=bpy.data.materials[r['name']]
 assert m['tm_exact_shader_resource']==r['shader'],r['name']
 assert json.loads(m['tm_exact_shader_chain'])==r['chain'],r['name']
for r in data['coverage']:
 m=bpy.data.materials[r['name']]
 assert m['tm_previous_shader_descriptor']==r['previous_shader']
 assert m['tm_shader_descriptor_relation']==r['classification']
 assert json.loads(m['tm_shader_descriptor_dependency_path'])==r['dependency_path']
 if r['classification']=='referenced_subshader':
  assert r['dependency_path'][0]==r['shader'].lower() and r['dependency_path'][-1]==r['previous_shader'].lower()
 else:assert r['classification']=='sibling_descriptor' and '_nodecal.shader.gbx' in r['shader'].lower()
for r in data['materials']:
 m=bpy.data.materials[r['name']];active=m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
 assert active==m.node_tree.nodes['Deco native layer controls'],r['name']
 assert m['tm_projection_refresh_revision']==data['revision']
 if 'selectors' in r:assert json.loads(m['tm_array_preview_selection'])==r['selectors']
count=sum(bool(m.get('tm_exact_shader_resource')) for m in bpy.data.materials if m.asset_data)
assert count==len(prior['coverage'])+len(data['coverage'])==792
proof=dict(revision=data['revision'],exact_roots=count,earlier_roots_retained=len(prior['coverage']),reconciled= dict(collections.Counter(r['classification'] for r in data['coverage'])),active_graphs=len(data['materials']),game_started=False)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(proof,indent=2));print('RECONCILED_SOURCES_VERIFIED',count,flush=True)
