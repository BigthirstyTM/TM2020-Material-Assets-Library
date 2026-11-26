# UV, grass, display depth, terrain arrays and colour masks

Published full-package revision: `2026.11.26-shader-followup-1`.

This update addresses the five groups identified after the Dyna preview audit.
Native material links, export declarations, asset identities, catalog membership,
feature badges and existing thumbnail artwork are retained. These changes are
Blender previews; changing preview controls does not edit the game's shaders.

## Explicit UV and normal inputs

Previously unnamed UV Map and tangent-normal UV selections now name
`BaseMaterial`. File-image samplers with an implicit active-UV fallback receive
an explicit BaseMaterial input. Already named UV maps and linked world/generated
projection coordinates are retained. This includes the previously reproduced
ItemRamp, Boost Sign and CustomModSelfIllumSimple multi-UV problems, together
with related materials using the same fallback pattern.

The update considers 527 material graphs: the 463 unique UV/normal candidates
plus 64 additional materials with unlinked file-image coordinates. Counts
overlap with the groups below; they are not additional assets. Named atlas/frame
and screen-image UV nodes remain in place.

## GrassX2

`Grass`, `WarpGrass` and `WarpGrass2` now include the source `Grass_X2.dds`
modulation. The compiled `Block_PyDSNX2_p` shader samples this map, doubles its
RGB and multiplies the selected base colour by it. Its source bitmap uses world
projection, scale `1/1024`, a 180-degree rotation and offset `(0.25, 0.25)`.
The Blender adapter maps the game's horizontal plane to Blender world XY.
This is surface-colour modulation, not generated grass geometry.

## Screen/sign SI depth

119 legacy generic SI-coordinate paths were reviewed individually. For 117
materials with height images, the SI texture uses the recovered eight-step
height trace with first-crossing interpolation, tangent-space refraction,
optional parallel-interface exit, per-axis `Meters_Depth / Meters_UV`, and
`1-roughness^4` attenuation. Material overrides take precedence over the exact
root shader's declared defaults. The existing MulInside picture coordinates,
screen aspect/frame selection, Hue paths, alpha composition and emission scales
are preserved.

`RaceArchCheckpointSmall` and `RaceArchFinishSmall` explicitly bind no height
resource. Their SI coordinates retain the source surface coordinates without
inventing a replacement height texture. The generic relief offset is bypassed.

These are view-dependent previews, not new timeline animations. A uniform or
inactive native height path may produce no visible change; a native depth
parameter alone does not establish visible relief.

## Previously deferred terrain arrays

The 24 BlueBay, GreenCoast, RedIsland and WhiteShore entries now use the selected
authored layer records instead of the earlier generic array treatment:

- Independent top dimensions (`U02/U03`) and side dimensions (`U06/U07`).
- Their corresponding offsets, stored rotation angle, and signed scale axes.
- The selected top/side D/R/N images and native rough/metal packing.
- Separate macro (`X2`) transforms and vertical-height (`HX2`) modulation.
- The authored cosine-domain transition ranges.
- Normal perturbations reoriented for signed/rotated texture frames.
- Existing UV decoration and vertex-alpha controls, where present.

The static image-array records and selectors are the source of these settings.
Standalone bitmap descriptors corroborate several scales and rotations, but are
not substituted for an explicitly selected array record. For example, the
WaterBottomPxz standalone bitmap and array row have different scales; the array
row is used for this array shader.

The implementation uses the standard bitmap transform convention and mapped
Blender projection/tangent frames. Native runtime matrix buffers, all engine
layer-selection overrides and exact renderer projection have not been captured.
These remain source-informed approximations, not verified native-renderer parity.

## Optional source colour masks

Fourteen materials gain the recovered chroma/grey Hue formula and their own
native mask images: Canopy, CanopyGlass, nine DecalPaint Sponsor/Logo variants,
RoadDirt, RoadDirtFullColorize and TrackWall. Masks are applied at the individual
sample coordinates before projected/decoration layer blending, not over a
completed surface with a single arbitrary UV mapping.

Enable **Enable source colour preview**, then choose **Explicit preview colour**.
For layered surfaces these controls are on the material's active surface group;
for simple materials they are named Value and RGB nodes in the Shader Editor.
The control defaults to zero. The local formula is
`c=max(G-(R+B)/2,0)`, `grey=G-c`,
`h=clamp(c*target + grey*mean(target),0,1)`,
`result=lerp(base,h,mask.alpha)`.

The white control default is an explicit preview input, not a recovered game
palette value. Engine target selectors do not necessarily encode a literal RGB
colour. They remain recorded as source data; no arbitrary colour is enabled by
default and no new customization badge is added. Export customization still
depends on Blendermania and the game's native material contract.

The supplied CanopyGlass mask has alpha zero throughout. Its recovered masked
branch therefore remains visually inactive even with the preview control
enabled; the adapter deliberately does not override that source mask.

## Scope and using the update

Refresh the library and append a fresh material copy. Existing materials already
appended into a project are not replaced automatically. Keep a UV map named
`BaseMaterial`; preserve any other named UVs required by your object/exporter.

The current thumbnail artwork remains as previously selected. The material
changes can improve applied surfaces without changing the static icon. Both full
ZIP releases include this revision. The remote extension pilot remains unchanged.

The game and Blender GUI were not used for validation. The update is checked
with fresh-file preservation tests and bounded CPU renders; this is not a new
in-game export or material compatibility clearance. Preview only classification,
the AnimatedFlag quarantine and deferred customization badges remain unchanged.

Source inputs: `data/shader-followup-inputs.json`. Reproducible build, adapter,
verification, render and installation tools are provided under `tools/` with
the `shader_followup` filename. Installation keeps a hash-pinned backup and
checks that the installed source has not changed since staging.

The [complete per-group material list](SHADER-FOLLOWUP-MATERIALS.md) records
555 unique updated material graphs. The group totals are 527 UV/sampler fixes,
3 GrassX2 surfaces, 119 SI depth paths, 24 terrain arrays and 14 colour-mask
adapters; one material can belong to more than one group.
