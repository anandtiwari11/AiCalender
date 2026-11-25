import { googleConnectUrl } from "@/lib/api";

export function LoginGate({
  oauthConfigured,
  error,
}: {
  oauthConfigured: boolean;
  error?: string | null;
}) {
  return (
    <div className="min-h-screen grid place-items-center px-6">
      <div className="w-full max-w-md text-center fade-up">
        <div className="font-display text-5xl tracking-tight text-[var(--ink)]">Cal.ai</div>
        <p className="mt-3 text-[var(--muted)] text-sm leading-relaxed">
          Sign in with Google to use your real calendar. No guest mode — every schedule, task, and AI
          suggestion runs against your Google account.
        </p>
        {error ? (
          <p className="mt-4 text-sm text-[var(--danger)]">Sign-in failed: {error}</p>
        ) : null}
        {oauthConfigured ? (
          <a
            className="btn btn-primary mt-8 w-full max-w-xs mx-auto"
            href={googleConnectUrl()}
          >
            Continue with Google
          </a>
        ) : (
          <p className="mt-8 text-sm text-[var(--warn)]">
            Google OAuth is not configured on this server yet.
          </p>
        )}
      </div>
    </div>
  );
}
