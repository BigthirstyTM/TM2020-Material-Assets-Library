# Updated material previews

Local thumbnail revision `2026.11.26-terrain-insets-2` updates 37 layered terrain icons with the approved higher-block, diffuse-inset and soft-shadow layout. The inset source now follows the active UV decoration or projected-top shader input; 25 stale source paths are corrected. Material graphs, native bindings and badge pixels are unchanged. See [thumbnail styles](THUMBNAIL-STYLES.md). This local icon update is not yet in the full ZIPs or remote pilot.

Published full-package revision `2026.11.26-shader-followup-1` updates 555 unique graphs across five shader-informed groups. See [UV/grass/display depth/terrain/colour controls and limits](SHADER-FOLLOWUP.md) and the [complete per-group material list](SHADER-FOLLOWUP-MATERIALS.md). Native export identities, badges and thumbnail artwork are preserved. Both ZIP editions include these changes; the remote pilot remains unchanged.

The included Dyna revision `2026.11.26-dyna-preview-1` adds [Dyna source analysis and preview corrections](DYNA-MATERIALS.md). Six material graphs were corrected; three related WarpDetails entries received source-provenance metadata. These Dyna changes are included in the current ZIPs; the remote pilot remains unchanged.

Both published full-package editions now contain `2026.11.26-shader-followup-1`. Each edition has two ZIPs; release checksums and public downloads have been verified. Check `release.json` or the installed `library.json` for the revision of your package.

The new packages include 843 flat/composed tiles with correct image/frame proportions: 341 rectangular images fit without stretching and 502 square tiles fill the canvas. They include restored emissive sign/light previews, slightly brighter active screens, flat CustomMod defaults, and 13 Custom spheres with enlarged texture detail. ItemObstacle last-frame icons and 21 clock time-step labels are restored. Vegetation, water/glass previews and existing feature badges are retained. See [thumbnail styles](THUMBNAIL-STYLES.md).

Both editions also include the 183 corrections below, [projected surface updates](PROJECTED-SURFACES.md), [shader reconciliation](SHADER-RECONCILIATION.md), and [catalog cleanup and AnimatedFlag quarantine](CATALOG-CLARITY.md). These changes do not imply new in-game tests or an identical native renderer.

Content revision: `2026.11.23-native-surfaces-1`. These 183 material previews received the following corrections. Counts overlap. Native links and edition membership remain unchanged. See [usage and limits](CONCRETE-SHADER-CORRECTIONS.md).

## F01 ? Removed RoughMetal blue-to-specular connection

163 materials.

- `TM_Boost2_Decal_ColorBlindness_asset` ? Preview only.
- `TM_Boost2_Decal_asset`
- `TM_Boost_Decal_ColorBlindness_asset` ? Preview only.
- `TM_Boost_Decal_asset`
- `TM_Cruise_Decal_asset`
- `TM_CustomBricks_asset`
- `TM_CustomConcrete_asset`
- `TM_CustomDirt_asset`
- `TM_CustomGrass_asset`
- `TM_CustomIce_asset`
- `TM_CustomMetalPainted_asset`
- `TM_CustomMetal_asset`
- `TM_CustomModColorize2_asset`
- `TM_CustomModColorize_asset`
- `TM_CustomModDecal2_asset`
- `TM_CustomModDecal_asset`
- `TM_CustomModOpaque2_asset`
- `TM_CustomModOpaque_asset`
- `TM_CustomModSelfIllumSimple2_asset`
- `TM_CustomModSelfIllumSimple_asset`
- `TM_CustomPlasticShiny_asset`
- `TM_CustomPlastic_asset`
- `TM_CustomRock_asset`
- `TM_CustomRoughWood_asset`
- `TM_CustomSand_asset`
- `TM_CustomSnow_asset`
- `TM_DecalCurbs_asset`
- `TM_DecalGateGameplay_asset`
- `TM_DecalMarksItems_asset`
- `TM_DecalMarksRamp_asset`
- `TM_DecalMarksStart_asset`
- `TM_DecalMarks_asset`
- `TM_DecalObstaclePusher_asset`
- `TM_DecalObstacleTube_asset`
- `TM_DecalObstacleTurnstileLeft_asset`
- `TM_DecalObstacleTurnstileRight_asset`
- `TM_DecalPaint2Logo4x1_asset`
- `TM_DecalPaint2Logo8x1_asset`
- `TM_DecalPaint2Sponsor4x1A_asset`
- `TM_DecalPaint2Sponsor4x1B_asset`
- `TM_DecalPaint2Sponsor4x1C_asset`
- `TM_DecalPaint2Sponsor4x1D_asset`
- `TM_DecalPaint2Sponsor4x1NoColorizeA_asset`
- `TM_DecalPaint2Sponsor4x1NoColorizeB_asset`
- `TM_DecalPaint2Sponsor4x1NoColorizeC_asset`
- `TM_DecalPaint2Sponsor4x1NoColorizeD_asset`
- `TM_DecalPaintLogo4x1_asset`
- `TM_DecalPaintLogo8x1Colorize_asset`
- `TM_DecalPaintLogo8x1_asset`
- `TM_DecalPaintSponsor4x1A_asset`
- `TM_DecalPaintSponsor4x1B_asset`
- `TM_DecalPaintSponsor4x1C_asset`
- `TM_DecalPaintSponsor4x1D_asset`
- `TM_DecalPaintSponsor4x1NoColorizeA_asset`
- `TM_DecalPaintSponsor4x1NoColorizeB_asset`
- `TM_DecalPaintSponsor4x1NoColorizeC_asset`
- `TM_DecalPaintSponsor4x1NoColorizeD_asset`
- `TM_DecalPlatform_asset`
- `TM_DecalSpecialTurbo_asset`
- `TM_DecalSponsor1x1BigA_asset`
- `TM_Fragile_Decal_asset`
- `TM_GateGameplayDesert_Decal_asset`
- `TM_GateGameplayRally_Decal_asset`
- `TM_GateGameplaySnow_Decal_asset`
- `TM_GlossyFloor_asset`
- `TM_ItemBase_asset`
- `TM_ItemBorder_asset`
- `TM_ItemCactus_asset`
- `TM_ItemFlagNoAnim_asset`
- `TM_ItemFlag_animated_asset`
- `TM_ItemInflatableFloor_asset`
- `TM_ItemInflatableMat_asset`
- `TM_ItemInflatableTube_asset`
- `TM_ItemLamp_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstacleLevel0_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstacleLevel1_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstacleLevel2_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstaclePusherLevel0_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstaclePusherLevel1_asset`
- `TM_ItemObstacleDiscontinuous_ItemObstaclePusherLevel2_asset`
- `TM_ItemObstaclePusher_asset`
- `TM_ItemObstacle_ItemObstacleLevel0_asset`
- `TM_ItemObstacle_ItemObstacleLevel1_asset`
- `TM_ItemObstacle_ItemObstacleLevel2_asset`
- `TM_ItemObstacle_ItemObstaclePusherLevel0_asset`
- `TM_ItemObstacle_ItemObstaclePusherLevel1_asset`
- `TM_ItemObstacle_ItemObstaclePusherLevel2_asset`
- `TM_ItemObstacle_asset`
- `TM_ItemPillar2_asset`
- `TM_ItemPillar_asset`
- `TM_ItemRamp_asset`
- `TM_ItemRoadSign_asset`
- `TM_ItemSpectatorLow_asset`
- `TM_ItemSpectator_asset`
- `TM_ItemSupportConnector_asset`
- `TM_ItemSupportTube_asset`
- `TM_ItemTrackBarrier2_asset`
- `TM_ItemTrackBarrierB_asset`
- `TM_ItemTrackBarrierC_asset`
- `TM_ItemTrackBarrier_asset`
- `TM_LightTubeBig_asset`
- `TM_LightTubeSmall_asset`
- `TM_NoBrake_Decal_asset`
- `TM_NoEngine_Decal_ColorBlindness_asset` ? Preview only.
- `TM_NoEngine_Decal_asset`
- `TM_NoSteering_Decal_asset`
- `TM_OpenTechBorders_asset`
- `TM_PlatformDirt_DecalPlatform_asset`
- `TM_PlatformDirt_OpenTechBorders_asset`
- `TM_PlatformGrass_DecalPlatform_asset`
- `TM_PlatformGrass_OpenTechBorders_asset`
- `TM_PlatformPlastic_DecalPlatform_asset`
- `TM_PlatformTech_asset`
- `TM_PodiumMedalMetal_asset`
- `TM_PodiumSelfIllum_asset`
- `TM_Pylon_asset`
- `TM_Reset_Decal_asset`
- `TM_RoadBump_asset`
- `TM_RoadDirtFullColorize_asset`
- `TM_RoadDirt_asset`
- `TM_RoadIce_asset`
- `TM_RoadTech_asset`
- `TM_ScreenBack_asset`
- `TM_SlowMotion_Decal_asset`
- `TM_SpeakerFront_asset`
- `TM_SpeakerSide_asset`
- `TM_SpeedometerLight_Dyna_asset`
- `TM_SpeedometerLight_asset`
- `TM_Speedometer_asset`
- `TM_Stadium_TechnicsStepLow_asset`
- `TM_Structure_asset`
- `TM_TechnicsSpecials_asset`
- `TM_TechnicsStep_asset`
- `TM_TechnicsTrimsColorize_asset`
- `TM_TechnicsTrims_asset`
- `TM_Technics_asset`
- `TM_ThemeRallyBarrier_asset`
- `TM_ThemeRallyCastleBorders_asset`
- `TM_ThemeRallyCastleRoof_asset`
- `TM_ThemeRallyCastleWallUV_asset`
- `TM_ThemeSnowRoadBorder_asset`
- `TM_ThemeSnowRoad_asset`
- `TM_ThemeSnowTempleDetails_asset`
- `TM_ThemeSnowTempleFloor_asset`
- `TM_TrackWallClips_asset`
- `TM_TrackWall_asset`
- `TM_Turbo2_Decal_asset`
- `TM_TurboRoulette_Decal_asset`
- `TM_Underwater_asset`
- `TM_WarpCeiling_WithLightmap_asset`
- `TM_WarpCeiling_asset` ? Preview only.
- `TM_WarpDetails_Dyna_asset`
- `TM_WarpDetails_WithLightmap_asset`
- `TM_WarpDetails_asset` ? Preview only.
- `TM_WarpLight_Dyna_asset`
- `TM_WarpTechnic_WithLightmap_asset`
- `TM_WarpTechnic_asset` ? Preview only.
- `TM_WarpWall2Bottom_asset`
- `TM_WarpWall2_WithLightmap_asset`
- `TM_WarpWall2_asset` ? Preview only.
- `TM_WarpWall_WithLightmap_asset`
- `TM_WarpWall_asset` ? Preview only.
- `TM_WaterBorders_asset`

## F02 ? Recovered remaining mixed terrain UV overlays

4 materials.

- `TM_GreenCoast_TrunkToGrass_asset`
- `TM_RoadDirtFullColorize_asset`
- `TM_RoadDirt_asset`
- `TM_TrackWall_asset`

## F03 ? Restored RoadIce surface mask and independent inner colour

1 materials.

- `TM_RoadIce_asset`

## F04 ? Restored sampled internal ice depth

1 materials.

- `TM_PlatformIce_OpenTechBorders_asset`

## F05 ? Restored CustomRock top/side texture families

1 materials.

- `TM_CustomRock_asset`

## F06 ? Applied native Custom Hue chroma/grey formula

13 materials.

- `TM_CustomBricks_asset`
- `TM_CustomConcrete_asset`
- `TM_CustomDirt_asset`
- `TM_CustomGrass_asset`
- `TM_CustomIce_asset`
- `TM_CustomMetalPainted_asset`
- `TM_CustomMetal_asset`
- `TM_CustomPlasticShiny_asset`
- `TM_CustomPlastic_asset`
- `TM_CustomRock_asset`
- `TM_CustomRoughWood_asset`
- `TM_CustomSand_asset`
- `TM_CustomSnow_asset`

## F07 ? Restored native macro modulation

9 materials.

- `TM_CustomConcrete_asset`
- `TM_CustomDirt_asset`
- `TM_CustomGrass_asset`
- `TM_CustomRock_asset`
- `TM_CustomSnow_asset`
- `TM_PlatformDirt_PlatformTech_asset`
- `TM_RoadDirtFullColorize_asset`
- `TM_RoadDirt_asset`
- `TM_TrackWall_asset`

## F08 ? Restored environment top/side texture families

2 materials.

- `TM_GreenCoast_TrackWallInWorld_asset`
- `TM_RedIsland_LakeBottom_asset`

## F09 ? Resolved TrackBorders source identity and restored layers

1 materials.

- `TM_Stadium_TrackBordersInWorld_asset`

## F10 ? Restored DetailsToDirt native base and overlay

1 materials.

- `TM_RedIsland_DetailsToDirt_asset`

## F11 ? Restored source screen normal image

12 materials.

- `TM_WarpScreen155B_asset`
- `TM_WarpScreen155C_asset`
- `TM_WarpScreen155_asset`
- `TM_WarpScreen16x9_asset`
- `TM_WarpScreen1x4A_asset`
- `TM_WarpScreen2x1A_asset`
- `TM_WarpScreen2x3A_asset`
- `TM_WarpScreen2x3B_asset`
- `TM_WarpScreen4x1A_asset`
- `TM_WarpScreen4x1B_asset`
- `TM_WarpScreenBench16x1_asset`
- `TM_WarpScreenBench8x1_asset`

## F12 ? Restored GrassFence colour/alpha layers

1 materials.

- `TM_Stadium_GrassFence_asset`
