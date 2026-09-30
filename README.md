# CodeSentinel AI

An AI-powered GitHub Action that automatically reviews pull requests and labels issues using LLMs.

## Quickstart

Add this to `.github/workflows/codesentinel.yml`:
```yaml
name: CodeSentinel
on:
  pull_request:
    types: [opened, synchronize]
  issues:
    types: [opened]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: kushmunjal/codesentinel-ai@v1
        with:
          provider: 'openai'
          model: 'gpt-4'
          api_key: ${{ secrets.LLM_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Security
- Follows least-privilege permissions.
- Hardened against prompt injection in untrusted PR data.
