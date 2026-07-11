#!/usr/bin/env python3
"""
Advanced LLM-based Markdown Translation Script
Inspired by md-translator (https://github.com/rockbenben/md-translator)

Features:
- Batch translation with context awareness
- Concurrent processing
- Caching
- Glossary support
- Retry logic with exponential backoff
- Progress reporting
- Cancellation support
- Prompt management
"""

import os
import sys
import json
import hashlib
import time
import re
import threading
import signal
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


# ======================================
# DEFAULT FOLDERS TO TRANSLATE
# ======================================

FOLDERS_TO_TRANSLATE = [
    "curriculum/i18n-curriculum//curriculum/challenges/swahili/blocks/designing-reliable-rag-systems",
    # Add more folders here as needed
    # "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/designing-reliable-rag-systems",
]


# ======================================
# CONFIGURATION
# ======================================

@dataclass
class TranslationConfig:
    """Configuration for translation."""
    source_lang: str = "swahili"
    target_lang: str = "serbian"
    model: str = "gemma4:latest"
    api_url: str = "http://localhost:11434/api/generate"
    max_workers: int = 2
    max_retries: int = 3
    timeout: int = 300
    temperature: float = 0.3
    max_chunk_size: int = 1000
    max_lines: int = 50
    cache_enabled: bool = True
    cache_dir: str = ".translation_cache"
    glossary_file: str = "glossary.json"
    log_file: str = "translation_llm.log"


# ======================================
# DATA MODELS
# ======================================

class TranslationStatus(Enum):
    PENDING = "pending"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    status: TranslationStatus
    tokens_used: int = 0
    duration: float = 0.0
    retries: int = 0
    error: Optional[str] = None


@dataclass
class FileTranslationResult:
    """Result of file translation."""
    file_path: str
    status: TranslationStatus
    chunks_translated: int = 0
    chunks_cached: int = 0
    chunks_failed: int = 0
    duration: float = 0.0
    error: Optional[str] = None


# ======================================
# CACHE MANAGER
# ======================================

class CacheManager:
    """Manages translation caching."""
    
    def __init__(self, cache_dir: str = ".translation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key from text and languages."""
        content = f"{source_lang}:{target_lang}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get cached translation."""
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with self.lock:
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('translated_text')
                except:
                    return None
        return None
    
    def set(self, text: str, source_lang: str, target_lang: str, translated_text: str):
        """Cache translation result."""
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with self.lock:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                        'original_text': text,
                        'translated_text': translated_text,
                        'timestamp': datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Warning: Failed to cache translation: {e}")
    
    def clear(self):
        """Clear all cache."""
        with self.lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except:
                    pass
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        return {
            'total_entries': len(cache_files),
            'cache_dir': str(self.cache_dir)
        }


# ======================================
# GLOSSARY MANAGER
# ======================================

class GlossaryManager:
    """Manages translation glossary."""
    
    def __init__(self, glossary_file: str = "glossary.json"):
        self.glossary_file = Path(glossary_file)
        self.glossary: Dict[str, str] = {}
        self.lock = threading.Lock()
        self.load()
    
    def load(self):
        """Load glossary from file."""
        with self.lock:
            if self.glossary_file.exists():
                try:
                    with open(self.glossary_file, 'r', encoding='utf-8') as f:
                        self.glossary = json.load(f)
                except:
                    self.glossary = {}
    
    def save(self):
        """Save glossary to file."""
        with self.lock:
            try:
                with open(self.glossary_file, 'w', encoding='utf-8') as f:
                    json.dump(self.glossary, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Warning: Failed to save glossary: {e}")
    
    def get(self, term: str) -> Optional[str]:
        """Get translation for term."""
        return self.glossary.get(term.lower())
    
    def add(self, term: str, translation: str):
        """Add term to glossary."""
        with self.lock:
            self.glossary[term.lower()] = translation
            self.save()
    
    def apply(self, text: str) -> str:
        """Apply glossary to text."""
        result = text
        for term, translation in self.glossary.items():
            # Use word boundaries for exact matches
            pattern = r'\b' + re.escape(term) + r'\b'
            result = re.sub(pattern, translation, result, flags=re.IGNORECASE)
        return result


# ======================================
# PROMPT TEMPLATES
# ======================================

class PromptTemplate:
    """Manages translation prompts."""
    
    @staticmethod
    def get_translation_prompt(source_lang: str, target_lang: str, text: str, context: str = "") -> str:
        """Generate translation prompt."""
        prompt = f"""Translate the following {source_lang} text to {target_lang}.

RULES:
1. Translate ONLY natural language text
2. Do NOT translate: code, URLs, API names, programming keywords, technical terms
3. Keep the same formatting and structure (Markdown, HTML, etc.)
4. Use natural {target_lang} technical terminology
5. Preserve all placeholders, variables, and template expressions
6. Provide ONLY the translation, no explanations or comments
7. Maintain consistency with previous translations

"""
        
        if context:
            prompt += f"CONTEXT FROM PREVIOUS CHUNKS:\n{context}\n\n"
        
        prompt += f"TEXT TO TRANSLATE:\n\n{text}"
        
        return prompt
    
    @staticmethod
    def get_system_prompt(source_lang: str, target_lang: str) -> str:
        """Get system prompt for translation."""
        return f"""You are a professional translator specializing in technical documentation.
You translate from {source_lang} to {target_lang}.
You preserve all code, technical terms, and formatting.
You provide accurate, natural-sounding translations."""


# ======================================
# LLM CLIENT
# ======================================

class LLMClient:
    """Client for interacting with LLM API."""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.session = None
    
    def translate(self, text: str, context: str = "", glossary: Optional[GlossaryManager] = None) -> TranslationResult:
        """
        Translate text using LLM.
        
        Args:
            text: Text to translate
            context: Context from previous chunks
            glossary: Glossary manager for term consistency
        
        Returns:
            TranslationResult
        """
        start_time = time.time()
        
        # Apply glossary if provided
        if glossary:
            text = glossary.apply(text)
        
        # Generate prompt
        prompt = PromptTemplate.get_translation_prompt(
            self.config.source_lang,
            self.config.target_lang,
            text,
            context
        )
        
        # Retry logic
        for attempt in range(self.config.max_retries):
            try:
                result = self._call_api(prompt)
                
                if result and result.strip():
                    duration = time.time() - start_time
                    return TranslationResult(
                        original_text=text,
                        translated_text=result.strip(),
                        status=TranslationStatus.COMPLETED,
                        duration=duration,
                        retries=attempt
                    )
                
                # Empty result, retry
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    duration = time.time() - start_time
                    return TranslationResult(
                        original_text=text,
                        translated_text=text,
                        status=TranslationStatus.FAILED,
                        duration=duration,
                        retries=attempt,
                        error=str(e)
                    )
        
        # All retries failed
        duration = time.time() - start_time
        return TranslationResult(
            original_text=text,
            translated_text=text,
            status=TranslationStatus.FAILED,
            duration=duration,
            retries=self.config.max_retries,
            error="Max retries exceeded"
        )
    
    def _call_api(self, prompt: str) -> str:
        """Call LLM API."""
        import urllib.request
        
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": 4096
            }
        }
        
        req = urllib.request.Request(
            self.config.api_url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('response', '').strip()


# ======================================
# MARKDOWN CHUNKER
# ======================================

class MarkdownChunker:
    """Splits markdown into translatable chunks."""
    
    def __init__(self, max_chunk_size: int = 1000, max_lines: int = 50):
        self.max_chunk_size = max_chunk_size
        self.max_lines = max_lines
    
    def chunk(self, text: str) -> List[Tuple[str, str]]:
        """
        Split text into chunks.
        
        Returns:
            List of (chunk_type, chunk_content) tuples
            chunk_type: 'text', 'code', 'newline', 'empty'
        """
        chunks = []
        
        # Split by code blocks first
        parts = re.split(r'(```[\s\S]*?```)', text)
        
        for part in parts:
            if part.startswith('```'):
                chunks.append(('code', part))
            else:
                chunks.extend(self._chunk_text(part))
        
        return chunks
    
    def _chunk_text(self, text: str) -> List[Tuple[str, str]]:
        """Chunk non-code text."""
        chunks = []
        paragraphs = re.split(r'(\n\n)', text)
        
        current_text = []
        current_lines = 0
        
        for para in paragraphs:
            if para == '\n\n':
                if current_text:
                    chunks.append(('text', ''.join(current_text)))
                    current_text = []
                    current_lines = 0
                chunks.append(('newline', para))
            elif para.strip():
                para_lines = para.count('\n') + 1
                
                if current_text and (current_lines + para_lines > self.max_lines or 
                                    len(''.join(current_text)) + len(para) > self.max_chunk_size):
                    chunks.append(('text', ''.join(current_text)))
                    current_text = []
                    current_lines = 0
                
                current_text.append(para)
                current_lines += para_lines
            else:
                if current_text:
                    chunks.append(('text', ''.join(current_text)))
                    current_text = []
                    current_lines = 0
                chunks.append(('empty', para))
        
        if current_text:
            chunks.append(('text', ''.join(current_text)))
        
        return chunks


# ======================================
# PROGRESS TRACKER
# ======================================

class ProgressTracker:
    """Tracks translation progress."""
    
    def __init__(self, total: int = 0):
        self.total = total
        self.current = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def update(self, delta: int = 1):
        """Update progress."""
        with self.lock:
            self.current += delta
    
    def get_progress(self) -> Dict:
        """Get progress information."""
        with self.lock:
            elapsed = time.time() - self.start_time
            rate = self.current / elapsed if elapsed > 0 else 0
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            
            return {
                'current': self.current,
                'total': self.total,
                'percentage': (self.current / self.total * 100) if self.total > 0 else 0,
                'elapsed': elapsed,
                'remaining': remaining,
                'rate': rate
            }
    
    def print_progress(self):
        """Print progress bar."""
        progress = self.get_progress()
        
        bar_length = 50
        filled = int(bar_length * progress['current'] / progress['total']) if progress['total'] > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r{bar} {progress['percentage']:.1f}% ({progress['current']}/{progress['total']}) "
              f"[{progress['elapsed']:.1f}s elapsed, {progress['remaining']:.1f}s remaining]", 
              end='', flush=True)
        
        if progress['current'] >= progress['total']:
            print()  # New line when complete


# ======================================
# TRANSLATION ENGINE
# ======================================

class TranslationEngine:
    """Core translation engine."""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.llm_client = LLMClient(config)
        self.chunker = MarkdownChunker(config.max_chunk_size, config.max_lines)
        self.cache = CacheManager(config.cache_dir) if config.cache_enabled else None
        self.glossary = GlossaryManager(config.glossary_file)
        self.progress = ProgressTracker()
        self.cancelled = False
        self.context_window: List[str] = []  # Keep last N translations for context
        self.max_context = 3
        
        # Setup signal handler for cancellation
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle cancellation signal."""
        self.cancelled = True
        print("\n⚠ Cancellation requested... finishing current chunk")
    
    def translate_file(self, file_path: str) -> FileTranslationResult:
        """
        Translate a markdown file.
        
        Args:
            file_path: Path to markdown file
        
        Returns:
            FileTranslationResult
        """
        start_time = time.time()
        
        # Create backup before translation
        backup_path = file_path + '.bak'
        if not os.path.exists(backup_path):
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                return FileTranslationResult(
                    file_path=file_path,
                    status=TranslationStatus.FAILED,
                    duration=0.0,
                    error=f"Failed to create backup: {e}"
                )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse file structure
            structure = self._parse_structure(content)
            
            # Translate each part
            translated_structure = []
            chunks_translated = 0
            chunks_cached = 0
            chunks_failed = 0
            
            for part_type, part_content in structure:
                if part_type == 'yaml':
                    # Translate only title in YAML
                    translated = self._translate_yaml(part_content)
                    translated_structure.append((part_type, translated))
                elif part_type == 'marker':
                    # Keep markers as-is
                    translated_structure.append((part_type, part_content))
                elif part_type == 'content':
                    # Translate content
                    result = self._translate_content(part_content)
                    translated_structure.append((part_type, result['text']))
                    chunks_translated += result['translated']
                    chunks_cached += result['cached']
                    chunks_failed += result['failed']
            
            # Reconstruct file
            translated_content = self._reconstruct_structure(translated_structure)
            
            # Write translated file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            duration = time.time() - start_time
            
            return FileTranslationResult(
                file_path=file_path,
                status=TranslationStatus.COMPLETED,
                chunks_translated=chunks_translated,
                chunks_cached=chunks_cached,
                chunks_failed=chunks_failed,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return FileTranslationResult(
                file_path=file_path,
                status=TranslationStatus.FAILED,
                duration=duration,
                error=str(e)
            )
    
    def _translate_yaml(self, yaml_content: str) -> str:
        """Translate YAML frontmatter (only title)."""
        lines = yaml_content.split('\n')
        translated_lines = []
        
        for line in lines:
            if line.startswith('title:'):
                # Translate title
                title_text = line.split(':', 1)[1].strip()
                if title_text:
                    result = self._translate_chunk(title_text)
                    if result.status == TranslationStatus.COMPLETED:
                        translated_lines.append(f"title: {result.translated_text}")
                    else:
                        translated_lines.append(line)
                else:
                    translated_lines.append(line)
            else:
                translated_lines.append(line)
        
        return '\n'.join(translated_lines)
    
    def _translate_content(self, content: str) -> Dict:
        """Translate content section."""
        chunks = self.chunker.chunk(content)
        
        translated_chunks = []
        translated_count = 0
        cached_count = 0
        failed_count = 0
        
        for chunk_type, chunk in chunks:
            if chunk_type in ('code', 'newline', 'empty'):
                # Don't translate code, newlines, empty lines
                translated_chunks.append((chunk_type, chunk))
            else:
                # Translate text chunk
                result = self._translate_chunk(chunk)
                
                if result.status == TranslationStatus.COMPLETED:
                    translated_chunks.append((chunk_type, result.translated_text))
                    translated_count += 1
                    # Add to context window
                    self.context_window.append(result.translated_text)
                    if len(self.context_window) > self.max_context:
                        self.context_window.pop(0)
                elif result.status == TranslationStatus.CACHED:
                    translated_chunks.append((chunk_type, result.translated_text))
                    cached_count += 1
                else:
                    # Keep original on failure
                    translated_chunks.append((chunk_type, chunk))
                    failed_count += 1
        
        # Reconstruct content
        text = ''.join(chunk for _, chunk in translated_chunks)
        
        return {
            'text': text,
            'translated': translated_count,
            'cached': cached_count,
            'failed': failed_count
        }
    
    def _translate_chunk(self, text: str) -> TranslationResult:
        """Translate a single chunk."""
        if self.cancelled:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                status=TranslationStatus.FAILED,
                error="Cancelled"
            )
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(text, self.config.source_lang, self.config.target_lang)
            if cached:
                return TranslationResult(
                    original_text=text,
                    translated_text=cached,
                    status=TranslationStatus.CACHED
                )
        
        # Get context from recent translations
        context = '\n\n'.join(self.context_window[-2:]) if self.context_window else ""
        
        # Translate
        result = self.llm_client.translate(text, context, self.glossary)
        
        # Cache successful translations
        if result.status == TranslationStatus.COMPLETED and self.cache:
            self.cache.set(text, self.config.source_lang, self.config.target_lang, result.translated_text)
        
        return result
    
    def _parse_structure(self, content: str) -> List[Tuple[str, str]]:
        """Parse markdown file structure."""
        structure = []
        
        # Extract YAML frontmatter
        yaml_match = re.match(r'^(---\n.*?\n---\n)', content, re.DOTALL)
        if yaml_match:
            structure.append(('yaml', yaml_match.group(1)))
            remaining = content[yaml_match.end():]
        else:
            remaining = content
        
        # Find section markers
        marker_pattern = r'^(\#{1,6}\s*--[a-z-]+--\s*)$'
        last_end = 0
        
        for match in re.finditer(marker_pattern, remaining, re.MULTILINE):
            if match.start() > last_end:
                content_text = remaining[last_end:match.start()]
                if content_text:
                    structure.append(('content', content_text))
            
            structure.append(('marker', match.group(1)))
            last_end = match.end()
        
        if last_end < len(remaining):
            content_text = remaining[last_end:]
            if content_text:
                structure.append(('content', content_text))
        elif last_end == 0:
            structure.append(('content', remaining))
        
        return structure
    
    def _reconstruct_structure(self, structure: List[Tuple[str, str]]) -> str:
        """Reconstruct file from structure."""
        return ''.join(content for _, content in structure)


# ======================================
# BATCH TRANSLATOR
# ======================================

class BatchTranslator:
    """Handles batch translation of multiple files."""
    
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.engine = TranslationEngine(config)
        self.lock = threading.Lock()
        self.results: List[FileTranslationResult] = []
    
    def translate_files(self, file_paths: List[str], progress_callback=None) -> List[FileTranslationResult]:
        """
        Translate multiple files concurrently.
        
        Args:
            file_paths: List of file paths to translate
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of FileTranslationResult
        """
        self.results = []
        self.engine.progress = ProgressTracker(len(file_paths))
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self.engine.translate_file, fp): fp 
                for fp in file_paths
            }
            
            for future in as_completed(futures):
                if self.engine.cancelled:
                    break
                
                file_path = futures[future]
                try:
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                    
                    if progress_callback:
                        progress_callback(result)
                    
                    self.engine.progress.update(1)
                    self.engine.progress.print_progress()
                    
                except Exception as e:
                    error_result = FileTranslationResult(
                        file_path=file_path,
                        status=TranslationStatus.FAILED,
                        error=str(e)
                    )
                    with self.lock:
                        self.results.append(error_result)
        
        return self.results
    
    def get_statistics(self) -> Dict:
        """Get translation statistics."""
        stats = {
            'total': len(self.results),
            'completed': sum(1 for r in self.results if r.status == TranslationStatus.COMPLETED),
            'failed': sum(1 for r in self.results if r.status == TranslationStatus.FAILED),
            'total_chunks': sum(r.chunks_translated + r.chunks_cached + r.chunks_failed for r in self.results),
            'total_translated': sum(r.chunks_translated for r in self.results),
            'total_cached': sum(r.chunks_cached for r in self.results),
            'total_failed': sum(r.chunks_failed for r in self.results),
            'total_duration': sum(r.duration for r in self.results)
        }
        
        if self.config.cache_enabled:
            stats['cache'] = self.engine.cache.get_stats()
        
        return stats


# ======================================
# MAIN INTERFACE
# ======================================

def translate_directory(directory: str, config: Optional[TranslationConfig] = None) -> List[FileTranslationResult]:
    """
    Translate all markdown files in a directory.
    
    Args:
        directory: Directory containing markdown files
        config: Translation configuration (uses default if not provided)
    
    Returns:
        List of FileTranslationResult
    """
    if config is None:
        config = TranslationConfig()
    
    # Find all markdown files
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    md_files = sorted([f for f in dir_path.glob('*.md') if not f.name.endswith('.bak')])
    
    if not md_files:
        print(f"No markdown files found in {directory}")
        return []
    
    print(f"Found {len(md_files)} files to translate")
    print("=" * 60)
    
    # Translate files
    translator = BatchTranslator(config)
    results = translator.translate_files([str(f) for f in md_files])
    
    # Print summary
    print("\n" + "=" * 60)
    print("TRANSLATION SUMMARY")
    print("=" * 60)
    
    stats = translator.get_statistics()
    print(f"Files processed: {stats['total']}")
    print(f"Completed: {stats['completed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total chunks translated: {stats['total_translated']}")
    print(f"Total chunks cached: {stats['total_cached']}")
    print(f"Total duration: {stats['total_duration']:.2f}s")
    
    if stats.get('cache'):
        print(f"\nCache statistics:")
        print(f"  Entries: {stats['cache']['total_entries']}")
    
    print("=" * 60)
    
    return results


def translate_file(file_path: str, config: Optional[TranslationConfig] = None) -> FileTranslationResult:
    """
    Translate a single markdown file.
    
    Args:
        file_path: Path to markdown file
        config: Translation configuration
    
    Returns:
        FileTranslationResult
    """
    if config is None:
        config = TranslationConfig()
    
    engine = TranslationEngine(config)
    return engine.translate_file(file_path)


# ======================================
# CLI INTERFACE
# ======================================

def translate_all_folders(config: Optional[TranslationConfig] = None) -> bool:
    """
    Translate all folders in FOLDERS_TO_TRANSLATE.
    
    Args:
        config: Translation configuration (uses default if not provided)
    
    Returns:
        True if all translations succeeded, False otherwise
    """
    if config is None:
        config = TranslationConfig()
    
    print(f"Found {len(FOLDERS_TO_TRANSLATE)} folders to translate")
    print("=" * 60)
    
    total_success = 0
    total_failed = 0
    
    for folder in FOLDERS_TO_TRANSLATE:
        folder_path = Path(folder)
        if not folder_path.exists():
            print(f"\n⚠ Folder not found: {folder}")
            continue
        
        md_files = sorted([f for f in folder_path.glob('*.md') if not f.name.endswith('.bak')])
        
        if not md_files:
            print(f"\n⚠ No .md files found in: {folder}")
            continue
        
        print(f"\n📁 Translating: {folder}")
        print(f"   Files: {len(md_files)}")
        print("-" * 60)
        
        translator = BatchTranslator(config)
        results = translator.translate_files([str(f) for f in md_files])
        
        folder_success = sum(1 for r in results if r.status == TranslationStatus.COMPLETED)
        folder_failed = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        
        total_success += folder_success
        total_failed += folder_failed
        
        print(f"\n  ✓ Folder complete: {folder_success} success, {folder_failed} failed")
    
    print("\n" + "=" * 60)
    print(f"TRANSLATION COMPLETE!")
    print(f"  Total success: {total_success}")
    print(f"  Total failed: {total_failed}")
    print("=" * 60)
    
    return total_failed == 0


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced LLM-based Markdown Translator')
    parser.add_argument('target', nargs='?', help='File or directory to translate')
    parser.add_argument('--model', default='gemma4:latest', help='LLM model to use')
    parser.add_argument('--source-lang', default='swahili', help='Source language')
    parser.add_argument('--target-lang', default='serbian', help='Target language')
    parser.add_argument('--workers', type=int, default=2, help='Number of parallel workers')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--clear-cache', action='store_true', help='Clear translation cache')
    parser.add_argument('--glossary', help='Path to glossary file')
    parser.add_argument('--all', action='store_true', help='Translate all folders in FOLDERS_TO_TRANSLATE')
    
    args = parser.parse_args()
    
    # Create config
    config = TranslationConfig(
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        model=args.model,
        max_workers=args.workers,
        cache_enabled=not args.no_cache,
        glossary_file=args.glossary or "glossary.json"
    )
    
    # Clear cache if requested
    if args.clear_cache:
        cache = CacheManager(config.cache_dir)
        cache.clear()
        print("Cache cleared")
        return
    
    # Translate all folders
    if args.all or (args.target is None):
        if not FOLDERS_TO_TRANSLATE:
            print("Error: No folders defined in FOLDERS_TO_TRANSLATE")
            sys.exit(1)
        success = translate_all_folders(config)
        sys.exit(0 if success else 1)
    
    # Translate specific target
    target = args.target
    
    if os.path.isfile(target):
        if not target.endswith('.md') or target.endswith('.bak'):
            print("Error: Please provide a .md file (not .bak)")
            sys.exit(1)
        
        print(f"Translating file: {target}")
        result = translate_file(target, config)
        
        if result.status == TranslationStatus.COMPLETED:
            print(f"✓ Translation completed in {result.duration:.2f}s")
            print(f"  Chunks translated: {result.chunks_translated}")
            print(f"  Chunks cached: {result.chunks_cached}")
        else:
            print(f"✗ Translation failed: {result.error}")
            sys.exit(1)
    
    elif os.path.isdir(target):
        results = translate_directory(target, config)
        
        failed = sum(1 for r in results if r.status == TranslationStatus.FAILED)
        if failed > 0:
            sys.exit(1)
    
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()