filepath = 'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/build-a-budget-app-project/5e44413e903586ffb414c94e.md'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Check first 500 chars
print("First 500 characters:")
print(content[:500])
print("\n" + "="*60)

# Check for various language indicators
swahili_words = ['kufanya', 'kujenga', 'kupanga', 'kutengeneza', 'kupata', 'kutumia', 'kuandika', 'kutoka', 'kufungua', 'kupata', 'kuweka', 'kama', 'au', 'na', 'ya', 'wa', 'katika', 'kwa', 'la', 'ni', 'kuu', 'pia', 'hii', 'hilo', 'hizi', 'hizo']
serbian_words = ['izgradite', 'projekat', 'aplikacije', 'budžet', 'potpuni', 'klasu', 'trebalo', 'bi', 'da', 'može', 'inicijalizovati', 'stavke', 'na', 'osnovu', 'različitih']

content_lower = content.lower()

print("Swahili indicators found:")
for word in swahili_words:
    if word in content_lower:
        print(f"  ✓ {word}")

print("\nSerbian indicators found:")
for word in serbian_words:
    if word in content_lower:
        print(f"  ✓ {word}")