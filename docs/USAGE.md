# Using the library

1. Open an Asset Browser and select **TM2020 Material Assets Library**.
2. Browse the environment categories, or search for a material by name.
3. Drag a material onto your mesh. Keep it as a native-linked material when exporting through Blendermania V2.
4. Use a UV map named **BaseMaterial**. Prepare a **LightMap** UV map when your export workflow requires it. Check the material's usage notes in the offline catalogue for special UV, animation or vertex-colour requirements.
5. Export the item through **Blendermania V2** with the included `MaterialLib.txt` selected in Settings.

Blender shader graphs provide an editing preview. Changing their image nodes does not replace the game's native textures during export. The game resolves the material's native link. Some effects, environment lighting and animations therefore differ between Blender and Trackmania.

## Preview only

The Complete edition adds **Trackmania2020 → 08 Preview only**, retaining subcategories for the source environments. These assets are useful for identifying and inspecting textures. A matching native export route has not been confirmed. They are omitted from Materials Only.

Vegetation, country flags, UI images and individual layers of composed materials may belong to specialised game systems. Applying their preview to a mesh does not turn it into a supported game material.

## Special materials

- **ColorBlindness variants:** the game's accessibility setting chooses the colours. The Blender preview does not force the alternate palette in exported items.
- **Animated materials:** use the Blender timeline where an animation adapter is provided; the thumbnail is a representative still frame.
- **Screens and signs:** use the correct panel aspect ratio. For applicable screen images, UV 0–1 spans one image; LED detail can use a different scale.
- **Invisible/collision materials:** helper patterns identify them in Blender. Their game appearance and collision role are separate from the preview.
- **HDRI Worlds:** use these for Blender preview lighting. They do not export as an item's material or recreate the complete game's lighting system.

Open `Catalogue/index.html` for searchable material thumbnails and usage details. See [BADGES.md](BADGES.md) for the small symbols on previews.

## Example scene

Open `Examples/Material-Usage.blend` for three editable sample cubes using RoadTech, RoadDirt and CustomIce. Each has `BaseMaterial` and `LightMap` UV layers and its own collection. This is a Blender usage example; configure your normal item placement, lightmap unwrap and V2 export options before exporting. Keep the example inside the installed folder so its relative texture paths continue to resolve.
