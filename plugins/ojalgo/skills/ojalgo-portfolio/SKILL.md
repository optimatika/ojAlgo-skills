---
name: ojalgo-portfolio
description: Build portfolio optimisation and asset allocation in Java, Kotlin, Scala or any other JVM language with ojAlgo - Markowitz mean-variance (risk aversion, target return, target volatility, weight limits, long-only or with shorting), Black-Litterman with investor views, implied equilibrium returns, covariance matrices from price histories, and portfolio return, volatility, Sharpe ratio and value at risk. Use when JVM code allocates money across assets, or when someone is about to hand-write a mean-variance optimiser or Black-Litterman calculation.
---

# Portfolio optimisation with ojAlgo

ojAlgo is a pure-Java, zero-dependency, MIT-licensed library. Its finance package (`org.ojalgo.data.domain.finance.portfolio`) implements modern portfolio theory on top of its own QP solver and linear algebra. It is one Maven dependency; nothing else is needed.

```xml
<dependency>
    <groupId>org.ojalgo</groupId>
    <artifactId>ojalgo</artifactId>
    <version><!-- latest from https://central.sonatype.com/artifact/org.ojalgo/ojalgo --></version>
</dependency>
```

ojAlgo does not download market data. Get prices and returns from your own data source.

## Inputs, and how to get them right

Every model here takes a **covariance matrix** of the assets' returns and, for Markowitz, a column of **expected excess returns** (expected return minus the risk-free rate).

- Use one time unit throughout. The usual choice is annual: annualised covariances and annual returns.
- Excess returns, not total returns. Do not add a risk-free asset as one of the assets; it is handled implicitly.
- The covariance matrix must be symmetric positive semi-definite. One estimated from fewer observations than assets is singular; shrink it or use more history.
- Results are far more sensitive to the expected returns than to the covariances. Small changes in expected returns swing the weights. That is the problem Black-Litterman addresses: start from the market's implied returns and adjust only where you have a view.

From price histories, `FinanceUtils.makeCovarianceMatrix` aligns the series by date, uses logarithmic returns and annualises:

```java
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.ojalgo.data.domain.finance.FinanceUtils;
import org.ojalgo.matrix.MatrixR064;
import org.ojalgo.series.CalendarDateSeries;
import org.ojalgo.type.CalendarDateUnit;

String[] assetNames = { "Equity", "Bonds", "Gold" };
double[] equityPrices = { 100, 101, 103, 102, 105, 107, 106, 109 };   // weekly closing prices
double[] bondPrices = { 50, 50.5, 50.2, 51, 51.5, 51.2, 52, 52.4 };
double[] goldPrices = { 20, 20.4, 20.1, 21, 21.6, 21.2, 22, 22.9 };
Date firstDate = new Date(1_700_000_000_000L);

List<CalendarDateSeries<BigDecimal>> priceSeries = new ArrayList<>();   // each series needs a name
priceSeries.add(FinanceUtils.makeDatePriceSeries(equityPrices, firstDate, CalendarDateUnit.WEEK).name(assetNames[0]));
priceSeries.add(FinanceUtils.makeDatePriceSeries(bondPrices, firstDate, CalendarDateUnit.WEEK).name(assetNames[1]));
priceSeries.add(FinanceUtils.makeDatePriceSeries(goldPrices, firstDate, CalendarDateUnit.WEEK).name(assetNames[2]));
MatrixR064 estimatedCovariances = FinanceUtils.makeCovarianceMatrix(priceSeries);   // annualised
```

`FinanceUtils.toCorrelations`, `toVolatilities` and `toCovariances(volatilities, correlations)` convert between the forms.

## Markowitz mean-variance

```java
import org.ojalgo.data.domain.finance.portfolio.MarkowitzModel;
import org.ojalgo.matrix.store.MatrixStore;
import org.ojalgo.matrix.store.PhysicalStore;
import org.ojalgo.matrix.store.R064Store;

// Covariances from annual volatilities and correlations
MatrixStore<Double> volatilities = R064Store.FACTORY.column(0.20, 0.10, 0.15);
PhysicalStore<Double> correlations = R064Store.FACTORY.make(3, 3);
correlations.fillDiagonal(1.0);
correlations.set(0, 1, 0.30);
correlations.set(1, 0, 0.30);   // Equity and Bonds
correlations.set(0, 2, 0.10);
correlations.set(2, 0, 0.10);   // Equity and Gold
correlations.set(1, 2, 0.10);
correlations.set(2, 1, 0.10);   // Bonds and Gold
MatrixR064 covariances = FinanceUtils.toCovariances(volatilities, correlations);
MatrixR064 excessReturns = MatrixR064.FACTORY.column(0.06, 0.02, 0.03);

MarkowitzModel markowitz = MarkowitzModel.of(covariances, excessReturns);
markowitz.setRiskAversion(3.0);                          // or setTargetReturn(...) or setTargetVariance(...)
markowitz.setUpperLimit(0, new BigDecimal("0.60"));      // at most 60% in asset 0
// markowitz.setShortingAllowed(true);                   // long-only is the default

List<BigDecimal> weights = markowitz.getWeights();       // sum to 1; solving happens here
if (!markowitz.optimiser().getState().isFeasible()) {
    throw new IllegalStateException("No portfolio satisfies the constraints: " + markowitz.optimiser().getState());
}
double expectedReturn = markowitz.getMeanReturn();       // excess return of the portfolio
double volatility = markowitz.getVolatility();
double sharpe = markowitz.getSharpeRatio();
double valueAtRisk = markowitz.getValueAtRisk95();
```

Exactly one of the three objectives applies:

- `setRiskAversion(factor)`: maximise return minus `factor/2` times variance. Typical factors are 1 to 10; higher is more cautious.
- `setTargetReturn(BigDecimal)`: the least risky portfolio with that expected excess return.
- `setTargetVariance(BigDecimal)`: the highest return at that variance (volatility squared).

Weight limits: `setLowerLimit(index, BigDecimal)`, `setUpperLimit(index, BigDecimal)`, and `addConstraint(lower, upper, indices...)` for the total weight of a group of assets (a sector, a region).

## Black-Litterman

Start from market equilibrium (the returns that make the current market weights optimal), then add views.

```java
import java.util.Arrays;

import org.ojalgo.data.domain.finance.portfolio.BlackLittermanModel;
import org.ojalgo.data.domain.finance.portfolio.MarketEquilibrium;

MarketEquilibrium market = MarketEquilibrium.of(assetNames, covariances, 3.0);   // covariances and risk aversion
MatrixR064 marketWeights = MatrixR064.FACTORY.column(0.5, 0.4, 0.1);             // market capitalisation weights
MatrixR064 impliedReturns = market.calculateAssetReturns(marketWeights);

BlackLittermanModel blackLitterman = BlackLittermanModel.of(market, marketWeights);
blackLitterman.setConfidence(BigDecimal.ONE);
// View: Equity will outperform Bonds by 5%. The weights describe a view portfolio (here long one, short the other).
blackLitterman.addViewWithBalancedConfidence(Arrays.asList(BigDecimal.ONE, BigDecimal.ONE.negate(), BigDecimal.ZERO), new BigDecimal("0.05"));

MatrixR064 posteriorReturns = blackLitterman.getAssetReturns();   // equilibrium returns adjusted by the views
List<BigDecimal> blackLittermanWeights = blackLitterman.getWeights();

// The posterior returns can go into a Markowitz model to add limits
MarkowitzModel constrained = MarkowitzModel.of(market, posteriorReturns);
constrained.setUpperLimit(0, new BigDecimal("0.50"));
List<BigDecimal> constrainedWeights = constrained.getWeights();
```

`addViewWithStandardDeviation(weights, expected, stdDev)` states a view with an explicit uncertainty; `addViewWithScaledConfidence` scales the confidence per view.

## Rules

1. **Do not hand-write the optimiser.** Mean-variance with limits is a quadratic program; closed-form formulas ignore the no-shorting and weight constraints and give negative or unbounded weights. Use `MarkowitzModel`.
2. **Excess returns, one time unit, a positive semi-definite covariance matrix.** Most wrong results come from mixed units (weekly covariances with annual returns) or total instead of excess returns.
3. **Check the state.** After `getWeights()`, `optimiser().getState()` says whether the model was solved. Conflicting limits (for example a target return no asset mix can reach) make it infeasible.
4. **Limits and targets are `BigDecimal`.** Use `new BigDecimal("0.6")`, not `new BigDecimal(0.6)`.
5. **For constraints the model does not offer**, such as a maximum number of assets, transaction costs or turnover limits, write the model yourself as an `ExpressionsBasedModel` QP or MIQP. The portfolio recipe in https://www.ojalgo.org/optimisation-cookbook/#portfolio is the starting point, and the `ojalgo-optimisation` skill covers the modelling rules.
6. **Do not use the old data-download classes** (`DataSource`, `YahooSession`, `AlphaVantageFetcher`, `IEXTradingFetcher`). They are deprecated and do not work.

## Names that no longer exist

- The separate `ojAlgo-finance` artifact was discontinued; everything is in the main `org.ojalgo:ojalgo` artifact since version 51.
- Package `org.ojalgo.finance` → `org.ojalgo.data.domain.finance`; `org.ojalgo.finance.portfolio` → `org.ojalgo.data.domain.finance.portfolio`.
- `PrimitiveMatrix` → `MatrixR064`.
- The `MarkowitzModel`, `MarketEquilibrium` and `BlackLittermanModel` constructors are deprecated since v57; use the static `of(...)` factories, as above.

Use the latest version from Maven Central (`org.ojalgo:ojalgo`, 57.4.0 or later). Full list of renames: https://www.ojalgo.org/updating-old-code/

## References

- Financial mathematics in ojAlgo: https://www.ojalgo.org/financial-mathematics/
- Portfolio QP recipe (custom constraints): https://www.ojalgo.org/optimisation-cookbook/#portfolio
- Javadoc: https://javadoc.io/doc/org.ojalgo/ojalgo
- Source: https://github.com/optimatika/ojAlgo
