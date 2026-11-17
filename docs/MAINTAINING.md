# Building and maintaining releases

Large Blender libraries and textures are distributed as GitHub release assets. They are not stored in Git. The repository includes the release installer, build scripts, catalog template and material inventory.

## Inputs

- Blender 5.2.3 LTS or compatible newer Blender, and Python 3.11+ for packaging.
- A complete source installation containing `Trackmania2020_assets.blend`, `blender_assets.cats.txt`, `MaterialLib.txt` and `Textures`. An extracted **Complete Library** release can serve as this input.
- `data/source-materials.json` from this repository.
- The material PNGs from the source installation's `Catalogue/previews` folder.

Keep the source installation separate from the build output. All scripts build copies; do not save changes back to the source library. External image files must live under its `Textures` directory. A complete source is required to rebuild both editions.

## Build

From the repository root, using your executable and source paths:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/build_library.py -- --source 'D:\TM2020-source\Trackmania2020_assets.blend' --inventory data/source-materials.json --output build/staging

python tools/prepare_payloads.py --staging build/staging --source 'D:\TM2020-source' --previews 'D:\TM2020-source\Catalogue\previews' --blender 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'

python tools/package_releases.py --staging build/staging --output dist
```

Use an empty staging/output directory for a new build. `prepare_payloads.py` may hard-link input texture files to save disk space. Do not edit staged texture files; ZIP archives contain independent bytes.

The Blender build preserves asset UUIDs, saved previews, material properties, shader graphs, animation, 20 Worlds and 42 asset node groups. It writes relative texture paths and places Preview only under the library's `08` category. Materials Only excludes the unbound assets. Packaging estimates compressed sizes and balances the content across the minimum number of ZIPs, with a 1.9 GB safety ceiling per download. Each initial edition has two ZIPs. `release.json` is the authoritative package list.

Fresh Blender processes reopen each staged library and check image availability, asset counts, catalog references and saved icons. Packaging reads every ZIP member back and compares its SHA-256. Each ZIP stays below 2 GB. These are packaging checks, not additional claims about game runtime behaviour.

## Publishing

The initial release tags are `v1.0.0-materials-only` and `v1.0.0-complete`. Upload all files in the matching `dist/<edition>` directory to its release. Set Materials Only as the latest/recommended release. Both tags point to the same source commit.

When bumping a version, update the build metadata, package names, installer default, README links/badges and release notes together. Prefer a new tag and installation folder for subsequent changes. The owner explicitly requested an in-place refresh of the initial 1.0.0 releases on 2026-11-17 for animated, smoothly filtered water. Those refreshed assets retain their filenames and have new checksums; `library.json` and `release.json` identify the content revision.

The generated release installer has its default edition filled in. When running the repository's generic installer directly, explicitly pass `-Edition materials-only` or `-Edition complete`.

## Provenance

The initial release derives from the V9 library dated 2026-11-12, source SHA-256 `15fcbca58dfb1b7d63385c85843162ef52c9d5e2e244d45aee9a4eeb534d4f1d`. It packages 847 native-linked materials and 272 additional preview assets. Fifteen recovered ColorBlindness links use the game's conditional accessibility palette. No new vegetation export route is included.
