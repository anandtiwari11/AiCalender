import { FormEvent, useState } from "react";
import { api, googleConnectUrl } from "@/lib/api";

export function LoginGate({
  oauthConfigured,
  error,
  onSignedIn,
}: {
  oauthConfigured: boolean;
  error?: string | null;
  onSignedIn: () => void;
}) {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [normalizedPhone, setNormalizedPhone] = useState("");

  const sendCode = async (e?: FormEvent) => {
    e?.preventDefault();
    setBusy(true);
    setLocalError(null);
    setDevOtp(null);
    try {
      const res = await api.phoneStart(phone);
      setNormalizedPhone(res.phone);
      setStep("otp");
      if (res.dev_otp) setDevOtp(res.dev_otp);
    } catch (err) {
      setLocalError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async (e?: FormEvent) => {
    e?.preventDefault();
    setBusy(true);
    setLocalError(null);
    try {
      await api.phoneVerify(normalizedPhone || phone, code);
      onSignedIn();
    } catch (err) {
      setLocalError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto w-full max-w-md fade-up">
        <div className="font-display text-5xl tracking-tight text-[var(--ink)]">Cal.ai</div>
        <p className="mt-2 text-[var(--accent)] text-sm font-semibold">
          Your time, intelligently managed.
        </p>
        <p className="mt-4 text-[var(--muted)] text-sm leading-relaxed">
          Sign in with your phone to keep your calendar in Cal.ai, or connect Google to manage your
          real Google Calendar. AI proposals always wait for your confirmation.
        </p>

        {error || localError ? (
          <p className="mt-4 text-sm text-[var(--danger)]">
            {localError || `Sign-in failed: ${error}`}
          </p>
        ) : null}

        <div className="mt-8 rounded-2xl border border-[var(--line)] bg-white p-5 shadow-[var(--shadow)] space-y-4">
          <div className="text-sm font-semibold">Continue with phone</div>
          {step === "phone" ? (
            <form onSubmit={sendCode} className="space-y-3">
              <label className="block text-xs text-[var(--muted)]">
                Phone number
                <input
                  className="mt-1 w-full rounded-xl border border-[var(--line)] px-3 py-2.5 text-sm"
                  placeholder="+91 98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  inputMode="tel"
                  autoComplete="tel"
                  required
                />
              </label>
              <button className="btn btn-primary w-full" disabled={busy || !phone.trim()}>
                {busy ? "Sending…" : "Send OTP"}
              </button>
            </form>
          ) : (
            <form onSubmit={verifyCode} className="space-y-3">
              <p className="text-xs text-[var(--muted)]">
                Code sent to <span className="text-[var(--ink)] font-medium">{normalizedPhone}</span>
              </p>
              {devOtp ? (
                <p className="text-xs rounded-lg bg-[var(--accent-soft)] text-[var(--accent)] px-3 py-2">
                  Demo OTP (SMS not configured): <strong>{devOtp}</strong>
                </p>
              ) : null}
              <label className="block text-xs text-[var(--muted)]">
                6-digit code
                <input
                  className="mt-1 w-full rounded-xl border border-[var(--line)] px-3 py-2.5 text-sm tracking-[0.3em]"
                  placeholder="000000"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  required
                />
              </label>
              <button className="btn btn-primary w-full" disabled={busy || code.length < 6}>
                {busy ? "Verifying…" : "Verify & continue"}
              </button>
              <button
                type="button"
                className="text-xs text-[var(--muted)] underline"
                onClick={() => {
                  setStep("phone");
                  setCode("");
                  setDevOtp(null);
                }}
              >
                Use a different number
              </button>
            </form>
          )}
        </div>

        <div className="my-6 flex items-center gap-3 text-xs text-[var(--muted)]">
          <div className="h-px flex-1 bg-[var(--line)]" />
          or
          <div className="h-px flex-1 bg-[var(--line)]" />
        </div>

        {oauthConfigured ? (
          <a className="btn btn-primary w-full" href={googleConnectUrl()}>
            Continue with Google
          </a>
        ) : (
          <p className="text-sm text-[var(--warn)] text-center">
            Google OAuth is not configured on this server yet.
          </p>
        )}

        <p className="mt-8 text-xs text-[var(--muted)] text-center">
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
