# Trackmania 2020 - Materials Library

Asset library extension for **Blender 5.3 and newer**.

The full **remote collection contains 873 materials and 20 HDRI Worlds**.
The extension installs from our GitHub-hosted repository; the complete material
download is **4.24 GB**, shared across **102 material bundles and 20 HDRI World files**.
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

For manual installation, download `trackmania_2020_materials_library-1.0.7.zip`
and use Preferences Ã¢â€ â€™ Get Extensions Ã¢â€ â€™ Install from Disk. You can also add the
repository URL above through Get Extensions and install the library from its list.

## Included assets

The collection matches the **873 Materials Only entries in the verified installed
source** (`2026.11.27-vista-catalogs-1`) and the published offline Materials Only
ZIPs. Both offline editions include the 53 vista additions and corrected catalogs;
both installers and all six public files per edition passed independent verification. Complete-only / Preview
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
choose **Download Assets**. The compact collection totals **4,238,434,233 bytes (4.24 GB)** in **102
shared-texture material bundles and 20 HDRI World files**, compared with 2.96 GB for the two offline Materials Only ZIPs.
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

All 873 materials were reopened and compared with the verified Materials Only
source, including shader graphs, drivers, native metadata, packed texture hashes
and thumbnail artwork. All current release files were independently checked against
GitHub SHA-256 digests. Public listing and extension bytes were checked, and the
extension was installed and enabled from its public repository in an isolated
Blender 5.3 profile. Eight representative public material downloads (four existing and one from each vista) were appended and assigned to test
meshes. All 20 HDRI Worlds were reopened with packed environment textures and
assigned to a scene; two public World downloads were independently appended
and assigned as the scene World. The existing installed library was unchanged.

Blender's native drag URL parser and installation path were verified; an
interactive browser-to-Blender drag was not automated. The 53 added vista links were preloaded and their linked test ItemModels loaded
in Trackmania; the user watched the visual check and confirmed they worked. This
does not establish driving/physics behaviour or exact Blender/game rendering.

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

Catalog correction: the 53 additions in extension 1.0.3 were incorrectly placed below HDRI World Moods. The correct environment material paths are published in extension 1.0.4 and all 893 public catalog assignments passed independent verification. Use Refresh Remote Listing and Download Assets to replace cached vista bundles. See [catalog correction](VISTA-CATALOGS.md).

## Sponsor logo correction: extension 1.0.5

Published content revision `2026.11.27-vista-logo-masks-1` corrects sixteen vista sponsor materials and icons using the native red-channel mask. All current public digests, catalog assignments, isolated native installation and sampled appends passed independent verification. Refresh Remote Listing, then Download Assets for the vista entries to replace cached bundles. Existing scene materials are not rewritten. Both offline editions now include the sponsor correction and colorpicker badges. See [exact shader/channel correction](VISTA-LOGO-MASKS.md).

## Ingame colorpicker badges: extension 1.0.6

Published revision `2026.11.27-colorpicker-badges-1` adds brush badges to86 materials with explicit native color-table bindings. All124 current public files,893 catalog assignments, isolated native installation, sampled material appends and World appends passed independent verification. Existing shader graphs and native export links are preserved. Refresh Remote Listing, then Download Assets to replace changed cached bundles. Existing scene materials are not rewritten. Both offline editions now publish the same colorpicker revision after isolated installer and independent public-file verification. See [full material list and evidence](COLORPICKER-MATERIALS.md).

## Clearer red paintbrush: extension 1.0.7

Remote extension **1.0.7** and both offline editions publish the red paintbrush redesign after independent installation and public-file verification. The same 86 native colorpicker materials now use a red background and a larger brush, distinct from the purple parallax marker. Shader graphs and all other thumbnail regions are unchanged. Refresh Remote Listing, then Download Assets for changed cached bundles. Existing scene materials are not rewritten.
