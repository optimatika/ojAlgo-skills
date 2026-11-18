#!/usr/bin/env python3
"""Builds the package for OpenAI's plugin directory (ChatGPT and Codex) from the one plugin in this repository.

    python3 codex/package.py        writes build/ojalgo-<version>.zip

There is one plugin, plugins/ojalgo, and its Claude manifest (.claude-plugin/plugin.json) is the source for name,
description, author, licence and links; its .mcp.json is the source for the MCP server's address. Nothing in them is
copied by hand: this script generates the Codex manifest (.codex-plugin/plugin.json) and the Codex .mcp.json inside the
zip. The only text kept for OpenAI alone is codex/listing.json, which holds what their listing and review ask for and
Claude's does not (a 30-character subtitle, category, capability labels, support, privacy and terms links, starter
prompts, a paragraph on the service, the review's test cases and demo recording, release notes).

The package is a "With MCP" plugin: OpenAI cannot add an MCP server to a plugin first submitted with skills only.

The version is the one in Claude's manifest, which codex/plugin_version.py derives – 1.0.<number of commits that
changed plugins/ojalgo or codex> – and a GitHub Action writes after each push. It goes up by itself whenever the
package changes, and not otherwise. This script stops if the manifest's version is not the derived one: pull the
Action's commit first.

The zip is uploaded by hand at https://platform.openai.com/plugins ("Upload new or existing plugin").
"""
import json
import pathlib
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.dont_write_bytecode = True  # A __pycache__ in codex/ would count as an uncommitted change below.
import plugin_version  # noqa: E402

root = pathlib.Path(__file__).resolve().parent.parent
plugin = root / "plugins" / "ojalgo"
claude = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
listing = json.loads((root / "codex" / "listing.json").read_text(encoding="utf-8"))

dirty = subprocess.run(["git", "status", "--porcelain", "--", "plugins/ojalgo", "codex"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
if dirty:
    sys.exit("plugins/ojalgo or codex has uncommitted changes. Commit first: the version number is counted from the commits.\n" + dirty)

version = claude.get("version")
if version != plugin_version.derived():
    sys.exit(f"plugin.json has version {version}, the commits make it {plugin_version.derived()}. Push, then pull the GitHub Action's "
             "version commit, or run codex/plugin_version.py --write and commit.")

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
long_description = (claude["description"] + "\n\n" + listing["serviceDescription"] + "\n\nSkills:\n"
                    + "\n".join("- " + name + ": " + text for name, text in skills))

# The Claude plugin's MCP server, as OpenAI takes it: the address only. A public submission refuses server headers,
# and the licence key in Claude's header comes from a userConfig prompt that OpenAI does not have.
servers = json.loads((plugin / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
mcp = {"mcpServers": {name: {"url": server["url"]} for name, server in servers.items()}}

review = dict(listing["review"])
if not review.get("demo_recording_url"):
    review.pop("demo_recording_url", None)

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
    "mcpServers": "./.mcp.json",
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
        "termsOfServiceURL": listing["termsOfServiceURL"],
        "defaultPrompt": listing["defaultPrompt"],
        "composerIcon": "./assets/icon.png",
        "logo": "./assets/icon.png",
    },
    "extensions": {
        "com.openai": {
            "review": review,
            "publication": {"release_notes": listing["releaseNotes"]},
        },
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
categories = ("Productivity", "Creativity", "Developer Tools", "Business & Operations", "Data & Analytics", "Communication", "Education & Research",
              "Security", "Finance", "Healthcare", "Travel", "Entertainment", "Other")
if interface["category"] not in categories:
    problems.append("category must be one of: " + ", ".join(categories))
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
for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
    if not interface[field].startswith("https://") or len(interface[field]) > 1024:
        problems.append(f"{field} must be an https:// address, at most 1024 characters")
if len(mcp["mcpServers"]) != 1 or not all(s["url"].startswith("https://") for s in mcp["mcpServers"].values()):
    problems.append("exactly one MCP server, at an https:// address")
cases = review["test_cases"]
if len(cases["positive"]) != 5 or len(cases["negative"]) != 3:
    problems.append("the review needs exactly five positive and three negative test cases")
for case in cases["positive"]:
    if not all(case.get(field) for field in ("description", "prompt", "tools_triggered", "expected_behavior")):
        problems.append("a positive test case needs description, prompt, tools_triggered and expected_behavior: " + case.get("prompt", "?"))
for case in cases["negative"]:
    if not all(case.get(field) for field in ("description", "prompt")):
        problems.append("a negative test case needs description and prompt")
if "demo_recording_url" in review and not review["demo_recording_url"].startswith("https://"):
    problems.append("demo_recording_url must be an https:// address")
if problems:
    sys.exit("Not packaged:\n- " + "\n- ".join(problems))

build = root / "build"
build.mkdir(exist_ok=True)
target = build / f"ojalgo-{version}.zip"
folder = manifest["name"]  # The folder in the zip must have the plugin's name.
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr(f"{folder}/.codex-plugin/plugin.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    archive.writestr(f"{folder}/.mcp.json", json.dumps(mcp, indent=2) + "\n")
    archive.write(plugin / ".claude-plugin" / "icon.png", f"{folder}/assets/icon.png")
    archive.write(plugin / "README.md", f"{folder}/README.md")
    archive.write(plugin / "LICENSE", f"{folder}/LICENSE")
    for file in sorted((plugin / "skills").rglob("*")):
        if file.is_file() and file.name != ".DS_Store":
            archive.write(file, f"{folder}/skills/{file.relative_to(plugin / 'skills')}")

print(f"{target.relative_to(root)}  (version {version}, {len(skills)} skills, MCP server {next(iter(mcp['mcpServers']))})")
if "demo_recording_url" not in review:
    print("No demo recording yet: the review needs one. Put its address in codex/listing.json, review.demo_recording_url, and package again.")
