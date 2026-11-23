# Deco and PlatformIce previews

Local preview revision: `2026.11.23-deco-ice-1`.

This update reviews all 32 Deco and PlatformIce material assets. Existing export links, gameplay settings, catalogue IDs and effect badges are retained. The asset thumbnails are rendered from the corrected material graphs on a lit 32 m panel with BaseMaterial UV coordinates from 0 to 1.

## Decoration and terrain

The fourteen mixed Hill materials use two different coordinate systems: Py/Pxz terrain is projected in world space; the authored T decoration uses the mesh's **BaseMaterial** UV map. The T image therefore appears once across UV 0–1, independent of object size. Repeated UVs still repeat the image. The Py macro modulation is applied before the decoration overlay.

The overlay weight is T texture alpha multiplied by vertex alpha. In **Deco native layer controls**, the default fallback alpha is 1. Enable **Use painted vertex alpha** to preview the alpha component of the **Color** corner colour attribute. Blender supplies zero for a missing colour attribute; it cannot reliably distinguish missing data from deliberately painted zero alpha. These controls affect the Blender preview only; export uses the object's actual colour data.

PlatformDirt and PlatformIce DecoGrass now reconstruct the compiled Hue shader's chroma/grey formula, with the source material's TargetColor default. This differs from multiplying the texture by an arbitrary grass tint. The target control is a preview setting; runtime game overrides are not captured.

Projected base colour, roughness and normals share the native base-colour coordinate transform, rather than independently using inconsistent bitmap defaults. Plain UV surfaces and decals retain their source UV layout and have their native image references repaired where necessary.

Macro X2/Hx2 images are multiplicative data: their midpoint is sampled as approximately 0.5 so the shader's factor of four is neutral for two mid-grey inputs. Applying an sRGB decode to those values darkens the result incorrectly. New adapter image instances keep these data settings separate from other materials' existing images.

## Layered ice

PlatformIce PlatformTech and OpenTechBorders use their native internal colour/depth images and the existing Blender planar depth adapter. Their projected roughness/normal layer blends with UV surface marks through TAlpha, without an extra vertex-alpha multiplier. Internal colour is tinted with SurfaceColor using combined roughness multiplied by SurfaceMaxOpacity. A missing PlatformIce internal colour image reference is restored.

The mask is TAlpha's red channel: the compiled `sample r5.w, ..., t7.yzwx` instruction routes source R into destination W. It is not a vertex-colour channel.

## Accuracy and limitations

Layer roles and Hue/mask/tint operations are based on native material/bitmap descriptors and compiled GPU shader disassembly. Blender's lighting, projected normal bases, angular transitions, matrix orientation and internal depth remain renderer approximations. Environment materials whose terrain-array selector is supplied at runtime retain an explicit first-layer preview when no selector is recorded in the material. These previews do not establish an exact match with every in-game object or lighting condition.

The compact source descriptors for the 32 reviewed assets are retained in `tools/data/deco-ice-inputs.json`. Shader evidence includes `Block_PyPxz_X2H2_DefWrite_Hue_p.hlsl.GpuCache.Gbx.00.asm.txt` (SHA-256 `6abd0c2add47888571cf013eeaf1248b0279533e8e34b57b5f3a5e59383c7f94`) and `Block_PyPxzTLayered_p.hlsl.GpuCache.Gbx.00.asm.txt` (SHA-256 `6206ee3a4b5b456f348c74997965a1db7cf78ff949f8bf9ccdd8be263e69fccf`). The local research retains the disassembly; game shader binaries are not added to this repository.

## Using the update

Refresh the asset library in Blender. Existing scene materials are separate copies: reimport an affected material to inspect the update. Preserve the object's authored BaseMaterial UVs. The preview studio is a neutral comparison fixture, not a reconstruction of a specific game mesh.

This local revision is separate from the immutable `2026.11.23-native-inputs-1` release packages. It will be included when the next combined packages are built.
