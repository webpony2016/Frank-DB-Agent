# Public demo deployment

The user approved a free Render web service in My Workspace and a separate free Neon database, provisioned through the user's existing Vercel-managed Neon installation. This is a fictional-data client demonstration.

## Runtime

- One FastAPI/Uvicorn worker on Render Free, Virginia.
- Independent Neon project frank-operations-demo (wandering-brook-55154107), US East 1, Free plan, built-in Auth disabled.
- Python 3.13.5 and pinned dependencies from requirements.lock.txt.
- Render receives DATABASE_URL as a secret environment variable. No credential is committed.
- APP_ORIGIN defaults to Render's RENDER_EXTERNAL_URL. Local use defaults to http://127.0.0.1:8000.
- HTTPS origins always issue Secure, HttpOnly, SameSite=Lax cookies and HSTS.
- Render refuses startup with SQLite; restart/redeployment must not erase demo edits.

The source repository is private. render.yaml records the service settings; direct service creation uses the same build/start configuration. Database credentials are configured separately.

## Data and limits

Each visitor receives separate fictional records. A workspace and its copied bearer cookie expire on the server after seven days, measured from creation. Expired records are cleaned when a new visitor workspace is created. There is no background cleanup schedule or account recovery.

Capacity is bounded to 100 active workspaces and 200 activity records per workspace. A full visitor workspace can still be reset. API traffic is limited to 120 requests per minute per network address visible to the application; the bounded in-memory limiter resets on restart. The service uses one worker. Database capacity checks and mutations are transactional.

PostgreSQL write transactions acquire one database-wide transaction advisory lock before reading versions or reservations. This intentionally serializes writes for a small demo and protects against conflicting bookings across separate application connections and overlapping deployments. Reads are not globally locked. This is not a high-throughput dispatch service.

New databases initialize schema version 1. Unknown schemas/versions fail without destructive repair. PostgreSQL quote amounts use BIGINT to retain the existing CAD 100 million illustrative limit. The existing SQLite representation already stores 64-bit integers. No user's local records are uploaded; the hosted database starts with fresh fictional workspaces.

## Reproduce tests

Run commands through the required RTK/PowerShell wrapper.

- Default: .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp_pytest/unique-run
- PostgreSQL: set TEST_DATABASE_URL to a direct (non-pooler) connection string, then run the same suite.
- Node: node --test tests/ui.test.mjs

PostgreSQL fixtures create a random frank_test_<uuid> schema for each fixture and drop only that owned schema afterward. Production public tables are not used by these tests. Standalone tests that explicitly construct local SQLite files still run on SQLite in PostgreSQL mode; the shared-fixture workflow, isolation, quota and concurrent-booking cases use PostgreSQL.

## Free-plan behavior

Render Free sleeps after inactivity, so the first request after sleep may wait for startup. Data stays in PostgreSQL while the web process is asleep or redeploying. Free quotas are shared with the account where applicable. No paid plan, live model provider or external business integration is enabled.

## Verification status

Final deployed URL, test counts, independent-review findings and live browser evidence are recorded in VALIDATION.md after deployment. The original local delivery record remains historical.
