import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertCircle, Tag, CheckCircle2, MessageSquare, Bug, Lightbulb, Copy } from "lucide-react";

export default function Issues() {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8080/api/issues")
      .then(res => res.json())
      .then(data => setIssues(data))
      .catch(console.error);
  }, []);

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'bug': return <Bug className="w-4 h-4 text-destructive" />;
      case 'enhancement': return <Lightbulb className="w-4 h-4 text-amber-500" />;
      case 'duplicate': return <Copy className="w-4 h-4 text-muted-foreground" />;
      default: return <MessageSquare className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-8 h-8 text-primary" />
        <h1 className="text-3xl font-bold tracking-tight">Issues & Triage</h1>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>AI Triage Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {issues.length === 0 ? (
               <div className="text-center py-8 text-muted-foreground">No issues tracked yet.</div>
            ) : issues.map((iss: any) => (
              <Dialog key={iss.number}>
                <DialogTrigger asChild>
                  <div className="flex items-center justify-between border-b pb-4 cursor-pointer hover:bg-muted/50 p-2 rounded-md transition-colors">
                    <div className="flex items-start space-x-3">
                      <div className="mt-1">{getTypeIcon(iss.auto_type)}</div>
                      <div>
                        <h3 className="font-semibold text-lg text-primary hover:underline">#{iss.number} {iss.title}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                           <Badge variant="outline" className="text-xs font-normal bg-muted">
                             <Tag className="w-3 h-3 mr-1" /> {iss.auto_type || 'unlabeled'}
                           </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Badge variant={iss.priority === "High" ? "destructive" : iss.priority === "Medium" ? "default" : "secondary"}>
                        {iss.priority} Priority
                      </Badge>
                      <Badge variant={iss.status === "Triaged" ? "default" : "outline"} className={iss.status === "Triaged" ? "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20" : ""}>
                        {iss.status === "Triaged" && <CheckCircle2 className="w-3 h-3 mr-1" />}
                        {iss.status}
                      </Badge>
                    </div>
                  </div>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[600px]">
                  <DialogHeader>
                    <DialogTitle className="text-xl flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5" />
                      <span>Issue #{iss.number}: {iss.title}</span>
                    </DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">AI Auto-Label</p>
                        <p className="font-medium flex items-center space-x-1 mt-1">{getTypeIcon(iss.auto_type)} <span className="capitalize">{iss.auto_type || 'unknown'}</span></p>
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">AI Priority Assessment</p>
                        <p className="font-medium mt-1">{iss.priority}</p>
                      </div>
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase font-semibold">Current Status</p>
                        <p className="font-medium mt-1">{iss.status}</p>
                      </div>
                    </div>
                    <div className="border-t pt-4">
                       <h4 className="font-semibold mb-2">CodeSentinel Actions Taken</h4>
                       <ul className="space-y-2 text-sm text-muted-foreground">
                          <li className="flex items-center space-x-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span>Analyzed issue title and body</span>
                          </li>
                          <li className="flex items-center space-x-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span>Checked against past {iss.auto_type === 'duplicate' ? 'duplicate' : 'similar'} issues</span>
                          </li>
                          <li className="flex items-center space-x-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <span>Applied `{iss.auto_type}` label automatically</span>
                          </li>
                       </ul>
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
