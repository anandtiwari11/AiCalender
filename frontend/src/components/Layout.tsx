import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Bot,
  CalendarDays,
  ChartNoAxesColumn,
  CheckSquare,
  LayoutDashboard,
  LogOut,
  Menu,
  Sparkles,
  X,
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

function useIsDesktop(breakpoint = 1024) {
  const [desktop, setDesktop] = useState(
    typeof window !== "undefined" ? window.innerWidth >= breakpoint : true
  );
  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${breakpoint}px)`);
    const onChange = () => setDesktop(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [breakpoint]);
  return desktop;
}

export function Layout({ onRefreshKey }: { onRefreshKey: () => void; refreshKey: number }) {
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const isDesktop = useIsDesktop();
  const [aiOpen, setAiOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

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

  // Close mobile drawers on navigate
  useEffect(() => {
    setMenuOpen(false);
    if (!isDesktop) setAiOpen(false);
  }, [location.pathname, isDesktop]);

  // Desktop: assistant open by default once known
  useEffect(() => {
    if (isDesktop) setAiOpen(true);
    else setAiOpen(false);
  }, [isDesktop]);

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
        onSignedIn={async () => {
          await loadAuth();
          onRefreshKey();
        }}
      />
    );
  }

  const displayName = auth.user?.name || auth.user?.phone || auth.user?.email || "Signed in";
  const calendarLabel =
    auth.calendar_source === "google" || auth.has_calendar
      ? "Google Calendar"
      : "Local calendar";

  const accountBlock = (
    <div className="rounded-2xl border border-[var(--line)] bg-white p-3">
      <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted)]">Account</div>
      <div className="mt-1 text-sm font-semibold truncate">{displayName}</div>
      <div className="text-[11px] text-[var(--muted)] truncate">
        {auth.user?.phone || auth.user?.email}
      </div>
      <div className="text-[11px] text-[var(--muted)] mt-1">{calendarLabel}</div>
      {auth.calendar_source !== "google" && auth.google_oauth_configured ? (
        <a
          className="mt-2 inline-flex text-xs text-[var(--accent)] underline underline-offset-2"
          href="/api/auth/google/start"
        >
          Connect Google Calendar
        </a>
      ) : null}
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
  );

  const navLinks = (opts?: { onNavigate?: () => void; compact?: boolean }) =>
    nav.map((item) => (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.to === "/"}
        onClick={opts?.onNavigate}
        className={({ isActive }) =>
          opts?.compact
            ? `flex flex-col items-center justify-center gap-0.5 min-w-0 flex-1 py-2 text-[10px] font-medium ${
                isActive ? "text-[var(--ink)]" : "text-[var(--muted)]"
              }`
            : `flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-colors ${
                isActive
                  ? "bg-[var(--ink)] !text-white"
                  : "text-[var(--muted)] hover:bg-black/[0.03] hover:text-[var(--ink)]"
              }`
        }
      >
        <item.icon size={opts?.compact ? 18 : 15} strokeWidth={1.75} />
        <span className={opts?.compact ? "truncate max-w-full px-0.5" : undefined}>{item.label}</span>
      </NavLink>
    ));

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[220px_1fr]">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col gap-8 sticky top-0 h-screen px-4 py-6 border-r border-[var(--line)] bg-white/70 backdrop-blur-md">
        <div className="px-2">
          <div className="font-display text-2xl tracking-tight text-[var(--ink)]">Cal.ai</div>
          <div className="mt-1 text-xs text-[var(--muted)] leading-snug">
            Your time, intelligently managed.
          </div>
        </div>
        <nav className="flex flex-col gap-0.5">{navLinks()}</nav>
        <div className="mt-auto space-y-3 px-1">
          {accountBlock}
          <button className="btn w-full" onClick={() => setAiOpen((v) => !v)}>
            {aiOpen ? "Hide assistant" : "Show assistant"}
          </button>
        </div>
      </aside>

      <div className={`min-w-0 ${aiOpen && isDesktop ? "xl:grid xl:grid-cols-[1fr_360px]" : ""}`}>
        <main className="min-w-0 pb-[calc(4.5rem+env(safe-area-inset-bottom))] lg:pb-0">
          <header className="sticky top-0 z-20 px-4 sm:px-5 md:px-8 py-3 sm:py-4 flex items-center justify-between gap-3 border-b border-[var(--line)] bg-[color-mix(in_srgb,var(--bg)_82%,white)] backdrop-blur-md">
            <div className="min-w-0 flex items-center gap-2">
              <button
                type="button"
                className="lg:hidden btn !px-2.5 !py-2"
                aria-label="Open menu"
                onClick={() => setMenuOpen(true)}
              >
                <Menu size={18} />
              </button>
              <div className="min-w-0">
                <div className="font-display text-base sm:text-lg md:text-xl tracking-tight truncate">
                  {new Date().toLocaleDateString(undefined, {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                  })}
                </div>
                <div className="text-[11px] sm:text-xs text-[var(--muted)] mt-0.5 truncate">
                  {displayName} · {calendarLabel}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button className="btn !text-xs sm:!text-sm" onClick={() => setAiOpen(true)}>
                Assistant
              </button>
              {auth.user?.picture ? (
                <img
                  src={auth.user.picture}
                  alt=""
                  className="h-8 w-8 sm:h-9 sm:w-9 rounded-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="h-8 w-8 sm:h-9 sm:w-9 rounded-full bg-[var(--ink)] text-white grid place-items-center text-xs font-semibold">
                  {displayName.slice(0, 1).toUpperCase()}
                </div>
              )}
            </div>
          </header>

          <div className="p-4 sm:p-5 md:p-8 max-w-6xl fade-up">
            <Outlet />
          </div>
        </main>

        {/* Desktop assistant column */}
        {aiOpen && isDesktop ? <AIPanel onApplied={onRefreshKey} /> : null}
      </div>

      {/* Mobile bottom nav */}
      <nav
        className="lg:hidden fixed bottom-0 inset-x-0 z-30 border-t border-[var(--line)] bg-white/95 backdrop-blur-md"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="flex items-stretch justify-between px-1 max-w-lg mx-auto">
          {navLinks({ compact: true })}
        </div>
      </nav>

      {/* Mobile account / more drawer */}
      {menuOpen ? (
        <div className="lg:hidden fixed inset-0 z-40">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close menu"
            onClick={() => setMenuOpen(false)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-[min(100%,20rem)] bg-[var(--bg)] shadow-xl p-5 flex flex-col gap-5 overflow-auto">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display text-2xl">Cal.ai</div>
                <div className="text-xs text-[var(--muted)]">Your time, intelligently managed.</div>
              </div>
              <button type="button" className="btn !px-2.5" onClick={() => setMenuOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <nav className="flex flex-col gap-0.5">{navLinks({ onNavigate: () => setMenuOpen(false) })}</nav>
            {accountBlock}
            <button
              className="btn btn-primary w-full"
              onClick={() => {
                setMenuOpen(false);
                setAiOpen(true);
              }}
            >
              Open assistant
            </button>
          </div>
        </div>
      ) : null}

      {/* Mobile assistant sheet */}
      {aiOpen && !isDesktop ? (
        <div className="lg:hidden fixed inset-0 z-50 flex flex-col bg-white">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--line)] shrink-0">
            <div className="font-display text-lg">Assistant</div>
            <button type="button" className="btn !px-2.5" onClick={() => setAiOpen(false)} aria-label="Close">
              <X size={18} />
            </button>
          </div>
          <div className="flex-1 min-h-0">
            <AIPanel onApplied={onRefreshKey} embedded />
          </div>
        </div>
      ) : null}
    </div>
  );
}
