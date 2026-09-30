import pytest
from codesentinel.diff.filter import filter_diff
from codesentinel.diff.chunk import chunk_diff
from codesentinel.diff.positions import map_line_to_position

def test_filter_diff():
    with open("tests/fixtures/sample_diff.txt", "r") as f:
        raw_diff = f.read()
    
    filtered = filter_diff(raw_diff)
    assert "good.py" in filtered
    assert "package-lock.json" not in filtered
    assert "dist/bundle.js" not in filtered

def test_chunk_diff():
    filtered = "diff --git a/1.py b/1.py\n+print(1)\ndiff --git a/2.py b/2.py\n+print(2)"
    # Max tokens very low to force split
    chunks = chunk_diff(filtered, max_tokens=10)
    assert len(chunks) == 2
    assert "1.py" in chunks[0]
    assert "2.py" in chunks[1]

def test_map_line_to_position():
    patch = "@@ -0,0 +1,2 @@\n+def test():\n+    pass\n"
    # Target line 1 corresponds to +def test(): which is position 2 in the patch
    pos = map_line_to_position(patch, 1)
    assert pos == 2
