# Terrain and water preview controls

Preview revision: `2026.11.23-shader-fidelity-1`.

This local library update corrects DecoHill/DecoHill2 and improves the five environment water previews and GlassWaterWall. It is prepared separately from the `native-inputs-1` release upload. Downloaded release packages include it only when their release notes explicitly name this revision.

## DecoHill and DecoHill2

The projected dirt uses the native Py/Pxz image family and scale. The separate decoration layer uses the mesh's **BaseMaterial** UV map. Map an island into 0–1 to display the full decoration once; UVs outside that range can still repeat it, as they do in the native material. Py macro colour affects the projected branch before the decoration is blended.

The decoration blend follows **texture alpha × vertex alpha**. Roughness, metal and the tangent-space decoration normal use the same blend weight. The material stays opaque.

## Painting alpha

For DecoHill and WaterWall, the default preview uses alpha 1, matching a native shader without a vertex-colour input. Blender returns zero for a missing colour attribute and shader nodes cannot reliably distinguish that from an intentionally painted zero.

To preview painted alpha:

1. Create a **Color** colour attribute and paint its alpha channel.
2. In the Shader Editor, set **Use painted vertex alpha** to **1**. For DecoHill it is in **Fidelity vertex alpha control**; for WaterWall it is in **WaterWall Source Layers Preview**.
3. Alpha 0 selects the projected DecoHill base or removes WaterWall foam/ripple strength. Alpha 1 includes the overlay through its texture opacity, or enables the native foam/ripple response.

RGB does not control these blends. The switch affects Blender preview only: native export continues to use the actual vertex-colour data declared by `DColor0()`.

## Ordinary water

Select **Water Depth Colour - Source-informed Preview** in the Shader Editor:

| Control | Effect |
| --- | --- |
| Water depth (meters, preview) | Preview water thickness. Default 3 m. More depth adds colour and reduces visibility through the water. |
| Fog distance (meters) | Distance used to sample the native fog-colour image. Uses the stored collection value where available. |
| Fog density (preview) | Strength of depth-dependent scattering. Zero disables scattering but retains coloured attenuation. |
| Fog image slice (preview) | Selects a slice of the source bitmap; it is not a game mood selector. |
| Tint per meter (preview) | Per-channel attenuation. Values closer to 1 transmit more light. |
| Use depth attribute | Set to 1 to read a float attribute named **TM_WaterDepth**, in meters, instead of the constant depth. |

Existing smooth animation controls, speed, direction and ripple strength remain available. Reflection still changes with the animated normal and viewing angle. Realtime transparency uses smooth alpha blending rather than dithered transparency.

The water colour comes from the environment's native fog image. Depth increases the ray's colour attenuation and fog contribution, including a refracted viewing-angle approximation. A material on a plane cannot automatically measure the distance to another scene object in Eevee, so moving the bottom mesh does not update the manual depth control. Use the control or a stored depth attribute for that purpose.

The fog bitmap supplies RGB lookup data. Its unused alpha channel is ignored; several source DDS images store zero there. This is separate from the depth-dependent opacity generated for the preview.

The game constructs depth-dependent fog and transmittance arrays using collection and runtime inputs. Blender's selectable bitmap slice, exponential fog density, interpretation of generator RGB parameters as per-metre tint, and scattering illumination are approximations. GreenCoast's collection could not be parsed; its fog image is native but its depth/tint defaults are explicit preview choices. Background rays are transmitted without screen-space bending.

## GlassWaterWall

**WaterWall Source Layers Preview** exposes the two native flow rates, sinusoidal horizontal motion, secondary-normal weight and an overall speed multiplier. Timeline playback drives the animation using the active scene's FPS.

The preview combines native RGB transmittance, the native Fresnel lookup, reflected light and a separate white foam layer. Foam opacity and normal strength respond to the selected vertex alpha. A single fixed transparency value no longer controls the result.

Blender approximates the game's reflection/refraction render targets and foam lighting. This material uses its own WaterWall composition; it does not inherit ordinary-water depth fog.

## Compatibility

Material names, export links, gameplay/physics settings, asset identities, catalogues, saved thumbnails and existing effect badges are retained. No customization badges are added. ColorBlindness variants remain in **Complete → Preview only**: this preview update does not provide a new custom-texture export route.

For decoded source evidence and remaining reconstruction limits, see [Shader fidelity review](SHADER-FIDELITY-REVIEW.md).
