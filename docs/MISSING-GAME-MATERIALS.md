# Missing game material links

Investigation: 2026-11-27. Read-only audit of the current Materials Only assets,
including the production remote library. This report records the read-only investigation. The subsequent quarantine
update below is now authorized and in progress. The game was not launched.

## Result

Five of the 825 offered materials point to material files absent from the current
installed game archives. The user reports red rendering for `16x9ScreenOff`;
the other four have the same missing-target defect but were not newly tested in
the game. Red rendering alone is not a universal diagnosis for every shader.

| Asset | Missing native target | Existing alternative to evaluate |
| --- | --- | --- |
| `TM_16x9ScreenOff_asset` | `Stadium/Media/Material/16x9ScreenOff.Material.Gbx` | No native ScreenOff counterpart found; use a separately authored dark material if this appearance is needed. |
| `TM_Ad16x9Screen_asset` | `Stadium/Media/Material/Ad16x9Screen.Material.Gbx` | `Stadium/Media/Material/Ad155Screen.Material.Gbx` |
| `TM_PodiumScreen16x9_asset` | `Stadium/Media/Material/PodiumScreen16x9.Material.Gbx` | `Stadium/Media/Material/PodiumScreen155.Material.Gbx` |
| `TM_WarpScreen16x9B_asset` | `Stadium256/Media/Material/WarpScreen16x9B.Material.Gbx` | `Stadium256/Media/Material/WarpScreen155B.Material.Gbx` |
| `TM_WarpScreen16x9C_asset` | `Stadium256/Media/Material/WarpScreen16x9C.Material.Gbx` | `Stadium256/Media/Material/WarpScreen155C.Material.Gbx` |

Alternatives in this table are existing resources, **not proven exact aliases**.
Their image layout, depth, UV conventions and appearance need comparison before
substitution. `TM_WarpScreen16x9_asset` without B/C has an existing native target;
this finding does not apply to all 16:9 screen materials.

## Cause

All five names occur in the add-on's supplied
`assets/nadeoimporters/Trackmania2020/NadeoImporterMaterialLib.txt` and in the
active material definition copies. Their `DMaterial` entries use `DLinkFull`
paths which do not occur in the installed archives. A definition therefore
exists for the exporter, while its eventual game resource does not.

The library preserved these legacy export aliases and builds a Blender preview
from local textures. This can look correct in Blender without a valid native
game material. Earlier shader-source research already recorded these five
unresolved aliases. The displayed `Native binding established` and `verified
from files` messages are too strong for these five entries and should be
corrected. A shader-preview change alone cannot repair an absent game target.

The defect is present in the library's MaterialLib and the installed Blender
5.2 and 5.3 add-on copies; it is not explained by forgetting to install the
expanded MaterialLib. Re-exporting an unchanged link will preserve the problem.

## Scope and evidence

- Enumerated all 13 current `.pak` / `.Pack.Gbx` archives directly, without
  launching the game: 71,722 stored entries, 71,687 unique canonical paths,
  985 distinct material paths, zero archive read errors.
- Reopened all 98 published material bundles in headless Blender 5.3 with the
  installed add-on registered. All 825 effective export aliases match the
  source inventory; this checks actual registered material properties rather
  than relying only on generic custom-property dumps.
- Resolved all 825 aliases against three MaterialLib copies. Exactly five
  native material targets are absent. No aliases are missing from these copies.
- All other 820 targets exist. Their direct references in the decoded native
  material inventories resolve against current archive paths after respecting
  resource-relative locations. This is a file-level check, not a complete
  transitive shader validation or runtime compatibility guarantee.
- The source inventory contains 1,119 materials: these 825 active entries and
  294 Preview only entries. Preview only entries are not counted as additional
  game-ready failures. The five affected entries are active in both offline
  editions and the remote library.

Local evidence under `build/red-material-audit/` includes `fresh-pak-index.json`,
`packed-effective-bindings.json`, `audit.json`, `missing-materiallib-targets.json`,
`unresolved-relative-dependencies.json` and `serialization-verification.json`.
`all-materials.csv` contains the complete per-material findings.

## Separate stored-metadata finding

Five materials have older aliases inside `MAT_PROPS_AS_JSON`:

| Material | Stored alias | Active alias |
| --- | --- | --- |
| `TM_BlueBay_Water_asset` | `Water` | `BlueBay_Water` |
| `TM_GreenCoast_Water_asset` | `Water` | `GreenCoast_Water` |
| `TM_RedIsland_Water_asset` | `Water` | `RedIsland_Water` |
| `TM_WhiteShore_Water_asset` | `Water` | `WhiteShore_Water` |
| `TM_Stadium_TechnicsStepLow_asset` | `TechnicsStep` | `Stadium_TechnicsStepLow` |

All five active links resolve to existing files. The installed V2 export path
calls `save_mat_props_json`; calling that same function on disposable appended
copies refreshed all five stored aliases to the correct active values. These
are a consistency/import-roundtrip concern, **not five additional proven red
materials**. Their stored metadata can be synchronized in a future update.

## Recommended correction

1. Reclassify the five broken-link screens as Preview only in Complete and
   exclude them from Materials Only / the remote listing, retaining their IDs
   for any eventual source-backed repair. Correct the misleading status text.
2. Evaluate the existing 155-format counterparts as explicit replacements;
   keep the distinction between a tested replacement and an exact alias.
   Reuse existing valid assets instead of adding near-duplicates where possible.
3. If a substitute is adopted, update the export definition and Blender graph
   together and verify the link serialized into a fresh Item.Gbx. Test the item
   in-game before marking the replacement runtime-verified. Existing exported
   items need re-exporting; listing refresh does not repair their stored links.
4. Add a release check that rejects game-ready materials whose resolved target
   is absent from the current game archive inventory. Keep runtime-specific
   risks separate from this file-existence check.

No library changes or publication were performed as part of this investigation.

## Authorized quarantine update

Revision `2026.11.27-missing-material-quarantine-1` clears the five export links
and moves the original materials, with unchanged shader graphs, icons and badges,
to **Preview only / Missing native materials** in Complete. Materials Only now
contains 820 materials; Complete retains all 1,119, including 299 Preview only
entries. Both keep 20 HDRI Worlds. Remote Materials Only excludes the same five
entries. No alternative texture or material is substituted. Local installation
is verified; full packages and the remote update are being prepared. Existing
scene copies and previously exported items are not automatically rewritten.
