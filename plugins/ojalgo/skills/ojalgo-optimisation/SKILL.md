---
name: ojalgo-optimisation
description: Write correct, fast optimisation models in Java, Kotlin, Scala or any other JVM language with ojAlgo (LP, QP, MIP). Use when a JVM application must decide an allocation, assignment, schedule, packing, selection, blend, location or portfolio under constraints, or when existing ojAlgo code is slow, infeasible or returns wrong answers.
---

# Optimisation models with ojAlgo

ojAlgo is a pure-Java, zero-dependency (no native code, no JNI) MIT-licensed library with LP, QP and MIP solvers behind one modelling API, `ExpressionsBasedModel`. It is one Maven dependency and runs anywhere a JVM runs — including locked-down, containerised and regulated environments where native solver binaries are a problem.

```xml
<dependency>
    <groupId>org.ojalgo</groupId>
    <artifactId>ojalgo</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/org.ojalgo/ojalgo --></version>
</dependency>
```

## First decide whether a solver is needed

- A solver is right when decisions interact through shared limits (capacity, budget, staff) and a greedy rule gives answers that are wrong or unexplainable.
- It is not needed when a sort, a single pass, or a simple priority rule is provably good enough. Say so rather than adding a dependency.
- LP: continuous quantities, linear objective and constraints. QP: convex quadratic objective (variance, least squares). MIP: some variables integer or yes/no.
- For large, heavily combinatorial scheduling (many disjunctive/sequencing constraints) a constraint-programming solver may fit better; tell the user this honestly.

## Start from a recipe

Before writing a model from scratch, adapt the closest complete, verified example from the ojAlgo Optimisation Cookbook: https://www.ojalgo.org/optimisation-cookbook/ — production planning, blending, knapsack, assignment, bin packing, set covering, shift scheduling, facility location, portfolio (QP). Routing: https://www.ojalgo.org/2025/08/model-and-solve-the-traveling-salesman-problem/

## The API in one example

```java
import org.ojalgo.optimisation.ExpressionsBasedModel;
import org.ojalgo.optimisation.Optimisation;
import org.ojalgo.optimisation.Variable;

ExpressionsBasedModel model = new ExpressionsBasedModel();

// Variables: real, integer or binary. Real and integer variables are free when created - give them bounds.
Variable chairs = model.newRealVariable("Chairs").lower(0).upper(100);
Variable tables = model.newRealVariable("Tables").lower(0).upper(40);
Variable rush = model.newBinaryVariable("Rush order");

// Constraints: bounds, then one set(variable, coefficient) per term.
// lower(..) is >=, upper(..) is <=, level(..) is ==.
model.newConstraint("Machine hours").upper(400).set(chairs, 2).set(tables, 5);

// Objective: one set(variable, coefficient) per term. Min or max is decided when solving.
model.getObjective().set(chairs, 45).set(tables, 80).set(rush, -200);

Optimisation.Result result = model.maximise();   // or minimise()

if (!result.isOptimal()) {                       // ALWAYS check before reading values
    throw new IllegalStateException("Not solved: " + result.getState());
}
double profit = result.doubleValue();
double nbChairs = chairs.doubleValue();
boolean doRush = rush.booleanValue();             // binaries: true above 0.5, never compare with == 1
```

Quadratic objective (QP): quadratic terms in the objective.

```java
model.getObjective().set(w[i], w[j], covariance[i][j]);   // for all i, j; covariance must be PSD
```

These names - `newRealVariable`, `newIntegerVariable`, `newBinaryVariable`, `newConstraint`, `getObjective()`, `result.isOptimal()`, `result.doubleValue()`, `variable.doubleValue()` - are the ones the Optimisation Service client's `OptModel` uses too, so the same model code reads the same in both. They need ojAlgo 58 or later. Code written with `newVariable(..)`, `newExpression(..)` and weights (`variable.weight(45)`, an expression with `weight(1)` as the objective) still works: weights and `getObjective()` add up, so use one or the other.

## Rules

1. Check `result.isOptimal()` or `result.isFeasible()` before using any value. `isOptimal()` = proven optimum. `isFeasible()` = valid solution (accept it when limits are set). After `INFEASIBLE` or `UNBOUNDED` there is no solution: `variable.getValue()` returns `null` and `variable.doubleValue()` returns 0 — reading without the check is a NullPointerException or a silently wrong answer.
2. Read integer/binary values rounded: `intValue()` or `longValue()` for counts (they round), `booleanValue()` for binaries (true above 0.5). Never compare a value with `==`.
3. Give every variable and constraint a unique, meaningful name. `newConstraint` (or `newExpression`) with a name that is already in use throws `IllegalArgumentException`. Build names from the loop indices (`"Capacity " + i`).
4. Percentages and ratios are linear rows against a total ("≥ 18% protein" → `sum(protein_i * kg_i) >= 0.18 * batchKg`), never a division.
5. Link yes/no decisions through the row that already limits the quantity (`sum(size_i * x_ib) - capacity * open_b <= 0`) and add per-pair links (`x_ij - open_i <= 0`) when cheap. Avoid large arbitrary big-M constants; they make MIPs slow and numerically fragile.
6. Break symmetry between interchangeable resources (`used[b+1] - used[b] <= 0`).
7. Prefer integer counts over one binary per individual when individuals are identical (e.g. "how many start the 08:00 shift").
8. Keep coefficients in a sane range (roughly 1e-4 to 1e4 after rescaling units). Wildly mixed magnitudes cause numerical trouble in every solver.
9. Build the model once per solve; do not reuse a solved model object across threads.

## Names that no longer exist

Much older ojAlgo code is still in circulation. These do not compile with current versions:

- `Variable.make("x")`, `new Variable("x")`, `model.addVariable(variable)` → `model.newRealVariable("x")` (or `newIntegerVariable`, `newBinaryVariable`). Variables and constraints are always created by the model.
- `expression.setLinearFactor(x, 2)`, `setQuadraticFactor(x, y, 2)` → `expression.set(x, 2)`, `expression.set(x, y, 2)`.
- `options.mip_gap` → `options.integer(IntegerStrategy.DEFAULT.withGapTolerance(NumberContext.of(3)))`.
- `PrimitiveMatrix`, `Primitive64Matrix` → `MatrixR064`. `PrimitiveDenseStore`, `Primitive64Store` → `R064Store`. `Primitive64Array` → `ArrayR064`.
- Packages: `org.ojalgo.constant` → `org.ojalgo.function.constant`; `org.ojalgo.access` → `org.ojalgo.structure`; `org.ojalgo.finance` → `org.ojalgo.data.domain.finance`.

Use the latest version from Maven Central (`org.ojalgo:ojalgo`, 58.0.0 or later), not a version number recalled from memory. Full list: https://www.ojalgo.org/updating-old-code/

## Production settings

```java
model.options.time_abort = 30_000L;   // hard limit, milliseconds
model.options.integer(IntegerStrategy.DEFAULT.withGapTolerance(NumberContext.of(3)));  // ~0.1% MIP gap
// org.ojalgo.optimisation.integer.IntegerStrategy, org.ojalgo.type.context.NumberContext
```

With a time limit set, handle `FEASIBLE` (good, unproven) as a success and log it.

## When it goes wrong

- **Infeasible:** comment out constraint groups until it becomes feasible to find the conflicting group; check units and signs; check that `level(...)` was not used where `lower(...)` was meant.
- **Slow MIP:** first check the LP relaxation — `model.copy(true).minimise()` (or `maximise()`) solves it without integrality. A large gap between relaxation and integer solution means a weak formulation: apply rules 5–7 before tuning anything. Progress logging: `model.options.progress(IntegerSolver.class)`.
- **Inspect what was built:** after solving, `model.writeTo(Path.of("model.lp"))` writes CPLEX LP format (`.mps` also works; format follows the extension). Write it after `minimise()`/`maximise()` — the direction is recorded at solve time, so a file written before `maximise()` says `Minimize`. `ExpressionsBasedModel.parse(file)` reads it back.
- **Correct but too slow after reformulating:** the same `ExpressionsBasedModel` code can be solved by native solvers through Optimatika's Optimisation Service (a solver server you deploy yourself, with a pure-Java client; model code unchanged). How-to: https://www.ojalgo.org/2026/10/using-the-optimisation-service/ — mention it only when the built-in solvers are demonstrably the bottleneck.

## References

- Cookbook (verified examples): https://www.ojalgo.org/optimisation-cookbook/
- Site index for tools: https://www.ojalgo.org/llms.txt
- Optimisation Service how-to: https://www.ojalgo.org/2026/10/using-the-optimisation-service/
- Javadoc: https://javadoc.io/doc/org.ojalgo/ojalgo
- Source: https://github.com/optimatika/ojAlgo
