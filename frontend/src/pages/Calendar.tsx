import { useEffect, useMemo, useState } from "react";
import {
  addDays,
  addMonths,
  format,
  parseISO,
  startOfDay,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import { api, CalendarEvent } from "@/lib/api";

type View = "day" | "week" | "month";

function initialView(): View {
  if (typeof window !== "undefined" && window.innerWidth < 768) return "day";
  return "week";
}

export function CalendarPage({ refreshKey }: { refreshKey: number }) {
  const [view, setView] = useState<View>(initialView);
  const [cursor, setCursor] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [provider, setProvider] = useState("mock");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    title: "",
    start_time: format(addDays(startOfDay(new Date()), 0), "yyyy-MM-dd'T'10:00"),
    end_time: format(addDays(startOfDay(new Date()), 0), "yyyy-MM-dd'T'11:00"),
    category: "meeting",
  });

  const range = useMemo(() => {
    if (view === "day") {
      const s = startOfDay(cursor);
      return { start: s, end: addDays(s, 1) };
    }
    if (view === "week") {
      const s = startOfWeek(cursor, { weekStartsOn: 1 });
      return { start: s, end: addDays(s, 7) };
    }
    const s = startOfWeek(startOfMonth(cursor), { weekStartsOn: 1 });
    return { start: s, end: addDays(s, 42) };
  }, [view, cursor]);

  const load = async () => {
    const res = await api.listEvents(range.start.toISOString(), range.end.toISOString());
    setEvents(res.events);
    setProvider(res.provider);
  };

  useEffect(() => {
    load().catch(console.error);
  }, [refreshKey, range.start.getTime(), range.end.getTime()]);

  const days =
    view === "day"
      ? [startOfDay(cursor)]
      : view === "week"
        ? Array.from({ length: 7 }, (_, i) => addDays(startOfWeek(cursor, { weekStartsOn: 1 }), i))
        : Array.from({ length: 42 }, (_, i) => addDays(range.start, i));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-sm text-gray-500">Source: {provider}</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden">
            {(["day", "week", "month"] as View[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3 py-1.5 text-sm capitalize ${view === v ? "bg-slate-900 text-white" : "bg-white"}`}
              >
                {v}
              </button>
            ))}
          </div>
          <button className="rounded-lg border px-3 py-1.5 text-sm" onClick={() => setCursor(new Date())}>
            Today
          </button>
          <button
            className="rounded-lg border px-3 py-1.5 text-sm"
            onClick={() => setCursor(view === "month" ? addMonths(cursor, -1) : addDays(cursor, view === "day" ? -1 : -7))}
          >
            ‹
          </button>
          <button
            className="rounded-lg border px-3 py-1.5 text-sm"
            onClick={() => setCursor(view === "month" ? addMonths(cursor, 1) : addDays(cursor, view === "day" ? 1 : 7))}
          >
            ›
          </button>
          <button
            className="rounded-lg bg-slate-900 text-white px-3 py-1.5 text-sm"
            onClick={() => setCreating(true)}
          >
            + Create event
          </button>
        </div>
      </div>

      {creating && (
        <form
          className="rounded-xl border bg-white p-4 grid gap-3 md:grid-cols-2"
          onSubmit={async (e) => {
            e.preventDefault();
            await api.createEvent({
              title: form.title,
              start_time: new Date(form.start_time).toISOString(),
              end_time: new Date(form.end_time).toISOString(),
              category: form.category,
            });
            setCreating(false);
            setForm((f) => ({ ...f, title: "" }));
            await load();
          }}
        >
          <label className="text-sm font-medium">
            Title
            <input
              required
              className="mt-1 w-full rounded-lg border px-3 py-2"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label className="text-sm font-medium">
            Category
            <select
              className="mt-1 w-full rounded-lg border px-3 py-2"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              <option value="meeting">Meeting</option>
              <option value="focus">Focus</option>
              <option value="personal">Personal</option>
              <option value="important">Important</option>
            </select>
          </label>
          <label className="text-sm font-medium">
            Start
            <input
              type="datetime-local"
              required
              className="mt-1 w-full rounded-lg border px-3 py-2"
              value={form.start_time}
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
            />
          </label>
          <label className="text-sm font-medium">
            End
            <input
              type="datetime-local"
              required
              className="mt-1 w-full rounded-lg border px-3 py-2"
              value={form.end_time}
              onChange={(e) => setForm({ ...form, end_time: e.target.value })}
            />
          </label>
          <div className="md:col-span-2 flex gap-2">
            <button type="submit" className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm">
              Save
            </button>
            <button type="button" className="rounded-lg border px-4 py-2 text-sm" onClick={() => setCreating(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="rounded-xl border bg-white overflow-x-auto shadow-sm -mx-1 px-1 sm:mx-0 sm:px-0">
        {view === "month" ? (
          <div className="grid grid-cols-7 min-w-[560px] sm:min-w-[800px]">
            {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
              <div key={d} className="p-2 text-xs text-gray-500 font-semibold text-center border-b">
                {d}
              </div>
            ))}
            {days.map((d) => {
              const key = format(d, "yyyy-MM-dd");
              const dayEvents = events.filter((e) => format(parseISO(e.start_time), "yyyy-MM-dd") === key);
              return (
                <div key={key} className="min-h-28 border-t border-r p-2">
                  <div className="text-sm font-semibold mb-1">{format(d, "d")}</div>
                  {dayEvents.slice(0, 3).map((e) => (
                    <button
                      key={e.id}
                      className="block w-full text-left text-[11px] rounded mb-1 px-1 py-0.5 bg-blue-50 truncate"
                      onClick={async () => {
                        if (confirm(`Delete “${e.title}”?`)) {
                          await api.deleteEvent(e.id);
                          await load();
                        }
                      }}
                      title="Click to delete"
                    >
                      {format(parseISO(e.start_time), "HH:mm")} {e.title}
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        ) : (
          <div className={view === "day" ? "min-w-0" : "min-w-[560px] sm:min-w-[700px]"}>
            <div
              className="grid border-b bg-gray-50"
              style={{
                gridTemplateColumns:
                  view === "day"
                    ? "52px 1fr"
                    : `52px repeat(${days.length}, minmax(88px, 1fr))`,
              }}
            >
              <div />
              {days.map((d) => (
                <div key={d.toISOString()} className="p-2 text-center text-sm border-l">
                  <div className="text-xs text-gray-500">{format(d, "EEE")}</div>
                  <div className="font-semibold">{format(d, "d")}</div>
                </div>
              ))}
            </div>
            {Array.from({ length: 12 }, (_, i) => i + 8).map((hour) => (
              <div
                key={hour}
                className="grid border-b min-h-14 sm:min-h-16"
                style={{
                  gridTemplateColumns:
                    view === "day"
                      ? "52px 1fr"
                      : `52px repeat(${days.length}, minmax(88px, 1fr))`,
                }}
              >
                <div className="p-2 text-xs text-gray-500">{String(hour).padStart(2, "0")}:00</div>
                {days.map((d) => {
                  const key = format(d, "yyyy-MM-dd");
                  const cellEvents = events.filter((e) => {
                    const s = parseISO(e.start_time);
                    return format(s, "yyyy-MM-dd") === key && s.getHours() === hour;
                  });
                  return (
                    <div key={key + hour} className="border-l p-1">
                      {cellEvents.map((e) => (
                        <button
                          key={e.id}
                          className="w-full text-left rounded-md bg-blue-50 border-l-4 border-blue-500 px-2 py-1 mb-1 text-xs"
                          onClick={async () => {
                            if (confirm(`Delete “${e.title}”?`)) {
                              await api.deleteEvent(e.id);
                              await load();
                            }
                          }}
                        >
                          <div className="font-semibold">{e.title}</div>
                          <div className="text-gray-500">
                            {format(parseISO(e.start_time), "HH:mm")}–{format(parseISO(e.end_time), "HH:mm")}
                          </div>
                        </button>
                      ))}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
