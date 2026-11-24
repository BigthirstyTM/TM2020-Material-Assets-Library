# Badge legend

The small symbols on saved material thumbnails identify features:

| Badge | Meaning |
| --- | --- |
| Green foliage / grass | Foliage or sprite-growth family. Some entries are preview references only. |
| Blue waves | Water material family. |
| Purple layered rectangles | Screen depth or parallax. |
| Orange/red flag | Cloth or flag feature. |
| Amber play symbol | Animation, animated UVs or an image atlas. |
| Teal grid / arrow | World-projected material or projection adapter. |
| Blue arrow / dashed wall | Invisible in game, with collision information recorded in the item files. |
| Gold World mood | HDRI World asset and its lighting mood. |

A feature badge is an identification aid, not a guarantee that Blender and the game render the effect identically or that every gameplay behaviour has been confirmed.

**Preview only** means export behaviour is unconfirmed, conditional or unsupported. **No static texture** means the material has no single standalone texture image. **Collision only** identifies a collision-focused surface. These labels describe the asset's role; they are not additional visual effects.

The repository's README badges show edition material counts and the Blender authoring version.

The local [A/B/C thumbnail styles](THUMBNAIL-STYLES.md) retain all existing badge symbols. Ordinary thumbnails show the complete Blender shader from above, vegetation uses tiles with representative source sprites standing on top, and Custom materials use spheres. Preview vegetation identifies the source family; it does not imply generated vegetation on your object or prove runtime compatibility.
