---
name: optimisation-service-client
description: Build and solve LP, QP and MIP models from Java, Kotlin, Scala or any other JVM language with the optimisation-service-client library for Optimatika's Optimisation Service. Use when JVM code needs an optimisation solver without native libraries or a solver dependency in the application, when code mentions OptClientV1, OptModel, OptVariable or OptResult, or when the user wants to submit MPS or LP files to the service from Java.
---

# Optimisation Service: the Java client library

The Optimisation Service is a solver server from Optimatika, the company behind ojAlgo. It solves linear, quadratic and mixed-integer models (LP, QP, MIP) with HiGHS, SCIP, Clarabel and ojAlgo's own solvers, and picks a suitable solver for each model. The user deploys it themselves as a container; Optimatika hosts nothing and never sees the models.

The client library is one Maven dependency with no transitive dependencies. It has two independent layers: `OptClientV1`, a thin HTTP client, and `OptModel`, a small modelling API. The application gets a solver without any native code or solver library on its own classpath.

Other ways in: any language can call the REST API directly (skill `optimisation-service-rest`), and existing ojAlgo `ExpressionsBasedModel` code can solve remotely without being rewritten (skill `optimisation-service-ojalgo`).

```xml
<dependency>
    <groupId>se.optimatika</groupId>
    <artifactId>optimisation-service-client</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/se.optimatika/optimisation-service-client --></version>
</dependency>
```

Requires Java 11 or later.

## Build and solve a model

```java
import java.util.concurrent.TimeUnit;

import se.optimatika.optimisation.service.client.OptClientV1;
import se.optimatika.optimisation.service.client.OptModel;
import se.optimatika.optimisation.service.client.OptResult;
import se.optimatika.optimisation.service.client.OptVariable;

OptClientV1 client = OptClientV1.newInstance("https://your-service-host");

if (!client.isServiceAvailable()) {
    throw new IllegalStateException("Optimisation Service not reachable");
}

OptModel model = client.newModel();

// Variables: real, integer or binary, with bounds
OptVariable chairs = model.newIntegerVariable("Chairs").lower(0).upper(100);
OptVariable tables = model.newIntegerVariable("Tables").lower(0).upper(60);
OptVariable rush = model.newBinaryVariable("RushOrder");

// Constraints: lower(...), upper(...), or level(...) for equality
model.newConstraint("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newConstraint("Labour").upper(450).set(chairs, 10).set(tables, 15).set(rush, -50);

// Objective: one per model
model.objective().set(chairs, 45).set(tables, 80).set(rush, -250);

// maximise() / minimise() return a Future
OptResult result = model.maximise().get(10, TimeUnit.MINUTES);

if (result.isFeasible()) {
    double profit = result.getValue().doubleValue();
    long nbChairs = Math.round(chairs.doubleValue());   // values are written back to the variables
    long nbTables = Math.round(tables.doubleValue());
    boolean doRush = rush.doubleValue() > 0.5;
}
```

Quadratic objective terms: `model.objective().set(x, y, coefficient)`.

## Submit an existing MPS or LP file

```java
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

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

Here the solution is `fileResult.getSolution()`, a list in the order of the variables in the file.

## Rules

1. **Check `isOptimal()` or `isFeasible()` before reading values.** Without a feasible result the variables hold no solution.
2. **Put a timeout on `get(...)`.** The server has no solve time limit. To give up on a solve, call `cancel(true)` on the `Future`: that also aborts it on the server and frees the worker. `cancel(false)` only stops waiting locally.
3. **Round integer and binary values.** Use `Math.round(v.doubleValue())` and `> 0.5`, never `==`.
4. **Create the client once and reuse it.** Create a new `OptModel` per problem.
5. **Print `client.getServiceEnvironment()` when something is unexpected.** It shows the server's build, licence state and available solvers.

## Getting a server

- **To experiment:** a public test server, limited in problem size and solve time. Never send it confidential models and never use it in production.

  ```
  https://optimisation-test-service-840974723912.europe-north2.run.app
  ```

- **For real use:** the user runs their own instance from the public image `ghcr.io/optimatika/optimisation-service` (port 8080, health check at `/health`). Locally: `docker run -p 8080:8080 ghcr.io/optimatika/optimisation-service`. It runs anywhere containers run. Two rules: keep it to **one instance per service**, because queued models and results live in memory on the instance that accepted them; and keep it **inside the user's network**, because the service has no authentication of its own.
- **Free without a licence key:** ojAlgo's own solvers, one vCPU, models of up to 1,000 variables or constraints. A larger model comes back `FAILED`.
- **With a licence key:** the full solver suite (HiGHS, SCIP, Clarabel and ojAlgo's own) on the licensed number of vCPUs, no size limit. Keys come with an Optimatika subscription, which includes support: https://www.optimatika.se/subscription/ Set them, all of them separated by spaces, in the `OPTIMATIKA_LICENCE_KEY` environment variable. Do not invent prices or plan details; point to that page.
- **To see what a server is:** `GET /optimisation/v1/environment` returns its build, licence state and available solvers. Just after a start it reports `"probed": false` and lists only the pure-Java solvers; ask again a few seconds later for the full list.

Deployment, sizing and configuration: https://www.optimatika.se/optimisation-service/docs/
