import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function PullRequests() {
  const [prs, setPrs] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8080/api/prs")
      .then(res => res.json())
      .then(data => setPrs(data))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Pull Requests</h1>
      <Card>
        <CardHeader>
          <CardTitle>Open PRs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {prs.length === 0 ? "No PRs reviewed yet." : prs.map((pr: any) => (
              <div key={pr.number} className="flex items-center justify-between border-b pb-4">
                <div>
                  <h3 className="font-semibold text-lg">#{pr.number} {pr.title}</h3>
                  <p className="text-sm text-muted-foreground">{pr.repo} • {pr.author}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={pr.risk_level.includes("HIGH") ? "destructive" : "default"}>{pr.risk_level}</Badge>
                  <Badge variant={pr.status === "Ready to merge" ? "default" : "secondary"}>{pr.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
