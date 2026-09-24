# Frank Operations Desk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a locally runnable English operations demo that takes fictional inquiries through quote approval, conflict-checked scheduling, job completion, and saved customer-update drafts.

**Architecture:** One FastAPI application serves a template shell, plain JavaScript/CSS, and workspace-scoped JSON APIs. SQLAlchemy persists records in SQLite; domain services own transactions and workflow rules. Deterministic sample assistant outputs and integration previews clearly identify their provenance and never call external services.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, Uvicorn, Jinja2, pytest, httpx, tzdata, plain JavaScript and CSS. Resolve compatible releases during implementation and save exact tested dependencies in `requirements.lock.txt`.

**Spec:** `docs/superpowers/specs/2026-09-24-frank-operations-demo-design.md` (approved).

## Global Constraints

- Build an English-language demonstration for an Upwork prospective client, using fictional sample data.
- Branding must identify it as an independent concept demo rather than an official company system.
- A persistent **Sample data · No live integrations** indicator explains the execution mode.
- No live LLM dependency or credential is required.
- All changes and activity events persist together in transactions. Workflow state validation is enforced on the backend.
- The server establishes an opaque visitor workspace through an HTTP-only cookie. Records and metrics are scoped to that workspace. IDs alone never grant access to another visitor's records.
- Scheduled work uses whole-day, inclusive Toronto date ranges.
- The job progression is Draft → Quoted → Scheduled → In progress → Completed.
- This initial scope includes a locally runnable app and deployment instructions.
- Keep all work in `Frank-DB-Agent`; do not stage or modify sibling files.
- The user explicitly approved using PowerShell 7.6.6 for this task through RTK.
- Every Windows shell command runs as `rtk 'C:\Program Files\PowerShell\7\pwsh.exe' -NoLogo -NoProfile -Command '<command>'`. Commands below show the inner command; preserve this wrapper when executing them.

## Review Focus

1. Two open tabs attempt to approve different quote revisions: only the current revision can be approved; cover in Task 3.
2. Two assignments compete for the same crew or equipment: one must receive a conflict, including shared boundary dates; cover in Task 4.
3. A browser carries a forged, expired, or another visitor's object identifier: never reveal or mutate another workspace; cover in Tasks 1 and 2.
4. A user enters HTML in a site, note, quote description, or message: render it as text; cover request storage in Task 5 and browser rendering in Task 6.
5. Seeding near Toronto midnight or a reset/reload creates misleading data: use Toronto dates, seed once, preserve other visitors; cover in Tasks 1 and 7.

## Files and responsibilities

| Files | Responsibility |
| --- | --- |
| `pyproject.toml`, `requirements.lock.txt`, `.gitignore`, `.env.example` | Dependencies, pytest configuration, ignored local state, documented configuration |
| `app/__init__.py`, `app/main.py`, `app/config.py` | App factory, lifecycle, shell/health endpoints, environment settings |
| `app/db.py`, `app/models.py`, `app/seed.py` | Engine/session management, relational records, explicit schema version and fictional fixtures |
| `app/workspaces.py`, `app/errors.py`, `app/schemas.py` | Workspace cookies, request scope/origin checks, domain errors, validated inputs |
| `app/jobs.py`, `app/quotes.py`, `app/scheduling.py` | Business operations and transactional state transitions |
| `app/assistant.py`, `app/communications.py`, `app/integrations.py` | Sample provider, draft lifecycle, local integration previews |
| `app/api.py`, `app/serializers.py` | Thin HTTP routing and explicit scoped response shapes |
| `app/templates/index.html`, `app/static/styles.css` | Accessible shell and responsive layout |
| `app/static/api.js`, `app/static/app.js`, `app/static/views.js`, `app/static/job.js` | Request/error handling, navigation, list views, job workspace |
| `tests/conftest.py`, `tests/test_workspaces.py`, `tests/test_jobs.py` | Shared fixtures, isolation, intake |
| `tests/test_quotes.py`, `tests/test_scheduling.py`, `tests/test_communications.py`, `tests/test_journey.py` | Domain regression tests and end-to-end API journey |
| `README.md`, `DEMO.md`, `VALIDATION.md` | Setup, short demonstration script, measured validation and limitations |

## Shared API and data contracts

All IDs are UUID strings. Foreign-workspace IDs return 404 without identifying their owner. Error responses use `{"detail":"Human-readable message"}` and status 404, 409 (workflow/version/conflict), 413 (request size), or 422 (invalid values). Pydantic field errors are formatted for browser display. Mutation requests require an exact configured origin; the app defaults to `http://127.0.0.1:8000`. Missing Origin on mutations is rejected. Responses containing workspace data use `Cache-Control: no-store`.

`create_app(database_url: str | None = None, origin: str | None = None) -> FastAPI` creates an app with its own database engine. Tests use isolated file-backed SQLite databases, not a shared developer database. Schema version 1 is created explicitly on fresh databases; unsupported versions fail startup with an actionable message rather than overwriting data. Enable SQLite foreign keys and a bounded busy timeout. Local deployment uses one Uvicorn worker. Write operations acquire SQLite's write reservation (`BEGIN IMMEDIATE`) before reading mutable workflow state. This serializes quote approvals and reservations in the initial SQLite implementation. PostgreSQL deployment needs its own verified locking/migration path before release.

`read_session(request: Request) -> Iterator[Session]` opens a read session. `write_session(request: Request) -> Iterator[Session]` opens a transaction before yielding, commits on success, and rolls back on exceptions. Services take `(session: Session, workspace_id: str, ...)`, flush as necessary, and never commit independently. `require_job(session, workspace_id, job_id) -> Job` is the only service entry for resolving a job ID. `DomainError(status: int, message: str)` maps to the response contract.

Core tables: `Workspace`, `Customer`, `Inquiry`, `Job`, `Quote`, `QuoteLine`, `Crew`, `Equipment`, `Assignment`, `CommunicationDraft`, `ActivityEvent`, `IntegrationPreview`, `SchemaVersion`. Every business record includes `workspace_id`; every query constrains it. `Job` has `source_inquiry_id` (unique per workspace), `status`, and `version`. `Quote` has a unique `(job_id, revision)`, frozen line items after creation, `state` (`draft`/`approved`), and exact cents total. `Assignment` has one row per job and inclusive start/end dates. A quote save creates a new immutable draft revision, including edits to a draft; approval only changes approval state. All mutable job operations accept `expected_version` and increment the job version. Missing or stale versions cannot silently overwrite changes.

Endpoints:

| Method and path | Request / response |
| --- | --- |
| GET `/health` | `{"status":"ok","mode":"sample","schema_version":1}` |
| GET `/api/bootstrap` | `mode`, `business_date`, `customers`, `inquiries`, `jobs`, `crews`, `equipment`, `assignments`, `metrics`, `activity`; initializes workspace once |
| POST `/api/inquiries/{id}/brief` | `{"mode":"sample","provenance":"prepared-example","brief":{customer_id,title,site,service,requested_start,requested_end,missing_information}}` |
| POST `/api/inquiries/{id}/job` | Edited brief fields; returns job detail (201 new / 200 existing) |
| GET `/api/jobs/{id}` | `id`, `version`, `status`, fields, `quotes`, `assignment`, `drafts`, `activity` |
| POST `/api/jobs/{id}/quotes` | `expected_version`, `lines:[{description,quantity,unit_price}]`; returns updated job detail |
| POST `/api/jobs/{id}/quotes/{quote_id}/approve` | `expected_version`; returns updated job detail |
| PUT `/api/jobs/{id}/assignment` | `expected_version`, `crew_id`, `equipment_id`, `start_date`, `end_date`; returns updated job detail |
| POST `/api/jobs/{id}/status` | `expected_version`, `status` (`in_progress`/`completed`); returns updated job detail |
| POST `/api/jobs/{id}/notes` | `expected_version`, `text`; returns updated job detail |
| POST `/api/jobs/{id}/drafts` | `expected_version`; generates a stored sample update draft; returns updated job detail |
| PUT `/api/jobs/{id}/drafts/{draft_id}` | `expected_version`, `subject`, `body`; returns updated job detail |
| GET `/api/integrations` | Connector cards, field mappings, local dry-run events; always not connected |
| POST `/api/jobs/{id}/integration-previews` | `expected_version`, `connector` (`quickbooks`/`email_calendar`/`crm`); persists local preview; returns updated job detail with `preview` |
| POST `/api/reset` | `{"confirm":true}`; deletes/reseeds current workspace's business records only; returns bootstrap |

Dates use ISO `YYYY-MM-DD`; UI labels use Toronto business dates without browser-timezone conversion. Money is CAD before tax, displayed with two decimals and labeled illustrative. Request bodies are bounded at 64 KiB. Titles/site fields: 1–200 characters; descriptions: 1–300; notes/drafts: 1–4000; quote lines: 1–30. Quantity: 0–100000 with up to three decimal places; price: 0–1000000 with at most two decimal places. Reject nonfinite inputs and negative values. Round each line with `ROUND_HALF_UP`, sum integer cents, and reject totals over CAD 100000000.00.

### Task 1: Persisted demo workspace and seeded overview API

**Files:** Create environment files, `app/__init__.py`, `app/main.py`, `app/config.py`, `app/db.py`, `app/models.py`, `app/seed.py`, `app/workspaces.py`, `app/errors.py`, `app/api.py`, `app/serializers.py`, `tests/conftest.py`, `tests/test_workspaces.py`.

**Interfaces:** Produces `create_app`, `read_session`, `write_session`, `DomainError`, `seed_workspace(session, workspace_id, today: date) -> None`, `business_date() -> date`, and the `/health` and `/api/bootstrap` contracts. Test fixtures produce `app`, `client`, and `other_client`.

- [x] Check exact Python/runtime and dependency availability through RTK. Create project-local Git metadata with `git init -b codex/frank-operations-demo` only after confirming `.git` is absent here. Never use the parent repository for staging. Add `.venv/`, `data/`, `.env`, `.pytest_cache/`, `__pycache__/`, `.tmp_pytest/`, and local logs to `.gitignore`.
- [x] Create an isolated virtual environment and install the listed dependencies from the normal package registry. Configure pytest to import `app` from the repository root. Tests and seed data must not depend on network access or a model credential.
- [x] Write the first workspace tests with these fixtures and assertions:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def app(tmp_path):
    return create_app(f"sqlite:///{tmp_path / 'test.db'}", "http://testserver")

@pytest.fixture
def client(app):
    with TestClient(app, headers={"Origin": "http://testserver"}) as c:
        c.get("/api/bootstrap")
        yield c

@pytest.fixture
def other_client(app):
    with TestClient(app, headers={"Origin": "http://testserver"}) as c:
        c.get("/api/bootstrap")
        yield c

# tests/test_workspaces.py
def test_workspace_seeds_once_and_is_isolated(client, other_client):
    one = client.get("/api/bootstrap").json()
    again = client.get("/api/bootstrap").json()
    two = other_client.get("/api/bootstrap").json()
    assert one["mode"] == "sample"
    assert one["jobs"] and one["inquiries"]
    assert [j["id"] for j in one["jobs"]] == [j["id"] for j in again["jobs"]]
    assert {j["id"] for j in one["jobs"]}.isdisjoint(j["id"] for j in two["jobs"])
    assert client.get("/api/bootstrap").headers["cache-control"] == "no-store"
```

- [x] Run `.venv\Scripts\python.exe -m pytest tests/test_workspaces.py -q -p no:cacheprovider --basetemp=.tmp_pytest/task1-red`; expect collection failure until `create_app` exists. Implement app, tables, cookie setup, seed, and bootstrap. Generate a cryptographically random workspace token with `secrets.token_urlsafe(32)` and store only its SHA-256 hash. Unknown tokens create fresh workspaces, never attach to a caller-supplied workspace ID. Cookie is HttpOnly and SameSite=Lax; secure mode is configurable for later HTTPS hosting.
- [x] Create 3 fictional inquiries, 6 jobs across workflow states, 3 crews, and 3 equipment units. Resource reservations must be internally consistent. Build metrics from queries instead of hardcoded KPI values. Date helper implementation:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

def business_date():
    return datetime.now(ZoneInfo("America/Toronto")).date()
```

- [x] Add a time-boundary unit check that converts `2026-09-24T02:30:00+00:00` to Toronto date `2026-09-23`, verify generated assignments use the injected seed date, and verify a malformed cookie receives a new dataset. Verify cookie flags and unsupported schema rejection. Rerun Task 1 tests until green.
- [x] Stage only the Task 1 files in the project-local repository and commit with `feat: add isolated persisted sample workspaces`.

### Task 2: Inquiry-to-job workflow with editable briefs

**Files:** Create `app/jobs.py`, `app/schemas.py`, `app/assistant.py`, `tests/test_jobs.py`; extend API/serializers and shared fixtures.

**Interfaces:** Consumes workspace/session infrastructure. Produces `require_job`, `get_job_detail(session, workspace_id, job_id) -> dict`, `prepare_brief(session, workspace_id, inquiry_id) -> dict`, `convert_inquiry(session, workspace_id, inquiry_id, brief: JobBriefInput) -> tuple[Job, bool]`. `JobBriefInput` defines the brief fields in the API table; `missing_information` is output-only. The assistant returns provenance and never updates jobs by itself.

- [x] Add the reusable `new_job(client) -> dict` test helper in `tests/conftest.py`:

```python
def new_job(client):
    inquiry = next(i for i in client.get("/api/bootstrap").json()["inquiries"] if not i["job_id"])
    brief = client.post(f"/api/inquiries/{inquiry['id']}/brief").json()["brief"]
    brief.pop("missing_information", None)
    response = client.post(f"/api/inquiries/{inquiry['id']}/job", json=brief)
    assert response.status_code == 201, response.text
    return response.json()
```

- [x] Write tests for idempotent conversion, edited site persistence, and foreign IDs:

```python
from conftest import new_job

def test_job_ids_do_not_bypass_workspace(client, other_client):
    job = new_job(client)
    assert other_client.get(f"/api/jobs/{job['id']}").status_code == 404

def test_conversion_is_idempotent(client):
    inquiry = next(i for i in client.get("/api/bootstrap").json()["inquiries"] if not i["job_id"])
    path = f"/api/inquiries/{inquiry['id']}"
    result = client.post(path + "/brief").json()
    assert result["mode"] == "sample"
    brief = result["brief"]
    brief.pop("missing_information", None)
    brief["site"] = "Fictional site reviewed by operator"
    first = client.post(path + "/job", json=brief)
    second = client.post(path + "/job", json=brief)
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["site"] == brief["site"]
```

- [x] Run `.venv\Scripts\python.exe -m pytest tests/test_jobs.py -q -p no:cacheprovider --basetemp=.tmp_pytest/task2-red`; observe failure at the missing endpoint. Implement scope-checked lookup, unique source-inquiry constraint, validated input, and creation event in one transaction. Returning an existing conversion must not overwrite reviewed details.
- [x] Use a sample-key lookup for known seeded inquiries; a missing sample key returns empty editable fields and an explicit manual-entry message with provenance `manual-entry-required`. Do not infer arbitrary text with an undisclosed keyword simulator. Add tests for an unknown key, foreign customer/inquiry IDs, and a reversed requested date range.
- [x] Run workspace/intake tests; commit Task 2 files with `feat: turn sample inquiries into reviewed jobs`.

### Task 3: Exact quotes, immutable revisions, and approval

**Files:** Create `app/quotes.py`, `tests/test_quotes.py`; extend schemas, API, serializers, and test helpers.

**Interfaces:** `quote_total_cents(lines: list[QuoteLineInput]) -> int`; `save_quote(session, workspace_id, job_id, expected_version: int, lines: list[QuoteLineInput]) -> Job`; `approve_quote(session, workspace_id, job_id, quote_id, expected_version: int) -> Job`. Quote outputs include `id`, `revision`, `state`, `lines`, `total` (two-decimal string), and `total_cents`.

- [x] Add `save_quote(client, job, price="125.55") -> dict` to `tests/conftest.py`, posting `expected_version=job["version"]` and one line `{"description":"Illustrative mobilization","quantity":"2","unit_price":price}` to the quote endpoint and asserting HTTP 200. Write this test before implementation:

```python
from conftest import new_job, save_quote

def test_old_quote_cannot_be_approved(client):
    job = save_quote(client, new_job(client))
    old_id = job["quotes"][-1]["id"]
    job = save_quote(client, job, "99.99")
    path = f"/api/jobs/{job['id']}/quotes/{old_id}/approve"
    assert client.post(path, json={"expected_version": job["version"]}).status_code == 409
    current = job["quotes"][-1]
    assert current["total"] == "199.98"
    approved = client.post(f"/api/jobs/{job['id']}/quotes/{current['id']}/approve",
                           json={"expected_version": job["version"]})
    assert approved.status_code == 200
    assert approved.json()["status"] == "quoted"
```

- [x] Run quote tests expecting missing-endpoint failures. Implement line validation, cents arithmetic, current-revision check, and optimistic job versions inside write transactions. The money primitive is:

```python
from decimal import Decimal, ROUND_HALF_UP

def line_cents(quantity: Decimal, unit_price: Decimal) -> int:
    amount = (quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(amount * 100)
```

- [x] Add parameterized invalid values (`"NaN"`, `"Infinity"`, `"-1"`, excessive precision, above-bound quantities/prices), empty lines, long descriptions, and total overflow. Verify `0.333 × 10.00 = 3.33`, and two `0.005 × 1.00` lines total `0.02` under per-line rounding. Every rejected request must leave the quote history and job version unchanged.
- [x] Approve a quote, save a revision, and assert the old revision remains approved and unchanged while the job returns to `draft` awaiting the new approval. Assert stale `expected_version` returns 409, scheduled/completed quote edits return 409, and quote IDs from another job/workspace return 404.
- [x] Run Tasks 1–3 tests; commit with `feat: add exact quote revisions and internal approval`.

### Task 4: Resource scheduling and job progression

**Files:** Create `app/scheduling.py`, `tests/test_scheduling.py`; extend jobs, API, schemas, serializers, and test helpers.

**Interfaces:** `assign_job(session, workspace_id, job_id, assignment: AssignmentInput) -> Job`; `transition_job(session, workspace_id, job_id, expected_version: int, status: str) -> Job`. `AssignmentInput` contains the five assignment fields and version from the API table. A reservation overlaps when `existing.start_date <= proposed.end_date and existing.end_date >= proposed.start_date`. Either resource matching creates a conflict. Exclude the current job during a reschedule.

- [x] Add `approved_job(client) -> dict` to `tests/conftest.py`: call `new_job`, call `save_quote`, POST approval for the last quote with the returned job version, assert 200, and return the detail. Add these behavioral tests:

```python
from datetime import date, timedelta
from conftest import approved_job, new_job

def test_crew_and_equipment_cannot_double_book(client):
    first, second = approved_job(client), approved_job(client)
    boot = client.get("/api/bootstrap").json()
    day = (date.fromisoformat(boot["business_date"]) + timedelta(days=90)).isoformat()
    fields = dict(crew_id=boot["crews"][0]["id"], equipment_id=boot["equipment"][0]["id"],
                  start_date=day, end_date=day)
    first_response = client.put(f"/api/jobs/{first['id']}/assignment",
                                json=dict(fields, expected_version=first["version"]))
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "scheduled"
    collision = client.put(f"/api/jobs/{second['id']}/assignment",
                           json=dict(fields, expected_version=second["version"]))
    assert collision.status_code == 409
    assert "conflict" in collision.json()["detail"].lower()

def test_draft_cannot_jump_to_completed(client):
    job = new_job(client)
    response = client.post(f"/api/jobs/{job['id']}/status",
                           json={"status": "completed", "expected_version": job["version"]})
    assert response.status_code == 409
```

- [x] Run scheduling tests expecting failure. Implement resource membership checks, approved-current-quote requirement, date validation, conflict query, transactional assignment/event, and version increment. Limit proposed assignment span to 366 days, report the resource and conflicting date range, and keep operational dates as SQL Date fields.
- [x] Allow scheduling for `quoted` and rescheduling for `scheduled`; allow only `scheduled → in_progress → completed` through the status endpoint. Completed/in-progress assignment edits return 409. Notes and customer drafts remain available after completion.
- [x] Parameterize conflicts so same crew/different equipment and different crew/same equipment both fail. Test shared end/start boundary conflicts, disjoint next-day success, reversed date rejection, foreign resource IDs, self-reschedule success, stale version rejection, and completed-job immutability.
- [x] Add a service-level concurrent reservation test: create two separate database sessions against the same test SQLite file; use two thread workers and a start barrier to submit different jobs for the same resources/date. Start the barrier before acquiring each write transaction. Assert exactly one success, one 409, and one persisted assignment. Verify the failed transaction adds no event. This test checks the database locking behavior, not merely the query predicate.
- [x] Run tests for Tasks 1–4; commit with `feat: schedule jobs with resource conflict protection`.

### Task 5: Operational notes, customer drafts, and honest integration previews

**Files:** Create `app/communications.py`, `app/integrations.py`, `tests/test_communications.py`; extend assistant, jobs, schemas, API, and serializers.

**Interfaces:** `add_note(session, workspace_id, job_id, expected_version: int, text: str) -> Job`; `create_draft(session, workspace_id, job_id, expected_version: int) -> Job`; `update_draft(session, workspace_id, job_id, draft_id, payload: DraftInput) -> Job`; `preview_integration(session, workspace_id, job_id, expected_version: int, connector: str) -> dict`. `DraftInput` contains `expected_version`, `subject`, and `body`. Preview output has `mode="sample"`, `connected=false`, `sent=false`, `connector`, `mapping`, `payload`, and `created_at`.

- [x] Write tests before adding endpoints:

```python
from conftest import new_job

def test_customer_draft_uses_saved_site_and_is_not_sent(client):
    job = new_job(client)
    result = client.post(f"/api/jobs/{job['id']}/drafts", json={"expected_version": job["version"]})
    assert result.status_code == 200
    job = result.json()
    draft = job["drafts"][-1]
    assert job["site"] in draft["body"]
    assert draft["mode"] == "sample" and draft["state"] == "draft"
    edited = client.put(f"/api/jobs/{job['id']}/drafts/{draft['id']}",
        json={"expected_version": job["version"], "subject": "Reviewed update", "body": "Ready for operator review."})
    assert edited.status_code == 200
    assert edited.json()["drafts"][-1]["body"] == "Ready for operator review."

def test_preview_is_explicitly_local(client):
    job = new_job(client)
    response = client.post(f"/api/jobs/{job['id']}/integration-previews",
                           json={"connector": "crm", "expected_version": job["version"]})
    assert response.status_code == 200
    preview = response.json()["preview"]
    assert preview["mode"] == "sample"
    assert preview["connected"] is False and preview["sent"] is False
    assert preview["payload"]["job_id"] == job["id"]
```

- [x] Run communications tests expecting missing endpoints. Implement templates using saved customer/job/status and actual assignment dates. Unscheduled drafts explicitly say scheduling is pending; no invented date or acceptance claims. Prefix subject/body with appropriate sample context in the surrounding UI, keeping editable draft text practical.
- [x] Provide illustrative payloads: QuickBooks estimate uses current quote lines/amounts and requires a current quote; calendar uses actual assignment dates/resources and requires an assignment; CRM uses current customer/job/status. Use generic preview field names rather than claiming a vendor-validated schema. Missing prerequisites return 409 with instructions. No connector has an OAuth button that pretends to authenticate.
- [x] Save local preview/draft/note event and job version atomically. Add tests for unscheduled-message wording, edited draft persistence, foreign draft IDs, invalid connectors, missing preview prerequisites, note length, and HTML text preservation. Patch `socket.create_connection` to raise in the preview test and verify that all connector preview paths still work without network access.
- [x] Run Tasks 1–5 tests; commit with `feat: add editable sample communications and integration previews`.

### Task 6: Responsive English interface and the complete client journey

**Files:** Create `app/templates/index.html`, `app/static/styles.css`, `app/static/api.js`, `app/static/app.js`, `app/static/views.js`, `app/static/job.js`; extend shell serving in `app/main.py`.

**Interfaces:** `api(path: string, options?: object) -> Promise<object>` wraps JSON requests; `refresh() -> Promise<void>` reloads bootstrap and rerenders; `renderView(root: Element, state: object, actions: object) -> void` draws Overview/Inbox/Jobs/Schedule/Integrations; `renderJob(root: Element, job: object, actions: object) -> void` draws a job workspace. URL hashes select the view and job (`#overview`, `#inbox`, `#jobs`, `#jobs/<uuid>`, `#schedule`, `#integrations`). No custom client-side framework or bundler is needed.

- [x] Start the app locally with `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Use a hidden process or managed terminal, capture logs in the project, and verify `/health` before browser inspection. Read applicable browser/local-development guidance before browser verification.
- [x] Build the semantic shell: skip link, side navigation with active state, main heading, sample-mode badge, workspace reset action, and live status/error region. No external fonts or third-party scripts. Use system fonts, warm surface colors, dark navigation, amber actions, visible keyboard focus, and accessible labels.
- [x] Implement the request primitive and safe text rendering before views:

```javascript
export async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json();
  if (!response.ok) {
    const detail = typeof payload.detail === "string"
      ? payload.detail
      : (payload.detail || []).map(item => `${item.loc?.slice(1).join(".")}: ${item.msg}`).join("; ");
    throw new Error(detail || "The request could not be completed. Please try again.");
  }
  return payload;
}

export function text(tag, value, className = "") {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = value ?? "";
  return node;
}
```

- [x] Overview displays derived metrics, upcoming assignments, unconverted inquiry cards, draft quotes needing review, and activity. Inbox shows the original sample email, a **Prepare job brief** action, editable fields, missing-information notice, and **Create draft job**. Reopening converted inquiries links to the existing job.
- [x] Jobs provides text search and status filtering with an explicit zero-results state. Job workspace includes details, line-item quote editor, revision history, internal approval action, scheduling form, state actions, note form, customer drafts, and activity. Submit the latest `expected_version` on all mutations. After 409, preserve entered text, explain the conflict, and offer reload; never silently retry stale actions.
- [x] Quote UI offers add/remove lines, shows server-computed totals only after save, identifies draft/approved revision, labels **Illustrative CAD · Tax excluded**, and differentiates approval from customer acceptance. Disable busy actions until their requests resolve and restore controls after failures.
- [x] Schedule defaults to the week containing Toronto's business date; support previous/next/current week. Render a desktop week grid and a mobile list from the same assignments. Job scheduling form displays exact crew/equipment options and surfaces server conflict messages adjacent to the form.
- [x] Customer updates support generate/edit/save/copy. On clipboard failure, leave selectable text and a manual-copy instruction. Integrations show all three **Demo / Not connected** cards, field mappings, selected job, local preview action, and preview JSON rendered with `textContent` inside `pre`. No fake progress claiming an external send.
- [x] Test the browser journey through these actions: open Overview; convert an inquiry; save and approve a quote; assign free resources; add a note; start and complete the job; generate/edit/save/copy a draft; preview CRM data; refresh and verify persistence. Separately trigger a resource conflict and show its explanation.
- [x] Verify keyboard navigation, focus visibility, actionable labels, error recovery, and empty search results. Enter `<img src=x onerror=alert(1)>` into a note and site field; verify visible literal text without an executable node/dialog. Inspect desktop and 390px layouts, check no page-wide horizontal overflow, then restore viewport. Fix observed defects and commit with `feat: deliver responsive operations demo interface`.

### Task 7: Reset, persistence regression, final validation, and handoff

**Files:** Extend `app/api.py`, `app/workspaces.py`, `app/seed.py`, `tests/test_workspaces.py`; create `tests/test_journey.py`, `README.md`, `DEMO.md`, `VALIDATION.md`; finalize lock file and `.env.example`.

**Interfaces:** `/api/reset` uses current scoped workspace and `confirm=true`, deletes dependent business rows in foreign-key order, reseeds once, and returns bootstrap. It does not clear other visitors or replace application schema. Read handlers never mutate existing workflow state.

- [x] Add reset/isolation tests before implementing reset:

```python
from conftest import new_job

def test_reset_only_changes_current_workspace(client, other_client):
    job = new_job(client)
    others = other_client.get("/api/bootstrap").json()["jobs"]
    assert client.post("/api/reset", json={"confirm": False}).status_code == 422
    assert client.post("/api/reset", json={"confirm": True}).status_code == 200
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404
    assert other_client.get("/api/bootstrap").json()["jobs"] == others

def test_foreign_origin_cannot_mutate(client):
    response = client.post("/api/reset", json={"confirm": True}, headers={"Origin": "https://invalid.example"})
    assert response.status_code == 403
```

- [x] Run reset tests red, implement scoped reset, and wire an in-app confirmation dialog. Add oversized-body rejection, missing-Origin rejection, and scoped detail/mutation checks for every object-taking endpoint. Verify unsupported database schema startup fails without destructive repair.
- [x] Add the complete API journey test using helper functions through job completion and a saved draft. Dispose the first app, create a second app against the same database file, copy the original cookie into its test client, and assert the completed job, quote history, assignment, and draft remain. This verifies on-disk persistence across app lifecycle, beyond an in-memory refresh check.
- [x] Run `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp_pytest/final`. Then run `.venv\Scripts\python.exe -m compileall -q app` and `git diff --check`. Record actual counts and outputs, not predicted results. Broaden testing only for new failures or changes.
- [x] Write README with exact venv/install/start/test commands using the required RTK/PowerShell wrapper; database path and reset behavior; environment variables `DATABASE_URL`, `APP_ORIGIN`, `COOKIE_SECURE`; sample-only runtime; schema/version handling; local single-worker constraint. Explain that `.env.example` is configuration documentation and environment variables must be explicitly set unless a dotenv loader is intentionally implemented and tested.
- [x] Write DEMO as a five-minute English script: overview → inquiry → quote → schedule → progress → customer draft → integration preview. Describe what is interactive and persisted, and identify everything simulated. Write VALIDATION with completed automated/browser checks, actual runtime mode, unresolved defects if any, and deferred live/infrastructure checks. No production-ready or live-agent claims.
- [x] Document future public release prerequisites without provisioning resources: durable database, verified PostgreSQL locking and schema path, HTTPS cookies, workspace expiry/cleanup, rate limits, and no real customer data until authorized. The current app is local-only and public hosting is not a claimed deliverable.
- [x] Run a final browser walkthrough, inspect console/runtime logs, and leave the working overview tab available. Review the whole project diff against this plan. If native execution was selected, follow its required fresh review; if subagent-driven execution was selected, use its task and whole-branch review gates. Address actionable findings and retest affected behaviors.
- [x] Commit only project files with `test: verify complete demo journey and document handoff`. Provide the local URL, setup/doc links, test results, and explicit sample-mode limitation.

## Plan self-review

- Coverage: purpose/mode is global and Tasks 1, 5, 6; all eight demo-journey steps are Tasks 2–6; five pages are Task 6; persistence/schema/configuration are Tasks 1 and 7; record/state constraints are Tasks 1–5; visitor isolation/origin/body validation and reset are Tasks 1, 2, 7; responsive/error states are Task 6; acceptance evidence/docs are Task 7.
- Review focus: stale quotes in Task 3, concurrent/boundary reservations in Task 4, scoped/forged IDs in Tasks 1/2/7, HTML handling in Tasks 5/6, Toronto dates and scoped reset in Tasks 1/7.
- Interface consistency: all domain mutations share the session/workspace signature, return updated job detail, and use `expected_version`; preview adds a `preview` field. Shared test helpers are defined before dependent tests. Quotes are ordered ascending by revision; drafts/activity ascending by creation timestamp with a stable ID tiebreaker.
- Execution recommendation: **Native execution in this session**, followed by the required independent final review. Seven tasks share closely related job/version/transaction contracts, so one implementer avoids repeated context transfer. Subagent-driven execution remains an alternative with a fresh implementer/reviewer for each task.
- Approval status: written design and implementation plan approved; native execution selected. All seven tasks complete. Independent final review found two Important UI issues; both were reproduced, fixed, and verified. Final suites: 47 Python and 6 frontend tests passed.
