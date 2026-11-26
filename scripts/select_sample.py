import csv
import random
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = root / "data/raw/defects4j/eligibility.csv"
output = root / "data/processed/sample_30.csv"

rng = random.Random(20261126)

with source.open(newline="") as f:
    rows = list(csv.DictReader(f))

sample = []

for project in ["Lang", "Jsoup", "Gson"]:
    eligible = [
        r for r in rows
        if r["project"] == project
        and r["eligibility"] == "ELIGIBLE"
    ]

    eligible.sort(key=lambda r: int(r["bug_id"]))

    if len(eligible) < 10:
        raise ValueError(f"{project}: menos de 10 elegíveis")

    sample.extend(rng.sample(eligible, 10))
    print(f"{project}: {len(eligible)} elegíveis, 10 selecionados")

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(sample)

print(f"Amostra salva em: {output}")
print(f"Total: {len(sample)} defeitos")
