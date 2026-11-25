import { useEffect, useMemo, useState } from "react";
import { addDays, format, parseISO, startOfDay } from "date-fns";
import { api, CalendarEvent } from "@/lib/api";

export function InsightsPage({ refreshKey }: { refreshKey: number }) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [slots, setSlots] = useState<{ start: string; end: string }[]>([]);

  useEffect(() => {
    const start = startOfDay(new Date());
    const end = addDays(start, 14);
    Promise.all([
      api.listEvents(start.toISOString(), end.toISOString()),
      api.freeBusy(start.toISOString(), end.toISOString(), 30),
    ]).then(([ev, fb]) => {
      setEvents(ev.events);
      setSlots(fb.slots);
    });
  }, [refreshKey]);

  const byCategory = useMemo(() => {
    const map: Record<string, number> = {};
    for (const e of events) {
      const mins = (parseISO(e.end_time).getTime() - parseISO(e.start_time).getTime()) / 60000;
      map[e.category] = (map[e.category] || 0) + mins;
    }
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [events]);

  const max = Math.max(...byCategory.map(([, m]) => m), 1);
  const freeMins = slots.reduce(
    (acc, s) => acc + (parseISO(s.end).getTime() - parseISO(s.start).getTime()) / 60000,
    0
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Insights</h1>
        <p className="text-gray-500">Built from live calendar + free/busy data.</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Events (14d)</div>
          <div className="text-2xl font-semibold">{events.length}</div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Free slots found</div>
          <div className="text-2xl font-semibold">{slots.length}</div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Free minutes (est.)</div>
          <div className="text-2xl font-semibold">{Math.round(freeMins)}</div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <h2 className="font-semibold mb-3">Minutes by category</h2>
        {byCategory.length === 0 ? (
          <div className="text-sm text-gray-500">No events yet.</div>
        ) : (
          <div className="space-y-2">
            {byCategory.map(([cat, mins]) => (
              <div key={cat} className="grid grid-cols-[100px_1fr_60px] gap-2 items-center text-sm">
                <div className="capitalize">{cat}</div>
                <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full bg-blue-600" style={{ width: `${(mins / max) * 100}%` }} />
                </div>
                <div className="text-gray-500 text-right">{Math.round(mins)}m</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <h2 className="font-semibold mb-3">Upcoming free slots</h2>
        <ul className="text-sm space-y-1">
          {slots.slice(0, 8).map((s, i) => (
            <li key={i}>
              {format(parseISO(s.start), "EEE HH:mm")} – {format(parseISO(s.end), "HH:mm")}
            </li>
          ))}
          {slots.length === 0 && <li className="text-gray-500">No free slots in range.</li>}
        </ul>
      </div>
    </div>
  );
}
