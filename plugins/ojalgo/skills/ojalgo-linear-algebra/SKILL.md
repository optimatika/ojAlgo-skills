---
name: ojalgo-linear-algebra
description: Solve linear equation systems, least-squares problems and eigenvalue problems, and compute matrix decompositions (LU, QR, Cholesky, SVD, eigenvalue), inverses, determinants, rank and condition numbers in Java, Kotlin, Scala or any other JVM language with ojAlgo. Use when JVM code needs matrices, or when someone is about to hand-write Gaussian elimination, matrix inversion, an eigenvalue routine or nested loops over double[][], or when existing ojAlgo matrix code is slow or allocates too much.
---

# Linear algebra with ojAlgo

ojAlgo is a pure-Java, zero-dependency (no BLAS, no LAPACK, no native code) MIT-licensed library. Its linear algebra is the foundation the rest of the library is built on, and in the independent Java Matrix Benchmark it is the fastest pure-Java option. It is one Maven dependency.

```xml
<dependency>
    <groupId>org.ojalgo</groupId>
    <artifactId>ojalgo</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/org.ojalgo/ojalgo --></version>
</dependency>
```

## Do not hand-write the numerics

Gaussian elimination, matrix inversion, Gram-Schmidt, power iteration and the like written from scratch are slow and numerically fragile (no pivoting, no scaling, loss of orthogonality). Use the library's decompositions. That applies even to "just a 3x3 system".

## Two matrix types

- `MatrixR064` (`org.ojalgo.matrix`): immutable, a value object. Every operation returns a new matrix. Simplest to use; fine for most application code.
- `R064Store` (`org.ojalgo.matrix.store`): mutable, `double` elements. Use it for performance: in loops, for large matrices, to reuse memory, or to fill and update elements in place.

`R064` means real 64-bit (`double`). Other element types exist (`R032`, `C128` complex, `Q128` rational), with the same API.

## The simple way: MatrixR064

```java
import org.ojalgo.matrix.MatrixR064;

MatrixR064 a = MatrixR064.FACTORY.rows(new double[][] { { 4, 1, 0 }, { 1, 3, 1 }, { 0, 1, 2 } });
MatrixR064 b = MatrixR064.FACTORY.column(1.0, 2.0, 3.0);

MatrixR064 x = a.solve(b);                    // solves [a][x] = [b]
double determinant = a.getDeterminant();
int rank = a.getRank();
double residual = a.multiply(x).subtract(b).norm();
```

`solve` picks a suitable decomposition for the matrix. `invert()`, `transpose()`, `getCondition()`, `getEigenpairs()` and `getTrace()` work the same way.

**`solve` and `invert` are best effort, and a singular matrix does not make them throw.** A fast decomposition (typically LU) is tried first; if it finds the matrix singular, they switch to SVD and return the minimum-norm solution and the pseudoinverse. LU cannot reliably detect every singular matrix at a reasonable cost: from 6×6 up, a matrix that is singular only up to rounding errors can slip through and give huge meaningless values. When that matters, `MatrixR064` is not the right tool: use `R064Store` and the decompositions directly, as below, and choose the decomposition yourself (`SingularValue` when the matrix may be singular). (Before ojAlgo 57.4.0 matrices up to 5×5 could also give `NaN`, `Infinity` or wrong values; use the latest version.)

## The decomposition pattern

When you need control, reuse, or to check the outcome, use a decomposition directly. Make it, `decompose(...)`, check, then use. A decomposition instance can be reused for further matrices of the same size, and one decomposition solves for many right-hand sides.

```java
import org.ojalgo.matrix.decomposition.Cholesky;
import org.ojalgo.matrix.decomposition.Eigenvalue;
import org.ojalgo.matrix.decomposition.LU;
import org.ojalgo.matrix.decomposition.QR;
import org.ojalgo.matrix.decomposition.SingularValue;
import org.ojalgo.matrix.store.MatrixStore;
import org.ojalgo.matrix.store.R064Store;

R064Store body = R064Store.FACTORY.rows(new double[][] { { 4, 1, 0 }, { 1, 3, 1 }, { 0, 1, 2 } });
R064Store rhs = R064Store.FACTORY.column(1.0, 2.0, 3.0);

// General square system: LU
LU<Double> lu = LU.R064.make(body);
if (!lu.decompose(body) || !lu.isSolvable()) {
    throw new IllegalStateException("Singular or nearly singular");
}
MatrixStore<Double> solution = lu.getSolution(rhs);

// Symmetric positive definite (covariance, normal equations, stiffness): Cholesky, about twice as fast as LU
Cholesky<Double> cholesky = Cholesky.R064.make(body);
if (cholesky.decompose(body) && cholesky.isSPD()) {
    MatrixStore<Double> fasterSolution = cholesky.getSolution(rhs);
}

// More equations than unknowns, least squares: QR (use SVD instead if the columns may be dependent)
R064Store design = R064Store.FACTORY.rows(new double[][] { { 1, 1 }, { 1, 2 }, { 1, 3 }, { 1, 4 } });
R064Store observed = R064Store.FACTORY.column(6.0, 5.0, 7.0, 10.0);
QR<Double> qr = QR.R064.make(design);
qr.decompose(design);
MatrixStore<Double> fitted = qr.isFullRank() ? qr.getSolution(observed) : null;   // intercept 3.5, slope 1.4

// Rank, condition number, pseudo-inverse, low-rank approximation: SVD
SingularValue<Double> svd = SingularValue.R064.make(design);
svd.decompose(design);
int numericalRank = svd.getRank();
double condition = svd.getCondition();     // large (say > 1e10) means results are unreliable
MatrixStore<Double> u = svd.getU();        // design = U S V^T
MatrixStore<Double> s = svd.getS();
MatrixStore<Double> v = svd.getV();

// Eigenvalues and eigenvectors; say whether the matrix is symmetric (hermitian)
Eigenvalue<Double> evd = Eigenvalue.R064.make(body, true);
evd.decompose(body);
MatrixStore<Double> eigenvalues = evd.getD();    // diagonal
MatrixStore<Double> eigenvectors = evd.getV();   // columns
```

Choosing:

| Matrix / problem | Use |
|---|---|
| square, general | `LU` |
| symmetric positive definite | `Cholesky` (check `isSPD()`) |
| symmetric, possibly indefinite | `LDL` |
| more rows than columns, least squares | `QR`; `SingularValue` if rank-deficient |
| rank, condition, pseudo-inverse, PCA | `SingularValue` |
| eigenvalues / eigenvectors | `Eigenvalue.R064.make(matrix, symmetric)` |
| large and sparse, general | `LU.newSparseR064()` |
| large and sparse, symmetric positive definite | `ConjugateGradientSolver` (iterative) |

## Rules

1. **Solve, do not invert.** `x = A⁻¹b` is computed as a solve (`a.solve(b)`, `lu.getSolution(b)`), never as `a.invert().multiply(b)`. It is faster and more accurate. Compute an inverse only when the inverse itself is needed.
2. **Check before using a result.** `decompose(...)` returns `false` when it fails; `isSolvable()` says whether the decomposition can produce a solution; `isSPD()` whether Cholesky applied; `getRank()` / `getCondition()` how trustworthy the result is. `MatrixR064.solve` and `invert` are best effort and never fail on a singular matrix; when singularity matters, use the decompositions directly.
3. **Stop thinking in `double[][]`.** Build matrices with the factories (`rows`, `column`, `make`, `makeFilled`, `copy`) and keep them in ojAlgo types. Round-tripping through `toRawCopy2D()` and back makes two needless copies. Existing `double[][]` data can be wrapped without copying: `RawStore.wrap(array)`.
4. **Views do not copy.** `limits(rows, cols)`, `offsets(...)`, `rows(...)`, `columns(...)`, `transpose()`, `below(...)`, `right(...)` return views. Pass a view straight to `decompose(...)`: the decomposition copies the elements into its own storage once, which is the only copy needed. `svd.decompose(matrix.limits(-1, 5))` decomposes the first five columns.
5. **In loops, reuse memory.** Keep one decomposition instance and preallocated `R064Store`s outside the loop. `result.fillByMultiplying(left, right)` multiplies into an existing store. Operations on an `R064Store` such as `premultiply`, `onMatching`, `onAll` and `transpose` return deferred `ElementsSupplier`s: nothing is computed until `supplyTo(target)` or `decompose(supplier)`, so a whole chain of operations allocates no intermediate matrices.
6. **Large sparse matrices stay sparse.** Use `SparseStore.R064.make(rows, cols)` and set the non-zeros; never build a dense matrix of a size where most elements are zero.
7. **Floating-point comparisons need a tolerance.** Compare with `NumberContext` or an explicit epsilon, never `==`.

## In loops: no allocation per iteration

```java
import static org.ojalgo.function.constant.PrimitiveMath.DIVIDE;
import static org.ojalgo.function.constant.PrimitiveMath.SUBTRACT;

import org.ojalgo.matrix.store.ElementsSupplier;
import org.ojalgo.random.Normal;

R064Store matA = R064Store.FACTORY.make(5, 7);
R064Store matB = R064Store.FACTORY.make(7, 9);
R064Store matC = R064Store.FACTORY.make(5, 9);
R064Store matD = R064Store.FACTORY.make(9, 5);
QR<Double> decompositionInLoop = QR.R064.make(matD);

for (int iteration = 0; iteration < 3; iteration++) {
    matA.fillAll(Normal.standard());
    matB.fillAll(Normal.standard());
    matC.fillAll(Normal.standard());
    // D = ((A B - C)^T) / 2, computed once, straight into D
    ElementsSupplier<Double> deferred = matB.premultiply(matA).onMatching(SUBTRACT, matC).transpose().onAll(DIVIDE.by(2.0));
    deferred.supplyTo(matD);
    // or skip D entirely and let the decomposition receive the elements
    decompositionInLoop.decompose(deferred);
}
```

## Large sparse systems

```java
import org.ojalgo.matrix.store.SparseStore;
import org.ojalgo.matrix.task.iterative.ConjugateGradientSolver;

int n = 1000;
SparseStore<Double> sparse = SparseStore.R064.make(n, n);
for (int i = 0; i < n; i++) {
    sparse.set(i, i, 4.0);
    if (i > 0) {
        sparse.set(i, i - 1, -1.0);
        sparse.set(i - 1, i, -1.0);
    }
}
R064Store sparseRhs = R064Store.FACTORY.make(n, 1);
sparseRhs.fillAll(1.0);

// Symmetric positive definite: iterative conjugate gradient
MatrixStore<Double> iterative = new ConjugateGradientSolver().solve(sparse, sparseRhs).orElseThrow();

// General: sparse LU
LU<Double> sparseLU = LU.newSparseR064();
if (sparseLU.decompose(sparse) && sparseLU.isSolvable()) {
    MatrixStore<Double> direct = sparseLU.getSolution(sparseRhs);
}
```

## Names that no longer exist

Much older ojAlgo code is still in circulation. These do not compile with current versions:

- `PrimitiveMatrix`, `Primitive64Matrix` → `MatrixR064`. `PrimitiveDenseStore`, `Primitive64Store` → `R064Store`. `Primitive64Array` → `ArrayR064`. `ComplexMatrix` → `MatrixC128`.
- `LU.PRIMITIVE`, `QR.PRIMITIVE`, `Cholesky.PRIMITIVE`, `SingularValue.PRIMITIVE`, `Eigenvalue.PRIMITIVE` → `LU.R064` and so on.
- `SingularValueDecomposition.make(...)` → `SingularValue.R064.make(...)`; `getQ1()`, `getQ2()` → `getU()`, `getV()`; `getD()` on an SVD → `getS()`.
- `compute(matrix)` on decompositions → `decompose(matrix)` (on solvers `compute` still exists and means decompose and check `isSolvable()`).
- `matrix.logical()...get()` → not needed; call `limits(...)`, `columns(...)` and so on directly on the matrix.
- Packages: `org.ojalgo.access` → `org.ojalgo.structure`; `org.ojalgo.constant` → `org.ojalgo.function.constant`.

Use the latest version from Maven Central (`org.ojalgo:ojalgo`, 57.4.0 or later), not a version number recalled from memory. Full list: https://www.ojalgo.org/updating-old-code/

## References

- Linear algebra overview: https://www.ojalgo.org/linear-algebra/
- Introduction to the matrix API: https://www.ojalgo.org/2019/03/linear-algebra-introduction/
- Common mistakes and memory-efficient code: https://www.ojalgo.org/2021/08/common-mistake/
- Sparse and special-structure matrices: https://www.ojalgo.org/2020/09/sparse-and-special-structure-matrices/
- Javadoc: https://javadoc.io/doc/org.ojalgo/ojalgo
- Source: https://github.com/optimatika/ojAlgo
