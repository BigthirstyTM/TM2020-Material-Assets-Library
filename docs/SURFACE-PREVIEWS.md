# Water, ice, terrain and glass previews

Content revision: `2026.11.17-surfaces-2`.

Use Material Preview or Rendered shading. Re-append updated materials into existing projects with **Reuse Data disabled**; copies already saved in a project retain their previous nodes. These controls affect Blender previews. Native Blendermania export links and game material settings are unchanged.

## Water transparency

The five ordinary water materials now show geometry underneath the surface in Eevee, including Material Preview without scene ray tracing. Existing smooth, animated height layers and speed/direction controls remain available.

In the Shader Editor, select **Water Clarity and Refraction Preview**:

- **Clarity** controls how much of the background passes through. Default: 0.92.
- **Water Roughness (preview)** and **Water IOR (preview)** value nodes control both preview modes. Defaults: 0.08 and 1.333.
- **Physical refraction = 0** gives a smooth alpha-blended preview with Fresnel reflections. Background rays pass through without bending; the default avoids dither speckles.
- **Tinted shadows = 0** passes light through without a sampled translucent shadow. This keeps the interactive preview clean. Set it to 1 if you want tinted shadows; these may need more samples.
- **Physical refraction = 1** uses the transmission BSDF. Use Cycles. For Eevee physical refraction, enable scene ray tracing/refraction and switch the material render method to Dithered; this optional mode may show sampling noise during movement. Closed geometry with thickness gives more useful physical refraction than a single plane.

The clarity, roughness and IOR values are adjustable preview choices. The native normal-layer motion and original height images remain source based. Automatic game depth fog, shoreline masking and underwater rendering are not reproduced.

`Examples/Water-Clarity-Example.blend` contains a patterned floor below animated water. In the locally maintained source library, the example is under `Documentation`.

## Layered ice

RoadIce and the compatible PlatformIce OpenTechBorders/PlatformTech materials now use native internal-depth and surface-opacity parameters, corrected BC5 normal decoding, and an internal layer that moves with the viewing angle. Reflection coating and mild subsurface scattering improve the ice appearance.

Adjust **Ice Internal Depth (meters)** and **Ice Surface Max Opacity (native)** in the Shader Editor. Depth is modulated by the native height image where available. Surface opacity mixes the internal colour with the native surface tint; it does not control transparency to objects underneath.

These native layered materials are opaque composites of internal imagery. They are not clear water or transparent glass. CustomIce uses a different projected shader and is not converted into this layered family. Ice IOR, coat and scattering settings are Blender approximations. Native mip-bias filtering and the full subsurface decal pipeline remain approximate.

## Terrain and rocks

87 existing world-projected materials have **Terrain Angular Transition Controls**. Top/side and side/side mixing now use separate angle ranges derived from native `ACosSmoothInRange` texture descriptors. Original texture choices, world scales, macro colour, height colour and normal projections remain in place.

The generated game lookup image itself was not captured. Blender reconstructs a smooth transition using normalized acos angles and the recovered range endpoints; the exact lookup curve is approximate. Adjust the start/end controls together to change the transition width. Mesh smoothing still affects the normals used to select the projections.

## Glass and parallax screens

CustomGlass uses native roughness and a complementary transmission tint informed by the compiled GlassBasic colour blending. **Glass Clarity and Refraction Preview** offers the same realtime/physical choice as water. The runtime tint strength and Blender IOR are approximate. Other glass shader families retain their existing graphs.

Eight parallax screens now use native `RefractIndex` and `DoubleRefract` parameters for planar refracted layer offsets. Recovered screen depths, metre-to-UV ratios, interior images, alpha layer composites and outer texture UV corrections are retained. A subtle reflective coat represents the front panel.

This is a planar reconstruction with a bounded grazing-angle offset. Native iterative height ray marching, concave interiors, render-target blending and the complete refraction pipeline are not reproduced exactly. Coat settings are preview choices.
