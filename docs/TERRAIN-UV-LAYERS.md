# Terrain UV detail and transition layers

Local source revision: `2026.11.26-terrain-uv-layers-1`.
The published full ZIPs remain `2026.11.26-shader-followup-1`; the remote pilot is unchanged.

Fifteen existing environment materials were missing their UV detail layer. The
array reconstruction retained `TBaseColorOp`, `TRoughMetal` and `TNormal` in its
source records, but the terrain adapter recognised only `TBaseColor`. As a result,
different transition materials could show only the same underlying terrain.

The correction retains the existing projected top, sides and macro layers and
adds the source UV detail after them. The compiled `Block_PyPxz_ids_DefWrite_p`
shader samples colour/opacity, roughness/metal and normals using the same UVs.
Its blend weight is `TBaseColorOp.alpha * vertex alpha`. The same weight blends
all three surface properties. Normal vectors are blended and normalised in the
existing Blender normal frame adapter.

`BaseMaterial` supplies authored mesh UVs. The compiled vertex shader passes
these UVs unchanged; the texture resource's mapping-scale hints are not applied
again. This matters for WhiteShore, where applying a second 1/32 scale would hide
the transition mask. The shader permutations either supply constant alpha 1 or
pass vertex colour alpha.

## Controls

The existing **Deco native layer controls** group retains its controls:

- **Fallback alpha**: strength when **Use painted vertex alpha** is 0; default 1.
- **Use painted vertex alpha**: set to 1 to read alpha from the `Color` attribute.
- Alpha 0 shows the projected terrain; alpha 1 allows the detail texture's own
  opacity mask to select the overlay. Intermediate values blend between them.

The correction changes previews, not native game material links. Dragging a
material does not add vegetation geometry. Previously appended local materials
in a user's open blend file must be replaced or updated from the library.

## Affected materials

| Environment | Material names (without `TM_` / `_asset`) |
| --- | --- |
| BlueBay | TransitionRocksToLand, TransitionToLand |
| GreenCoast | CliffTransition2ToGrass, CliffTransitionToGrass, LakeShoreToGrass, TransitionForestToGrass |
| RedIsland | DetailsCliffToDirt, DetailsRocksToDirt, DetailsToDirt, DetailsVegetationToDirt, RiverShoreToRiverSide, RockToDirt |
| WhiteShore | WaterShore, WaterShoreRocky, WaterShoreToBeach |

These are corrections to existing assets, not additional materials. Some terrain
variants intentionally share side textures; different top/UV layers do not imply
that every face should differ. Authored UV placement and vertex alpha affect the
result. The 15 affected terrain C icons are rerendered with the restored shader,
and their identification insets now show its active UV-detail diffuse source.
Existing badge artwork and other icons are preserved.

Blender projection and normal frames remain approximations of the native
renderer. No new game/export test is implied.

## Maintenance

`tools/repair_terrain_uv_layers.py` stages the bounded repair from its pinned
source, verifies fresh saved files and installs locally with a backup/rollback
guard. `tools/test_terrain_uv_layers.py` checks the retained projection at alpha
0, visible detail at alpha 1, linear half-strength colour and vertex-alpha
equivalence. `tools/deco_ice_adapters.py` also recognises `TBaseColorOp` in future
full terrain rebuilds. `data/shader-followup-inputs.json` remains the native slot
inventory. `data/terrain-thumbnail-sources.json` records the revised inset sources.
