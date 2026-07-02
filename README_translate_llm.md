# Advanced LLM-based Markdown Translator (`translate_llm.py`)

## Overview

`translate_llm.py` is an advanced Markdown translation script inspired by [md-translator](https://github.com/rockbenben/md-translator). It provides a robust, production-ready solution for translating Markdown files using local LLM models (via Ollama/LM Studio).

## Key Features

### 1. **Batch Translation with Context Awareness**
- Translates files in batches while maintaining context between chunks
- Context window keeps track of recent translations for consistency
- Ensures terminology consistency across the entire document

### 2. **Concurrent Processing**
- Uses `ThreadPoolExecutor` for parallel file translation
- Configurable worker count (default: 2)
- Thread-safe operations with proper locking

### 3. **Caching System**
- Hash-based caching to avoid redundant API calls
- Persistent cache stored in `.translation_cache/` directory
- Significantly speeds up re-runs and large batches
- Cache statistics reporting

### 4. **Glossary Support**
- JSON-based glossary for custom term translations
- Automatic application of glossary terms during translation
- Ensures consistent translation of technical terms
- Example: `glossary.json`

### 5. **Retry Logic with Exponential Backoff**
- Automatic retries on API failures (default: 3 attempts)
- Exponential backoff: 1s, 2s, 4s delays
- Graceful degradation on persistent failures

### 6. **Timeout Handling**
- Configurable timeout for API calls (default: 300s)
- Prevents hanging on slow responses

### 7. **Progress Reporting**
- Real-time progress bar with percentage
- Shows elapsed time, remaining time, and processing rate
- Clean, user-friendly output

### 8. **Cancellation Support**
- Press `Ctrl+C` to gracefully cancel translation
- Finishes current chunk before stopping
- No corrupted files or partial writes

### 9. **Prompt Management**
- Separate prompt templates for translation
- Context-aware prompts that include previous chunks
- System prompts for consistent LLM behavior

### 10. **Markdown Structure Preservation**
- Parses and preserves YAML frontmatter
- Protects code blocks, inline code, and technical terms
- Maintains exact file structure and formatting

## Architecture

```
translate_llm.py
├── TranslationConfig (dataclass)
│   └── Configuration parameters
├── TranslationResult (dataclass)
│   └── Translation result tracking
├── CacheManager
│   ├── get() - Retrieve cached translation
│   ├── set() - Store translation in cache
│   ├── clear() - Clear all cache
│   └── get_stats() - Cache statistics
├── GlossaryManager
│   ├── load() / save() - JSON glossary
│   ├── get() - Lookup term
│   ├── add() - Add new term
│   └── apply() - Apply glossary to text
├── PromptTemplate
│   ├── get_translation_prompt() - Main prompt
│   └── get_system_prompt() - System prompt
├── LLMClient
│   ├── translate() - Main translation method
│   └── _call_api() - API interaction
├── MarkdownChunker
│   ├── chunk() - Split text into chunks
│   └── _chunk_text() - Chunk non-code text
├── ProgressTracker
│   ├── update() - Update progress
│   ├── get_progress() - Get statistics
│   └── print_progress() - Display progress bar
├── TranslationEngine
│   ├── translate_file() - Translate single file
│   ├── _translate_yaml() - Translate YAML title
│   ├── _translate_content() - Translate content
│   └── _parse_structure() - Parse Markdown
└── BatchTranslator
    ├── translate_files() - Batch translation
    └── get_statistics() - Get stats
```

## Installation

No additional dependencies required beyond Python 3.7+ standard library.

```bash
# Ensure you have Python 3.7+
python --version

# Make the script executable (optional)
chmod +x translate_llm.py
```

## Configuration

### Basic Configuration

Edit the `TranslationConfig` dataclass in the script or use CLI arguments:

```python
config = TranslationConfig(
    source_lang="swahili",        # Source language
    target_lang="serbian",        # Target language
    model="gemma4:latest",        # LLM model
    api_url="http://localhost:11434/api/generate",  # Ollama API
    max_workers=2,                # Parallel workers
    max_retries=3,                # Retry attempts
    timeout=300,                  # API timeout (seconds)
    temperature=0.3,              # LLM temperature
    max_chunk_size=1000,          # Max chunk size (chars)
    max_lines=50,                 # Max lines per chunk
    cache_enabled=True,           # Enable caching
    cache_dir=".translation_cache",  # Cache directory
    glossary_file="glossary.json"    # Glossary file
)
```

### Glossary Configuration

Create a `glossary.json` file to define custom translations:

```json
{
  "display": "display",
  "flex": "flex",
  "flexbox": "flexbox",
  "container": "container",
  "assert": "assert",
  "const": "const"
}
```

The glossary ensures technical terms are translated consistently.

## Usage

### Command Line Interface

```bash
# Translate a single file
python translate_llm.py path/to/file.md

# Translate a directory
python translate_llm.py path/to/directory/

# Use specific model
python translate_llm.py path/to/directory/ --model llama3:latest

# Specify languages
python translate_llm.py path/to/directory/ --source-lang swahili --target-lang serbian

# Use custom glossary
python translate_llm.py path/to/directory/ --glossary my_glossary.json

# Disable caching
python translate_llm.py path/to/directory/ --no-cache

# Clear cache
python translate_llm.py path/to/directory/ --clear-cache

# Use more workers (be careful with API rate limits)
python translate_llm.py path/to/directory/ --workers 4
```

### Python API

```python
from translate_llm import translate_file, translate_directory, TranslationConfig

# Configure
config = TranslationConfig(
    source_lang="swahili",
    target_lang="serbian",
    model="gemma4:latest"
)

# Translate single file
result = translate_file("path/to/file.md", config)
print(f"Status: {result.status}")
print(f"Chunks translated: {result.chunks_translated}")
print(f"Duration: {result.duration:.2f}s")

# Translate directory
results = translate_directory("path/to/directory/", config)
for result in results:
    print(f"{result.file_path}: {result.status}")
```

## Model Recommendation

### Current: Gemma 4 Latest
- **Pros**: Good general-purpose model, fast inference
- **Cons**: May not be optimized for translation tasks
- **Use case**: General translation, good balance of speed and quality

### Recommended for Translation: Specialized Models

For better translation quality, consider these models:

1. **Llama 3 70B** (if you have enough RAM/VRAM)
   - Excellent multilingual capabilities
   - Better context understanding
   - More natural translations

2. **Mistral Large**
   - Strong multilingual performance
   - Good for technical content
   - Faster than Llama 3 70B

3. **Qwen2.5 72B**
   - Excellent for multilingual tasks
   - Strong technical documentation translation
   - Good balance of speed and quality

4. **Custom fine-tuned translation models**
   - Check HuggingFace for models fine-tuned on Swahili-English or Swahili-Serbian pairs
   - Example: `Helsinki-NLP/opus-mt-sw-en` (Swahili to English)
   - You can chain translations: Swahili → English → Serbian

### Installation

```bash
# Install recommended model (example with Llama 3)
ollama pull llama3:70b

# Or use Qwen2.5
ollama pull qwen2.5:72b

# Update script to use new model
python translate_llm.py directory/ --model llama3:70b
```

## Workflow

1. **Initial Translation**
   ```bash
   python translate_llm.py curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/css-flexbox
   ```

2. **Review Translations**
   - Check a few files manually
   - Verify technical terms are preserved
   - Ensure code blocks are intact

3. **Refine Glossary**
   - Add terms that need consistent translation
   - Re-run with updated glossary

4. **Re-translate with Cache**
   ```bash
   # Cache will skip already translated chunks
   python translate_llm.py curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/css-flexbox
   ```

5. **Clear Cache if Needed**
   ```bash
   python translate_llm.py directory/ --clear-cache
   ```

## Output

### Console Output

```
Found 17 files to translate
============================================================

███████████████████████████████████████████████████ 100.0% (17/17) [45.2s elapsed, 0.0s remaining]

============================================================
TRANSLATION SUMMARY
============================================================
Files processed: 17
Completed: 17
Failed: 0
Total chunks translated: 234
Total chunks cached: 0
Total duration: 45.23s

Cache statistics:
  Entries: 234
============================================================
```

### Cache Structure

```
.translation_cache/
├── a1b2c3d4...e5f6.json
├── b2c3d4e5...f6a7.json
└── ...
```

Each cache file contains:
```json
{
  "source_lang": "swahili",
  "target_lang": "serbian",
  "original_text": "...",
  "translated_text": "...",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Comparison with `translate_novo.py`

| Feature | translate_novo.py | translate_llm.py |
|---------|-------------------|------------------|
| Caching | ❌ | ✅ |
| Glossary | ❌ | ✅ |
| Context-aware | ❌ | ✅ |
| Progress bar | ❌ | ✅ |
| Cancellation | ❌ | ✅ |
| Retry logic | Basic | Exponential backoff |
| Batch processing | Sequential | Concurrent |
| Statistics | Basic | Detailed |
| Prompt management | Hardcoded | Template-based |

## Troubleshooting

### API Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Out of Memory
- Reduce `max_workers` to 1
- Use a smaller model (e.g., `gemma2:2b`)
- Reduce `max_chunk_size`

### Poor Translation Quality
- Use a larger/better model (Llama 3 70B, Qwen2.5 72B)
- Add more terms to glossary
- Adjust `temperature` (lower = more deterministic)
- Increase `num_ctx` in LLMClient for longer context

### Cache Issues
```bash
# Clear cache and restart
python translate_llm.py directory/ --clear-cache --no-cache
```

## Future Enhancements

Potential improvements based on md-translator:

1. **Multi-pass translation**
   - First pass: literal translation
   - Second pass: context refinement

2. **Term extraction**
   - Automatically extract technical terms
   - Suggest glossary entries

3. **Quality scoring**
   - Score translation quality
   - Flag low-quality translations for review

4. **Diff mode**
   - Show changes between original and translated
   - Highlight modified sections

5. **Web UI**
   - Browser-based interface
   - Real-time preview
   - Manual correction tools

## License

Same as the main project.

## Contributing

Contributions welcome! Areas for improvement:
- Additional language support
- Better chunking strategies
- More sophisticated caching
- Integration with other LLM APIs (OpenAI, Anthropic, etc.)