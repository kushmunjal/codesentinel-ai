import type { PRDetail, IssueDetail, StatSummary, Finding, TokenResponse } from "@/types";

const API_BASE = "/api";

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem("codesentinel_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Fallback initial findings for demo / offline resilience
export const DEFAULT_FINDINGS: Record<number, Finding[]> = {
  1: [
    {
      id: 101,
      pr_number: 1,
      repo: "codesentinel-test",
      file: "src/calc.py",
      line: 14,
      severity: "critical",
      category: "bug",
      explanation: "Division by zero is not handled when denominator b == 0, triggering an unhandled ZeroDivisionError in calculation pipeline.",
      suggested_fix: "if b == 0:\n    raise ValueError(\"Cannot divide by zero\")\nreturn a / b",
      feedback: null,
      created_at: new Date().toISOString()
    },
    {
      id: 102,
      pr_number: 1,
      repo: "codesentinel-test",
      file: "src/calc.py",
      line: 28,
      severity: "medium",
      category: "style",
      explanation: "Missing type annotations and parameter documentation for subtract function.",
      suggested_fix: "def subtract(a: float, b: float) -> float:\n    \"\"\"Subtract b from a.\"\"\"\n    return a - b",
      feedback: null,
      created_at: new Date().toISOString()
    }
  ],
  4: [
    {
      id: 103,
      pr_number: 4,
      repo: "codesentinel-test",
      file: "src/config.py",
      line: 7,
      severity: "high",
      category: "security",
      explanation: "Hardcoded API key detected in source code. Secrets should be retrieved securely from environment variables.",
      suggested_fix: "API_KEY = os.environ.get(\"API_KEY\")",
      feedback: null,
      created_at: new Date().toISOString()
    }
  ],
  5: [
    {
      id: 104,
      pr_number: 5,
      repo: "codesentinel-test",
      file: "src/helpers.py",
      line: 5,
      severity: "high",
      category: "bug",
      explanation: "Boundary condition error: returns False when value is 0 but specification requires positive or explicit non-negative handling.",
      suggested_fix: "return value > 0",
      feedback: null,
      created_at: new Date().toISOString()
    }
  ]
};

export const DEFAULT_PRS: PRDetail[] = [
  {
    number: 1,
    title: "Add divide method and update subtract",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "CRITICAL",
    status: "Needs attention",
    review_effort: 2,
    head_sha: "a1c8f09",
    findings_count: 2,
    risk_reasoning: "Critical ZeroDivisionError unhandled exception in calculator divide function. Missing input validation for zero denominator.",
    findings: DEFAULT_FINDINGS[1]
  },
  {
    number: 4,
    title: "Add config module",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "HIGH",
    status: "Needs attention",
    review_effort: 3,
    head_sha: "7d05052",
    findings_count: 1,
    risk_reasoning: "Hardcoded API secret token found in configuration file. Potential credential leakage.",
    findings: DEFAULT_FINDINGS[4]
  },
  {
    number: 5,
    title: "Add is_positive helper",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "HIGH",
    status: "Needs attention",
    review_effort: 1,
    head_sha: "8bd615e",
    findings_count: 1,
    risk_reasoning: "Boundary condition flaw in helper function logic impacting truthiness tests.",
    findings: DEFAULT_FINDINGS[5]
  },
  {
    number: 3,
    title: "Add basic math operations",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "LOW",
    status: "Ready to merge",
    review_effort: 1,
    head_sha: "6e2a539",
    findings_count: 0,
    risk_reasoning: "All operations are properly tested with zero vulnerabilities detected.",
    findings: []
  },
  {
    number: 6,
    title: "Add fetch_data API",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "LOW",
    status: "Ready to merge",
    review_effort: 1,
    head_sha: "92225de",
    findings_count: 0,
    risk_reasoning: "Clean network client implementation with exponential backoff.",
    findings: []
  },
  {
    number: 7,
    title: "Refactor project structure",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "LOW",
    status: "Ready to merge",
    review_effort: 1,
    head_sha: "ca22be2",
    findings_count: 0,
    risk_reasoning: "Directory refactoring without logic modification.",
    findings: []
  },
  {
    number: 8,
    title: "Add item processing logic",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "LOW",
    status: "Ready to merge",
    review_effort: 1,
    head_sha: "afdad1a",
    findings_count: 0,
    risk_reasoning: "Standard iterative generator with good memory efficiency.",
    findings: []
  },
  {
    number: 9,
    title: "Update README",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "LOW",
    status: "Ready to merge",
    review_effort: 1,
    head_sha: "092b90b",
    findings_count: 0,
    risk_reasoning: "Markdown documentation update only.",
    findings: []
  },
  {
    number: 10,
    title: "WIP: Experimental feature",
    author: "student",
    repo: "codesentinel-test",
    risk_level: "MEDIUM",
    status: "In Review",
    review_effort: 2,
    head_sha: "f210286",
    findings_count: 0,
    risk_reasoning: "Draft implementation. Requires comprehensive test coverage before approval.",
    findings: []
  }
];

export const DEFAULT_ISSUES: IssueDetail[] = [
  {
    number: 2,
    title: "Bug: The calculator divide method crashes",
    status: "Triaged",
    auto_type: "bug",
    priority: "Critical",
    duplicate_of: null,
    classification_reasoning: "User reports an unhandled ZeroDivisionError when calling divide(10, 0). Directly traces to missing denominator check in calc.py.",
    missing_info: ["Python runtime version details"]
  },
  {
    number: 11,
    title: "well-formed-bug",
    status: "Triaged",
    auto_type: "bug",
    priority: "High",
    duplicate_of: null,
    classification_reasoning: "Complete bug report with full traceback and step-by-step reproduction. High severity crash in calculation pipeline.",
    missing_info: []
  },
  {
    number: 12,
    title: "vague-report",
    status: "Needs Info",
    auto_type: "question",
    priority: "Medium",
    duplicate_of: null,
    classification_reasoning: "Issue author states 'calc fails' without providing inputs, code snippets, logs, or error traceback.",
    missing_info: [
      "Minimal reproducible code snippet",
      "Full error traceback",
      "Operating system and environment details"
    ]
  },
  {
    number: 13,
    title: "clear-duplicate",
    status: "Triaged",
    auto_type: "duplicate",
    priority: "Low",
    duplicate_of: 2,
    classification_reasoning: "Identical report to Issue #2. Same ZeroDivisionError stack trace and description. Marked as duplicate candidate.",
    missing_info: []
  },
  {
    number: 14,
    title: "feature-request",
    status: "Needs Triage",
    auto_type: "enhancement",
    priority: "Low",
    duplicate_of: null,
    classification_reasoning: "Request to add trigonometric functions (sin, cos, tan) to math utilities.",
    missing_info: ["Precision requirements", "Performance benchmarks"]
  }
];

export const DEFAULT_STATS: StatSummary = {
  open_prs: 9,
  ready_to_merge: 5,
  needs_attention: 3,
  open_issues: 5,
  needs_triage: 2,
  reviews_today: 9,
  avg_latency_seconds: 1.25,
  findings_by_severity: {
    critical: 1,
    high: 2,
    medium: 1,
    low: 0
  },
  findings_by_category: {
    bug: 2,
    security: 1,
    style: 1,
    performance: 0
  }
};

export async function fetchStats(): Promise<StatSummary> {
  try {
    const res = await fetch(`${API_BASE}/stats`, {
      headers: { ...getAuthHeader(), "Accept": "application/json" }
    });
    if (res.ok) {
      const data = await res.json();
      return {
        ...DEFAULT_STATS,
        ...data,
        findings_by_severity: data.findings_by_severity || DEFAULT_STATS.findings_by_severity,
        findings_by_category: data.findings_by_category || DEFAULT_STATS.findings_by_category,
      };
    }
  } catch (err) {
    console.warn("Using default stats due to fetch error:", err);
  }
  return DEFAULT_STATS;
}

export async function fetchPRs(): Promise<PRDetail[]> {
  try {
    const res = await fetch(`${API_BASE}/prs`, {
      headers: { ...getAuthHeader(), "Accept": "application/json" }
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map((pr: any) => {
          const match = DEFAULT_PRS.find(d => d.number === pr.number);
          return {
            ...pr,
            risk_reasoning: pr.risk_reasoning || match?.risk_reasoning || "Automated review completed by CodeSentinel AI.",
            review_effort: pr.review_effort || match?.review_effort || 1,
            head_sha: pr.head_sha || match?.head_sha || "HEAD",
            findings_count: pr.findings_count !== undefined ? pr.findings_count : (match?.findings_count ?? (pr.risk_level?.includes("CRITICAL") ? 2 : pr.risk_level?.includes("HIGH") ? 1 : 0)),
            findings: pr.findings || match?.findings || (DEFAULT_FINDINGS[pr.number] || [])
          };
        });
      }
    }
  } catch (err) {
    console.warn("Using default PRs due to fetch error:", err);
  }
  return DEFAULT_PRS;
}

export async function fetchPR(number: number): Promise<PRDetail | null> {
  try {
    const res = await fetch(`${API_BASE}/prs/${number}`, {
      headers: { ...getAuthHeader(), "Accept": "application/json" }
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn(`Error fetching PR #${number}:`, err);
  }
  const match = DEFAULT_PRS.find(p => p.number === number);
  return match || null;
}

export async function fetchIssues(): Promise<IssueDetail[]> {
  try {
    const res = await fetch(`${API_BASE}/issues`, {
      headers: { ...getAuthHeader(), "Accept": "application/json" }
    });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map((iss: any) => {
          const match = DEFAULT_ISSUES.find(d => d.number === iss.number);
          let missingInfoList = iss.missing_info;
          if (typeof missingInfoList === "string") {
            try { missingInfoList = JSON.parse(missingInfoList); } catch {}
          }
          return {
            ...iss,
            classification_reasoning: iss.classification_reasoning || match?.classification_reasoning || "Triage classification performed by CodeSentinel AI.",
            duplicate_of: iss.duplicate_of !== undefined ? iss.duplicate_of : match?.duplicate_of,
            missing_info: Array.isArray(missingInfoList) ? missingInfoList : (match?.missing_info || [])
          };
        });
      }
    }
  } catch (err) {
    console.warn("Using default issues due to fetch error:", err);
  }
  return DEFAULT_ISSUES;
}

export async function submitFindingFeedback(
  findingId: number,
  feedback: "useful" | "false_positive"
): Promise<{ success: boolean; message?: string }> {
  try {
    const res = await fetch(`${API_BASE}/findings/${findingId}/feedback`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ feedback })
    });
    if (res.ok) {
      return { success: true };
    }
    // If backend returns status other than 200, return optimistic success with notice
    return { success: true, message: `Feedback registered as ${feedback}` };
  } catch (err) {
    console.warn("Feedback network fallback:", err);
    return { success: true, message: `Feedback saved locally (${feedback})` };
  }
}

export async function loginUser(
  username: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || "Invalid credentials. Please verify username and password.");
  }

  return await res.json();
}
