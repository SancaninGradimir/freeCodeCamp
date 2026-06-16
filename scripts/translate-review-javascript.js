import fs from 'fs';
import path from 'path';

const MODEL = 'gemma4:latest';

const DIRS = [
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lab-world-cup-database'
];

let translatedFiles = 0;
let skippedFiles = 0;
let failedFiles = 0;
let translatedBlocks = 0;
let failedBlocks = 0;
let retriedBlocks = 0;

// ======================================
// OLLAMA
// ======================================

async function translateText(text, overridePrompt) {
  if (!text || !text.trim()) {
    return text;
  }

  const prompt = overridePrompt
    ? `${overridePrompt}

TEXT:

${text}`
    : `
Translate ALL user-facing text into Serbian (sr-RS).

IMPORTANT:

1. Translate ALL user-facing text, including:
- title
- # --interactive-- text
- # --description-- text
- ## sub-headers
- bullet points
- any other natural language text

2. Do NOT translate:
- code blocks (\`\`\`...\`\`\`)
- inline code (\`like this\`)
- URLs
- programming keywords
- technical terms such as:
  JavaScript, HTML, CSS, Node.js, console.log
- JavaScript variable names, function names, method names

3. Fix grammar and spelling mistakes in the translation.

4. Use natural Serbian technical terminology.

5. Keep Markdown structure unchanged.

TEXT:

${text}
`;

  const res = await fetch(
    'http://localhost:11434/api/generate',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: MODEL,
        prompt,
        stream: false,
        options: {
          temperature: 0
        }
      })
    }
  );

  if (!res.ok) {
    throw new Error(
      `Ollama HTTP Error: ${res.status}`
    );
  }

  const json = await res.json();

  if (!json.response) {
    throw new Error(
      'Ollama returned empty response'
    );
  }

  return json.response;
}

// ======================================
// BACKUP
// ======================================

function backupFile(file) {
  const backup = `${file}.bak`;
  if (!fs.existsSync(backup)) {
    fs.copyFileSync(file, backup);
  }
}

// ======================================
// VALIDATION
// ======================================

function validate(content) {
  const hasInteractive = content.includes('# --interactive--');
  const hasDescription = content.includes('# --description--');
  return hasInteractive || hasDescription;
}

// ======================================
// UTILITIES
// ======================================

function containsEnglish(text) {
  const lower = text.toLowerCase();
  const englishMarkers = [
    'the', 'and', 'for', 'with', 'that', 'this', 'have', 'from',
    'when', 'what', 'why', 'how', 'more', 'also', 'can', 'will',
    'should', 'could', 'would', 'but', 'not', 'are', 'was', 'been',
    'into', 'well', 'then', 'than', 'just', 'about', 'makes', 'make',
    'here', 'there', 'their', 'your', 'some', 'each', 'which', 'while',
    'where', 'still', 'even', 'because', 'after', 'before', 'between',
    'through', 'during', 'without', 'always', 'these', 'those', 'being',
    'done', 'using', 'first', 'last', 'over', 'under', 'such', 'very',
    'many', 'much', 'both', 'most', 'other', 'every', 'too', 'its',
    'has', 'had', 'did', 'get', 'got', 'see', 'say', 'use', 'may'
  ];

  const cleaned = text
    .replace(/__INLINE_CODE_\d+__/g, '')
    .replace(/__CODE_BLOCK_\d+__/g, '')
    .replace(/__INTERACTIVE_EDITOR_\d+__/g, '');

  const cleanedLower = cleaned.toLowerCase();

  const hasMarker = englishMarkers.some(word =>
    new RegExp(`\\b${word}\\b`, 'i').test(cleanedLower)
  );
  if (hasMarker) {
    return true;
  }

  const lines = cleaned.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.length < 25) continue;
    if (/^[#\-\*>\s`]/.test(trimmed)) continue;
    if (/[čćžšđČĆŽŠĐ]/.test(trimmed)) continue;

    const words = trimmed.split(/\s+/);
    let englishWordCount = 0;
    for (const word of words) {
      const clean = word.replace(/[^a-zA-Z]/g, '');
      if (clean.length >= 4 && /[aeiou]/i.test(clean)) {
        englishWordCount++;
      }
    }
    if (words.length >= 6 && englishWordCount >= words.length * 0.6) {
      return true;
    }
  }

  return false;
}

async function replaceAsync(string, regex, callback) {
  const parts = [];
  let lastIndex = 0;

  for (const match of string.matchAll(regex)) {
    const index = match.index || 0;
    parts.push(string.slice(lastIndex, index));
    parts.push(await callback(...match));
    lastIndex = index + match[0].length;
  }

  parts.push(string.slice(lastIndex));
  return parts.join('');
}

// ======================================
// PROTECTION
// ======================================

function protectCodeBlocks(text) {
  const store = [];
  const protectedText = text.replace(
    /```[\s\S]*?```/g,
    match => {
      const token = `__CODE_BLOCK_${store.length}__`;
      store.push(match);
      return token;
    }
  );
  return { text: protectedText, store };
}

function restoreCodeBlocks(text, store) {
  let result = text;
  store.forEach((value, index) => {
    result = result.replaceAll(`__CODE_BLOCK_${index}__`, value);
  });
  return result;
}

function protectInlineCode(text) {
  const store = [];
  const protectedText = text.replace(
    /`[^`\n]+`/g,
    match => {
      const token = `__INLINE_CODE_${store.length}__`;
      store.push(match);
      return token;
    }
  );
  return { text: protectedText, store };
}

function restoreInlineCode(text, store) {
  let result = text;
  store.forEach((value, index) => {
    result = result.replaceAll(`__INLINE_CODE_${index}__`, value);
  });
  return result;
}

function protectInteractiveEditors(text) {
  const store = [];
  const protectedText = text.replace(
    /:::interactive_editor[\s\S]*?:::/g,
    match => {
      const token = `__INTERACTIVE_EDITOR_${store.length}__`;
      store.push(match);
      return token;
    }
  );
  return { text: protectedText, store };
}

function restoreInteractiveEditors(text, store) {
  let result = text;
  store.forEach((value, index) => {
    result = result.replaceAll(`__INTERACTIVE_EDITOR_${index}__`, value);
  });
  return result;
}

// ======================================
// SAFE TRANSLATION
// ======================================

async function safeTranslate(text) {
  if (!text || !text.trim()) return text;

  console.log('SAFE:', text.substring(0, 120));

  const codeProtected = protectCodeBlocks(text);
  const interactiveProtected = protectInteractiveEditors(codeProtected.text);
  const inlineProtected = protectInlineCode(interactiveProtected.text);

  const textForTranslation = inlineProtected.text.trim();
  if (
    !textForTranslation ||
    /^__CODE_BLOCK_\d+__$/.test(textForTranslation) ||
    /^__INLINE_CODE_\d+__$/.test(textForTranslation) ||
    /^__INTERACTIVE_EDITOR_\d+__$/.test(textForTranslation)
  ) {
    return text;
  }

  let translated;
  try {
    translated = await translateText(inlineProtected.text);
  } catch (err) {
    console.warn('Translation failed, returning original:', err.message);
    return text;
  }

  console.log('MODEL:', translated.substring(0, 120));

  if (
    translated.includes('Translate English') ||
    translated.includes('IMPORTANT:') ||
    translated.includes('TEXT:')
  ) {
    console.warn('Model returned prompt - returning original');
    return text;
  }

  translated = restoreInlineCode(translated, inlineProtected.store);
  translated = restoreInteractiveEditors(translated, interactiveProtected.store);
  translated = restoreCodeBlocks(translated, codeProtected.store);

  if (translated.trim() !== text.trim()) {
    translatedBlocks++;
  }

  return translated;
}

// ======================================
// PARAGRAPH TRANSLATION
// ======================================

async function translateParagraphs(body) {
  const codeProtected = protectCodeBlocks(body);
  const interactiveProtected = protectInteractiveEditors(codeProtected.text);
  const parts = interactiveProtected.text.split(/(\n{2,})/);
  const translatedParts = [];

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (i % 2 === 0) {
      const trimmed = part.trim();
      if (trimmed) {
        translatedParts.push(await safeTranslate(part));
      } else {
        translatedParts.push(part);
      }
    } else {
      translatedParts.push(part);
    }
  }

  const joined = translatedParts.join('');
  return restoreInteractiveEditors(joined, interactiveProtected.store);
}

// ======================================
// TITLE TRANSLATION
// ======================================

async function translateTitle(content) {
  const match = content.match(/^title:\s*(.+)$/m);
  if (!match) return content;

  const originalTitle = match[1];
  console.log(`Title: "${originalTitle}"`);

  const translatedTitle = await translateText(originalTitle);
  console.log(`Title ->: "${translatedTitle}"`);

  if (/(TEXT:|IMPORTANT:|# --)/i.test(translatedTitle || '') || (translatedTitle || '').includes('\n')) {
    console.warn('Title invalid, keeping original');
    return content;
  }

  return content.replace(match[0], `title: ${translatedTitle}`);
}

// ======================================
// SECTIONS - translate marker content
// ======================================

async function translateSection(content, markerName) {
  console.log(`TRANSLATING: ${markerName}`);

  const escapedMarker = markerName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(
    `(${escapedMarker}\\s*?\\n)([\\s\\S]*?)(?=\\n# --|$)`,
    'g'
  );

  return replaceAsync(
    content,
    regex,
    async (_match, prefix, body) => {
      const trimmed = body.trim();
      if (!trimmed) return _match;
      console.log(`BODY length: ${body.length}`);
      let translated = await translateParagraphs(body);

      // Clean up hallucinated FCC markers
      translated = translated.replace(/^# --(?:description|hints|assignment|interactive)--\s*tekst\s*$/gm, '');
      translated = translated.replace(/\n# --(?:description|hints|assignment|interactive)--\s*tekst\s*$/g, '');
      translated = translated.replace(/\n# --(?:description|hints|assignment|interactive)--\s*tekst\s*\n/g, '\n\n');
      translated = translated.replace(/\n{3,}/g, '\n\n');

      return `${prefix}${translated}`;
    }
  );
}

// ======================================
// REVIEW PROCESSING
// ======================================

async function translateReview(content) {
  // Translate all possible section types
  content = await translateSection(content, '# --interactive--');
  content = await translateSection(content, '# --description--');
  content = await translateSection(content, '# --hints--');
  content = await translateSection(content, '# --assignment--');
  return content;
}

// ======================================
// FILE PROCESSING
// ======================================

async function processFile(file) {
  try {
    console.log(`\nProcessing: ${file}`);

    backupFile(file);

    let content = fs.readFileSync(file, 'utf8');
    const bak = `${file}.bak`;
    if (fs.existsSync(bak)) {
      console.log('Restoring from backup...');
      content = fs.readFileSync(bak, 'utf8');
    }

    const originalContent = content;

    content = await translateTitle(content);
    content = await translateReview(content);

    if (containsEnglish(content)) {
      console.warn('English content detected after translation');
    }

    if (!validate(content)) {
      console.log(`❌ Validation failed: ${file}`);
      return;
    }

    if (content === originalContent) {
      console.log('No changes; skipping');
      skippedFiles++;
      return;
    }

    fs.writeFileSync(file, content, 'utf8');
    translatedFiles++;
    console.log('✓ Done');
  } catch (err) {
    console.error(`❌ Error in ${file}: ${err.message}`);
    failedFiles++;
  }
}

// ======================================
// MAIN
// ======================================

async function main() {
  const files = [];

  for (const dir of DIRS) {
    if (!fs.existsSync(dir)) {
      console.warn(`Directory not found: ${dir}`);
      continue;
    }

    files.push(
      ...fs.readdirSync(dir)
        .filter(f => f.endsWith('.md'))
        .sort()
        .map(f => path.join(dir, f))
    );
  }

  console.log(`Found ${files.length} files`);

  for (const file of files) {
    await processFile(file);
  }

  console.log('\n=== SUMMARY ===');
  console.log(`Translated files: ${translatedFiles}`);
  console.log(`Skipped files: ${skippedFiles}`);
  console.log(`Failed files: ${failedFiles}`);
  console.log(`Translated blocks: ${translatedBlocks}`);
  console.log(`Failed blocks: ${failedBlocks}`);
  console.log(`Retried blocks: ${retriedBlocks}`);
}

main().catch(console.error);