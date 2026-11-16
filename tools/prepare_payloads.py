"""Assemble standalone, versioned editions from the portable Blender builds."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--staging', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--previews', type=Path, required=True)
    p.add_argument('--blender', type=Path, required=True)
    a = p.parse_args()
    staging = a.staging.resolve()
    images = json.loads((staging / 'source-images.json').read_text(encoding='utf-8'))
    for edition in ('materials-only', 'complete'):
        out = staging / edition
        # Hard links are a build optimization only: archives always store file bytes.
        for rel, source in images.items():
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                try:
                    os.link(source, dest)
                except OSError:
                    shutil.copy2(source, dest)
        shutil.copy2(a.source / 'MaterialLib.txt', out / 'MaterialLib.txt')
        report = out / 'verification.json'
        subprocess.run([str(a.blender), '--background', '--factory-startup', '--python-exit-code', '1',
                        '--python', str(ROOT / 'tools/verify_library.py'), '--',
                        '--library', str(out / 'Trackmania2020_assets.blend'), '--report', str(report)], check=True)
        checked = json.loads(report.read_text(encoding='utf-8'))
        needed = set(checked['external_images'])
        for rel in images:
            if rel not in needed:
                (out / rel).unlink()
        docs = out / 'docs'
        docs.mkdir(exist_ok=True)
        for name in ('INSTALLATION.md', 'USAGE.md', 'BADGES.md', 'CREDITS.md', 'MAINTAINING.md'):
            shutil.copy2(ROOT / 'docs' / name, docs / name)
        shutil.copy2(ROOT / 'README.md', out / 'README.md')
        shutil.copy2(ROOT / 'LICENSE-CODE', out / 'LICENSE-CODE')
        shutil.copy2(ROOT / 'installer/configure_blender.py', out / 'configure_blender.py')
        rows = json.loads((out / 'materials.json').read_text(encoding='utf-8'))
        cat = out / 'Catalogue'
        (cat / 'previews').mkdir(parents=True, exist_ok=True)
        for row in rows:
            shutil.copy2(a.previews / (row['id'] + '.png'), cat / 'previews' / (row['id'] + '.png'))
        template = (ROOT / 'tools/catalogue.html').read_text(encoding='utf-8')
        payload = json.dumps(rows).replace('<', '\\u003c')
        (cat / 'index.html').write_text(template.replace('__MATERIAL_DATA__', payload).replace('__EDITION__', html.escape(edition)), encoding='utf-8')
        metadata_path = out / 'build-source.json'
        if not metadata_path.exists():
            metadata_path = out / 'library.json'
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        metadata.update(version='1.0.0', edition=edition)
        (out / 'library.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        # Keep build/verification details outside the public installation UI.
        report.replace(staging / (edition + '-verification.json'))
        (out / 'build-source.json').unlink(missing_ok=True)
        print('PAYLOAD_READY', edition, len(rows), len(needed), flush=True)
    subprocess.run([str(a.blender), '--background', '--factory-startup', '--python-exit-code', '1',
                    '--python', str(ROOT / 'tools/build_examples.py'), '--', '--staging', str(staging)], check=True)


if __name__ == '__main__':
    main()
