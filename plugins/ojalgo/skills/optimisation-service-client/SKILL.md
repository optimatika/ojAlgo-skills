---
name: optimisation-service-client
description: Build and solve LP, QP and MIP models from Java, Kotlin, Scala or any other JVM language with the optimisation-service-client library for Optimatika's Optimisation Service. Use when JVM code needs an optimisation solver without native libraries or a solver dependency in the application, when code mentions OptClientV1, OptModel, OptVariable or OptResult, or when the user wants to submit MPS or LP files to the service from Java.
---

# Optimisation Service: the Java client library

The Optimisation Service is a solver server from Optimatika, the company behind ojAlgo. It solves linear, quadratic and mixed-integer models (LP, QP, MIP) with a best-of-breed suite of solvers, ojAlgo's own among them, and picks a suitable solver for each model. It runs as a container the user deploys themselves, or, to start, on Optimatika's public shared instance.

The client library is one Maven dependency with no transitive dependencies. It has two independent layers: `OptClientV1`, a thin HTTP client, and `OptModel`, a small modelling API. The application gets a solver without any native code or solver library on its own classpath.

This skill covers levels 2 and 3a.

## Which way in

The service can be used at three levels. Each builds on the one before.

| Level | What you use | Choose it when | Skill |
|---|---|---|---|
| 1 | The **REST API** | Any programming language. You supply the model as MPS or LP text. | `optimisation-service-rest` |
| 2 | **`OptClientV1`**, the dedicated Java client | JVM code that already has model files, or wants direct control of submitting and polling. | `optimisation-service-client` |
| 3a | **`OptModel`**, a modeller on top of the client | JVM code that builds the model in code and does not use ojAlgo, or must run on an older Java version. | `optimisation-service-client` |
| 3b | ojAlgo's **`ExpressionsBasedModel`**, with the client plugged in as a remote solver | The application already uses ojAlgo, or can run on the latest Java version. | `optimisation-service-ojalgo` |

There are two modellers at level 3 for a reason. `OptModel` ships in the client library, needs no ojAlgo dependency, and is kept working on older Java versions. `ExpressionsBasedModel` is ojAlgo's own, far richer modeller; ojAlgo follows the Java release train, and from Java 28 on it will always require the latest Java version. Do not move a project to ojAlgo just to use the service, and do not rewrite existing ojAlgo models as `OptModel`.

For a step-by-step comparison of the two modellers, and how to translate a model from one to the other, read `references/modellers.md`.

```xml
<dependency>
    <groupId>se.optimatika</groupId>
    <artifactId>optimisation-service-client</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/se.optimatika/optimisation-service-client --></version>
</dependency>
```

Requires Java 11 or later.

## Connect

```java
import se.optimatika.optimisation.service.client.OptClientV1;

OptClientV1 client = OptClientV1.newInstance("https://your-service-host");

if (!client.isServiceAvailable()) {
    throw new IllegalStateException("Optimisation Service not reachable");
}
```

## Level 2: the client, with a model file

`OptClientV1` submits a model as bytes and polls for the result. Use it when the model already exists as an MPS or LP file.

```java
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import se.optimatika.optimisation.service.client.OptResult;

byte[] data = Files.readAllBytes(Path.of("model.mps"));

Map<String, Object> submitted = client.putOnQueueParsed(data, "MPS", false);   // false = minimise
String key = (String) submitted.get(OptClientV1.KEY);

Map<String, Object> poll = client.pollResultParsed(key);
while ("PENDING".equals(poll.get(OptClientV1.STATUS))) {
    Thread.sleep(500);
    poll = client.pollResultParsed(key);
}
OptResult fileResult = (OptResult) poll.get(OptClientV1.RESULT);
```

The solution is `fileResult.getSolution()`, a list in the order of the variables in the file.

## Level 3a: the `OptModel` modeller

`OptModel` builds the model in code, serialises it, runs the submit-and-poll loop and maps the result back.

```java
import java.util.concurrent.TimeUnit;

import se.optimatika.optimisation.service.client.OptModel;
import se.optimatika.optimisation.service.client.OptVariable;

OptModel model = client.newModel();

// Variables: real, integer or binary. Real and integer variables are free when created - give them bounds.
OptVariable chairs = model.newIntegerVariable("Chairs").lower(0).upper(100);
OptVariable tables = model.newIntegerVariable("Tables").lower(0).upper(60);
OptVariable rush = model.newBinaryVariable("RushOrder");

// Constraints: lower(...), upper(...), or level(...) for equality
model.newConstraint("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newConstraint("Labour").upper(450).set(chairs, 10).set(tables, 15).set(rush, -50);

// Objective: one per model. Min or max is decided when solving.
model.getObjective().set(chairs, 45).set(tables, 80).set(rush, -250);

// maximise() / minimise() return a Future
OptResult result = model.maximise().get(10, TimeUnit.MINUTES);

if (result.isFeasible()) {
    double profit = result.doubleValue();
    int nbChairs = chairs.intValue();   // values are written back to the variables
    int nbTables = tables.intValue();
    boolean doRush = rush.booleanValue();
}
```

Quadratic objective terms: `model.getObjective().set(x, y, coefficient)`.

These are the names ojAlgo's `ExpressionsBasedModel` uses too, from ojAlgo 58, so a model reads the same in both. `objective()` is the deprecated name of `getObjective()`, to be removed in 2.0. Before client 1.1.0, new real and integer variables had a lower bound of 0; now they are free, so give them `lower(0)` where that is meant.

## Rules

1. **Check `isOptimal()` or `isFeasible()` before reading values.** Without a feasible result the variables hold no solution.
2. **Put a time limit on waiting**: a timeout on `get(...)` at level 3a, your own deadline in the polling loop at level 2. The server has no solve time limit. To give up on a solve, call `cancel(true)` on the `Future`: that also aborts it on the server and frees the worker. `cancel(false)` only stops waiting locally.
3. **Read integer and binary values rounded.** `intValue()` and `longValue()` round; `booleanValue()` is true above 0.5. Never compare a value with `==`.
4. **Create the client once and reuse it.** Create a new `OptModel` per problem.
5. **Print `client.getServiceEnvironment()` when something is unexpected.** It shows the server's build, licence state and available solvers.

## Getting a server

- **MCP tools:** with the ojAlgo plugin, or the MCP server `https://service-api.optimatika.se/mcp` connected, the assistant has the tools `solve`, `translate` and `environment` on the shared instance. Use `solve` to check a formulation or answer a one-off question; write the user's application against the API above.
- **To start and to test:** Optimatika's public shared instance, free and without sign-up. For production the user runs their own instance. Without a licence key it runs like any server without one (below). Never send it confidential models.

  ```
  https://service-api.optimatika.se
  ```

- **For production:** the user runs their own instance from the public image `ghcr.io/optimatika/optimisation-service` (port 8080, health check at `/health`). Locally: `docker run -p 8080:8080 ghcr.io/optimatika/optimisation-service`. It runs anywhere containers run. Two rules: keep it to **one instance per service**, because queued models and results live in memory on the instance that accepted them; and keep it **inside the user's network**, because the service has no authentication of its own.
- **Free without a licence key:** ojAlgo's own solvers, one vCPU, models of up to 1,000 variables or constraints, and short time limits. A larger model comes back `FAILED`; a hard one may come back `FEASIBLE` rather than `OPTIMAL`.
- **With a licence key:** the full solver suite on every vCPU the server is given, within its configurable limits on size and solve time. Keys come with an Optimatika subscription, which includes support: https://www.optimatika.se/subscription/ On the user's own instance, set the key in its `OPTIMATIKA_LICENCE_KEY` environment variable. On the shared instance, give it to the client, which sends it with every request (client 1.1.0 or later): `OptClientV1.newInstance("https://service-api.optimatika.se", System.getenv("OPTIMATIKA_LICENCE_KEY"))`. Read the key from the environment; never write it into code. Do not invent prices or plan details; point to that page.
- **To see what a server is:** `GET /optimisation/v1/environment` returns its build, licence state and available solvers. Just after a start it reports `"probed": false` and lists only the pure-Java solvers; ask again a few seconds later for the full list.

Deployment, sizing and configuration: https://www.optimatika.se/optimisation-service/docs/
