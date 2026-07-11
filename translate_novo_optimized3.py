#!/usr/bin/env python3
"""
Swahili to Serbian Translation Script for freeCodeCamp Curriculum (OPTIMIZED)

This is a throughput-optimized rewrite of translate_novo.py.

It follows the SAME logic, prompt, protection/restoration tokens, structure
parsing, validation, and output format as the original. The ONLY changes are
to the *execution model* and a couple of correctness fixes that reduce wasted
LLM calls:

  1. Intra-file parallelism: text chunks within a single file are translated
     concurrently with a thread pool (Ollama serves concurrent requests).
     Order is strictly preserved by index, so reconstruction is identical.
  2. Unified file-level parallelism: both the folder path and the `all` path
     use the same configurable ThreadPoolExecutor (the original used
     max_workers=2 for `all` and was fully sequential for a single folder).
  3. Reduced LLM calls per file:
       - The title is translated through the SAME chunk pool rather than as a
         separate serial round-trip.
       - The double retry layer (translate_text's internal 3x retry +
         translate_and_verify's extra 2x) is collapsed into a single coherent
         retry budget, avoiding up to ~9 calls per chunk.
       - has_swahili_text no longer matches ultra-common particles (na, ni, si,
         ya, wa, ...) that also appear in valid Serbian/Spanish text, which in
         the original caused false-positive re-translations.

Quality is identical or better: the prompt and protection are unchanged, and
verification no longer fires on false positives.

Backend: 100% local Ollama (no paid cloud APIs). The model is fully
configuration-driven and never hardcoded at a call site, so you can switch
between qwen3:32b, qwen3-coder:30b, gemma4:latest, or any future Ollama model
via configuration only.

Throughput features:
    - parallel file processing
    - parallel chunk processing (incl. the YAML title)
    - persistent content-hash cache for repeated chunks (skips LLM calls)
    - single coherent retry budget (no nested retry blow-up)
    - false-positive-free Swahili verification (fewer needless retries)

Usage:
    python translate_novo_optimized.py <file.md|folder|all> [--model NAME] [--host URL]

Configuration (CLI flags override env vars; env vars override defaults):
    --model NAME / TRANSLATE_MODEL    ollama model (default gemma4:latest)
    --host URL   / OLLAMA_HOST        ollama endpoint (default http://localhost:11434)
                                      (set this when Ollama runs in Windows and
                                       the script runs in WSL)
    TRANSLATE_FILE_WORKERS            files translated in parallel (default 4)
    TRANSLATE_CHUNK_WORKERS           chunks/file translated in parallel (default 6)
    TRANSLATE_CACHE=0                 disable the persistent chunk cache
    TRANSLATE_CACHE_DIR               cache directory (default .translation_cache)

Examples:
    # Ollama in Windows, script in WSL, using qwen3:32b
    OLLAMA_HOST=http://$(grep nameserver /etc/resolv.conf | awk '{print $2}'):11434 \\
        python translate_novo_optimized.py all --model qwen3:32b
"""

import os
import sys
import json
import urllib.request
import shutil
import time
import re
import threading
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


FOLDERS_TO_TRANSLATE = [
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-aria",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-common-searching-and-sorting-algorithms",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-data-visualization",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-git-and-github",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-javascript",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-javascript-libraries-and-frameworks",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-javascript-objects-and-their-properties",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-npm",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-python",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-python-strings",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-strings",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-introduction-to-typescript",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-numbers-and-mathematical-operations",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-python-installation",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-react-strategies-and-debugging",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-routing-react-frameworks-and-dependency-management-tools",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-searching-and-sorting-algorithms",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-styling-lists-and-links",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-the-var-keyword-and-hoisting",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-abstraction",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-aria-expanded-aria-live-and-common-aria-states",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-asynchronous-programming",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-bash-scripting",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-code-clarity",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-comparisons-and-conditionals",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-computer-internet-and-tooling-basics",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-dynamic-programming",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-dynamic-programming-js",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-effects-and-referencing-values-in-react",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-error-handling",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-error-handling-and-health-checks",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-form-validation",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-functional-programming",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-functions-and-scope",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-graphs-and-trees",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-graphs-and-trees-js",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-how-html-affects-seo",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-how-http-dns-tcpip-work",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-how-to-work-with-classes-in-javascript",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-how-to-work-with-floats-and-positioning-in-css",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-html-attributes",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-inheritance-and-polymorphism",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-modules-imports-and-exports",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-nuanced-semantic-elements",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-object-oriented-programming-and-encapsulation",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-performance-in-web-applications",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-recursion-and-the-call-stack",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-rest-api-and-web-services",
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/lecture-understanding-routing-in-express-js",
]

# Tunable concurrency (overridable via environment variables).
FILE_WORKERS = int(os.environ.get("TRANSLATE_FILE_WORKERS", "10"))
CHUNK_WORKERS = int(os.environ.get("TRANSLATE_CHUNK_WORKERS", "12"))

# Model is fully configuration-driven (NEVER hardcoded at a call site).
# Switch freely between qwen3:32b, qwen3-coder:30b, gemma4:latest, or any
# future Ollama model via the TRANSLATE_MODEL env var or the --model CLI flag.
DEFAULT_MODEL = os.environ.get("TRANSLATE_MODEL", "gemma4:latest")

# Ollama endpoint is configurable. This matters because Ollama may run in
# Windows (PowerShell) while this script runs in WSL: in that case localhost
# does NOT reach the Windows host. Set OLLAMA_HOST to the Windows host, e.g.
#   export OLLAMA_HOST=http://$(grep nameserver /etc/resolv.conf | awk '{print $2}'):11434
# or to your Windows LAN IP. Defaults to localhost for native-Linux Ollama.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"

# Persistent content-hash cache for repeated chunks. The freeCodeCamp
# curriculum contains many identical strings (e.g. repeated feedback lines),
# so caching protected-chunk -> translation avoids redundant LLM calls.
# Reuses the existing .translation_cache/ directory and a compatible JSON shape.
CACHE_DIR = os.environ.get("TRANSLATE_CACHE_DIR", ".translation_cache")
CACHE_ENABLED = os.environ.get("TRANSLATE_CACHE", "1") != "0"
SOURCE_LANG = "swahili"
TARGET_LANG = "serbian"

# Maximum total translation attempts per chunk (single coherent retry budget,
# replacing the original nested 3x + 2x layers).
MAX_CHUNK_ATTEMPTS = 3

# Optional hook for testing/benchmarking: if set to a callable, it is used
# instead of the real Ollama HTTP call. Signature: fn(prompt, model) -> str.
# This lets a benchmark harness inject a mock LLM without touching the network.
LLM_BACKEND = None

# Technical terms that should never be translated
NEVER_TRANSLATE = {
    "JavaScript", "HTML", "CSS", "Node.js", "React", "Git", "GitHub",
    "JSON", "API", "DOM", "Python", "SQL", "MongoDB", "Express",
    "Angular", "Vue", "TypeScript", "Webpack", "Babel", "Docker",
    "Kubernetes", "AWS", "Azure", "GCP", "REST", "GraphQL",
    "HTTP", "HTTPS", "URL", "URI", "SSL", "TLS", "JWT",
    "OAuth", "XML", "YAML", "CSV", "PDF", "PNG", "JPG", "GIF",
    "Array", "Object", "Promise", "fetch", "console", "console.log",
    "Math", "Date", "Map", "Set", "JSON.stringify", "JSON.parse",
    "Boolean", "String", "Number", "Function", "Symbol", "null",
    "undefined", "true", "false", "let", "const", "var", "class",
    "extends", "super", "this", "new", "return", "if", "else",
    "for", "while", "do", "switch", "case", "break", "continue",
    "try", "catch", "finally", "throw", "async", "await", "import",
    "export", "default", "from", "as", "static", "get", "set"
}

# YAML fields that should never be translated
PROTECTED_YAML_FIELDS = {
    'id', 'challengeType', 'dashedName', 'videoId', 'forumTopicId',
    'helpCategory', 'saveSubmissionToDB', 'isRequired'
}


# ======================================
# LOGGING (Thread-safe)
# ======================================

class TranslationLogger:
    def __init__(self, log_file='translation.log'):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.stats = {
            'translated': 0,
            'skipped': 0,
            'failed': 0,
            'restored': 0
        }
        self.init_log()

    def init_log(self):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"Translation Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

    def log(self, file_path, status, message=""):
        with self.lock:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{status}] {file_path}\n")
                if message:
                    f.write(f"  {message}\n")

            if status in self.stats:
                self.stats[status] += 1

    def print_summary(self):
        print("\n" + "=" * 80)
        print("TRANSLATION SUMMARY")
        print("=" * 80)
        for status, count in self.stats.items():
            print(f"  {status.capitalize()}: {count}")
        print("=" * 80)


# Global logger instance
logger = TranslationLogger()


# ======================================
# PERSISTENT CHUNK CACHE (Thread-safe)
# ======================================

class ChunkCache:
    """
    Thread-safe, disk-backed cache mapping a protected chunk (+ model + langs)
    to its translation. Compatible with the existing .translation_cache/ JSON
    layout (source_lang, target_lang, original_text, translated_text,
    timestamp). Each entry is a <sha256>.json file.

    The cache key includes the MODEL so switching models (qwen3:32b,
    qwen3-coder:30b, gemma4:latest, ...) never returns a translation produced
    by a different model.
    """

    def __init__(self, cache_dir=CACHE_DIR, enabled=CACHE_ENABLED):
        self.enabled = enabled
        self.cache_dir = Path(cache_dir)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.writes = 0
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, text, model):
        raw = f"{SOURCE_LANG}:{TARGET_LANG}:{model}:{text}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, text, model):
        if not self.enabled:
            return None
        path = self.cache_dir / f"{self._key(text, model)}.json"
        # Reading is safe without the lock (independent files), but we guard
        # the counters.
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                translated = data.get("translated_text")
                if translated is not None:
                    with self.lock:
                        self.hits += 1
                    return translated
            except Exception:
                pass  # Corrupt/partial entry: treat as a miss.
        with self.lock:
            self.misses += 1
        return None

    def put(self, text, model, translated):
        if not self.enabled:
            return
        path = self.cache_dir / f"{self._key(text, model)}.json"
        payload = {
            "source_lang": SOURCE_LANG,
            "target_lang": TARGET_LANG,
            "model": model,
            "original_text": text,
            "translated_text": translated,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            # Atomic write: write to a unique temp file then rename, so
            # concurrent workers never read a half-written entry.
            tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, path)
            with self.lock:
                self.writes += 1
        except Exception:
            pass  # Caching is best-effort; never fail a translation over it.

    def stats(self):
        with self.lock:
            total = self.hits + self.misses
            rate = (100.0 * self.hits / total) if total else 0.0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "writes": self.writes,
                "hit_rate_pct": round(rate, 1),
            }


# Global cache instance
cache = ChunkCache()


# ======================================
# LANGUAGE DETECTION
# ======================================

def has_swahili_text(text):
    """
    Check if text contains Swahili using characteristic Swahili words.

    Used for post-translation verification. Compared to the original, the
    ultra-common particles (na, ni, si, ya, wa, la, ku, mu, tu, se, ima, bar,
    ...) have been removed because they ALSO appear in valid Serbian and Spanish
    text and caused false-positive re-translations. We keep only words that are
    strongly characteristic of untranslated Swahili, and still require >= 2
    matches.
    """
    swahili_indicators = [
        # Characteristic Swahili content words (low collision with sr/es).
        "mtu", "kazi", "sasa", "hapa", "hapo", "huku", "kule",
        "hadi", "kufika", "kwenda", "kuja", "ruka",
        "hii", "hilo", "hili", "hiyo", "hizi", "hizo", "hawa", "hao",
        "mimi", "wewe", "yeye", "sisi", "ninyi", "wao",
        "sema", "fanya", "enda", "ona", "sikia", "jua",
        "tafuta", "pata", "toa", "weka", "chukua", "peleka",
        "leo", "jana", "kesho", "wakati", "muda",
        "nini", "wapi", "lini", "vipi",
        "hadithi", "mtumiaji", "mradi", "mitihani", "imepitwa",
        "wasilisha", "ukiisha", "ramani", "kichwa",
        "maelezo", "kwamba", "kuhusu", "anauliza", "swali",
        "unaweza", "kutumia", "linamaanisha", "mwenzake", "mfanyakazi",
        "kuandika", "kusikiliza", "sikiliza", "chagua", "jibu",
    ]

    text_lower = text.lower()
    matches = 0

    for word in swahili_indicators:
        # Match whole word only
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matches += 1
            if matches >= 2:  # Require at least 2 matches for verification
                return True

    return False


# ======================================
# TRANSLATION
# ======================================

def is_refusal_message(text):
    """
    Check if text is a refusal/request message that should NOT be translated.
    These are messages where someone asks for Swahili text input.
    Detects in multiple languages (English, Serbian, Swahili).
    """
    if not text or not text.strip():
        return False

    text_lower = text.lower().strip()

    # English patterns
    refusal_patterns = [
        "please provide the swahili text",
        "please provide the text",
        "i need the swahili text",
        "i need the text",
        "provide the text you",
        "provide the swahili text",
        "which text would you like",
        "what text would you like",
        "please specify the text",
        "please enter the text",
        "give me the text to",
        "text to translate",
    ]

    # Serbian patterns (translated refusals)
    serbian_refusal_patterns = [
        "molim vas da mi date tekst",
        "molimo vas da dostavite tekst",
        "molimo vas da pružite tekst",
        "molimo vas da navedete tekst",
        "molim vas, unesite tekst",
        "molimo vas da mi pružite tekst",
        "dostavite tekst na swahili",
        "navedite tekst na swahili",
        "unesite tekst na swahili",
        "da li želite da prevedem",
        "koji želite da prevedem",
        "koji želite da prevedemo",
    ]

    all_patterns = refusal_patterns + serbian_refusal_patterns

    for pattern in all_patterns:
        if pattern in text_lower:
            return True

    # Check if it's very short and asks for text
    if len(text_lower) < 100:
        has_provide = any(word in text_lower for word in ["provide", "give", "enter", "dostavite", "pružite", "navedite", "unesite"])
        has_text = "tekst" in text_lower or "text" in text_lower
        has_translate = "preved" in text_lower or "translate" in text_lower

        if has_provide and has_text and has_translate:
            return True

    return False


def _call_llm(prompt, model):
    """
    Perform a single LLM completion. Uses LLM_BACKEND if injected (for tests),
    otherwise calls the local Ollama HTTP API exactly like the original script.
    Returns the raw response string (stripped) or raises on transport error.
    """
    if LLM_BACKEND is not None:
        return (LLM_BACKEND(prompt, model) or "").strip()

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096
        }
    }

    req = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=300) as response:
        result = json.loads(response.read().decode('utf-8'))

    return result.get('response', '').strip()


def _build_prompt(text):
    """Build the translation prompt (identical wording to the original)."""
    return f"""Translate this Swahili text to Serbian (sr-RS).

RULES:
1. Translate ONLY natural language text
2. Do NOT translate: code, URLs, API names, programming keywords, technical terms
3. Keep the same formatting and structure
4. Use natural Serbian technical terminology
5. Provide ONLY the translation, no explanations

TEXT:

{text}"""


def translate_text(text, model=DEFAULT_MODEL):
    """
    Translate text using the LLM.

    This collapses the original two-layer retry scheme (translate_text's 3x +
    translate_and_verify's 2x, up to ~9 calls) into a SINGLE coherent retry
    budget of MAX_CHUNK_ATTEMPTS. Each attempt validates:
      - not a refusal message
      - non-empty
      - protection tokens (@@) count preserved
      - no characteristic Swahili left (post-translation verification)
    On exhausting attempts, the original text is returned unchanged (same
    fallback behavior as the original).
    """
    if not text or not text.strip():
        return text

    # Original text is itself a refusal message -> skip (same as original).
    if is_refusal_message(text):
        logger.log("chunk", 'skipped', 'Original text is a refusal message, skipping')
        return text

    # Cache lookup: identical protected chunks (very common in the curriculum)
    # are served from disk without an LLM call. Keyed by model so switching
    # models never returns another model's output.
    cached = cache.get(text, model)
    if cached is not None:
        return cached

    prompt = _build_prompt(text)
    expected_tokens = text.count("@@")

    for attempt in range(MAX_CHUNK_ATTEMPTS):
        try:
            translated = _call_llm(prompt, model)

            # Reject refusal messages returned by the LLM.
            if is_refusal_message(translated):
                if attempt < MAX_CHUNK_ATTEMPTS - 1:
                    time.sleep(1)
                    continue
                logger.log("chunk", 'skipped', 'LLM returned refusal message after retries')
                return text

            # Validate: non-empty and protection tokens preserved.
            tokens_ok = (
                translated
                and translated.strip() != ""
                and translated.count("@@") == expected_tokens
            )
            if not tokens_ok:
                if attempt < MAX_CHUNK_ATTEMPTS - 1:
                    time.sleep(1)
                    continue
                return text

            # Verification: characteristic Swahili should not remain.
            if has_swahili_text(translated):
                if attempt < MAX_CHUNK_ATTEMPTS - 1:
                    print(f"    ⚠ Swahili text detected, retrying ({attempt + 1}/{MAX_CHUNK_ATTEMPTS})...")
                    time.sleep(1)
                    continue
                # Out of attempts: return best effort (token-valid) translation.
                # Not cached: verification failed, so we don't persist it.
                return translated

            # Successful, verified translation -> cache it for reuse.
            cache.put(text, model, translated)
            return translated

        except Exception as e:
            if attempt < MAX_CHUNK_ATTEMPTS - 1:
                time.sleep(1)
            else:
                print(f"    ✗ Error: {e}")
                return text

    return text


# ======================================
# PROTECTION SYSTEM (Deterministic tokens)
# ======================================

def generate_token(prefix, index, original_text):
    """Generate deterministic token based on content hash."""
    hash_input = f"{prefix}:{index}:{original_text}".encode('utf-8')
    hash_hex = hashlib.sha256(hash_input).hexdigest()[:8].upper()
    return f"@@{prefix}_{hash_hex}_{index:04d}@@"


def protect_code_blocks(text):
    """Replace code blocks with tokens."""
    store = []
    pattern = r'```[\s\S]*?```'

    def replace(match):
        token = generate_token("CODE_BLOCK", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_code_blocks(text, store):
    """Restore code blocks from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_inline_code(text):
    """Replace inline code with tokens."""
    store = []
    pattern = r'`[^`\n]+`'

    def replace(match):
        token = generate_token("INLINE_CODE", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_inline_code(text, store):
    """Restore inline code from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_html_tags(text):
    """Replace HTML tags with tokens."""
    store = []
    pattern = r'</?[A-Za-z][^>]*>'

    def replace(match):
        token = generate_token("HTML_TAG", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_html_tags(text, store):
    """Restore HTML tags from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_html_entities(text):
    """Replace HTML entities with tokens."""
    store = []
    pattern = r'&[a-zA-Z]+;|&[0-9]+;|&#[0-9]+;'

    def replace(match):
        token = generate_token("HTML_ENTITY", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_html_entities(text, store):
    """Restore HTML entities from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_markdown_links(text):
    """Replace Markdown links with tokens."""
    store = []
    pattern = r'\[[^\]]+\]\([^)]+\)'

    def replace(match):
        token = generate_token("MD_LINK", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_markdown_links(text, store):
    """Restore Markdown links from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_markdown_images(text):
    """Replace Markdown images with tokens."""
    store = []
    pattern = r'!\[([^\]]*)\]\([^\)]+\)'

    def replace(match):
        token = generate_token("MD_IMAGE", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    protected = re.sub(pattern, replace, text)
    return protected, store


def restore_markdown_images(text, store):
    """Restore Markdown images from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_reference_links(text):
    """Replace reference links with tokens."""
    store = []

    pattern1 = r'\[([^\]]+)\]\[([^\]]+)\]'
    pattern2 = r'^\[([^\]]+)\]:\s*.+$'

    def replace1(match):
        token = generate_token("REF_LINK", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    def replace2(match):
        token = generate_token("REF_DEF", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    text = re.sub(pattern1, replace1, text, flags=re.MULTILINE)
    text = re.sub(pattern2, replace2, text, flags=re.MULTILINE)

    return text, store


def restore_reference_links(text, store):
    """Restore reference links from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_references(text):
    """Replace template references with tokens."""
    store = []

    pattern1 = r'\{\{[^}]+\}\}'
    pattern2 = r'\$\{[^}]+\}'
    pattern3 = r'%\{[^}]+\}'

    def replace(match):
        token = generate_token("REF", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    text = re.sub(pattern1, replace, text)
    text = re.sub(pattern2, replace, text)
    text = re.sub(pattern3, replace, text)

    return text, store


def restore_references(text, store):
    """Restore references from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_placeholders(text):
    """Replace format placeholders with tokens."""
    store = []

    pattern1 = r'%[sdifFeEgGxXo]'
    pattern2 = r'(?<!\{)\{[^{}]+\}(?!\})'
    pattern3 = r'\{\{[^}]+\}\}'
    pattern4 = r'\$\d+'

    def replace(match):
        token = generate_token("PLACEHOLDER", len(store), match.group(0))
        store.append((token, match.group(0)))
        return token

    text = re.sub(pattern1, replace, text)
    text = re.sub(pattern3, replace, text)
    text = re.sub(pattern2, replace, text)
    text = re.sub(pattern4, replace, text)

    return text, store


def restore_placeholders(text, store):
    """Restore placeholders from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_technical_terms(text):
    """Replace technical terms with tokens."""
    store = []

    for term in sorted(NEVER_TRANSLATE, key=len, reverse=True):
        pattern = r'\b' + re.escape(term) + r'\b'

        def replace(match, term=term):
            token = generate_token("TECH_TERM", len(store), match.group(0))
            store.append((token, match.group(0)))
            return token

        text = re.sub(pattern, replace, text)

    return text, store


def restore_technical_terms(text, store):
    """Restore technical terms from tokens."""
    result = text
    for token, original in store:
        result = result.replace(token, original)
    return result


def protect_all(text):
    """Apply all protections in correct order."""
    text, code_blocks = protect_code_blocks(text)
    text, inline_codes = protect_inline_code(text)
    text, html_tags = protect_html_tags(text)
    text, html_entities = protect_html_entities(text)
    text, md_images = protect_markdown_images(text)
    text, md_links = protect_markdown_links(text)
    text, ref_links = protect_reference_links(text)
    text, refs = protect_references(text)
    text, placeholders = protect_placeholders(text)
    text, tech_terms = protect_technical_terms(text)

    return text, {
        'code_blocks': code_blocks,
        'inline_codes': inline_codes,
        'html_tags': html_tags,
        'html_entities': html_entities,
        'md_images': md_images,
        'md_links': md_links,
        'ref_links': ref_links,
        'refs': refs,
        'placeholders': placeholders,
        'tech_terms': tech_terms
    }


def restore_all(text, stores):
    """Restore all protected elements in reverse order."""
    text = restore_technical_terms(text, stores['tech_terms'])
    text = restore_placeholders(text, stores['placeholders'])
    text = restore_references(text, stores['refs'])
    text = restore_reference_links(text, stores['ref_links'])
    text = restore_markdown_links(text, stores['md_links'])
    text = restore_markdown_images(text, stores['md_images'])
    text = restore_html_entities(text, stores['html_entities'])
    text = restore_html_tags(text, stores['html_tags'])
    text = restore_inline_code(text, stores['inline_codes'])
    text = restore_code_blocks(text, stores['code_blocks'])
    return text


def verify_tokens_intact(text, stores):
    """Verify all tokens are still present after translation (before restore)."""
    all_ok = True
    missing = []

    for category, store in stores.items():
        for token, original in store:
            if token not in text:
                all_ok = False
                missing.append(token)

    return all_ok, missing


# ======================================
# FILE PROCESSING
# ======================================

def split_into_chunks(text, max_chunk_size=1000, max_lines=50):
    """Split text into translatable chunks."""
    chunks = []

    parts = re.split(r'(```[\s\S]*?```)', text)

    for part in parts:
        if part.startswith('```'):
            chunks.append(('code', part))
        else:
            paragraphs = re.split(r'(\n\n)', part)

            current_text = []
            current_lines = 0

            for para in paragraphs:
                if para == '\n\n':
                    if current_text:
                        text_block = ''.join(current_text)
                        chunks.append(('text', text_block))
                        current_text = []
                        current_lines = 0
                    chunks.append(('newline', para))
                elif para.strip():
                    para_lines = para.count('\n') + 1

                    if current_text and (current_lines + para_lines > max_lines or
                                        len(''.join(current_text)) + len(para) > max_chunk_size):
                        text_block = ''.join(current_text)
                        chunks.append(('text', text_block))
                        current_text = []
                        current_lines = 0

                    current_text.append(para)
                    current_lines += para_lines
                else:
                    if current_text:
                        text_block = ''.join(current_text)
                        chunks.append(('text', text_block))
                        current_text = []
                        current_lines = 0
                    chunks.append(('empty', para))

            if current_text:
                text_block = ''.join(current_text)
                chunks.append(('text', text_block))

    return chunks


def _translate_one_text_chunk(chunk, model):
    """
    Translate a single 'text' chunk: protect -> translate -> verify tokens ->
    restore. Returns the final chunk string. Identical semantics to the
    original translate_chunks body for a single text chunk; this is the unit
    we now run in parallel.
    """
    protected_text, stores = protect_all(chunk)
    translated = translate_text(protected_text, model)

    tokens_ok, missing = verify_tokens_intact(translated, stores)
    if not tokens_ok:
        print(f"    ⚠ Warning: {len(missing)} tokens damaged, keeping original chunk")
        return chunk

    return restore_all(translated, stores)


def translate_chunks(chunks, model=DEFAULT_MODEL, executor=None):
    """
    Translate a list of chunks, preserving order.

    Non-text chunks (code/newline/empty) pass through untouched. All 'text'
    chunks are submitted to a thread pool and translated concurrently; results
    are reassembled by index so the output order is identical to the input.
    """
    translated_chunks = [None] * len(chunks)
    text_indices = []

    for i, (chunk_type, chunk) in enumerate(chunks):
        if chunk_type in ('code', 'newline', 'empty'):
            translated_chunks[i] = (chunk_type, chunk)
        else:
            text_indices.append(i)

    if not text_indices:
        return translated_chunks

    own_executor = None
    if executor is None:
        own_executor = ThreadPoolExecutor(max_workers=CHUNK_WORKERS)
        executor = own_executor

    try:
        future_to_index = {
            executor.submit(_translate_one_text_chunk, chunks[i][1], model): i
            for i in text_indices
        }
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            try:
                translated_chunks[i] = ('text', future.result())
            except Exception as e:
                print(f"    ✗ Chunk error, keeping original: {e}")
                translated_chunks[i] = ('text', chunks[i][1])
    finally:
        if own_executor is not None:
            own_executor.shutdown(wait=True)

    return translated_chunks


def parse_file_structure(content):
    """
    Parse file into ordered list of (type, ...) tuples.
    Types: 'yaml', 'marker', 'content'
    Preserves exact content including all whitespace using string slicing.
    """
    structure = []

    # Extract YAML frontmatter with exact content
    yaml_match = re.match(r'^(---\n.*?\n---\n)', content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
        structure.append(('yaml', yaml_content))
        remaining = content[yaml_match.end():]
    else:
        remaining = content

    # Find all section markers with positions using regex.
    # Capture the marker AND any trailing whitespace (newlines, spaces).
    marker_pattern = r'^(\#{1,6}\s*--[a-z-]+--\s*)(\n*)'

    last_end = 0
    for match in re.finditer(marker_pattern, remaining, re.MULTILINE):
        # Content before this marker (preserve exactly)
        if match.start() > last_end:
            content_text = remaining[last_end:match.start()]
            if content_text:
                structure.append(('content', content_text))
        # The marker itself with its trailing newlines
        marker_text = match.group(1)
        trailing_newlines = match.group(2)
        structure.append(('marker', marker_text, trailing_newlines))
        last_end = match.end()

    # Remaining content after last marker
    if last_end < len(remaining):
        content_text = remaining[last_end:]
        if content_text:
            structure.append(('content', content_text))
    elif last_end == 0:
        # No markers found, entire remaining is content
        structure.append(('content', remaining))

    return structure


def reconstruct_file(structure):
    """Reconstruct file from structure list, preserving exact formatting."""
    result = []
    for item in structure:
        if item[0] == 'marker':
            # Marker tuple: ('marker', marker_text, trailing_newlines)
            marker_text, trailing_newlines = item[1], item[2]
            result.append(marker_text)
            result.append(trailing_newlines)
        else:
            # YAML and content: ('yaml', content) or ('content', content)
            result.append(item[1])
    return ''.join(result)


def validate_translation(original_content, translated_content, original_structure, translated_structure):
    """Validate that translation preserved structure exactly."""
    errors = []

    if len(original_structure) != len(translated_structure):
        errors.append(f"Structure length mismatch: {len(original_structure)} vs {len(translated_structure)}")
        return errors

    for i, (orig_item, trans_item) in enumerate(zip(original_structure, translated_structure)):
        orig_type = orig_item[0]
        trans_type = trans_item[0]

        if orig_type != trans_type:
            errors.append(f"Part {i}: type mismatch {orig_type} vs {trans_type}")

        if orig_type == 'yaml':
            orig_content = orig_item[1]
            trans_content = trans_item[1]
            orig_lines = orig_content.split('\n')
            trans_lines = trans_content.split('\n')

            for j, (orig_line, trans_line) in enumerate(zip(orig_lines, trans_lines)):
                if orig_line.startswith('title:'):
                    continue
                elif orig_line.strip() in ('---', '...'):
                    if orig_line != trans_line:
                        errors.append(f"YAML delimiter changed at line {j}: {orig_line}")
                elif any(orig_line.startswith(f'{field}:') for field in PROTECTED_YAML_FIELDS):
                    if orig_line != trans_line:
                        errors.append(f"Protected YAML field changed at line {j}: {orig_line}")
                elif orig_line != trans_line:
                    errors.append(f"YAML line {j} changed: {orig_line}")

        elif orig_type == 'marker':
            # Marker tuple: ('marker', marker_text, trailing_newlines)
            orig_marker_text = orig_item[1]
            orig_trailing = orig_item[2]
            trans_marker_text = trans_item[1]
            trans_trailing = trans_item[2]

            if orig_marker_text != trans_marker_text:
                errors.append(f"Marker {i} text changed: {orig_marker_text} vs {trans_marker_text}")
            if orig_trailing != trans_trailing:
                errors.append(f"Marker {i} trailing whitespace changed: {repr(orig_trailing)} vs {repr(trans_trailing)}")

    # Check for corrupted marker patterns (marker directly followed by text without newline)
    corruption_patterns = [
        r'# --description--[^\n]',
        r'#### --text--[^\n]',
        r'#### --distractors--[^\n]',
        r'#### --answer--[^\n]',
    ]

    for pattern in corruption_patterns:
        matches = re.findall(pattern, translated_content)
        if matches:
            errors.append(f"Corrupted marker pattern detected: {pattern} - found {len(matches)} occurrences")

    return errors


def _build_title_job(yaml_content, model):
    """
    Prepare a YAML part for translation. Returns (needs_title, prefix,
    title_text, lines, title_line_index). The actual LLM call for the title is
    issued through the shared chunk pool so it overlaps with body chunks.
    """
    lines = yaml_content.split('\n')
    for idx, line in enumerate(lines):
        if line.startswith('title:'):
            match = re.match(r'^(title:\s*)(.+)$', line)
            if match:
                return True, match.group(1), match.group(2), lines, idx
            break
    return False, None, None, lines, -1


def translate_file(file_path, model=DEFAULT_MODEL):
    """
    Translate a markdown file with ultra-safe chunk-based translation.

    Optimized: the title and ALL body text chunks across all content sections
    are translated concurrently through a single per-file thread pool, instead
    of section-by-section and chunk-by-chunk serial calls. Order is preserved
    exactly, so the reconstructed output is identical in format to the original
    pipeline.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    original_structure = parse_file_structure(original_content)

    if not original_structure:
        logger.log(file_path, 'skipped', 'Could not parse structure')
        print(f"  ⚠ Could not parse structure: {file_path}")
        return False

    yaml_count = sum(1 for item in original_structure if item[0] == 'yaml')
    marker_count = sum(1 for item in original_structure if item[0] == 'marker')

    print(f"  Found {len(original_structure)} parts: {yaml_count} YAML, {marker_count} markers, {len(original_structure) - yaml_count - marker_count} content sections")

    # We build the translated structure in two passes:
    #  1) Split every content section into chunks and collect all text chunks +
    #     the title job, submitting them to a shared per-file pool.
    #  2) Reassemble in order once all futures complete.
    translated_structure = [None] * len(original_structure)

    # Plan for content sections: store the chunk list per index.
    content_chunks = {}  # index -> list[(type, chunk)]
    # Plan for the title: (yaml_index, prefix, lines, title_line_index)
    title_plan = None

    with ThreadPoolExecutor(max_workers=CHUNK_WORKERS) as pool:
        # Futures we need to await, with metadata describing where the result goes.
        title_future = None

        for i, item in enumerate(original_structure):
            part_type = item[0]

            if part_type == 'yaml':
                yaml_content = item[1]
                needs_title, prefix, title_text, lines, title_idx = _build_title_job(yaml_content, model)
                if needs_title:
                    title_plan = (i, prefix, lines, title_idx)
                    title_future = pool.submit(translate_text, title_text, model)
                else:
                    translated_structure[i] = ('yaml', yaml_content)

            elif part_type == 'marker':
                # Preserve marker with its trailing newlines.
                translated_structure[i] = item

            elif part_type == 'content':
                chunks = split_into_chunks(item[1])
                content_chunks[i] = chunks

        # Submit all body text chunks concurrently, keyed by (section_index, chunk_index).
        chunk_futures = {}
        for sec_idx, chunks in content_chunks.items():
            for c_idx, (chunk_type, chunk) in enumerate(chunks):
                if chunk_type not in ('code', 'newline', 'empty'):
                    fut = pool.submit(_translate_one_text_chunk, chunk, model)
                    chunk_futures[(sec_idx, c_idx)] = fut

        # Collect title result.
        if title_plan is not None and title_future is not None:
            yaml_i, prefix, lines, title_idx = title_plan
            try:
                translated_title = title_future.result()
            except Exception as e:
                print(f"    ✗ Title error, keeping original: {e}")
                translated_title = lines[title_idx][len(prefix):]
            lines[title_idx] = f"{prefix}{translated_title}"
            translated_structure[yaml_i] = ('yaml', '\n'.join(lines))
            print(f"    ✓ Translated YAML title")

        # Collect body chunk results and rebuild each content section.
        chunk_results = {}
        for key, fut in chunk_futures.items():
            try:
                chunk_results[key] = fut.result()
            except Exception as e:
                sec_idx, c_idx = key
                print(f"    ✗ Chunk error, keeping original: {e}")
                chunk_results[key] = content_chunks[sec_idx][c_idx][1]

        for sec_idx, chunks in content_chunks.items():
            rebuilt = []
            translated_count = 0
            for c_idx, (chunk_type, chunk) in enumerate(chunks):
                if (sec_idx, c_idx) in chunk_results:
                    new_chunk = chunk_results[(sec_idx, c_idx)]
                    if new_chunk != chunk:
                        translated_count += 1
                    rebuilt.append(new_chunk)
                else:
                    rebuilt.append(chunk)
            translated_structure[sec_idx] = ('content', ''.join(rebuilt))
            if translated_count > 0:
                print(f"    ✓ Translated {translated_count} text chunk(s) in section")

    translated_content = reconstruct_file(translated_structure)

    errors = validate_translation(original_content, translated_content, original_structure, translated_structure)

    if errors:
        logger.log(file_path, 'restored', '; '.join(errors[:3]))
        print(f"  ✗ Validation failed:")
        for error in errors[:5]:
            print(f"    - {error}")
        print(f"  ↳ Restoring from backup")
        backup_path = file_path + '.bak'
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"  ✓ Restored from backup")
        else:
            print(f"  ⚠ No backup found to restore")
        return False

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(translated_content)

    logger.log(file_path, 'translated')
    return True


def translate_single_file(file_path, model=DEFAULT_MODEL):
    """Wrapper for parallel processing."""
    try:
        backup_path = file_path + '.bak'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)

        return translate_file(file_path, model)
    except Exception as e:
        logger.log(file_path, 'failed', str(e))
        print(f"✗ Error translating {file_path}: {e}")
        return False


def _translate_files_parallel(md_files, model, max_workers):
    """Translate a list of files in parallel, returning (success, failed)."""
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(translate_single_file, str(md_file), model): md_file
            for md_file in md_files
        }
        for future in as_completed(futures):
            md_file = futures[future]
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.log(str(md_file), 'failed', str(e))
                print(f"  ✗ Error translating {md_file}: {e}")
                fail_count += 1

    return success_count, fail_count


def _parse_cli_args(argv):
    """
    Parse positional target plus optional --model/--host flags. Applies --host
    globally (rebuilds the Ollama URL) and returns (target, model).
    Model resolution order: --model flag > TRANSLATE_MODEL env > default.
    """
    global OLLAMA_HOST, OLLAMA_GENERATE_URL

    target = None
    model = DEFAULT_MODEL
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--model", "-m") and i + 1 < len(argv):
            model = argv[i + 1]
            i += 2
        elif arg.startswith("--model="):
            model = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--host", "-H") and i + 1 < len(argv):
            OLLAMA_HOST = argv[i + 1].rstrip("/")
            OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"
            i += 2
        elif arg.startswith("--host="):
            OLLAMA_HOST = arg.split("=", 1)[1].rstrip("/")
            OLLAMA_GENERATE_URL = f"{OLLAMA_HOST}/api/generate"
            i += 1
        elif target is None:
            target = arg
            i += 1
        else:
            i += 1
    return target, model


def _print_cache_stats(model):
    """Print cache + config info after a run."""
    s = cache.stats()
    print("\n" + "-" * 60)
    print(f"Model: {model}  |  Ollama: {OLLAMA_HOST}")
    print(f"Cache: {s['hits']} hits, {s['misses']} misses, "
          f"{s['writes']} writes ({s['hit_rate_pct']}% hit rate)")
    print("-" * 60)


def main(target=None, model=None):
    if target is None or model is None:
        target, model = _parse_cli_args(sys.argv[1:])
    if target is None:
        print("Usage: python translate_novo_optimized.py <file.md|folder|all> [--model NAME] [--host URL]")
        sys.exit(1)

    if os.path.isfile(target):
        if not target.endswith('.md') or target.endswith('.bak'):
            print("Error: Please provide a .md file (not .bak)")
            sys.exit(1)

        backup_path = target + '.bak'
        if not os.path.exists(backup_path):
            print(f"Creating backup: {backup_path}")
            shutil.copy2(target, backup_path)

        success = translate_file(target, model)
        _print_cache_stats(model)
        sys.exit(0 if success else 1)

    elif os.path.isdir(target):
        md_files = sorted([f for f in Path(target).glob('*.md') if not f.name.endswith('.bak')])

        if not md_files:
            print(f"No .md files found in {target}")
            sys.exit(1)

        print(f"Found {len(md_files)} files to translate")
        print(f"Model: {model} | Ollama: {OLLAMA_HOST}")
        print(f"File workers: {FILE_WORKERS}, Chunk workers: {CHUNK_WORKERS}")
        print("-" * 60)

        success_count, fail_count = _translate_files_parallel(md_files, model, FILE_WORKERS)

        print("-" * 60)
        print(f"Translation complete! Success: {success_count}, Failed: {fail_count}")
        _print_cache_stats(model)
        logger.print_summary()

    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)


def translate_all_folders(model=DEFAULT_MODEL):
    """Translate all folders in FOLDERS_TO_TRANSLATE with parallel processing."""
    print(f"Found {len(FOLDERS_TO_TRANSLATE)} folders to translate")
    print(f"Model: {model} | Ollama: {OLLAMA_HOST}")
    print(f"File workers: {FILE_WORKERS}, Chunk workers: {CHUNK_WORKERS}")
    print("=" * 60)

    total_success = 0
    total_failed = 0

    for folder in FOLDERS_TO_TRANSLATE:
        folder_path = Path(folder)
        if not folder_path.exists():
            logger.log(folder, 'skipped', 'Folder not found')
            print(f"\n⚠ Folder not found: {folder}")
            continue

        md_files = sorted([f for f in folder_path.glob('*.md') if not f.name.endswith('.bak')])

        if not md_files:
            logger.log(folder, 'skipped', 'No .md files')
            print(f"\n⚠ No .md files found in: {folder}")
            continue

        print(f"\n📁 Translating: {folder}")
        print(f"   Files: {len(md_files)}")
        print("-" * 60)

        folder_success, folder_failed = _translate_files_parallel(md_files, model, FILE_WORKERS)
        total_success += folder_success
        total_failed += folder_failed

        logger.log(folder, 'translated', f'{folder_success} success, {folder_failed} failed')
        print(f"\n  ✓ Folder complete: {folder_success} success, {folder_failed} failed")

    print("\n" + "=" * 60)
    print(f"TRANSLATION COMPLETE!")
    print(f"  Total success: {total_success}")
    print(f"  Total failed: {total_failed}")
    _print_cache_stats(model)
    logger.print_summary()


if __name__ == "__main__":
    # Parse once so flags may appear in any order (e.g. `--model X all`).
    _target, _model = _parse_cli_args(sys.argv[1:])
    if _target == "all":
        translate_all_folders(_model)
    else:
        main(_target, _model)
