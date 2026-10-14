import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GitPullRequest, Lock, User, ShieldCheck, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password) {
      setError("Please enter both username and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await login(username, password);
      if (res.success) {
        navigate("/");
      } else {
        setError(res.error || "Authentication failed. Check credentials.");
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col justify-center items-center bg-background p-4 relative">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-2xl text-primary mb-2 shadow-sm">
            <GitPullRequest className="w-10 h-10" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">CodeSentinel Console</h1>
          <p className="text-sm text-muted-foreground">
            Autonomous PR Review & Issue Triage System
          </p>
        </div>

        {isAuthenticated && user && (
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <CardContent className="pt-6 text-center space-y-3">
              <div className="flex items-center justify-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium">
                <ShieldCheck className="w-5 h-5" />
                <span>Currently signed in as <strong>{user.username}</strong> ({user.role})</span>
              </div>
              <div className="flex justify-center gap-2">
                <Button variant="default" size="sm" onClick={() => navigate("/")}>
                  Go to Dashboard
                </Button>
                <Button variant="outline" size="sm" onClick={logout}>
                  Sign Out
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="shadow-lg border-border">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Maintainer Sign In</CardTitle>
            <CardDescription>
              Enter credentials to access review queue, feedback, and telemetry
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit} noValidate>
            <CardContent className="space-y-4">
              {error && (
                <div
                  role="alert"
                  className="flex items-center gap-2 p-3 text-sm rounded-lg bg-destructive/10 text-destructive border border-destructive/20"
                >
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">
                  Username
                </Label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-3 text-muted-foreground pointer-events-none" />
                  <Input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    placeholder="student"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-9"
                    required
                    aria-required="true"
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-muted-foreground pointer-events-none" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="????????"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-9"
                    required
                    aria-required="true"
                    disabled={isSubmitting}
                  />
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col gap-3">
              <Button
                type="submit"
                className="w-full gap-2"
                disabled={isSubmitting}
                aria-busy={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    <span>Sign In</span>
                  </>
                )}
              </Button>
              <p className="text-xs text-center text-muted-foreground">
                Default maintainer credentials: <code>student</code> / <code>maintainer</code>
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
