"""Publish only verified immutable files; resume missing uploads and promotions."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import datetime,hashlib,json,msvcrt,os,subprocess,threading,time,urllib.request
from pathlib import Path

import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--revision',default='2026.11.24-thumbnail-styles-2',help='Only publish files with this verified content revision.')
parser.add_argument('--temporary-suffix',default='.thumbnail-styles-refresh',help='Revision-owned suffix for temporary uploads.')
for key in ['workspace','dist','state']:parser.add_argument('--'+key,type=Path,required=True)
parser.add_argument('--obsolete-temporary-asset',action='append',default=[],help='Exact obsolete temporary manifest name, removed only after all new final files verify.')
args=parser.parse_args()
for name in args.obsolete_temporary_asset:
    assert any(name.startswith(prefix+'.') and name.endswith('-refresh') for prefix in ['release.json','SHA256SUMS.txt']) and all(c.isalnum() or c in '.-' for c in name),name
BASE=args.workspace.resolve();DIST=args.dist.resolve();OUT=args.state.resolve();OUT.mkdir(parents=True,exist_ok=True)
GH=BASE/'.tools/gh/bin/gh.exe';REPO='BigthirstyTM/TM2020-Material-Assets-Library';REV=args.revision;SUFFIX=args.temporary_suffix
assert SUFFIX.startswith('.') and SUFFIX.endswith('-refresh') and all(c.isalnum() or c in '.-' for c in SUFFIX)
guard=(OUT/'worker.lock').open('a+b');guard.seek(0);guard.write(b'0');guard.flush();guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
lock=threading.Lock();state=dict(revision=REV,pid=os.getpid(),phase='validating',uploaded=[],editions={})
def status(**changes):
    with lock:
        state.update(changes);state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=OUT/'status.tmp';p.write_text(json.dumps(state,indent=2));p.replace(OUT/'status.json')
def allowed():
    assert not (OUT/'PAUSED-BY-USER.json').exists(),'Publication paused by user'
def gh(*args):return subprocess.check_output([str(GH),*[str(a) for a in args]],text=True,stderr=subprocess.PIPE)
def release(edition):return json.loads(gh('api',f'repos/{REPO}/releases/tags/v1.0.0-{edition}'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def patch(asset,name):gh('api',f'repos/{REPO}/releases/assets/{asset["id"]}','--method','PATCH','-f','name='+name)
def upload(edition,path,digest):
    allowed();assets={a['name']:a for a in release(edition)['assets']};existing=assets.get(path.name)
    if not existing or existing.get('digest')!=digest or existing['state']!='uploaded':
        for attempt in range(3):
            allowed()
            try:gh('release','upload','v1.0.0-'+edition,path,'--repo',REPO,'--clobber');break
            except subprocess.CalledProcessError:
                existing={a['name']:a for a in release(edition)['assets']}.get(path.name)
                if existing and existing.get('digest')==digest and existing['state']=='uploaded':break
                if attempt==2:raise
    with lock:state['uploaded'].append(edition+'/'+path.name)
    status();print('TEMPORARY_UPLOAD_COMPLETE',edition,path.name,flush=True)

try:
    status()
    for edition in ['materials-only','complete']:
        # The verified Materials Only edition may upload while Complete is
        # still packaging. Never inspect/promote an unfinished Complete ZIP.
        while edition=='complete' and json.loads((OUT.parent/'packaging-status.json').read_text())['phase']!='complete':
            allowed();pack=json.loads((OUT.parent/'packaging-status.json').read_text())
            assert pack['phase']!='failed',('Packaging failed',pack)
            status(phase='waiting-for-complete-packages',edition=edition);time.sleep(5)
        allowed();folder=DIST/edition;files={p.name:p for p in folder.iterdir() if p.is_file()}
        manifest=json.loads(files['release.json'].read_text());assert manifest['content_revision']==REV and manifest['archives']
        assert set(files)=={x['name'] for x in manifest['archives']}|{'release.json','SHA256SUMS.txt','Install-Library.ps1','INSTALLATION.md'}
        digests={name:'sha256:'+sha(p) for name,p in files.items()}
        for digest,name in (line.split('  ',1) for line in files['SHA256SUMS.txt'].read_text().splitlines()):assert digests[name]=='sha256:'+digest
        original=release(edition);snapshot=OUT/(edition+'-before.json')
        if not snapshot.exists():snapshot.write_text(json.dumps(original,indent=2))
        temp=OUT/edition;temp.mkdir(exist_ok=True);jobs=[]
        assets={a['name']:a for a in original['assets']}
        for name,path in files.items():
            current=assets.get(name)
            if current and current.get('digest')==digests[name] and current['state']=='uploaded':continue
            staged=temp/(name+SUFFIX)
            if not staged.exists():os.link(path,staged)
            assert sha(staged)==digests[name][7:]
            jobs.append((staged,digests[name]))
        status(phase='uploading',edition=edition,total_bytes=sum(p.stat().st_size for p,d in jobs),pending_files=[p.name for p,d in jobs])
        with ThreadPoolExecutor(max_workers=2) as pool:
            for job in as_completed([pool.submit(upload,edition,p,d) for p,d in jobs]):job.result()
        # Every replacement must exist and have its expected server digest
        # before any public asset is renamed. Existing downloads remain intact.
        assets={a['name']:a for a in release(edition)['assets']}
        for name,path in files.items():
            candidates=[assets.get(name),assets.get(name+SUFFIX)]
            assert any(a and a['state']=='uploaded' and a.get('digest')==digests[name] and a['size']==path.stat().st_size for a in candidates),name
        allowed();status(phase='switching-downloads',edition=edition)
        order=[x['name'] for x in manifest['archives']]+['Install-Library.ps1','INSTALLATION.md','SHA256SUMS.txt','release.json']
        for name in order:
            allowed();assets={a['name']:a for a in release(edition)['assets']};current=assets.get(name)
            if current and current.get('digest')==digests[name]:continue
            replacement=assets[name+SUFFIX];assert replacement.get('digest')==digests[name]
            if current:patch(current,name+'.previous-thumbnail-styles-'+str(current['id']))
            patch(replacement,name)
        final=release(edition);assets={a['name']:a for a in final['assets']}
        assert all(assets[n].get('digest')==digests[n] and assets[n]['state']=='uploaded' for n in files)
        # Delete only obsolete revision-owned assets after all final downloads
        # verify. Any unrelated asset causes review instead of blind deletion.
        for asset in final['assets']:
            name=asset['name']
            if name in files:continue
            assert '.previous-thumbnail-styles-' in name or name.endswith(SUFFIX) or name in args.obsolete_temporary_asset,('Unexpected public asset',name)
            allowed();gh('api',f'repos/{REPO}/releases/assets/{asset["id"]}','--method','DELETE')
        gh('release','edit','v1.0.0-'+edition,'--repo',REPO,'--notes-file',OUT/(edition+'-notes.md'))
        final=release(edition);assert {a['name'] for a in final['assets']}==set(files)
        (OUT/(edition+'-after.json')).write_text(json.dumps(final,indent=2))
        state['editions'][edition]=dict(url=final['html_url'],verified=True,archives=len(manifest['archives']),sizes=[a['bytes'] for a in manifest['archives']]);status(phase='edition-complete',edition=edition)
    gh('release','edit','v1.0.0-materials-only','--repo',REPO,'--latest')
    status(phase='verifying-public-downloads');proof={}
    for edition in ['materials-only','complete']:
        files={p.name:p for p in (DIST/edition).iterdir() if p.is_file()};remote=release(edition);assets={a['name']:a for a in remote['assets']}
        assert set(files)==set(assets)
        for name,path in files.items():assert assets[name].get('digest')=='sha256:'+sha(path) and assets[name]['size']==path.stat().st_size
        downloads={}
        for name in ['release.json','Install-Library.ps1','INSTALLATION.md','SHA256SUMS.txt']:
            allowed();req=urllib.request.Request(assets[name]['browser_download_url'],headers={'User-Agent':'TM2020-Library-Public-Verification'})
            with urllib.request.urlopen(req,timeout=60) as response:data=response.read()
            assert data==files[name].read_bytes();(OUT/(edition+'-public-'+name)).write_bytes(data);downloads[name]=hashlib.sha256(data).hexdigest()
        metadata=json.loads(files['release.json'].read_text());assert metadata['content_revision']==REV
        proof[edition]=dict(url=remote['html_url'],revision=REV,all_digests_verified=True,verified_file_count=len(files),public_downloads=downloads,archives=metadata['archives'])
    (OUT/'public-verification.json').write_text(json.dumps(proof,indent=2));status(phase='complete')
    (OUT/'completion.json').write_text(json.dumps(dict(revision=REV,phase='complete',public_verification=proof),indent=2))
    print('BOTH_CURRENT_RELEASES_PUBLICLY_VERIFIED',flush=True)
except Exception as e:status(phase='failed',error=repr(e));raise
