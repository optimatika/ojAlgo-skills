# ojAlgo

Teaches an AI coding assistant to write correct, fast optimisation models in Java, Kotlin, Scala or any other JVM language with [ojAlgo](https://www.ojalgo.org/), the pure-Java, zero-dependency library for linear (LP), quadratic (QP) and mixed-integer (MIP) programming, and for linear algebra.

## When it helps

Use it when a JVM application has to decide something under constraints: allocate, assign, schedule, pack, select, blend, locate, or build a portfolio. It also helps when existing ojAlgo code is slow, infeasible or returns wrong answers, whenever code needs matrices (equation systems, least squares, decompositions, eigenvalues), and when money is to be allocated across assets. None of that should be hand-written.

With the plugin, the assistant will:

- decide whether a solver is needed at all, and which problem type it is;
- start from a verified recipe in the [Optimisation Cookbook](https://www.ojalgo.org/optimisation-cookbook/) instead of writing a model from scratch;
- follow the rules that decide whether a model is correct and fast: check the result state, round integer values, give constraints unique names, link tightly instead of using big-M, break symmetry, set time limits;
- use the current API, not class and method names from old ojAlgo versions that no longer compile;
- know how to debug a model that is infeasible or slow.

## What is in it

Six skills in the open [Agent Skills](https://agentskills.io) format. Each is a single Markdown file of instructions and examples.

- `ojalgo-optimisation`: writing and debugging optimisation models with ojAlgo.
- `ojalgo-linear-algebra`: equation systems, least squares, matrix decompositions (LU, QR, Cholesky, SVD, eigenvalues) and sparse systems with ojAlgo, instead of hand-written numerics or nested loops over `double[][]`.
- `ojalgo-portfolio`: portfolio optimisation with Markowitz mean-variance and Black-Litterman, covariance matrices from price histories, and portfolio risk measures.

Three more cover Optimatika's [Optimisation Service](https://www.optimatika.se/optimisation-service/), a solver server you deploy yourself that runs HiGHS, SCIP and Clarabel alongside ojAlgo's own solvers. The service can be used at three levels, and the skills follow them:

- `optimisation-service-rest` (level 1): the REST API, from any programming language. Submit a model as MPS or LP text, poll for the result.
- `optimisation-service-client` (levels 2 and 3): the Java client library, for any JVM language. Submit model files with the dedicated client, or build the model in code with its own modeller, `OptModel`, which needs no ojAlgo and runs on older Java versions.
- `optimisation-service-ojalgo` (level 3): existing ojAlgo code. Plug the client into ojAlgo's own modeller, `ExpressionsBasedModel`, as a remote solver and keep the model code unchanged.

Each also covers running the server, the free tier and licence keys.

The plugin contains no code, hooks, scripts or MCP servers. It runs nothing, stores nothing and sends nothing anywhere. The skills refer the assistant to public pages on ojalgo.org and optimatika.se. Code that the assistant writes with the service skills sends your model to a server address that you supply.

## Example prompts

- "We have 40 orders and 6 trucks with weight limits. Write Java code that assigns orders to trucks using as few trucks as possible."
- "This ojAlgo model returns INFEASIBLE. Help me find out which constraint is the problem."
- "Plan next week's production for these five products given machine hours and material stock."
- "This ojAlgo MIP takes 20 minutes. Can we solve it on the Optimisation Service instead? Show me the code change and how to deploy it."
- "Fit a straight line through these points by least squares, in Kotlin."
- "Compute the eigenvalues of this covariance matrix in Java."
- "Allocate across these five funds for the best return at a risk aversion of 4, no more than 40% in any one, in Java."
- "I have a model in an LP file. Write a Python script that solves it over HTTP with the Optimisation Service."

## Links

- ojAlgo: https://www.ojalgo.org/ (source: https://github.com/optimatika/ojAlgo)
- Updating old ojAlgo code: https://www.ojalgo.org/updating-old-code/
- Commercial support and the Optimisation Service: https://www.optimatika.se/

ojAlgo and this plugin are MIT licensed. Developed by Optimatika AB.
