from pathlib import Path

INPUT_FILE = "translations.txt"

# Root folder gde se nalazi i18n-curriculum
ROOT = Path("curriculum/i18n-curriculum")

for row in Path(INPUT_FILE).read_text(encoding="utf-8").splitlines():
    if not row.strip():
        continue

    try:
        file_path, line_number, new_text = row.split("\t", 2)
    except ValueError:
        print(f"Neispravan red:\n{row}")
        continue

    # Dodaj putanju do i18n-curriculum
    file_path = ROOT / Path(file_path)
    line_number = int(line_number)

    if not file_path.exists():
        print(f"Fajl ne postoji: {file_path}")
        continue

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

    if line_number < 1 or line_number > len(lines):
        print(f"Linija {line_number} ne postoji u {file_path}")
        continue

    # Sačuvaj isti tip novog reda
    newline = "\n"
    if lines[line_number - 1].endswith("\r\n"):
        newline = "\r\n"

    old_line = lines[line_number - 1].rstrip("\r\n")
    lines[line_number - 1] = new_text + newline

    file_path.write_text("".join(lines), encoding="utf-8")

    print(f"✓ {file_path} (linija {line_number})")
    print(f"  STARO: {old_line}")
    print(f"  NOVO : {new_text}")