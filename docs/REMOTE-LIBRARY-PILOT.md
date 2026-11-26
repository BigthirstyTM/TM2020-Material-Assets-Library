# Materials Only remote library pilot

This Blender 5.3+ pilot contains 12 Materials Only entries. The public extension
will offer Materials Only; experimental and Preview only entries remain for DEV
evaluation. The existing offline packages remain available as a fallback.

The GitHub-hosted pilot is published and verified.
[Open the installation page](https://bigthirstytm.github.io/TM2020-Material-Assets-Library/).
Extension installation, native listing discovery and downloading/applying a material
were verified in an isolated Blender 5.3 profile. Game export was not tested.

## Installation

1. Download `tm2020_materials_only-0.1.0.zip` from the
   [pilot prerelease](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/remote-materials-only-pilot-v0.1.0).
2. Enable Online Access in Blender.
3. Choose Preferences > Get Extensions > Install from Disk and select the ZIP.
4. Enable **TM2020 Materials Only (Pilot)** under Preferences > Asset Libraries.
5. Select the library in an Asset Browser. Blender downloads materials when needed.

No PowerShell launcher or local server is needed for the GitHub-hosted pilot.
To download the entire pilot, clear search and catalog filters, select all assets,
and choose Download Assets. Refresh Remote Listing retrieves the current listing.
Refreshing the library does not replace materials already appended to a scene.

Blendermania and its MaterialLib setup are separate. The extension does not bundle
`MaterialLib.txt`; obtain the export setup through Blendermania.
The [badge legend](BADGES.md) explains the existing thumbnail badges.

## Visible update trial

CustomBricks deliberately retains the yellow/black preview and **UPDATE 02** icon
from the local update trial. Its stable asset ID and native game link are retained.
This is a test appearance rather than the original brick preview.

## Hosting and updates

Small listings and content-versioned thumbnails are hosted on GitHub Pages.
Packed material files are hosted as content-addressed GitHub Release assets.
The stable file path and asset ID remain in the listing; a changed material points
to a new binary URL and hash. Unchanged material files can be reused. Thumbnail
URLs also change with their content to avoid stale preview caches.

The extension and public index contain only the selected Materials Only entries,
not the local DEV pilot's Preview only material. The local pilot is retained and
is not modified by public deployment. The offline full-library upload is separate.

The pilot has substantial duplicate packed texture data in layered materials.
Before expanding to the full collection, evaluate family bundles, disk use,
batch/offline downloads and real Asset Browser cache updates. Shader previews
approximate the game renderer; native links do not guarantee gameplay behavior.
