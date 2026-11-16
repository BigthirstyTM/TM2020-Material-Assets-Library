# Installation

## Requirements

- Windows for the automatic installer and Trackmania export workflow.
- Blender **5.2.3 LTS**, the authoring version, or a newer version able to read its files. Older Blender versions are not supported by this release.
- Blendermania with its **V2 export workflow** and native material-link support. The authoring setup used a local Blendermania **4.4.6 V2 build**. Version numbers alone do not establish support: your build must expose the V2 exporter and a **Material Lib** setting. This release does not bundle or replace the Blendermania add-on or converter.
- Trackmania 2020 and the converter/importer required by your Blendermania installation for game exports.
- Internet and enough disk space for both the downloaded ZIPs and extracted textures. The installer shows each download's size.

The upstream add-on project is [Blendermania](https://github.com/skyslide22/blendermania-addon). For a different V2 distribution, follow that distribution's setup instructions. Blender material browsing does not require a working game converter.

## Automatic installation

1. Choose **Materials Only** or **Complete Library** on the project's GitHub Releases page.
2. Download `Install-Library.ps1` from that release. Each release's script selects its own edition by default.
3. Close all Blender windows so saved preferences and settings cannot be overwritten by another Blender session.
4. In PowerShell, change to the folder containing the script and run:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-Library.ps1
   ```

5. Open Blender and select **TM2020 Material Assets Library** in the Asset Browser's library selector.

The default installation folder is `%LOCALAPPDATA%\TM2020 Material Assets Library\<edition>\<version>`. The download cache is alongside it under `Downloads`. After a successful installation you can remove the cached ZIPs to recover space.

To choose a folder or Blender executable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-Library.ps1 -Destination 'D:\Blender Assets\TM2020' -Blender 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
```

The installer registers one asset library and, where supported, sets Blendermania's saved `Material Lib` path to the included `MaterialLib.txt`. Preference and settings backups receive a `before-tm2020` timestamp. It does not modify an open project or replace add-on files. If automatic Blendermania configuration is unavailable, set the path manually as described below.

## Manual / offline installation

If you downloaded all release ZIPs **and** `release.json`, the installer can also verify and install them without downloading again:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Install-Library.ps1 -PackageDirectory .
```

1. Download **all ZIP files from the chosen release**. Packages from different editions must not be mixed.
2. Extract each ZIP into the **same empty folder**. The resulting folder must directly contain `Trackmania2020_assets.blend`, `blender_assets.cats.txt`, `MaterialLib.txt` and `Textures`. Do not leave each ZIP in a separate subfolder.
3. In Blender, open **Edit → Preferences → File Paths → Asset Libraries**, click **+**, and add that folder. Name it **TM2020 Material Assets Library** and save preferences.
4. In **Blendermania → Settings → Material Lib**, select the installed `MaterialLib.txt`. Save Blendermania settings if your build requires it, then restart Blender.
5. Select the library in the Asset Browser. If an import method selector is available, use **Append** for editable material copies.

The Blender library uses relative texture paths. Keep `Textures` next to the `.blend` file. Once materials are appended into your own project, keep the library installed; pack external images into your project before sharing that project separately.

## Updates and changing editions

Install the new version into a fresh folder. The installer updates the single named asset-library entry and Material Lib path. Complete includes Materials Only; install only one active edition.

Existing materials already appended into a project retain their previous data. Append the updated material again without reusing the old local datablock, then assign the new copy to the relevant mesh. Keep the previous installation until projects that reference its textures have been migrated or packed.

## Troubleshooting

- **Pink materials:** confirm `Textures` is next to the library `.blend`, and that every ZIP was extracted. For older appended materials, use Blender's **File → External Data → Find Missing Files** and select the installed `Textures` folder.
- **Unknown native link / material not found:** select the included `MaterialLib.txt` in Blendermania settings, restart Blender, and use the V2 exporter.
- **Missing V2 exporter:** install the V2-capable Blendermania distribution used by your workflow. The asset library does not add an exporter.
- **Missing or stale thumbnails:** refresh the Asset Browser or restart Blender.
- **Checksum failure:** remove only the named failed ZIP from the download cache and rerun the installer. It reuses other verified downloads.
- **Destination already exists:** choose a new empty folder with `-Destination`. The installer does not overwrite an existing installation.
- **Blender setup fails:** the files may already be installed; use the manual registration and Material Lib steps above.
- **A vegetation preview will not export:** Preview only is a browsing category, not an exportable vegetation solution.

## Uninstall

Remove **TM2020 Material Assets Library** from Blender's Asset Libraries preferences. Restore your previous Material Lib path in Blendermania, or use the timestamped settings backup. Delete the installed library folder and optional download cache when no project depends on their texture files.
