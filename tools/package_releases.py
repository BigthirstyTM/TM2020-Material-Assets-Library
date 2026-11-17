"""Create independently downloadable ZIP components below GitHub's asset limit."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
import math
import zlib

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 1_900_000_000


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def compressed_size(path):
    compressor = zlib.compressobj(level=4, wbits=-15)
    total = 0
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            total += len(compressor.compress(chunk))
    return total + len(compressor.flush()) + 1024


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--staging', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    for edition in ('materials-only', 'complete'):
        source = a.staging / edition
        output = a.output / edition
        output.mkdir(parents=True, exist_ok=True)
        files = sorted(p for p in source.rglob('*') if p.is_file())
        estimates = {path: compressed_size(path) for path in files}
        part_count = max(1, math.ceil(sum(estimates.values()) / MAX_ARCHIVE_BYTES))
        groups = [[] for _ in range(part_count)]
        sizes = [0 for _ in groups]
        for path in sorted(files, key=lambda path: (-estimates[path], path.as_posix())):
            index = min(range(part_count), key=lambda i: sizes[i])
            groups[index].append(path)
            sizes[index] += estimates[path]
        manifest = dict(version='1.0.0', edition=edition, archives=[], files={})
        for index, members in enumerate(groups):
            label = f'part{index + 1:02d}'
            dest = output / f'TM2020-1.0.0-{edition}-{label}.zip'
            for path in members:
                manifest['files'][path.relative_to(source).as_posix()] = sha(path)
            with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as archive:
                for path in sorted(members):
                    archive.write(path, path.relative_to(source).as_posix())
            assert dest.stat().st_size < MAX_ARCHIVE_BYTES, dest
            with zipfile.ZipFile(dest) as archive:
                assert set(archive.namelist()) == {path.relative_to(source).as_posix() for path in members}
                for name in archive.namelist():
                    with archive.open(name) as stream:
                        assert hashlib.file_digest(stream, 'sha256').hexdigest() == manifest['files'][name], name
            manifest['archives'].append(dict(name=dest.name, bytes=dest.stat().st_size, sha256=sha(dest)))
            print('ZIP_VERIFIED', edition, label, dest.stat().st_size, flush=True)
        (output / 'release.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        installer = (ROOT / 'installer/Install-Library.ps1').read_text(encoding='utf-8').replace("$Edition = 'materials-only'", "$Edition = " + repr(edition))
        (output / 'Install-Library.ps1').write_text(installer, encoding='utf-8-sig')
        shutil.copy2(ROOT / 'docs/INSTALLATION.md', output / 'INSTALLATION.md')
        sums = ''.join(sha(path) + '  ' + path.name + '\n' for path in sorted(output.iterdir()) if path.is_file() and path.name != 'SHA256SUMS.txt')
        (output / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
        print('RELEASE_READY', edition, sum(r['bytes'] for r in manifest['archives']), flush=True)


if __name__ == '__main__':
    main()
