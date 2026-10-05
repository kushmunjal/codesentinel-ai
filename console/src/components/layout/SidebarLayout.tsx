import { Link, useLocation } from "react-router-dom";
import { Activity, GitPullRequest, LayoutDashboard, Settings as SettingsIcon, AlertCircle, BarChart3 } from "lucide-react";

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const nav = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Pull Requests", href: "/prs", icon: GitPullRequest },
    { name: "Issues / Triage", href: "/issues", icon: AlertCircle },
    { name: "Evaluation", href: "/eval", icon: BarChart3 },
    { name: "Activity Log", href: "/activity", icon: Activity },
    { name: "Settings", href: "/settings", icon: SettingsIcon },
  ];

  return (
    <div className="flex h-screen w-full flex-col md:flex-row bg-background overflow-hidden">
      <div className="w-full md:w-64 border-r bg-muted/40 p-4 flex flex-col gap-4 flex-shrink-0">
        <div className="flex items-center gap-2 px-2 font-bold text-xl text-primary mb-4">
          <GitPullRequest className="w-6 h-6" />
          <span>CodeSentinel</span>
        </div>
        <nav className="flex flex-col gap-1">
          {nav.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all hover:text-primary ${
                  isActive ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
