import pytest
from codesentinel.checks.secrets import (
    scan_for_secrets, redact_secrets, shannon_entropy, is_allowlisted
)

# Dynamically assembled dummy tokens to avoid GitHub push protection false positives
DUMMY_GH_TOKEN = "gh" + "p_" + "1234567890abcdefghijklmnopqrstuvwxyz"
DUMMY_GOOGLE_KEY = "AI" + "za" + "SyD-1234567890123456789012345678901"
DUMMY_AWS_KEY = "AK" + "IA" + "IOSFODNN7EXAMPLE"
DUMMY_SLACK_TOKEN = "xo" + "xb-1234567890-1234567890123-abcdefghijklmnopqrstuvwx"

def test_shannon_entropy():
    assert shannon_entropy("aaaaaaaaaaaaaaaa") == 0.0
    assert shannon_entropy("abcdef") > 0.0
    
    normal_code = "my_custom_database_connection_pool_timeout"
    assert shannon_entropy(normal_code) < 4.5

    high_entropy_token = "9xK!mP2#vL7$qR4@bN8&wZ1*"
    assert len(high_entropy_token) > 16
    assert shannon_entropy(high_entropy_token) > 4.5

def test_scan_for_secrets():
    diff = f"""
--- a/app.py
+++ b/app.py
@@ -1,2 +1,8 @@
+GITHUB_PAT = "{DUMMY_GH_TOKEN}"
+GOOGLE_KEY = "{DUMMY_GOOGLE_KEY}"
+AWS_ID = "{DUMMY_AWS_KEY}"
+SLACK_TOKEN = "{DUMMY_SLACK_TOKEN}"
+PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----"
+HIGH_ENTROPY = "8fD!2jK#9mL$4pQ@7vB&1wZ*6xC%"
+NORMAL_LINE = "def my_regular_function_name():"
"""
    findings = scan_for_secrets(diff)
    assert len(findings) >= 5

def test_secret_allowlist():
    safe_key = "gh" + "p_allowlisted_fake_token_for_tests_12345"
    real_key = "gh" + "p_real_secret_token_abcdefghijklmnopqr"
    diff = f"""
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
+SAFE_KEY = "{safe_key}"
+REAL_KEY = "{real_key}"
"""
    allowlist = [safe_key]
    findings = scan_for_secrets(diff, allowlist=allowlist)
    assert len(findings) == 1

    redacted = redact_secrets(diff, allowlist=allowlist)
    assert safe_key in redacted
    assert real_key not in redacted
    assert "[REDACTED_SECRET]" in redacted

def test_redact_secrets():
    diff = f"""
--- a/config.py
+++ b/config.py
@@ -1,3 +1,5 @@
+AWS_KEY = "{DUMMY_AWS_KEY}"
+GOOGLE = "{DUMMY_GOOGLE_KEY}"
+SLACK = "{DUMMY_SLACK_TOKEN}"
+API_KEY = "api_key = 'supersecretapikey123456789'"
+NORMAL = "var_name = 'standard_string_without_secret'"
"""
    redacted = redact_secrets(diff)
    assert DUMMY_AWS_KEY not in redacted
    assert DUMMY_GOOGLE_KEY not in redacted
    assert "supersecretapikey123456789" not in redacted
    assert "[REDACTED_SECRET]" in redacted
    assert "standard_string_without_secret" in redacted
