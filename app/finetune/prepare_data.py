"""Turn Q&A pairs into the chat JSONL format Azure OpenAI fine-tuning expects.
Input:  finetune/pairs.csv  with columns question,answer
Output: finetune/train.jsonl and finetune/validation.jsonl (80/20 split)"""
import csv
import json
import random
from pathlib import Path

SYSTEM = "You answer questions about PallerlaFin credit policy in a concise, formal style."
here = Path(__file__).parent
rows = list(csv.DictReader((here / "pairs.csv").open(encoding="utf-8")))
random.Random(7).shuffle(rows)
cut = max(1, int(len(rows) * 0.8))


def dump(name, items):
    with (here / name).open("w", encoding="utf-8") as fh:
        for r in items:
            fh.write(json.dumps({"messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": r["question"]},
                {"role": "assistant", "content": r["answer"]}]}) + "\n")


dump("train.jsonl", rows[:cut])
dump("validation.jsonl", rows[cut:])
print(f"train={cut} validation={len(rows) - cut}")
