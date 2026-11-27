# Ingame colorpicker materials

The **red paintbrush badge** identifies an explicit native `CPlugMaterialColorTargetTable` binding. The audit found **86 current library materials**: Stadium 62 and six in each vista. All 86 are in Materials Only; Complete retains the same native-linked entries. Counts and export classification are unchanged.

The item/block colorpicker selects a color index. The native table maps that index to a material-specific palette, and the shader/masks determine which parts change. This does not promise arbitrary RGB replacement, a complete surface recolor, or that changing a Blender color node changes the exported game palette. NoColorize names, fixed Hue targets and vertex colors are not used as evidence.

Evidence: all985 decoded native materials and all1172 library entries were checked, including material-parent chains. Nine referenced table files were opened and verified as valid five-slot native palettes. There are109 native material resources with a table reference;23 have no standalone corresponding library entry and are listed separately below. No new per-material game colorpicker test was performed.

## Publication status

Remote extension **1.0.7** now publishes the red paintbrush redesign after independent verification. Both offline editions are being updated.

Remote extension **1.0.6** is published and independently verified with all 86 brush badges. Both offline editions now publish revision `2026.11.27-colorpicker-badges-1` with the same86 badges after isolated installer and independent public-file verification.

## Full list of current library materials

### Stadium (62)

| Blender asset | Color table | Native material source |
| --- | --- | --- |
| `TM_Canopy_asset` | `Canopy`, `TrackWall` | `Stadium/Media/Material/Canopy.Material.Gbx` |
| `TM_CanopyGlass_asset` | `Canopy` | `Stadium/Media/Material/CanopyGlass.Material.Gbx` |
| `TM_CanopyStructure_asset` | `CanopyStructure`, `TrackWall` | `Stadium/Media/Material/CanopyStructure.Material.Gbx` |
| `TM_CustomModColorize2_asset` | `SportObstacles` | `Stadium/Media/Material_BlockCustom/CustomModColorize2.Material.Gbx` |
| `TM_CustomModColorize_asset` | `SportObstacles` | `Stadium/Media/Material_BlockCustom/CustomModColorize.Material.Gbx` |
| `TM_DecalCurbs_asset` | `SportDecals` | `Stadium/Media/Material/DecalCurbs.Material.Gbx` |
| `TM_DecalMarksItems_asset` | `SportDecals` | `Stadium/Media/Material/DecalMarksItems.Material.Gbx` |
| `TM_DecalMarksStart_asset` | `Sport` | `Stadium/Media/Material/DecalMarksStart.Material.Gbx` |
| `TM_DecalPaint2Sponsor4x1A_asset` | `SportDecals2` | `Stadium/Media/Material/DecalPaint2Sponsor4x1A.Material.Gbx` |
| `TM_DecalPaint2Sponsor4x1B_asset` | `SportDecals2` | `Stadium/Media/Material/DecalPaint2Sponsor4x1B.Material.Gbx` |
| `TM_DecalPaint2Sponsor4x1C_asset` | `SportDecals2` | `Stadium/Media/Material/DecalPaint2Sponsor4x1C.Material.Gbx` |
| `TM_DecalPaint2Sponsor4x1D_asset` | `SportDecals2` | `Stadium/Media/Material/DecalPaint2Sponsor4x1D.Material.Gbx` |
| `TM_DecalPaintLogo8x1Colorize_asset` | `SportDecals` | `Stadium/Media/Material/DecalPaintLogo8x1Colorize.Material.Gbx` |
| `TM_DecalPaintSponsor4x1A_asset` | `SportDecals` | `Stadium/Media/Material/DecalPaintSponsor4x1A.Material.Gbx` |
| `TM_DecalPaintSponsor4x1B_asset` | `SportDecals` | `Stadium/Media/Material/DecalPaintSponsor4x1B.Material.Gbx` |
| `TM_DecalPaintSponsor4x1C_asset` | `SportDecals` | `Stadium/Media/Material/DecalPaintSponsor4x1C.Material.Gbx` |
| `TM_DecalPaintSponsor4x1D_asset` | `SportDecals` | `Stadium/Media/Material/DecalPaintSponsor4x1D.Material.Gbx` |
| `TM_DecalPlatform_asset` | `Sport` | `Stadium/Media/Material/DecalPlatform.Material.Gbx` |
| `TM_DecoCliffBase_asset` | `TrackWall` | `Stadium/Media/Material/DecoCliffBase.Material.Gbx` |
| `TM_ItemFlagNoAnim_asset` | `SportObstacles` | `Stadium/Media/Material/ItemFlagNoAnim.Material.Gbx` |
| `TM_ItemInflatableFloor_asset` | `Fun` | `Stadium/Media/Material/ItemInflatableFloor.Material.Gbx` |
| `TM_ItemInflatableMat_asset` | `Fun` | `Stadium/Media/Material/ItemInflatableMat.Material.Gbx` |
| `TM_ItemInflatableTube_asset` | `Fun` | `Stadium/Media/Material/ItemInflatableTube.Material.Gbx` |
| `TM_ItemPillar2_asset` | `SportObstacles` | `Stadium/Media/Material/ItemPillar2.Material.Gbx` |
| `TM_ItemPillar_asset` | `SportObstacles` | `Stadium/Media/Material/ItemPillar.Material.Gbx` |
| `TM_ItemRamp_asset` | `SportObstacles` | `Stadium/Media/Material/ItemRamp.Material.Gbx` |
| `TM_ItemSupportTube_asset` | `SportObstacles` | `Stadium/Media/Material/ItemSupportTube.Material.Gbx` |
| `TM_ItemTrackBarrier2_asset` | `SportObstacles` | `Stadium/Media/Material/ItemTrackBarrier2.Material.Gbx` |
| `TM_ItemTrackBarrier_asset` | `SportObstacles` | `Stadium/Media/Material/ItemTrackBarrier.Material.Gbx` |
| `TM_ItemTrackBarrierB_asset` | `SportObstacles` | `Stadium/Media/Material/ItemTrackBarrierB.Material.Gbx` |
| `TM_ItemTrackBarrierC_asset` | `SportObstacles` | `Stadium/Media/Material/ItemTrackBarrierC.Material.Gbx` |
| `TM_OpenTechBorders_asset` | `Sport` | `Stadium/Media/Material/OpenTechBorders.Material.Gbx` |
| `TM_PlatformDirt_DecalPlatform_asset` | `Sport` | `Stadium/Media/Modifier/PlatformDirt/DecalPlatform.Material.Gbx` |
| `TM_PlatformDirt_DecoCliffBase_asset` | `TrackWall` | `Stadium/Media/Modifier/PlatformDirt/DecoCliffBase.Material.Gbx` |
| `TM_PlatformDirt_OpenTechBorders_asset` | `Sport` | `Stadium/Media/Modifier/PlatformDirt/OpenTechBorders.Material.Gbx` |
| `TM_PlatformGrass_DecalPlatform_asset` | `Sport` | `Stadium/Media/Modifier/PlatformGrass/DecalPlatform.Material.Gbx` |
| `TM_PlatformGrass_OpenTechBorders_asset` | `Sport` | `Stadium/Media/Modifier/PlatformGrass/OpenTechBorders.Material.Gbx` |
| `TM_PlatformIce_DecalPlatform_asset` | `Sport` | `Stadium/Media/Modifier/PlatformIce/DecalPlatform.Material.Gbx` |
| `TM_PlatformIce_DecoCliffBase_asset` | `TrackWall` | `Stadium/Media/Modifier/PlatformIce/DecoCliffBase.Material.Gbx` |
| `TM_PlatformIce_OpenTechBorders_asset` | `Sport` | `Stadium/Media/Modifier/PlatformIce/OpenTechBorders.Material.Gbx` |
| `TM_PlatformPlastic_DecalPlatform_asset` | `Fun` | `Stadium/Media/Modifier/PlatformPlastic/DecalPlatform.Material.Gbx` |
| `TM_PlatformPlastic_PlatformTech_asset` | `Fun` | `Stadium/Media/Modifier/PlatformPlastic/PlatformTech.Material.Gbx` |
| `TM_RoadBump_asset` | `Sport` | `Stadium/Media/Material/RoadBump.Material.Gbx` |
| `TM_RoadDirt_asset` | `Sport` | `Stadium/Media/Material/RoadDirt.Material.Gbx` |
| `TM_RoadDirtFullColorize_asset` | `Sport` | `Stadium/Media/Material/RoadDirtFullColorize.Material.Gbx` |
| `TM_RoadIce_asset` | `Sport` | `Stadium/Media/Material/RoadIce.Material.Gbx` |
| `TM_RoadTech_asset` | `Sport` | `Stadium/Media/Material/RoadTech.Material.Gbx` |
| `TM_Stadium_StructureTruss_asset` | `Sport` | `Stadium/Media/Material/StructureTruss.Material.Gbx` |
| `TM_Stadium_TechnicsStepLow_asset` | `SportObstacles` | `Stadium/Media/Material/TechnicsStepLow.Material.Gbx` |
| `TM_Stadium_ThemeDesertBarrier_asset` | `Sport` | `Stadium/Media/Material/ThemeDesertBarrier.Material.Gbx` |
| `TM_Structure_asset` | `Sport` | `Stadium/Media/Material/Structure.Material.Gbx` |
| `TM_Technics_asset` | `SportObstacles` | `Stadium/Media/Material/Technics.Material.Gbx` |
| `TM_TechnicsStep_asset` | `SportObstacles` | `Stadium/Media/Material/TechnicsStep.Material.Gbx` |
| `TM_TechnicsTrimsColorize_asset` | `SportObstacles` | `Stadium/Media/Material/TechnicsTrimsColorize.Material.Gbx` |
| `TM_ThemeRallyCastleRoof_asset` | `Sport` | `Stadium/Media/Material/ThemeRallyCastleRoof.Material.Gbx` |
| `TM_ThemeSnowRoadBorder_asset` | `Sport` | `Stadium/Media/Material/ThemeSnowRoadBorder.Material.Gbx` |
| `TM_ThemeSnowTempleDetails_asset` | `Sport` | `Stadium/Media/Material/ThemeSnowTempleDetails.Material.Gbx` |
| `TM_ThemeSnowTempleFloor_asset` | `TrackWall` | `Stadium/Media/Material/ThemeSnowTempleFloor.Material.Gbx` |
| `TM_TrackBorders_asset` | `SportIllum` | `Stadium/Media/Material/TrackBorders.Material.Gbx` |
| `TM_TrackBordersOff_asset` | `Sport` | `Stadium/Media/Material/TrackBordersOff.Material.Gbx` |
| `TM_TrackWall_asset` | `TrackWall` | `Stadium/Media/Material/TrackWall.Material.Gbx` |
| `TM_TrackWallClips_asset` | `Sport` | `Stadium/Media/Material/TrackWallClips.Material.Gbx` |

### BlueBay (6)

| Blender asset | Color table | Native material source |
| --- | --- | --- |
| `TM_Stadium_StructureInWorld_asset` | `Sport` | `BlueBay/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` |
| `TM_Stadium_TrackBordersInWorld_asset` | `SportIllum` | `BlueBay/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` |
| `TM_Stadium_TrackWallClipsInWorld_asset` | `Sport` | `BlueBay/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` |
| `TM_BlueBay_DecalPaint2Sponsor4x1D_asset` | `SportDecals2` | `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` |
| `TM_BlueBay_DecalPaintSponsor4x1D_asset` | `SportDecals` | `BlueBay/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` |
| `TM_BlueBay_TrackBordersOffInWorld_asset` | `Sport` | `BlueBay/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` |

### GreenCoast (6)

| Blender asset | Color table | Native material source |
| --- | --- | --- |
| `TM_GreenCoast_DecalPaint2Sponsor4x1D_asset` | `SportDecals2` | `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` |
| `TM_GreenCoast_DecalPaintSponsor4x1D_asset` | `SportDecals` | `GreenCoast/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` |
| `TM_GreenCoast_StructureInWorld_asset` | `Sport` | `GreenCoast/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` |
| `TM_GreenCoast_TrackBordersInWorld_asset` | `SportIllum` | `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` |
| `TM_GreenCoast_TrackBordersOffInWorld_asset` | `Sport` | `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` |
| `TM_GreenCoast_TrackWallClipsInWorld_asset` | `Sport` | `GreenCoast/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` |

### RedIsland (6)

| Blender asset | Color table | Native material source |
| --- | --- | --- |
| `TM_RedIsland_DecalPaint2Sponsor4x1D_asset` | `SportDecals2` | `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` |
| `TM_RedIsland_DecalPaintSponsor4x1D_asset` | `SportDecals` | `RedIsland/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` |
| `TM_RedIsland_StructureInWorld_asset` | `Sport` | `RedIsland/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` |
| `TM_RedIsland_TrackBordersInWorld_asset` | `SportIllum` | `RedIsland/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` |
| `TM_RedIsland_TrackBordersOffInWorld_asset` | `Sport` | `RedIsland/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` |
| `TM_RedIsland_TrackWallClipsInWorld_asset` | `Sport` | `RedIsland/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` |

### WhiteShore (6)

| Blender asset | Color table | Native material source |
| --- | --- | --- |
| `TM_WhiteShore_DecalPaint2Sponsor4x1D_asset` | `SportDecals2` | `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaint2Sponsor4x1D.Material.Gbx` |
| `TM_WhiteShore_DecalPaintSponsor4x1D_asset` | `SportDecals` | `WhiteShore/Media/Modifier/StadiumOnTerrain/DecalPaintSponsor4x1D.Material.Gbx` |
| `TM_WhiteShore_StructureInWorld_asset` | `Sport` | `WhiteShore/Media/Modifier/StadiumOnTerrain/StructureInWorld.Material.Gbx` |
| `TM_WhiteShore_TrackBordersInWorld_asset` | `SportIllum` | `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackBordersInWorld.Material.Gbx` |
| `TM_WhiteShore_TrackBordersOffInWorld_asset` | `Sport` | `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackBordersOffInWorld.Material.Gbx` |
| `TM_WhiteShore_TrackWallClipsInWorld_asset` | `Sport` | `WhiteShore/Media/Modifier/StadiumOnTerrain/TrackWallClipsInWorld.Material.Gbx` |

## Native sources without a separate library entry (23)

These are source coverage findings, not new assets or newly confirmed export aliases. They are not substituted for existing materials.

- `Stadium/Media/Modifier/Reset/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/DecalSponsor4x1DOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/SlowMotion/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Cruise/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Fragile/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/TurboRoulette/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Turbo2/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/DecalMarksStartOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/NoSteering/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/DecalSponsor4x1AOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/StructureNoSkin.Material.Gbx`
- `Stadium/Media/Modifier/NoEngine/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/ItemFlag.Material.Gbx`
- `Stadium/Media/Material/DecalSponsor4x1COnRoadIce.Material.Gbx`
- `Stadium/Media/Material/StructureTrussTransparent.Material.Gbx`
- `Stadium/Media/Material/RoadTechSubIce.Material.Gbx`
- `Stadium/Media/Material/DecalMarksOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/DecalSponsor4x1BOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Boost2/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Boost/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/Turbo/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Modifier/NoBrake/DecalOnRoadIce.Material.Gbx`
- `Stadium/Media/Material/TrackWallClipsNoSkin.Material.Gbx`
