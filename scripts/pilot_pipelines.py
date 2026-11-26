import csv
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data/processed/sample_30.csv"
OUT = ROOT / "data/raw/pilot"
WORK = Path.home() / "defects4j-pilot"

PMD = ROOT / "tools/pmd-bin-7.19.0/bin/pmd"
SPOTBUGS = ROOT / "tools/spotbugs-4.10.5/bin/spotbugs"

OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

with SAMPLE.open(newline="") as f:
    defect = next(csv.DictReader(f))

project = defect["project"]
bug = defect["bug_id"]
results = []

def run(cmd, log):
    start = time.monotonic()
    p = subprocess.run(
        cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True
    )
    log.write_text(p.stdout)
    return p.returncode, time.monotonic() - start, p.stdout

def export(ws, prop):
    p = subprocess.run(
        ["defects4j", "export", "-w", str(ws), "-p", prop],
        capture_output=True, text=True, check=True
    )
    return p.stdout.strip()

for version in ["b", "f"]:
    # Alterna a ordem entre as duas versões no piloto.
    scenarios = (
        ["baseline", "shiftleft"] if version == "b"
        else ["shiftleft", "baseline"]
    )

    for scenario in scenarios:
        ws = WORK / f"{project}-{bug}-{version}-{scenario}"
        prefix = OUT / f"{project}-{bug}{version}-{scenario}"
        shutil.rmtree(ws, ignore_errors=True)

        row = {
            "project": project,
            "bug_id": bug,
            "version": version,
            "scenario": scenario,
            "status": "ERROR",
            "pmd_s": 0,
            "compile_s": 0,
            "spotbugs_s": 0,
            "test_s": 0,
            "total_s": 0,
        }

        print(f"Executando {project}-{bug}{version} | {scenario}",
              flush=True)

        try:
            rc, _, _ = run(
                ["defects4j", "checkout", "-p", project,
                 "-v", f"{bug}{version}", "-w", str(ws)],
                Path(str(prefix) + "-checkout.log")
            )
            if rc != 0:
                raise RuntimeError("Checkout falhou")

            # Checkout e preparação ficam fora do tempo do pipeline.
            start = time.monotonic()

            if scenario == "shiftleft":
                src = ws / export(ws, "dir.src.classes")
                rc, t, _ = run(
                    [str(PMD), "check", "-d", str(src),
                     "-R", "rulesets/java/quickstart.xml",
                     "-f", "xml",
                     "-r", str(prefix) + "-pmd.xml"],
                    Path(str(prefix) + "-pmd.log")
                )
                row["pmd_s"] = round(t, 3)
                if rc not in (0, 4):
                    raise RuntimeError("PMD falhou")

            rc, t, _ = run(
                ["defects4j", "compile", "-w", str(ws)],
                Path(str(prefix) + "-compile.log")
            )
            row["compile_s"] = round(t, 3)
            if rc != 0:
                raise RuntimeError("Compilação falhou")

            if scenario == "shiftleft":
                classes = ws / export(ws, "dir.bin.classes")
                rc, t, _ = run(
                    [str(SPOTBUGS), "-textui", "-effort:max",
                     "-low", "-xml:withMessages",
                     "-output", str(prefix) + "-spotbugs.xml",
                     str(classes)],
                    Path(str(prefix) + "-spotbugs.log")
                )
                row["spotbugs_s"] = round(t, 3)
                if rc not in (0, 1):
                    raise RuntimeError("SpotBugs falhou")

            triggers = re.split(r"[\s,;]+", defect["trigger_test"].strip())
            failures = 0
            test_time = 0

            for i, trigger in enumerate(filter(None, triggers)):
                rc, t, output = run(
                    ["defects4j", "test", "-w", str(ws), "-t", trigger],
                    Path(str(prefix) + f"-test-{i}.log")
                )
                test_time += t
                match = re.search(r"Failing tests:\s*(\d+)", output)
                if not match:
                    raise RuntimeError("Resultado de teste não reconhecido")
                failures += int(match.group(1))

            row["test_s"] = round(test_time, 3)
            row["failing_tests"] = failures
            row["total_s"] = round(time.monotonic() - start, 3)
            row["status"] = "COMPLETED"

        except Exception as e:
            row["error"] = str(e)
            print(f"Erro: {e}", flush=True)

        finally:
            results.append(row)
            shutil.rmtree(ws, ignore_errors=True)

fields = [
    "project", "bug_id", "version", "scenario", "status",
    "pmd_s", "compile_s", "spotbugs_s", "test_s",
    "total_s", "failing_tests", "error"
]

with (OUT / "pilot.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print(f"Piloto salvo em {OUT / 'pilot.csv'}")
