# Website badge previews

Website-only animated WebP examples for Water and TurboRoulette Sign. These do not replace Blender Asset Browser thumbnails or material bundles.

Rendered from the verified production packed materials with Blender 5.3, CPU Cycles, fixed seed, 192 px and 24 timeline samples. TurboRoulette uses its timeline atlas states; Water uses its animated normal shader and a lit basin. Water reverses the sampled frames to close the web loop; that is a presentation loop, not a claim about its native animation period. Each frame carries the existing material badge. `manifest.json` records media hashes.

Regenerate frames using `tools/render_remote_gallery_animations.py` with Blender `-b --factory-startup --python`, followed by `-- --export <verified-export> --output <frames-directory> --kind water` (or `animation`). Encode as looping WebP with Pillow, overlay the existing badge, hash the final file and update the manifest. `prepare_remote_materials.py` copies these media into the installation site. Visitors preferring reduced motion see the original static thumbnail.

The TurboRoulette website loop is played at 40% of its previous speed (three
840 ms states; 2.52 s total). This presentation timing does not alter the asset.

The blue Stadium Ad155Screen parallax example uses 36 rendered viewing angles
over a four-second loop. The camera oscillates by 32 degrees to either side,
without changing the graph depth values. The original 1.55:1 composition is
centre-cropped to fill the square without stretching, and an equally cropped
static poster is used for reduced motion. Generate with `--kind parallax`.
