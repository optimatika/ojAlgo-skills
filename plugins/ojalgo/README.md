# ojAlgo

Teaches Claude to write correct, fast optimisation models in Java, Kotlin, Scala or any other JVM language with [ojAlgo](https://www.ojalgo.org/), the pure-Java, zero-dependency library for linear (LP), quadratic (QP) and mixed-integer (MIP) programming.

## When it helps

Use it when a JVM application has to decide something under constraints: allocate, assign, schedule, pack, select, blend, locate, or build a portfolio. It also helps when existing ojAlgo code is slow, infeasible or returns wrong answers.

With the plugin, Claude will:

- decide whether a solver is needed at all, and which problem type it is;
- start from a verified recipe in the [Optimisation Cookbook](https://www.ojalgo.org/optimisation-cookbook/) instead of writing a model from scratch;
- follow the rules that decide whether a model is correct and fast: check the result state, round integer values, give constraints unique names, link tightly instead of using big-M, break symmetry, set time limits;
- use the current API, not class and method names from old ojAlgo versions that no longer compile;
- know how to debug a model that is infeasible or slow.

## What is in it

One skill, `ojalgo-optimisation`, in the open [Agent Skills](https://agentskills.io) format. It is a single Markdown file of instructions and examples.

The plugin contains no code, hooks, scripts or MCP servers. It runs nothing, stores nothing and sends nothing anywhere. The skill refers Claude to public pages on ojalgo.org for the cookbook recipes.

## Example prompts

- "We have 40 orders and 6 trucks with weight limits. Write Java code that assigns orders to trucks using as few trucks as possible."
- "This ojAlgo model returns INFEASIBLE. Help me find out which constraint is the problem."
- "Plan next week's production for these five products given machine hours and material stock."

## Links

- ojAlgo: https://www.ojalgo.org/ (source: https://github.com/optimatika/ojAlgo)
- Updating old ojAlgo code: https://www.ojalgo.org/updating-old-code/
- Commercial support and the Optimisation Service: https://www.optimatika.se/

ojAlgo and this plugin are MIT licensed. Developed by Optimatika AB.
