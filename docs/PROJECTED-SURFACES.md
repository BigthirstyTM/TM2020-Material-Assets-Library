# Projected terrain and source previews

For the subsequent terrain-array and LakeBottom changes, see [shader reconciliation](SHADER-RECONCILIATION.md).

Local content revision: **2026.11.23-projection-sources-1**.

This follow-up improves 31 projected terrain, rock, Deco and Custom previews, integrates two light-tube emission adapters and four optional structure colour-mask previews, and refreshes the 37 affected thumbnails.

## Projected materials

The projected adapter now samples each colour, roughness/metalness and normal texture with its own source bitmap transform. Previously these channels shared the base-colour transform even when the normal or roughness descriptor differed.

Side normal maps are blended in packed texture space before BC5 decoding. Their decoded vectors are oriented in surface-tangent top/side frames and normalized after blending, rather than adding an XY perturbation directly to a world normal. This improves slopes and opposed faces while keeping the projection anchored in world space when an object is moved, rotated or scaled.

Height macro modulation uses the vertical coordinate. The existing BaseMaterial UV decoration and vertex-alpha blend are retained. Keep a UV layer named **BaseMaterial** for authored decorations. The **Deco native layer controls** group retains the existing fallback-alpha and painted-alpha controls. Newly appended material copies contain the changes; copies already stored in another scene must be replaced or reimported.

Native texture identities and source-local operations are used. Existing angular lookup interpolation and mapped Blender coordinate conventions remain preview adapters, rather than a complete native shader port. Texture-array families with incompletely decoded per-layer transforms and the separately rotated LakeBottom bitmap frame were not rebuilt using guessed scales or bases. LakeBottom's exact shader reference was nevertheless recovered and recorded.

## Light tubes

LightTubeBig and LightTubeSmall now include the source refracted-emission image and one-dimensional viewing-angle gradient. Both retain ordinary emission scale **1.5**. The additional source scale is **0.2** for Big and **0** for Small; Small's extra branch therefore remains disabled by default.

The shader group provides separate preview global HDR and night multipliers. Both source NightOnly flags are zero, so no night-only filter is imposed. The game's scene HDR scale and selected runtime rendering permutation are not reconstructed by these material-local controls.

## Optional structure colour masks

StructureInWorld, StructureTruss, ThemeDesertBarrier and TrackWallClipsInWorld include the recovered mask RGB/alpha and chroma/grey target-colour formula. In the **P2 opt-in recovered masked hue** group, set **Explicit preview target** and enable **Enable recovered hue preview** to inspect it.

The option is disabled by default because the runtime palette selection has not yet been established. The illustrative preview colour is not presented as a recovered game default. Native selector values such as `[0,1,0]` are not treated as literal green. Changing Blender preview nodes does not change the game's native material definition or exported customization data.

## Thumbnails and existing assets

The 37 corrected material thumbnails use a three-dimensional sample so the top and side appearance can be seen together. Existing badge pixels and meanings are retained; no customization badges were added. Native links, identifiers, catalog assignments, collision/gameplay declarations and MaterialLib are unchanged.

See [source resolution](SOURCE-RESOLUTION.md) for the additional 88 exact shader references and remaining research gaps. The game was not started. Blender checks do not constitute new in-game export clearance.

This local follow-up is newer than the published `2026.11.23-native-surfaces-1` full release ZIPs. The existing releases have not been replaced as part of this follow-up.

## Maintenance inputs

`tools/prepare_projection_refresh.py` resolves references from the three extracted resource inventories. It accepts `--native-workspace`, `--audit`, `--snapshot`, `--library` and `--output`; it does not launch the game. Reviewed inputs are retained in `tools/data/projection-refresh-inputs.json` and `tools/data/secondary-preview-inputs.json`. Their recorded source hash pins the original baseline; a later update requires a new reviewed baseline.

The build tool `apply_projection_refresh.py` accepts `--library` (asset folder), `--inputs`, `--secondary` and `--output`. Verify with `verify_projection_refresh.py` (`--original` baseline blend, `--staged` build folder, `--inputs`, `--output`) and `verify_secondary_previews.py` (`--library` staged blend, `--secondary`, `--output`). Run these Blender scripts in background mode with arguments after `--`. The installer requires the verified staging output and checks that the installed source still matches its baseline before replacement.
