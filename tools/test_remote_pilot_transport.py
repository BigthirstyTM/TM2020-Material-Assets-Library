"""Bounded loopback test of the pilot using isolated Blender preferences.

Server runs only during this test and is always closed. No public hosting.
"""
import argparse
import functools
import hashlib
import http.server
import json
import os
import subprocess
import threading
import urllib.request
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--blender', type=Path, required=True)
p.add_argument('--pilot', type=Path, required=True)
a = p.parse_args()
root = a.pilot.resolve()
host = root / 'host'
work = root / 'transport-test'
work.mkdir(exist_ok=True)
requests = []


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        requests.append(dict(path=self.path, message=format % args))


env = os.environ.copy()
for key, subdir in [('BLENDER_USER_CONFIG', 'config'),
                    ('BLENDER_USER_EXTENSIONS', 'extensions'),
                    ('BLENDER_USER_DATAFILES', 'datafiles'),
                    ('BLENDER_USER_SCRIPTS', 'scripts')]:
    path = work / subdir
    path.mkdir(exist_ok=True)
    env[key] = str(path)


def run(name, arguments, factory=False):
    cmd = [str(a.blender.resolve()), '-b', '-t', '2', '--online-mode']
    if factory:
        cmd.append('--factory-startup')
    with (work / (name + '.log')).open('w') as log:
        subprocess.run(cmd + arguments, env=env, cwd=work, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=180,
                       creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)


server = http.server.ThreadingHTTPServer(('127.0.0.1', 52153),
    functools.partial(Handler, directory=str(host)))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    run('repo-add', ['--command', 'extension', 'repo-add', '--clear-all',
                    '--name', 'TM2020 Pilot Test', '--directory', str(work / 'repository'),
                    'tm2020_pilot_test'], factory=True)
    run('extension-install', ['--command', 'extension', 'install-file', '--repo',
                             'tm2020_pilot_test', '--enable',
                             str(root / 'tm2020_remote_pilot-0.1.0.zip')])
    inspect = work / 'inspect_extension.py'
    inspect.write_text('''import bpy,json
from pathlib import Path
libs=[dict(name=x.name,path=x.path,remote_url=x.remote_url) for x in bpy.context.preferences.filepaths.asset_libraries if x.name=='TM2020 Remote Pilot']
assert len(libs)==1 and libs[0]['remote_url']=='http://127.0.0.1:52153/',libs
Path('extension-registration.json').write_text(json.dumps(libs,indent=2))
''')
    run('extension-inspect', ['--python-exit-code', '1', '--python', str(inspect)])
    # Native Blender listing download, not our own index parser.
    run('native-listing-download', ['--command', 'asset_listing', 'download',
                                   'http://127.0.0.1:52153/'])
    assert any('_asset-library-meta.json' in r['path'] for r in requests)
    assert any('assets-00000.json' in r['path'] for r in requests)
    # Listing discovery must not pull in every material file.
    assert not any('.blend' in r['path'] for r in requests), requests
    discovery_requests = len(requests)
    # Check static-server requirements and import one downloaded material.
    name = 'materials/mat-6e0293a1428e6f9bec7596aa.blend'
    original = (host / name).read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    with urllib.request.urlopen('http://127.0.0.1:52153/' + name + '?hash=' + digest,
                                timeout=30) as response:
        assert int(response.headers['Content-Length']) == len(original)
        downloaded = response.read()
    assert downloaded == original
    (work / 'downloaded.blend').write_bytes(downloaded)
    script = work / 'append_downloaded.py'
    script.write_text('''import bpy,json
from pathlib import Path
with bpy.data.libraries.load(str(Path('downloaded.blend').resolve()),link=False) as (source,target):
 target.materials=['TM_CustomBricks_asset']
m=target.materials[0]
assert m['tm_asset_id']=='mat-6e0293a1428e6f9bec7596aa'
assert m['tm_remote_pilot_demo_revision']==2
assert m.preview_ensure().image_size[0]>0
mesh=bpy.data.meshes.new('Pilot quad');mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[],[(0,1,2,3)])
obj=bpy.data.objects.new('Downloaded pilot material',mesh);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(m)
assert obj.data.materials[0]==m
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.filepath)
Path('downloaded-import.json').write_text(json.dumps(dict(material=m.name,id=m['tm_asset_id'],assigned_to_mesh=True,packed_dependencies=True),indent=2))
''')
    run('downloaded-import', ['--python-exit-code', '1', '--python', str(script)], factory=True)
    proof = dict(extension_installed_in_isolated_profile=True,
                 native_listing_downloaded=True, discovery_requests=discovery_requests,
                 discovery_downloaded_material_files=0,
                 selected_material_http_download_verified=True,
                 selected_material_appended_and_assigned=True,
                 content_length_and_query_supported=True,
                 asset_browser_interaction_tested=False,
                 native_asset_cache_update_tested=False,
                 game_or_exporter_runtime_tested=False,
                 requests=requests)
    (root / 'transport-verification.json').write_text(json.dumps(proof, indent=2))
    print('PILOT_EXTENSION_AND_HTTP_TRANSPORT_VERIFIED', flush=True)
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
