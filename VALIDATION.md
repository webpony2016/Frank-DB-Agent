# Validation record

Validated locally on September 23, 2026 (America/Toronto).

## Scope and runtime

- Python 3.13.5; approved PowerShell 7.6.6 through RTK.
- FastAPI application, local SQLite schema version 1, one Uvicorn worker.
- Runtime is sample-only. No API key, live model call, email send, OAuth connection, vendor API request, or public deployment was used.
- Exact installed Python packages are recorded in requirements.lock.txt.

## Automated evidence

The full test run at this stage reported **47 passed**. It covers:

- Workspace creation, isolation, forged cookies, cookie flags and unknown-schema rejection.
- Editable/idempotent inquiry conversion and unsupported-example manual entry.
- Decimal money, per-line rounding, invalid values, total bounds, quote revisions and stale approval.
- Crew/equipment overlap including boundary dates, self-rescheduling and true concurrent database sessions: one winner, one conflict, one event.
- Job transition restrictions, completed-job immutability and stale assignment rejection.
- Saved customer drafts, long-title subject bounds, text preservation and local offline previews.
- Confirmation-gated per-workspace reset, origin checks, request size bounds, and foreign IDs across mutation endpoints.
- Completed future assignments excluded from upcoming totals.
- Full job journey persisted and read through a newly constructed application instance.
- HTML shell and linked static assets are served.

One upstream warning remains: Starlette 1.7.0 deprecates its httpx TestClient adapter in favor of httpx2. The tests pass with the pinned dependency set; this is a test-tool deprecation, not a browser/runtime failure.

Python compileall and JavaScript syntax checks passed. Git whitespace checks passed after removing trailing blank lines. Final independent-review findings and any additional regression checks will be recorded below.

## Browser evidence

Verified in Chrome against http://127.0.0.1:8000:

1. Overview derives current metrics from saved sample records.
2. Inquiry brief is editable; converting it creates FD-1047 and reduces the pending inquiry count.
3. Quantity 2 at CAD 125.55 saves a CAD 251.10 quote. Internal approval unlocks scheduling.
4. Booking Crew Alpha over its existing dates returns a specific conflict. Choosing available dates succeeds.
5. Scheduled → In progress → Completed updates the timeline and locks quote/assignment editing.
6. An HTML-shaped note is visibly literal text: no image node or JavaScript dialog was created.
7. Customer update generation, editing, saving, and copying all work. The visible copy feedback confirms nothing was sent.
8. Browser refresh and a server restart preserve the completed job and edited message.
9. CRM local preview shows the saved completed status, connected=false and sent=false.
10. Search produces a useful no-results state.
11. At an actual 390 CSS-pixel viewport, overview, schedule list and job workspace have no page-wide horizontal overflow. Browser zoom required a 488-pixel viewport override to obtain 390 CSS pixels; the override was reset afterward.
12. The skip link focuses the current main content without navigating away.
13. Reset confirmation replaces only the test visitor's sample workspace; the reset success message is visible and initial counts return.
14. Browser console inspection returned no warning/error entries during the tested journey.

The browser test workspace was reset after verification, leaving a fresh demonstration. Automated tests use separate temporary databases and never reset the user's application database.

## Limits

- No public endpoint or hosted database has been provisioned.
- PostgreSQL migrations/locking, multiple application workers, abuse limits and retention cleanup are deferred.
- Real customer accounts, live AI accuracy, QuickBooks schema compliance, CRM/calendar providers, and email delivery are not validated.
- Generated operational text is a reviewable draft. No engineering or blasting guidance is generated.
- The seven-day visitor cookie is a convenience scope for fictional demo data, not production user authentication.

## Independent review

Pending the fresh reviewer pass after the implementation and local checks.
