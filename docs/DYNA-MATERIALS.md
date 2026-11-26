# Dyna material previews

Local revision: `2026.11.26-dyna-preview-1`.

`Dyna` is an engine material variant name. It does **not** by itself mean an
animated texture, scrolling UVs, a different diffuse texture, or a predictable
day/night appearance. Read the individual material and its shader chain.

## Findings and changes

| Materials | Source evidence and Blender behavior |
| --- | --- |
| `WarpDetails_Dyna` / `WarpDetails_WithLightmap` | Same parsed shader, texture slots and material parameters: `Tech3_Block_TDSN_CubeOut`. Their previews remain equivalent under identical Blender lighting. Source payload hashes differ, so unparsed flags or engine routing may still differ. |
| `SpeedometerLight` / `SpeedometerLight_Dyna` | Same parsed `Tech3_Block_TDSNI_CubeOut` inputs, including `SelfIllumScale=20` and `RefractSI=0`. Both now explicitly use `BaseMaterial` for emissive UVs and tangent-space normals. No suffix-based animation was added. |
| `WarpLight_Dyna` | Uses `Tech3 Block TSelfIllum`, unlike the other Warp light materials below. Retains `SelfIllumScale=2.5`; the shader is opaque and `NightOnly_SelfIllum=0`. Its emissive texture and tangent normals now use explicit `BaseMaterial` UVs, and diffuse alpha no longer creates object transparency. |
| `WarpLight`, `WarpLightRay`, `WarpLightRay_Dyna` | Use `Tech3_Block_TDSN_CubeOut_DispIn`. The previous preview selected one light layer instead of composing the interior. The new preview multiplies the flattened interior by SI and by `1-BaseColorOp.alpha`, retains the native emission scale, and weights the outer base color by its alpha. The result is an opaque composite. |

The DispIn SI texture now uses a source-derived eight-step height trace, with
first-crossing interpolation, tangent-space refraction, optional parallel-interface
exit, `Meters_Depth / Meters_UV` per axis, and `1-roughness^4` attenuation. Native
values for the three Warp materials are read from their individual records;
they are not guessed from the material name. The shader's `RefractIndex` is
used as a refraction ratio here, rather than copied into Principled IOR.

No time driver was introduced. Changing the viewing angle affects the depth
preview; advancing the timeline alone does not invent movement.

## Scope and limits

The audit resolved source chains for all **25 Dyna-named entries** in the current
source inventory: four concrete Stadium materials and 21 experimental Techno3
material instances or shader templates. Five related counterparts were also
compared. The experimental templates include additive energy/shield and dynamic
lighting paths with engine-supplied inputs. They are not 21 newly validated game
materials, and were not promoted, reclassified, or given speculative animations.

The Warp interior still uses the existing flattened `MulInside` texture. The
native renderer supports texture-array layers, room projection, display
activation, lightmaps, probes, deferred passes, and engine exposure. These are
not fully reproduced by this adapter. The reconstructed SI path is therefore a
closer Blender approximation, not a native-renderer replacement.

Shader parameters and compiled Direct3D instructions were inspected offline.
Background Blender 5.3 CPU renders checked interior contribution, depth response,
UV-map independence, counterpart equivalence, and timeline stability. There was
no new in-game visual comparison or exporter test in this revision.

## Using the local update

Refresh the asset library or reopen Blender, then append the material again.
Materials already appended into an existing project are local copies and are
not automatically replaced. Use a UV map named `BaseMaterial`.

The local library was updated with a backup. Asset identities, native export
links, catalogs, badges, thumbnails, `MaterialLib.txt`, and unrelated material
graphs are preserved. The existing GitHub ZIP releases and remote pilot retain
their previous content until a separate packaging/publication update.

## Reproducible tools

- `tools/audit_dyna_sources.py`: resolve individual source chains and compare parsed inputs.
- `tools/dyna_preview_adapters.py`: source-backed Blender node adapters.
- `tools/apply_dyna_previews.py`: guarded staging and fresh-file preservation checks.
- `tools/test_dyna_previews.py`: bounded CPU render checks using actual material graphs.
- `tools/install_dyna_previews.py`: hash-pinned installation with backup and reopened verification.

Native source descriptors, hashes, shader-program provenance, and adapter scope
are recorded in `data/dyna-preview-evidence.json`. Extracted compiled shaders
and local test receipts are kept outside the source repository.
