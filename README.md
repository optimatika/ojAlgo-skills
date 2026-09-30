# ojAlgo skills for coding agents

An [Agent Skill](https://agentskills.io) that teaches AI coding assistants to write correct, fast optimisation models with [ojAlgo](https://www.ojalgo.org/) — the pure-Java, zero-dependency library for LP, QP and MIP.

With it, an assistant that is asked to allocate, assign, schedule, pack, select, blend, locate or build a portfolio in a JVM application will:

- decide whether a solver is actually needed, and which problem type it is;
- start from a verified recipe in the [Optimisation Cookbook](https://www.ojalgo.org/optimisation-cookbook/) rather than write a model from scratch;
- follow the rules that decide whether a model is correct and fast — checking the result state, rounding integer values, unique constraint names, tight linking instead of big-M, symmetry breaking, time limits;
- know how to debug an infeasible or slow model.

## Install in Claude Code

```text
/plugin marketplace add optimatika/ojAlgo-skills
/plugin install ojalgo@ojalgo
```

Or copy [`plugins/ojalgo/skills/ojalgo-optimisation`](plugins/ojalgo/skills/ojalgo-optimisation) into `~/.claude/skills/` (for yourself) or `.claude/skills/` in a project (for everyone working on it).

## Other agents

The skill is a plain [`SKILL.md`](plugins/ojalgo/skills/ojalgo-optimisation/SKILL.md) in the open Agent Skills format. For any agent that supports skills, copy the `ojalgo-optimisation` folder into that agent's skills directory. For one that does not, the file still works as reference material to give the agent as context.

## Links

- ojAlgo: https://www.ojalgo.org/ · source: https://github.com/optimatika/ojAlgo
- Optimisation Cookbook: https://www.ojalgo.org/optimisation-cookbook/
- Commercial support and the Optimisation Service: https://www.optimatika.se/

ojAlgo and this skill are MIT licensed.
