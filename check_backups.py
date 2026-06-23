import os
files = [
    'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md.bak',
    'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-cash-register-project/657bdcc3a322aae1eac38392.md.bak',
    'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-polygon-area-calculator-project/5e444147903586ffb414c94f.md.bak',
]
for f in files:
    exists = os.path.exists(f)
    size = os.path.getsize(f) if exists else -1
    print(f"{f}: exists={exists}, size={size}")