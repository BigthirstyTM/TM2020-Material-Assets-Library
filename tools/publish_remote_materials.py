"""Resume-safe publication of the complete remote Materials Only collection."""
import argparse,concurrent.futures,datetime,hashlib,json,msvcrt,os,re,shutil,subprocess,sys,threading,time,urllib.request
from pathlib import Path
p=argparse.ArgumentParser()
for k in ['workspace','state','blender','git']:p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();base=a.workspace.resolve();out=a.state.resolve();plan=json.loads((out/'plan.json').read_text());repo=plan['repo'];tag=plan['tag'];gh_exe=base/'.tools/gh/bin/gh.exe'
guard=(out/'publication.lock').open('a+b');guard.write(b'0');guard.flush();guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
mutex=threading.Lock();state=dict(pid=os.getpid(),phase='validating',uploaded=[])
def save(**kw):
 with mutex:
  state.update(kw);state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();temp=out/'publication-status.tmp';temp.write_text(json.dumps(state,indent=2));temp.replace(out/'publication-status.json')
def allowed():assert not (out/'PAUSED-BY-USER.json').exists(),'Publication paused by user'
def gh(*args):
 allowed();r=subprocess.run([str(gh_exe),*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if r.returncode:raise RuntimeError(r.stderr.strip())
 return r.stdout
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def release():
 records=json.loads(gh('api',f'repos/{repo}/releases?per_page=100'));return next((x for x in records if x['tag_name']==tag),None)
def remote_assets(release_id):
 result={};page=1
 while True:
  batch=json.loads(gh('api',f'repos/{repo}/releases/{release_id}/assets?per_page=100&page={page}'))
  result.update({x['name']:x for x in batch})
  if len(batch)<100:return result
  page+=1
def git(*args,cwd):return subprocess.check_output([str(a.git.resolve()),*map(str,args)],cwd=cwd,text=True,stderr=subprocess.STDOUT)
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'TM2020-Materials-Extension-Verification'})
 with urllib.request.urlopen(req,timeout=60) as response:return response.read()
def blender(name,args,factory=False):
 profile=out/'public-verification-profile';profile.mkdir(exist_ok=True);env=os.environ.copy()
 for key,folder in [('BLENDER_USER_CONFIG','config'),('BLENDER_USER_EXTENSIONS','extensions'),('BLENDER_USER_DATAFILES','datafiles'),('BLENDER_USER_SCRIPTS','scripts')]:
  d=profile/folder;d.mkdir(exist_ok=True);env[key]=str(d)
 cmd=[str(a.blender.resolve()),'-b','-t','2','--online-mode']+(['--factory-startup'] if factory else [])+list(map(str,args))
 with (out/(name+'.log')).open('w') as log:subprocess.run(cmd,cwd=profile,env=env,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=1200,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
try:
 save();files={p.name:p for p in (out/'assets').iterdir() if p.is_file()};assert len(files)==plan['file_count']+2,len(files)
 build=json.loads((Path(plan['source_export'])/'build-report.json').read_text());assert sha(Path(build['source']))==plan['source_sha256']
 local=json.loads((out/'local-verification.json').read_text());assert local['materials']==825 and local['native_drop_url_verified']
 digests={name:sha(path) for name,path in files.items()}
 remote=release()
 if remote is None:
  gh('release','create',tag,'--repo',repo,'--target','main','--draft','--latest=false','--title',plan['title'],'--notes-file',out/'release-notes.md');remote=release()
 assert remote is not None;release_id=remote['id'];existing=remote_assets(release_id);(out/'release-before.json').write_text(json.dumps(remote))
 # Retain older content-addressed binaries for clients with a cached listing.
 # Later material updates append just new binaries and reuse matching files.
 for extra in set(existing)-set(files):
  assert re.fullmatch(r'(?:mat-[0-9a-f]{24}|bundle-[0-9]{4})\.[0-9a-f]{16}\.blend',extra),('Unrelated file on production release',extra)
 jobs=[(name,path) for name,path in files.items() if not (name in existing and existing[name]['state']=='uploaded' and existing[name].get('digest')=='sha256:'+digests[name] and existing[name]['size']==path.stat().st_size)]
 save(phase='uploading',pending_files=len(jobs),total_files=len(files),total_bytes=sum(p.stat().st_size for _,p in jobs),release_id=release_id)
 def upload(job):
  name,path=job
  for attempt in range(3):
   allowed()
   try:gh('release','upload',tag,path,'--repo',repo,'--clobber');break
   except RuntimeError:
    # A completed upload can outlive an interrupted gh response. Inspect only
    # this file before retrying; never replace verified files unnecessarily.
    candidates=remote_assets(release_id);found=candidates.get(name)
    if found and found['state']=='uploaded' and found.get('digest')=='sha256:'+digests[name]:break
    if attempt==2:raise
  with mutex:state['uploaded'].append(name)
  save();print('REMOTE_FILE_UPLOADED',len(state['uploaded']),len(jobs),name,flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for future in concurrent.futures.as_completed([pool.submit(upload,j) for j in sorted(jobs,key=lambda x:x[1].stat().st_size)]):future.result()
 assets=remote_assets(release_id);assert set(files)<=set(assets)
 for name,path in files.items():assert assets[name]['state']=='uploaded' and assets[name].get('digest')=='sha256:'+digests[name] and assets[name]['size']==path.stat().st_size,name
 save(phase='publishing-release');allowed();gh('release','edit',tag,'--repo',repo,'--draft=false','--latest=false','--title',plan['title'],'--notes-file',out/'release-notes.md')
 assets=remote_assets(release_id);checkout=out/'pages-checkout'
 if not (checkout/'.git').exists():git('clone','--single-branch','--branch',plan['pages_branch'],'https://github.com/'+repo+'.git',checkout,cwd=out)
 else:git('pull','--ff-only','origin',plan['pages_branch'],cwd=checkout)
 for key in ['user.name','user.email']:git('config',key,git('config',key,cwd=base/'TM2020-Material-Assets-Library').strip(),cwd=checkout)
 # Preserve the original pilot site and endpoint; the root page now offers the
 # production extension. New production files live under a separate URL.
 pilot=checkout/'pilot/index.html'
 if not pilot.exists():
  pilot.parent.mkdir(exist_ok=True);pilot_html=(checkout/'index.html').read_text(encoding='utf-8');pilot.write_text(pilot_html.replace('<head>','<head><base href="'+plan['pages_url']+'">',1),encoding='utf-8')
 shutil.copytree(out/'site',checkout,dirs_exist_ok=True);git('add','.',cwd=checkout)
 if git('status','--porcelain',cwd=checkout).strip():git('commit','-m','Publish full Materials Library extension for Blender 5.3',cwd=checkout)
 allowed();save(phase='publishing-pages');git('push','origin',plan['pages_branch'],cwd=checkout)
 expected=(out/'site/remote/tm2020-materials/_asset-library-meta.json').read_bytes();save(phase='waiting-for-pages')
 for attempt in range(60):
  allowed()
  try:
   if get(plan['library_url']+'_asset-library-meta.json?verify=production100')==expected:break
  except Exception:pass
  time.sleep(10)
 else:raise RuntimeError('New production Pages listing did not appear')
 save(phase='verifying-public-site');site_files=[p for p in (out/'site').rglob('*') if p.is_file() and p.name not in {'.nojekyll','.gitattributes'}];site_hashes={}
 def check_site(path):
  rel=path.relative_to(out/'site').as_posix();data=get(plan['pages_url']+rel+'?verify=production100');assert data==path.read_bytes(),rel;return rel,hashlib.sha256(data).hexdigest()
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for rel,digest in pool.map(check_site,site_files):site_hashes[rel]=digest
 save(phase='verifying-native-install')
 # A remote repository install is the same download/manifest path used after
 # Blender's native drag/drop prompts. No current user preferences are touched.
 blender('public-repo-add',['--command','extension','repo-add','--clear-all','--name','Trackmania Materials','--directory',out/'public-verification-profile/repository','--url',plan['repository_url'],'trackmania_materials_test'],factory=True)
 blender('public-extension-install',['--command','extension','install','--sync','--enable',plan['extension_id']])
 blender('public-registration',['--python-exit-code','1','--python',out/'verify_registration.py'])
 blender('public-native-listing',['--command','asset_listing','download',plan['library_url']])
 cache=out/'public-verification-profile/_asset_download_location/_v1';index=json.loads((cache/'asset-index.json').read_text());assert index['asset_count']==825 and index['file_count']==plan['file_count']
 listing=[]
 for entry in index['pages']:
  rel=entry['url'];page_path=out/'public-verification-profile/_asset_download_location'/rel;page=json.loads(page_path.read_text());listing.extend(page['assets']);assert page_path.read_bytes()==(out/'site/remote/tm2020-materials'/rel).read_bytes()
 assert len(listing)==825 and {x['name'] for x in listing}==set(plan['materials']);assert not any('Preview only' in c['path'] for c in index['catalogs'])
 selected=[]
 for name in ['TM_CustomBricks_asset','TM_Water_asset','TM_PlatformDirt_DecoHill_asset','TM_RedIsland_DetailsToDirt_asset']:
  row=next(x for x in build['materials'] if x['name']==name);payload=next(x for x in plan['assets'] if x['path']==row['path']);asset=assets[payload['name']];data=get(asset['browser_download_url']);assert hashlib.sha256(data).hexdigest()==row['sha256'];dest=out/'public-verification-profile'/Path(row['path']).name;dest.write_bytes(data);selected.append(dict(name=name,path=str(dest),id=row['id']))
 (out/'selected-public-materials.json').write_text(json.dumps(selected));blender('public-material-append',['--python-exit-code','1','--python',out/'verify_downloaded_materials.py'],factory=True)
 assert sha(Path(build['source']))==plan['source_sha256']
 proof=dict(phase='complete',revision=plan['source_revision'],release_url=release()['html_url'],pages_url=plan['pages_url'],library_url=plan['library_url'],extension_url=assets[plan['extension_name']]['browser_download_url'],repository_url=plan['repository_url'],drag_url=plan['drag_url'],materials=825,preview_only=0,materiallib_included=False,all_server_assets_verified=digests,site_files=site_hashes,isolated_repository_install_verified=True,native_listing_825_verified=True,selected_public_materials_appended=4,interactive_drag_drop_tested=False,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 (out/'public-verification.json').write_text(json.dumps(proof,indent=2));(out/'completion.json').write_text(json.dumps(proof,indent=2));save(phase='complete');print('FULL_REMOTE_MATERIALS_EXTENSION_PUBLICLY_VERIFIED',flush=True)
except Exception as error:save(phase='failed',error=repr(error));raise
