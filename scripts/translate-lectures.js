import fs from 'fs';
import path from 'path';

const MODEL = 'qwen3:32b';

const DIRS = [
  'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-accessible-media-elements'
];

const FORCE_RESTORE_FROM_BAK = true;
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
Translate ALL English natural language into Serbian (sr-RS).

IMPORTANT:

- Translate all English sentences.
- Do NOT leave any English unchanged.
- Preserve markdown exactly.
- Preserve all line breaks.
- Preserve all blank lines.
- Preserve code blocks exactly.
- Preserve inline code exactly.
- Preserve :::interactive_editor blocks exactly.
- Preserve HTML tags exactly.
- Preserve CSS exactly.
- Preserve JavaScript code exactly.
- Preserve all FCC markers exactly.
- Do not explain anything.
- Return ONLY translated text.

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
  const hasInteractive =
    content.includes('# --interactive--');

  const hasDescription =
    content.includes('# --description--');

  const hasQuestions =
    content.includes('# --questions--');

  if (
    !hasInteractive &&
    !hasDescription
  ) {
    return false;
  }

  if (!hasQuestions) {
    return false;
  }

  const beforeEditors =
    (content.match(
      /:::interactive_editor/g
    ) || []).length;

  const afterEditors =
    (content.match(
      /:::/g
    ) || []).length;

  if (
    beforeEditors > 0 &&
    afterEditors < beforeEditors * 2
  ) {
    return false;
  }

  return true;
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
    'the',
    'and',
    'for',
    'with',
    'that',
    'this',
    'have',
    'from',
    'when',
    'what',
    'why',
    'how',
    'more',
    'also',
    'can',
    'will',
    'should',
    'could',
    'would'
  ];

  return englishMarkers.some(word =>
    new RegExp(`\\b${word}\\b`, 'i').test(lower)
  );
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
// FCC MARKERS
// ======================================

function protectFCCMarkers(text) {
  const markers = [
    '# --interactive--',
    '# --description--',
    '# --questions--',
    '## --text--',
    '## --answers--',
    '### --feedback--',
    '## --video-solution--'
  ];

  let result = text;

  markers.forEach((marker, index) => {
    result = result.replaceAll(
      marker,
      `__FCC_MARKER_${index}__`
    );
  });

  return {
    text: result,
    markers
  };
}

function restoreFCCMarkers(
  text,
  markers
) {
  let result = text;

  markers.forEach((marker, index) => {
    result = result.replaceAll(
      `__FCC_MARKER_${index}__`,
      marker
    );
  });

  return result;
}

// ======================================
// CODE BLOCKS
// ======================================

function protectCodeBlocks(text) {
  const store = [];

  const protectedText = text.replace(
    /```[\s\S]*?```/g,
    match => {
      const token =
        `__CODE_BLOCK_${store.length}__`;

      store.push(match);

      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreCodeBlocks(
  text,
  store
) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__CODE_BLOCK_${index}__`,
      value
    );
  });

  return result;
}

// ======================================
// INLINE CODE
// ======================================

function protectInlineCode(text) {
  const store = [];

  const protectedText = text.replace(
    /`[^`\n]+`/g,
    match => {
      const token =
        `__INLINE_CODE_${store.length}__`;

      store.push(match);

      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreInlineCode(
  text,
  store
) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__INLINE_CODE_${index}__`,
      value
    );
  });

  return result;
}

// ======================================
// INTERACTIVE EDITORS
// ======================================

function protectInteractiveEditors(
  text
) {
  const store = [];

  const protectedText = text.replace(
    /:::interactive_editor[\s\S]*?:::/g,
    match => {
      const token =
        `__INTERACTIVE_EDITOR_${store.length}__`;

      store.push(match);

      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreInteractiveEditors(
  text,
  store
) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__INTERACTIVE_EDITOR_${index}__`,
      value
    );
  });

  return result;
}

// ======================================
// HTML / STYLE / SCRIPT BLOCKS
// ======================================

function protectStyleBlocks(text) {
  const store = [];

  const protectedText = text.replace(
    /<style[\s\S]*?<\/style>/gi,
    match => {
      const token = `__STYLE_BLOCK_${store.length}__`;

      store.push(match);
      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreStyleBlocks(text, store) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__STYLE_BLOCK_${index}__`,
      value
    );
  });

  return result;
}

function protectScriptBlocks(text) {
  const store = [];

  const protectedText = text.replace(
    /<script[\s\S]*?<\/script>/gi,
    match => {
      const token = `__SCRIPT_BLOCK_${store.length}__`;

      store.push(match);
      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreScriptBlocks(text, store) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__SCRIPT_BLOCK_${index}__`,
      value
    );
  });

  return result;
}

function protectHtmlTags(text) {
  const store = [];

  const protectedText = text.replace(
    /<[^>]+>/g,
    match => {
      const token = `__HTML_TAG_${store.length}__`;

      store.push(match);
      return token;
    }
  );

  return {
    text: protectedText,
    store
  };
}

function restoreHtmlTags(text, store) {
  let result = text;

  store.forEach((value, index) => {
    result = result.replaceAll(
      `__HTML_TAG_${index}__`,
      value
    );
  });

  return result;
}

async function translateParagraphs(body) {
  const codeProtected = protectCodeBlocks(body);
  const paragraphs = codeProtected.text.split(/\n\n+/);
  const translatedParagraphs = [];

  for (const paragraph of paragraphs) {
    const trimmed = paragraph.trim();

    if (!trimmed) {
      translatedParagraphs.push(paragraph);
      continue;
    }

    translatedParagraphs.push(
      await safeTranslate(paragraph)
    );
  }

  return restoreCodeBlocks(
    translatedParagraphs.join('\n\n'),
    codeProtected.store
  );
}

// ======================================
// SAFE TRANSLATION
// ======================================

async function safeTranslate(text) {
  console.log(
    'SAFE TRANSLATE CALLED'
  );

  console.log(
    text.substring(0, 150)
  );

  const beforeCodeBlocks =
    (text.match(/```/g) || []).length;
  const beforeEditorOpeners =
    (text.match(/:::interactive_editor/g) || []).length;

  const fccProtected = protectFCCMarkers(text);
  // Protect code blocks before HTML so HTML inside code examples is not tokenized.
  const codeProtected = protectCodeBlocks(
    fccProtected.text
  );
  // Protect interactive editors before HTML as well.
  const interactiveProtected = protectInteractiveEditors(
    codeProtected.text
  );
  const inlineProtected = protectInlineCode(
    interactiveProtected.text
  );
  const styleProtected = protectStyleBlocks(
    inlineProtected.text
  );
  const scriptProtected = protectScriptBlocks(
    styleProtected.text
  );

  let translated = await translateText(
    inlineProtected.text
  );

  console.log(
    'MODEL RESPONSE PREVIEW:'
  );

  console.log(
    translated.substring(0, 500)
  );

  if (
    translated.includes('Translate English') ||
    translated.includes('IMPORTANT:') ||
    translated.includes('TEXT:')
  ) {
    throw new Error('Model returned prompt instead of translation');
  }

  const inputParagraphs = inlineProtected.text
    .split(/\n\s*\n/)
    .filter(Boolean).length;
  const outputParagraphs = translated
    .split(/\n\s*\n/)
    .filter(Boolean).length;

  console.log({
    inputParagraphs,
    outputParagraphs
  });

  if (
    inputParagraphs > 0 &&
    outputParagraphs < inputParagraphs * 0.7
  ) {
    retriedBlocks++;
    console.warn(
      'Partial translation detected, retrying with stronger prompt'
    );

    translated = await translateText(
      inlineProtected.text,
      `Translate EVERYTHING into Serbian (sr-RS).

Do NOT leave any English sentences.

Rules:
- Translate all natural language
- Preserve markdown exactly
- Preserve code blocks exactly
- Preserve inline code exactly
- Preserve HTML tags exactly
- Preserve CSS exactly
- Preserve JavaScript code exactly
- Preserve all FCC markers exactly
- Return ONLY Serbian text`
    );

    console.log(
      'MODEL RESPONSE PREVIEW:'
    );

    console.log(
      translated.substring(0, 500)
    );

    const retryOutputParagraphs = translated
      .split(/\n\s*\n/)
      .filter(Boolean).length;

    console.log({
      inputParagraphs,
      retryOutputParagraphs
    });

    if (retryOutputParagraphs < inputParagraphs * 0.7) {
      failedBlocks++;
      throw new Error('Partial translation detected');
    }
  }

  if (containsEnglish(translated)) {
    console.warn('Partial English detected');
  }

  if (
    /TEXT:/i.test(translated) ||
    /IMPORTANT:/i.test(translated)
  ) {
    throw new Error(
      'Model returned prompt instead of translation'
    );
  }

  const originalTrimmed = inlineProtected.text.trim();
  const translatedTrimmed = translated.trim();

  const originalNormalized =
    originalTrimmed
      .replace(/\s+/g, ' ')
      .toLowerCase();

  const translatedNormalized =
    translatedTrimmed
      .replace(/\s+/g, ' ')
      .toLowerCase();

  if (
    originalTrimmed.length > 50 &&
    originalNormalized === translatedNormalized
  ) {
    retriedBlocks++;

    translated = await translateText(
      inlineProtected.text,
      `Translate ALL English natural language into Serbian.

Do NOT leave any English sentences unchanged.

Preserve:
- markdown
- code blocks
- inline code
- HTML
- FCC markers

Return only Serbian text.
`
    );

    if (inlineProtected.text.trim() === translated.trim()) {
      failedBlocks++;
      throw new Error('Translation failed: content remained in English');
    }
  }

  translated = restoreScriptBlocks(
    translated,
    scriptProtected.store
  );
  translated = restoreStyleBlocks(
    translated,
    styleProtected.store
  );
  translated = restoreInlineCode(
    translated,
    inlineProtected.store
  );
  translated = restoreInteractiveEditors(
    translated,
    interactiveProtected.store
  );
  translated = restoreCodeBlocks(
    translated,
    codeProtected.store
  );
  translated = restoreFCCMarkers(
    translated,
    fccProtected.markers
  );

  if (translated.trim() !== text.trim()) {
    translatedBlocks++;
  }

  const afterCodeBlocks =
    (translated.match(/```/g) || []).length;
  const afterEditorOpeners =
    (translated.match(/:::interactive_editor/g) || []).length;

  if (beforeCodeBlocks !== afterCodeBlocks) {
    throw new Error(
      'Code block count changed during translation'
    );
  }

  if (beforeEditorOpeners !== afterEditorOpeners) {
    throw new Error(
      'Interactive editor count changed during translation'
    );
  }

  return translated;
}

async function translateTitle(content) {
  const match = content.match(/^title:\s*(.+)$/m);

  if (!match) {
    return content;
  }

  const originalTitle = match[1];
  console.log(`Title original: "${originalTitle}"`);

  const translatedTitle = await translateText(originalTitle);

  console.log(`Title translated: "${translatedTitle}"`);
  console.log(
    `Title length: before=${originalTitle.length}, after=${(
      translatedTitle || ''
    ).length}`
  );

  // Validation: reject obviously-bad translations
  const invalidChecks = [
    /TEXT:/i,
    /IMPORTANT:/i,
    /# --/ // any FCC marker leakage
  ];

  const hasInvalid = invalidChecks.some(rx => rx.test(translatedTitle || ''));
  const hasNewline = (translatedTitle || '').includes('\n');

  if (hasInvalid || hasNewline) {
    console.warn('Title translation invalid — keeping original title');
    return content;
  }

  return content.replace(
    match[0],
    `title: ${translatedTitle}`
  );
}

async function translateIntroSection(content) {
  console.log('ENTER translateIntroSection');

  const matches = content.match(
    /(^# --interactive--\n)([\s\S]*?)(?=^# --questions--|$)/gm
  );

  console.log('MATCHES:', matches?.length || 0);

  console.log(
    'ENTERED translateIntroSection'
  );

  console.log(
    JSON.stringify(
      content.slice(
        content.indexOf('# --interactive--'),
        content.indexOf('# --interactive--') + 200
      )
    )
  );

  // Translate either the interactive or description intro section.
  if (content.includes('# --interactive--')) {
    console.log(
      'INTERACTIVE SECTION DETECTED'
    );

    const testMatch =
      content.match(
        /(^# --interactive--\s*\n)([\s\S]*?)(?=^# --questions--|$)/gm
      );

    console.log(
      'INTERACTIVE MATCH:',
      !!testMatch
    );

    if (testMatch) {
      console.log(
        'MATCH LENGTH:',
        testMatch[0].length
      );
    }

    const regex = /(^# --interactive--\s*\n)([\s\S]*?)(?=^# --questions--|$)/gm;

    console.log(
      'USING INTERACTIVE REGEX'
    );

    return replaceAsync(content, regex, async (_match, prefix, body) => {
      console.log(
        'BODY LENGTH:',
        body.length
      );

      console.log(
        'BODY PREVIEW:',
        body.substring(0, 150)
      );
      const translatedBody = await translateParagraphs(body);

      if (body.trim().length > 80 && body.trim() === (translatedBody || '').trim()) {
        console.warn('Warning: interactive/intro block unchanged after translation');
      }

      return `${prefix}${translatedBody}`;
    });
  }

  // Fallback: description
  const regex = /(^# --description--\s*\n)([\s\S]*?)(?=^# --questions--|$)/gm;

  return replaceAsync(content, regex, async (_match, prefix, body) => {
    const codeProtected = protectCodeBlocks(body);
    let translatedBody = await translateParagraphs(body);

    if (
      containsEnglish(translatedBody) ||
      body.trim() === (translatedBody || '').trim()
    ) {
      console.warn('Retrying description block with stronger prompt');
      const retry = await translateText(
        codeProtected.text,
        `Translate EVERYTHING into Serbian (sr-RS).

Do NOT leave any English sentences.

Rules:
- Translate all natural language
- Preserve markdown exactly
- Preserve code, HTML, and FCC markers
- Return ONLY Serbian text`
      );
      translatedBody = restoreCodeBlocks(retry, codeProtected.store);
    }

    if (body.trim().length > 80 && body.trim() === (translatedBody || '').trim()) {
      console.warn('Warning: description block unchanged after translation');
    }

    return `${prefix}${translatedBody}`;
  });
}

async function translateSectionBlocks(
  content,
  marker,
  nextMarkersPattern
) {
  const regex = new RegExp(
    `(${escapeRegExp(marker)}\\s*\\n)([\\s\\S]*?)(?=(?:${nextMarkersPattern})|$)`,
    'gm'
  );

  return replaceAsync(
    content,
    regex,
    async (_match, prefix, body) => {
      let translatedBody = await translateParagraphs(body);

      if (
        containsEnglish(translatedBody) ||
        body.trim() === (translatedBody || '').trim()
      ) {
        console.warn(
          `Retrying section '${marker}' with stronger prompt`
        );

        translatedBody = await translateParagraphs(body);
      }

      if (/[a-zA-Z]{4,}/.test(translatedBody)) {
        const codeProtected = protectCodeBlocks(body);
        const retry = await translateText(
          codeProtected.text,
          'Translate ALL text into Serbian. No English allowed.'
        );

        translatedBody = restoreCodeBlocks(retry, codeProtected.store);
      }

      try {
        const THRESHOLD = 60;

        if (
          body.trim().length > THRESHOLD &&
          body.trim() === (translatedBody || '').trim()
        ) {
          console.warn(
            `Warning: section '${marker}' unchanged after translation (${body.trim().length} chars)`
          );
        }
      } catch (err) {
        // non-fatal
      }

      return `${prefix}${translatedBody}`;
    }
  );
}

async function translateQuestionSection(content) {
  console.log('ENTER translateQuestionSection');

  const matches = content.match(
    /(# --questions--\s*\n)([\s\S]*?)(?=(?:^# --questions--)|$)/gm
  );

  console.log(
    'QUESTION MATCHES:',
    matches?.length || 0
  );

  // Process every # --questions-- block, not just the first one.
  const questionSectionRegex = /(# --questions--\s*\n)([\s\S]*?)(?=(?:^# --questions--)|$)/gm;

  return replaceAsync(
    content,
    questionSectionRegex,
    async (_match, prefix, body) => {
      console.log(
        'QUESTION BLOCK FOUND'
      );

      console.log(
        body.substring(0, 150)
      );
      let questionSection = body;

      questionSection = await translateSectionBlocks(
        questionSection,
        '## --text--',
        '^## --answers--\s*|^### --feedback--\s*|^## --text--\s*|^## --video-solution--\s*'
      );

      questionSection = await translateSectionBlocks(
        questionSection,
        '## --answers--',
        '^## --answers--\s*|^### --feedback--\s*|^## --text--\s*|^## --video-solution--\s*'
      );

      questionSection = await translateSectionBlocks(
        questionSection,
        '### --feedback--',
        '^## --text--\s*|^## --video-solution--\s*'
      );

      return `${prefix}${questionSection}`;
    }
  );
}

async function translateLesson(content) {
  console.log('TRANSLATE LESSON START');

  console.log(
    'HAS INTERACTIVE:',
    content.includes('# --interactive--')
  );

  console.log(
    'HAS DESCRIPTION:',
    content.includes('# --description--')
  );

  console.log(
    'HAS QUESTIONS:',
    content.includes('# --questions--')
  );

  content = await translateIntroSection(content);
  content = await translateQuestionSection(content);
  return content;
}

// ======================================
// FILE
// ======================================

async function processFile(file) {
  try {
    console.log(`Processing: ${file}`);

    backupFile(file);

    let content = fs.readFileSync(
      file,
      'utf8'
    );

    if (FORCE_RESTORE_FROM_BAK) {
      const bak = `${file}.bak`;

      if (fs.existsSync(bak)) {
        content = fs.readFileSync(bak, 'utf8');
      }
    }

    const originalContent = content;

    content = await translateTitle(content);
    content = await translateLesson(content);

    if (containsEnglish(content)) {
      console.warn(
        'English content detected after translation'
      );
    }

    const englishSignals = [
      "Let's take a look",
      "Making your",
      "Here are some",
      "Why is",
      "Why are",
      "How can you",
      "What are"
    ];

    for (const signal of englishSignals) {
      if (content.includes(signal)) {
        console.warn(
          `English text still present: ${signal}`
        );
      }
    }

    if (!validate(content)) {
      console.log(`❌ Validation failed: ${file}`);
      return;
    }

    if (content === originalContent) {
      console.log('No changes detected; skipping write');
      skippedFiles++;
      return;
    }

    fs.writeFileSync(file, content, 'utf8');
    translatedFiles++;

    console.log('✓ Done');
  } catch (err) {
    if (err.message === 'Translation appears unchanged') {
      console.warn(`Skipping ${file}: ${err.message}`);
      fs.appendFileSync(
        'failed-translations.txt',
        `${file}\n`,
        'utf8'
      );
      failedFiles++;
      return;
    }

    console.error(
      `❌ Error in ${file}`
    );

    console.error(err.message);
  }
}

// ======================================
// MAIN
// ======================================

async function main() {
  const files = [];

  for (const dir of DIRS) {
    if (!fs.existsSync(dir)) {
      continue;
    }

    files.push(
      ...fs
        .readdirSync(dir)
        .filter(f => f.endsWith('.md'))
        .sort()
        .map(f => path.join(dir, f))
    );
  }

  console.log(
    `Found ${files.length} files`
  );

  for (const file of files) {
    await processFile(file);
  }

  console.log(
    'DEBUG:',
    {
      translatedBlocks,
      retriedBlocks,
      failedBlocks
    }
  );
  console.log(`Translated files: ${translatedFiles}`);
  console.log(`Skipped files: ${skippedFiles}`);
  console.log(`Failed files: ${failedFiles}`);
  console.log(`Translated blocks: ${translatedBlocks}`);
  console.log(`Retried blocks: ${retriedBlocks}`);
  console.log(`Failed blocks: ${failedBlocks}`);
  console.log('\nALL DONE');
}

main().catch(console.error);