import { NavLink, Outlet } from "react-router-dom";
import {
  Bot,
  CalendarDays,
  ChartNoAxesColumn,
  CheckSquare,
  LayoutDashboard,
  PanelRight,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, AuthStatus, googleConnectUrl } from "@/lib/api";
import { AIPanel } from "./AIPanel";

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
  const [aiOpen, setAiOpen] = useState(true);

  const loadAuth = async () => {
    try {
      setAuth(await api.authStatus());
    } catch {
      setAuth(null);
    }
  };

  useEffect(() => {
    loadAuth();
  }, []);

  const providerLabel = auth?.user?.provider === "google" ? "Google" : "Local";

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
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted)]">Source</div>
            <div className="mt-1 text-sm font-semibold">{providerLabel} calendar</div>
            {auth?.google_oauth_configured ? (
              auth?.user?.provider === "google" ? (
                <button
                  className="mt-2 text-xs text-[var(--muted)] underline underline-offset-2"
                  onClick={async () => {
                    await api.disconnectGoogle();
                    await loadAuth();
                    onRefreshKey();
                  }}
                >
                  Disconnect
                </button>
              ) : (
                <a className="mt-2 inline-block text-xs text-[var(--accent)] underline underline-offset-2" href={googleConnectUrl()}>
                  Connect Google
                </a>
              )
            ) : (
              <div className="mt-2 text-[11px] leading-relaxed text-[var(--muted)]">
                Add Google OAuth keys to connect a real calendar.
              </div>
            )}
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
                {auth?.user?.name || "Guest"} · {providerLabel}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button className="btn xl:hidden" onClick={() => setAiOpen((v) => !v)}>
                Assistant
              </button>
              <div className="h-9 w-9 rounded-full bg-[var(--ink)] text-white grid place-items-center text-xs font-semibold">
                {(auth?.user?.name || "G").slice(0, 1).toUpperCase()}
              </div>
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
