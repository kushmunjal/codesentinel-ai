# Security Policy

The CodeSentinel AI team takes the security of our platform, dependencies, and users seriously. We appreciate the efforts of security researchers and community members in keeping CodeSentinel AI safe.

---

## Supported Versions

Only the latest active release branch receives proactive security updates and vulnerability patches.

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 0.2.x   | :white_check_mark: | Active           |
| 0.1.x   | :white_check_mark: | Critical only    |
| < 0.1.0 | :x:                | Unsupported      |

---

## Reporting a Vulnerability

**Please do NOT file public GitHub issues for security vulnerabilities.**

If you discover a security vulnerability in CodeSentinel AI (including prompt injection bypasses, authentication flaws, secret leakage, or dependency vulnerabilities), please report it responsibly:

1. **Email Disclosure:** Send an email to `security@codesentinel.ai` (or create a private GitHub Security Advisory at `https://github.com/kushmunjal/codesentinel-ai/security/advisories/new`).
2. **Details to Include:**
   - Detailed description of the vulnerability and attack vector.
   - Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
   - Component affected (`review/pipeline`, `triage/pipeline`, `api/auth`, `api/main`, etc.).
   - Potential impact (e.g., privilege escalation, unauthorized data access, DoS).
   - Any proposed remediation or patches.

### Response Timelines & SLAs

- **Initial Acknowledgment:** Within **24 to 48 hours** of receiving your report.
- **Triage & Assessment:** Within **5 business days**, confirming severity and validity.
- **Remediation & Patching:**
  - Critical Severity: Within **7 calendar days**.
  - High Severity: Within **14 calendar days**.
  - Medium / Low Severity: Within **30 calendar days**.
- **Public Disclosure:** Following patch deployment, coordinated with the reporter.

---

## Coordinated Disclosure Policy

CodeSentinel AI follows Coordinated Vulnerability Disclosure (CVD):
- We ask researchers to give us reasonable time (up to 90 days) to address vulnerabilities before making any public disclosure.
- We will coordinate advisory release dates with the finder.
- We will credit researchers in security release notes and advisories (unless anonymity is requested).

---

## Safe Harbor Policy

We consider security research conducted under this policy to be:
- Authorized under relevant computer fraud and abuse laws.
- Exempt from anti-circumvention prohibitions.
- Lawful, good-faith security research.

To remain eligible for safe harbor:
- Do not exploit a vulnerability beyond the minimal extent necessary to demonstrate the risk.
- Do not destroy, alter, or access data belonging to other users or organizations.
- Do not disrupt or degrade production services or LLM billing quotas.
- Comply with all applicable data privacy and protection laws.

---

## Secure Deployment Guidelines

When deploying CodeSentinel AI in production:
1. **Never commit secrets:** Never commit `.env` files, GitHub tokens, or LLM API keys. Use GitHub Actions Secrets or environment variables.
2. **Enforce Least Privilege:** Restrict GitHub Token permissions to the minimum necessary:
   ```yaml
   permissions:
     contents: read
     pull-requests: write
     issues: write
   ```
3. **Configure Rate Limits:** Set `RATE_LIMIT_PER_MINUTE` according to expected console traffic.
4. **Change Default Credentials:** Set `JWT_SECRET_KEY`, `DEFAULT_ADMIN_PASSWORD`, and `DEFAULT_MAINTAINER_PASSWORD` to cryptographically strong values prior to production use.
5. **Lock Down CORS:** Set `ALLOWED_ORIGINS` to the exact hostnames allowed to access the console API.
