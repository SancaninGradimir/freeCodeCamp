import fs from 'fs';
import path from 'path';

const MODEL = 'gemma4:latest';

const DIRS = [
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-bash-commands',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-bash-scripting',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-basic-css',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-basic-html',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-classes-and-objects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-computer-basics',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-accessibility',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-animations',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-attribute-selectors',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-backgrounds-and-borders',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-colors',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-flexbox',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-grid',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-layout-and-effects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-libraries-and-frameworks',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-positioning',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-pseudo-classes',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-relative-and-absolute-units',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-typography',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-css-variables',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-data-structures',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-data-structures-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-debugging-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-design-fundamentals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-dictionaries-and-sets',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-dom-manipulation-and-click-events-with-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-dom-manipulation-by-building-a-rock-paper-scissors-game',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-dynamic-programming',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-dynamic-programming-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-error-handling',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-error-handling-in-express',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-express-middleware',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-form-validation-with-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-front-end-libraries',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-git',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-graphs-and-trees',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-graphs-and-trees-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-html',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-html-accessibility',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-html-tables-and-forms',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-http-and-the-web-standards-model',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-introduction-to-express',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-arrays',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-audio-and-video',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-classes',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-comparisons-and-conditionals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-dates',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-functional-programming',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-functions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-fundamentals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-higher-order-functions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-loops',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-maps-and-sets',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-math',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-objects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-regular-expressions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-strings',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-javascript-variables-and-data-types',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/review-js-a11y'
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
- # --description-- text
- # --hints-- text (but NOT the JavaScript code inside \`\`\`js blocks)
- # --assignment-- text
- any other natural language text

2. Do NOT translate:
- code blocks (\`\`\`...\`\`\`)
- inline code (\`like this\`)
- URLs
- programming keywords
- technical terms such as:
  JavaScript, HTML, CSS, Node.js, HTTP, API, GET, POST
- JavaScript variable names, function names, method names
- CSS property names, selector names

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
  const hasDescription = content.includes('# --description--');
  return hasDescription;
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
    .replace(/__CODE_BLOCK_\d+__/g, '');

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

// ======================================
// SAFE TRANSLATION
// ======================================

async function safeTranslate(text) {
  if (!text || !text.trim()) return text;

  console.log('SAFE:', text.substring(0, 120));

  const codeProtected = protectCodeBlocks(text);
  const inlineProtected = protectInlineCode(codeProtected.text);

  const textForTranslation = inlineProtected.text.trim();
  if (
    !textForTranslation ||
    /^__CODE_BLOCK_\d+__$/.test(textForTranslation) ||
    /^__INLINE_CODE_\d+__$/.test(textForTranslation)
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
  const parts = codeProtected.text.split(/(\n{2,})/);
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

  return restoreCodeBlocks(translatedParts.join(''), codeProtected.store);
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

  // Match marker then capture everything until the next # -- section marker (FCC marker) or end
  // Do NOT stop at ## sub-headers inside the content
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
      
      // Post-process: remove hallucinated FCC markers that the model sometimes inserts
      // The model may generate fake # --description--, # --hints--, # --assignment-- markers
      translated = translated.replace(/^# --(?:description|hints|assignment)--\s*tekst\s*$/gm, '');
      translated = translated.replace(/\n# --(?:description|hints|assignment)--\s*tekst\s*$/g, '');
      translated = translated.replace(/\n# --(?:description|hints|assignment)--\s*tekst\s*\n/g, '\n\n');
      
      // Remove any lines that match the "Objekat Promise je temeljni koncept" pattern or similar hallucinated content
      // These are paragraphs the model invents that don't correspond to any original text
      
      // Clean up excessive blank lines from removals
      translated = translated.replace(/\n{3,}/g, '\n\n');
      
      return `${prefix}${translated}`;
    }
  );
}

// ======================================
// REVIEW PROCESSING
// ======================================

async function translateReview(content) {
  // Translate description, hints, assignment - any # --xxx-- section
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