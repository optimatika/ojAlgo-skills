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

Four skills in the open [Agent Skills](https://agentskills.io) format. Each is a single Markdown file of instructions and examples.

- `ojalgo-optimisation`: writing and debugging optimisation models with ojAlgo.

Three more cover Optimatika's [Optimisation Service](https://www.optimatika.se/optimisation-service/), a solver server you deploy yourself that runs HiGHS, SCIP and Clarabel alongside ojAlgo's own solvers. They match the three ways to use it:

- `optimisation-service-rest`: the REST API, from any programming language. Submit a model as MPS or LP text, poll for the result.
- `optimisation-service-client`: the Java client library, for any JVM language. Build a model with its small modelling API, or submit model files.
- `optimisation-service-ojalgo`: existing ojAlgo code. Register the service as a remote solver and keep the model code unchanged.

Each also covers running the server, the free tier and licence keys.

The plugin contains no code, hooks, scripts or MCP servers. It runs nothing, stores nothing and sends nothing anywhere. The skills refer Claude to public pages on ojalgo.org and optimatika.se. Code that Claude writes with the service skills sends your model to a server address that you supply.

## Example prompts

- "We have 40 orders and 6 trucks with weight limits. Write Java code that assigns orders to trucks using as few trucks as possible."
- "This ojAlgo model returns INFEASIBLE. Help me find out which constraint is the problem."
- "Plan next week's production for these five products given machine hours and material stock."
- "This ojAlgo MIP takes 20 minutes. Can we solve it on the Optimisation Service instead? Show me the code change and how to deploy it."
- "I have a model in an LP file. Write a Python script that solves it over HTTP with the Optimisation Service."

## Links

- ojAlgo: https://www.ojalgo.org/ (source: https://github.com/optimatika/ojAlgo)
- Updating old ojAlgo code: https://www.ojalgo.org/updating-old-code/
- Commercial support and the Optimisation Service: https://www.optimatika.se/

ojAlgo and this plugin are MIT licensed. Developed by Optimatika AB.
