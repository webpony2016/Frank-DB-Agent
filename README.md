# Frank Operations Desk

An independent concept demo for Frank's Drilling & Blasting: an English operations workspace built from the public Upwork brief.

**Sample data only. No live AI calls, external integrations, or messages sent.** Customers, sites, projects and prices are fictional.

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
- Job progression, operational notes, editable customer drafts, and clipboard copying.
- Illustrative QuickBooks, email/calendar and CRM payload previews stored locally.
- Per-visitor workspaces, responsive pages, and a reset action limited to the current workspace.

A fresh quote revision needs approval again. Quotes and assignments become read-only after work starts; quotes also lock once a job is scheduled. An internal approval is not customer acceptance. Totals are illustrative CAD, before tax. Each quote line is rounded to cents using ROUND_HALF_UP, then the rounded lines are summed.

## Configuration and persistence

| Variable | Default | Purpose |
| --- | --- | --- |
| DATABASE_URL | sqlite:///data/frank.db | File-backed local SQLite database |
| APP_ORIGIN | http://127.0.0.1:8000 | Exact permitted host/origin for browser mutations |
| COOKIE_SECURE | false | Set true only for a configured HTTPS deployment |

**.env.example is documentation; the application does not load .env files automatically.** Set variables explicitly before launching when overriding defaults.

```powershell
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '$env:APP_ORIGIN="http://127.0.0.1:8001"; .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001'
```

SQLite schema version 1 is initialized only for a fresh database. An unknown schema/version fails startup rather than replacing data. Back up data/frank.db with the server stopped. Reset sample data uses the application dialog; it never resets another visitor's workspace.

A random HTTP-only cookie identifies each workspace; only its hash is stored in the database. Cookies expire after seven days. Losing the cookie starts a new workspace; this demo has no account recovery. Database rows are retained until a future retention policy is implemented. Do not enter real customer data.

The initial SQLite implementation uses one Uvicorn worker, explicit write transactions, and a bounded busy timeout. It accepts DATABASE_URL as configuration but deliberately rejects non-SQLite databases: PostgreSQL schema/locking behavior has not been implemented or verified.

## Verification

```powershell
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command 'New-Item -ItemType Directory -Force .tmp_pytest | Out-Null; .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp_pytest/check'
rtk "C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -Command '.venv/Scripts/python.exe -m compileall -q app'
```

Use a new basetemp subdirectory for each run if Windows retains handles to previous test files.

Read [DEMO.md](DEMO.md) for the client walkthrough and [VALIDATION.md](VALIDATION.md) for evidence and limits.

## Architecture

FastAPI serves a Jinja2 HTML shell, plain JavaScript/CSS, and workspace-scoped JSON endpoints. SQLAlchemy stores relational records. Domain services own job, quote, scheduling, draft and preview rules; the shared request transaction commits each change with its activity event or rolls it all back.

The sample assistant retrieves prepared example briefs and composes messages from saved job facts. Unrecognized examples request manual entry. No agent framework or model endpoint is invoked.

## Later public deployment

This delivery is local; no public hosting has been provisioned. Before a public release: select durable storage, implement and verify any PostgreSQL migration/locking path, configure HTTPS and secure cookies, add workspace retention/cleanup and abuse limits, then repeat browser and isolation tests against the deployment.

Live QuickBooks, email/calendar, CRM OAuth and LLM providers require separate credentials, verified contracts, permissions and acceptance tests. The previews are illustrative mappings, not vendor-validated API payloads or synchronization receipts.
