import sys
file_path = 'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(''.join(lines[:50]))
print('---')
print(f'Total lines: {len(lines)}')
print(f'First line repr: {repr(lines[0]) if lines else "EMPTY"}')
print(f'Second line repr: {repr(lines[1]) if len(lines) > 1 else "EMPTY"}')