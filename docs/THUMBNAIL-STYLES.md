# Material thumbnail styles

The current installed source uses `2026.11.25-readable-thumbnails-1`. Published full ZIPs currently contain `2026.11.24-thumbnail-styles-2`; a later full-package build must use the current installed source.

| Style | Materials | Preview |
| --- | --- | --- |
| A | 843 ordinary and CustomMod materials | Flat, layered color and emission evaluated from a disposable shader copy, without cast shadows or studio reflections. |
| B | 98 vegetation materials | Existing angled tile with representative source vegetation standing on its upper surface, unchanged. |
| C | 13 Custom materials | Smooth sphere with enlarged texture detail for easier identification. |

157 functional, runtime-input and technical symbols, seven water/waterfall previews and the CustomGlass sphere are retained. HDRI World and source node-group previews are unchanged. Material names, catalogs, production shader graphs, native export links and existing feature badges are preserved.

## Flat layered previews

A evaluates the material's existing color-layer and UV networks instead of displaying only its diffuse image. In a temporary material copy, surface BSDFs are replaced by unlit color/emission contributions, retaining alpha and shader mixing. This removes camera-dependent illumination, cast shadows, bump shading and reflected studio lamps from the identification tile. The earlier subtraction of direct glossy light is no longer used: that approach removed too much visible energy from metals such as ItemRamp and Pylon.

These are identification previews, not final PBR renders. They do not depict metallic reflectivity, roughness, normal relief, refracted depth or actual emitted luminance. Source texture shading and dark authored regions remain visible. ScreenOff stays dark because it is an unlit display; a dark region is not automatically a missing texture. Transparent FX use a dark neutral backdrop; decals use a lighter neutral backdrop so black logos remain legible. No artificial soft shadow is added.

CustomMod materials use the same flat tile. They show their supplied default inputs, not a user's future custom texture. Existing water, waterfall and CustomGlass previews retain their carefully composed appearances rather than using an unlit replacement.

## Animation and time labels

Animation states already recorded in the asset's preview metadata are reapplied only to the disposable thumbnail copy. ItemObstacle screen previews use the recorded final active atlas frame and a LAST FRAME footer. Chrono and ChronoFinish previews use the recorded representative clock digit and a STEP footer showing that digit's time interval in seconds, minutes or hours. The label identifies the interval, not the current race time or the total animation duration. Native emissive gain is retained for these selected animated frames so their display is not buried under the diffuse LED grid.

Actual animation inputs, timeline drivers, periods and export bindings remain unchanged. The orange play badge still identifies animated or time-dependent behavior; the static icon itself does not animate.

## Custom texture detail

Thirteen non-Mod, non-glass Custom materials remain spheres. Their temporary UV, Generated and Object/Position coordinates are reduced to 0.22x, making texture features approximately 4.55 times larger. This is a readability choice at thumbnail size; it does not change native texture scale or the material applied to an object. CustomGlass retains its earlier sphere and scale exactly.

## Vegetation on the tile

37 terrain previews use the sprite entries identified in their native foliage datasets and source atlases. Another 61 individual vegetation cutout previews use their own diffuse-alpha image on standing cards. These 98 previews are unchanged by this update. Placement, scale and density are representative thumbnail geometry; dragging a material does not generate plants or reconstruct a complete tree.

## Preservation and limits

Existing badge pixels are copied exactly. The turquoise grid badge retains its existing meaning; this update adds no customization badges. See BADGES.md for the short badge legend. All render-only shader copies, coordinate changes and preview fixtures are removed before saving. No additional production texture dependencies are introduced.

The update is installed with a backup and a fresh-file check of all shader graphs, identities, export metadata, node groups and badge pixels. Blender previews remain approximations; no new in-game test is implied.
