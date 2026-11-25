// Local: leave empty to use Vite proxy. Production: set VITE_API_BASE to API URL.
const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type CalendarEvent = {
  id: string;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  attendees: string[];
  category: string;
  location: string;
  priority: string;
  meeting_link: string;
  notes: string;
  source: string;
};

export type AuthStatus = {
  authenticated: boolean;
  google_oauth_configured: boolean;
  has_calendar?: boolean;
  user: {
    id: number;
    email: string;
    name: string;
    picture: string;
    provider: string;
  } | null;
};

export const api = {
  health: () => request<{ ok: boolean; google_oauth_configured: boolean }>("/api/health"),
  authStatus: () => request<AuthStatus>("/api/auth/status"),
  logout: () => request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  disconnectGoogle: () =>
    request<{ ok: boolean }>("/api/auth/disconnect-google", { method: "POST" }),
  listEvents: (start: string, end: string) =>
    request<{ provider: string; events: CalendarEvent[] }>(
      `/api/events?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
    ),
  createEvent: (body: Partial<CalendarEvent> & { title: string; start_time: string; end_time: string }) =>
    request<CalendarEvent>("/api/events", { method: "POST", body: JSON.stringify(body) }),
  updateEvent: (id: string, body: Partial<CalendarEvent>) =>
    request<CalendarEvent>(`/api/events/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteEvent: (id: string) =>
    request<{ ok: boolean }>(`/api/events/${id}`, { method: "DELETE" }),
  freeBusy: (start: string, end: string, minMinutes = 30) =>
    request<{ provider: string; slots: { start: string; end: string }[] }>(
      `/api/freebusy?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&min_minutes=${minMinutes}`
    ),
  aiStatus: () =>
    request<{ configured: boolean; provider: string; model: string; label: string }>(
      "/api/ai/status"
    ),
  brief: () => request<Record<string, unknown>>("/api/ai/brief"),
  chat: (message: string) =>
    request<{
      reply: string;
      summary: string;
      actions: unknown[];
      proposal_id: number | null;
      mode: string;
      provider: string;
    }>("/api/ai/chat", { method: "POST", body: JSON.stringify({ message }) }),
  proposals: () =>
    request<{
      proposals: { id: number; summary: string; actions: unknown[]; created_at: string }[];
    }>("/api/ai/proposals"),
  confirmProposal: (id: number) =>
    request<{ ok: boolean; results: string[]; provider: string }>(
      `/api/ai/proposals/${id}/confirm`,
      { method: "POST" }
    ),
  dismissProposal: (id: number) =>
    request<{ ok: boolean }>(`/api/ai/proposals/${id}/dismiss`, { method: "POST" }),
  messages: () =>
    request<{ messages: { id: number; role: string; content: string }[] }>("/api/ai/messages"),
  chiefOfStaff: () => request<any>("/api/intelligence/chief-of-staff"),
  importance: () => request<any>("/api/intelligence/importance"),
  conflicts: () => request<any>("/api/intelligence/conflicts"),
  focusPlan: () => request<any>("/api/intelligence/focus"),
  protectFocus: () =>
    request<{ proposal_id: number | null; actions: unknown[]; plan: any }>(
      "/api/intelligence/focus/protect",
      { method: "POST" }
    ),
  buffers: () => request<any>("/api/intelligence/buffers"),
  proposeRecommendation: (summary: string, actions: unknown[], kind = "recommendation") =>
    request<{ proposal_id: number | null; actions: unknown[] }>("/api/intelligence/propose", {
      method: "POST",
      body: JSON.stringify({ summary, actions, kind }),
    }),
  proposeConflictResolution: (move_event_id: string, alternative_start: string, alternative_end: string) =>
    request<{ proposal_id: number | null }>("/api/intelligence/conflicts/propose", {
      method: "POST",
      body: JSON.stringify({ move_event_id, alternative_start, alternative_end }),
    }),
  getPreferences: () => request<Record<string, unknown>>("/api/intelligence/preferences"),
  updatePreferences: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/intelligence/preferences", {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  listTasks: () => request<{ tasks: any[] }>("/api/tasks"),
  createTask: (body: Record<string, unknown>) =>
    request<any>("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
  toggleTask: (id: number) => request<any>(`/api/tasks/${id}/toggle`, { method: "POST" }),
  deleteTask: (id: number) => request<{ ok: boolean }>(`/api/tasks/${id}`, { method: "DELETE" }),
};

export function googleConnectUrl() {
  return `${API_BASE}/api/auth/google/start`;
}
