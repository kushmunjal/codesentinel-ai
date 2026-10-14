export interface Finding {
  id: number;
  pr_number: number;
  repo: string;
  file: string;
  line: number;
  severity: "low" | "medium" | "high" | "critical" | string;
  category: "security" | "bug" | "performance" | "style" | string;
  explanation: string;
  suggested_fix?: string | null;
  feedback?: "useful" | "false_positive" | null;
  created_at?: string;
}

export interface PRState {
  id?: number;
  number: number;
  title: string;
  author: string;
  repo: string;
  status: string;
  risk_level: string;
  review_effort?: number;
  head_sha?: string | null;
  findings_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PRDetail extends PRState {
  risk_reasoning?: string | null;
  last_reviewed_sha?: string | null;
  findings?: Finding[];
}

export interface IssueState {
  id?: number;
  number: number;
  title: string;
  status: string;
  auto_type: string;
  priority: string;
  duplicate_of?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface IssueDetail extends IssueState {
  classification_reasoning?: string | null;
  missing_info?: string[] | null;
}

export interface StatSummary {
  open_prs: number;
  ready_to_merge: number;
  needs_attention: number;
  open_issues: number;
  needs_triage: number;
  reviews_today: number;
  avg_latency_seconds?: number;
  findings_by_severity?: Record<string, number>;
  findings_by_category?: Record<string, number>;
}

export interface User {
  username: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}
