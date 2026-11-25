import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Msg = { role: string; content: string };

export function AIPanel({ onApplied }: { onApplied: () => void }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [proposals, setProposals] = useState<
    { id: number; summary: string; actions: unknown[] }[]
  >([]);

  const refresh = async () => {
    const [st, msgs, props] = await Promise.all([
      api.aiStatus(),
      api.messages(),
      api.proposals(),
    ]);
    setStatus(st.label);
    setMessages(msgs.messages.map((m) => ({ role: m.role, content: m.content })));
    setProposals(props.proposals);
  };

  useEffect(() => {
    refresh().catch(console.error);
  }, []);

  const send = async () => {
    const message = input.trim();
    if (!message || busy) return;
    setBusy(true);
    setInput("");
    setMessages((m) => [
      ...m,
      { role: "user", content: message },
      { role: "assistant", content: "Thinking…" },
    ]);
    try {
      const res = await api.chat(message);
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: `${res.reply}\n\n_(${res.mode} · ${res.provider})_`,
        };
        return next;
      });
      await refresh();
    } catch (e) {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: `Error: ${(e as Error).message}`,
        };
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="border-l border-[var(--line)] bg-white/80 backdrop-blur-md h-[100dvh] sticky top-0 flex flex-col">
      <div className="p-5 border-b border-[var(--line)]">
        <div className="font-display text-lg">Assistant</div>
        <div className="text-xs text-[var(--muted)] mt-0.5">Confirm before any calendar change</div>
        <div
          className={`mt-3 inline-flex text-[11px] font-semibold px-2.5 py-1 rounded-full ${
            status.toLowerCase().includes("connected")
              ? "bg-[var(--accent-soft)] text-[var(--accent)]"
              : "bg-[#fff7ed] text-[var(--warn)]"
          }`}
        >
          {status || "…"}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-sm text-[var(--muted)] leading-relaxed px-1">
            Schedule meetings, protect focus time, or ask what your day looks like.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[92%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-[var(--ink)] text-white"
                  : "bg-[#f4f4f1] text-[var(--ink)]"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
      </div>

      {proposals.length > 0 && (
        <div className="border-t border-[var(--line)] p-3 space-y-2 max-h-44 overflow-auto bg-[#fafaf8]">
          {proposals.map((p) => (
            <div key={p.id} className="rounded-xl border border-[var(--line)] bg-white p-3">
              <div className="text-sm font-medium mb-2">{p.summary}</div>
              <div className="flex gap-2">
                <button
                  className="btn btn-primary !py-1.5 !px-3 !text-xs"
                  onClick={async () => {
                    await api.confirmProposal(p.id);
                    await refresh();
                    onApplied();
                  }}
                >
                  Confirm
                </button>
                <button
                  className="btn !py-1.5 !px-3 !text-xs"
                  onClick={async () => {
                    await api.dismissProposal(p.id);
                    await refresh();
                  }}
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="border-t border-[var(--line)] p-3 space-y-2">
        <textarea
          className="input min-h-20 resize-y text-sm"
          placeholder="e.g. Block 90 minutes for deep work tomorrow morning"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button disabled={busy} onClick={send} className="btn btn-primary w-full disabled:opacity-50">
          {busy ? "Working…" : "Send"}
        </button>
      </div>
    </aside>
  );
}
