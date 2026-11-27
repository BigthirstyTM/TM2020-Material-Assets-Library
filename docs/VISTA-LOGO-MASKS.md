# Vista sponsor logo masks

Revision `2026.11.27-vista-logo-masks-1` corrects the materials and icons of sixteen sponsor decals: four variants each in BlueBay, GreenCoast, RedIsland and WhiteShore. Remote extension **1.0.5** is published and independently verified with this correction. Both offline ZIP editions are being prepared; until their publication completes, their public version remains `2026.11.27-vista-catalogs-1`.

The native `DecalSponsor4x1D_M.dds` files contain different masks in different channels. Red contains the named vista logo; alpha contains a legacy Stadium logo. The compiled `Block_DecalGeom_TOp_PyPxzDSN_X2` pixel shader samples `TMapTOpacity` red (`t12.x`) and multiplies it by vertex alpha (`v1.w`). The previous Blender adapter used bitmap alpha and therefore revealed the wrong logo. No source texture or export link was replaced.

The corrected adapter separates red and uses it for opacity. Ordinary Blender objects without a Color attribute use opaque vertex alpha by default. For meshes with authored Color alpha, set **Use Color vertex alpha for decal opacity** to 1 in the material nodes. This enables the native multiplication. BaseMaterial UV, projected paint colour, normal and roughness remain unchanged. This note supersedes the earlier preview-provenance wording describing TOpacity alpha.

The four variants per environment are:

- `DecalPaint2Sponsor4x1D`
- `DecalPaint2Sponsor4x1NoColorizeD`
- `DecalPaintSponsor4x1D`
- `DecalPaintSponsor4x1NoColorizeD`

All sixteen icons were rendered again at the authored 4:1 aspect ratio, retaining their existing badge pixels. All 1,234 asset identities/catalogs/export properties and unrelated graphs/icons, all node groups, MaterialLib and the catalog file were checked after saving and reopening the staged and installed libraries. Counts remain 873 Materials Only, 1,172 Complete materials (299 Preview only) and 20 Worlds.

The four BlueBay logo silhouettes were compared with the existing game captures using new renders of the same comparison fixture. The other twelve fixes use their exact source masks and the same compiled shader contract; they have not received a new game visual check. Lighting, native decal depth and the complete native renderer are not claimed identical. No game or user Blender GUI was started or controlled for this correction.

Reproducible tools: `tools/vista_decal_opacity.py`, `tools/fix_vista_decal_logos.py`; the candidate builder also uses the corrected contract. Local receipts and the recoverable previous master are in `build/vista-decal-fix` in the workspace.
