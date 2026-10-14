import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { GitPullRequest, GitMerge, AlertTriangle, CheckCircle, Clock } from "lucide-react";

export default function PullRequests() {
  const [prs, setPrs] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8080/api/prs")
      .then(res => res.json())
      .then(data => setPrs(data))
      .catch(console.error);
  }, []);

  const getRiskIcon = (risk: string) => {
    if (risk.includes("HIGH") || risk.includes("CRITICAL")) return <AlertTriangle className="w-4 h-4 text-destructive" />;
    if (risk.includes("LOW")) return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    return <AlertTriangle className="w-4 h-4 text-amber-500" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <GitPullRequest className="w-8 h-8 text-primary" />
        <h1 className="text-3xl font-bold tracking-tight">Pull Requests</h1>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Active Reviews</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {prs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No PRs reviewed yet.</div>
            ) : prs.map((pr: any) => (
              <Dialog key={pr.number}>
                <DialogTrigger asChild>
                  <div className="flex items-center justify-between border-b pb-4 cursor-pointer hover:bg-muted/50 p-2 rounded-md transition-colors">
                    <div className="flex items-start space-x-3">
                      <div className="mt-1">{getRiskIcon(pr.risk_level)}</div>
                      <div>
                        <h3 className="font-semibold text-lg text-primary hover:underline">#{pr.number} {pr.title}</h3>
                        <p className="text-sm text-muted-foreground flex items-center space-x-1">
                           <span>{pr.repo}</span> <span>•</span> <span>by {pr.author}</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant={pr.risk_level.includes("HIGH") ? "destructive" : "outline"} className="uppercase">
                        {pr.risk_level} Risk
                      </Badge>
                      <Badge variant={pr.status === "Ready to merge" ? "default" : "secondary"}>
                        {pr.status === "Ready to merge" ? <GitMerge className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                        {pr.status}
                      </Badge>
                    </div>
                  </div>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[600px]">
                  <DialogHeader>
                    <DialogTitle className="text-xl flex items-center space-x-2">
                      <GitPullRequest className="w-5 h-5" />
                      <span>PR #{pr.number}: {pr.title}</span>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">Author</p>
                        <p className="font-medium">{pr.author}</p>
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">Repository</p>
                        <p className="font-medium">{pr.repo}</p>
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">AI Risk Assessment</p>
                        <p className="font-medium flex items-center space-x-1">{getRiskIcon(pr.risk_level)} <span>{pr.risk_level}</span></p>
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">Current Status</p>
                        <p className="font-medium">{pr.status}</p>
                      </div>
                    </div>
                    <div className="border-t pt-4">
                       <h4 className="font-semibold mb-2">AI Review Summary</h4>
                       <p className="text-sm text-muted-foreground bg-muted/50 p-4 rounded-md border">
                         The CodeSentinel AI has analyzed this PR. {pr.risk_level.includes("HIGH") ? "Critical issues were detected that need immediate attention before merging." : "Code looks clean and meets standard best practices. Approved for merge."}
                       </p>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
