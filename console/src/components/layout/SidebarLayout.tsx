import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  GitPullRequest,
  LayoutDashboard,
  Settings as SettingsIcon,
  AlertCircle,
  BarChart3,
  Menu,
  X,
  LogOut,
  LogIn,
  UserCheck
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const nav = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Pull Requests", href: "/prs", icon: GitPullRequest },
    { name: "Issues / Triage", href: "/issues", icon: AlertCircle },
    { name: "Evaluation", href: "/eval", icon: BarChart3 },
    { name: "Activity Log", href: "/activity", icon: Activity },
    { name: "Settings", href: "/settings", icon: SettingsIcon },
  ];

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <div className="flex h-screen w-full flex-col md:flex-row bg-background text-foreground overflow-hidden">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b bg-card z-30">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg text-primary">
          <GitPullRequest className="w-5 h-5" />
          <span>CodeSentinel</span>
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav"
            className="h-9 w-9"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-nav"
          role="navigation"
          aria-label="Mobile Navigation"
          className="md:hidden fixed inset-0 top-[57px] bg-background/95 backdrop-blur-sm z-20 flex flex-col p-6 space-y-4 overflow-y-auto"
        >
          <nav className="flex flex-col gap-2">
            {nav.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={closeMobileMenu}
                  className={`flex items-center gap-3 rounded-lg px-4 py-3 text-base transition-all ${
                    isActive
                      ? "bg-primary text-primary-foreground font-semibold shadow-sm"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="border-t pt-4 mt-auto space-y-3">
            {isAuthenticated && user ? (
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/60">
                <div className="flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-500" />
                  <div>
                    <p className="text-sm font-medium">{user.username}</p>
                    <p className="text-xs text-muted-foreground capitalize">{user.role}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => { logout(); closeMobileMenu(); }}>
                  <LogOut className="w-4 h-4 mr-1" />
                  Logout
                </Button>
              </div>
            ) : (
              <Link to="/login" onClick={closeMobileMenu}>
                <Button variant="outline" className="w-full justify-center">
                  <LogIn className="w-4 h-4 mr-2" />
                  Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside
        className="hidden md:flex w-64 border-r bg-card/60 backdrop-blur-sm p-4 flex-col gap-4 flex-shrink-0 justify-between"
        role="navigation"
        aria-label="Sidebar Navigation"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2 pt-1">
            <Link to="/" className="flex items-center gap-2 font-bold text-xl text-primary">
              <GitPullRequest className="w-6 h-6 text-primary" />
              <span>CodeSentinel</span>
            </Link>
          </div>

          <nav className="flex flex-col gap-1.5 pt-2">
            {nav.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                    isActive
                      ? "bg-primary text-primary-foreground font-medium shadow-xs"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Desktop Sidebar Bottom Footer */}
        <div className="border-t pt-4 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-medium text-muted-foreground">Theme</span>
            <ThemeToggle />
          </div>

          {isAuthenticated && user ? (
            <div className="p-2.5 rounded-lg bg-muted/50 border border-border/50 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 overflow-hidden">
                  <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <UserCheck className="w-4 h-4 text-primary" />
                  </div>
                  <div className="truncate">
                    <p className="text-xs font-semibold truncate">{user.username}</p>
                    <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 uppercase font-normal">
                      {user.role}
                    </Badge>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-destructive"
                  onClick={logout}
                  aria-label="Sign out"
                  title="Sign out"
                >
                  <LogOut className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ) : (
            <Link to="/login" className="block">
              <Button variant="outline" size="sm" className="w-full gap-2">
                <LogIn className="h-3.5 w-3.5" />
                <span>Sign In</span>
              </Button>
            </Link>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main
        id="main-content"
        role="main"
        className="flex-1 overflow-y-auto p-4 md:p-8 focus:outline-none"
        tabIndex={-1}
      >
        <div className="max-w-7xl mx-auto space-y-6">
          {children}
        </div>
      </main>
    </div>
  );
}

export default SidebarLayout;
