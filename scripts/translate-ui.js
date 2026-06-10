import fs from 'fs';

const FILE = 'client/i18n/locales/swahili/meta-tags.json';
const data = JSON.parse(fs.readFileSync(FILE, 'utf8'));

const MODEL = 'gemma4:latest';

// stabilan batch za lokalne modele
const BATCH_SIZE = 5;

// =========================
// COLLECT STRINGS
// =========================
function collectStrings(obj, path = [], out = []) {
  if (typeof obj === 'string') {
    out.push({ path, value: obj });
    return out;
  }

  if (Array.isArray(obj)) {
    obj.forEach((item, i) =>
      collectStrings(item, [...path, i], out)
    );
    return out;
  }

  if (obj && typeof obj === 'object') {
    Object.entries(obj).forEach(([k, v]) =>
      collectStrings(v, [...path, k], out)
    );
  }

  return out;
}

// =========================
// SET VALUE
// =========================
function setValue(obj, path, value) {
  let cur = obj;
  for (let i = 0; i < path.length - 1; i++) {
    cur = cur[path[i]];
  }
  cur[path[path.length - 1]] = value;
}

// =========================
// 🔥 ROBUST JSON PARSER (OLLAMA SAFE)
// =========================
function safeParse(text) {
  if (!text) throw new Error("Empty response");

  let cleaned = text
    .replace(/```json/g, "")
    .replace(/```/g, "")
    .trim();

  const start = cleaned.indexOf("[");
  const end = cleaned.lastIndexOf("]");

  if (start === -1 || end === -1) {
    console.log("❌ RAW OUTPUT:", cleaned);
    throw new Error("No JSON array found");
  }

  let jsonString = cleaned.slice(start, end + 1);

  // fix common Ollama mistakes
  jsonString = jsonString
    .replace(/,\s*}/g, "}")
    .replace(/,\s*]/g, "]");

  try {
    return JSON.parse(jsonString);
  } catch (e) {
    console.log("❌ BROKEN JSON:", jsonString);

    // fallback: extract strings only
    const matches = jsonString.match(/"([^"]+)"/g);
    if (matches) {
      return matches.map(m => m.replace(/"/g, ""));
    }

    throw e;
  }
}

// =========================
// OLLAMA CALL
// =========================
async function translateBatch(strings) {
  const prompt = `
You are a professional localization translator.

Translate English → Serbian (sr-RS).

IMPORTANT:
- Translate ALL UI text.
- Do NOT leave English words untranslated unless they are product names or technologies.
- Use natural Serbian UI terminology.
- Do NOT use Croatian, Bosnian, Montenegrin or Macedonian variants.
- Preserve placeholders like {{name}} exactly.
- Preserve HTML tags exactly.
- Preserve code snippets exactly.
- Keep the same order.

Translate these UI terms as:
Copy -> Kopiraj
View -> Prikaži
View Code -> Prikaži kod
View Project -> Prikaži projekat
Submit -> Pošalji
Submit and continue -> Pošalji i nastavi
Save Progress -> Sačuvaj napredak
Show Certification -> Prikaži sertifikat
Claim Certification -> Preuzmi sertifikat
Get Started -> Počni

Return ONLY a valid JSON array.
No markdown.
No explanations.

INPUT:
${JSON.stringify(strings)}
`;

  const res = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: MODEL,
      prompt,
      stream: false,
      options: {
        temperature: 0
      }
    })
  });

  const json = await res.json();

  const text = json?.response;

  if (!text) {
    console.log("❌ FULL RESPONSE:", json);
    throw new Error("Empty Ollama response");
  }

  return safeParse(text);
}

// =========================
// MAIN LOOP
// =========================
async function main() {
  const strings = collectStrings(data);

  console.log(`Found ${strings.length} strings`);

  for (let i = 0; i < strings.length; i += BATCH_SIZE) {
    const batch = strings.slice(i, i + BATCH_SIZE);

    try {
      const translated = await translateBatch(
        batch.map(x => x.value)
      );

      batch.forEach((item, idx) => {
        setValue(data, item.path, translated[idx]);
      });

      console.log(
        `Translated ${Math.min(i + BATCH_SIZE, strings.length)}/${strings.length}`
      );

      fs.writeFileSync(FILE, JSON.stringify(data, null, 2));

      // small delay for CPU stability
      await new Promise(r => setTimeout(r, 80));

    } catch (err) {
      console.log("❌ Batch failed at index:", i);
      console.error(err);

      // ne prekidamo sve – nego nastavljamo dalje
      continue;
    }
  }

  console.log("DONE");
}

main().catch(console.error);