import re

filepath = 'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Show lines 1-15 to see the structure
print("First 15 lines:")
for i, line in enumerate(lines[:15], 1):
    print(f"  {i:3}: {repr(line)}")

# Find all section markers with flexible matching
print("\n\nAll section markers found:")
for i, line in enumerate(lines, 1):
    if '--description--' in line or '--instructions--' in line or '--hints--' in line or '--solutions--' in line:
        print(f"  Line {i}: {repr(line[:150])}")