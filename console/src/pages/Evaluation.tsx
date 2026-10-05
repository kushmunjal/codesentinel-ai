import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Evaluation() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Evaluation & Performance</h1>
      <Card>
        <CardHeader>
          <CardTitle>Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            Run an evaluation to see metrics here.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
