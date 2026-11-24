# Material thumbnail styles

The user-selected thumbnail layout is `2026.11.24-thumbnail-styles-1`. It replaces the previous diffuse-only local thumbnail follow-up. The published full ZIPs remain `native-surfaces-1` and do not yet contain these local updates.

| Style | Materials | Preview |
| --- | --- | --- |
| A | 836 ordinary materials | Complete Blender shader on a nearly top-down surface, with slightly brighter neutral lighting and medium-high contrast. |
| B | 98 vegetation materials | Angled tile with representative source vegetation standing on its upper surface. |
| C | 28 Custom materials | Smooth sphere under soft neutral lighting. |

157 existing functional, runtime-input and technical symbols are retained. Rendering an invisible collision surface or missing runtime input as a plain square would remove useful identification information. HDRI World and source node-group thumbnails are unchanged. Material names, catalogs, shader graphs, native export links and existing feature badges are preserved.

## Vegetation on the tile

37 terrain materials use the sprite entries already identified in their native foliage datasets and source atlases. The preview places representative crossed, alpha-cut cards on the tile's top surface. Its base and side faces use the material's complete Blender shader.

61 individual vegetation cutout materials use their own diffuse alpha image on standing preview cards above a neutral tile. This includes leaf, branch and tree-sprite texture references. A leaf atlas represents a source texture; these preview cards do not reconstruct a complete tree mesh. Bark and trunk materials without a vegetation cutout use A.

Card placement, scale and density are chosen to make the thumbnail readable at small sizes. They are not a reconstruction of the game's vegetation distribution or a promise that dragging the material will generate plants. No preview geometry or helper atlas image is added to the actual material or item export.

## Lighting and limits

A keeps the complete shader instead of displaying only its diffuse image, so texture-layer blending, normal detail and transparent contributions can appear. It uses broad lights, a neutral environment, a small exposure increase and AgX medium-high contrast. B and C retain the soft studio treatment chosen in the comparison.

A single view cannot show every projection angle or every painted vertex-alpha combination. These icons use the current default material inputs. A static image does not show water animation or other time-varying behavior. Rendered previews remain Blender approximations of native shaders; no new game test is implied.

The update is installed through a checked, recoverable backup. It changes saved thumbnails and their descriptive metadata; the earlier AnimatedFlag quarantine and duplicate-example cleanup remain in place.
