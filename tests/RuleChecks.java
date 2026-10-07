import java.io.File;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Callable;

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
 * The rules about writing ojAlgo code are stated in three places that have to be edited by hand: the "rules"
 * list in ojAlgo/context7.json (the source; ojalgo.org generates its copies from it), the "Rules that apply to
 * every model" section of the Optimisation Cookbook (www_ojalgo_org/content/optimisation-cookbook.md) and the
 * ojalgo-optimisation skill in this repository. Each check below pins down one behaviour those texts describe.
 * This runs against the latest ojAlgo release, so when a release changes a behaviour the check fails and says
 * which texts to update. After updating them, change the check to expect the new behaviour.
 * <p>
 * The current names used in the texts are simply used here, in {@link #currentNames()}: if one of them is
 * renamed this file stops compiling, which is the same signal.
 */
public class RuleChecks {

    private static final String EVERYWHERE = "ojAlgo/context7.json, the cookbook's rules, the ojalgo-optimisation skill";

    private static int changed = 0;

    public static void main(final String[] args) throws Exception {

        check("A second expression with a name already in use replaces the first", EVERYWHERE + " (the rule about unique expression names)", () -> {
            ExpressionsBasedModel model = new ExpressionsBasedModel();
            Variable x = model.newVariable("x").lower(0).upper(1000).weight(1);
            model.newExpression("limit").upper(10).set(x, 1);
            try {
                model.newExpression("limit").upper(100).set(x, 1);
            } catch (IllegalArgumentException cause) {
                return false; // Refused: the texts must now say that it throws.
            }
            return Math.round(model.maximise().getValue()) == 100L; // Only the second constraint is left.
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

        Class<?>[] names = { org.ojalgo.matrix.MatrixR064.class, org.ojalgo.matrix.store.R064Store.class, org.ojalgo.array.ArrayR064.class,
                org.ojalgo.function.constant.PrimitiveMath.class, org.ojalgo.structure.Access1D.class, org.ojalgo.data.domain.finance.FinanceUtils.class };

        if (expression == null || names.length == 0 || Double.isNaN(value)) {
            throw new IllegalStateException();
        }
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

}
