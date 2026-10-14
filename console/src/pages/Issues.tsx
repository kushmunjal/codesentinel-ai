import { useEffect, useState, useMemo } from "react";
import {
  AlertCircle,
  
  CheckCircle2,
  MessageSquare,
  Bug,
  Lightbulb,
  Copy,
  Search,
  Download,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  HelpCircle,
  FileQuestion,
  Layers,
  AlertTriangle,
  Info
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
import type { IssueDetail } from "@/types";
import { fetchIssues } from "@/lib/api";

export default function Issues() {
  const [issues, setIssues] = useState<IssueDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  const [selectedIssue, setSelectedIssue] = useState<IssueDetail | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    const data = await fetchIssues();
    setIssues(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case "bug":
        return <Bug className="w-4 h-4 text-destructive shrink-0" />;
      case "enhancement":
        return <Lightbulb className="w-4 h-4 text-amber-500 shrink-0" />;
      case "duplicate":
        return <Copy className="w-4 h-4 text-purple-500 shrink-0" />;
      default:
        return <MessageSquare className="w-4 h-4 text-blue-500 shrink-0" />;
    }
  };

  const getPriorityBadge = (priority: string) => {
    const p = (priority || "").toLowerCase();
    if (p === "critical") {
      return (
        <Badge variant="destructive" className="font-semibold bg-red-600 hover:bg-red-700">
          Critical Priority
        </Badge>
      );
    }
    if (p === "high") {
      return (
        <Badge variant="destructive" className="font-semibold bg-orange-600 hover:bg-orange-700">
          High Priority
        </Badge>
      );
    }
    if (p === "medium") {
      return (
        <Badge variant="secondary" className="font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
          Medium Priority
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="font-normal text-muted-foreground">
        Low Priority
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    const s = (status || "").toLowerCase();
    if (s.includes("triaged")) {
      return (
        <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1">
          <CheckCircle2 className="w-3 h-3" />
          <span>Triaged</span>
        </Badge>
      );
    }
    if (s.includes("needs info")) {
      return (
        <Badge variant="secondary" className="bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/30 gap-1">
          <Info className="w-3 h-3" />
          <span>Needs Info</span>
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="gap-1 border-amber-500/40 text-amber-600 dark:text-amber-400">
        <HelpCircle className="w-3 h-3" />
        <span>{status}</span>
      </Badge>
    );
  };

  // Filtered issues
  const filteredIssues = useMemo(() => {
    return issues.filter((iss) => {
      // Search
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchesNum = iss.number.toString().includes(query.replace("#", ""));
        const matchesTitle = iss.title.toLowerCase().includes(query);
        const matchesType = (iss.auto_type || "").toLowerCase().includes(query);
        const matchesPriority = (iss.priority || "").toLowerCase().includes(query);
        if (!matchesNum && !matchesTitle && !matchesType && !matchesPriority) {
          return false;
        }
      }

      // Priority Filter
      if (priorityFilter !== "ALL") {
        if ((iss.priority || "").toLowerCase() !== priorityFilter.toLowerCase()) {
          return false;
        }
      }

      // Status Filter
      if (statusFilter !== "ALL") {
        if ((iss.status || "").toLowerCase() !== statusFilter.toLowerCase()) {
          return false;
        }
      }

      // Type Filter
      if (typeFilter !== "ALL") {
        if ((iss.auto_type || "").toLowerCase() !== typeFilter.toLowerCase()) {
          return false;
        }
      }

      return true;
    });
  }, [issues, searchQuery, priorityFilter, statusFilter, typeFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredIssues.length / pageSize));
  const paginatedIssues = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredIssues.slice(startIndex, startIndex + pageSize);
  }, [filteredIssues, currentPage, pageSize]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, priorityFilter, statusFilter, typeFilter]);

  const handleOpenDialog = (iss: IssueDetail) => {
    setSelectedIssue(iss);
    setIsDialogOpen(true);
  };

  const exportToCSV = () => {
    const headers = ["Number", "Title", "Type", "Priority", "Status", "Duplicate Of", "Missing Info Items", "Triage Reasoning"];
    const rows = filteredIssues.map((iss) => [
      iss.number,
      `"${iss.title.replace(/"/g, '""')}"`,
      `"${iss.auto_type || ""}"`,
      `"${iss.priority || ""}"`,
      `"${iss.status || ""}"`,
      iss.duplicate_of ? iss.duplicate_of : "",
      iss.missing_info ? `"${iss.missing_info.join("; ").replace(/"/g, '""')}"` : '""',
      `"${(iss.classification_reasoning || "").replace(/"/g, '""')}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `codesentinel_issues_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearFilters = () => {
    setSearchQuery("");
    setPriorityFilter("ALL");
    setStatusFilter("ALL");
    setTypeFilter("ALL");
  };

  const hasActiveFilters = searchQuery !== "" || priorityFilter !== "ALL" || statusFilter !== "ALL" || typeFilter !== "ALL";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg text-primary">
            <AlertCircle className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Issues & Triage</h1>
            <p className="text-sm text-muted-foreground">
              Automated classification, duplicate detection, and missing info resolution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            aria-label="Refresh issues list"
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={exportToCSV}
            disabled={filteredIssues.length === 0}
            className="gap-2"
            aria-label="Export issues to CSV"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search issue #, title, type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9"
                aria-label="Search issues by title or number"
              />
            </div>

            {/* Priority Filter */}
            <div>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by priority level"
              >
                <option value="ALL">All Priorities</option>
                <option value="Critical">Critical Priority</option>
                <option value="High">High Priority</option>
                <option value="Medium">Medium Priority</option>
                <option value="Low">Low Priority</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by triage status"
              >
                <option value="ALL">All Statuses</option>
                <option value="Triaged">Triaged</option>
                <option value="Needs Triage">Needs Triage</option>
                <option value="Needs Info">Needs Info</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Filter by issue type"
              >
                <option value="ALL">All Issue Types</option>
                <option value="bug">Bug</option>
                <option value="enhancement">Enhancement</option>
                <option value="question">Question</option>
                <option value="duplicate">Duplicate</option>
              </select>
            </div>
          </div>

          {/* Active Filter Indicators */}
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
                {priorityFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Priority: {priorityFilter}
                  </Badge>
                )}
                {statusFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Status: {statusFilter}
                  </Badge>
                )}
                {typeFilter !== "ALL" && (
                  <Badge variant="secondary" className="text-xs">
                    Type: {typeFilter}
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

      {/* Issues Table */}
      <Card>
        <CardHeader className="p-4 sm:p-6 pb-2 sm:pb-3">
          <CardTitle className="text-lg">Triage Queue</CardTitle>
          <CardDescription>
            Showing {filteredIssues.length} of {issues.length} issues
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Issue #</TableHead>
                  <TableHead className="min-w-[280px]">Title</TableHead>
                  <TableHead>Classification</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Duplicate Of</TableHead>
                  <TableHead>Missing Info</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedIssues.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                      {loading ? "Loading issues..." : "No issues match the selected filters."}
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedIssues.map((iss) => {
                    const missingCount = iss.missing_info ? iss.missing_info.length : 0;

                    return (
                      <TableRow
                        key={iss.number}
                        className="cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => handleOpenDialog(iss)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            handleOpenDialog(iss);
                          }
                        }}
                        aria-label={`View triage details for issue number ${iss.number}`}
                      >
                        <TableCell className="font-semibold text-primary">#{iss.number}</TableCell>
                        <TableCell>
                          <div className="font-medium text-foreground hover:underline">
                            {iss.title}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center gap-1.5 text-xs font-medium capitalize">
                            {getTypeIcon(iss.auto_type)}
                            <span>{iss.auto_type || "unlabeled"}</span>
                          </span>
                        </TableCell>
                        <TableCell>{getPriorityBadge(iss.priority)}</TableCell>
                        <TableCell>{getStatusBadge(iss.status)}</TableCell>
                        <TableCell>
                          {iss.duplicate_of ? (
                            <Badge variant="outline" className="font-mono text-xs gap-1 border-purple-500/30 text-purple-600 dark:text-purple-400 bg-purple-500/10">
                              <Copy className="w-3 h-3" />
                              #{iss.duplicate_of}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">?</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {missingCount > 0 ? (
                            <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30">
                              {missingCount} missing
                            </Badge>
                          ) : (
                            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" /> None
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenDialog(iss);
                            }}
                            className="h-8 text-xs font-medium"
                          >
                            View Triage
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
                {Math.min(currentPage * pageSize, filteredIssues.length)} of {filteredIssues.length} entries
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

      {/* Detailed Issue Drawer / Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        {selectedIssue && (
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader className="space-y-1">
              <DialogTitle className="text-xl flex items-center gap-2 font-bold">
                <AlertCircle className="w-5 h-5 text-primary" />
                <span>Issue #{selectedIssue.number}: {selectedIssue.title}</span>
              </DialogTitle>
              <DialogDescription>
                Automated triage and classification analysis by CodeSentinel
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-5 py-2">
              {/* Metadata chips */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Auto-Type</span>
                  <div className="flex items-center gap-1.5 font-medium text-sm mt-1 capitalize">
                    {getTypeIcon(selectedIssue.auto_type)}
                    <span>{selectedIssue.auto_type || "unlabeled"}</span>
                  </div>
                </div>

                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Priority Badge</span>
                  <div className="mt-1">{getPriorityBadge(selectedIssue.priority)}</div>
                </div>

                <div className="bg-muted/60 p-3 rounded-lg border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">Current Status</span>
                  <div className="mt-1">{getStatusBadge(selectedIssue.status)}</div>
                </div>
              </div>

              {/* Triage Reasoning */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <Layers className="w-4 h-4 text-primary" />
                  <span>AI Triage Reasoning</span>
                </h4>
                <div className="p-4 rounded-lg bg-muted/40 border text-sm leading-relaxed text-foreground/90">
                  {selectedIssue.classification_reasoning || "Analyzed issue content, semantics, and similarities against past repository reports."}
                </div>
              </div>

              {/* Duplicate Candidates */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <Copy className="w-4 h-4 text-primary" />
                  <span>Duplicate Candidates</span>
                </h4>
                {selectedIssue.duplicate_of ? (
                  <div className="p-3 rounded-lg border bg-purple-500/10 border-purple-500/30 flex items-start gap-3">
                    <Copy className="w-4 h-4 text-purple-600 dark:text-purple-400 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-purple-900 dark:text-purple-200">
                        Marked as Duplicate of Issue #{selectedIssue.duplicate_of}
                      </p>
                      <p className="text-xs text-purple-700 dark:text-purple-300 mt-0.5">
                        High semantic and stack-trace similarity detected with primary issue #{selectedIssue.duplicate_of}.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg border bg-muted/30 text-xs text-muted-foreground flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>No duplicate candidate identified. This is a unique issue report.</span>
                  </div>
                )}
              </div>

              {/* Missing Information Checklist */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <FileQuestion className="w-4 h-4 text-primary" />
                  <span>Missing Information Checklist</span>
                </h4>
                {selectedIssue.missing_info && selectedIssue.missing_info.length > 0 ? (
                  <div className="space-y-2">
                    <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-xs text-amber-800 dark:text-amber-200 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                      <span>The issue report is missing {selectedIssue.missing_info.length} critical details required for maintainer reproduction:</span>
                    </div>
                    <ul className="space-y-2">
                      {selectedIssue.missing_info.map((item, idx) => (
                        <li
                          key={idx}
                          className="flex items-center gap-2.5 p-2.5 rounded-md border bg-card/60 text-sm"
                        >
                          <div className="w-4 h-4 rounded border-2 border-amber-500 flex items-center justify-center shrink-0">
                            <span className="w-2 h-2 rounded-xs bg-amber-500"></span>
                          </div>
                          <span className="font-medium text-foreground/90">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <span>All necessary reproduction steps, environment details, and logs were provided by the author.</span>
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
