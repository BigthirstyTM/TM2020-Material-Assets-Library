# Material thumbnail styles

Published thumbnail revision `2026.11.26-thumbnail-shadow-lift-1` slightly lifts the six dark icons listed below. The preceding material revision is `2026.11.26-terrain-uv-layers-1`: 15 terrain icons are rerendered after restoring missing UV layers; the other 22 retain the preceding terrain C artwork. See [terrain UV layers](TERRAIN-UV-LAYERS.md). These changes are included in combined full-package revision `2026.11.26-thumbnail-shadow-lift-1`; check the downloaded manifest for its revision. The remote extension pilot is unchanged. The other icon styles retain the preceding aspect/family/readability refinements.

## Approved terrain C layout

The 37 terrain previews with native foliage dataset entries use a 24 x 24 x 22 block, a separate base-diffuse inset and a real soft shadow on a neutral ground plane. This is the approved **C proposal for terrain**, distinct from the existing **Custom sphere** category. The block's top remains at the previous world height so extending the sides does not move it closer to the lights. The original key/fill/environment setup is retained, with a weak additional front light to reveal the shaded faces.

The inset is resolved from the material's current active Base Color graph. An enabled UV-decoration TBaseColor or TBaseColorOp input takes priority; otherwise the current projected-top PyBaseColor is used. Legacy projected inputs are accepted only if connected to the active colour graph. For example, BlueBay_DecoHill2 shows DecoHill2_D, not the older generic Land_D fallback. Twenty-five of the 37 source paths were corrected; all 37 insets were rebuilt with encoded RGB preserved. Square images fill it; rectangular images fit without stretching. It does not represent the final PBR stack, macro modulation or every projected side layer. The source shader still renders on the block. The foliage cards are representative preview geometry, not generated vegetation on exported objects.

PNG render bytes and source RGB are read without applying a second sRGB conversion. Source alpha is a blend mask, so it does not erase RGB from the identification inset. The preceding inset-only repair left every pixel outside its 84 x 84 region unchanged. The newer UV-layer correction rerenders the 15 affected blocks as their shaders have changed. Existing badge pixels are preserved exactly. Actual shader graphs, native links, asset identities, catalogs and MaterialLib remain unchanged. The other 61 individual vegetation cutout thumbnails and all general, Custom, animation-label and symbolic icons retain their existing artwork.

Reproduce with `tools/apply_terrain_c_thumbnails.py`, `data/terrain-thumbnail-sources.json`, the installed library and `--sprite-directory` pointing to the hash-checked source atlas directory. Native atlas/model/dataset/crop provenance is recorded in the input recipe. No atlas bytes or helper geometry are added to the installed material library.

| Style | Materials | Preview |
| --- | --- | --- |
| A | 843 ordinary and CustomMod materials | Layered-color tiles; emissive sign/light families use their restored composed previews where the flat adapter obscured their design. |
| B | 98 vegetation materials | Existing angled tile with representative source vegetation standing on its upper surface, unchanged. |
| C | 13 Custom materials | Smooth sphere with enlarged texture detail for easier identification. |

157 functional, runtime-input and technical symbols, seven water/waterfall previews and the CustomGlass sphere are retained. HDRI World and source node-group previews are unchanged. Material names, catalogs, production shader graphs, native export links and existing feature badges are preserved.

## Source proportions and edge-to-edge tiles

All 843 flat/composed material tiles now retain the proportions of their displayed source image or active atlas frame. 341 are rectangular; 502 are square. Square tiles fill the icon canvas without the earlier studio margin. Rectangular tiles fit their complete image inside the square canvas with a neutral background in the unused area. The image is neither cropped to a square nor stretched. A clock or animation footer keeps its own bottom strip; its image fits above that strip without losing its aspect ratio. Badges retain their exact pixels and positions.

For composed screens, the displayed image layer determines the proportions rather than the square LED/detail map: examples include 1024x576 (16:9), 1024x512 (2:1) and 2048x512 (4:1). For manually selected atlas animation frames, encoded image dimensions are combined with the source group's UV-cell scale; the dimensions of the complete sheet are not used as the frame shape. Other materials use their recorded source texture or primary color image. Procedural previews without an image use a square fixture. No game mesh aspect or gameplay compatibility is inferred from a filename.

The 13 Custom spheres, 98 vegetation tiles, functional symbols and existing glass/water previews keep their chosen presentation. Their shapes are deliberate fixtures, not flat image sheets. No material UV coordinates, texture scale on objects, production shader or export binding is changed.

The restored emissive families are rendered with their composed shader treatment under the new proportional fixture. Thus their saved pixels are no longer identical to the earlier square fixture, while preserving the recovered sign/light appearance.

## Family-specific corrections

140 thumbnails are updated in this revision. The complete related families are reviewed, rather than only the examples shown in screenshots:

- 80 previously verified composed previews are restored for non-animated emissive sign and light materials. This includes related Boost/Turbo/gameplay signs, RaceArch, ItemObstacle light levels and other emissive families. The flat unlit adapter had reduced their emission gain, letting the gray base texture obscure the sign or light color. Restored previews are checked against the saved source-preview manifest from the previously published source.
- 45 active screen previews, including advertisements and parallax variants, receive a small +0.25-stop exposure lift. ScreenOff and ScreenBack are excluded; black/off screens are not made artificially luminous.
- Two emissive CustomMod defaults retain flat tiles and restore their emission contribution rather than reverting to the previous spheres.
- All 13 non-Mod, non-glass Custom spheres use 0.055x temporary coordinate scale: four times larger texture features than the preceding icon revision. CustomBricks now shows distinct brick courses.

The 21 clock time-step footers, six final-frame ItemObstacle previews, vegetation tiles, glass/water previews and existing badges are retained. No production material shader or game export binding changes.

## Flat layered previews

A evaluates the material's existing color-layer and UV networks instead of displaying only its diffuse image. In a temporary material copy, surface BSDFs are replaced by unlit color/emission contributions, retaining alpha and shader mixing. This removes camera-dependent illumination, cast shadows, bump shading and reflected studio lamps from the identification tile. Ordinary flat tiles do not use direct glossy-light subtraction: that approach removed too much visible energy from metals such as ItemRamp and Pylon.

These are identification previews, not final PBR renders. They do not depict metallic reflectivity, roughness, normal relief, refracted depth or actual emitted luminance. Source texture shading and dark authored regions remain visible. ScreenOff stays dark because it is an unlit display; a dark region is not automatically a missing texture. Transparent FX use a dark neutral backdrop; decals use a lighter neutral backdrop so black logos remain legible. No artificial soft shadow is added to flat tiles. Restored emissive icons retain their previous composed lighting and framing.

CustomMod materials use the same flat tile. They show their supplied default inputs, not a user's future custom texture. Existing water, waterfall and CustomGlass previews retain their carefully composed appearances rather than using an unlit replacement.

## Animation and time labels

Animation states already recorded in the asset's preview metadata are reapplied only to the disposable thumbnail copy. ItemObstacle screen previews use the recorded final active atlas frame and a LAST FRAME footer. Chrono and ChronoFinish previews use the recorded representative clock digit and a STEP footer showing that digit's time interval in seconds, minutes or hours. The label identifies the interval, not the current race time or the total animation duration. Native emissive gain is retained for these selected animated frames so their display is not buried under the diffuse LED grid.

Actual animation inputs, timeline drivers, periods and export bindings remain unchanged. The orange play badge still identifies animated or time-dependent behavior; the static icon itself does not animate.

## Custom texture detail

Thirteen non-Mod, non-glass Custom materials remain spheres. Their temporary UV, Generated and Object/Position coordinates are reduced to 0.055x, making texture features approximately 18.18 times larger. This is a readability choice at thumbnail size; it does not change native texture scale or the material applied to an object. CustomGlass retains its earlier sphere and scale exactly.

## Vegetation on the tile

37 terrain previews use the sprite entries identified in their native foliage datasets and source atlases. Another 61 individual vegetation cutout previews use their own diffuse-alpha image on standing cards. The 37 terrain entries receive the terrain C layout above; the 61 individual cutout previews retain their existing artwork. Placement, scale and density are representative thumbnail geometry; dragging a material does not generate plants or reconstruct a complete tree.

## Preservation and limits

Existing badge pixels are copied exactly. The turquoise grid badge retains its existing meaning; this update adds no customization badges. See BADGES.md for the short badge legend. All render-only shader copies, coordinate changes and preview fixtures are removed before saving. No additional production texture dependencies are introduced.

The update is installed with a backup and a fresh-file check of all shader graphs, identities, export metadata, node groups and badge pixels. Blender previews remain approximations; no new in-game test is implied.

## Selected dark icons

`ItemObstacleLight`, `ItemLampLight`, `ItemLampLightB`, `ItemLampLightC`,
`RedIsland_Water` and `WhiteShore_WaterBottom` have a small shadow lift in their
saved thumbnail artwork. Deep black areas gain a modest floor and dark texture
variation becomes easier to read. The lift fades towards midtones and leaves
highlights unchanged; badge pixels are preserved exactly. This identification
adjustment does not change the material on an object, its lighting, shader or
export properties. Reproduce with `tools/lighten_selected_thumbnails.py`.
