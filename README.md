# Frank Operations Desk

An independent concept demo for Frank's Drilling & Blasting: an English operations workspace built from the public Upwork brief.

**Sample data only. No live AI calls, external integrations, or messages sent.** Customers, sites, projects and prices are fictional.

[Open the public demo](https://frank-operations-demo.onrender.com) — no login required. Free hosting may take around a minute or longer to wake after inactivity.

## Run locally on Windows

Tested with Python 3.13.5. PowerShell 7.6.6 was explicitly approved for this session. All commands run through RTK from this project directory.

Create the environment and install the exact tested dependencies:

```powershell
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command 'python -m venv .venv'
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '.venv/Scripts/python.exe -m pip install -r requirements.lock.txt'
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
```

Open **http://127.0.0.1:8000**. Use that exact origin; the default configuration does not treat localhost as an alias. The first visit creates a private sample workspace, with no account or API key required. Stop the server with Ctrl+C.

The running server must restart after Python changes. Browser assets load on refresh.

## What works

- Overview with metrics calculated from persisted records.
- Three sample customer inquiries, editable structured job briefs, and duplicate-safe job creation.
- Decimal quote calculations, immutable revisions, internal approval, and stale-version protection.
- Whole-day crew and equipment assignments with inclusive date conflict checking.
- Job progression, operational notes, expandable activity history, editable customer drafts, and clipboard copying.
- Illustrative QuickBooks, email/calendar and CRM payload previews stored within the demo database.
- Per-visitor workspaces, responsive pages, and a reset action limited to the current workspace.

When another job form has unsaved edits, saving asks whether to keep editing or explicitly discard those other edits. Save changes before navigating away or reloading. A fresh quote revision needs approval again. Quotes and assignments become read-only after work starts; quotes also lock once a job is scheduled. An internal approval is not customer acceptance. Totals are illustrative CAD, before tax. Each quote line is rounded to cents using ROUND_HALF_UP, then the rounded lines are summed.

## Configuration and persistence

| Variable | Default | Purpose |
| --- | --- | --- |
| DATABASE_URL | sqlite:///data/frank.db | Local SQLite or hosted PostgreSQL connection |
| APP_ORIGIN | RENDER_EXTERNAL_URL when hosted, otherwise http://127.0.0.1:8000 | Exact permitted host/origin for browser mutations |
| COOKIE_SECURE | false locally; automatically true for HTTPS | Secure visitor cookie |

**.env.example is documentation; the application does not load .env files automatically.** Set variables explicitly before launching when overriding defaults.

```powershell
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '$env:APP_ORIGIN="http://127.0.0.1:8001"; .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001'
```

SQLite schema version 1 is initialized only for a fresh database. An unknown schema/version fails startup rather than replacing data. Back up data/frank.db with the server stopped. Reset sample data uses the application dialog; it never resets another visitor's workspace.

A random HTTP-only cookie identifies each workspace; only its hash is stored in the database. The cookie and server-side workspace access expire seven days after workspace creation, including replay of a copied token. Losing the cookie starts a new workspace; this demo has no account recovery. Expired workspace rows are cleaned when a new visitor workspace is created. Do not enter real customer data.

Local SQLite and hosted PostgreSQL are supported. Use one Uvicorn worker. SQLite uses explicit write transactions and a bounded busy timeout; PostgreSQL uses transaction advisory locks to serialize demo writes. Render refuses SQLite to prevent loss on its ephemeral filesystem. HTTPS enables secure cookies automatically.

## Verification

```powershell
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command 'New-Item -ItemType Directory -Force .tmp_pytest | Out-Null; .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp_pytest/check'
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '.venv/Scripts/python.exe -m compileall -q app'
```

Use a new basetemp subdirectory for each run if Windows retains handles to previous test files. Frontend regressions use Node 22.17.1 and its built-in test runner (no npm dependencies): run node --test tests/ui.test.mjs through the same RTK/PowerShell wrapper.

Read [DEMO.md](DEMO.md) for the client walkthrough and [VALIDATION.md](VALIDATION.md) for evidence and limits.

## Architecture

FastAPI serves a Jinja2 HTML shell, plain JavaScript/CSS, and workspace-scoped JSON endpoints. SQLAlchemy stores relational records. Domain services own job, quote, scheduling, draft and preview rules; the shared request transaction commits each change with its activity event or rolls it all back.

The sample assistant retrieves prepared example briefs and composes messages from saved job facts. Unrecognized examples request manual entry. No agent framework or model endpoint is invoked.

## Public deployment

The approved public setup uses Render Free with a dedicated Neon PostgreSQL database. See docs/DEPLOYMENT.md for configuration, retention, capacity limits, test isolation and free-tier cold starts. The user approved publishing this sample-only source repository. Use VALIDATION.md for current deployment evidence.

Live QuickBooks, email/calendar, CRM OAuth and LLM providers require separate credentials, verified contracts, permissions and acceptance tests. The previews are illustrative mappings, not vendor-validated API payloads or synchronization receipts.
