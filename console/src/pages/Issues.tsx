import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Issues() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Issues / Triage</h1>
      <Card>
        <CardHeader>
          <CardTitle>Triage Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            No issues tracked yet.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
