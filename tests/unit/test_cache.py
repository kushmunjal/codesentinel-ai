import pytest
from codesentinel.llm.cache import compute_chunk_hash, get_cached_chunk, set_cached_chunk

def test_cache_storage_and_lookup():
    chunk = "diff --git a/foo.py b/foo.py\n+def foo(): return 42"
    model = "qwen/qwen3.8-27b"
    
    # Hash check
    h = compute_chunk_hash(chunk, model)
    assert len(h) == 64  # sha256 is 64 hex characters

    # Cache store & retrieval
    test_json = '{"findings": [{"file": "foo.py", "line": 1, "severity": "low", "category": "style", "explanation": "test"}]}'
    set_cached_chunk(chunk, test_json, model)

    retrieved = get_cached_chunk(chunk, model)
    assert retrieved == test_json

    # Non-existent chunk lookup
    missing = get_cached_chunk("nonexistent chunk", model)
    assert missing is None
