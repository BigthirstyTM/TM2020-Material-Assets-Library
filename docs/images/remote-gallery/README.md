# Website badge previews

Website-only animated WebP examples for Water and TurboRoulette Sign. These do not replace Blender Asset Browser thumbnails or material bundles.

Rendered from the verified production packed materials with Blender 5.3, CPU Cycles, fixed seed, 192 px and 24 timeline samples. TurboRoulette uses its timeline atlas states; Water uses its animated normal shader and a lit basin. Water reverses the sampled frames to close the web loop; that is a presentation loop, not a claim about its native animation period. Each frame carries the existing material badge. `manifest.json` records media hashes.

Regenerate frames using `tools/render_remote_gallery_animations.py` with Blender `-b --factory-startup --python`, followed by `-- --export <verified-export> --output <frames-directory> --kind water` (or `animation`). Encode as looping WebP with Pillow, overlay the existing badge, hash the final file and update the manifest. `prepare_remote_materials.py` copies these media into the installation site. Visitors preferring reduced motion see the original static thumbnail.
