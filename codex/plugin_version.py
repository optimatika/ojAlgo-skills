#!/usr/bin/env python3
"""The plugin's version: 1.0.<number of commits that changed plugins/ojalgo or codex>, not counting the commits that
only set it.

    python3 codex/plugin_version.py           prints it
    python3 codex/plugin_version.py --write   writes it into plugins/ojalgo/.claude-plugin/plugin.json

Anthropic's directory asks for a version in plugin.json, raised with every release, because installed copies use it
to tell that an update exists. The GitHub Action .github/workflows/plugin-version.yml runs --write after each push
that changes the plugin and commits the result, so nobody raises it by hand. package.py packages the same number for
OpenAI.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "plugins" / "ojalgo" / ".claude-plugin" / "plugin.json"
# The Action's commits start with this, and are not counted.
MARK = "Set plugin version"


def derived():
    count = subprocess.run(["git", "rev-list", "--count", "--invert-grep", "--grep=^" + MARK, "HEAD", "--", "plugins/ojalgo", "codex"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return "1.0." + count


def written():
    return json.loads(MANIFEST.read_text(encoding="utf-8")).get("version")


def write(version):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("version") == version:
        return False
    manifest["version"] = version
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


if __name__ == "__main__":
    version = derived()
    if "--write" in sys.argv[1:]:
        write(version)
    print(version)
