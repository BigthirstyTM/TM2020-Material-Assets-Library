# Shader fidelity review

Research date: 2026-11-23. These findings underpin the separate local preview revision `2026.11.23-shader-fidelity-1`. They are **not included** in the `2026.11.23-native-inputs-1` packages currently being published. No game runtime comparison has been completed for these changes.

The local preview implementation is documented in [Terrain and water preview controls](SHADER-FIDELITY-PREVIEWS.md). It applies recovered layer roles and formulas, with the remaining renderer/runtime differences explicitly identified as approximations.

## PlatformDirt_DecoHill and DecoHill2

The native material inherits `Tech3 Block PyPxzTDiffSpecNorm_PyX2Hx2`. Its shader combines projected Py/Pxz terrain with a separately UV-mapped T layer.

| Native role | DecoHill image family | Coordinates |
| --- | --- | --- |
| Py base/roughness/normal | `DecoHillDirtPy_D/R/N` | Generated world XZ, bitmap scale enabled |
| Pxz base/roughness/normal | `DecoHillDirtPy_D/R/N` | Generated world XY/ZY blend |
| T base/roughness/normal | `DecoHillDirt_D/R/N` | Mesh UV, `NoGenerate`, bitmap scale disabled |

DecoHill2 substitutes `DecoHillDirt2_D` for the T base-colour image. The other listed families remain the same.

The current Blender graph incorrectly samples the T image family through a world-space projection adapter, including duplicate `tex_D/R/N World 1/2` samplers. This can repeat the whole overlay across the object. The native UV sampling does not establish a universal rule that the image appears once on every object: that also depends on the mesh's authored UVs. A BaseMaterial UV island spanning 0–1 samples one full overlay image.

Compiled `Block_PyPxzT_X2H2_p` establishes the blend direction:

```text
T = sample(TBaseColor, mesh_uv)
weight = T.alpha * vertex_colour_0.alpha
colour = projected_colour + weight * (T.rgb - projected_colour)
```

The same weight blends roughness/metal and the decoded normal contributions. Vertex variants with `COLOR0` pass its alpha to the pixel shader; variants without that input supply 1. The current graph instead uses vertex alpha alone and applies an additional macro operation after the layer combination. Both layer roles and operation ordering require review; simply changing repeat/clamp or texture scale would conceal the underlying mismatch.

Required correction: keep the projected terrain branch, sample the T branch through `BaseMaterial`, apply the recovered alpha product, and apply Py/Pxz modulation to the appropriate projected branch. Reconstruct normal spaces deliberately rather than treating an overlay tangent normal as a world-projected normal. Preserve native links and Sand physics.

The current MaterialLib already declares `BaseMaterial` slot 0, `Lightmap` slot 1 and `DColor0()` for both materials. These declarations should be retained. This defect is not evidence that the BaseMaterial UV should be removed.

## Ordinary water

`Water.Material.Gbx` inherits `Tech3_Water_MultiH`. Its slots describe normals, reflection/refraction, Fresnel and masks; there is no static blue diffuse map in that material. The current Blender clear-surface adapter defaults to clarity 0.92 and white transmission. That is an earlier preview choice and omits the engine's depth-colour composition.

The collection supplies additional resources. The inspected Stadium collection references:

- `Stadium/Media/Texture/Image/WaterFog.dds`, a 256 × 32 texture;
- `Stadium/Media/Texture/Image/WaterTransmittance.ImageGen.Gbx`, generator kind 51, integer parameters `[2048, 1]` and real parameters `[0.84, 0.95, 0.97, 50]`;
- stored bump speed 0.01, UV scale 0.015, bump scale 0.15, refraction perturbation 0.1 and fog clamp distance 0.1.

These are stored collection inputs, not captured active GPU constants. Other collections differ. Do not interpret the generator parameters as a confirmed exponential formula or blindly replace animation controls with the stored numbers: units, active collection, runtime overrides and shader permutation still matter.

The compiled `WaterFogFromDepthH_p` shader reconstructs scene depth, calculates the water path length (with a refracted-ray option), scales it by the selected water's maximum-depth inverse, then samples **two 1D texture arrays** at that coordinate and water index:

```text
F = sample(WaterFogDayTimed, normalized_water_path, water_index)
T = sample(WaterTransmittance, normalized_water_path, water_index)
fog_output.rgb = F.rgb * F.alpha
transmittance_output.rgb = T.rgb * (1 - F.alpha)
```

This proves a missing depth-colour stage, rather than a missing single blue surface colour. The raw DDS is an input to engine processing; its rows must not be assumed to map directly to the shader's water-array index. Day-time construction, generator kind 51, active runtime constants and render-target blend state require further reconstruction for a complete port.

Required correction: preserve animated surface normals and Fresnel, add source-informed depth-dependent colour and attenuation, and label any manually supplied preview water depth as an approximation. A plane without a water volume cannot infer the same path length as the game. Do not set an arbitrary constant blue and call it an exact shader reconstruction.

## GlassWaterWall

This material inherits `Tech3 Block WaterWall`. Its source roles are `GlassWaterWall_T` (RGB transmittance), `_R` (roughness/metal), `_N` (normal), `_O` (foam opacity) and a Fresnel lookup. It is a different shader from ordinary horizontal water.

The compiled vertex shader establishes:

```text
uv0.x = mesh_uv.x + X0_Scale * sin(2*pi*time/X0_Period)
uv0.y = mesh_uv.y + fract(time*Y0_Speed)
uv1.x = mesh_uv.x
uv1.y = mesh_uv.y + fract(time*Y1_Speed)
```

For this native material the stored values are Y0 speed 1, Y1 speed 1.1, X0 period 4, X0 scale 0.01 and Normal1 weight 0.01. The pixel shader blends the two decoded normal samples using Normal1 weight and scales their horizontal components by vertex alpha × 1.001 before normalizing.

In the inspected pixel permutation, foam weight is `_O * vertex_alpha`. The coloured transmission coefficient includes `_T.rgb * (1 - Fresnel) * (1 - foam_weight)`. Foam contributes separately lit surface colour; reflection/refraction are sampled from engine render targets. The final target alpha is 1 in this permutation: its transmission is computed inside the shader, not represented by a generic surface alpha value.

The current Blender graph feeds `_T` to Base Color and an inverted colour to scalar Transmission Weight, with fixed alpha 0.8. That loses per-channel transmission and the recovered foam relationship. The replacement must combine tinted transmission, foam and reflection explicitly. Blender screen-space refraction remains a renderer approximation; ordinary-water depth fog must not be copied to this shader without evidence.

Current MaterialLib already includes the mesh UV and `DColor0()` required by this family. Preview colour defects alone do not justify changing native links, physics or the export declarations.

## ColorBlindness variants

The extracted variant directory contains 30 DDS/TGA images, representing 15 image replacements, and no standalone Material.Gbx. The decoded `GameSkin/ColorBlindness.GameSkin.gbx` maps ordinary texture image paths through `Stadium/Media/Modifier/ColorBlindness/`. The inspected native resource inventory likewise contains no ColorBlindness-named material resource.

Therefore a material alias or `DLinkFull` to that image directory does not force accessibility colours. It links a material; it does not apply the GameSkin image remap. Linking the ordinary material remains subject to the game's selected mode.

The installed Blendermania V2 exporter confirms an additional limitation: `CustomImporter.py::_get_material_configs_from_collection` fills Link/Color/PhysicsId/GameplayId in its TM2020 branch; BaseTexture/Model are filled in the Maniaplanet branch. The shared MaterialConfig dataclass having a BaseTexture field is not proof that TM2020 custom texture export supports it.

A future custom-texture material/export route could reproduce selected appearances independently of accessibility mode. That requires actual TM2020 texture packaging and shader support, and separate verification of animation, emissive response, physics and gameplay. This is not a direct-link fix. Keep these 15 variants in Complete / Preview only until an independent route is demonstrated.

## Evidence and limits

Local evidence is under `build/shader-fidelity-review`: current Blender graph inspection, collection reflection, water-fog samples and disassembled WaterWall/WaterFog shader permutations. Existing PyPxzT assembly is under `build/material-improvements/gpu`; Sea assembly is under `build/water-research/gpu`. Evidence hashes are recorded separately in `evidence-manifest.json`.

Shader descriptors establish bindings, generators and some stored constants. Compiled DXBC establishes the instructions of its included permutations. Collection and mood data supply additional inputs. None alone proves the active runtime state or exact appearance in a particular map. Compiled game shader binaries are research inputs and are not added to the distribution.
