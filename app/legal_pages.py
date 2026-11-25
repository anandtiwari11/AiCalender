"""Public legal / marketing HTML pages for Google OAuth branding checks."""

ABOUT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cal.ai — Your time, intelligently managed</title>
  <meta name="description" content="Cal.ai is an AI-native calendar that manages your Google Calendar with confirm-before-write scheduling assistance." />
  <style>
    :root { color-scheme: light; }
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; color: #171717;
      background: radial-gradient(1200px 600px at 10% -10%, #eef7f4 0%, transparent 55%), #f7f7f5; }
    main { max-width: 44rem; margin: 0 auto; padding: 3rem 1.25rem 4rem; line-height: 1.55; }
    h1 { font-size: 2.4rem; letter-spacing: -0.03em; margin: 0 0 0.4rem; }
    .tag { color: #0f766e; font-weight: 600; margin: 0 0 1.25rem; }
    h2 { font-size: 1.15rem; margin: 1.75rem 0 0.5rem; }
    p, li { color: #404040; }
    a { color: #0f766e; }
    .cta { display: inline-block; margin-top: 1.5rem; background: #171717; color: #fff !important;
      text-decoration: none; padding: 0.7rem 1.1rem; border-radius: 10px; font-weight: 600; }
    nav { margin-top: 2rem; font-size: 0.95rem; }
    nav a { margin-right: 1rem; }
  </style>
</head>
<body>
  <main>
    <h1>Cal.ai</h1>
    <p class="tag">Your time, intelligently managed.</p>
    <p>
      Cal.ai is an AI-native calendar app for business professionals. It connects to your
      <strong>Google Calendar</strong> and helps you protect focus time, prioritize meetings,
      detect conflicts, and schedule with natural language — without silently changing your calendar.
    </p>
    <h2>What it does</h2>
    <ul>
      <li>Reads your live Google Calendar and free/busy data</li>
      <li>Proposes focus blocks, buffers, and reschedules using AI (Google Gemini)</li>
      <li>Applies changes only after you confirm (confirm-before-write)</li>
      <li>Provides Today briefing, Workspace intelligence, Planner, Tasks, and Insights</li>
    </ul>
    <h2>Who it is for</h2>
    <p>Engineers, product managers, founders, and executives who need uninterrupted deep work amid meetings and deadlines.</p>
    <a class="cta" href="/">Open the app</a>
    <nav>
      <a href="/privacy">Privacy Policy</a>
      <a href="/terms">Terms of Service</a>
    </nav>
  </main>
</body>
</html>
"""

PRIVACY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cal.ai Privacy Policy</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; max-width: 44rem;
      margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.55; color: #171717; }
    h1 { font-size: 1.75rem; } h2 { font-size: 1.1rem; margin-top: 1.6rem; }
    p, li { color: #404040; } a { color: #0f766e; }
  </style>
</head>
<body>
  <p><a href="/about">← Cal.ai home</a></p>
  <h1>Cal.ai Privacy Policy</h1>
  <p><strong>Last updated:</strong> November 25, 2025</p>
  <p>
    This Privacy Policy describes how Cal.ai (&quot;we&quot;, &quot;the App&quot;) collects, uses, stores,
    and shares information when you use https://calai-qe3a.onrender.com and related services.
  </p>

  <h2>1. Who we are</h2>
  <p>
    Cal.ai is a prototype AI calendar application that helps users manage their Google Calendar.
    Contact for privacy questions: the developer email shown on the Google OAuth consent screen
    for this application (support / developer contact).
  </p>

  <h2>2. Information we collect</h2>
  <p>Depending on how you use the App, we may collect:</p>
  <ul>
    <li><strong>Google account identity:</strong> Google user id, name, email address, and profile picture, when you sign in with Google.</li>
    <li><strong>Google Calendar data:</strong> event titles, descriptions, times, attendees (if present), locations, and free/busy information that you authorize via Google OAuth scopes.</li>
    <li><strong>App-generated data:</strong> tasks you create in Cal.ai, AI chat messages, pending proposals, preference settings (work hours, focus windows, timezone), and action audit logs.</li>
    <li><strong>Technical data:</strong> session cookies needed to keep you signed in, and standard server logs (IP, timestamps, request paths) for reliability and security.</li>
  </ul>

  <h2>3. How we use information</h2>
  <ul>
    <li>To authenticate you and maintain your session</li>
    <li>To display and manage your Google Calendar inside Cal.ai</li>
    <li>To compute scheduling insights (focus protection, meeting priority, conflicts, buffers)</li>
    <li>To generate AI suggestions via Google Gemini using calendar/task context you provide through the App</li>
    <li>To apply calendar create/update/delete actions <strong>only after you explicitly confirm</strong></li>
    <li>To operate, debug, and secure the service</li>
  </ul>

  <h2>4. Legal basis / consent</h2>
  <p>
    Access to Google user data is granted only after you complete Google&apos;s OAuth consent flow.
    You may revoke access at any time in your Google Account permissions.
  </p>

  <h2>5. How we share information</h2>
  <p>We do not sell personal data. We share data only as needed to run the App:</p>
  <ul>
    <li><strong>Google Calendar API</strong> — to read and write calendar events you authorize</li>
    <li><strong>Google Gemini API</strong> — to generate natural-language scheduling replies and structured proposals from prompts that may include calendar context</li>
    <li><strong>Hosting providers</strong> (e.g. Render) — infrastructure that stores application data and serves the App</li>
  </ul>
  <p>We do not use Google user data to serve advertisements, and we do not allow human review of Google user data except as needed for security, abuse investigation, or legal compliance.</p>

  <h2>6. Storage and retention</h2>
  <ul>
    <li>OAuth access and refresh tokens are stored on our servers so the App can call Google APIs on your behalf.</li>
    <li>Tasks, preferences, AI messages, and proposals are stored in our application database.</li>
    <li>You may request deletion of your Cal.ai account data by contacting the developer email on the OAuth consent screen. You can also remove Cal.ai from your Google Account to revoke API access.</li>
  </ul>

  <h2>7. Security</h2>
  <p>
    We use HTTPS in production, HttpOnly session cookies, and keep Google OAuth client secrets and tokens on the server (not in the browser).
    No method of transmission or storage is 100% secure; use the App with that understanding, especially while it is a prototype.
  </p>

  <h2>8. Children</h2>
  <p>Cal.ai is intended for business professionals and is not directed at children under 13. We do not knowingly collect data from children.</p>

  <h2>9. Changes</h2>
  <p>We may update this policy as the product evolves. The &quot;Last updated&quot; date at the top will change when we do.</p>

  <h2>10. Contact</h2>
  <p>
    Questions about this policy or your data: use the developer contact email listed on the Google OAuth consent screen for Cal.ai.
  </p>

  <p><a href="/about">About Cal.ai</a> · <a href="/terms">Terms of Service</a> · <a href="/">Open app</a></p>
</body>
</html>
"""

TERMS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Cal.ai Terms of Service</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; max-width: 44rem;
      margin: 2rem auto; padding: 0 1.25rem 3rem; line-height: 1.55; color: #171717; }
    h1 { font-size: 1.75rem; } h2 { font-size: 1.1rem; margin-top: 1.6rem; }
    p, li { color: #404040; } a { color: #0f766e; }
  </style>
</head>
<body>
  <p><a href="/about">← Cal.ai home</a></p>
  <h1>Cal.ai Terms of Service</h1>
  <p><strong>Last updated:</strong> November 25, 2025</p>
  <p>By using Cal.ai you agree to these terms.</p>
  <h2>Service</h2>
  <p>Cal.ai is a prototype that helps you manage Google Calendar with AI assistance. Features may change or break without notice.</p>
  <h2>Your responsibilities</h2>
  <ul>
    <li>Provide accurate account information and keep your Google account secure</li>
    <li>Review AI proposals before confirming calendar changes</li>
    <li>Use the App in compliance with Google&apos;s terms and applicable law</li>
  </ul>
  <h2>Disclaimer</h2>
  <p>The App is provided &quot;as is&quot; without warranties of any kind. We are not liable for missed meetings, incorrect schedules, or data loss arising from use of this prototype.</p>
  <h2>Privacy</h2>
  <p>See our <a href="/privacy">Privacy Policy</a> for how data is handled.</p>
  <p><a href="/about">About Cal.ai</a> · <a href="/privacy">Privacy Policy</a> · <a href="/">Open app</a></p>
</body>
</html>
"""
