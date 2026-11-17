"""Create independently downloadable ZIP components below GitHub's asset limit."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_UNCOMPRESSED = 96_000_000


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--staging', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reuse-textures', action='store_true')
    a = p.parse_args()
    for edition in ('materials-only', 'complete'):
        source = a.staging / edition
        output = a.output / edition
        output.mkdir(parents=True, exist_ok=True)
        files = sorted(p for p in source.rglob('*') if p.is_file())
        groups = [[p for p in files if p.relative_to(source).parts[0] != 'Textures']]
        for path in files:
            if path.relative_to(source).parts[0] != 'Textures':
                continue
            if len(groups) == 1 or sum(p.stat().st_size for p in groups[-1]) + path.stat().st_size > MAX_UNCOMPRESSED:
                groups.append([])
            assert path.stat().st_size < MAX_UNCOMPRESSED, path
            groups[-1].append(path)
        manifest = dict(version='1.0.0', edition=edition, archives=[], files={})
        for index, members in enumerate(groups):
            label = 'library' if index == 0 else f'textures-{index:02d}'
            dest = output / f'TM2020-1.0.0-{edition}-{label}.zip'
            for path in members:
                manifest['files'][path.relative_to(source).as_posix()] = sha(path)
            if not (a.reuse_textures and index > 0 and dest.is_file()):
                with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as archive:
                    for path in members:
                        archive.write(path, path.relative_to(source).as_posix())
            assert dest.stat().st_size < 2_000_000_000, dest
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
