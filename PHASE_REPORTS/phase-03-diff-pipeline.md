# Phase 3 ? Diff Pipeline

**What was done:**
- Implemented `github_client.py` wrapping GitHub's REST API for PR diffs.
- Created `fetch.py` for downloading the raw diff.
- Built `filter.py` to drop `package-lock.json`, minified files, binary paths, etc.
- Added `chunk.py` with token-aware chunking using `tiktoken`.
- Added `positions.py` to map new file line numbers to diff positions for GitHub PR comments.
- Wrote and passed unit tests with fixture diffs (avoiding live network calls).
- Updated the dashboard's Build Progress and swapped the "Live PR Review" placeholder for a small pipeline sample output.

**Exact commands run:**
- Updated `pyproject.toml` with `requests` and `tiktoken`, ran `pip install -e .[dev]`.
- Created python modules in `src/codesentinel/diff/` and test fixtures.
- Ran `pytest -v`.
- Modified `dashboard/index.html` via Python script to update UI state.

**Proof of completion:**
Test results:
```
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0 -- /home/student/codesentinel-ai/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/student/codesentinel-ai
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 3 items

tests/unit/test_diff.py::test_filter_diff PASSED                         [ 33%]
tests/unit/test_diff.py::test_chunk_diff PASSED                          [ 66%]
tests/unit/test_diff.py::test_map_line_to_position PASSED                [100%]

============================== 3 passed in 0.13s ===============================
```

**What changed in the dashboard:**
- Phase 3 is ticked off in the Build Progress checklist.
- The "Live PR Review" panel was updated from a placeholder to show a sample filtered diff snippet representing pipeline success.

**What's left for the next phase:**
Phase 4: Provider-agnostic LLM layer + structured output schemas.
