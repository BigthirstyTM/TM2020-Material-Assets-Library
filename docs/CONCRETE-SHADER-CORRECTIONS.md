# Native surface corrections

Content revision: **2026.11.23-native-surfaces-1**.

This combined refresh includes the preceding Deco/Ice and water/WaterWall updates and corrects another 183 material previews. Material counts remain **826 Materials Only** and **1,119 Complete**, including **293 Preview only** assets.

## What changed

| Material family | Correction |
| --- | --- |
| 163 RoughMetal previews | Removed the incorrect blue-channel connection to Specular IOR Level. Usage 36/37 supplies roughness and metalness; dielectric reflection now uses Blender's standard IOR response. |
| RoadDirt, RoadDirtFullColorize, TrackWall, GreenCoast TrunkToGrass | Separate projected top/side layers, native normal images and macro modulation, followed by the authored BaseMaterial UV decoration. Overlay weight is texture alpha multiplied by the selected vertex alpha. |
| RoadIce | Restored the native surface-mark mask, projected ice normals/roughness and internal colour independently of vertex alpha. Internal depth no longer contributes an invented outer-surface bump. |
| PlatformIce OpenTechBorders | Internal refraction depth now samples RoadIce_H rather than using a uniform depth. |
| CustomRock | Restored the distinct CustomRockPxz side-texture family and native top macro input. |
| 13 Custom surfaces | Added the recovered chroma/grey Hue formula with each material's stored native TargetColor. |
| Remaining macro inputs | Restored native modulation in the reviewed Custom, PlatformDirt PlatformTech, RoadDirt and TrackWall previews. |
| GreenCoast TrackWallInWorld | Replaced the unrelated grass-image family with the native TrackWallPxzInWorld inputs. |
| RedIsland LakeBottom | Restored LakeBottom top colour and LakeBottomPxz side colour, roughness and normal images. |
| TrackBordersInWorld | Resolved the apparent naming conflict, retained its existing BlueBay export identity, and restored source colour masks, illumination, height and interior-image inputs. |
| RedIsland DetailsToDirt | Added the missing native UV detail overlay and actual array-selected Dirt/DirtHill base layers. |
| 12 Warp screens | Replaced LightCells3_N with the source-linked LightCells_N normal image. |
| Stadium GrassFence | Restored Diffuse, GrassX2, FenceA colour/opacity and a two-sided cutout preview. |

Counts overlap: one material can receive several corrections. Existing feature badges are retained; no customization badges were added. Native export aliases, material identifiers, catalog assignments, collision/gameplay data and MaterialLib declarations are preserved.

The complete material names for each correction are listed in [Updated materials](UPDATED-MATERIALS.md).

## Using the corrected previews

Refresh the Asset Browser and append/import a fresh copy of an affected material. Materials already appended into another scene retain their previous nodes until you replace them. A pencil icon identifies a local editable copy.

Mixed terrain previews have a **Deco native layer controls** group. Their decoration uses a UV map named **BaseMaterial**; resizing or moving the mesh does not repeat this decoration through world projection. Projected ground/side layers still use world coordinates by design.

The controls default to **Fallback alpha = 1** and **Use painted vertex alpha = 0**, so an object without a colour attribute displays the decoration. To paint the blend, add a colour attribute named **Color**, paint its alpha and enable **Use painted vertex alpha**. Alpha 0 selects the base; alpha 1 adds decoration through the texture's own alpha. RGB does not control that blend. These controls affect the Blender preview; export uses the object's actual vertex data.

Custom Hue materials expose **Hue target (native default)**, initialized from their stored TargetColor. This is a preview control: changing nodes alone does not change the game's native material definition or exported customization data.

## Approximation limits

- Removing RoughMetal blue from specular fixes an unsupported channel interpretation. Blender's BRDF/IOR response is still a renderer adapter, not a reproduction of every native lighting pass.
- Native top/side texture identities and recovered layer formulas are used. Angular interpolation, projection normal bases, runtime arrays and some target-mode branches remain Blender approximations.
- LakeBottom's material slots and bitmap transforms are available, but its exact shader descriptor remains unresolved. Its corrected top/side preview is not claimed as a complete shader port.
- TrackBordersInWorld's **Stadium** name identifies its texture family. The existing native link and export alias select **BlueBay_TrackBordersInWorld**. This refresh preserves that link. Its interior uses a planar refraction approximation and a stored default colour-table entry; native cube/intersection rendering and runtime target selection remain approximate.
- GrassFence restores source texture multiplication and alpha. Its VDepLight render target, native geometry deformation, edge fade and MSAA sample coverage require game-specific rendering context. The deterministic preview cutout threshold of 0.5 is adjustable in **Native GrassFence Surface** and is not a conversion of native AlphaRef 50. It avoids stochastic transparency speckles.
- Ice internal projection remains a planar depth adapter; full native decal/LOD and rendering behavior are not reconstructed by this refresh.

The game was not started for this update. Shader/cache analysis and Blender checks do not constitute a new in-game clearance of every material. Preview-only ColorBlindness variants and unsupported Warp originals remain Preview only.

For the retained water controls, see [Terrain and water previews](SHADER-FIDELITY-PREVIEWS.md). For the preceding 32-material update, see [Deco and ice previews](DECO-ICE-PREVIEWS.md). Existing icons are explained in the [short badge legend](BADGES.md).
