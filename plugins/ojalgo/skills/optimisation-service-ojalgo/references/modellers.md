# `OptModel` and `ExpressionsBasedModel`, side by side

Two modellers can build a model for the Optimisation Service. `OptModel` is part of the client library `optimisation-service-client`: no ojAlgo dependency, kept working on older Java versions, always solves on the service. `ExpressionsBasedModel` is ojAlgo's modeller: far richer, solves in-process or on the service, and follows the latest Java version.

They are separate implementations, but from ojAlgo 58 and client 1.1.0 they share their names: what both can do is written the same way in both. Write either one that way, and translating a model is mostly a matter of changing the types and how the model is created and solved.

Use this file to write either one, or to translate a model from one to the other. The same comparison, for people: https://www.optimatika.se/optimisation-service/docs/expressionsbasedmodel-vs-optmodel/

## Step by step

| Step | `OptModel` (client library) | `ExpressionsBasedModel` (ojAlgo) |
|---|---|---|
| Create the model | `OptModel model = client.newModel();` | `ExpressionsBasedModel model = new ExpressionsBasedModel();` to solve in-process, or `environment.newModel()` with a remote solver set |
| Continuous variable | `model.newRealVariable("x")` | the same |
| Integer variable | `model.newIntegerVariable("n")` | the same |
| Binary variable | `model.newBinaryVariable("b")` | the same |
| Variable type | `OptVariable`, or more precisely `OptVariable.RealVariable`, `IntegerVariable`, `BinaryVariable` | `Variable` |
| Variable bounds | `.lower(0).upper(100)`; real and integer variables are free when created, binary ones between 0 and 1 | the same |
| Constraint | `model.newConstraint("c")`, an `OptConstraint` | `model.newConstraint("c")`, an `Expression` |
| Constraint limits | `.lower(v)`, `.upper(v)`, `.level(v)` for equality | the same |
| Linear term in a constraint | `.set(x, 2.5)` | the same |
| Quadratic term in a constraint | not available | `.set(x, y, 2.5)` |
| Linear objective term | `model.getObjective().set(x, 3)` | the same |
| Quadratic objective term | `model.getObjective().set(x, y, 0.5)` | the same |
| Constant term | `.constant(c)` on the objective and on constraints | not available |
| Solve | `model.maximise()` or `model.minimise()`, always remote, returns `Future<OptResult>` | `model.maximise()` or `model.minimise()` in-process, returns `Optimisation.Result`; `model.submit(Optimisation.Sense.MAX)` with the environment's remote solver, returns `Future<Optimisation.Result>` |
| Was it solved? | `result.isOptimal()`, `result.isFeasible()` | the same |
| Objective value | `result.doubleValue()` | the same |
| A variable's value | `x.doubleValue()`, `n.intValue()`, `b.booleanValue()`; the values are written back to the variables when the solve is done | the same, after `minimise()`, `maximise()` and `submit(...)` |
| The whole solution | `result.doubleValue(i)`, `result.get(i)`, in the order the variables were created | the same |
| Write the model out, to read what was built | `model.exportModel("LP")` returns an `InputStream`; `"MPS"` and `"EBM"` also work. LP and MPS are produced by the service. | `model.writeTo(Path.of("model.lp"))`; the format follows the file name |
| Give up on a solve | `future.cancel(true)` also aborts it on the server | `model.options.time_abort` (milliseconds) in-process; a timeout on `get(...)` when remote, and `cancel` only stops the waiting |

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

model.getObjective().set(chairs, 45).set(tables, 80);

OptResult result = model.maximise().get(10, TimeUnit.MINUTES);

if (result.isFeasible()) {
    int nbChairs = chairs.intValue();
    int nbTables = tables.intValue();
}
```

With `ExpressionsBasedModel`, solved in-process:

```java
import org.ojalgo.optimisation.ExpressionsBasedModel;
import org.ojalgo.optimisation.Optimisation;
import org.ojalgo.optimisation.Variable;

ExpressionsBasedModel model = new ExpressionsBasedModel();

Variable chairs = model.newIntegerVariable("Chairs").lower(0).upper(100);
Variable tables = model.newIntegerVariable("Tables").lower(0).upper(60);

model.newConstraint("Wood").upper(400).set(chairs, 5).set(tables, 20);
model.newConstraint("Labour").upper(450).set(chairs, 10).set(tables, 15);

model.getObjective().set(chairs, 45).set(tables, 80);

Optimisation.Result result = model.maximise();

if (result.isFeasible()) {
    int nbChairs = chairs.intValue();
    int nbTables = tables.intValue();
}
```

To solve it on the service instead, create the model with `environment.newModel()`, from an environment with the client set as its remote solver, and replace `model.maximise()` with `model.submit(Optimisation.Sense.MAX).get(10, TimeUnit.MINUTES)`.

## Translating between them

Written with the shared names, a model translates by changing four things: how the model is created, the declared types (`OptVariable` and `Variable`, `OptConstraint` and `Expression`, `OptResult` and `Optimisation.Result`), the call that solves it, and the imports.

**Older ojAlgo code** writes the objective with weights: a weight on a variable, `x.weight(3)`, and expressions with a weight, often one with `weight(1)` that holds the quadratic terms. That still works, and weights add up with `getObjective()`. Translating it:

- Each `variable.weight(w)` becomes `model.getObjective().set(variable, w)`. For each expression with `weight(w)`, add its terms to the objective multiplied by `w`. If that expression also has a lower or upper limit, it is a constraint as well: create a `newConstraint` for the limits.
- The other old names: `newVariable("x")` is `newRealVariable("x")`, with `.integer()` it is `newIntegerVariable`, with `.binary()` `newBinaryVariable`; `newExpression("c")` is `newConstraint("c")`; `result.getState().isOptimal()` is `result.isOptimal()`; `result.getValue()` is `result.doubleValue()`; `x.getValue().doubleValue()` is `x.doubleValue()`.
- Before ojAlgo 58 the variables were not updated after `submit(...)`; such code reads the solution from the result, `result.doubleValue(model.indexOf(x))`, which still works.

**What does not translate from ojAlgo.** Quadratic constraints, solver options (`model.options`), `add(...)` to accumulate a coefficient (`OptModel` has only `set(...)`, which replaces), and solving in-process have no `OptModel` counterpart. If the model needs those, keep it in ojAlgo.

**What does not translate from `OptModel`.** Constant terms, `constant(...)`, and a value receiver given when a variable is created, `model.newRealVariable("x", value -> ...)`.

## Writing a model so it translates easily

1. Build the model in one method that takes the application's data and returns the application's own result type. Nothing outside that method should see a modeller class.
2. Use the shared names: `newRealVariable`, `newIntegerVariable`, `newBinaryVariable`, `newConstraint`, `getObjective()`. In ojAlgo, do not use weights.
3. Create variables in a fixed, documented order, and name every variable and constraint. The solution vector follows creation order in both modellers.
4. Read the solution in one place, after checking `isOptimal()` or `isFeasible()`: `doubleValue()`, and `intValue()` or `booleanValue()`, which round, for integer and binary variables.
5. Stay within what both support unless there is a reason not to: bounds, linear constraints, a linear or quadratic objective, `set(...)` only.
