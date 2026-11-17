# Water animation preview

For the current water transparency and optional physical refraction controls, see [Surface previews](SURFACE-PREVIEWS.md). The animation controls below remain available.

The five ordinary water assets now have animated ripples in Blender:

- `TM_Water_asset` (Stadium)
- `TM_BlueBay_Water_asset`
- `TM_GreenCoast_Water_asset`
- `TM_RedIsland_Water_asset`
- `TM_WhiteShore_Water_asset`

## Use

Refresh the Asset Browser, then append a fresh water material. Materials already copied into a project do not update automatically. Disable **Reuse Data** when appending if Blender would otherwise reuse an older copy.

Use **Material Preview** or **Rendered** shading and play the timeline. Solid shading does not show the animation. Reflections and objects beneath the surface make the ripples easier to see. The optional `Water-Animation-Preview.blend` provides a small basin, markers and an existing native HDR World for inspection; its geometry is only a Blender example.

In the Shader Editor, select **Water Animation - Source-informed Preview**:

| Control | Effect |
| --- | --- |
| Speed | Motion rate in texture cycles per second. Default 0.03; negative values reverse motion. This is an adjustable preview value. |
| Direction (degrees) | Rotates both flow directions. Zero retains the recovered shader directions. |
| World scale | Texture repeats per Blender metre. Default 0.03125. Increase for smaller ripples. This is an adjustable preview value. |
| Bump distance | Original bitmap bump factor interpreted by Blender: 4 for Stadium, 0.25 for the four other environments. |
| Strength | Blender ripple strength; 0 makes the animated normal flat. |

Set **Water Animation Enabled (0 static / 1 animated)** to **0** to restore the previous static height adapter. Its original UV path uses a UV map named **BaseMaterial**. The animated path uses world coordinates to keep neighboring horizontal surfaces aligned. It is intended for horizontal water surfaces.

Animation uses the active scene's frame rate and begins at frame 1. Changing speed or direction changes the preview; these controls are not baked animation tracks.

## Basis and limits

The original game GPU cache contains compiled `Tech3/Sea_v` and `Tech3/Sea_p` shader programs. Their disassembly reveals two moving texture coordinates:

```
q = WorldXZ * BumpScaleUV
t = Time * BumpSpeedUV
uvA = q + t * (-0.636945, 0.448750)
uvB = q + t * (1, 1)
```

The pixel shader samples the same normal map twice and adds the sampled vectors before normalization. This preview follows that two-layer pattern, using the library's actual native height textures and Blender Bump conversion. Trackmania X/Z maps to Blender X/-Y.

The game supplies speed, scale and further shading values at runtime. Their active values have not been captured. Preview defaults are therefore adjustable approximations, not recovered game settings. Blender's height-to-normal filtering differs from the game's `Height2NxNyNz` processing. Normal decals, engine reflection/refraction buffers, depth effects and full native lighting are not reproduced. This is animated shading relief; it does not deform the mesh silhouette.

Native Blendermania export bindings are unchanged. The game uses its own material shader after export; Blender preview controls do not replace or configure that shader. The existing waterfall adapter is separate and unchanged.

The water badge identifies a water-related asset. It does not certify that every water-related asset is animated or that its Blender appearance exactly matches the game. The five assets listed above have this animation explicitly recorded in their material properties.

## Smooth water shading

Native height images are sampled with cubic interpolation and Blender Bump filter width 1.0. This keeps height derivatives smooth between texels and avoids block-shaped highlights in close views. Original texture files are unchanged. Shade Smooth affects mesh normals; it cannot remove texture sampling facets on a flat water plane.

## Updating

Install the refreshed packages for your chosen edition. Keep the water example in its supplied subfolder so relative texture paths resolve. In existing Blender projects, append a fresh water material without Reuse Data; existing material copies retain the older shader graph.
