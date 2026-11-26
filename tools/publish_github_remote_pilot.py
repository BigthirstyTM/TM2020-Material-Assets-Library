"""Resume-safe publication of the prepared Materials Only GitHub pilot."""
import argparse
import datetime
import hashlib
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

p = argparse.ArgumentParser()
for key in ['workspace', 'state', 'blender', 'git']:
    p.add_argument('--' + key, type=Path, required=True)
a = p.parse_args()
base = a.workspace.resolve()
out = a.state.resolve()
plan = json.loads((out / 'plan.json').read_text())
repo, tag = plan['repo'], plan['tag']
gh_exe = base / '.tools/gh/bin/gh.exe'
guard = (out / 'publication.lock').open('a+b')
guard.write(b'0'); guard.flush(); guard.seek(0)
msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
state = dict(pid=os.getpid(), phase='validating', uploaded=[])


def save(**values):
    state.update(values)
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    temp = out / 'publication-status.tmp'
    temp.write_text(json.dumps(state, indent=2))
    temp.replace(out / 'publication-status.json')


def allowed():
    assert not (out / 'PAUSED-BY-USER.json').exists(), 'Pilot publication paused'
    assert not (base / 'build/thumbnail-release/publication/PAUSED-BY-USER.json').exists(), 'Publication paused'


def gh(*args, data=None):
    allowed()
    result = subprocess.run([str(gh_exe), *map(str, args)],
                            input=json.dumps(data) if data is not None else None,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def optional_api(path):
    try:
        return json.loads(gh('api', path))
    except RuntimeError as error:
        if 'HTTP 404' in str(error):
            return None
        raise


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def release():
    # GitHub's tag endpoint can return 404 for a newly created draft.
    found = optional_api(f'repos/{repo}/releases/tags/{tag}')
    if found is not None:
        return found
    candidates = json.loads(gh('api',f'repos/{repo}/releases?per_page=100'))
    return next((x for x in candidates if x['tag_name']==tag),None)


def git(*args, cwd):
    allowed()
    return subprocess.check_output([str(a.git.resolve()), *map(str, args)],
                                   cwd=cwd, text=True, stderr=subprocess.STDOUT)


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'TM2020-Remote-Pilot-Verification'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def blender_step(name, args, *, factory=False):
    profile = out / 'verification-profile'
    profile.mkdir(exist_ok=True)
    env = os.environ.copy()
    for key, folder in [('BLENDER_USER_CONFIG','config'), ('BLENDER_USER_EXTENSIONS','extensions'),
                        ('BLENDER_USER_DATAFILES','datafiles'), ('BLENDER_USER_SCRIPTS','scripts')]:
        directory = profile / folder
        directory.mkdir(exist_ok=True)
        env[key] = str(directory)
    cmd = [str(a.blender.resolve()), '-b', '-t', '2', '--online-mode']
    if factory:
        cmd.append('--factory-startup')
    with (out / (name + '.log')).open('w') as log:
        subprocess.run(cmd + list(map(str,args)), cwd=profile, env=env, check=True,
                       stdout=log, stderr=subprocess.STDOUT, timeout=240,
                       creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)


try:
    save()
    payloads = {p.name:p for p in (out / 'assets').iterdir() if p.is_file()}
    assert len(payloads) == 13 and plan['excluded_preview_only'] == 1
    digests = {name:sha(path) for name,path in payloads.items()}
    for item in plan['assets']:
        assert digests[item['name']] == item['sha256']
    remote = release()
    if remote is None:
        gh('release', 'create', tag, '--repo', repo, '--target', 'main', '--draft',
           '--prerelease', '--latest=false', '--title', 'Materials Only — Remote Library Pilot 0.1.0',
           '--notes-file', out / 'release-notes.md')
        remote = release()
    assert remote['prerelease'], 'Pilot tag belongs to a non-prerelease'
    (out / 'release-before.json').write_text(json.dumps(remote,indent=2))
    # One pilot upload at a time, alongside the existing independent full-package publisher.
    for name, path in sorted(payloads.items(), key=lambda item:item[1].stat().st_size):
        allowed()
        assets = {x['name']:x for x in release()['assets']}
        existing = assets.get(name)
        if existing and existing['state']=='uploaded' and existing.get('digest')=='sha256:'+digests[name]:
            continue
        save(phase='uploading-pilot-file', file=name, bytes=path.stat().st_size)
        last_error = None
        for attempt in range(3):
            try:
                gh('release','upload',tag,path,'--repo',repo,'--clobber')
                last_error = None
                break
            except RuntimeError as error:
                last_error = error
                candidates = {x['name']:x for x in release()['assets']}
                candidate = candidates.get(name)
                if candidate and candidate['state']=='uploaded' and candidate.get('digest')=='sha256:'+digests[name]:
                    last_error = None
                    break
        if last_error:
            raise last_error
        state['uploaded'].append(name)
        save()
        print('PILOT_FILE_UPLOADED', name, flush=True)
    assets = {x['name']:x for x in release()['assets']}
    assert set(assets)==set(payloads)
    for name,path in payloads.items():
        assert assets[name]['state']=='uploaded' and assets[name].get('digest')=='sha256:'+digests[name]
        assert assets[name]['size']==path.stat().st_size
    save(phase='publishing-pilot-release')
    if release()['draft']:
        gh('release','edit',tag,'--repo',repo,'--draft=false','--prerelease','--latest=false')
    # Draft asset URLs can contain an untagged placeholder; refresh after publishing.
    assets = {x['name']:x for x in release()['assets']}
    checkout = out / 'pages-checkout'
    branch = plan['pages_branch']
    if not (checkout / '.git').exists():
        existing = optional_api(f'repos/{repo}/branches/{branch}')
        if existing:
            git('clone','--single-branch','--branch',branch,'https://github.com/'+repo+'.git',checkout,cwd=out)
        else:
            checkout.mkdir(exist_ok=True)
            git('init','--initial-branch',branch,cwd=checkout)
            git('remote','add','origin','https://github.com/'+repo+'.git',cwd=checkout)
    for key in ['user.name','user.email']:
        configured = git('config',key,cwd=base/'TM2020-Material-Assets-Library').strip()
        git('config',key,configured,cwd=checkout)
    shutil.copytree(out/'site',checkout,dirs_exist_ok=True)
    git('add','.',cwd=checkout)
    if git('status','--porcelain',cwd=checkout).strip():
        git('commit','-m','Publish Materials Only remote-library pilot',cwd=checkout)
    save(phase='publishing-pages-branch')
    git('push','origin',branch,cwd=checkout)
    pages = optional_api(f'repos/{repo}/pages')
    if pages is None:
        pages = json.loads(gh('api',f'repos/{repo}/pages','--method','POST','--input','-',
                          data=dict(source=dict(branch=branch,path='/'))))
    else:
        assert pages.get('source',{}).get('branch')==branch, 'An unrelated Pages source is configured'
    (out/'pages-settings.json').write_text(json.dumps(pages,indent=2))
    save(phase='waiting-for-public-pages')
    expected = (out/'site/remote/materials-only/_asset-library-meta.json').read_bytes()
    last = None
    for attempt in range(60):
        allowed()
        try:
            if get(plan['library_url']+'_asset-library-meta.json?verify=pilot01') == expected:
                break
        except Exception as error:
            last = repr(error)
        time.sleep(20)
    else:
        raise RuntimeError('Pages did not become available: '+str(last))
    save(phase='verifying-public-pilot')
    public_files = {}
    for path in (out/'site').rglob('*'):
        if not path.is_file() or path.name in {'.nojekyll', '.gitattributes'}:
            continue
        relative = path.relative_to(out/'site').as_posix()
        downloaded = get(plan['pages_url']+relative)
        assert downloaded==path.read_bytes(),relative
        public_files[relative] = hashlib.sha256(downloaded).hexdigest()
    extension = out/'assets'/plan['extension_name']
    assert get(assets[extension.name]['browser_download_url'])==extension.read_bytes()
    blender_step('pilot-repo-add',['--command','extension','repo-add','--clear-all',
                 '--name','TM2020 Public Pilot Test','--directory',out/'verification-profile/repository',
                 'tm2020_public_pilot_test'],factory=True)
    blender_step('pilot-extension-install',['--command','extension','install-file','--repo',
                 'tm2020_public_pilot_test','--enable',extension])
    script = out/'verify_public_extension.py'
    script.write_text('''import bpy,json
from pathlib import Path
libs=[x for x in bpy.context.preferences.filepaths.asset_libraries if x.name=='TM2020 Materials Only (Pilot)']
assert len(libs)==1
libs[0].enabled=True
assert libs[0].remote_url=='''+repr(plan['library_url'])+'''
assert libs[0].enabled
bpy.ops.wm.save_userpref()
Path('extension-verification.json').write_text(json.dumps(dict(name=libs[0].name,url=libs[0].remote_url,enabled=True),indent=2))
''')
    blender_step('pilot-extension-verification',['--python-exit-code','1','--python',script])
    blender_step('pilot-native-public-listing',['--command','asset_listing','download',plan['library_url']])
    cache = out/'verification-profile/_asset_download_location/_v1'
    cached_page = json.loads((cache/'assets-00000.json').read_text())
    cached_index = json.loads((cache/'asset-index.json').read_text())
    assert cached_page['asset_count']==12 and len(cached_page['assets'])==12
    assert {x['name'] for x in cached_page['assets']}==set(plan['materials'])
    assert not any('Preview only' in x['path'] for x in cached_index['catalogs'])
    assert (cache/'assets-00000.json').read_bytes()==(out/'site/remote/materials-only/_v1/assets-00000.json').read_bytes()
    candidate = next(item for item in plan['assets'] if item['library_path'].endswith('mat-6e0293a1428e6f9bec7596aa.blend'))
    item = assets[candidate['name']]
    selected = get(item['browser_download_url']+'?hash='+candidate['sha256'])
    assert hashlib.sha256(selected).hexdigest()==candidate['sha256']
    (out/'verification-profile/downloaded.blend').write_bytes(selected)
    append_script = out/'verify_public_material.py'
    append_script.write_text('''import bpy,json
from pathlib import Path
with bpy.data.libraries.load(str(Path('downloaded.blend').resolve()),link=False) as (source,target):
 target.materials=['TM_CustomBricks_asset']
m=target.materials[0]
assert m['tm_asset_id']=='mat-6e0293a1428e6f9bec7596aa'
assert m['tm_remote_pilot_demo_revision']==2
assert m.preview_ensure().image_size[0]>0
mesh=bpy.data.meshes.new('Public pilot quad')
mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[],[(0,1,2,3)])
obj=bpy.data.objects.new('Public pilot material',mesh)
bpy.context.scene.collection.objects.link(obj)
obj.data.materials.append(m)
assert obj.data.materials[0]==m
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
Path('public-material-verification.json').write_text(json.dumps(dict(material=m.name,assigned_to_mesh=True,packed_dependencies=True),indent=2))
''')
    blender_step('pilot-public-material-append',['--python-exit-code','1','--python',append_script],factory=True)
    proof = dict(phase='complete',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 release_url=release()['html_url'],pages_url=plan['pages_url'],library_url=plan['library_url'],
                 extension_url=assets[extension.name]['browser_download_url'],materials=12,
                 preview_only_materials=0,release_assets_verified=digests,
                 public_site_files=public_files,public_material_download_verified=True,
                 native_listing_download_verified=True,isolated_extension_install_verified=True,
                 public_material_appended_and_assigned=True,
                 interactive_asset_browser_test_pending=True,materiallib_included=False)
    (out/'public-verification.json').write_text(json.dumps(proof,indent=2))
    (out/'completion.json').write_text(json.dumps(proof,indent=2))
    save(phase='complete')
    print('GITHUB_MATERIALS_ONLY_PILOT_PUBLICLY_VERIFIED',flush=True)
except Exception as error:
    save(phase='failed',error=repr(error))
    raise
