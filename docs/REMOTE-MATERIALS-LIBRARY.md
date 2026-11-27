# Trackmania 2020 - Materials Library

Asset library extension for **Blender 5.3 and newer**.

The full **remote collection contains 820 materials and 20 HDRI Worlds**.
The extension installs from our GitHub-hosted repository; the complete material
download is **3.35 GB**, shared across **98 material bundles and 20 HDRI World files**.
The existing offline ZIPs remain available.

- Installation page: https://bigthirstytm.github.io/TM2020-Material-Assets-Library/
- Separate extension release: https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/materials-library-extension-v1.0.0
- Extension repository: https://bigthirstytm.github.io/TM2020-Material-Assets-Library/extensions/index.json

## Drag-and-drop installation

1. Open Blender 5.3 or newer. Enable **Online Access** in Preferences Ã¢â€ â€™ System.
2. Open the installation page and drag its green **Drag into Blender to install**
   button into Blender.
3. Confirm adding our extension repository if Blender asks, then confirm installing
   the asset library extension. Blender may ask you to drag the button again after
   adding a new repository; this is part of Blender's native installation flow.
4. Enable **Trackmania 2020 - Materials Library** under Preferences Ã¢â€ â€™ Asset Libraries
   if needed. Select it in an Asset Browser.

No terminal, PowerShell launcher or local server is needed. The installation ZIP
is small; the material files are hosted separately and downloaded when used.
This is our GitHub-hosted extension repository. Adding it makes the extension
available through Get Extensions; it is not a listing on Blender's official directory.

For manual installation, download `trackmania_2020_materials_library-1.0.0.zip`
and use Preferences Ã¢â€ â€™ Get Extensions Ã¢â€ â€™ Install from Disk. You can also add the
repository URL above through Get Extensions and install the library from its list.

## Included assets

The collection matches the **820 material entries in the current Materials Only
offline release** (`2026.11.26-thumbnail-shadow-lift-1`). Complete-only / Preview
only assets and source node-group assets are not offered. The 20 HDRI Worlds
from Materials Only are included under **06 HDRI World Moods**, grouped by
BlueBay, GreenCoast, RedIsland, Stadium and WhiteShore, each with day, night,
sunrise and sunset presets. The native
names, IDs, catalogs, shader graphs, animation drivers, export properties, current
thumbnails and existing feature badges are retained. See the [badge legend](BADGES.md).

This includes the latest terrain UV layers, water/ice previews, terrain C icons,
active-source diffuse insets and the six lighter identification thumbnails.
CustomBricks uses the current production material and icon.

Blendermania and its MaterialLib configuration are separate. The installation page offers a separate `MaterialLib.txt` download. Save it in a permanent folder and select it in Blendermania Settings ? Material Lib, then save the add-on settings. The asset-library extension does not configure Blendermania automatically.

## Downloads and updates

Blender downloads and caches a small material bundle (`.blend`), including its
packed textures. Related materials share a bundle to avoid repeatedly downloading
the same textures. A selected material downloads its whole containing bundle;
other assets in that bundle are then available without another payload download.
Bundles work without the original Trackmania texture folders.
Download and cache locations are managed by Blender's remote-assets system.

Use **Refresh Remote Listing** to discover additions and changed files. Thumbnail
URLs include their content hash to avoid stale images. Updated bundles
have new content-addressed download URLs; unchanged bundles remain reusable.
The same extension can retrieve new material listings without a new extension ZIP.

Refreshing or downloading a library asset does not replace a material already
appended into an open project. Replace or append the newer material when wanted.

To download everything, clear search and catalog filters, select all assets and
choose **Download Assets**. The compact collection totals **3,351,098,791 bytes (3.35 GB)** in **98
shared-texture material bundles and 20 HDRI World files**, compared with approximately 2.75 GB for the offline ZIPs.
Some texture-heavy bundles are larger than others (up to about 636 MB). The rejected per-material
layout required 10.37 GB because textures were repeated across many separate files.
Bundling and stronger lossless native Zstandard compression reduce duplication
without reducing texture resolution or changing material appearance.
Normal use only downloads the assets you need. Previously downloaded assets can
be used from the cache without downloading them again.

Existing offline libraries remain available as a fallback.

## Limits

The remote version preserves the source previews; it does not reconstruct a
different game renderer. Native links do not guarantee identical game appearance
or runtime behaviour. One existing native volume DDS resource cannot be decoded
as a Blender 2D image; its original bytes and material graph are retained. The
remote conversion does not invent a replacement for it.

## Maintenance

`tools/build_remote_materials.py` records the per-material reference;
`tools/build_remote_bundles.py` exports the stable shared bundles from
`data/remote-material-bundles.json`. The exporter records
stable contracts for shader inputs, node properties, group interfaces, drivers,
packed-image hashes, native metadata and preview artwork. Reuse its export directory
for later builds: unchanged files are preserved. Keep existing bundle assignments
stable; add new bundles for new materials instead of globally reclustering on
each update. `tools/compress_remote_bundles.py` checks identical decoded byte
streams before adopting stronger native compression.
`tools/verify_remote_bundles.py` reopens all bundles in Blender and checks every
saved material independently of its original texture paths.

The preparation tools require Python with Pillow and zstandard; these are
maintainer dependencies and are not required to install the Blender extension.

Generate the listing with Blender's `asset_listing generate` command, then use
`tools/prepare_remote_materials.py` to prepare the production site, extension and
content-addressed downloads. Build the extension and extension-repository index
with Blender's native extension commands. `tools/publish_remote_materials.py`
reuses verified uploads, appends changed bundle binaries, preserves older
content-addressed files and publishes metadata only after the files verify.
Keep old binary URLs available for clients with cached listings. Split later
hosting releases before reaching GitHub's per-release asset limit.

## Verification

All 820 materials were reopened and compared with the verified Materials Only
source, including shader graphs, drivers, native metadata, packed texture hashes
and thumbnail artwork. All current release files were independently checked against
GitHub SHA-256 digests. Public listing and extension bytes were checked, and the
extension was installed and enabled from its public repository in an isolated
Blender 5.3 profile. Four representative public material downloads were appended and assigned to test
meshes. All 20 HDRI Worlds were reopened with packed environment textures and
assigned to a scene; two public World downloads were independently appended
and assigned as the scene World. The existing installed library was unchanged.

Blender's native drag URL parser and installation path were verified; an
interactive browser-to-Blender drag was not automated. No new game export or
runtime tests were performed for this hosting conversion.

## HDRI Worlds

Existing extension users can use **Refresh Remote Listing** to discover the
**06 HDRI World Moods** catalog. Download or apply a World to use its lighting
and background in the scene. In Material Preview viewport shading, enable **Scene World**
to see the assigned environment. Refreshing the listing does not replace
a World already assigned to an open scene.

## Website badge examples

The installation page shows seven compact badge examples on one row on wide
screens, wrapping to four or two columns on smaller screens. Water and
TurboRoulette Sign use looping WebP previews rendered from their actual Blender
timeline shaders. TurboRoulette plays at a calmer presentation speed. A blue
Stadium Ad155Screen example fills its square with a centre crop; a gentle
camera movement reveals its existing parallax depth layers. Visitors who prefer reduced motion see the original static
thumbnail. Blender Asset Browser thumbnails remain static. In Blender, press
**Spacebar** (default) to start or stop timeline playback for animated materials.


Listing refresh updates metadata, not already-downloaded bundles. A warning triangle can indicate that the cached bundle differs from the current listing. Select an affected asset and use right-click ? Download Assets, then refresh the Asset Browser. Updating a shared bundle also updates the other assets stored in that bundle. Existing scene copies and exported items remain unchanged.
