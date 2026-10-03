#!/usr/bin/env python3
"""Turns the code blocks in the service skills into runnable files, so that what is tested is what is published."""
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent.parent
skills = root / "plugins" / "ojalgo" / "skills"
out = pathlib.Path(sys.argv[1])
host = sys.argv[2]


def blocks(skill, language):
    text = (skills / skill / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"```" + language + r"\n(.*?)```", text, re.S)


def java_class(name, snippets, tail):
    imports, body = [], []
    for snippet in snippets:
        for line in snippet.splitlines():
            (imports if line.startswith("import ") else body).append(line)
    imports = sorted(set(imports))
    lines = imports + ["", "public class " + name + " {", "    public static void main(String[] args) throws Exception {"]
    lines += ["        " + line for line in body + tail]
    lines += ["    }", "}", ""]
    target = out / "src" / "main" / "java" / (name + ".java")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).replace("https://your-service-host", host), encoding="utf-8")


(out / "rest.sh").write_text(blocks("optimisation-service-rest", "bash")[0].replace("https://your-service-host", host), encoding="utf-8")
(out / "rest.py").write_text(blocks("optimisation-service-rest", "python")[0].replace("https://your-service-host", host), encoding="utf-8")

java_class("ClientSkill", blocks("optimisation-service-client", "java"), [
    'System.out.println("model: optimal=" + result.isOptimal() + " value=" + result.getValue() + " chairs=" + chairs.doubleValue() + " tables=" + tables.doubleValue() + " rush=" + rush.doubleValue());',
    'System.out.println("file:  optimal=" + fileResult.isOptimal() + " value=" + fileResult.getValue() + " solution=" + fileResult.getSolution());',
    "System.out.println(client.getServiceEnvironment());",
])

java_class("OjAlgoSkill", blocks("optimisation-service-ojalgo", "java"), [
    'System.out.println("result: " + result);',
    'System.out.println("chairs=" + result.doubleValue(model.indexOf(chairs)) + " tables=" + result.doubleValue(model.indexOf(tables)) + " variable.getValue()=" + chairs.getValue());',
])
