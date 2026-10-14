import { useEffect, useState, useMemo } from "react";
import {
  GitPullRequest,
  GitMerge,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Download,
  Filter,
  FileCode,
  ThumbsUp,
  ThumbsDown,
  X,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { PRDetail, Finding } from "@/types";
import { fetchPRs, submitFindingFeedback } from "@/lib/api";

export default function PullRequests() {
  const [prs, setPrs] = useState<PRDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [repoFilter, setRepoFilter] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // Selected PR for detail dialog
  const [selectedPR, setSelectedPR] = useState<PRDetail | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Feedback states tracked per finding ID
  const [feedbackState, setFeedbackState] = useState<Record<number, "useful" | "false_positive">>({});
  const [feedbackLoading, setFeedbackLoading] = useState<Record<number, boolean>>({});

  const loadData = async () => {
    setLoading(true);
    const data = await fetchPRs();
    setPrs(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  // Distinct repositories
  const repositories = useMemo(() => {
    const set = new Set<string>();
    prs.forEach((pr) => {
      if (pr.repo) set.add(pr.repo);
    });
    return Array.from(set);
  }, [prs]);

  // Filtered PR list
  const filteredPRs = useMemo(() => {
    return prs.filter((pr) => {
      // Search matching number, title, author, repo
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchesNumber = pr.number.toString().includes(query.replace("#", ""));
        const matchesTitle = pr.title.toLowerCase().includes(query);
        const matchesAuthor = pr.author.toLowerCase().includes(query);
        const matchesRepo = pr.repo.toLowerCase().includes(query);
        if (!matchesNumber && !matchesTitle && !matchesAuthor && !matchesRepo) {
          return false;
        }
      }

      // Severity / Risk filter
      if (severityFilter !== "ALL") {
        const prRisk = (pr.risk_level || "").toUpperCase();
        if (!prRisk.includes(severityFilter)) {
          return false;
        }
      }

      // Status filter
      if (statusFilter !== "ALL") {
        if (pr.status.toLowerCase() !== statusFilter.toLowerCase()) {
          return false;
        }
      }

      // Repo filter
      if (repoFilter !== "ALL") {
        if (pr.repo !== repoFilter) {
          return false;
        }
      }

      return true;
    });
  }, [prs, searchQuery, severityFilter, statusFilter, repoFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredPRs.length / pageSize));
  const paginatedPRs = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredPRs.slice(startIndex, startIndex + pageSize);
  }, [filteredPRs, currentPage, pageSize]);

  // Reset to page 1 on filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, severityFilter, statusFilter, repoFilter]);

  const handleOpenDialog = (pr: PRDetail) => {
    setSelectedPR(pr);
    setIsDialogOpen(true);
  };

  const handleFeedback = async (findingId: number, type: "useful" | "false_positive") => {
    setFeedbackLoading((prev) => ({ ...prev, [findingId]: true }));
    try {
      await submitFindingFeedback(findingId, type);
      setFeedbackState((prev) => ({ ...prev, [findingId]: type }));
    } catch (e) {
      console.error("Feedback error:", e);
    } finally {
      setFeedbackLoading((prev) => ({ ...prev, [findingId]: false }));
    }
  };

  const exportToCSV = () => {
    const headers = ["Number", "Title", "Author", "Repository", "Risk Level", "Status", "Review Effort", "Findings Count", "Head SHA"];
    const rows = filteredPRs.map((pr) => [
      pr.number,
      `"${pr.title.replace(/"/g, '""')}"`,
      `"${pr.author}"`,
      `"${pr.repo}"`,
      `"${pr.risk_level}"`,
      `"${pr.status}"`,
      pr.review_effort ?? 1,
      pr.findings_count ?? (pr.findings ? pr.findings.length : 0),
      `"${pr.head_sha || ""}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `codesentinel_pull_requests_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearFilters = () => {
    setSearchQuery("");
    setSeverityFilter("ALL");
    setStatusFilter("ALL");
    setRepoFilter("ALL");
  };

  const hasActiveFilters = searchQuery !== "" || severityFilter !== "ALL" || statusFilter !== "ALL" || repoFilter !== "ALL";

  const getRiskBadge = (risk: string) => {
    const r = (risk || "").toUpperCase();
    if (r.includes("CRITICAL")) {
      return (
        <Badge variant="destructive" className="font-semibold gap-1 bg-red-600 hover:bg-red-700">
          <AlertTriangle className="w-3 h-3" />
          <span>CRITICAL</span>
        </Badge>
      );
    }
    if (r.includes("HIGH")) {
      return (
        <Badge variant="destructive" className="font-semibold gap-1 bg-orange-600 hover:bg-orange-700">
          <AlertTriangle className="w-3 h-3" />
          <span>HIGH</span>
        </Badge>
      );
    }
    if (r.includes("MEDIUM")) {
      return (
        <Badge variant="secondary" className="font-semibold gap-1 bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3" />
          <span>MEDIUM</span>
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="font-semibold gap-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
        <CheckCircle className="w-3 h-3" />
        <span>LOW</span>
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    if (status === "Ready to merge") {
      return (
        <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
          <GitMerge className="w-3 h-3" />
          <span>Ready to merge</span>
        </Badge>
      );
    }
    if (status === "Needs attention") {
      return (
        <Badge variant="destructive" className="gap-1">
          <AlertTriangle className="w-3 h-3" />
          <span>Needs attention</span>
        </Badge>
      );
    }
    return (
      <Badge variant="secondary" className="gap-1">
        <Clock className="w-3 h-3" />
        <span>{status}</span>
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg text-primary">
            <GitPullRequest className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Pull Requests</h1>
            <p className="text-sm text-muted-foreground">
              Autonomous risk analysis, code findings, and review automation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            aria-label="Refresh pull requests"
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={exportToCSV}
            disabled={filteredPRs.length === 0}
            className="gap-2"
            aria-label="Export pull requests to CSV"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Controls Bar: Search & Filters */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search PR #, title, author..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9"
                aria-label="Search pull requests by number, title, or author"
              />
            </div>

            {/* Severity Filter */}
            <div>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by severity or risk level"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by review status"
              >
                <option value="ALL">All Statuses</option>
                <option value="Ready to merge">Ready to merge</option>
                <option value="Needs attention">Needs attention</option>
                <option value="In Review">In Review</option>
                <option value="Skipped">Skipped</option>
              </select>
            </div>

            {/* Repo Filter */}
            <div>
              <select
                value={repoFilter}
                onChange={(e) => setRepoFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by repository"
              >
                <option value="ALL">All Repositories</option>
                {repositories.map((repo) => (
                  <option key={repo} value={repo}>
                    {repo}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Filter Pills */}
          {hasActiveFilters && (
            <div className="flex items-center justify-between pt-2 border-t text-xs text-muted-foreground">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5" /> Active Filters:
                </span>
                {searchQuery && (
                  <Badge variant="secondary" className="text-xs">
                    Search: "{searchQuery}"
                  </Badge>
                )}
                {severityFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Risk: {severityFilter}
                  </Badge>
                )}
                {statusFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Status: {statusFilter}
                  </Badge>
                )}
                {repoFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Repo: {repoFilter}
                  </Badge>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="w-3 h-3 mr-1" />
                Clear Filters
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* PR Table Card */}
      <Card>
        <CardHeader className="p-4 sm:p-6 pb-2 sm:pb-3 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Pull Request Reviews</CardTitle>
            <CardDescription>
              Showing {filteredPRs.length} of {prs.length} pull requests
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">PR #</TableHead>
                  <TableHead className="min-w-[280px]">Title</TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Author</TableHead>
                  <TableHead>Risk Level</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Findings</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedPRs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                      {loading ? "Loading pull requests..." : "No pull requests match the current filters."}
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedPRs.map((pr) => {
                    const findingsCount = pr.findings_count ?? (pr.findings ? pr.findings.length : 0);
                    return (
                      <TableRow
                        key={pr.number}
                        className="cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => handleOpenDialog(pr)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            handleOpenDialog(pr);
                          }
                        }}
                        aria-label={`View details for pull request number ${pr.number}`}
                      >
                        <TableCell className="font-semibold text-primary">#{pr.number}</TableCell>
                        <TableCell>
                          <div className="font-medium text-foreground hover:underline">
                            {pr.title}
                          </div>
                          {pr.head_sha && (
                            <div className="text-xs text-muted-foreground font-mono">
                              commit: {pr.head_sha}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{pr.repo}</TableCell>
                        <TableCell className="text-xs">{pr.author}</TableCell>
                        <TableCell>{getRiskBadge(pr.risk_level)}</TableCell>
                        <TableCell>{getStatusBadge(pr.status)}</TableCell>
                        <TableCell>
                          {findingsCount > 0 ? (
                            <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-xs">
                              {findingsCount} finding{findingsCount > 1 ? "s" : ""}
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                              Clean
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDialog(pr);
                            }}
                            className="h-8 text-xs font-medium"
                          >
                            Review Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination Footer */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t text-sm text-muted-foreground">
              <div>
                Showing {(currentPage - 1) * pageSize + 1} to{" "}
                {Math.min(currentPage * pageSize, filteredPRs.length)} of {filteredPRs.length} entries
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Previous
                </Button>
                <div className="text-xs font-medium px-2">
                  Page {currentPage} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  aria-label="Next page"
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed PR Drawer / Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        {selectedPR && (
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader className="space-y-1">
              <div className="flex items-center justify-between gap-2 pr-6">
                <DialogTitle className="text-xl flex items-center gap-2 font-bold">
                  <GitPullRequest className="w-5 h-5 text-primary" />
                  <span>
                    PR #{selectedPR.number}: {selectedPR.title}
                  </span>
                </DialogTitle>
              </div>
              <DialogDescription>
                Repository: <strong>{selectedPR.repo}</strong> ? Author: <strong>{selectedPR.author}</strong>
                {selectedPR.head_sha && ` ? SHA: ${selectedPR.head_sha}`}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-5 py-2">
              {/* Top metadata grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Risk Level</span>
                  <div className="mt-1">{getRiskBadge(selectedPR.risk_level)}</div>
                </div>
                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Review Status</span>
                  <div className="mt-1">{getStatusBadge(selectedPR.status)}</div>
                </div>
                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Review Effort</span>
                  <p className="font-semibold text-sm mt-1">{selectedPR.review_effort ?? 1} / 5</p>
                </div>
                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Findings Count</span>
                  <p className="font-semibold text-sm mt-1">
                    {(selectedPR.findings?.length ?? selectedPR.findings_count) ?? 0}
                  </p>
                </div>
              </div>

              {/* Risk Reasoning */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-primary" />
                  <span>AI Risk Reasoning</span>
                </h4>
                <div className="p-4 rounded-lg bg-muted/40 border text-sm leading-relaxed text-foreground/90">
                  {selectedPR.risk_reasoning || "Automated review completed by CodeSentinel AI engine."}
                </div>
              </div>

              {/* Findings Breakdown */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between border-b pb-2">
                  <h4 className="font-semibold text-sm">
                    Detailed Code Findings ({selectedPR.findings?.length || 0})
                  </h4>
                  <span className="text-xs text-muted-foreground">
                    Grouped by severity & category
                  </span>
                </div>

                {!selectedPR.findings || selectedPR.findings.length === 0 ? (
                  <div className="p-6 text-center rounded-lg border border-dashed text-muted-foreground space-y-2">
                    <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto" />
                    <p className="font-medium text-foreground">No Issues or Code Smells Detected</p>
                    <p className="text-xs">This pull request adheres to security, performance, and code quality standards.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {selectedPR.findings.map((finding: Finding) => {
                      const currentFeedback = feedbackState[finding.id] || finding.feedback;
                      const isFeedbackSubmitting = feedbackLoading[finding.id];

                      return (
                        <div
                          key={finding.id}
                          className="p-4 rounded-lg border bg-card/60 space-y-3 transition-colors hover:border-primary/40"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted">
                                <FileCode className="w-3.5 h-3.5 text-primary" />
                                {finding.file}:{finding.line}
                              </span>
                              <Badge
                                variant={
                                  finding.severity === "critical"
                                    ? "destructive"
                                    : finding.severity === "high"
                                    ? "destructive"
                                    : "secondary"
                                }
                                className="text-[10px] uppercase font-bold"
                              >
                                {finding.severity}
                              </Badge>
                              <Badge variant="outline" className="text-[10px] uppercase">
                                {finding.category}
                              </Badge>
                            </div>

                            {/* Feedback action buttons */}
                            <div className="flex items-center gap-1.5">
                              {currentFeedback ? (
                                <Badge
                                  variant="outline"
                                  className={`text-xs gap-1 ${
                                    currentFeedback === "useful"
                                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                                      : "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30"
                                  }`}
                                >
                                  {currentFeedback === "useful" ? (
                                    <>
                                      <ThumbsUp className="w-3 h-3" /> Marked Useful
                                    </>
                                  ) : (
                                    <>
                                      <ThumbsDown className="w-3 h-3" /> False Positive
                                    </>
                                  )}
                                </Badge>
                              ) : (
                                <>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={isFeedbackSubmitting}
                                    onClick={() => handleFeedback(finding.id, "useful")}
                                    className="h-7 px-2 text-xs gap-1 hover:text-emerald-600 hover:border-emerald-500/40"
                                    aria-label="Mark finding as useful"
                                  >
                                    <ThumbsUp className="w-3 h-3" />
                                    <span>Useful</span>
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={isFeedbackSubmitting}
                                    onClick={() => handleFeedback(finding.id, "false_positive")}
                                    className="h-7 px-2 text-xs gap-1 hover:text-rose-600 hover:border-rose-500/40"
                                    aria-label="Mark finding as false positive"
                                  >
                                    <ThumbsDown className="w-3 h-3" />
                                    <span>False Positive</span>
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Explanation */}
                          <p className="text-sm text-foreground/90 leading-normal">
                            {finding.explanation}
                          </p>

                          {/* Suggested Fix Code Block */}
                          {finding.suggested_fix && (
                            <div className="space-y-1">
                              <span className="text-[11px] font-semibold text-muted-foreground uppercase">
                                Suggested Fix:
                              </span>
                              <pre className="p-3 bg-muted/80 rounded-md font-mono text-xs overflow-x-auto text-foreground border">
                                <code>{finding.suggested_fix}</code>
                              </pre>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}
