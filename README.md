# TM2020 Material Assets Library

A material asset library for **Trackmania 2020**, designed for the **Blendermania V2 export workflow**. Browse materials in Blender's Asset Browser, apply them to your mesh, and export using their native game material links.

[![Materials Only](https://img.shields.io/badge/Materials_Only-847_materials-287a48)](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-materials-only)
[![Complete Library](https://img.shields.io/badge/Complete_Library-1119_materials-3779b6)](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-complete)
[![Blender](https://img.shields.io/badge/Blender-5.2.3_LTS-e87d0d)](docs/INSTALLATION.md)

The badges above show the material count in each edition and the Blender version used to prepare the library. The small symbols on material thumbnails describe material features; see the [short badge legend](docs/BADGES.md).

## Choose your edition

| Edition | Included | Recommended for |
| --- | --- | --- |
| [Materials Only](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-materials-only) | 847 native-linked materials | Building and exporting items |
| [Complete Library](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-complete) | All 1,119 materials, including 272 Preview only assets | Browsing the full material and texture collection |

Both editions include 20 HDRI World assets, 42 shader node-group assets, their required textures, `MaterialLib.txt`, and an offline material catalogue. **Choose one edition**; Complete already includes everything in Materials Only.

Each edition has **two ZIP downloads**. Extract both into the same folder for manual installation, or use the installer to download and combine them automatically.

Both editions include **animated water previews** for Stadium, BlueBay, GreenCoast, RedIsland and WhiteShore. The two-layer motion follows recovered game shader instructions, with adjustable preview speed, direction and ripple strength. Cubic height-texture filtering keeps close-up ripples smooth. See [Water animation](docs/WATER-ANIMATION.md).

<img src="docs/images/water-animation.gif" alt="Animated Stadium water preview rendered in Blender" width="640">

The current refresh also adds water transparency in Eevee, internal ice depth and colouring, terrain angle transitions, and improved CustomGlass and parallax-screen refraction previews. See [Surface preview controls](docs/SURFACE-PREVIEWS.md) for settings and approximation limits.

Native-linked means an export link is available. It is not a blanket guarantee of in-game visibility, identical appearance, physics or crash-free behaviour. Preview only assets have no confirmed export route and are kept under **Trackmania2020 → 08 Preview only**. This includes vegetation previews that are not currently exportable through this library.

## Install on Windows

1. Install Blender **5.2.3 LTS or a compatible newer version** and your Blendermania build with the **V2 exporter** enabled. See [requirements](docs/INSTALLATION.md#requirements).
2. Close Blender. Open the release for your chosen edition and download **Install-Library.ps1**.
3. Open PowerShell in your download folder and run:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-Library.ps1
   ```

The installer downloads the matching packages, checks their SHA-256 hashes, extracts the library and registers it in Blender. It also configures the Material Lib path when it can locate Blendermania. No administrator access is needed. Existing preferences and Blendermania settings are backed up before changes.

4. Start Blender, open an **Asset Browser**, and select **TM2020 Material Assets Library**.

For manual installation, custom locations, updating or uninstalling, see [Installation](docs/INSTALLATION.md). To start using materials, see [Usage](docs/USAGE.md).

## Project contents

- **GitHub repository:** installer, build tools, documentation and machine-readable material inventories.
- **Release downloads:** Blender libraries, required texture files, catalogue and installation tools. Large texture downloads are divided into ordinary ZIP packages which the installer combines automatically.
- **Offline catalogue:** open `Catalogue/index.html` inside your installed library. It includes search, categories, thumbnails and per-material usage notes.

Game assets remain the property of their respective owners. This is an independent community project. See [Credits and asset rights](docs/CREDITS.md).

For rebuilding and publishing the project, see [Maintaining](docs/MAINTAINING.md). The original installer and build tooling are covered by [LICENSE-CODE](LICENSE-CODE); this licence does not apply to game assets.
