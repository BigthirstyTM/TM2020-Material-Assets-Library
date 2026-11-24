"""Build, check and test-install both complete editions with restart receipts."""
import argparse,datetime,hashlib,json,msvcrt,os,subprocess,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];REV='2026.11.24-thumbnail-styles-2'
p=argparse.ArgumentParser()
for key in ['workspace','installation','staging','output','state','previous','blender']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();BASE=a.workspace.resolve();OUT=a.state.resolve();STAGE=a.staging.resolve();DIST=a.output.resolve();OUT.mkdir(exist_ok=True,parents=True)
receipt=json.loads(a.installation.read_text());assert receipt['revision']==REV
SOURCE=Path(receipt['installed']).parent
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(SOURCE/'Trackmania2020_assets.blend')==receipt['sha256']
guard=(OUT/'packaging-worker.lock').open('a+b');guard.seek(0);guard.write(b'0');guard.flush();guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
def signature():
 files=[REPO/'README.md',REPO/'data/source-materials.json']
 for folder in ['docs','tools','installer']:
  files.extend(p for p in (REPO/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 return hashlib.sha256(json.dumps([(p.relative_to(REPO).as_posix(),sha(p)) for p in sorted(files)]).encode()).hexdigest()
sig=signature();state_path=OUT/'packaging-status.json';state=json.loads(state_path.read_text()) if state_path.exists() else dict(revision=REV,completed=[],recipe_sha256=sig,source_sha256=receipt['sha256'])
assert state['revision']==REV and state['recipe_sha256']==sig and state['source_sha256']==receipt['sha256'],'Inputs changed; review before resuming.'
def save(**changes):
 state.update(changes);state['pid']=os.getpid();state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();state_path.write_text(json.dumps(state,indent=2))
def step(name,cmd):
 if name in state['completed']:print('ALREADY_COMPLETED',name,flush=True);return
 save(phase=name)
 with (OUT/(name+'.log')).open('w') as log:subprocess.run([str(x) for x in cmd],cwd=BASE,stdout=log,stderr=subprocess.STDOUT,check=True,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 state['completed'].append(name);save();print('PACKAGE_STEP_COMPLETE',name,flush=True)
def blend(script,*args):return [a.blender,'-b','--factory-startup','-t','2','--python-exit-code','1','--python',REPO/'tools'/script,'--',*args]
try:
 step('export-previews',blend('export_asset_previews.py','--source',SOURCE/'Trackmania2020_assets.blend','--output',OUT/'release-previews'))
 step('portable-build',blend('build_library.py','--source',SOURCE/'Trackmania2020_assets.blend','--inventory',REPO/'data/source-materials.json','--output',STAGE))
 step('prepare-payloads',[sys.executable,REPO/'tools/prepare_payloads.py','--staging',STAGE,'--source',SOURCE,'--previews',OUT/'release-previews','--blender',a.blender,'--content-revision',REV])
 step('refresh-examples',blend('refresh_release_examples.py','--staging',STAGE,'--source',SOURCE,'--previews',OUT/'release-previews'))
 step('edition-verification',blend('verify_release_surface_editions.py','--staging',STAGE,'--source',SOURCE,'--inputs',REPO/'tools/data/concrete-shader-inputs.json'))
 expected_previews=json.loads((OUT/'release-previews/source-preview-manifest.json').read_text())
 for edition in ['materials-only','complete']:
  root=STAGE/edition;rows=json.loads((root/'materials.json').read_text());ids={r['id'] for r in rows}
  assert all(sha(root/'Catalogue/previews'/(r['id']+'.png'))==r['sha256'] for r in expected_previews['materials'] if r['id'] in ids)
  metadata=json.loads((root/'library.json').read_text());assert metadata['content_revision']==REV
 step('package-zips',[sys.executable,REPO/'tools/package_releases.py','--staging',STAGE,'--output',DIST,'--previous',a.previous])
 for edition in ['materials-only','complete']:
  # Keep relocated test paths below Windows MAX_PATH. The normal user install
  # is shorter than this workspace; a deeply nested test root can fail even
  # when all extracted bytes and the production destination are valid.
  dest=OUT/'installed'/edition
  step(edition+'-installer',['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',DIST/edition/'Install-Library.ps1','-Edition',edition,'-PackageDirectory',DIST/edition,'-Destination',dest,'-SkipConfiguration'])
  step(edition+'-installer-verification',blend('verify_library.py','--library',dest/'Trackmania2020_assets.blend','--report',OUT/(edition+'-installer-verification.json')))
  metadata=json.loads((dest/'library.json').read_text());assert metadata['content_revision']==REV
  assert sha(dest/'Trackmania2020_assets.blend')==sha(STAGE/edition/'Trackmania2020_assets.blend')
  manifest=json.loads((DIST/edition/'release.json').read_text());assert len(manifest['archives'])==2 and len(list((DIST/edition).iterdir()))==6
 assert signature()==sig and sha(SOURCE/'Trackmania2020_assets.blend')==receipt['sha256'],'Source changed during packaging.'
 save(phase='complete',dist=str(DIST),staging=str(STAGE));print('BOTH_CURRENT_PACKAGES_AND_INSTALLERS_VERIFIED',flush=True)
except Exception as error:save(phase='failed',error=repr(error));raise
