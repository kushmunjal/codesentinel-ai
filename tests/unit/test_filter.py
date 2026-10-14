from codesentinel.diff.filter import filter_diff, should_ignore


def test_should_ignore_lockfiles():
    assert should_ignore("package-lock.json") is True
    assert should_ignore("yarn.lock") is True
    assert should_ignore("Cargo.lock") is True
    assert should_ignore("poetry.lock") is True
    assert should_ignore("nested/path/to/pnpm-lock.yaml") is True

def test_should_ignore_dist_and_build():
    assert should_ignore("dist/bundle.js") is True
    assert should_ignore("dist/static/css/app.css") is True
    assert should_ignore("build/main.o") is True
    assert should_ignore("build/output.wasm") is True

def test_should_ignore_minified_and_bytecode():
    assert should_ignore("vendor/jquery.min.js") is True
    assert should_ignore("app.min.js") is True
    assert should_ignore("module.pyc") is True
    assert should_ignore("__pycache__/foo.cpython-312.pyc") is True

def test_should_not_ignore_standard_source_code():
    assert should_ignore("src/main.py") is False
    assert should_ignore("src/components/Button.tsx") is False
    assert should_ignore("main.go") is False
    assert should_ignore("src/lib.rs") is False
    assert should_ignore("README.md") is False
    assert should_ignore("package.json") is False

def test_filter_diff_removes_ignored_files():
    raw_diff = """diff --git a/src/index.ts b/src/index.ts
index 1111..2222 100644
--- a/src/index.ts
+++ b/src/index.ts
@@ -1,3 +1,4 @@
 import express from 'express';
+export const app = express();
diff --git a/package-lock.json b/package-lock.json
index 3333..4444 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,5 @@
-"version": "1.0.0"
+"version": "1.0.1"
diff --git a/dist/bundle.js b/dist/bundle.js
index 5555..6666 100644
--- a/dist/bundle.js
+++ b/dist/bundle.js
@@ -1 +1 @@
-var a=1;
+var a=2;
diff --git a/src/utils.ts b/src/utils.ts
index 7777..8888 100644
--- a/src/utils.ts
+++ b/src/utils.ts
@@ -1,2 +1,3 @@
+export const add = (a: number, b: number) => a + b;
"""
    filtered = filter_diff(raw_diff)
    assert "src/index.ts" in filtered
    assert "src/utils.ts" in filtered
    assert "package-lock.json" not in filtered
    assert "dist/bundle.js" not in filtered
    assert "var a=2;" not in filtered

def test_filter_diff_alternate_header_format():
    # Tests line.split(" ")[-1][2:] fallback branch where header has 4 parts without b/
    raw_diff = "diff --git i/src/app.py w/src/app.py\n+print('hello')\ndiff --git i/dist/app.js w/dist/bundle.js\n+var x=1;"
    filtered = filter_diff(raw_diff)
    assert "src/app.py" in filtered
    assert "dist/bundle.js" not in filtered

def test_filter_diff_empty():
    assert filter_diff("") == ""

def test_filter_diff_preserves_clean_diff():
    raw_diff = """diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1 +1 @@
-old
+new"""
    assert filter_diff(raw_diff) == raw_diff
