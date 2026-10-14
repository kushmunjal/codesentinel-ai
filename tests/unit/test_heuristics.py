from codesentinel.checks.heuristics import check_heuristics
from codesentinel.checks.secrets import scan_for_secrets


def test_check_heuristics_small_pr_no_warnings():
    diff = "diff --git a/src/app.py b/src/app.py\n+x = 1\n+y = 2"
    warnings = check_heuristics(diff)
    assert warnings == []

def test_check_heuristics_missing_tests_warning():
    # 51 additions without any test files
    added_lines = "\n".join([f"+value_{i} = {i}" for i in range(55)])
    diff = f"diff --git a/src/app.py b/src/app.py\n{added_lines}"
    warnings = check_heuristics(diff)
    assert len(warnings) == 1
    assert "no tests seem to be included" in warnings[0]

def test_check_heuristics_with_tests_included():
    # > 50 additions but tests are included
    added_lines = "\n".join([f"+value_{i} = {i}" for i in range(60)])
    diff = f"""diff --git a/src/app.py b/src/app.py
{added_lines}
diff --git a/tests/test_app.py b/tests/test_app.py
+def test_app():
+    assert True"""
    warnings = check_heuristics(diff)
    assert warnings == []

def test_check_heuristics_large_pr_warning():
    # > 500 additions
    added_lines = "\n".join([f"+item_{i} = {i}" for i in range(505)])
    diff = f"""diff --git a/src/big.py b/src/big.py
{added_lines}
diff --git a/tests/test_big.py b/tests/test_big.py
+def test_big(): pass"""
    warnings = check_heuristics(diff)
    assert len(warnings) == 1
    assert "Large PR detected (506 additions)" in warnings[0]

def test_check_heuristics_large_pr_and_no_tests():
    added_lines = "\n".join([f"+item_{i} = {i}" for i in range(510)])
    diff = f"diff --git a/src/big.py b/src/big.py\n{added_lines}"
    warnings = check_heuristics(diff)
    assert len(warnings) == 2
    assert any("Large PR detected" in w for w in warnings)
    assert any("no tests seem to be included" in w for w in warnings)

def test_check_heuristics_empty_diff():
    assert check_heuristics("") == []

def test_scan_for_secrets_api_key():
    diff = """diff --git a/config.py b/config.py
+api_key = "fake_api_key_sample_token_123456789"
"""
    secrets = scan_for_secrets(diff)
    assert len(secrets) == 1
    assert secrets[0].startswith("Potential secret committed")

def test_scan_for_secrets_bearer_token():
    diff = """diff --git a/client.ts b/client.ts
+const authHeader = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz';
"""
    secrets = scan_for_secrets(diff)
    assert len(secrets) == 1
    assert secrets[0].startswith("Potential secret committed")

def test_scan_for_secrets_aws_access_key():
    diff = """diff --git a/deploy.sh b/deploy.sh
+export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
"""
    secrets = scan_for_secrets(diff)
    assert len(secrets) == 1
    assert secrets[0].startswith("Potential secret committed")

def test_scan_for_secrets_ignores_deletions_and_safe_lines():
    diff = """diff --git a/config.py b/config.py
-api_key = "fake_api_key_sample_token_123456789"
+api_key = os.environ.get("API_KEY")
+name = "CodeSentinel"
"""
    secrets = scan_for_secrets(diff)
    assert secrets == []
