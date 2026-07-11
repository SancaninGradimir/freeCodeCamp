from pathlib import Path
from collections import Counter
import re

ROOT = Path("curriculum/i18n-curriculum/curriculum/challenges/swahili_backup")
OUTPUT = "swahili_dictionary.txt"

counter = Counter()

for md_file in ROOT.rglob("*.md"):
    try:
        text = md_file.read_text(encoding="utf-8")
    except Exception:
        continue

    # Izbaci code blokove
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)

    # Izvuci sve reči
    words = re.findall(r"[A-Za-zÀ-ÿ']+", text.lower())

    for word in words:
        if len(word) < 2:
            continue
        counter[word] += 1

with open(OUTPUT, "w", encoding="utf-8") as f:
    for word, count in counter.most_common():
        f.write(f"{word}\t{count}\n")

print(f"Sačuvano {len(counter)} jedinstvenih reči u {OUTPUT}")