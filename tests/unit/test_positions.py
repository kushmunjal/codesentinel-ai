from codesentinel.diff.positions import map_line_to_position


def test_map_line_added_line():
    patch = "@@ -0,0 +1,3 @@\n+def foo():\n+    x = 1\n+    return x\n"
    # Position 1: @@ header
    # Position 2: +def foo(): (line 1)
    # Position 3: +    x = 1 (line 2)
    # Position 4: +    return x (line 3)
    assert map_line_to_position(patch, 1) == 2
    assert map_line_to_position(patch, 2) == 3
    assert map_line_to_position(patch, 3) == 4

def test_map_line_context_line():
    patch = "@@ -10,3 +10,3 @@\n def unchanged():\n-    old = 1\n+    new = 2\n     return\n"
    # Position 1: @@ header
    # Position 2:  def unchanged(): (context line 10)
    # Position 3: -    old = 1 (deleted line, does not advance target line)
    # Position 4: +    new = 2 (added line 11)
    # Position 5:      return (context line 12)
    assert map_line_to_position(patch, 10) == 2
    assert map_line_to_position(patch, 11) == 4
    assert map_line_to_position(patch, 12) == 5

def test_map_line_with_multiple_hunks():
    patch = """@@ -5,2 +5,3 @@
 context 5
+added 6
 context 7
@@ -20,2 +21,3 @@
 context 21
+added 22
 context 23"""
    assert map_line_to_position(patch, 6) == 3
    assert map_line_to_position(patch, 22) == 7

def test_map_line_single_line_range_header():
    # Hunk header without comma: +1
    patch = "@@ -1 +1 @@\n+single line replacement\n"
    assert map_line_to_position(patch, 1) == 2

def test_map_line_not_found():
    patch = "@@ -1,2 +1,2 @@\n+line1\n+line2\n"
    assert map_line_to_position(patch, 999) == -1
    assert map_line_to_position(patch, 0) == -1

def test_map_line_empty_patch():
    assert map_line_to_position("", 1) == -1
