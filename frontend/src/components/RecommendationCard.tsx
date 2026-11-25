import { useState } from "react";
import { api } from "@/lib/api";

export type Recommendation = {
  id: string;
  kind: string;
  problem: string;
  explanation: string;
  proposed_action: string;
  expected_benefit: string;
  actions?: unknown[];
  alternatives?: { start: string; end: string; score: number }[];
};

export function RecommendationCard({
  rec,
  onApplied,
}: {
  rec: Recommendation;
  onApplied?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<"idle" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  const approve = async () => {
    if (!rec.actions || rec.actions.length === 0) {
      setMessage("No executable actions for this recommendation.");
      return;
    }
    setBusy(true);
    try {
      const res = await api.proposeRecommendation(
        rec.proposed_action || rec.problem,
        rec.actions,
        rec.kind
      );
      if (!res.proposal_id) {
        setStatus("error");
        setMessage("Could not create proposal.");
        return;
      }
      const confirm = await api.confirmProposal(res.proposal_id);
      setStatus("done");
      setMessage((confirm.results || []).join(" · ") || "Applied.");
      onApplied?.();
    } catch (e) {
      setStatus("error");
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="surface p-4 space-y-3 fade-up">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">
        {rec.kind.replaceAll("_", " ")}
      </div>
      <div className="font-display text-[1.05rem] leading-snug">{rec.problem}</div>
      <p className="text-sm text-[var(--muted)] leading-relaxed">{rec.explanation}</p>
      <div className="text-sm">
        <span className="font-semibold">Proposed</span>
        <div className="text-[var(--muted)] mt-0.5">{rec.proposed_action}</div>
      </div>
      <div className="text-sm">
        <span className="font-semibold">Benefit</span>
        <div className="text-[var(--muted)] mt-0.5">{rec.expected_benefit}</div>
      </div>
      {rec.alternatives?.[0] && (
        <div className="text-xs text-[var(--muted)]">
          Top alternative: {rec.alternatives[0].start.replace("T", " ").slice(0, 16)}
        </div>
      )}
      <div className="flex gap-2 pt-1">
        <button
          disabled={busy || !rec.actions?.length || status === "done"}
          onClick={approve}
          className="btn btn-primary !text-xs disabled:opacity-40"
        >
          {busy ? "Applying…" : status === "done" ? "Applied" : "Approve"}
        </button>
        <button disabled={busy} onClick={() => setStatus("done")} className="btn !text-xs">
          Reject
        </button>
      </div>
      {message && <div className="text-xs text-[var(--muted)]">{message}</div>}
    </div>
  );
}
