#!/usr/bin/env python3
import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "emails.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "emails_listmonk.csv")

with open(INPUT_CSV, newline="", encoding="utf-8") as fin, \
     open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:

    reader = csv.DictReader(fin)
    writer = csv.writer(fout)
    writer.writerow(["email", "name", "attributes"])

    for row in reader:
        attributes = json.dumps({
            "language": row["language"],
            "geo": row["geo"],
        }, ensure_ascii=False)
        writer.writerow([row["email"], row["name"], attributes])

print(f"Done → {OUTPUT_CSV}")
