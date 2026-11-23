# Asset types and game export

The Asset Browser contains different Blender asset types. File extensions such as `.tga` and `.dds` describe image storage, not game-export support.

| Asset type | Apply to a mesh? | Game export |
| --- | --- | --- |
| Native-linked material | Yes; drag it onto a mesh or assign it to a material slot. | Uses its recorded native material link through Blendermania V2. A link does not guarantee identical rendering or universal runtime compatibility. |
| Preview-only material | Yes, for Blender texture inspection. | Unconfirmed, conditional or unsupported export behaviour; retained for reference. |
| Source texture node group | Add it in the Shader Editor; it is not a material to drag onto an object. Outputs are Raw Color and Raw Alpha. | No standalone game material link. |
| HDRI World | Configures Blender scene lighting; not a mesh material. | Does not export as an item's material. |

## Source resources

The 42 `TM_Stadium_Source_...` assets are source texture node groups, including cloud images, Fresnel lookup gradients, mood icons and cubemap inputs. They are now under **Trackmania2020 / 08 Preview only / Source resources**. Their descriptions and tags explicitly identify their role.

These images are inputs to specialised game shaders and lighting systems. Making a Blender material from an image does not create a native game material link. No exportable materials have been removed or reclassified as source textures.

Cubemap source nodes display an image-face preview. Use the supplied HDRI World assets for convenient Blender environment lighting.

## Empty categories

Catalogues with no assets anywhere in their subtree are omitted. Parent categories remain when they contain populated subcategories. This is evaluated for each edition, so Materials Only does not retain empty Preview-only resource categories.

## Refreshing an existing installation

Refresh the Asset Browser, or reopen Blender. A project already holding an old catalogue selection may need its Asset Browser library to be selected again. The material graphs, export links, asset names, catalogue UUIDs and saved thumbnails are preserved.
