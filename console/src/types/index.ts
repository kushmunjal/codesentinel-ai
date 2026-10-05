export interface PRState {
  id: number;
  number: number;
  title: string;
  author: string;
  repo: string;
  status: string;
  risk_level: string;
  created_at: string;
  updated_at: string;
}

export interface IssueState {
  id: number;
  number: number;
  title: string;
  status: string;
  auto_type: string;
  priority: string;
  created_at: string;
  updated_at: string;
}

export interface StatSummary {
  open_prs: number;
  ready_to_merge: number;
  needs_attention: number;
  open_issues: number;
  needs_triage: number;
  reviews_today: number;
}
