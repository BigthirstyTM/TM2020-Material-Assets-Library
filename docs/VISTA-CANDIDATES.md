# Vista candidates added locally

Revision `2026.11.27-vista-candidates-1` adds **53 source-backed materials** with saved 256?256 icons. They are installed in Complete under `Trackmania2020/08 Preview only/Vista candidates`, grouped by vista. They are not added to Materials Only or the remote extension and have no enabled export links. Each material retains its real source alias/path and decoded shader information for later testing. No similar-looking textures or replacement materials were selected.

Complete now has 1,172 materials (352 Preview only). Materials Only remains 820 materials. The 20 HDRI Worlds and all 1,181 preceding asset identities, graphs and icons are preserved. No game session was started.

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

## Preview limits and later game review

All 53 materials remain untested in Trackmania. File existence and Blender rendering are not runtime clearance. The candidate aliases are recorded as provenance and are disabled in actual add-on RNA and serialized export properties.

17 materials select texture-array layers. Their named source selectors were recovered, including distinct top/side selections where authored. The source records store `cIndexPerVertex=0`; the earlier coverage report must not be read as proving that all 17 require an unknown per-vertex index. These previews use the explicit named material selections. Whether a particular runtime mesh overrides them remains a later test.

Six materials retain nontrivial native array matrix fields that are not fully reconstructed. Their previews use the recorded primary dimensions and show an explicit limitation in material metadata:

- `TM_RedIsland_Cliff_asset`
- `TM_RedIsland_Cliff2_asset`
- `TM_RedIsland_CliffEnds_asset`
- `TM_RedIsland_DetailsRocksToCliff2_asset`
- `TM_WhiteShore_WaterShoreRockyToWaterBottom_asset`
- `TM_WhiteShore_WaterShoreToWaterBottom_asset`

The three WarpGround candidates show static source projection; native view/horizon warp remains incomplete. The CubeOut/DispIn candidates reproduce the source surface, color mask and available SI depth branch; some native interior/foreground activation remains approximate. Sponsor decals use their own opacity mask and preserve that mask's aspect in the icon. No foliage was added without a source sprite binding.

`Vista-Candidates-Review.blend` in the installed Documentation folder applies all 53 candidates to test meshes with BaseMaterial UV and Color attributes. The scene has no asset marks, so it does not duplicate Asset Browser entries. Open it manually and use Material Preview or Rendered shading. This is a Blender review scene, not an export-ready or game-verified item set. Export aliases must be deliberately enabled in a separate test copy when the full game audit is authorized.

## Validation

All 53 graph builds and icons were reopened and checked. All images resolve. The preceding 1,181 assets retained their identities, graphs, export data, badges and saved icons. Source MaterialLib is unchanged. Installation has a recoverable backup. The production remote listing, shared public packages, user Blender GUI and local pilot server were not changed.
