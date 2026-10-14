import json
import os
from typing import List, Dict, Any
from codesentinel.schemas import Finding

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"

SEVERITY_LEVEL_MAP = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note"
}

def generate_sarif(findings: List[Finding], repo_uri: str = "https://github.com/kushmunjal/codesentinel-ai", repo_name: str = "", commit_sha: str = "", **kwargs) -> Dict[str, Any]:
    """Generates a SARIF v2.1.0 dictionary representation from CodeSentinel findings."""
    rules_dict = {}
    results = []

    for idx, finding in enumerate(findings):
        cat = (finding.category or "bug").lower()
        rule_id = f"codesentinel/{cat}"
        
        if rule_id not in rules_dict:
            rules_dict[rule_id] = {
                "id": rule_id,
                "name": f"{cat.capitalize()}Rule",
                "shortDescription": {
                    "text": f"CodeSentinel {cat.capitalize()} finding"
                },
                "defaultConfiguration": {
                    "level": SEVERITY_LEVEL_MAP.get(finding.severity.lower(), "warning")
                }
            }

        level = SEVERITY_LEVEL_MAP.get(finding.severity.lower(), "warning")
        target_line = max(1, finding.line)
        
        result = {
            "ruleId": rule_id,
            "ruleIndex": list(rules_dict.keys()).index(rule_id),
            "level": level,
            "message": {
                "text": finding.explanation
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.file,
                            "uriBaseId": "%SRCROOT%"
                        },
                        "region": {
                            "startLine": target_line,
                            "endLine": target_line
                        }
                    }
                }
            ]
        }

        if finding.suggested_fix:
            result["fixes"] = [
                {
                    "description": {
                        "text": "Suggested code fix"
                    },
                    "fileChanges": [
                        {
                            "artifactLocation": {
                                "uri": finding.file
                            },
                            "replacements": [
                                {
                                    "deletedRegion": {
                                        "startLine": target_line,
                                        "endLine": target_line
                                    },
                                    "insertedContent": {
                                        "text": finding.suggested_fix
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]

        results.append(result)

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeSentinel AI",
                        "version": "1.0.0",
                        "informationUri": repo_uri,
                        "rules": list(rules_dict.values())
                    }
                },
                "results": results
            }
        ]
    }

def write_sarif(findings: List[Finding], output_path: str, repo_uri: str = "https://github.com/kushmunjal/codesentinel-ai") -> Dict[str, Any]:
    """Generates and writes SARIF v2.1.0 output to the specified file path."""
    sarif_data = generate_sarif(findings, repo_uri=repo_uri)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sarif_data, f, indent=2)
    return sarif_data


def write_sarif_file(sarif_data: Dict[str, Any], filepath: str) -> None:
    dirname = os.path.dirname(os.path.abspath(filepath))
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(sarif_data, f, indent=2)
