# Vista materials: 53 native-linked additions

Revision `2026.11.27-vista-native-1` promotes **53 source-backed vista materials** into Materials Only and their existing environment catalogs. Complete now contains **1,172 materials**, including **299 Preview only**; Materials Only contains **873 materials**. All 20 HDRI Worlds are preserved. The remote update is published as extension **1.0.4** and independently verified. Both offline editions are also published as `2026.11.27-vista-catalogs-1`, including the corrected environment catalogs. Their isolated installers passed, all twelve public file digests match the local packages, and both public revision manifests were independently checked.

All 53 exact native resources loaded successfully in Trackmania and all 53 embedded test items loaded their models. The user watched the fixture and visually confirmed that the materials worked, then authorized promotion. This is a linked-item load and user visual check, not a driving/physics test or proof of identical Blender/native rendering. No substitute textures or replacement links were selected. MaterialLib already contains the 53 aliases and remains byte-for-byte unchanged.

The preceding 1,181 assets retain their graphs, identities, export data, badges and icons. All 53 new asset IDs are preserved; six candidate projection graphs/icons were corrected before promotion.

## New materials

Names below omit the common `TM_` prefix and `_asset` suffix. The CSV has full names, source paths and candidate export aliases.

### BlueBay (12)

- `BlueBay_TransitionRocksToCliffPxz`
- `BlueBay_TransitionRocksToRocksTop`
- `BlueBay_TransitionRocksToSand`
- `BlueBay_TransitionRocksToSeaFloor`
- `BlueBay_TransitionToCliffPxz`
- `BlueBay_TransitionToSand`
- `BlueBay_TransitionToSeaFloor`
- `BlueBay_DecalPaint2Sponsor4x1D`
- `BlueBay_DecalPaint2Sponsor4x1NoColorizeD`
- `BlueBay_DecalPaintSponsor4x1D`
- `BlueBay_DecalPaintSponsor4x1NoColorizeD`
- `BlueBay_TrackBordersOffInWorld`

### GreenCoast (13)

- `GreenCoast_CliffTransition2ToCliff3`
- `GreenCoast_CliffTransitionToCliff2`
- `GreenCoast_LakeShoreToLake`
- `GreenCoast_TransitionForestToTrunkA`
- `GreenCoast_WarpGround`
- `GreenCoast_DecalPaint2Sponsor4x1D`
- `GreenCoast_DecalPaint2Sponsor4x1NoColorizeD`
- `GreenCoast_DecalPaintSponsor4x1D`
- `GreenCoast_DecalPaintSponsor4x1NoColorizeD`
- `GreenCoast_StructureInWorld`
- `GreenCoast_TrackBordersInWorld`
- `GreenCoast_TrackBordersOffInWorld`
- `GreenCoast_TrackWallClipsInWorld`

### RedIsland (16)

- `RedIsland_Cliff`
- `RedIsland_Cliff2`
- `RedIsland_Cliff4`
- `RedIsland_CliffEnds`
- `RedIsland_DetailsRocksToCliff2`
- `RedIsland_RiverSideToLakeBottom`
- `RedIsland_WarpGround`
- `RedIsland_DecalPaint2Sponsor4x1D`
- `RedIsland_DecalPaint2Sponsor4x1NoColorizeD`
- `RedIsland_DecalPaintSponsor4x1D`
- `RedIsland_DecalPaintSponsor4x1NoColorizeD`
- `RedIsland_StructureInWorld`
- `RedIsland_TrackBordersInWorld`
- `RedIsland_TrackBordersOffInWorld`
- `RedIsland_TrackWallClipsInWorld`
- `RedIsland_TrackWallInWorld`

### WhiteShore (12)

- `WhiteShore_WarpGround`
- `WhiteShore_WaterShoreRockyToWaterBottom`
- `WhiteShore_WaterShoreToWaterBottom`
- `WhiteShore_DecalPaint2Sponsor4x1D`
- `WhiteShore_DecalPaint2Sponsor4x1NoColorizeD`
- `WhiteShore_DecalPaintSponsor4x1D`
- `WhiteShore_DecalPaintSponsor4x1NoColorizeD`
- `WhiteShore_StructureInWorld`
- `WhiteShore_TrackBordersInWorld`
- `WhiteShore_TrackBordersOffInWorld`
- `WhiteShore_TrackWallClipsInWorld`
- `WhiteShore_TrackWallInWorld`

## Projection correction and preview limits

The source image-array format exposes separate **Py (top)** and **Pxz (side)** dimensions/offsets, plus a Py rotation. Native reflected values were read in the game and compared with the decoded array fields and compiled projection shader. The earlier preview incorrectly reused Py dimensions for Pxz.

For `WhiteShore_WaterShoreToWaterBottom` and its Rocky variant, `WaterBottomPxz` uses **80 by 7 metres**, with a 2-metre horizontal offset; its top dimensions are 1 by 1 metre and must not be used for the side. The selected `WaterBottom` top texture uses 32 by 32 metres and a 7-degree rotation. The visible every-metre repeated bands were a Blender mapping bug. Native tiling over the authored dimensions remains intentional; mesh-UV transition layers still follow the object's BaseMaterial UV and Color alpha.

Six graphs and matched thumbnails were corrected:

- `TM_RedIsland_Cliff_asset`
- `TM_RedIsland_Cliff2_asset`
- `TM_RedIsland_CliffEnds_asset`
- `TM_RedIsland_DetailsRocksToCliff2_asset`
- `TM_WhiteShore_WaterShoreRockyToWaterBottom_asset`
- `TM_WhiteShore_WaterShoreToWaterBottom_asset`

The 17 texture-array materials use their explicit named source selections. The three WarpGround previews retain static source projection; native view/horizon warping remains incomplete. CubeOut/DispIn reproduces the surface, color mask and available SI depth branch; some native interior/foreground activation remains approximate. Sponsor decals use their own opacity masks. No foliage was invented without a source sprite binding.

`Documentation/Vista-Candidates-Review.blend` is a disposable Blender review scene with BaseMaterial UV and Color attributes. It has no asset marks and does not duplicate browser entries. The production materials now have enabled Blendermania RNA and serialized export aliases; the separate old candidate backup retains the prior disabled links.

## Validation

The staged and installed master were independently reopened. All 53 actual add-on export links, serialized aliases, IDs, saved icons and classification were checked. All unrelated assets remain unchanged, all images resolve, and installation has a recoverable backup. The five separately quarantined screen materials and AnimatedFlag remain Preview only. Remote publication checks verify all 873 materials, 20 HDRI Worlds, packed payloads and the native Blender 5.3 extension/listing; remote-first publication status is recorded separately.

Catalog correction: the 53 additions in extension 1.0.3 were incorrectly placed below HDRI World Moods. The correct environment material paths are published in extension 1.0.4 and all 893 public catalog assignments passed independent verification. Use Refresh Remote Listing and Download Assets to replace cached vista bundles. See [catalog correction](VISTA-CATALOGS.md).
