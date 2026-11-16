"""Register an extracted edition. Run with Blender closed; no project is saved."""
import argparse
import importlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
import bpy


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--skip-addon-settings', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = a.library.resolve()
    data = json.loads((root / 'library.json').read_text(encoding='utf-8'))
    assert (root / 'Trackmania2020_assets.blend').is_file()
    assert (root / 'MaterialLib.txt').is_file()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    config = Path(bpy.utils.user_resource('CONFIG'))
    prefs = config / 'userpref.blend'
    if prefs.exists():
        bpy.ops.wm.read_userpref()
        if not a.dry_run:
            shutil.copy2(prefs, prefs.with_name('userpref.before-tm2020-' + stamp + '.blend'))
    name = 'TM2020 Material Assets Library'
    existing = next((x for x in bpy.context.preferences.filepaths.asset_libraries if x.name == name), None)
    if not a.dry_run:
        if existing:
            existing.path = str(root)
        else:
            bpy.context.preferences.filepaths.asset_libraries.new(name=name, directory=str(root))
        bpy.ops.wm.save_userpref()
    configured = False
    if not a.skip_addon_settings:
        try:
            import addon_utils
            addon_utils.enable('blendermania-addon', default_set=False)
            constants = importlib.import_module('blendermania-addon.utils.Constants')
            target = Path(constants.PATH_DEFAULT_SETTINGS_JSON)
            old = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
            updated = dict(old)
            updated[constants.SETTINGS_MATERIALLIB] = str(root / 'MaterialLib.txt')
            if not a.dry_run:
                if target.exists():
                    shutil.copy2(target, target.with_name('settings.before-tm2020-' + stamp + '.json'))
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + '.tm2020.tmp')
                temporary.write_text(json.dumps(updated, indent=4), encoding='utf-8')
                temporary.replace(target)
            configured = True
        except (ImportError, AttributeError, RuntimeError) as exc:
            print('Set Blendermania Settings > Material Lib to:', root / 'MaterialLib.txt')
            print('Automatic Blendermania configuration was unavailable:', type(exc).__name__)
    print('TM2020_CONFIGURATION', json.dumps(dict(edition=data['edition'], version=data['version'],
          library=str(root), dry_run=a.dry_run, materiallib_configured=configured)), flush=True)


if __name__ == '__main__':
    main()
