import json

data = json.load(open('client/i18n/locales/swahili/intro.json', 'r', encoding='utf-8'))
keys = list(data.keys())

print('=== TRANSLATION VERIFICATION ===')
print()

# Check sections that had English text
checks = [
    (3, 'javascript-algorithms-and-data-structures-v8'),
    (4, 'front-end-development-libraries'),
    (10, 'scientific-computing-with-python'),
    (12, 'learn-python-for-beginners'),
    (13, 'introduction-to-algorithms-and-data-structures'),
    (14, 'learn-rag-mcp-fundamentals'),
    (15, 'introduction-to-precalculus'),
    (16, 'introduction-to-bash'),
    (17, 'introduction-to-sql-and-postgresql'),
    (18, 'learn-bash-scripting'),
    (19, 'learn-sql-and-bash'),
]

for idx, name in checks:
    section = data.get(name, {})
    title = section.get('title', 'MISSING')
    intro = section.get('intro', [])
    print(f'--- Section {idx+1}: {name} ---')
    print(f'  title: {title}')
    if intro:
        print(f'  intro[0]: {intro[0][:120]}')
    blocks = section.get('blocks', {})
    if blocks:
        for bk, bv in list(blocks.items())[:2]:
            print(f'  block: {bk}')
            print(f'    title: {bv.get("title", "MISSING")}')
    print()

print('=== Check JSON is still valid ===')
try:
    json.dumps(data, ensure_ascii=False)
    print('JSON valid: YES')
except Exception as e:
    print(f'JSON valid: NO - {e}')

print()
print(f'Total top-level sections: {len(keys)}')
print(f'First 20 processed: {keys[0]} to {keys[19]}')