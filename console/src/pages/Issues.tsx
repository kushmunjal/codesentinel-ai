import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function Issues() {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8080/api/issues")
      .then(res => res.json())
      .then(data => setIssues(data))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Issues / Triage</h1>
      <Card>
        <CardHeader>
          <CardTitle>Triage Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {issues.length === 0 ? "No issues tracked yet." : issues.map((iss: any) => (
              <div key={iss.number} className="flex items-center justify-between border-b pb-4">
                <div>
                  <h3 className="font-semibold text-lg">#{iss.number} {iss.title}</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">{iss.auto_type}</Badge>
                  <Badge variant={iss.priority === "High" ? "destructive" : "secondary"}>{iss.priority}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
