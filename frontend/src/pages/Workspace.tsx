import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { RecommendationCard, Recommendation } from "@/components/RecommendationCard";

type Tab = "chief" | "focus" | "importance" | "conflicts" | "buffers" | "prefs";

export function WorkspacePage({ refreshKey, onApplied }: { refreshKey: number; onApplied: () => void }) {
  const [tab, setTab] = useState<Tab>("chief");
  const [chief, setChief] = useState<any>(null);
  const [focus, setFocus] = useState<any>(null);
  const [importance, setImportance] = useState<any>(null);
  const [conflicts, setConflicts] = useState<any>(null);
  const [buffers, setBuffers] = useState<any>(null);
  const [prefs, setPrefs] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [c, f, i, co, b, p] = await Promise.all([
        api.chiefOfStaff(),
        api.focusPlan(),
        api.importance(),
        api.conflicts(),
        api.buffers(),
        api.getPreferences(),
      ]);
      setChief(c);
      setFocus(f);
      setImportance(i);
      setConflicts(co);
      setBuffers(b);
      setPrefs(p);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [refreshKey]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "chief", label: "Chief of Staff" },
    { id: "focus", label: "Focus Protector" },
    { id: "importance", label: "Meeting Priority" },
    { id: "conflicts", label: "Conflicts" },
    { id: "buffers", label: "Smart Buffers" },
    { id: "prefs", label: "Preferences" },
  ];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Workspace</h1>
          <p className="text-gray-500">
            Phase 1 intelligence — grounded in your calendar, applied only after approval.
          </p>
        </div>
        <button
          onClick={load}
          className="rounded-lg border bg-white px-3 py-2 text-sm"
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh analysis"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-3 py-1.5 text-sm border ${
              tab === t.id ? "bg-slate-900 text-white border-slate-900" : "bg-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}

      {tab === "chief" && chief && (
        <div className="space-y-4">
          <div className="rounded-xl border border-blue-100 bg-slate-50 p-5 shadow-sm">
            <div className="text-xs font-bold uppercase tracking-wide text-blue-600 mb-2">
              Daily Chief of Staff · {chief.provider}
            </div>
            <p className="text-base leading-relaxed">{chief.narrative}</p>
            {chief.problems?.length > 0 && (
              <ul className="mt-3 text-sm text-amber-800 list-disc pl-5">
                {chief.problems.map((p: string) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            )}
          </div>
          <div className="grid md:grid-cols-3 gap-3">
            <Stat label="Meetings" value={chief.all_meeting_scores?.length ?? 0} />
            <Stat label="Longest free" value={`${chief.longest_free_minutes}m`} />
            <Stat label="Deadlines soon" value={chief.upcoming_deadlines?.length ?? 0} />
          </div>
          <Section title="Recommended actions">
            <div className="grid md:grid-cols-2 gap-3">
              {(chief.recommendations || []).map((r: Recommendation) => (
                <RecommendationCard key={r.id} rec={r} onApplied={onApplied} />
              ))}
              {(chief.recommendations || []).length === 0 && (
                <div className="text-sm text-gray-500">No urgent scheduling changes recommended.</div>
              )}
            </div>
          </Section>
          <Section title="Today's schedule">
            <ul className="text-sm space-y-1">
              {(chief.schedule || []).map((e: any) => (
                <li key={e.id}>
                  {e.start_time?.slice(11, 16)}–{e.end_time?.slice(11, 16)} · {e.title}
                </li>
              ))}
              {(chief.schedule || []).length === 0 && <li className="text-gray-500">No events today.</li>}
            </ul>
          </Section>
        </div>
      )}

      {tab === "focus" && focus && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <button
              className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm"
              onClick={async () => {
                const res = await api.protectFocus();
                if (res.proposal_id) {
                  await api.confirmProposal(res.proposal_id);
                  onApplied();
                  load();
                } else {
                  alert("No focus actions to propose — calendar may already be protected.");
                }
              }}
            >
              Protect my focus time
            </button>
            <div className="text-sm text-gray-500 self-center">
              Longest free block: {focus.longest_free_minutes}m
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {(focus.recommendations || []).map((r: Recommendation) => (
              <RecommendationCard key={r.id} rec={r} onApplied={onApplied} />
            ))}
          </div>
        </div>
      )}

      {tab === "importance" && importance && (
        <div className="rounded-xl border bg-white p-4 shadow-sm overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2">Meeting</th>
                <th>Level</th>
                <th>Score</th>
                <th>Suggestion</th>
                <th>Why</th>
              </tr>
            </thead>
            <tbody>
              {(importance.meetings || []).map((m: any) => (
                <tr key={m.event_id} className="border-b align-top">
                  <td className="py-2 pr-2 font-medium">{m.title}</td>
                  <td className="capitalize">{m.level}{m.uncertain ? " ?" : ""}</td>
                  <td>{m.score}</td>
                  <td>{m.suggestion_text}</td>
                  <td className="text-gray-600">{(m.reasons || []).join(" ")}</td>
                </tr>
              ))}
              {(importance.meetings || []).length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-gray-500">
                    No meetings today to score.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "conflicts" && conflicts && (
        <div className="space-y-3">
          {(conflicts.conflicts || []).length === 0 && (
            <div className="text-sm text-gray-500">No overlapping meetings detected.</div>
          )}
          {(conflicts.conflicts || []).map((c: any) => (
            <div key={c.move.id} className="rounded-xl border bg-white p-4 shadow-sm space-y-2">
              <div className="font-semibold text-sm">{c.problem}</div>
              <p className="text-sm text-gray-600">{c.explanation}</p>
              {c.alternatives?.[0] && (
                <button
                  className="rounded-md bg-slate-900 text-white px-3 py-1.5 text-xs"
                  onClick={async () => {
                    const res = await api.proposeConflictResolution(
                      c.move.id,
                      c.alternatives[0].start,
                      c.alternatives[0].end
                    );
                    if (res.proposal_id) {
                      await api.confirmProposal(res.proposal_id);
                      onApplied();
                      load();
                    }
                  }}
                >
                  Approve move to {c.alternatives[0].start.replace("T", " ").slice(0, 16)}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === "buffers" && buffers && (
        <div className="grid md:grid-cols-2 gap-3">
          {(buffers.recommendations || []).map((r: Recommendation) => (
            <RecommendationCard key={r.id} rec={r} onApplied={onApplied} />
          ))}
          {(buffers.recommendations || []).length === 0 && (
            <div className="text-sm text-gray-500">No buffer recommendations for today.</div>
          )}
        </div>
      )}

      {tab === "prefs" && prefs && (
        <form
          className="rounded-xl border bg-white p-4 grid md:grid-cols-3 gap-3 shadow-sm"
          onSubmit={async (e) => {
            e.preventDefault();
            const updated = await api.updatePreferences(prefs);
            setPrefs(updated);
          }}
        >
          {(
            [
              ["work_start_hour", "Work start"],
              ["work_end_hour", "Work end"],
              ["preferred_focus_start", "Focus start"],
              ["preferred_focus_end", "Focus end"],
              ["min_focus_minutes", "Min focus (min)"],
              ["buffer_minutes", "Prep buffer (min)"],
              ["break_minutes", "Break (min)"],
              ["max_consecutive_meeting_minutes", "Max consecutive meetings (min)"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="text-sm font-medium">
              {label}
              <input
                type="number"
                className="mt-1 w-full rounded-lg border px-3 py-2"
                value={prefs[key] ?? ""}
                onChange={(e) => setPrefs({ ...prefs, [key]: Number(e.target.value) })}
              />
            </label>
          ))}
          <label className="text-sm font-medium md:col-span-3">
            Timezone (IANA)
            <input
              className="mt-1 w-full rounded-lg border px-3 py-2"
              value={prefs.timezone || ""}
              onChange={(e) => setPrefs({ ...prefs, timezone: e.target.value })}
            />
          </label>
          <button type="submit" className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm md:col-span-3 w-fit">
            Save preferences
          </button>
        </form>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="font-semibold">{title}</h2>
      {children}
    </section>
  );
}
