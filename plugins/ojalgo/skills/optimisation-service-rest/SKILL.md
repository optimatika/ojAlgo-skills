---
name: optimisation-service-rest
description: Solve LP, QP and MIP models over HTTP with Optimatika's Optimisation Service REST API, from any programming language. Use when the user has a model as an MPS or CPLEX LP file or can write one, wants to solve it with HiGHS, SCIP or Clarabel without installing a solver, works in Python, JavaScript, Go, C#, a shell script or anything else that can make HTTP requests, or mentions the put-on-queue or poll-result endpoints.
---

# Optimisation Service: the REST API

The Optimisation Service is a solver server from Optimatika, the company behind ojAlgo. It solves linear, quadratic and mixed-integer models (LP, QP, MIP) with HiGHS, SCIP, Clarabel and ojAlgo's own solvers, and picks a suitable solver for each model. The user deploys it themselves as a container; Optimatika hosts nothing and never sees the models.

The REST API is the foundation: submit a model as text, get a key, poll for the result. Any language with an HTTP client can use it.

This skill covers level 1.

## Which way in

The service can be used at three levels. Each builds on the one before.

| Level | What you use | Choose it when | Skill |
|---|---|---|---|
| 1 | The **REST API** | Any programming language. You supply the model as MPS or LP text. | `optimisation-service-rest` |
| 2 | **`OptClientV1`**, the dedicated Java client | JVM code that already has model files, or wants direct control of submitting and polling. | `optimisation-service-client` |
| 3a | **`OptModel`**, a modeller on top of the client | JVM code that builds the model in code and does not use ojAlgo, or must run on an older Java version. | `optimisation-service-client` |
| 3b | ojAlgo's **`ExpressionsBasedModel`**, with the client plugged in as a remote solver | The application already uses ojAlgo, or can run on the latest Java version. | `optimisation-service-ojalgo` |

There are two modellers at level 3 for a reason. `OptModel` ships in the client library, needs no ojAlgo dependency, and is kept working on older Java versions. `ExpressionsBasedModel` is ojAlgo's own, far richer modeller; ojAlgo follows the Java release train, and from Java 28 on it will always require the latest Java version. Do not move a project to ojAlgo just to use the service, and do not rewrite existing ojAlgo models as `OptModel`.

## The protocol

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/optimisation/v1/put-on-queue/{format}/{sense}` | Submit a model. `format` is `MPS` or `LP`; `sense` is `MIN` or `MAX`. Body: the model file as raw bytes. |
| `GET` | `/optimisation/v1/poll-result/{key}` | Status, and the result when done. |
| `POST` | `/optimisation/v1/translate/{from}/{to}` | Convert a model between `MPS`, `LP` and `EBM` (ojAlgo's own format). |
| `POST` | `/optimisation/v1/abort/{key}` | Abandon a queued or running solve. It goes to `DONE` with no `result`. |
| `GET` | `/optimisation/v1/environment` | Build, licence state, available solvers. |
| `GET` | `/health` | Health check: a status code and no body. |

The full OpenAPI specification: https://www.optimatika.se/optimisation-service/openapi.yaml

Submitting returns:

```json
{ "key": "PmkvX3SNQ0gjRtCD", "status": "PENDING" }
```

Polling returns `"status": "PENDING"` while the solver works, then:

```json
{
  "key": "PmkvX3SNQ0gjRtCD",
  "status": "DONE",
  "result": "OPTIMAL 13.0 @ { 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1 }"
}
```

The `result` string is: the solver state, the objective value, then `@` and the solution vector in braces. Values are in the order the variables (columns) appear in the submitted model.

## With curl

```bash
HOST=https://your-service-host

KEY=$(curl -s -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @model.mps \
  "$HOST/optimisation/v1/put-on-queue/MPS/MIN" | jq -r '.key')

while true; do
  RESULT=$(curl -s "$HOST/optimisation/v1/poll-result/$KEY")
  [ "$(echo "$RESULT" | jq -r '.status')" = "PENDING" ] || break
  sleep 1
done
echo "$RESULT"
```

## With Python

```python
import time
import requests

HOST = "https://your-service-host"

with open("model.lp", "rb") as f:
    submitted = requests.post(f"{HOST}/optimisation/v1/put-on-queue/LP/MAX", data=f.read(),
                              headers={"Content-Type": "application/octet-stream"}, timeout=30)
submitted.raise_for_status()
key = submitted.json()["key"]

deadline = time.time() + 600          # the server has no time limit; set your own
delay = 0.1
while True:
    poll = requests.get(f"{HOST}/optimisation/v1/poll-result/{key}", timeout=30)
    poll.raise_for_status()
    body = poll.json()
    if body["status"] != "PENDING":
        break
    if time.time() > deadline:
        raise TimeoutError("solve did not finish in time")
    time.sleep(delay)
    delay = min(delay * 2, 10)

if "result" not in body:            # DONE without a result: the solve was aborted or failed outright
    raise RuntimeError("the solve finished without a result")

state, rest = body["result"].split(" ", 1)
value, vector = rest.split(" @ ")
solution = [float(v) for v in vector.strip("{} ").split(",") if v.strip()]

if state in ("OPTIMAL", "FEASIBLE"):
    print(float(value), solution)
```

## Rules

1. **`DONE` means stop polling, not that there is a solution.** An aborted solve, or one that failed outright, is `DONE` with no `result` field. Then check the state before using the numbers: `OPTIMAL` is a proven optimum; `FEASIBLE` is a usable solution not proven optimal. `INFEASIBLE`, `UNBOUNDED` and `FAILED` carry no solution to use.
2. **Set your own time limit and back off between polls.** The server has no solve timeout; a large MIP can run for a long time by design. When you give up, `POST /optimisation/v1/abort/{key}` so the server stops working on it.
3. **Map the vector by variable order.** The solution has no names. Keep the list of variables in the order they were written to the model file.
4. **Round integer and binary values.** Solvers return 0.9999999 for 1; never compare with `==`.
5. **Handle the status codes.** `400`: the model could not be parsed, or an unknown format or sense. `404`: unknown key, or a result that expired (results are kept one hour after last access). `429`: the queue is full; retry with backoff. `500`: the solve failed; the detail is in the server log, not the response.
6. **Writing the model file.** Most modelling tools export MPS or LP (PuLP, Pyomo, OR-Tools, JuMP, Gurobi and CPLEX formats). LP is easier to read and to generate by hand; MPS is the safer interchange format.

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
