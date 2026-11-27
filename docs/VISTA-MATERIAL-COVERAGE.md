# Vista material coverage audit

Research date: 2026-11-27. This report records the read-only baseline before the authorized local build. The subsequent 53 Preview only additions are documented in VISTA-CANDIDATES.md; no public release or game session was changed.

## Findings

The four vista archives contain **119 distinct standalone material paths**. All 119 have definitions in the current MaterialLib. Only 66 paths map to existing library assets through their recorded native path or active export alias. **53 paths have no corresponding Blender asset**, including Preview only. This is a coverage gap in asset creation, not evidence that all these paths are absent from MaterialLib.

An intermediate progress message estimated 55 gaps. The complete per-environment matrix establishes 53 (12 + 13 + 16 + 12); the earlier estimate is superseded. Both recorded native paths and active aliases resolved through MaterialLib were checked. Counts refer to distinct source paths, not guaranteed visually unique or runtime-safe materials.

| Vista | Standalone material paths | Paths represented by assets | Paths without assets | Paths absent from MaterialLib |
| --- | ---: | ---: | ---: | ---: |
| BlueBay | 30 | 18 | 12 | 0 |
| GreenCoast | 33 | 20 | 13 | 0 |
| RedIsland | 34 | 18 | 16 | 0 |
| WhiteShore | 22 | 10 | 12 | 0 |

All 119 source materials were already decoded in the prior native-resource inventories. The scan of 13 current archives found 985 unique standalone material paths overall. Of those, 181 do not map to library assets, including the 53 vista candidates. The remaining 128 include internal engine/UI/vehicle/shader resources and must not be interpreted as 128 additional usable surface materials.

None of the 53 vista candidates has the same recorded uncompressed material payload SHA-256 as a source path represented by an existing asset. That rules out exact payload copies among the decoded comparison set; it does not prove different rendered appearance.

## Why preloading can change an in-game list

A PAK directory inventory and a runtime FID/material browser are different data sources. Existing local editor source (`logs/v6/editor-source/Editor/MaterialCache.as`) enumerates `CSystemFidsFolder` trees; it does not read the raw archive directory. `RefreshCache()` scans a fixed list of folders, and that list omits BlueBay, GreenCoast, RedIsland and WhiteShore. The UI also has `Update Fid Trees` and `Expanded Search`; the latter scans the broader game/user/fake/resource/program-data FID roots. Its Materials List exposes full FID paths and a clipboard export.

This is concrete evidence that an editor material list can be incomplete even when the files exist. Loading a vista macroblock may expose more resources in those runtime trees, consistent with Chraz's observation. The exact before/after behavior of his installed editor build was not reproduced here; the inspected source is a previously saved local checkout, not proof of its current running version.

Preloading is **not required to discover these 119 standalone paths offline**: the PAK directory and decoded shader/material data already contain them. It remains necessary to distinguish listing visibility from whether a fresh exported custom item resolves the material without a supporting vista object.

## Source requirements

17 of the missing candidates use texture arrays and have a `cIndexPerVertex` control recorded as 0. The follow-up build recovered explicit named top/side selections from the material descriptors. The option name alone does not prove that these 17 require a per-vertex override. Mesh overrides, vertex alpha, terrain UV conventions, world projection and transition inputs still require later validation. The local previews use the named descriptor selections; no unknown runtime layer index is invented.

The other 36 candidates include sponsor decals, projected borders/walls/structures, terrain transitions and Warp ground. They still require correct transparency, projection, animation and item-export validation; they are not automatically cleared as Materials Only assets.

## Complete missing-vista asset list

The aliases below already exist in the current MaterialLib. No replacement texture or similar-looking material was selected.

| Source path | Existing MaterialLib alias | Array / per-vertex layer index |
| --- | --- | --- |
| `BlueBay/Media/Material/TransitionRocksToCliffPxz.Material.Gbx` | `BlueBay_TransitionRocksToCliffPxz` | Yes |
| `BlueBay/Media/Material/TransitionRocksToRocksTop.Material.Gbx` | `BlueBay_TransitionRocksToRocksTop` | Yes |
| `BlueBay/Media/Material/TransitionRocksToSand.Material.Gbx` | `BlueBay_TransitionRocksToSand` | Yes |
| `BlueBay/Media/Material/TransitionRocksToSeaFloor.Material.Gbx` | `BlueBay_TransitionRocksToSeaFloor` | Yes |
| `BlueBay/Media/Material/TransitionToCliffPxz.Material.Gbx` | `BlueBay_TransitionToCliffPxz` | Yes |
| `BlueBay/Media/Material/TransitionToSand.Material.Gbx` | `BlueBay_TransitionToSand` | Yes |
| `BlueBay/Media/Material/TransitionToSeaFloor.Material.Gbx` | `BlueBay_TransitionToSeaFloor` | Yes |
| `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` | `BlueBay_DecalPaint2Sponsor4x1D` | No |
| `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1NoColorizeD.Material.Gbx` | `BlueBay_DecalPaint2Sponsor4x1NoColorizeD` | No |
| `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` | `BlueBay_DecalPaintSponsor4x1D` | No |
| `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1NoColorizeD.Material.Gbx` | `BlueBay_DecalPaintSponsor4x1NoColorizeD` | No |
| `BlueBay/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` | `BlueBay_TrackBordersOffInWorld` | No |
| `GreenCoast/Media/Material/CliffTransition2ToCliff3.Material.Gbx` | `GreenCoast_CliffTransition2ToCliff3` | Yes |
| `GreenCoast/Media/Material/CliffTransitionToCliff2.Material.Gbx` | `GreenCoast_CliffTransitionToCliff2` | Yes |
| `GreenCoast/Media/Material/LakeShoreToLake.Material.Gbx` | `GreenCoast_LakeShoreToLake` | Yes |
| `GreenCoast/Media/Material/TransitionForestToTrunkA.Material.Gbx` | `GreenCoast_TransitionForestToTrunkA` | No |
| `GreenCoast/Media/Material/WarpGround.Material.Gbx` | `GreenCoast_WarpGround` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` | `GreenCoast_DecalPaint2Sponsor4x1D` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1NoColorizeD.Material.Gbx` | `GreenCoast_DecalPaint2Sponsor4x1NoColorizeD` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` | `GreenCoast_DecalPaintSponsor4x1D` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1NoColorizeD.Material.Gbx` | `GreenCoast_DecalPaintSponsor4x1NoColorizeD` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` | `GreenCoast_StructureInWorld` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` | `GreenCoast_TrackBordersInWorld` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` | `GreenCoast_TrackBordersOffInWorld` | No |
| `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` | `GreenCoast_TrackWallClipsInWorld` | No |
| `RedIsland/Media/Material/Cliff.Material.Gbx` | `RedIsland_Cliff` | Yes |
| `RedIsland/Media/Material/Cliff2.Material.Gbx` | `RedIsland_Cliff2` | Yes |
| `RedIsland/Media/Material/Cliff4.Material.Gbx` | `RedIsland_Cliff4` | Yes |
| `RedIsland/Media/Material/CliffEnds.Material.Gbx` | `RedIsland_CliffEnds` | Yes |
| `RedIsland/Media/Material/DetailsRocksToCliff2.Material.Gbx` | `RedIsland_DetailsRocksToCliff2` | Yes |
| `RedIsland/Media/Material/RiverSideToLakeBottom.Material.Gbx` | `RedIsland_RiverSideToLakeBottom` | No |
| `RedIsland/Media/Material/WarpGround.Material.Gbx` | `RedIsland_WarpGround` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` | `RedIsland_DecalPaint2Sponsor4x1D` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1NoColorizeD.Material.Gbx` | `RedIsland_DecalPaint2Sponsor4x1NoColorizeD` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` | `RedIsland_DecalPaintSponsor4x1D` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1NoColorizeD.Material.Gbx` | `RedIsland_DecalPaintSponsor4x1NoColorizeD` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` | `RedIsland_StructureInWorld` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` | `RedIsland_TrackBordersInWorld` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` | `RedIsland_TrackBordersOffInWorld` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` | `RedIsland_TrackWallClipsInWorld` | No |
| `RedIsland/Media/Modifier/StadiumOnTerrain/TrackWallInWorld.Material.Gbx` | `RedIsland_TrackWallInWorld` | No |
| `WhiteShore/Media/Material/WarpGround.Material.Gbx` | `WhiteShore_WarpGround` | No |
| `WhiteShore/Media/Material/WaterShoreRockyToWaterBottom.Material.Gbx` | `WhiteShore_WaterShoreRockyToWaterBottom` | Yes |
| `WhiteShore/Media/Material/WaterShoreToWaterBottom.Material.Gbx` | `WhiteShore_WaterShoreToWaterBottom` | Yes |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` | `WhiteShore_DecalPaint2Sponsor4x1D` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1NoColorizeD.Material.Gbx` | `WhiteShore_DecalPaint2Sponsor4x1NoColorizeD` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` | `WhiteShore_DecalPaintSponsor4x1D` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1NoColorizeD.Material.Gbx` | `WhiteShore_DecalPaintSponsor4x1NoColorizeD` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` | `WhiteShore_StructureInWorld` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` | `WhiteShore_TrackBordersInWorld` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` | `WhiteShore_TrackBordersOffInWorld` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` | `WhiteShore_TrackWallClipsInWorld` | No |
| `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackWallInWorld.Material.Gbx` | `WhiteShore_TrackWallInWorld` | No |

## Completion criteria for adding candidates

1. Keep this full source-path/alias/asset matrix as a release coverage report. Every discovered path must have an explicit outcome: existing asset, source-backed new asset, internal resource, duplicate with evidence, or Preview only with a reason.
2. For the 53 candidates, trace the source material ? parent material/shader ? textures/arrays, plus the vista mesh attributes where required. Preserve distinct full paths even when names match across vistas.
3. Create preview candidates from those actual sources; never substitute a similar texture. Retain Preview only status until export/use is validated.
4. Perform a controlled runtime comparison for each vista: fresh game session before loading its macroblock, after loading, refreshed/expanded full-path material list, and a newly exported item. Then repeat the item in a fresh session without the supporting macroblock. This separates list-cache behavior from a real preload dependency.
5. Reconcile the runtime-only paths against the 985-path directory inventory. Additional embedded or generated material instances require inspection of referenced Item/Prefab/Solid resources; this static audit does not certify exhaustive coverage of embedded instances.
6. Promote only validated candidates into Materials Only and its remote extension. Keep unsupported candidates in Complete Preview only. Existing public assets and the held offline publication remain unchanged by this research.

## Evidence

Local `build/vista-coverage-audit/`: `audit.py`, `coverage.json` (985-path matrix), `missing-vista-assets.json` (53 candidates), and `vista-materials.csv` (all 119 vista rows). Source inputs: the current source-materials inventory and installed MaterialLib, fresh PAK directory index from 2026-11-27, and decoded strict-native/v6/experimental resource inventories. No new game or interactive export tests were performed. The linked video was not used as independently observed runtime evidence.
