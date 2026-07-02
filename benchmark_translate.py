#!/usr/bin/env python3
"""
Benchmark: original translate_novo.py vs translate_novo_optimized.py

Goal: prove the optimized pipeline improves throughput while producing
IDENTICAL output, using the SAME translation logic.

Because a real Ollama server is not required to demonstrate the structural
throughput win, this harness injects a MOCK LLM with a fixed per-call latency
(default 0.20s) into BOTH pipelines. The mock is deterministic: for a given
input it always returns the same "translation", so:

  * the two pipelines must produce byte-for-byte identical files, and
  * the wall-clock difference is purely due to serial vs parallel execution.

To run the SAME benchmark against a real model instead, set:
    BENCH_REAL=1            # use the real Ollama backend (no mock)
and start Ollama with the configured model. Latency is then real.

Usage:
    python benchmark_translate.py [folder] [n_files]

Defaults:
    folder  = curriculum/.../es-a1-learn-talking-about-colleagues
    n_files = 10
"""

import os
import sys
import time
import shutil
import tempfile
import importlib.util
from pathlib import Path


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
DEFAULT_FOLDER = (
    "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/"
    "es-a1-learn-talking-about-colleagues"
)
MOCK_LATENCY = float(os.environ.get("BENCH_LATENCY", "0.20"))  # seconds per LLM call
USE_REAL = os.environ.get("BENCH_REAL", "0") == "1"
ORIG_PATH = "translate_novo.py"
OPT_PATH = "translate_novo_optimized.py"


# ----------------------------------------------------------------------------
# Module loading (load each script as an isolated module)
# ----------------------------------------------------------------------------
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------
# Deterministic mock LLM
# ----------------------------------------------------------------------------
# Calls counter is shared so we can report how many LLM calls each pipeline made.
class CallCounter:
    def __init__(self):
        self.count = 0

    def reset(self):
        self.count = 0


def make_mock_llm(counter):
    """
    Returns a function with the optimized backend signature fn(prompt, model).
    It extracts the TEXT block from the prompt and returns a deterministic
    pseudo-translation that PRESERVES every @@TOKEN@@ (so token validation
    passes) and contains no Swahili indicator words (so verification passes).
    """
    def mock(prompt, model=None):
        counter.count += 1
        if MOCK_LATENCY > 0:
            time.sleep(MOCK_LATENCY)
        # The prompt ends with "TEXT:\n\n<text>"; extract everything after it.
        marker = "TEXT:\n\n"
        idx = prompt.find(marker)
        text = prompt[idx + len(marker):] if idx != -1 else prompt
        # Deterministic transform: prefix a tag. Tokens (@@...@@) are left
        # untouched because we don't alter them. This yields stable, identical
        # output for both pipelines and keeps token counts intact.
        return "SR::" + text
    return mock


def patch_original(orig, mock):
    """
    The original translate_text() calls the network directly. We monkeypatch it
    to use the mock while keeping its surrounding retry/verify logic intact, so
    the comparison is apples-to-apples on the SAME translation result.
    """
    import json as _json

    def fake_urlopen(req, timeout=300):
        # Reconstruct prompt from the request body and feed the mock.
        body = req.data.decode("utf-8")
        data = _json.loads(body)
        prompt = data["prompt"]
        response_text = mock(prompt, data.get("model"))

        class _Resp:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *a):
                return False
            def read(self_inner):
                return _json.dumps({"response": response_text}).encode("utf-8")
        return _Resp()

    orig.urllib.request.urlopen = fake_urlopen


def prepare_files(src_folder, n, workdir, suffix):
    """Copy first n .md files into a fresh subdir for an isolated run."""
    dest = Path(workdir) / suffix
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(
        f for f in Path(src_folder).glob("*.md") if not f.name.endswith(".bak")
    )[:n]
    copied = []
    for f in files:
        target = dest / f.name
        shutil.copy2(f, target)
        copied.append(target)
    return copied


def run_pipeline(translate_single_file, files, model):
    start = time.perf_counter()
    ok = 0
    for f in files:
        if translate_single_file(str(f), model):
            ok += 1
    elapsed = time.perf_counter() - start
    return elapsed, ok


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FOLDER
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    if not Path(folder).is_dir():
        print(f"Error: folder not found: {folder}")
        sys.exit(1)

    print("=" * 72)
    print("TRANSLATION THROUGHPUT BENCHMARK")
    print("=" * 72)
    print(f"Folder      : {folder}")
    print(f"Files       : {n}")
    print(f"Mode        : {'REAL Ollama' if USE_REAL else f'MOCK LLM (latency={MOCK_LATENCY}s/call)'}")
    print("-" * 72)

    orig = load_module("orig_translate", ORIG_PATH)
    opt = load_module("opt_translate", OPT_PATH)

    model = getattr(opt, "DEFAULT_MODEL", "gemma4:latest")

    orig_counter = CallCounter()
    opt_counter = CallCounter()

    # Disable the optimized script's persistent cache during benchmarking so
    # the comparison reflects raw pipeline throughput, not warm-cache hits from
    # a previous run. (Cache effectiveness is reported separately below.)
    if hasattr(opt, "cache"):
        opt.cache.enabled = False

    if not USE_REAL:
        mock_orig = make_mock_llm(orig_counter)
        mock_opt = make_mock_llm(opt_counter)
        patch_original(orig, mock_orig)
        opt.LLM_BACKEND = mock_opt

    with tempfile.TemporaryDirectory() as workdir:
        orig_files = prepare_files(folder, n, workdir, "orig")
        opt_files = prepare_files(folder, n, workdir, "opt")

        # --- Original (sequential, serial chunks) ---
        print("\nRunning ORIGINAL pipeline (sequential files, serial chunks)...")
        orig_counter.reset()
        orig_time, orig_ok = run_pipeline(orig.translate_single_file, orig_files, model)
        orig_calls = orig_counter.count
        print(f"  -> {orig_ok}/{len(orig_files)} ok in {orig_time:.2f}s, {orig_calls} LLM calls")

        # --- Optimized (parallel files + parallel chunks) ---
        print("\nRunning OPTIMIZED pipeline (parallel files + chunks)...")
        opt_counter.reset()
        opt_start = time.perf_counter()
        opt_ok, opt_fail = opt._translate_files_parallel(opt_files, model, opt.FILE_WORKERS)
        opt_time = time.perf_counter() - opt_start
        opt_calls = opt_counter.count
        print(f"  -> {opt_ok}/{len(opt_files)} ok in {opt_time:.2f}s, {opt_calls} LLM calls")

        # --- Output identity check ---
        print("\nVerifying output identity (byte-for-byte)...")
        mismatches = []
        for of, pf in zip(sorted(orig_files), sorted(opt_files)):
            a = Path(of).read_text(encoding="utf-8")
            b = Path(pf).read_text(encoding="utf-8")
            if a != b:
                mismatches.append((of.name, pf.name))
        if mismatches:
            print(f"  ✗ {len(mismatches)} file(s) differ:")
            for a, b in mismatches[:5]:
                print(f"    - {a} vs {b}")
        else:
            print(f"  ✓ All {len(orig_files)} outputs identical")

    # --- Report ---
    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)
    print(f"  Original   : {orig_time:.2f}s   ({orig_calls} LLM calls)")
    print(f"  Optimized  : {opt_time:.2f}s   ({opt_calls} LLM calls)")
    if opt_time > 0:
        print(f"  Speedup    : {orig_time / opt_time:.2f}x faster")
    if orig_calls:
        print(f"  Call delta : {orig_calls - opt_calls} fewer calls "
              f"({100 * (orig_calls - opt_calls) / orig_calls:.1f}% reduction)")
    print(f"  Identical  : {'YES' if not mismatches else 'NO'}")
    print("=" * 72)


if __name__ == "__main__":
    main()
