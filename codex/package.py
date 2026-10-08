#!/usr/bin/env python3
"""Builds the package for OpenAI's plugin directory (ChatGPT and Codex) from the one plugin in this repository.

    python3 codex/package.py        writes build/ojalgo-<version>.zip

There is one plugin, plugins/ojalgo, and its Claude manifest (.claude-plugin/plugin.json) is the source for name,
description, author, licence and links. Nothing in it is copied by hand: this script generates the Codex manifest
(.codex-plugin/plugin.json) inside the zip. The only text kept for OpenAI alone is codex/listing.json, which holds
what their listing asks for and Claude's does not (a 30-character subtitle, category, capability labels, support and privacy links, starter prompts).

OpenAI requires an explicit version; Claude's manifest has none on purpose. The version is derived: 1.0.<number of
commits that touched plugins/ojalgo or codex>. It goes up by itself whenever the package changes, and not otherwise.

The zip is uploaded by hand at https://platform.openai.com/plugins ("Upload new or existing plugin").
"""
import json
import pathlib
import re
import subprocess
import sys
import zipfile

root = pathlib.Path(__file__).resolve().parent.parent
plugin = root / "plugins" / "ojalgo"
claude = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
listing = json.loads((root / "codex" / "listing.json").read_text(encoding="utf-8"))

count = subprocess.run(["git", "rev-list", "--count", "HEAD", "--", "plugins/ojalgo", "codex"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
version = "1.0." + count

dirty = subprocess.run(["git", "status", "--porcelain", "--", "plugins/ojalgo", "codex"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
if dirty:
    sys.exit("plugins/ojalgo or codex has uncommitted changes. Commit first: the version number is counted from the commits.\n" + dirty)

# The long description is put together from the skills themselves.
skills = []
for skill in sorted((plugin / "skills").iterdir()):
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    name = re.search(r"^name:\s*(.+)$", front, re.M).group(1).strip()
    description = re.search(r"^description:\s*(.+)$", front, re.M).group(1).strip()
    skills.append((name, description.split(". Use when")[0].rstrip(".") + "."))
order = ["ojalgo-optimisation", "ojalgo-linear-algebra", "ojalgo-portfolio"]
skills.sort(key=lambda s: (order.index(s[0]) if s[0] in order else len(order), s[0]))
long_description = claude["description"] + "\n\nSkills:\n" + "\n".join("- " + name + ": " + text for name, text in skills)

manifest = {
    "name": claude["name"],
    "version": version,
    "description": claude["description"],
    "author": claude["author"],
    "homepage": claude["homepage"],
    "repository": claude["repository"],
    "license": claude["license"],
    "keywords": ["optimisation", "optimization", "linear programming", "mixed integer programming", "java", "jvm", "ojalgo"],
    "skills": "./skills/",
    "interface": {
        "displayName": claude["displayName"],
        "shortDescription": listing["shortDescription"],
        "longDescription": long_description,
        "developerName": claude["author"]["name"],
        "category": listing["category"],
        "capabilities": listing["capabilities"],
        "websiteURL": listing["websiteURL"],
        "supportURL": listing["supportURL"],
        "privacyPolicyURL": listing["privacyPolicyURL"],
        "defaultPrompt": listing["defaultPrompt"],
        "composerIcon": "./assets/icon.png",
        "logo": "./assets/icon.png",
    },
}

# OpenAI's stated limits. Better to fail here than in their portal.
problems = []
interface = manifest["interface"]
if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", manifest["name"]) or len(manifest["name"]) > 64:
    problems.append("name must be lowercase letters, numbers and single hyphens, at most 64 characters")
for field, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80)):
    if len(interface[field]) > limit:
        problems.append(f"{field} is {len(interface[field])} characters, the limit is {limit}")
if len(manifest["description"]) > 4000:
    problems.append("description is over 4000 characters")
if len(manifest["author"]["name"]) > 120:
    problems.append("author.name is over 120 characters")
prompts = interface["defaultPrompt"]
if len(prompts) > 3 or len(set(prompts)) != len(prompts):
    problems.append("at most three starter prompts, all different")
for prompt in prompts:
    if len(prompt) > 128:
        problems.append(f"starter prompt is {len(prompt)} characters, the limit is 128: {prompt}")
capabilities = interface["capabilities"]
if len(capabilities) > 20 or any(len(c) > 120 for c in capabilities):
    problems.append("at most 20 capabilities, each at most 120 characters")
for field in ("websiteURL", "supportURL", "privacyPolicyURL"):
    if not interface[field].startswith("https://"):
        problems.append(f"{field} must be an https:// address")
if problems:
    sys.exit("Not packaged:\n- " + "\n- ".join(problems))

build = root / "build"
build.mkdir(exist_ok=True)
target = build / f"ojalgo-{version}.zip"
folder = manifest["name"]  # The folder in the zip must have the plugin's name.
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr(f"{folder}/.codex-plugin/plugin.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    archive.write(plugin / ".claude-plugin" / "icon.png", f"{folder}/assets/icon.png")
    archive.write(plugin / "README.md", f"{folder}/README.md")
    archive.write(plugin / "LICENSE", f"{folder}/LICENSE")
    for file in sorted((plugin / "skills").rglob("*")):
        if file.is_file() and file.name != ".DS_Store":
            archive.write(file, f"{folder}/skills/{file.relative_to(plugin / 'skills')}")

print(f"{target.relative_to(root)}  (version {version}, {len(skills)} skills)")
