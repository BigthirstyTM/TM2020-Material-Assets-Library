"""Read our unfiltered RGBA preview PNGs without Blender's import rounding."""
import struct,zlib
import numpy as np

def read_saved_preview(path):
 data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
 offset=8;payload=[];header=None
 while offset<len(data):
  length=struct.unpack('>I',data[offset:offset+4])[0];tag=data[offset+4:offset+8];chunk=data[offset+8:offset+8+length]
  assert struct.unpack('>I',data[offset+8+length:offset+12+length])[0]==zlib.crc32(tag+chunk)&0xffffffff
  if tag==b'IHDR':header=struct.unpack('>2I5B',chunk)
  if tag==b'IDAT':payload.append(chunk)
  offset+=length+12
 assert header==(256,256,8,6,0,0,0),header
 rows=np.frombuffer(zlib.decompress(b''.join(payload)),dtype=np.uint8).reshape(256,1025);assert not rows[:,0].any()
 pixels=rows[:,1:].reshape(256,256,4).copy()
 # Saved PNG is straight alpha; Blender previews use premultiplied bytes.
 pixels[:,:,:3]=np.rint(pixels[:,:,:3].astype(float)*pixels[:,:,3:4]/255).astype(np.uint8)
 return pixels
