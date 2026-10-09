#!/usr/bin/env python3
"""Turns the code blocks in the skills into runnable files, so that what is tested is what is published."""
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent.parent
skills = root / "plugins" / "ojalgo" / "skills"
out = pathlib.Path(sys.argv[1])
host = sys.argv[2]


def blocks(skill, language):
    text = (skills / skill / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"```" + language + r"\n(.*?)```", text, re.S)


def java_class(name, snippets, tail):
    imports, body = [], []
    for snippet in snippets:
        for line in snippet.splitlines():
            (imports if line.startswith("import ") else body).append(line)
    imports = sorted(set(imports))
    lines = imports + ["", "public class " + name + " {", "    public static void main(String[] args) throws Exception {"]
    lines += ["        " + line for line in body + tail]
    lines += ["    }", "}", ""]
    target = out / "src" / "main" / "java" / (name + ".java")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).replace("https://your-service-host", host), encoding="utf-8")


(out / "rest.sh").write_text(blocks("optimisation-service-rest", "bash")[0].replace("https://your-service-host", host), encoding="utf-8")
(out / "rest.py").write_text(blocks("optimisation-service-rest", "python")[0].replace("https://your-service-host", host), encoding="utf-8")

java_class("ClientSkill", blocks("optimisation-service-client", "java"), [
    'System.out.println("model: optimal=" + result.isOptimal() + " value=" + result.getValue() + " chairs=" + chairs.doubleValue() + " tables=" + tables.doubleValue() + " rush=" + rush.doubleValue());',
    'System.out.println("file:  optimal=" + fileResult.isOptimal() + " value=" + fileResult.getValue() + " solution=" + fileResult.getSolution());',
    "System.out.println(client.getServiceEnvironment());",
])

reference = (skills / "optimisation-service-client" / "references" / "modellers.md").read_text(encoding="utf-8")
copy = (skills / "optimisation-service-ojalgo" / "references" / "modellers.md").read_text(encoding="utf-8")
if reference != copy:
    sys.exit("references/modellers.md differs between the client skill and the ojAlgo skill - they must be identical")
comparison = re.findall(r"```java\n(.*?)```", reference, re.S)

java_class("CompareOptModel", [comparison[0]], [
    'System.out.println("OptModel:              optimal=" + result.isOptimal() + " value=" + result.getValue() + " chairs=" + chairs.doubleValue() + " tables=" + tables.doubleValue());',
])

java_class("CompareExpressionsBasedModel", [comparison[1]], [
    'System.out.println("ExpressionsBasedModel: " + result + " chairs=" + chairs.getValue() + " tables=" + tables.getValue());',
])

java_class("LinearAlgebraSkill", blocks("ojalgo-linear-algebra", "java"), [
    'System.out.println("x=" + solution.doubleValue(0) + " det=" + determinant + " residual=" + residual);',
    'System.out.println("lu=" + solution.doubleValue(0) + " least squares=" + fitted.doubleValue(0) + "," + fitted.doubleValue(1) + " svd rank=" + numericalRank + " eigenvalues=" + eigenvalues.doubleValue(0, 0) + "," + eigenvalues.doubleValue(1, 1) + "," + eigenvalues.doubleValue(2, 2));',
    'System.out.println("cg residual=" + sparse.multiply(iterative).subtract(sparseRhs).norm() + " loop D[0,0]=" + matD.doubleValue(0, 0) + " qr rank=" + decompositionInLoop.getRank());',
])

java_class("PortfolioSkill", blocks("ojalgo-portfolio", "java"), [
    'System.out.println("covariance from prices: " + estimatedCovariances.countRows() + "x" + estimatedCovariances.countColumns() + ", first variance " + estimatedCovariances.doubleValue(0, 0));',
    'System.out.println("markowitz " + weights + " return=" + expectedReturn + " volatility=" + volatility + " sharpe=" + sharpe + " VaR95=" + valueAtRisk);',
    'System.out.println("implied " + impliedReturns.doubleValue(0) + "," + impliedReturns.doubleValue(1) + "," + impliedReturns.doubleValue(2) + " posterior " + posteriorReturns.doubleValue(0) + "," + posteriorReturns.doubleValue(1) + "," + posteriorReturns.doubleValue(2));',
    'System.out.println("black-litterman " + blackLittermanWeights + " constrained " + constrainedWeights + " " + constrained.optimiser().getState());',
])

java_class("OjAlgoSkill", blocks("optimisation-service-ojalgo", "java"), [
    'System.out.println("result: " + result);',
    'System.out.println("chairs=" + result.doubleValue(model.indexOf(chairs)) + " tables=" + result.doubleValue(model.indexOf(tables)) + " variable.getValue()=" + chairs.getValue());',
])
