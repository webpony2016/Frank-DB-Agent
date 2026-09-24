# Validation record

## Public deployment — September 24, 2026

**Live demo:** https://frank-operations-demo.onrender.com
**Source:** https://github.com/webpony2016/Frank-DB-Agent
**Runtime:** sample-only. No live LLM call, email delivery, OAuth business connection or external vendor API call.

- Render service frank-operations-demo, Free plan, Virginia, one Python 3.13.5 Uvicorn worker.
- Dedicated Neon project frank-operations-demo, Free plan, US East 1. Built-in Neon Auth disabled.
- Hosted data is PostgreSQL; local SQLite data was not uploaded.
- Render reported live for initial deploy dep-daqaa9942hec738umq00 and health-setting redeploy dep-daqabtnf3r2c73akqer0.
- Service health check is /health. HTTPS returns mode=sample and schema_version=1.
- Application code reviewed and tested at b816a80; later commits update deployment documentation.

### Automated checks

- **56 tests passed** in PostgreSQL test mode, 565.99 seconds. Shared fixtures use independent random schemas in the real Neon database, covering persisted workflows, isolation, quote boundaries, stale versions, concurrent scheduling, reset, expiry and quotas. Standalone local-file tests still use SQLite by design.
- SQLite full suite: **55 passed** before the added maximum-valid-quote regression; the final hosting subset including that regression: **9 passed**.
- Node frontend regressions: **6 passed**.
- Python compileall and Git whitespace checks passed.
- The eight initial hosting tests were observed failing before implementation; all pass after the changes. Added a valid CAD 100 million quote round-trip to exercise PostgreSQL BIGINT.
- One pinned Starlette TestClient deprecation warning remains; it concerns the test adapter, not a live browser failure.

### Live HTTP checks

A dedicated disposable visitor completed the actual hosted API journey:

1. Secure, HttpOnly, SameSite=Lax cookie, HSTS and no-store API responses.
2. A second visitor receives different records; foreign job IDs return 404.
3. Mutations from another origin return 403.
4. Convert an inquiry, save CAD 251.10, approve, assign resources.
5. Competing reservation receives 409.
6. Start and complete the job, save a note, generate and edit a customer draft.
7. CRM preview returns mode=sample, connected=false and sent=false.
8. After the health-setting redeploy finished live, reusing the original visitor cookie returned the exact saved job, quote, assignment, activities and message. This verifies persistence across a real hosted process replacement.
9. Render error-log inspection returned no error entries during the initial checks.

### Public browser checks

Chrome loaded the public HTTPS endpoint and initialized its own workspace. The browser journey converted Cedar Ridge access road, saved a 2 × CAD 125.55 quote, approved it, scheduled Crew Alpha/Rig 01 for October 1–2, started and completed the job, then generated and edited a customer update. A page reload retained the completed job and edited message. Console inspection returned no errors or warnings. Reset restored the browser visitor's initial fictional examples, and the overview was left open.

The original local build's 390 CSS-pixel layout verification remains applicable to the unchanged frontend assets. A new hosted mobile-size check was not counted: the viewport override did not affect the intended public tab and was reset.

### Independent deployment review

A separate read-only review of the public-hosting changes found **no Critical or Important defects**. It checked transaction-level PostgreSQL locking, atomic capacity enforcement, 64-bit quote cents, server-enforced expiry, cleanup order, HTTPS settings, Render's SQLite guard and temporary test-schema isolation. The reviewer did not read credentials or operate cloud resources.

The reviewer verified that Render's native Python runtime supplies FORWARDED_ALLOW_IPS, consumed by Uvicorn. Actual shared quotas, provider uptime and cold-start time are not guaranteed by these application checks.

## Original local MVP — September 23, 2026

The local baseline passed 47 Python tests and 6 frontend tests, plus the inquiry-to-completion browser journey, clipboard feedback, literal HTML rendering, empty search, reload/server-restart persistence, keyboard skip focus and a 390 CSS-pixel responsive check.

The original whole-project reviewer found two Important UI issues: saving one form discarded unsaved edits elsewhere; notes older than eight events were inaccessible. Both were reproduced, covered with RED-to-GREEN regressions and fixed with an explicit keep/discard choice and expandable activity history. No Minor findings were deferred.

## Current limits

- Render Free sleeps with inactivity. A cold start may delay the first visit by around a minute or longer.
- Workspaces expire seven days after creation. Expired tokens are rejected immediately; record cleanup occurs when a new workspace is created.
- Limits: 100 active workspaces, 200 activity records per workspace, 120 API requests per minute per network address. Rate counters are in-memory and reset with the single process.
- This is a fictional-data public demo, not a production authentication or engineering system. Do not enter real customer information.
- Live AI accuracy, QuickBooks/CRM/calendar vendor contracts, email delivery, paid hosting, multi-worker scaling and distributed abuse controls are outside this delivery.
- Historical deployment deferrals in docs/implementation-record.md describe the earlier local-only milestone; PostgreSQL, hosting, session expiry and basic limits are now implemented as documented above.
