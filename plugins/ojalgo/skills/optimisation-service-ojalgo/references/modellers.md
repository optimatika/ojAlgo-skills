# `OptModel` and `ExpressionsBasedModel`, side by side

Two modellers can build a model for the Optimisation Service. `OptModel` is part of the client library `optimisation-service-client`: no ojAlgo dependency, kept working on older Java versions, always solves on the service. `ExpressionsBasedModel` is ojAlgo's modeller: far richer, solves in-process or on the service, and follows the latest Java version.

Use this file to write either one, or to translate a model from one to the other.

## Step by step

| Step | `OptModel` (client library) | `ExpressionsBasedModel` (ojAlgo) |
|---|---|---|
| Create the model | `OptModel model = client.newModel();` | `ExpressionsBasedModel model = new ExpressionsBasedModel();` to solve in-process, or `environment.newModel()` with a remote solver set |
| Continuous variable | `OptVariable x = model.newRealVariable("x");` | `Variable x = model.newVariable("x");` |
| Integer variable | `model.newIntegerVariable("n")` | `model.newVariable("n").integer()` |
| Binary variable | `model.newBinaryVariable("b")` | `model.newVariable("b").binary()` |
| Variable bounds | `.lower(0).upper(100)` | `.lower(0).upper(100)` |
| Constraint | `model.newConstraint("c")` | `model.newExpression("c")` |
| Constraint limits | `.lower(v)`, `.upper(v)`, `.level(v)` for equality | `.lower(v)`, `.upper(v)`, `.level(v)` for equality |
| Linear term in a constraint | `.set(x, 2.5)` | `.set(x, 2.5)` |
| Quadratic term in a constraint | not available | `.set(x, y, 2.5)` |
| Linear objective term | `model.objective().set(x, 3)` | `x.weight(3)` |
| Quadratic objective term | `model.objective().set(x, y, 0.5)` | an expression with a weight: `model.newExpression("q").weight(1).set(x, y, 0.5)` |
| Solve | `model.maximise()` or `model.minimise()`, always remote, returns `Future<OptResult>` | `model.maximise()` or `model.minimise()` in-process, returns `Optimisation.Result`; `model.submit(Optimisation.Sense.MAX)` remote, returns `Future<Optimisation.Result>` |
| Was it solved? | `result.isOptimal()`, `result.isFeasible()` | `result.getState().isOptimal()`, `result.getState().isFeasible()` |
| Objective value | `result.getValue()` (a `BigDecimal`) | `result.getValue()` (a `double`) |
| A variable's value | `x.doubleValue()`; the values are written back to the variables | In-process: `x.getValue()`. After `submit(...)`: `result.doubleValue(model.indexOf(x))`, because the variables are not updated |
| The whole solution | `result.getSolution()`, in the order the variables were created | `result`, indexed in the order the variables were created |
| Write the model out, to read what was built | `model.exportModel("LP")` returns an `InputStream`; `"MPS"` and `"EBM"` also work. LP and MPS are produced by the service. | `model.writeTo(Path.of("model.lp"))`; the format follows the file name |
| Give up on a solve | `future.cancel(true)` also aborts it on the server | `model.options.time_abort` (milliseconds) in-process; a timeout on `get(...)` when remote |

## The same model, both ways

With `OptModel`:

```java
import java.util.concurrent.TimeUnit;

import se.optimatika.optimisation.service.client.OptClientV1;
import se.optimatika.optimisation.service.client.OptModel;
import se.optimatika.optimisation.service.client.OptResult;
import se.optimatika.optimisation.service.client.OptVariable;

OptClientV1 client = OptClientV1.newInstance("https://your-service-host");

OptModel model = client.newModel();

OptVariable chairs = model.newIntegerVariable("Chairs").lower(0).upper(100);
OptVariable tables = model.newIntegerVariable("Tables").lower(0).upper(60);

model.newConstraint("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newConstraint("Labour").upper(450).set(chairs, 10).set(tables, 15);

model.objective().set(chairs, 45).set(tables, 80);

OptResult result = model.maximise().get(10, TimeUnit.MINUTES);

if (result.isFeasible()) {
    long nbChairs = Math.round(chairs.doubleValue());
    long nbTables = Math.round(tables.doubleValue());
}
```

With `ExpressionsBasedModel`, solved in-process:

```java
import org.ojalgo.optimisation.ExpressionsBasedModel;
import org.ojalgo.optimisation.Optimisation;
import org.ojalgo.optimisation.Variable;

ExpressionsBasedModel model = new ExpressionsBasedModel();

Variable chairs = model.newVariable("Chairs").lower(0).upper(100).integer().weight(45);
Variable tables = model.newVariable("Tables").lower(0).upper(60).integer().weight(80);

model.newExpression("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newExpression("Labour").upper(450).set(chairs, 10).set(tables, 15);

Optimisation.Result result = model.maximise();

if (result.getState().isFeasible()) {
    long nbChairs = Math.round(chairs.getValue().doubleValue());
    long nbTables = Math.round(tables.getValue().doubleValue());
}
```

## Translating between them

The two differences that need thought are the objective and reading the result. Everything else is a rename.

**The objective.** `OptModel` has one objective object. `ExpressionsBasedModel` has none: the objective is the sum of every variable's weight, plus every expression that has a weight.

- `ExpressionsBasedModel` to `OptModel`: each `variable.weight(w)` becomes `model.objective().set(variable, w)`. For each expression with `weight(w)`, add its terms to the objective multiplied by `w`. If that expression also has a lower or upper limit, it is a constraint as well: create a `newConstraint` for the limits.
- `OptModel` to `ExpressionsBasedModel`: each linear objective term becomes a `weight` on the variable. Collect the quadratic terms in one expression with `weight(1)`.

**Reading the result.** `OptModel` writes the solution back to its variables. `ExpressionsBasedModel` does that only when it solves in-process; after `submit(...)` read from the `Result` by index.

**What does not translate from ojAlgo.** Quadratic constraints, solver options (`model.options`), special ordered sets, and solving in-process have no `OptModel` counterpart. If the model needs those, keep it in ojAlgo.

## Writing a model so it translates easily

1. Build the model in one method that takes the application's data and returns the application's own result type. Nothing outside that method should see a modeller class.
2. Keep constraints and objective apart. In ojAlgo, put weights on variables, and use a weighted expression only for quadratic objective terms; do not give a weight to an expression that is also a constraint.
3. Create variables in a fixed, documented order, and name every variable and constraint. The solution vector follows creation order in both modellers.
4. Read the solution in one place, through one small function per variable type, and round integer and binary values there.
5. Stay within what both support unless there is a reason not to: bounds, linear constraints, a linear or quadratic objective.
