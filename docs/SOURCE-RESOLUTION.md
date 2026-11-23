# Exact shader source resolution

Local revision: **2026.11.23-projection-sources-1**.

Following the actual native material ancestor references recovered **88 previously missing exact shader descriptor links**. In particular, the PyPxzDiff_Spec_Norm base material explicitly names its PC3 descriptor; this is a recorded reference, not an inferred substitute. Native export links were not changed.

The library records 698 unambiguous ancestor chains in `tm_exact_shader_resource` and `tm_exact_shader_chain`. These are provenance fields, not new asset badges. A known descriptor does not prove that its complete rendering behavior is implemented.

## Remaining gaps

- 94 ancestor chains differ from previously captured shader descriptors. Their existing captured evidence and graphs are retained; the new chains are kept in the research data for reconciliation. They are not silently promoted as a new exact identity.
- Five legacy screen aliases remain unresolved: 16x9ScreenOff, Ad16x9Screen, PodiumScreen16x9, WarpScreen16x9B and WarpScreen16x9C. The three decoded resource inventories and unpacked material names provided no exact hit. Their game links are unchanged.
- Texture-only reference assets do not acquire a fictitious unique material shader.
- Array layer selectors, physical scale/angle field semantics and rotated normal frames need further work. Array-wide unit scale is not accepted as an exact per-layer transform.

## Newly recovered descriptor links

| Material | Exact referenced descriptor |
| --- | --- |
| `TM_BlueBay_Deco_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_BlueBay_TransitionRocks_asset` | `Techno3/Media/Shader/Tech3 Block TDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_Boost2_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Boost2_Decal_ColorBlindness_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Boost_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Boost_Decal_ColorBlindness_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Canopy_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_Cruise_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_CustomModDecal2_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_CustomModDecal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_CustomModTrans2_asset` | `Techno3/Media/Shader/Tech3 Block TDiffA_Spec_Norm PC3.Shader.Gbx` |
| `TM_CustomModTrans_asset` | `Techno3/Media/Shader/Tech3 Block TDiffA_Spec_Norm PC3.Shader.Gbx` |
| `TM_DecalCurbs_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalGateGameplay_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalMarks_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalMarksItems_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalMarksRamp_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalMarksStart_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalObstaclePusher_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalObstacleTube_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalObstacleTurnstileLeft_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalObstacleTurnstileRight_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalPlatform_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalSpecialTurbo_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecalSponsor1x1BigA_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_DecoCliff_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_Fragile_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_GateGameplayDesert_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_GateGameplayRally_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_GateGameplaySnow_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Grass_asset` | `Techno3/Media/Shader/Tech3 Block PDiff_Spec_Norm GrassX2 PC3.Shader.Gbx` |
| `TM_GreenCoast_Deco_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_GreenCoast_LakeRocks_asset` | `Techno3/Media/Shader/Tech3 Block TDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_GreenCoast_TreeBranch_asset` | `Techno3/Media/Shader/Tech3 Block TDiffA_Spec_Norm PC3.Shader.Gbx` |
| `TM_GreenCoast_Trees2_asset` | `Techno3/Media/Shader/Tech3 Block TreeSprite PC3.Shader.Gbx` |
| `TM_GreenCoast_TrunkA_asset` | `Techno3/Media/Shader/Tech3 Block PxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_Invisible_Asphalt_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Concrete_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Dirt_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Grass_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Green_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Ice_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Metal_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_MetalTrans_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_NotCollidable_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Pavement_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Plastic_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_ResonantMetal_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_RoadIce_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_RoadSynthetic_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Rock_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Rubber_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Sand_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Snow_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_TechMagnetic_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_TechMagneticAccel_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_TechSuperMagnetic_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_Invisible_Wood_asset` | `Effects/Media/Shader/Invisible.Shader.Gbx` |
| `TM_NoBrake_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_NoEngine_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_NoEngine_Decal_ColorBlindness_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_NoSteering_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_PlatformDirt_DecalPlatform_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_PlatformDirt_DecoCliff_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_PlatformGrass_DecalPlatform_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_PlatformGrass_DecoCliff_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_PlatformGrass_PlatformTech_asset` | `Techno3/Media/Shader/Tech3 Block TDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_PlatformIce_DecalPlatform_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_PlatformIce_DecoCliff_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_PlatformPlastic_DecalPlatform_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_RedIsland_Deco_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_RedIsland_DetailsRocks2_asset` | `Techno3/Media/Shader/Tech3 Block TDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_RedIsland_DetailsRocks3_asset` | `Techno3/Media/Shader/Tech3 Block TDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_RedIsland_LakeBottom_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_RedIsland_WaterGround_asset` | `Techno3/Media/Shader/Tech3 Block PDiff_Spec_Norm GrassX2 PC3.Shader.Gbx` |
| `TM_Reset_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_SlowMotion_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_Stadium_DecalSpecialMarks_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_ThemeRallyCastleBordersTransparent_asset` | `Techno3/Media/Shader/Tech3 Block TDiffA_Spec_Norm PC3.Shader.Gbx` |
| `TM_ThemeRallyCastleWall_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_ThemeSnowTempleTransparent_asset` | `Techno3/Media/Shader/Tech3 Block TDiffA_Spec_Norm PC3.Shader.Gbx` |
| `TM_Turbo2_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_TurboRoulette_Decal_asset` | `Techno3/Media/Shader/Tech3 DeferredDecal.Shader.Gbx` |
| `TM_WarpGrass2_asset` | `Techno3/Media/Shader/Tech3 Block PDiff_Spec_Norm GrassX2 PC3.Shader.Gbx` |
| `TM_WarpGrass_asset` | `Techno3/Media/Shader/Tech3 Block PDiff_Spec_Norm GrassX2 PC3.Shader.Gbx` |
| `TM_WarpLight_Dyna_asset` | `Techno3/Media/Shader/Tech3 Block TSelfIllum PC3.Shader.Gbx` |
| `TM_Waterground_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |
| `TM_WhiteShore_Deco_asset` | `Techno3/Media/Shader/Tech3 Block PyPxzDiff_Spec_Norm PC3.Shader.Gbx` |

## Projected previews updated

- `TM_Canopy_asset`
- `TM_CustomBricks_asset`
- `TM_CustomConcrete_asset`
- `TM_CustomDirt_asset`
- `TM_CustomGrass_asset`
- `TM_CustomIce_asset`
- `TM_CustomMetal_asset`
- `TM_CustomMetalPainted_asset`
- `TM_CustomPlastic_asset`
- `TM_CustomPlasticShiny_asset`
- `TM_CustomRock_asset`
- `TM_CustomRoughWood_asset`
- `TM_CustomSand_asset`
- `TM_CustomSnow_asset`
- `TM_DecoCliff_asset`
- `TM_DecoHill2_asset`
- `TM_DecoHill_asset`
- `TM_PlatformDirt_DecoCliff_asset`
- `TM_PlatformDirt_DecoGrass_asset`
- `TM_PlatformDirt_DecoHill2_asset`
- `TM_PlatformDirt_DecoHill_asset`
- `TM_PlatformGrass_DecoCliff_asset`
- `TM_PlatformIce_DecoCliff_asset`
- `TM_PlatformIce_DecoGrass_asset`
- `TM_PlatformIce_DecoHill2_asset`
- `TM_PlatformIce_DecoHill_asset`
- `TM_RoadDirt_asset`
- `TM_RoadDirtFullColorize_asset`
- `TM_ThemeRallyCastleWall_asset`
- `TM_TrackWall_asset`
- `TM_Waterground_asset`
