import fs from 'fs';
import path from 'path';

const MODEL = 'gemma4:latest';

const DIRS = [
'curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/quiz-asynchronous-javascript'
];

// ======================================
// OLLAMA
// ======================================
async function translateText(text) {
  if (!text || !text.trim()) {
    return text;
  }

  const prompt = `
Translate English to Serbian (sr-RS).

IMPORTANT:

- Translate only natural language.
- Preserve markdown exactly.
- Preserve all line breaks.
- Preserve all blank lines.
- Do not modify formatting.
- Do not translate code.
- Do not translate variable names.
- Do not translate identifiers.
- Do not translate placeholders.

Preserve these markers exactly:

# --description--
# --hints--
# --questions--
# --seed--
# --seed-contents--
# --before-user-code--
# --after-user-code--

Return ONLY translated text.

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
  const required = [
    '# --description--',
    '# --seed--'
  ];

  if (
    !required.every(marker =>
      content.includes(marker)
    )
  ) {
    return false;
  }

  const markers = [
    '# --description--',
    '# --hints--',
    '# --questions--',
    '# --seed--',
    '# --seed-contents--',
    '# --before-user-code--',
    '# --after-user-code--'
  ];

  for (const marker of markers) {
    const escaped = marker.replace(
      /[.*+?^${}()|[\]\\]/g,
      '\\$&'
    );

    if (
      new RegExp(`${escaped}\\S`).test(content)
    ) {
      return false;
    }
  }

  return true;
}

// ======================================
// FCC MARKERS
// ======================================

function protectFCCMarkers(text) {
  const markers = [
    '# --description--',
    '# --hints--',
    '# --questions--',
    '# --seed--',
    '# --seed-contents--',
    '# --before-user-code--',
    '# --after-user-code--'
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
// SAFE TRANSLATE
// ======================================

async function safeTranslate(text) {
  const beforeCodeCount =
    (text.match(/```/g) || []).length;

  const beforeMarkerCount =
    (text.match(
      /# --(description|hints|questions|seed|seed-contents|before-user-code|after-user-code)--/g
    ) || []).length;

  const fccProtected =
    protectFCCMarkers(text);

  const codeProtected =
    protectCodeBlocks(
      fccProtected.text
    );

  const inlineProtected =
    protectInlineCode(
      codeProtected.text
    );

  let translated =
    await translateText(
      inlineProtected.text
    );

  translated =
    restoreInlineCode(
      translated,
      inlineProtected.store
    );

  translated =
    restoreCodeBlocks(
      translated,
      codeProtected.store
    );

  translated =
    restoreFCCMarkers(
      translated,
      fccProtected.markers
    );

  const afterCodeCount =
    (translated.match(/```/g) || []).length;

  const afterMarkerCount =
    (translated.match(
      /# --(description|hints|questions|seed|seed-contents|before-user-code|after-user-code)--/g
    ) || []).length;

  if (
    beforeCodeCount !==
    afterCodeCount
  ) {
    throw new Error(
      'Code block count changed during translation'
    );
  }

  if (
    beforeMarkerCount !==
    afterMarkerCount
  ) {
    throw new Error(
      'FCC marker count changed during translation'
    );
  }

  return translated;
}

// ======================================
// TITLE
// ======================================

async function translateTitle(content) {
  const match =
    content.match(/^title:\s*(.+)$/m);

  if (!match) {
    return content;
  }

  const title = match[1];

  if (
    title.startsWith('Korak') ||
    title.startsWith('Uvod') ||
    title.startsWith('Pregled')
  ) {
    return content;
  }

  const translated =
    await translateText(title);

  return content.replace(
    match[0],
    `title: ${translated}`
  );
}

// ======================================
// DESCRIPTION
// ======================================

async function translateDescription(
  content,
  file
) {
  const regex =
    /# --description--\n*([\s\S]*?)\n*(# --hints--|# --questions--|# --seed--)/;

  const match =
    content.match(regex);

  if (!match) {
    console.log(
      `⚠ Description block not found: ${file}`
    );

    return content;
  }

  const description =
    match[1];

  const endMarker =
    match[2];

  const translated =
    await safeTranslate(
      description
    );

  return content.replace(
    regex,
`# --description--

${translated}

${endMarker}`
  );
}

// ======================================
// FILE
// ======================================

async function processFile(file) {
  try {
    console.log(
      `Processing: ${file}`
    );

    backupFile(file);

    let content =
      fs.readFileSync(
        file,
        'utf8'
      );

    content =
      await translateTitle(
        content
      );

    content =
      await translateDescription(
        content,
        file
      );

    if (!validate(content)) {
      console.log(
        `❌ Validation failed: ${file}`
      );
      return;
    }

    fs.writeFileSync(
      file,
      content
    );

    console.log('✓ Done');
  } catch (err) {
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
        .filter(f =>
          f.endsWith('.md')
        )
        .sort()
        .map(f =>
          path.join(dir, f)
        )
    );
  }

  console.log(
    `Found ${files.length} files`
  );

  for (const file of files) {
    await processFile(file);
  }

  console.log(
    '\nALL DONE'
  );
}

main().catch(console.error);