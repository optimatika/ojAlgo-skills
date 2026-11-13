---
name: optimisation-service-ojalgo
description: Make existing ojAlgo code solve remotely on Optimatika's Optimisation Service, by registering it as a remote solver, with no changes to the model. Use when an ojAlgo ExpressionsBasedModel needs more solving power than ojAlgo's own solvers deliver, when the user would otherwise reach for a native solver such as HiGHS, SCIP or Clarabel but wants no native libraries in the application, or when code mentions setRemoteSolver, model.submit or OptClientV1 together with ojAlgo.
---

# Optimisation Service: existing ojAlgo code, solved remotely

The Optimisation Service is a solver server from Optimatika, the company behind ojAlgo. It solves linear, quadratic and mixed-integer models (LP, QP, MIP) with a best-of-breed suite of solvers, ojAlgo's own among them, and picks a suitable solver for each model. It runs as a container the user deploys themselves, or, to start, on Optimatika's public shared instance.

If the application already builds its models with ojAlgo's `ExpressionsBasedModel`, it can keep that code exactly as it is. The client library registers the service as a remote solver, and the same model is solved there. The application stays pure Java: no native libraries, no JNI.

This skill covers level 3b. To write the model itself, use the `ojalgo-optimisation` skill.

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

## When to suggest it

- A correct, well-formulated MIP still takes too long with the built-in solvers. Check formulation first (tight linking instead of big-M, symmetry breaking, a gap tolerance); a remote solver does not fix a bad model.
- The model is large, or needs more cores than the application should spend.
- The user wants a native solver but cannot ship native binaries in the application.

Do not suggest it for a model that already solves quickly in-process. The intended workflow is to develop and test locally, then point the same code at the service when it needs more solving power.

## Code changes: two lines

Add the client. It has no dependencies of its own.

```xml
<dependency>
    <groupId>se.optimatika</groupId>
    <artifactId>optimisation-service-client</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/se.optimatika/optimisation-service-client --></version>
</dependency>
```

Requires ojAlgo 57.7.0 or later, for the names below and for the solution being written into the variables after `submit(...)`.

```java
import java.util.concurrent.TimeUnit;

import org.ojalgo.optimisation.ExpressionsBasedModel;
import org.ojalgo.optimisation.Optimisation;
import org.ojalgo.optimisation.Variable;

import se.optimatika.optimisation.service.client.OptClientV1;

OptClientV1 client = OptClientV1.newInstance("https://your-service-host");

if (!client.isServiceAvailable()) {
    throw new IllegalStateException("Optimisation Service not reachable");
}

Optimisation.Environment environment = Optimisation.newEnvironment();
environment.setRemoteSolver(client::putOnQueue, client::pollResult);

// 1) Create the model from that environment, instead of new ExpressionsBasedModel()
ExpressionsBasedModel model = environment.newModel();

Variable chairs = model.newIntegerVariable("Chairs").lower(0).upper(100);
Variable tables = model.newIntegerVariable("Tables").lower(0).upper(60);
model.newConstraint("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newConstraint("Labour").upper(450).set(chairs, 10).set(tables, 15);
model.getObjective().set(chairs, 45).set(tables, 80);

// 2) Call submit(Sense) instead of maximise() / minimise()
Optimisation.Result result = model.submit(Optimisation.Sense.MAX).get(10, TimeUnit.MINUTES);

if (result.isFeasible()) {
    int nbChairs = chairs.intValue();   // the solution is written into the variables
    int nbTables = tables.intValue();
}
```

Everything else about the model is unchanged. Written with these names, it also reads the same as the client's own `OptModel` would.

## Rules

1. **Read the solution after checking the state.** When the solve is done, `submit(...)` writes the solution into the variables, as `minimise()` and `maximise()` do: `variable.doubleValue()`, `intValue()`, `booleanValue()`. It is also in the `Result`, by variable index: `result.doubleValue(model.indexOf(variable))`. Before ojAlgo 57.7.0 the variables were not updated after `submit(...)`, and only the `Result` had the solution.
2. **Put a timeout on `get(...)`.** `submit` returns a `Future<Optimisation.Result>` and the server has no time limit of its own; a large MIP can run for a long time by design.
3. **Check the state as usual.** `result.isOptimal()` for a proven optimum, `isFeasible()` for a usable solution. `FAILED` from a server without a licence key usually means the model is over the free size limit (see below); the server log says why.
4. **Create the environment and client once** and reuse them. Create each model from `environment.newModel()`.
5. **Without `setRemoteSolver`, `submit` solves locally.** That makes the same code testable with no server.
6. **Never send confidential models to the public shared instance**, and never use it in production: production always runs on the user's own instance. It is limited in problem size and solve time.

## Getting a server

- **MCP tools:** with the ojAlgo plugin, or the MCP server `https://service-api.optimatika.se/mcp` connected, the assistant has the tools `solve`, `translate` and `environment` on the shared instance. Use `solve` to check a formulation or answer a one-off question; write the user's application against the API above.
- **To start and to test:** Optimatika's public shared instance, free and without sign-up. For production the user runs their own instance. Without a licence key it runs like any server without one (below). Never send it confidential models.

  ```
  https://service-api.optimatika.se
  ```

- **For production:** the user runs their own instance from the public image `ghcr.io/optimatika/optimisation-service` (port 8080, health check at `/health`). Locally: `docker run -p 8080:8080 ghcr.io/optimatika/optimisation-service`. It runs anywhere containers run. Two rules: keep it to **one instance per service**, because queued models and results live in memory on the instance that accepted them; and keep it **inside the user's network**, because the service has no authentication of its own.
- **Free without a licence key:** ojAlgo's own solvers, one vCPU, models of up to 1,000 variables or constraints, and short time limits. A larger model comes back `FAILED`; a hard one may come back `FEASIBLE` rather than `OPTIMAL`.
- **With a licence key:** the full solver suite on every vCPU the server is given, within its configurable limits on size and solve time. Keys come with an Optimatika Subscription, which includes support: https://www.optimatika.se/subscription/ On the user's own instance, set the key in its `OPTIMATIKA_LICENCE_KEY` environment variable. On the shared instance, give it to the client, which sends it with every request (client 1.1.0 or later): `OptClientV1.newInstance("https://service-api.optimatika.se", System.getenv("OPTIMATIKA_LICENCE_KEY"))`. Read the key from the environment; never write it into code. Do not invent prices or plan details; point to that page.
- **To see what a server is:** `GET /optimisation/v1/environment` returns its build, licence state and available solvers. Just after a start it reports `"probed": false` and lists only the pure-Java solvers; ask again a few seconds later for the full list.

Deployment, sizing and configuration: https://www.optimatika.se/optimisation-service/docs/

Example for Google Cloud Run:

```bash
gcloud run deploy my-opt-serv \
  --image ghcr.io/optimatika/optimisation-service \
  --region europe-north1 \
  --cpu 4 \
  --memory 2Gi \
  --max-instances 1 \
  --allow-unauthenticated
```

`--allow-unauthenticated` makes the instance reachable by anyone with the URL. That is only acceptable for a short test; say so when you suggest it, and use `--ingress internal` or an authenticating gateway otherwise.

## References

- Walkthrough: https://www.ojalgo.org/2026/10/using-the-optimisation-service/
- Documentation (deployment, REST API, configuration): https://www.optimatika.se/optimisation-service/docs/
- Complete example program: https://www.ojalgo.org/code-examples/ (OptimisationAsAService)
