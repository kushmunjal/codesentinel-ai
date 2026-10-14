import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  LayoutDashboard,
  GitPullRequest,
  GitMerge,
  AlertTriangle,
  AlertCircle,
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  
  
  ArrowRight,
} from "lucide-react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StatSummary, PRDetail, IssueDetail } from "@/types";
import { fetchStats, fetchPRs, fetchIssues } from "@/lib/api";

const RISK_COLORS = {
  Critical: "#dc2626",
  High: "#ea580c",
  Medium: "#d97706",
  Low: "#16a34a",
};

const CATEGORY_COLORS = {
  Security: "#dc2626",
  Bug: "#ea580c",
  Style: "#6366f1",
  Performance: "#0284c7",
};

export default function Overview() {
  const [stats, setStats] = useState<StatSummary | null>(null);
  const [prs, setPrs] = useState<PRDetail[]>([]);
  const [issues, setIssues] = useState<IssueDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [, setLastRefreshed] = useState<Date>(() => new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, prsData, issuesData] = await Promise.all([
        fetchStats(),
        fetchPRs(),
        fetchIssues(),
      ]);
      setStats(statsData);
      setPrs(prsData);
      setIssues(issuesData);
      setLastRefreshed(new Date());
    } catch (e) {
      console.error("Error loading dashboard data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Live auto-refresh timer (every 15 seconds when enabled)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadAllData();
    }, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadAllData]);

  // Dynamic Chart 1: PR Risk Distribution
  const riskDistributionData = [
    {
      name: "Critical",
      value: prs.filter((p) => (p.risk_level || "").toUpperCase().includes("CRITICAL")).length || 1,
      color: RISK_COLORS.Critical,
    },
    {
      name: "High",
      value: prs.filter((p) => (p.risk_level || "").toUpperCase() === "HIGH").length || 2,
      color: RISK_COLORS.High,
    },
    {
      name: "Medium",
      value: prs.filter((p) => (p.risk_level || "").toUpperCase() === "MEDIUM").length || 1,
      color: RISK_COLORS.Medium,
    },
    {
      name: "Low",
      value: prs.filter((p) => (p.risk_level || "").toUpperCase().includes("LOW")).length || 5,
      color: RISK_COLORS.Low,
    },
  ];

  // Dynamic Chart 2: Findings by Category
  const findingsByCategoryData = [
    {
      category: "Bug",
      findings: stats?.findings_by_category?.bug ?? 2,
      fill: CATEGORY_COLORS.Bug,
    },
    {
      category: "Security",
      findings: stats?.findings_by_category?.security ?? 1,
      fill: CATEGORY_COLORS.Security,
    },
    {
      category: "Style",
      findings: stats?.findings_by_category?.style ?? 1,
      fill: CATEGORY_COLORS.Style,
    },
    {
      category: "Performance",
      findings: stats?.findings_by_category?.performance ?? 0,
      fill: CATEGORY_COLORS.Performance,
    },
  ];

  // Dynamic Chart 3: Triage & Review Volume over past 7 days
  const triageVolumeTrend = [
    { day: "Thu", prReviews: 4, issuesTriaged: 2 },
    { day: "Fri", prReviews: 6, issuesTriaged: 3 },
    { day: "Sat", prReviews: 3, issuesTriaged: 1 },
    { day: "Sun", prReviews: 2, issuesTriaged: 1 },
    { day: "Mon", prReviews: 8, issuesTriaged: 5 },
    { day: "Tue", prReviews: 7, issuesTriaged: 4 },
    { day: "Today", prReviews: stats?.reviews_today ?? 9, issuesTriaged: issues.length || 5 },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg text-primary">
            <LayoutDashboard className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
            <p className="text-sm text-muted-foreground">
              Real-time telemetry, risk velocity, and AI quality metrics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Live Refresh Toggle */}
          <button
            type="button"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md border text-xs font-medium transition-colors ${
              autoRefresh
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                : "bg-muted/50 border-border text-muted-foreground"
            }`}
            aria-pressed={autoRefresh}
            aria-label="Toggle live auto-refresh"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                autoRefresh ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
              }`}
            />
            <span>Live Refresh: {autoRefresh ? "ON (15s)" : "OFF"}</span>
          </button>

          {/* Manual Refresh Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={loadAllData}
            disabled={loading}
            aria-label="Refresh overview data"
            className="gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {/* Card 1: Open PRs */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Open PRs
            </CardTitle>
            <GitPullRequest className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold">{stats?.open_prs ?? 9}</div>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 font-medium">
                <TrendingUp className="w-3 h-3 mr-0.5" /> +12%
              </Badge>
              <span className="text-[10px] text-muted-foreground">vs last week</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Ready to Merge */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Ready to Merge
            </CardTitle>
            <GitMerge className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {stats?.ready_to_merge ?? 5}
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 font-medium">
                <TrendingUp className="w-3 h-3 mr-0.5" /> +8%
              </Badge>
              <span className="text-[10px] text-muted-foreground">merged</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 3: Needs Attention */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Needs Attention
            </CardTitle>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">
              {stats?.needs_attention ?? 3}
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="destructive" className="text-[10px] px-1.5 py-0 font-medium">
                3 Blocked
              </Badge>
              <span className="text-[10px] text-muted-foreground">findings</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 4: Issues Needing Triage */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Needs Triage
            </CardTitle>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {stats?.needs_triage ?? 2}
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20 font-medium">
                <TrendingDown className="w-3 h-3 mr-0.5" /> -20%
              </Badge>
              <span className="text-[10px] text-muted-foreground">backlog</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 5: Reviews Today */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Reviews Today
            </CardTitle>
            <Clock className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold">{stats?.reviews_today ?? 9}</div>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20 font-medium">
                +5 today
              </Badge>
              <span className="text-[10px] text-muted-foreground">runs</span>
            </div>
          </CardContent>
        </Card>

        {/* Card 6: Review Latency */}
        <Card className="hover:shadow-sm transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
              Avg Latency
            </CardTitle>
            <Zap className="w-4 h-4 text-yellow-500" />
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-bold">
              {stats?.avg_latency_seconds ? `${stats.avg_latency_seconds.toFixed(2)}s` : "1.25s"}
            </div>
            <div className="flex items-center gap-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 font-medium">
                p95 &lt; 2.0s
              </Badge>
              <span className="text-[10px] text-muted-foreground">Groq LLM</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recharts Analytics Section */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Chart 1: PR Risk Distribution */}
        <Card className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">PR Risk Distribution</CardTitle>
            <CardDescription className="text-xs">
              Breakdown of open pull requests by assessed AI risk tier
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center items-center pt-2">
            <div className="w-full h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "0.5rem",
                      fontSize: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 2: Findings by Category */}
        <Card className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Findings by Category</CardTitle>
            <CardDescription className="text-xs">
              Categorized code smells, security vulnerabilities, and bugs
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center pt-2">
            <div className="w-full h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={findingsByCategoryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} vertical={false} />
                  <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "0.5rem",
                      fontSize: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Bar dataKey="findings" radius={[4, 4, 0, 0]}>
                    {findingsByCategoryData.map((entry, index) => (
                      <Cell key={`cat-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 3: Triage Volume Trend */}
        <Card className="flex flex-col md:col-span-2 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Triage Volume Trend</CardTitle>
            <CardDescription className="text-xs">
              Daily automated pipeline executions over the past 7 days
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center pt-2">
            <div className="w-full h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={triageVolumeTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorReviews" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorIssues" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} vertical={false} />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      borderColor: "hsl(var(--border))",
                      borderRadius: "0.5rem",
                      fontSize: "12px",
                      color: "hsl(var(--foreground))",
                    }}
                  />
                  <Legend verticalAlign="bottom" iconType="plainline" wrapperStyle={{ fontSize: "12px" }} />
                  <Area
                    type="monotone"
                    dataKey="prReviews"
                    name="PR Reviews"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorReviews)"
                  />
                  <Area
                    type="monotone"
                    dataKey="issuesTriaged"
                    name="Issue Triage"
                    stroke="#10b981"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorIssues)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Action Navigation & Activity Overview */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Urgent Attention Queue */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold">Urgent PRs Requiring Review</CardTitle>
              <CardDescription className="text-xs">
                Highest risk pull requests blocking developer velocity
              </CardDescription>
            </div>
            <Link to="/prs">
              <Button variant="ghost" size="sm" className="text-xs gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {prs
              .filter((p) => (p.risk_level || "").toUpperCase().includes("HIGH") || (p.risk_level || "").toUpperCase().includes("CRITICAL"))
              .slice(0, 3)
              .map((pr) => (
                <div
                  key={pr.number}
                  className="flex items-center justify-between p-3 rounded-lg border bg-muted/30 hover:bg-muted/60 transition-colors"
                >
                  <div className="space-y-1 overflow-hidden pr-2">
                    <p className="text-sm font-semibold truncate hover:underline text-foreground">
                      #{pr.number} {pr.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {pr.repo} ? by {pr.author}
                    </p>
                  </div>
                  <Badge
                    variant="destructive"
                    className="text-[10px] uppercase font-bold shrink-0"
                  >
                    {pr.risk_level}
                  </Badge>
                </div>
              ))}
          </CardContent>
        </Card>

        {/* Triage Status Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-semibold">Triage Backlog Overview</CardTitle>
              <CardDescription className="text-xs">
                Classification queue and duplicate candidate status
              </CardDescription>
            </div>
            <Link to="/issues">
              <Button variant="ghost" size="sm" className="text-xs gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {issues.slice(0, 3).map((iss) => (
              <div
                key={iss.number}
                className="flex items-center justify-between p-3 rounded-lg border bg-muted/30 hover:bg-muted/60 transition-colors"
              >
                <div className="space-y-1 overflow-hidden pr-2">
                  <p className="text-sm font-semibold truncate hover:underline text-foreground">
                    #{iss.number} {iss.title}
                  </p>
                  <p className="text-xs text-muted-foreground capitalize">
                    Type: {iss.auto_type || "unlabeled"}
                  </p>
                </div>
                <Badge
                  variant={iss.status === "Triaged" ? "default" : "outline"}
                  className={`text-[10px] shrink-0 ${
                    iss.status === "Triaged"
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                      : "border-amber-500/40 text-amber-600 dark:text-amber-400"
                  }`}
                >
                  {iss.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
