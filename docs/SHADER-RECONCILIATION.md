# Shader roots and remaining terrain projections

Local revision: **2026.11.23-source-reconciliation-1**.

This follow-up clarifies 94 shader roots, improves ten reviewed array-based terrain/rock previews and LakeBottom, and refreshes their eleven thumbnails. Existing native export links, asset IDs, badges, catalogs, MaterialLib and material counts are retained. No material is promoted out of Preview only.

## Descriptor reconciliation

For 91 materials, the earlier descriptor is reachable through explicit shader references from the material's root descriptor. These are dependent passes, rather than contradictory material identities. The exact material ancestor chain now identifies the root; the earlier descriptor and its dependency path remain available as provenance. Captured shader states are retained as historical pass evidence, not rewritten as though all passes were the root.

Three materials explicitly select **Tech3 Block PyPxzTLayered_NoDecal.Shader.Gbx**: PlatformIce OpenTechBorders, PlatformIce PlatformTech and RoadIce. The previous sibling descriptor included SubsurfaceDecalBaseColor and SubsurfaceDecalBaseColorHueMask addresses plus extra decal defaults. The root identity is corrected; their existing production previews already use the non-decal internal layers, so their graphs and thumbnails are retained. Sharing compiled program filenames or dependent passes does not make these two root descriptors interchangeable. Previously merged parameter metadata may include the sibling's historical defaults; it is not authoritative evidence that a decal branch is active.

`tm_exact_shader_resource` and `tm_exact_shader_chain` identify the explicit root chain. `tm_previous_shader_descriptor`, `tm_shader_descriptor_relation` and `tm_shader_descriptor_dependency_path` preserve the reconciliation evidence. There are now **792 recorded unambiguous root chains**, including the previously recorded 698. These fields do not establish new runtime/export clearance.

## Reviewed array subset

The compiled array shader samples D/R/N with shared source coordinates and interpolates top/side channels in the cosine domain. Its blend uses a clamped cubic smoothstep of the normalized normal components. The reviewed adapter restores material-local image selections, consistent physical texture scale across colour/roughness/normal roles, and the selected layers' angular ranges.

Only rows with positive, equal top/side dimensions and zero rotation/offset fields are adapted here. The interpretation is corroborated by decoded array rows, standalone bitmap scales and compiled buffer/sample operations. Native runtime buffer contents have not been captured; mapped Blender tangent frames remain an approximation. The material's static selectors are used without inventing runtime overrides.

Updated materials:

- `TM_BlueBay_CliffPxz_asset`
- `TM_BlueBay_HillPxz_asset`
- `TM_BlueBay_RocksTop_asset`
- `TM_BlueBay_Sand_asset`
- `TM_BlueBay_SeaFloor_asset`
- `TM_GreenCoast_Cliff2_asset`
- `TM_GreenCoast_Cliff3_asset`
- `TM_GreenCoast_Cliff4_asset`
- `TM_GreenCoast_Cliff_asset`
- `TM_GreenCoast_Lake_asset`

## LakeBottom

RedIsland LakeBottom now samples each colour, roughness and normal channel with its own bitmap transform. Its top colour uses the recorded 72-degree rotation and 1/128 scale; the side colour uses separate horizontal/vertical scales. Both normal descriptors are unrotated with positive scale, so the colour rotation does not require rotating those normal frames. The standard bitmap rotation convention, mapped Blender axes and retained angular adapter are still preview limits.

## Remaining array work

The following 24 materials retain their existing graphs. Their signed/rotated/offset fields, distinct top/side dimensions or height-array packing need further matrix and basis reconstruction. No array-wide unit scale or guessed per-layer transform is installed.

- `TM_BlueBay_Land_asset`
- `TM_BlueBay_TransitionRocksToLand_asset`
- `TM_BlueBay_TransitionToLand_asset`
- `TM_GreenCoast_CliffTransition2ToGrass_asset`
- `TM_GreenCoast_CliffTransitionToGrass_asset`
- `TM_GreenCoast_Grass_asset`
- `TM_GreenCoast_LakeShoreToGrass_asset`
- `TM_GreenCoast_TransitionForestToGrass_asset`
- `TM_RedIsland_Cliff3_asset`
- `TM_RedIsland_DetailsCliffToDirt_asset`
- `TM_RedIsland_DetailsRocksToDirt_asset`
- `TM_RedIsland_DetailsToDirt_asset`
- `TM_RedIsland_DetailsVegetationToDirt_asset`
- `TM_RedIsland_Dirt_asset`
- `TM_RedIsland_DirtRocky_asset`
- `TM_RedIsland_RiverShoreToRiverSide_asset`
- `TM_RedIsland_RiverSide_asset`
- `TM_RedIsland_RockToDirt_asset`
- `TM_WhiteShore_Beach_asset`
- `TM_WhiteShore_Land_asset`
- `TM_WhiteShore_WaterBottom_asset`
- `TM_WhiteShore_WaterShore_asset`
- `TM_WhiteShore_WaterShoreRocky_asset`
- `TM_WhiteShore_WaterShoreToBeach_asset`

## Five unresolved screens

16x9ScreenOff, Ad16x9Screen, PodiumScreen16x9, WarpScreen16x9B and WarpScreen16x9C still have no exact match in the three decoded resource inventories or the unpacked GBX filenames. An additional raw-content search of the unpacked GBX files also found no occurrences; compressed payloads make that supporting evidence incomplete. Nearby 155-format and unsuffixed 16x9 materials exist, but neither names nor similar images prove an exact alias. Existing screen graphs and export aliases are retained. Runtime name lookup or additional official resource mappings are required before substitution.

## Using the update

Append a fresh copy of an updated material from the library. Existing copies inside a scene retain their previous nodes. Keep the existing BaseMaterial UV and vertex-alpha requirements where applicable. The updated library contains eleven refreshed 3D thumbnails; established badge pixels and meanings are unchanged.

Offline preservation checks and numeric Blender render fixtures passed. The game was not started and no new in-game tests are claimed. This follow-up is included in both combined full packages with content revision `2026.11.24-thumbnail-styles-2`.

The complete per-material root/dependency evidence and deferred array rows are retained in the [reviewed input data](../tools/data/source-reconciliation-inputs.json).

## Maintenance

`tools/prepare_source_reconciliation.py` accepts `--native-workspace`, `--prior-inputs`, `--audit`, `--library` (asset folder) and `--output`. It follows explicit shader dependency references and retains ambiguous array rows as research data. Reviewed inputs are in `tools/data/source-reconciliation-inputs.json`.

Run `apply_source_reconciliation.py` in background Blender with `--library`, `--inputs`, `--secondary` (a JSON object with an empty targets list for this revision) and `--output`. Verify using `verify_source_reconciliation.py` with `--original`, `--staged`, `--inputs`, `--output`, and `verify_reconciled_projection_formulas.py` with `--output`. The installer checks the baseline hash before making a recoverable replacement. A later revision requires newly reviewed inputs and a new baseline hash.
