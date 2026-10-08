#!/usr/bin/env bash
#
# Runs the code in the skills: the three Optimisation Service skills against a live
# server, and the linear algebra skill locally.
#
#   ./tests/run.sh                 the public test server
#   HOST=https://... ./tests/run.sh   any other instance
#
# The code is extracted from the SKILL.md files each time, so what runs here is
# what is published. Needs curl, jq, python3 and Maven.
#
# It also runs RuleChecks.java, which checks that the latest ojAlgo release still
# behaves the way the rules in the skill, the cookbook and ojAlgo/context7.json
# say. If a release changes one of those behaviours, that step fails and names
# the texts to update.
#
# Expected: the chairs-and-tables model maximises to 2200 (24 chairs, 14 tables).
# The curl and file examples minimise the same model, so they report 0.

set -uo pipefail

cd "$(dirname "$0")"

HOST="${HOST:-https://optimisation-test-service-840974723912.europe-north2.run.app}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

python3 extract.py "${WORK}" "${HOST}" || exit 1
cp model.lp model.mps pom.xml "${WORK}/"
cp RuleChecks.java "${WORK}/src/main/java/"
cd "${WORK}"

echo "==> Server: ${HOST}"
curl -s -m 60 "${HOST}/optimisation/v1/environment"; echo; echo

echo "==> 1/4 REST skill, curl example (MPS, MIN - expect OPTIMAL 0)"
bash rest.sh; echo; echo

echo "==> 2/4 REST skill, Python example (LP, MAX - expect 2200.0 [24.0, 14.0])"
python3 -m venv venv >/dev/null && ./venv/bin/pip install -q requests && ./venv/bin/python rest.py; echo

echo "==> Compiling the Java examples"
mvn -q -B compile dependency:build-classpath -Dmdep.outputFile=cp.txt || { echo "COMPILE FAILED"; exit 1; }
CP="target/classes:$(cat cp.txt)"; echo

echo "==> Rules (does the latest ojAlgo release still behave as the rules say? needs no server)"
java -cp "${CP}" RuleChecks || RULES_CHANGED=1
echo

echo "==> Linear algebra skill (expect x=0.222.. det=18 rank=3, least squares 3.5,1.4, svd rank 2, eigenvalues 4.73,3,1.27 in some order, small residuals)"
java -cp "${CP}" LinearAlgebraSkill; echo

echo "==> Portfolio skill (expect markowitz ~{0.41, 0.25, 0.34}, implied 0.0678,0.0213,0.01095, black-litterman ~{0.515, 0.385, 0.1}, constrained equity at most 0.5)"
java -cp "${CP}" PortfolioSkill; echo

echo "==> 3/4 Client skill (expect model: value 2200, chairs 24, tables 14, rush 0; file: value 0, it is minimised)"
java -cp "${CP}" ClientSkill; echo

echo "==> 4/4 ojAlgo skill (expect OPTIMAL 2200, chairs=24 tables=14, variable.getValue()=null)"
java -cp "${CP}" OjAlgoSkill; echo

echo "==> Modeller comparison (expect value 2200, chairs 24, tables 14, from both)"
java -cp "${CP}" CompareOptModel
java -cp "${CP}" CompareExpressionsBasedModel

if [ "${RULES_CHANGED:-0}" = 1 ]; then
  echo
  echo "==> The Rules step reported CHANGED behaviour (see above). The other steps ran anyway."
  exit 1
fi
