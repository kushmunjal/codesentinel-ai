import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Activity() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Activity Log</h1>
      <Card>
        <CardHeader>
          <CardTitle>Audit Trail</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            Log will appear here as the bot operates.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
