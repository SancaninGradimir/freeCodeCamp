from pathlib import Path
import re

# Folder sa prevedenim fajlovima
ROOT = Path("curriculum/i18n-curriculum/curriculum/challenges/swahili")

# Rečnik svahili reči (jedna reč po redu)
DICT_FILE = "swahili_dictionary.txt"

# Izlaz
OUTPUT = "swahili_lines.txt"

# Koliko svahili reči mora da postoji u liniji
MIN_MATCHES = 3

# Učitaj rečnik
swahili_words = set()

with open(DICT_FILE, encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        # podržava i "reč\tbroj" i samo "reč"
        word = line.split()[0].lower()
        swahili_words.add(word)

results = []

for md_file in ROOT.rglob("*.md"):
    with md_file.open(encoding="utf-8") as f:
        in_code_block = False

        for line_no, line in enumerate(f, start=1):
            text = line.strip()

            if not text:
                continue

            # preskoči code blokove
            if text.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # izdvoji reči
            words = re.findall(r"[A-Za-zÀ-ÿ']+", text.lower())

            if not words:
                continue

            matches = sum(
                1
                for w in words
                if w in swahili_words
            )

            if matches >= MIN_MATCHES:
                rel_path = md_file.relative_to(ROOT.parent.parent.parent)
                results.append(f"{rel_path.as_posix()}:{line_no}:{text}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print(f"Pronađeno {len(results)} linija.")
print(f"Rezultat je upisan u {OUTPUT}")