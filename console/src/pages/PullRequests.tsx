import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function PullRequests() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Pull Requests</h1>
      <Card>
        <CardHeader>
          <CardTitle>Open PRs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            No PRs reviewed yet ? connect a repo to get started.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
