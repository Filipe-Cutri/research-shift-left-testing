#!/usr/bin/env bash
set -u

PROJECT="${1:?Uso: $0 PROJECT BUG_ID}"
BUG_ID="${2:?Uso: $0 PROJECT BUG_ID}"

ROOT="$HOME/projects/research-shift-left-testing"
WORK_ROOT="$HOME/defects4j-validation"
trap 'rm -rf -- "$WORK_ROOT/${PROJECT}-${BUG_ID}b" "$WORK_ROOT/${PROJECT}-${BUG_ID}f"' EXIT
LOG_ROOT="$ROOT/data/raw/defects4j/logs"
RESULTS="$ROOT/data/raw/defects4j/eligibility.csv"

mkdir -p "$WORK_ROOT" "$LOG_ROOT"

if [[ ! -f "$RESULTS" ]]; then
    echo "project,bug_id,trigger_test,buggy_trigger_failed,fixed_failing_tests,eligibility,reason" > "$RESULTS"
fi

if grep -q "^\"$PROJECT\",\"$BUG_ID\"," "$RESULTS"; then
    echo "Defeito já registrado. Ignorando: $PROJECT-$BUG_ID"
    exit 0
fi

record_result() {
    local trigger="$1"
    local buggy="$2"
    local fixed="$3"
    local status="$4"
    local reason="$5"

    printf '"%s","%s","%s","%s","%s","%s","%s"\n' \
        "$PROJECT" "$BUG_ID" "$trigger" "$buggy" "$fixed" "$status" "$reason" \
        >> "$RESULTS"
}

investigate() {
    local reason="$1"
    echo "Resultado: INVESTIGATE ($reason)"
    record_result "${trigger:-UNKNOWN}" "${buggy_trigger_failed:-UNKNOWN}" \
        "${fixed_failures:-UNKNOWN}" "INVESTIGATE" "$reason"
    exit 0
}

for version in b f; do
    workspace="$WORK_ROOT/${PROJECT}-${BUG_ID}${version}"
    rm -rf "$workspace"

    echo "Checkout ${PROJECT}-${BUG_ID}${version}"

    if ! defects4j checkout \
        -p "$PROJECT" \
        -v "${BUG_ID}${version}" \
        -w "$workspace" \
        > "$LOG_ROOT/${PROJECT}-${BUG_ID}-${version}-checkout.log" 2>&1; then
        investigate "CHECKOUT_${version}_FAILED"
    fi
done

BUGGY="$WORK_ROOT/${PROJECT}-${BUG_ID}b"
FIXED="$WORK_ROOT/${PROJECT}-${BUG_ID}f"

trigger=$(cd "$BUGGY" && defects4j export -p tests.trigger 2>/dev/null) || investigate "TRIGGER_EXPORT_FAILED"

if [[ -z "$trigger" ]]; then
    investigate "NO_TRIGGER_TEST"
fi

if [[ "$(printf '%s\n' "$trigger" | sed '/^[[:space:]]*$/d' | wc -l)" -ne 1 ]]; then
    investigate "MULTIPLE_TRIGGER_TESTS"
fi

echo "Teste de referência: $trigger"

for version in b f; do
    workspace="$WORK_ROOT/${PROJECT}-${BUG_ID}${version}"

    echo "Compilando versão $version..."

    if ! (cd "$workspace" && defects4j compile) \
        > "$LOG_ROOT/${PROJECT}-${BUG_ID}-${version}-compile.log" 2>&1; then
        investigate "COMPILE_${version}_FAILED"
    fi

    echo "Compilação $version: PASS"
done

BUGGY_LOG="$LOG_ROOT/${PROJECT}-${BUG_ID}-b-test.log"
FIXED_LOG="$LOG_ROOT/${PROJECT}-${BUG_ID}-f-test.log"

echo "Executando teste de referência na versão defeituosa..."

if ! (cd "$BUGGY" && defects4j test -t "$trigger") > "$BUGGY_LOG" 2>&1; then
    investigate "BUGGY_TEST_EXECUTION_FAILED"
fi

echo "Executando teste de referência na versão corrigida..."

if ! (cd "$FIXED" && defects4j test -t "$trigger") > "$FIXED_LOG" 2>&1; then
    investigate "FIXED_TEST_EXECUTION_FAILED"
fi

buggy_count=$(sed -n 's/^Failing tests: *//p' "$BUGGY_LOG" | tail -1)
fixed_count=$(sed -n 's/^Failing tests: *//p' "$FIXED_LOG" | tail -1)

if ! [[ "$buggy_count" =~ ^[0-9]+$ && "$fixed_count" =~ ^[0-9]+$ ]]; then
    investigate "TEST_RESULT_UNREADABLE"
fi

buggy_trigger_failed="NO"
if grep -Fq -- "$trigger" "$BUGGY_LOG" && [[ "$buggy_count" -gt 0 ]]; then
    buggy_trigger_failed="YES"
fi

fixed_failures="$fixed_count"

if [[ "$buggy_trigger_failed" == "YES" && "$fixed_failures" -eq 0 ]]; then
    eligibility="ELIGIBLE"
    reason="REFERENCE_TEST_CONFIRMED"
else
    eligibility="INVESTIGATE"
    reason="EXPECTED_BEHAVIOR_NOT_CONFIRMED"
fi

record_result "$trigger" "$buggy_trigger_failed" "$fixed_failures" "$eligibility" "$reason"

echo
echo "========== RESULTADO =========="
echo "Projeto: $PROJECT"
echo "Defeito: $BUG_ID"
echo "Teste falha na buggy: $buggy_trigger_failed"
echo "Falhas na fixed: $fixed_failures"
echo "Elegibilidade: $eligibility"
echo "Motivo: $reason"
echo "CSV: $RESULTS"
