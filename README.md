# TM2020 Material Assets Library

A material asset library for **Trackmania 2020**, designed for the **Blendermania V2 export workflow**. Browse materials in Blender's Asset Browser, apply them to your mesh, and export using their native game material links.

[![Materials Only](https://img.shields.io/badge/Materials_Only-873_materials-287a48)](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-materials-only)
[![Complete Library](https://img.shields.io/badge/Complete_Library-1172_materials-3779b6)](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-complete)
[![Blender](https://img.shields.io/badge/Blender-5.3.0-e87d0d)](docs/INSTALLATION.md)

The badges above show the material count in each edition and the Blender version used to prepare the library. The small symbols on material thumbnails describe material features; see the [short badge legend](docs/BADGES.md).

Both full ZIP editions now publish **2026.11.27-vista-catalogs-1**, including the 53 additional native-linked vista materials and their corrected environment catalog placement. Both isolated installers and all twelve public release files passed independent verification. The combined packages retain the preceding material and thumbnail improvements: the terrain update restores missing UV detail/transition colour, roughness/metal and normal layers in 15 environment materials, including six RedIsland variants. It also includes 37 clearer terrain C thumbnails with active-source diffuse insets and a gentle lift for six dark light/water icons. See [terrain layers and controls](docs/TERRAIN-UV-LAYERS.md) and [thumbnail styles](docs/THUMBNAIL-STYLES.md).

The preceding [Dyna corrections](docs/DYNA-MATERIALS.md), [555 shader follow-up updates](docs/SHADER-FOLLOWUP.md) and thumbnail proportion/frame improvements are included. Existing badges and native export links are preserved. Both editions have two ZIPs with verified checksums; download both or use the installer.

## Sponsor logo correction in publication

The sixteen vista sponsor decals and their thumbnails are corrected locally in **2026.11.27-vista-logo-masks-1**. Remote extension **1.0.5** will publish first, followed by both offline editions. Existing public downloads remain available while these updates are verified. See [the exact shader/channel correction](docs/VISTA-LOGO-MASKS.md).

## Current combined refresh

Content revision **2026.11.27-vista-catalogs-1** includes the Dyna and shader follow-up updates above and combines the latest material improvements with the selected [A/B/C thumbnail styles](docs/THUMBNAIL-STYLES.md): softer top-down shader renders without visible studio-lamp reflections, vegetation standing on tiles, and Custom spheres. The [catalog clarity update](docs/CATALOG-CLARITY.md) removes duplicate example assets. AnimatedFlag is retained under Preview only after a reported item-loading crash; its animated MaterialLib alias is disabled.

Both full packages include the improvements to 31 projected previews, two light tubes and four optional structure colour masks, plus 88 recovered exact shader references. See [projected surfaces](docs/PROJECTED-SURFACES.md) and [source resolution](docs/SOURCE-RESOLUTION.md). The [shader reconciliation](docs/SHADER-RECONCILIATION.md) clarifies 94 root/pass references and improves ten array-based terrain previews plus LakeBottom. These source references do not promote Preview only entries to confirmed game compatibility.

## Vista update and catalog correction: remote and offline published

The local library now includes [53 additional vista materials](docs/VISTA-CANDIDATES.md) after a Trackmania linked-item load check and user visual confirmation. Six projected previews/icons use corrected separate top/side dimensions. Local totals are 873 Materials Only / 1,172 Complete (299 Preview only), plus 20 HDRI Worlds. The remote library is now published as extension **1.0.4**, content revision **2026.11.27-vista-catalogs-1**. The 53 additions are correctly placed below their own environment material categories; HDRI World Moods contains only World assets. All 893 public catalog assignments, current release digests and native installation checks passed independent verification. Both offline editions are also published with content revision **2026.11.27-vista-catalogs-1**. All six public files per edition match the independently verified local packages, and both isolated installers passed.

## Blender 5.3 asset-library extension

The full **Trackmania 2020 - Materials Library** extension is published with all 873 Materials Only entries and 20 HDRI Worlds. Install it from the [drag-and-drop installation page](https://bigthirstytm.github.io/TM2020-Material-Assets-Library/) or the [separate Blender 5.3+ asset-library extension release](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/materials-library-extension-v1.0.0). It uses our GitHub-hosted extension repository. See [installation and update details](docs/REMOTE-MATERIALS-LIBRARY.md). The full remote download is 4.24 GB in 122 files (102 material bundles and 20 HDRI Worlds); only changed bundles need downloading again. Five legacy screen materials with missing game targets are retained only under Preview only in Complete. Original texture resolutions are retained. Offline ZIPs remain available.

## Choose your edition

| Edition | Included | Recommended for |
| --- | --- | --- |
| [Materials Only](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-materials-only) | 873 native-linked materials | Building and exporting items |
| [Complete Library](https://github.com/BigthirstyTM/TM2020-Material-Assets-Library/releases/tag/v1.0.0-complete) | All 1,172 materials, including 299 Preview only assets | Browsing the full material and texture collection |

Both editions include 20 HDRI World assets, required textures, `MaterialLib.txt`, and an offline material catalogue. Complete retains 42 source texture node groups under **Preview only / Source resources**; Materials Only omits these node-group assets. They are shader inputs, not materials to drag onto a mesh. **Choose one edition**; Complete already includes everything in Materials Only.

Each edition has **two ZIP downloads**. Materials Only totals **2.96 GB** (1,479,414,626 and 1,479,410,327 bytes); Complete totals **3.41 GB** (1,706,252,675 and 1,706,252,932 bytes). Sizes use decimal GB. Extract both parts of your chosen edition into the same folder for manual installation, or use the installer to download and combine them automatically.

Both editions include **animated water previews** for Stadium, BlueBay, GreenCoast, RedIsland and WhiteShore. The two-layer motion follows recovered game shader instructions, with adjustable preview speed, direction and ripple strength. Cubic height-texture filtering keeps close-up ripples smooth. See [Water animation](docs/WATER-ANIMATION.md).

<img src="docs/images/water-animation.gif" alt="Animated Stadium water preview rendered in Blender" width="640">

The current refresh also adds water transparency in Eevee, internal ice depth and colouring, terrain angle transitions, and improved CustomGlass and parallax-screen refraction previews. See [Surface preview controls](docs/SURFACE-PREVIEWS.md) for settings and approximation limits.

The current refresh corrects native UV/vertex-colour declarations and adds source-based vertex-alpha transition layers to 14 terrain materials. Fifteen conditional ColorBlindness variants and six unsupported Warp originals now live in Complete / Preview only. See [Native material inputs](docs/NATIVE-INPUTS.md) for painting instructions and an editable example.

The combined `2026.11.23-native-surfaces-1` refresh includes the DecoHill UV overlays, depth-dependent water colour, and reconstructed WaterWall transmission, foam and animation. See [Terrain and water preview controls](docs/SHADER-FIDELITY-PREVIEWS.md) for settings and approximation limits.

It also includes the preceding 32-material Deco/PlatformIce update and another 183 corrected previews: remaining RoadDirt/ice layers, Custom Hue colour and macrodetail, native top/side texture families, GrassFence cutout, Warp screen normals and RoughMetal/specular connections. Matching thumbnails retain the existing feature badges. See [Native surface corrections](docs/CONCRETE-SHADER-CORRECTIONS.md) and [Deco and ice previews](docs/DECO-ICE-PREVIEWS.md). Check `release.json` or the installed `library.json` for the package's content revision.

Native-linked means an export link is available. It is not a blanket guarantee of in-game visibility, identical appearance, physics or crash-free behaviour. Preview only assets are reference assets with unconfirmed, conditional or unsupported export behaviour and are kept under **Trackmania2020 â†’ 08 Preview only**. This includes vegetation previews that are not currently exportable through this library.

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

> The published remote library and both offline ZIP editions include the 53 new vista materials with corrected catalogs. The five quarantined screens remain only under Preview only in Complete; no replacement materials are substituted.
