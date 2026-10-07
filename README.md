# ojAlgo skills for coding agents

[Agent Skills](https://agentskills.io) that teach AI coding assistants to work with [ojAlgo](https://www.ojalgo.org/), the pure-Java, zero-dependency library for LP, QP and MIP, and with Optimatika's [Optimisation Service](https://www.optimatika.se/optimisation-service/).

| Skill | What it teaches |
|---|---|
| [`ojalgo-optimisation`](plugins/ojalgo/skills/ojalgo-optimisation/SKILL.md) | Writing and debugging optimisation models with ojAlgo |
| [`optimisation-service-rest`](plugins/ojalgo/skills/optimisation-service-rest/SKILL.md) | Level 1: solving models over the service's REST API, from any language |
| [`optimisation-service-client`](plugins/ojalgo/skills/optimisation-service-client/SKILL.md) | Levels 2 and 3: the Java client library, from any JVM language. Submit model files, or build models with its own modeller (no ojAlgo needed, older Java versions supported) |
| [`optimisation-service-ojalgo`](plugins/ojalgo/skills/optimisation-service-ojalgo/SKILL.md) | Level 3: solving existing ojAlgo models remotely, with no changes to the model code |

With the first one, an assistant that is asked to allocate, assign, schedule, pack, select, blend, locate or build a portfolio in a JVM application will:

- decide whether a solver is actually needed, and which problem type it is;
- start from a verified recipe in the [Optimisation Cookbook](https://www.ojalgo.org/optimisation-cookbook/) rather than write a model from scratch;
- follow the rules that decide whether a model is correct and fast: checking the result state, rounding integer values, unique constraint names, tight linking instead of big-M, symmetry breaking, time limits;
- use the current API, not names from old ojAlgo versions that no longer compile;
- know how to debug an infeasible or slow model.

## Install

**Claude (chat, Cowork, Claude Code):** the plugin is listed in Claude's plugin directory as **ojAlgo**. Add it from there.

**Claude Code, from this repository:**

```text
/plugin marketplace add optimatika/ojAlgo-skills
/plugin install ojalgo@ojalgo
```

**Other agents:** each skill is a plain `SKILL.md` in the open Agent Skills format. For any agent that supports skills, copy the folders under [`plugins/ojalgo/skills`](plugins/ojalgo/skills) into that agent's skills directory. For one that does not, the files still work as reference material to give the agent as context.

## Tested

The code in the three service skills is run against a live server by [`tests/run.sh`](tests/run.sh), which extracts it from the skill files each time. The same script checks that the latest ojAlgo release still behaves the way the rules in the `ojalgo-optimisation` skill say it does ([`tests/RuleChecks.java`](tests/RuleChecks.java)).

## Links

- ojAlgo: https://www.ojalgo.org/ · source: https://github.com/optimatika/ojAlgo
- Optimisation Cookbook: https://www.ojalgo.org/optimisation-cookbook/
- Commercial support and the Optimisation Service: https://www.optimatika.se/

ojAlgo and these skills are MIT licensed.
