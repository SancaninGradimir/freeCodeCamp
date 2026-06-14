import fs from 'fs';
import path from 'path';

const MODEL = 'gemma4:latest';

const DIRS = [
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-bash-and-sql',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-bash-commands',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-bash-scripting',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-basic-css',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-basic-html',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-classes-and-objects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-computer-basics',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-accessibility',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-animations',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-attribute-selectors',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-backgrounds-and-borders',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-colors',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-flexbox',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-grid',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-layout-and-effects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-libraries-and-frameworks',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-positioning',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-pseudo-classes',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-relative-and-absolute-units',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-typography',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-css-variables',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-data-structures',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-data-structures-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-debugging-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-design-fundamentals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-dictionaries-and-sets',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-dom-manipulation-and-click-event-with-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-dynamic-programming',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-dynamic-programming-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-error-handling',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-error-handling-in-express',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-express-middleware',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-form-validation-with-javascript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-git',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-graph-and-trees-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-graphs-and-trees',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-html-accessibility',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-html-tables-and-forms',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-http-and-the-web-standards-model',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-introduction-to-express',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-arrays',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-audio-and-video',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-classes',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-comparisons-and-conditionals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-dates',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-functional-programming',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-functions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-fundamentals',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-higher-order-functions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-loops',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-maps-and-sets',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-math',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-objects',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-regular-expressions',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-strings',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-javascript-variables-and-data-types',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-js-a11y',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-local-storage-and-crud',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-loops-and-sequences',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-node-js-core-modules',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-node-js-intro',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-npm',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-object-oriented-programming',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-python-basics',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-python-installation',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-react-basics',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-react-forms-data-fetching-and-routing',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-react-state-and-hooks',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-recursion',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-responsive-web-design',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-searching-and-sorting-algorithms',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-searching-and-sorting-algorithms-js',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-semantic-html',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-sql-and-postgresql',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-styling-forms',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-testing',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-typescript',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-web-performance',
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-websockets'
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
- # --description--
- questions
- answers
- distractors
- feedback

2. Do NOT translate:
- code blocks
- URLs
- API names
- programming keywords
- technical terms such as:
  Promise, Fetch API, Response, Request, Callback, HTTP, API, GET, POST, PUT, DELETE, PATCH, async, await, JavaScript, Node.js

3. Fix grammar and spelling mistakes in the translation.

4. Use natural Serbian technical terminology. Avoid literal translations such as:
- "rezolvuje" → use "razrešava"
- "asinhronna" → "asinhrona"
- "asinhrokna" → "asinhrona"

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
  const hasQuizzes = content.includes('# --quizzes--');
  const hasQuiz = content.includes('## --quiz--');
  const hasQuestion = content.includes('### --question--');
  
  return hasQuizzes && hasQuiz && hasQuestion;
}

// ======================================
// UTILITIES
// ======================================

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

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

  // Remove protected tokens before checking
  const cleaned = text
    .replace(/__INLINE_CODE_\d+__/g, '')
    .replace(/__CODE_BLOCK_\d+__/g, '')
    .replace(/__FCC_MARKER_\d+__/g, '');

  const cleanedLower = cleaned.toLowerCase();

  const hasMarker = englishMarkers.some(word =>
    new RegExp(`\\b${word}\\b`, 'i').test(cleanedLower)
  );
  if (hasMarker) {
    return true;
  }

  // Check for English sentences (>60% English words, 6+ words)
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

function protectFCCMarkers(text) {
  const markers = [
    '# --quizzes--',
    '## --quiz--',
    '### --question--',
    '#### --text--',
    '#### --distractors--',
    '#### --answer--'
  ];

  let result = text;
  markers.forEach((marker, index) => {
    result = result.replaceAll(marker, `__FCC_MARKER_${index}__`);
  });

  return { text: result, markers };
}

function restoreFCCMarkers(text, markers) {
  let result = text;
  markers.forEach((marker, index) => {
    result = result.replaceAll(`__FCC_MARKER_${index}__`, marker);
  });
  return result;
}

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

  console.log('SAFE TRANSLATE:', text.substring(0, 120));

  const fccProtected = protectFCCMarkers(text);
  const codeProtected = protectCodeBlocks(fccProtected.text);
  const inlineProtected = protectInlineCode(codeProtected.text);

  // Skip if only non-translatable content
  const textForTranslation = inlineProtected.text.trim();
  if (
    !textForTranslation ||
    textForTranslation === '---' ||
    /^__CODE_BLOCK_\d+__$/.test(textForTranslation) ||
    /^__INLINE_CODE_\d+__$/.test(textForTranslation) ||
    /^__FCC_MARKER_\d+__$/.test(textForTranslation)
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

  // Restore
  translated = restoreInlineCode(translated, inlineProtected.store);
  translated = restoreCodeBlocks(translated, codeProtected.store);
  translated = restoreFCCMarkers(translated, fccProtected.markers);

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
// QUIZ SECTIONS
// ======================================

async function translateQuizQuestion(content) {
  console.log('TRANSLATING QUIZ QUESTION');

  // First translate `#### --text--` (question text)
  // Match #### --text-- then content until next #### or end
  content = await replaceAsync(
    content,
    /(#### --text--\s*?\n)([\s\S]*?)(?=\n####|$)/g,
    async (_match, prefix, body) => {
      const translated = await translateParagraphs(body);
      return `${prefix}${translated}`;
    }
  );

  // Translate `#### --distractors--` (wrong answers)
  content = await replaceAsync(
    content,
    /(#### --distractors--\s*?\n)([\s\S]*?)(?=\n####|$)/g,
    async (_match, prefix, body) => {
      const translated = await translateParagraphs(body);
      return `${prefix}${translated}`;
    }
  );

  // Translate `#### --answer--` (correct answer)
  content = await replaceAsync(
    content,
    /(#### --answer--\s*?\n)([\s\S]*?)(?=\n####|$|\n###)/g,
    async (_match, prefix, body) => {
      const translated = await translateParagraphs(body);
      return `${prefix}${translated}`;
    }
  );

  return content;
}

async function translateQuiz(content) {
  console.log('TRANSLATING: # --quizzes--');

  // Process each ### --question-- block
  content = await replaceAsync(
    content,
    /(### --question--\s*?\n)([\s\S]*?)(?=\n### --question--|$)/g,
    async (_match, prefix, body) => {
      console.log('QUESTION BLOCK FOUND, length:', body.length);
      const translated = await translateQuizQuestion(body);
      return `${prefix}${translated}`;
    }
  );

  return content;
}

async function translateDescription(content) {
  console.log('TRANSLATING: # --description--');

  const regex = /(# --description--\s*?\n)([\s\S]*?)(?=\n# --quizzes--)/g;

  return replaceAsync(
    content,
    regex,
    async (_match, prefix, body) => {
      const translated = await translateParagraphs(body);
      return `${prefix}${translated}`;
    }
  );
}

async function translateLesson(content) {
  content = await translateDescription(content);
  content = await translateQuiz(content);
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
    content = await translateLesson(content);

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