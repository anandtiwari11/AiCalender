import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { RecommendationCard, Recommendation } from "@/components/RecommendationCard";

export function TodayPage({ refreshKey }: { refreshKey: number }) {
  const [brief, setBrief] = useState<any>(null);
  const [error, setError] = useState("");

  const load = () => {
    api
      .chiefOfStaff()
      .then(setBrief)
      .catch((e) => setError(String(e.message || e)));
  };

  useEffect(() => {
    load();
  }, [refreshKey]);

  if (error) return <div className="text-[var(--danger)] text-sm">{error}</div>;
  if (!brief) return <div className="text-[var(--muted)] text-sm">Loading brief…</div>;

  return (
    <div className="space-y-7">
      <div className="flex justify-between gap-4 flex-wrap items-end">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--muted)] mb-2">
            Daily brief
          </div>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">{brief.greeting}</h1>
          <p className="text-sm text-[var(--muted)] mt-2">Source: {brief.provider}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn" onClick={load}>Refresh</button>
          <Link to="/workspace" className="btn btn-primary">Workspace</Link>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ["Meetings", brief.all_meeting_scores?.length ?? 0],
          ["Focus", `${brief.focus_minutes}m`],
          ["Available", `${brief.available_minutes}m`],
          ["Longest free", `${brief.longest_free_minutes}m`],
        ].map(([label, value]) => (
          <div key={String(label)} className="surface p-4">
            <div className="text-xs text-[var(--muted)]">{label}</div>
            <div className="font-display text-2xl mt-1 tracking-tight">{value}</div>
          </div>
        ))}
      </div>

      <div className="surface p-5 md:p-6 bg-[linear-gradient(180deg,#fff_0%,#f8fbf9_100%)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)] mb-3">
          Chief of Staff
        </div>
        <p className="font-display text-lg md:text-xl leading-relaxed text-[var(--ink)]">
          {brief.narrative}
        </p>
        {brief.problems?.length > 0 && (
          <ul className="mt-4 text-sm text-[var(--warn)] space-y-1">
            {brief.problems.map((p: string) => (
              <li key={p}>• {p}</li>
            ))}
          </ul>
        )}
      </div>

      {(brief.recommendations || []).length > 0 && (
        <div className="space-y-3">
          <h2 className="font-display text-xl">Recommended actions</h2>
          <div className="grid md:grid-cols-2 gap-3">
            {(brief.recommendations as Recommendation[]).slice(0, 4).map((r) => (
              <RecommendationCard key={r.id} rec={r} onApplied={load} />
            ))}
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-3">
        <div className="surface p-5">
          <h2 className="font-display text-lg mb-3">Important meetings</h2>
          <ul className="text-sm space-y-2">
            {(brief.important_meetings || []).map((m: any) => (
              <li key={m.event_id} className="flex gap-2">
                <span className="capitalize text-[var(--accent)] font-semibold">{m.level}</span>
                <span className="text-[var(--muted)]">—</span>
                <span>{m.title}</span>
              </li>
            ))}
            {(brief.important_meetings || []).length === 0 && (
              <li className="text-[var(--muted)]">None scored high today.</li>
            )}
          </ul>
        </div>
        <div className="surface p-5">
          <h2 className="font-display text-lg mb-3">Deadlines</h2>
          <ul className="text-sm space-y-2">
            {(brief.upcoming_deadlines || []).map((t: any) => (
              <li key={t.id}>
                {t.title}
                <div className="text-xs text-[var(--muted)]">
                  due {t.due_date?.slice(0, 10)} · ~{t.estimated_minutes}m
                </div>
              </li>
            ))}
            {(brief.upcoming_deadlines || []).length === 0 && (
              <li className="text-[var(--muted)]">Add tasks to ground deadline advice.</li>
            )}
          </ul>
        </div>
      </div>

      <div className="surface p-5">
        <h2 className="font-display text-lg mb-3">Schedule</h2>
        {(brief.schedule || []).length === 0 ? (
          <div className="text-sm text-[var(--muted)]">No events today.</div>
        ) : (
          <ul className="text-sm space-y-2">
            {brief.schedule.map((e: any) => (
              <li key={e.id} className="flex gap-3">
                <span className="text-[var(--muted)] tabular-nums w-24 shrink-0">
                  {e.start_time?.slice(11, 16)}–{e.end_time?.slice(11, 16)}
                </span>
                <span>{e.title}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
