import { googleConnectUrl } from "@/lib/api";

export function LoginGate({
  oauthConfigured,
  error,
}: {
  oauthConfigured: boolean;
  error?: string | null;
}) {
  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto w-full max-w-xl fade-up">
        <div className="font-display text-5xl tracking-tight text-[var(--ink)]">Cal.ai</div>
        <p className="mt-2 text-[var(--accent)] text-sm font-semibold">
          Your time, intelligently managed.
        </p>
        <p className="mt-4 text-[var(--muted)] text-sm leading-relaxed">
          AI-native calendar for business professionals. Cal.ai connects to your Google Calendar to
          protect focus time, prioritize meetings, catch conflicts, and schedule in natural language —
          with confirm-before-write so nothing changes until you approve.
        </p>

        <ul className="mt-6 space-y-2 text-sm text-[var(--ink)]">
          <li>• Live Google Calendar read &amp; write</li>
          <li>• Chief of Staff briefing, Focus Protector, Meeting Priority</li>
          <li>• Gemini assistant that proposes; you confirm</li>
        </ul>

        {error ? (
          <p className="mt-4 text-sm text-[var(--danger)]">Sign-in failed: {error}</p>
        ) : null}

        {oauthConfigured ? (
          <a className="btn btn-primary mt-8 inline-flex" href={googleConnectUrl()}>
            Continue with Google
          </a>
        ) : (
          <p className="mt-8 text-sm text-[var(--warn)]">
            Google OAuth is not configured on this server yet.
          </p>
        )}

        <p className="mt-8 text-xs text-[var(--muted)]">
          Learn more without signing in:{" "}
          <a className="underline text-[var(--accent)]" href="/about">
            About
          </a>
          {" · "}
          <a className="underline text-[var(--accent)]" href="/privacy">
            Privacy Policy
          </a>
          {" · "}
          <a className="underline text-[var(--accent)]" href="/terms">
            Terms
          </a>
        </p>
      </div>
    </div>
  );
}
