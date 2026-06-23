import re

def parse_markdown_sections(content):
    """Parse markdown file into sections for translation."""
    sections = []
    
    # Split by section markers while keeping the markers
    parts = re.split(r'(\n?[-]*#\s*--[a-z-]+--)', content)
    
    current_section = None
    section_content = []
    
    for part in parts:
        # Check if this is a section marker
        match = re.match(r'\n?[-]*#\s*--([a-z-]+)--', part)
        if match:
            # Save previous section if exists
            if current_section and section_content:
                sections.append((current_section, ''.join(section_content)))
            
            # Start new section
            current_section = match.group(1)
            section_content = [part]
        else:
            # This is content
            if current_section is not None:
                section_content.append(part)
    
    # Don't forget the last section
    if current_section and section_content:
        sections.append((current_section, ''.join(section_content)))
    
    return sections

# Test with the budget app file
filepath = 'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

sections = parse_markdown_sections(content)

print(f"Found {len(sections)} sections:")
for i, (name, content) in enumerate(sections, 1):
    print(f"\n{i}. Section: {name}")
    print(f"   Size: {len(content)} bytes")
    print(f"   First 100 chars: {repr(content[:100])}")