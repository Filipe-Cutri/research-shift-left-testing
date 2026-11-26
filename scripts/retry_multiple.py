import csv
import os
import re
import shutil
import subprocess
from pathlib import Path

root = Path.home() / "defects4j-validation"
csv_path = Path("data/raw/defects4j/eligibility.csv")
logs = Path("data/raw/defects4j/logs")
root.mkdir(parents=True, exist_ok=True)

with csv_path.open(newline="") as f:
    rows = list(csv.DictReader(f))
    fields = list(rows[0])

def save():
    tmp = csv_path.with_suffix(".tmp")
    with tmp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, csv_path)

def run(cmd, cwd, log):
    with log.open("w") as f:
        return subprocess.run(
            cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT
        ).returncode

for r in rows:
    if r["reason"] != "MULTIPLE_TRIGGER_TESTS":
        continue

    p, b = r["project"], r["bug_id"]
    print(f"Validando {p}-{b}", flush=True)
    work = {v: root / f"{p}-{b}{v}" for v in ("b", "f")}
    reason = ""
    detected = False
    fixed_ok = True

    try:
        for v in ("b", "f"):
            shutil.rmtree(work[v], ignore_errors=True)
            if run(
                ["defects4j", "checkout", "-p", p, "-v", f"{b}{v}",
                 "-w", str(work[v])],
                Path.cwd(), logs / f"{p}-{b}-{v}-checkout.log"
            ):
                reason = f"CHECKOUT_{v}_FAILED"
                break

            if run(
                ["defects4j", "compile"], work[v],
                logs / f"{p}-{b}-{v}-compile.log"
            ):
                reason = f"COMPILE_{v}_FAILED"
                break

        if not reason:
            result = subprocess.run(
                ["defects4j", "export", "-p", "tests.trigger"],
                cwd=work["b"], capture_output=True, text=True
            )
            tests = [
                t for t in re.split(r"[\s,]+", result.stdout.strip()) if t
            ]
            if result.returncode or not tests:
                reason = "TRIGGER_EXPORT_FAILED"

        if not reason:
            for i, test in enumerate(tests, 1):
                for v in ("b", "f"):
                    log = logs / f"{p}-{b}-{v}-trigger-{i}.log"
                    code = run(
                        ["defects4j", "test", "-t", test], work[v], log
                    )
                    content = log.read_text(errors="replace")
                    counts = re.findall(
                        r"^Failing tests:\s*(\d+)", content, re.MULTILINE
                    )
                    if code or not counts:
                        reason = f"TEST_{v}_UNREADABLE"
                        break
                    count = int(counts[-1])
                    if v == "b" and count > 0 and test in content:
                        detected = True
                    if v == "f" and count != 0:
                        fixed_ok = False
                if reason:
                    break

        if not reason and detected and fixed_ok:
            r["eligibility"] = "ELIGIBLE"
            r["reason"] = "REFERENCE_TEST_CONFIRMED"
            r["buggy_trigger_failed"] = "YES"
            r["fixed_failing_tests"] = "0"
            r["trigger_test"] = ";".join(tests)
        else:
            r["eligibility"] = "INVESTIGATE"
            r["reason"] = reason or "EXPECTED_BEHAVIOR_NOT_CONFIRMED"

        save()
        print(f"{p}-{b}: {r['eligibility']} ({r['reason']})", flush=True)
    finally:
        for directory in work.values():
            shutil.rmtree(directory, ignore_errors=True)
