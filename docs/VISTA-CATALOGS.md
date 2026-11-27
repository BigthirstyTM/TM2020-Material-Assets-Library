# Vista catalog correction

Revision `2026.11.27-vista-catalogs-1` corrects the catalog IDs of all 53 new vista materials. An environment-name suffix lookup matched the BlueBay/GreenCoast/RedIsland/WhiteShore HDRI subcatalogs. Material placement now uses exact environment material paths. Terrain, sponsor decals and structures are separated into Terrain, Decals and signs, and Other materials below each environment's Materials catalog.

All shader graphs, native links, material IDs, thumbnails and feature badges are preserved. Counts remain 873 Materials Only, 1,172 Complete (299 Preview only) and 20 HDRI Worlds. Only World assets belong under HDRI World Moods. Reopened staged and installed files verify these rules across every asset. Remote preparation and offline verification now compare each material's catalog with the source inventory and reject materials under HDRI or Worlds outside HDRI. The prior broken public listing is a regression fixture: all 53 assignments are detected.

Remote correction is being published first; offline publication is held until the corrected remote release verifies. Existing users should refresh the remote listing and download the four updated vista bundles after publication. Cached bundles can retain old assignments until downloaded again. Existing scene materials are not rewritten.
