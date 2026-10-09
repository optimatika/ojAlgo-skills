import java.io.File;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Callable;

import org.ojalgo.data.domain.finance.portfolio.MarkowitzModel;
import org.ojalgo.matrix.MatrixR064;
import org.ojalgo.matrix.decomposition.Cholesky;
import org.ojalgo.matrix.decomposition.Eigenvalue;
import org.ojalgo.matrix.decomposition.LU;
import org.ojalgo.matrix.decomposition.QR;
import org.ojalgo.matrix.decomposition.SingularValue;
import org.ojalgo.matrix.store.MatrixStore;
import org.ojalgo.matrix.store.R064Store;
import org.ojalgo.matrix.store.RawStore;
import org.ojalgo.optimisation.Expression;
import org.ojalgo.optimisation.ExpressionsBasedModel;
import org.ojalgo.optimisation.Optimisation;
import org.ojalgo.optimisation.Variable;
import org.ojalgo.optimisation.integer.IntegerSolver;
import org.ojalgo.optimisation.integer.IntegerStrategy;
import org.ojalgo.type.context.NumberContext;

/**
 * Checks that ojAlgo still behaves the way the rules say it does.
 * <p>
 * The rules about writing ojAlgo code are stated in places that have to be edited by hand: the "rules" list in
 * ojAlgo/context7.json (the source; ojalgo.org generates its copies from it), the "Rules that apply to every
 * model" section of the Optimisation Cookbook (www_ojalgo_org/content/optimisation-cookbook.md), and the
 * ojalgo-optimisation, ojalgo-linear-algebra and ojalgo-portfolio skills in this repository. Each check below pins down one behaviour those texts describe.
 * This runs against the latest ojAlgo release (57.4.0 or later), so when a release changes a behaviour the check
 * fails and says which texts to update. After updating them, change the check to expect the new behaviour.
 * <p>
 * The current names used in the texts are simply used here, in {@link #currentNames()}: if one of them is
 * renamed this file stops compiling, which is the same signal.
 */
public class RuleChecks {

    private static final String EVERYWHERE = "ojAlgo/context7.json, the cookbook's rules, the ojalgo-optimisation skill";

    private static int changed = 0;

    public static void main(final String[] args) throws Exception {

        check("A second expression with a name already in use throws IllegalArgumentException", EVERYWHERE + " (the rule about unique expression names)", () -> {
            ExpressionsBasedModel model = new ExpressionsBasedModel();
            Variable x = model.newVariable("x").lower(0).upper(1000).weight(1);
            model.newExpression("limit").upper(10).set(x, 1);
            try {
                model.newExpression("limit").upper(100).set(x, 1);
                return false; // Accepted: the texts say it throws.
            } catch (IllegalArgumentException cause) {
                return true;
            }
        });

        check("After an INFEASIBLE result variable.getValue() returns null", EVERYWHERE + " (the rule about checking the state)", () -> {
            ExpressionsBasedModel model = new ExpressionsBasedModel();
            Variable x = model.newVariable("x").lower(0).upper(1).weight(1);
            model.newExpression("impossible").lower(5).set(x, 1);
            Optimisation.Result result = model.minimise();
            return !result.getState().isFeasible() && x.getValue() == null;
        });

        check("A model file written before maximise() says Minimize, written after it says Maximize", "the cookbook's rule 8, the skill's \"When it goes wrong\"", () -> {
            ExpressionsBasedModel model = new ExpressionsBasedModel();
            Variable x = model.newVariable("x").lower(0).upper(10).weight(1);
            model.newExpression("limit").upper(4).set(x, 1);
            Path before = Files.createTempFile("before", ".lp");
            Path after = Files.createTempFile("after", ".lp");
            model.writeTo(before);
            model.maximise();
            model.writeTo(after);
            String first = Files.readString(before).toLowerCase();
            String second = Files.readString(after).toLowerCase();
            Files.delete(before);
            Files.delete(after);
            return first.contains("minimi") && !first.contains("maximi") && second.contains("maximi");
        });

        String oldNames = "ojAlgo/context7.json (the rule about old names), the skill's \"Names that no longer exist\", ojalgo.org/updating-old-code/";

        for (String name : new String[] { "org.ojalgo.matrix.PrimitiveMatrix", "org.ojalgo.matrix.Primitive64Matrix", "org.ojalgo.matrix.store.PrimitiveDenseStore",
                "org.ojalgo.matrix.store.Primitive64Store", "org.ojalgo.array.Primitive64Array", "org.ojalgo.constant.PrimitiveMath", "org.ojalgo.access.Access1D",
                "org.ojalgo.finance.FinanceUtils" }) {
            check("The old name " + name + " does not exist", oldNames, () -> !RuleChecks.exists(name));
        }

        check("Variable.make(String) and a public Variable constructor do not exist", oldNames,
                () -> !RuleChecks.hasMethod(Variable.class, "make") && Variable.class.getConstructors().length == 0);
        check("ExpressionsBasedModel.addVariable(Variable) does not exist", oldNames, () -> {
            try {
                ExpressionsBasedModel.class.getMethod("addVariable", Variable.class);
                return false;
            } catch (NoSuchMethodException cause) {
                return true; // addVariable() and addVariable(String) do exist, and create the variable.
            }
        });
        check("Expression.setLinearFactor and setQuadraticFactor do not exist", oldNames,
                () -> !RuleChecks.hasMethod(Expression.class, "setLinearFactor") && !RuleChecks.hasMethod(Expression.class, "setQuadraticFactor"));
        check("Optimisation.Options.mip_gap does not exist", oldNames, () -> {
            try {
                Optimisation.Options.class.getField("mip_gap");
                return false;
            } catch (NoSuchFieldException cause) {
                return true;
            }
        });

        String oldLinearAlgebra = "the ojalgo-linear-algebra skill's \"Names that no longer exist\", ojalgo.org/updating-old-code/";

        check("The old name org.ojalgo.matrix.decomposition.SingularValueDecomposition does not exist", oldLinearAlgebra,
                () -> !RuleChecks.exists("org.ojalgo.matrix.decomposition.SingularValueDecomposition"));
        for (Class<?> type : new Class<?>[] { LU.class, QR.class, Cholesky.class, SingularValue.class, Eigenvalue.class }) {
            check(type.getSimpleName() + ".PRIMITIVE does not exist", oldLinearAlgebra, () -> {
                try {
                    type.getField("PRIMITIVE");
                    return false;
                } catch (NoSuchFieldException cause) {
                    return true;
                }
            });
        }
        check("SingularValue.getQ1() and getQ2() do not exist", oldLinearAlgebra,
                () -> !RuleChecks.hasMethod(SingularValue.class, "getQ1") && !RuleChecks.hasMethod(SingularValue.class, "getQ2"));

        for (int size : new int[] { 2, 5, 6, 9 }) {
            String claim = "MatrixR064.solve(..) and invert() on a singular " + size + "x" + size + " matrix give the minimum-norm solution and the SVD pseudoinverse";
            if (size <= 5 && !RuleChecks.isAtLeast(57, 4)) {
                // Fixed in 57.4.0 – before that NaN, Infinity or wrong values, as the skill says
                RuleChecks.pending(claim, "57.4.0");
            } else {
                check(claim, "the ojalgo-linear-algebra skill (\"The simple way\" and rule 2)", () -> RuleChecks.singularGivesPseudoinverse(size));
            }
        }

        String finance = "the ojalgo-portfolio skill";
        check("The old package org.ojalgo.finance.portfolio does not exist", finance + " (\"Names that no longer exist\")",
                () -> !RuleChecks.exists("org.ojalgo.finance.portfolio.MarkowitzModel"));
        check("MarkowitzModel is long-only by default, and its weights sum to 1", finance + " (Markowitz section)", () -> {
            MarkowitzModel markowitz = MarkowitzModel.of(RawStore.wrap(new double[][] { { 0.04, 0.006 }, { 0.006, 0.01 } }), MatrixR064.FACTORY.column(0.06, -0.02));
            markowitz.setRiskAversion(3.0);
            double sum = 0.0;
            boolean nonNegative = true;
            for (java.math.BigDecimal weight : markowitz.getWeights()) {
                sum += weight.doubleValue();
                nonNegative &= weight.signum() >= 0;
            }
            return !markowitz.isShortingAllowed() && nonNegative && Math.abs(sum - 1.0) < 1e-5 && markowitz.optimiser().getState().isOptimal(); // the weights are rounded to 6 decimals
        });

        check("LU on a singular matrix: decompose(..) returns true and isSolvable() false", "the ojalgo-linear-algebra skill (the decomposition pattern, rule 2)", () -> {
            MatrixStore<Double> singular = RawStore.wrap(new double[][] { { 1, 2 }, { 2, 4 } });
            LU<Double> lu = LU.R064.make(singular);
            return lu.decompose(singular) && !lu.isSolvable();
        });

        RuleChecks.currentNames();

        if (changed > 0) {
            System.out.println(changed + " behaviour(s) changed. Update the texts named above, then update the checks in tests/RuleChecks.java.");
            System.exit(1);
        }
        System.out.println("ojAlgo behaves as the rules say.");
    }

    /**
     * The current names the texts tell people to use. Nothing to assert: it is enough that this compiles.
     */
    static void currentNames() throws Exception {

        ExpressionsBasedModel model = new ExpressionsBasedModel();
        Variable x = model.newVariable("x").lower(0).upper(10).weight(1);
        Variable y = model.newVariable("y").binary();
        Variable z = model.newVariable("z").integer();
        Expression expression = model.newExpression("e").lower(0).upper(5).set(x, 1).set(y, 2);
        model.newExpression("f").level(0).set(z, 1);
        model.newExpression("q").weight(1).set(x, x, 2);

        model.options.time_abort = 30_000L;
        model.options.integer(IntegerStrategy.DEFAULT.withGapTolerance(NumberContext.of(3)));
        model.options.progress(IntegerSolver.class);
        model.options.progress(null);

        model.copy(true).minimise();
        Optimisation.Result result = model.minimise();
        boolean usable = result.getState().isOptimal() || result.getState().isFeasible();
        double value = usable ? result.getValue() + x.getValue().doubleValue() + result.doubleValue(model.indexOf(x)) : 0;

        File file = File.createTempFile("model", ".mps");
        model.writeTo(file.toPath());
        ExpressionsBasedModel.parse(file);
        file.delete();

        SingularValue<Double> svd = SingularValue.R064.make(2, 2);
        Eigenvalue<Double> evd = Eigenvalue.R064.make(2, true);
        MatrixStore<Double> square = RawStore.wrap(new double[][] { { 2, 1 }, { 1, 2 } });
        svd.decompose(square.limits(-1, 2));
        evd.decompose(square);
        if (svd.getU() == null || svd.getS() == null || svd.getV() == null || evd.getD() == null || evd.getV() == null || svd.getRank() < 0) {
            throw new IllegalStateException();
        }
        org.ojalgo.matrix.decomposition.LU<Double> sparseLU = LU.newSparseR064();
        org.ojalgo.matrix.store.SparseStore<Double> sparse = org.ojalgo.matrix.store.SparseStore.R064.make(2, 2);
        new org.ojalgo.matrix.task.iterative.ConjugateGradientSolver();
        org.ojalgo.matrix.store.RawStore.wrap(new double[][] { { 1 } });
        if (sparseLU == null || sparse == null) {
            throw new IllegalStateException();
        }

        Class<?>[] names = { org.ojalgo.matrix.MatrixR064.class, org.ojalgo.matrix.store.R064Store.class, org.ojalgo.array.ArrayR064.class,
                org.ojalgo.function.constant.PrimitiveMath.class, org.ojalgo.structure.Access1D.class, org.ojalgo.data.domain.finance.FinanceUtils.class };

        if (expression == null || names.length == 0 || Double.isNaN(value)) {
            throw new IllegalStateException();
        }
    }

    /**
     * A singular, rank-deficient square matrix: the last row repeats the first.
     */
    static boolean singularGivesPseudoinverse(final int size) {
        double[][] elements = new double[size][size];
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                elements[i][j] = (i + 1) * (j + 1) + (i == j ? 1 : 0);
            }
        }
        elements[size - 1] = elements[0].clone();
        MatrixR064 matrix = MatrixR064.FACTORY.copy(RawStore.wrap(elements));
        double[] ones = new double[size];
        java.util.Arrays.fill(ones, 1.0);
        MatrixR064 rhs = matrix.multiply(MatrixR064.FACTORY.column(ones));

        SingularValue<Double> svd = SingularValue.R064.make(matrix);
        svd.decompose(matrix);
        MatrixR064 pseudoinverse = MatrixR064.FACTORY.copy(svd.getInverse());
        MatrixR064 minimumNorm = pseudoinverse.multiply(rhs);

        MatrixR064 solution = matrix.solve(rhs);
        MatrixR064 inverse = matrix.invert();

        double scale = 1.0 + pseudoinverse.norm();
        return matrix.getRank() == size - 1 && solution.subtract(minimumNorm).norm() < 1e-8 * (1.0 + minimumNorm.norm())
                && inverse.subtract(pseudoinverse).norm() < 1e-8 * scale;
    }

    private static void check(final String claim, final String where, final Callable<Boolean> test) {
        boolean holds;
        try {
            holds = test.call();
        } catch (Exception cause) {
            holds = false;
            System.out.println("          " + cause);
        }
        if (holds) {
            System.out.println("ok        " + claim);
        } else {
            changed++;
            System.out.println("CHANGED   " + claim);
            System.out.println("          Update: " + where);
        }
    }

    private static boolean exists(final String className) {
        try {
            Class.forName(className);
            return true;
        } catch (ClassNotFoundException | LinkageError cause) {
            return false;
        }
    }

    private static boolean hasMethod(final Class<?> type, final String name) {
        for (java.lang.reflect.Method method : type.getMethods()) {
            if (method.getName().equals(name) && Modifier.isPublic(method.getModifiers())) {
                return true;
            }
        }
        return false;
    }

    /**
     * Is the ojAlgo version on the classpath at least major.minor? An unknown version (no manifest) counts as
     * the latest.
     */
    private static boolean isAtLeast(final int major, final int minor) {
        String[] parts = org.ojalgo.OjAlgoUtils.getVersion().split("[.-]");
        try {
            int actualMajor = Integer.parseInt(parts[0]);
            int actualMinor = Integer.parseInt(parts[1]);
            return actualMajor > major || actualMajor == major && actualMinor >= minor;
        } catch (RuntimeException cause) {
            return true;
        }
    }

    /**
     * A claim the texts already make about a release that is not out yet. Not checked, and not counted as
     * changed, until that release is the latest.
     */
    private static void pending(final String claim, final String release) {
        System.out.println("pending   " + claim + " (ojAlgo " + release + ", running " + org.ojalgo.OjAlgoUtils.getVersion() + ")");
    }

}
