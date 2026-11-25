import { NavLink, Outlet } from "react-router-dom";
import {
  Bot,
  CalendarDays,
  ChartNoAxesColumn,
  CheckSquare,
  LayoutDashboard,
  LogOut,
  PanelRight,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, AuthStatus } from "@/lib/api";
import { AIPanel } from "./AIPanel";
import { LoginGate } from "./LoginGate";

const nav = [
  { to: "/", label: "Today", icon: LayoutDashboard },
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/workspace", label: "Workspace", icon: Bot },
  { to: "/tasks", label: "Tasks", icon: CheckSquare },
  { to: "/planner", label: "Planner", icon: Sparkles },
  { to: "/insights", label: "Insights", icon: ChartNoAxesColumn },
];

export function Layout({ onRefreshKey }: { onRefreshKey: () => void; refreshKey: number }) {
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiOpen, setAiOpen] = useState(true);

  const loadAuth = async () => {
    try {
      setAuth(await api.authStatus());
    } catch {
      setAuth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const err = params.get("auth_error");
    if (err) setAuthError(err);
    if (params.get("connected") || err) {
      window.history.replaceState({}, "", window.location.pathname);
    }
    loadAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center text-sm text-[var(--muted)]">
        Loading…
      </div>
    );
  }

  if (!auth?.authenticated) {
    return (
      <LoginGate
        oauthConfigured={Boolean(auth?.google_oauth_configured)}
        error={authError}
      />
    );
  }

  const displayName = auth.user?.name || auth.user?.email || "Signed in";

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[220px_1fr]">
      <aside className="hidden lg:flex flex-col gap-8 sticky top-0 h-screen px-4 py-6 border-r border-[var(--line)] bg-white/70 backdrop-blur-md">
        <div className="px-2">
          <div className="font-display text-2xl tracking-tight text-[var(--ink)]">Cal.ai</div>
          <div className="mt-1 text-xs text-[var(--muted)] leading-snug">
            Your time, intelligently managed.
          </div>
        </div>

        <nav className="flex flex-col gap-0.5">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-colors ${
                  isActive
                    ? "bg-[var(--ink)] !text-white"
                    : "text-[var(--muted)] hover:bg-black/[0.03] hover:text-[var(--ink)]"
                }`
              }
            >
              <item.icon size={15} strokeWidth={1.75} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-3 px-1">
          <div className="rounded-2xl border border-[var(--line)] bg-white p-3">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted)]">Account</div>
            <div className="mt-1 text-sm font-semibold truncate">{displayName}</div>
            <div className="text-[11px] text-[var(--muted)] truncate">{auth.user?.email}</div>
            <button
              className="mt-2 inline-flex items-center gap-1 text-xs text-[var(--muted)] underline underline-offset-2"
              onClick={async () => {
                await api.logout();
                await loadAuth();
                onRefreshKey();
              }}
            >
              <LogOut size={12} /> Sign out
            </button>
          </div>
          <button className="btn w-full" onClick={() => setAiOpen((v) => !v)}>
            <PanelRight size={14} />
            {aiOpen ? "Hide assistant" : "Show assistant"}
          </button>
        </div>
      </aside>

      <div className={`min-w-0 ${aiOpen ? "xl:grid xl:grid-cols-[1fr_360px]" : ""}`}>
        <main className="min-w-0">
          <header className="sticky top-0 z-10 px-5 md:px-8 py-4 flex items-center justify-between border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--bg)_82%,white)] backdrop-blur-md">
            <div>
              <div className="font-display text-lg md:text-xl tracking-tight">
                {new Date().toLocaleDateString(undefined, {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
              </div>
              <div className="text-xs text-[var(--muted)] mt-0.5">
                {displayName} · Google Calendar
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="btn xl:hidden" onClick={() => setAiOpen((v) => !v)}>
                Assistant
              </button>
              {auth.user?.picture ? (
                <img
                  src={auth.user.picture}
                  alt=""
                  className="h-9 w-9 rounded-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="h-9 w-9 rounded-full bg-[var(--ink)] text-white grid place-items-center text-xs font-semibold">
                  {displayName.slice(0, 1).toUpperCase()}
                </div>
              )}
            </div>
          </header>
          <div className="p-5 md:p-8 max-w-6xl fade-up">
            <Outlet />
          </div>
        </main>
        {aiOpen && <AIPanel onApplied={onRefreshKey} />}
      </div>
    </div>
  );
}
