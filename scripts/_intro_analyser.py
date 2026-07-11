import json

data = json.load(open('client/i18n/locales/swahili/intro.json', 'r', encoding='utf-8'))
keys = list(data.keys())

for i in range(20):
    k = keys[i]
    v = data[k]
    print(f'=== SECTION {i+1}: {k} ===')
    title = v.get('title', 'N/A')
    print(f'  title: {title}')
    
    intro = v.get('intro', [])
    if intro:
        for j, item in enumerate(intro):
            if len(str(item)) > 120:
                print(f'  intro[{j}]: {str(item)[:120]}...')
            else:
                print(f'  intro[{j}]: {item}')
    
    note = v.get('note', '')
    if note:
        if len(str(note)) > 120:
            print(f'  note: {str(note)[:120]}...')
        else:
            print(f'  note: {note}')
    
    blocks = v.get('blocks', {})
    if blocks:
        for bk, bv in blocks.items():
            bt = bv.get('title', 'N/A')
            print(f'    block: {bk}')
            print(f'      title: {bt}')
    print()