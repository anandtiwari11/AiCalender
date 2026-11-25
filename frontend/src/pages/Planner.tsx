import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const suggestions = [
  "Make tomorrow less meeting-heavy",
  "Find a free hour for project work tomorrow",
  "Block 2 hours for deep work before lunch",
  "Do I have any overlapping meetings?",
  "What should I prepare for my next meeting?",
];

export function PlannerPage({ refreshKey, onApplied }: { refreshKey: number; onApplied: () => void }) {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [proposals, setProposals] = useState<
    { id: number; summary: string; actions: unknown[] }[]
  >([]);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const res = await api.proposals();
    setProposals(res.proposals);
  };

  useEffect(() => {
    load().catch(console.error);
  }, [refreshKey]);

  const submit = async (text: string) => {
    setBusy(true);
    try {
      const res = await api.chat(text);
      setReply(res.reply);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">AI Planner</h1>
        <p className="text-gray-500">
          Natural language → structured proposal → you confirm → calendar mutation.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-xl border bg-white p-4 space-y-3 shadow-sm">
          <textarea
            className="w-full min-h-28 rounded-lg border p-3 text-sm"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Schedule a 45-minute meeting with Rahul tomorrow at 3 PM."
          />
          <button
            disabled={busy || !message.trim()}
            className="rounded-lg bg-slate-900 text-white px-4 py-2 text-sm disabled:opacity-50"
            onClick={() => submit(message)}
          >
            {busy ? "Generating…" : "Generate proposal"}
          </button>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                className="rounded-full border px-3 py-1 text-xs bg-slate-50"
                onClick={() => {
                  setMessage(s);
                  submit(s);
                }}
              >
                {s}
              </button>
            ))}
          </div>
          {reply && (
            <div className="rounded-lg bg-slate-50 border p-3 text-sm whitespace-pre-wrap">{reply}</div>
          )}
        </div>

        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <h2 className="font-semibold mb-3">Pending proposals</h2>
          {proposals.length === 0 ? (
            <div className="text-sm text-gray-500">No pending proposals.</div>
          ) : (
            <div className="space-y-3">
              {proposals.map((p) => (
                <div key={p.id} className="rounded-lg border p-3">
                  <div className="font-medium mb-2">{p.summary}</div>
                  <pre className="text-[11px] bg-slate-950 text-slate-100 rounded p-2 overflow-auto max-h-28 mb-2">
                    {JSON.stringify(p.actions, null, 2)}
                  </pre>
                  <div className="flex gap-2">
                    <button
                      className="rounded-md bg-slate-900 text-white px-3 py-1.5 text-xs"
                      onClick={async () => {
                        await api.confirmProposal(p.id);
                        await load();
                        onApplied();
                      }}
                    >
                      Confirm & apply
                    </button>
                    <button
                      className="rounded-md border px-3 py-1.5 text-xs"
                      onClick={async () => {
                        await api.dismissProposal(p.id);
                        await load();
                      }}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
