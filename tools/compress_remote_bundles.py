"""Losslessly recompress native Zstandard .blend streams with a larger window."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
import zstandard as z
p=argparse.ArgumentParser();p.add_argument('--export',type=Path,required=True);a=p.parse_args()
root=a.export.resolve();report_path=root/'build-report.json';report=json.loads(report_path.read_text())
receipt=root/'compression.json';checks=json.loads(receipt.read_text()) if receipt.exists() else {}
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def decoded_sha(path):
 result=hashlib.sha256();size=0
 with path.open('rb') as f,z.ZstdDecompressor(max_window_size=512*1024*1024).stream_reader(f) as stream:
  while data:=stream.read(4*1024*1024):result.update(data);size+=len(data)
 return result.hexdigest(),size
for i,row in enumerate(report['bundles']):
 path=root/'host'/row['path'];before=path.stat().st_size;existing=checks.get(row['id'])
 if not (existing and existing.get('format_version')==3 and sha(path)==existing['sha256']):
  original_hash,raw_size=decoded_sha(path);pending=path.with_suffix('.recompressed')
  parameters=z.ZstdCompressionParameters.from_level(9,window_log=27,enable_ldm=True,threads=2)
  with path.open('rb') as source,pending.open('wb') as target,z.ZstdDecompressor(max_window_size=512*1024*1024).stream_reader(source) as stream:
   z.ZstdCompressor(compression_params=parameters).copy_stream(stream,target,size=raw_size)
  assert decoded_sha(pending)==(original_hash,raw_size),('Lossless compression mismatch',path)
  if pending.stat().st_size<before or (existing and existing.get('format_version')!=3):pending.replace(path)
  else:pending.unlink()
  checks[row['id']]=dict(format_version=3,original_bytes=existing['original_bytes'] if existing else before,bytes=path.stat().st_size,sha256=sha(path),decoded_sha256=original_hash)
  receipt.write_text(json.dumps(checks,indent=2))
 info=checks[row['id']];row.update(bytes=info['bytes'],sha256=info['sha256'])
 for material in report['materials']:
  if material['path']==row['path']:material.update(bytes=row['bytes'],sha256=row['sha256'])
 report_path.write_text(json.dumps(report))
 print('BUNDLE_LOSSLESSLY_COMPRESSED',i+1,len(report['bundles']),row['id'],info['original_bytes'],info['bytes'],flush=True)
report['total_bytes']=sum(row['bytes'] for row in report['bundles']);report['lossless_compression_verified']=True;report_path.write_text(json.dumps(report))
state_path=root/'export-state.json'
if state_path.exists():
 state=json.loads(state_path.read_text())
 for row in report['bundles']:state[row['id']]['sha256']=row['sha256']
 state_path.write_text(json.dumps(state))
(root/'compression-completion.json').write_text(json.dumps(dict(files=len(checks),before_bytes=sum(v['original_bytes'] for v in checks.values()),bytes=report['total_bytes'],decoded_streams_identical=True),indent=2))
print('ALL_BUNDLES_LOSSLESSLY_COMPRESSED',report['total_bytes'],flush=True)
