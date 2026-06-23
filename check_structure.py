import re

files = [
    'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md',
    'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-cash-register-project/657bdcc3a322aae1eac38392.md',
]

for filepath in files:
    print(f"\n{'='*60}")
    print(f"FILE: {filepath}")
    print('='*60)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")
    print(f"Total size: {len(content)} bytes")
    
    # Find all section markers
    section_pattern = r'^(# --[a-z-]+--|## --[a-z-]+--)'
    sections = []
    for i, line in enumerate(lines):
        if re.match(section_pattern, line):
            sections.append((i+1, line))
    
    print(f"\nFound {len(sections)} sections:")
    for line_num, marker in sections:
        print(f"  Line {line_num}: {marker}")
    
    # Show first 20 lines
    print(f"\nFirst 20 lines:")
    for i, line in enumerate(lines[:20], 1):
        print(f"  {i:3}: {line[:100]}")