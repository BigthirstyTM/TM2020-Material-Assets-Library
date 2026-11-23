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

The Blender build preserves asset UUIDs, saved previews, material properties, shader graphs, animation, 20 Worlds and, in Complete, 42 asset node groups. It writes relative texture paths and places Preview only under the library's `08` category. Materials Only excludes assets explicitly classified as Preview only, even when a historical native link remains. Packaging estimates compressed sizes and balances the content across the minimum number of ZIPs, with a 1.9 GB safety ceiling per download. Each initial edition has two ZIPs. `release.json` is the authoritative package list.

Fresh Blender processes reopen each staged library and check image availability, asset counts, catalog references and saved icons. Packaging reads every ZIP member back and compares its SHA-256. Each ZIP stays below 2 GB. These are packaging checks, not additional claims about game runtime behaviour.

## Publishing

The initial release tags are `v1.0.0-materials-only` and `v1.0.0-complete`. Upload all files in the matching `dist/<edition>` directory to its release. Set Materials Only as the latest/recommended release. Both tags point to the same source commit.

When bumping a version, update the build metadata, package names, installer default, README links/badges and release notes together. Prefer a new tag and installation folder for subsequent changes. The owner explicitly requested an in-place refresh of the initial 1.0.0 releases on 2026-11-17 for animated, smoothly filtered water. Those refreshed assets retain their filenames and have new checksums; `library.json` and `release.json` identify the content revision.

The generated release installer has its default edition filled in. When running the repository's generic installer directly, explicitly pass `-Edition materials-only` or `-Edition complete`.

## Native input refresh

Build shader contracts with `tools/build_shader_contracts.py` using the extracted native resources, source inventory and MaterialLib. Run `tools/apply_chraz_corrections.py` in background Blender into a separate source directory before the portable build. Its reviewed projected-family allowlist excludes mixed shaders and unavailable exact shader definitions; do not automatically apply every audit proposal. Keep the source Textures tree alongside the staged blend. `tools/verify_native_inputs.py` reopens it, renders an alpha/RGB fixture and optionally exercises the installed V2 exporter with `--export`. `tools/build_native_input_example.py` writes the portable editing example. Use content revision `2026.11.23-native-inputs-1` for this combined refresh.

## Provenance

For the separate local Deco/PlatformIce update, run `tools/apply_deco_ice.py` in factory-startup background Blender with `--source` pointing to the installed shader-fidelity-1 library, `--inputs tools/data/deco-ice-inputs.json`, and a separate `--output` directory. Run `tools/verify_deco_ice.py --source STAGED_DIRECTORY --output VERIFICATION_DIRECTORY --original INSTALLED_LIBRARY.blend` before `tools/install_deco_ice.py`. The installer uses the same arguments as `install_shader_fidelity.py` and requires the matching verification JSON. It preserves a backup and refuses an installed source that changed after staging. Keep active upload packages immutable; use the newest installed library for the next combined build.

The portable builder omits Preview-only source node groups from Materials Only and removes empty catalog subtrees per edition. An incremental updater is deferred for later integration into Blendermania V2.

The `2026.11.17-surfaces-2` in-place refresh adds water transparency, internal ice depth/colour, terrain angular transitions, CustomGlass clarity and refracted screen layers. See [Surface source notes](SURFACE-SOURCES.md) for recovered data, remaining approximations and the adapter rebuild command.

The initial release derives from the V9 library dated 2026-11-12, source SHA-256 `15fcbca58dfb1b7d63385c85843162ef52c9d5e2e244d45aee9a4eeb534d4f1d`. It packages 847 native-linked materials and 272 additional preview assets. Fifteen recovered ColorBlindness links use the game's conditional accessibility palette. No new vegetation export route is included.
