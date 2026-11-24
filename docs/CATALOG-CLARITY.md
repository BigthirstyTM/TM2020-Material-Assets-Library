# Asset Browser clarity and reported flag crash

This follow-up, `2026.11.23-catalog-clarity-1`, is included in the combined full packages with content revision `2026.11.24-thumbnail-styles-2`.

## One main copy of each asset

Four example files inside the scanned library folder also contained asset-marked copies. Their 12 asset markers have been removed while retaining example scenes and materials. This removes duplicate water, transition and World entries without replacing the improved main library materials. The release-example refresh tool now clears example asset markers too.

Distinct native material variants can share the same diffuse image. They remain separate because their shaders, parameters, collision or export links can differ. Texture files have not been deleted.

If an already open Asset Browser still displays cached entries, refresh its library listing. Materials already appended to an open project remain part of that project.

## Clearer thumbnails

**Superseded thumbnail layout:** the subsequent [A/B/C thumbnail styles](THUMBNAIL-STYLES.md) replace the diffuse-only layout described below. The duplicate-example cleanup and AnimatedFlag quarantine on this page still apply.

262 thumbnails have been refreshed: 195 flat base-diffuse images, 37 diffuse images with representative native vegetation cutouts, 28 Custom materials rendered on smooth spheres, and two tree-sprite alpha previews. Existing feature badges are preserved. Other thumbnails and material shader graphs are unchanged.

Vegetation cutouts are selected from atlas entries referenced by each material's existing native foliage dataset and model. They identify associated source vegetation; they do not simulate native distribution, scale, density, wind or generated geometry. A thumbnail is not evidence of game compatibility.

## AnimatedFlag: Preview only

The user reported a game crash while selecting or placing an item with approximately six faces and different materials, after applying AnimatedFlag. This was not an isolated single-material test. No relevant crash dump was available; older unrelated logs were excluded from the diagnosis.

`TM_ItemFlag_animated_asset` is retained under **Preview only / Reported runtime issues**. Its custom, JSON and registered Blender RNA export-link fields are cleared and only the `Stadium_ItemFlag` declaration is removed from the bundled MaterialLib. The full-package check caught an older RNA value that survived the initial metadata-only cleanup; that value is cleared in the combined refresh too. Original source provenance is retained separately. Static `ItemFlagNoAnim` aliases are preserved, without claiming a new game test.

The native animated material selects `Tech3_Warp_TDiffSpec_VertexTween`; its compiled vertex shader reads packed vertex/instance data. A required animation or mesh context is a plausible hypothesis, not a demonstrated crash cause.

| Future isolated observation | Interpretation |
| --- | --- |
| Static flag loads; animated flag crashes on the same simple mesh | Narrows the problem to the animated binding or its required context. |
| Both flags crash | Investigate common mesh/export/item data first. |
| Both load alone; the multi-material item crashes | Investigate material interaction and the original item. |
| Original crash cannot be reproduced | Keep the report unresolved; do not infer runtime safety. |

The game was not started for this update. No shader changes, new badges or runtime clearance are implied.
