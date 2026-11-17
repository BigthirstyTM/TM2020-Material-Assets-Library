# Surface preview source notes

The `2026.11.17-surfaces-2` preview update builds on the smooth animated water revision. Original game textures and native export bindings are retained.

- **Water:** the compiled Sea shader supplied the existing two-layer normal motion. The transparency adapter addresses Blender Eevee preview behaviour; clarity, roughness and IOR defaults are artist controls rather than recovered runtime constants.
- **Ice:** compiled `Block_PyPxzTLayered` samples depth, multiplies it by `SubsurfaceMaxDepth`, projects the view into tangent space and offsets internal UVs by depth divided by `TextureSizeInMeters`. Its surface colour mix uses roughness multiplied by `SurfaceMaxOpacity`. RoadIce stores depth 0.1 m, opacity 0.1 and texture size 32 × 32 m. The Blender adapter reconstructs this internal depth/colour behaviour while retaining the existing surface/mark graph. It also decodes the two BC5 normal samples before mixing. The full native decal/mip pipeline is not recreated.
- **Terrain:** compiled PyPxz shaders use separate lookup samples for top/side and horizontal side blending. Eight native lookup descriptors embed `CPlugFileGen`, generator kind 33 (`ACosSmoothInRange`). Their range parameters are recorded in `data/terrain-angle-lookups.json`. The Blender reconstruction uses smoothstep over a normalized acos angle. This curve convention is inferred; the generated LUT pixels were not captured.
- **CustomGlass:** compiled GlassBasic uses dual-source colour blending and complementary per-channel transmission. Native roughness is 0.05. The preview maps `1 - TargetColor` into transmission tint and adds Fresnel reflection. The runtime multiplier and absorption path remain approximate.
- **Parallax screens:** compiled screen code uses `RefractIndex` in the vector refraction equation and has a `DoubleRefract` branch. The adapter applies those source parameters to a planar tangent-space interior offset. Existing image stacks, alpha composites and native depth/UV ratios are retained. Native iterative height ray marching and concave interiors remain unresolved.

## Rebuilding the adapters

`tools/apply_surface_previews.py` applies this revision to an unmodified `2026.11.17-water-motion-2` Complete library. It requires the external research `resources.json` inventory containing native shader/texture-slot metadata. Game archives and compiled shader binaries are not bundled in this repository.

```powershell
blender --factory-startup --background --python-exit-code 1 --python tools/apply_surface_previews.py -- --source PATH/Trackmania2020_assets.blend --native-resources PATH/resources.json --blend-lookups data/terrain-angle-lookups.json --output-directory PATH/staged
```

The command stages a library with absolute texture paths; the distribution builder subsequently makes the two portable editions. Keep the previous source available until the new library and paths have been checked. Native material metadata, asset identities and saved icons are preserved; unrelated material graphs are checked before saving.
