# Frank Operations Desk — MVP design

Status: Approved by the user ("按这份方案继续"); implementation, local verification, independent final review and its two fixes complete.

## Purpose and source

Build an English-language demonstration for an Upwork prospective client, using fictional sample data. The user confirmed this purpose on September 23, 2026 (America/Toronto).

Source: https://www.upwork.com/jobs/~022102907283842784424

The job listing was read directly in Chrome. Frank's Drilling & Blasting Ltd, Ontario, seeks AI agents for scheduling, quoting, job tracking, communications, and integrations with QuickBooks, email, scheduling platforms, and CRM systems. It requests Python/API skills and experience with agent frameworks. It does not specify the company's actual pricing, workflow rules, systems configuration, or data schemas.

This demo demonstrates a proposed workflow, not a reconstruction of the customer's internal systems. All clients, projects, rates, messages, and activity records are fictional. Branding must identify it as an independent concept demo rather than an official company system.

## Selected direction

Recommended: a working operations application with a Python backend, persisted sample records, and an explicit sample-mode agent workflow. This demonstrates business value across a complete journey without requiring client credentials.

Alternatives considered:

1. A static clickable prototype: quickest to build, but cannot establish correct calculations, scheduling checks, or persistence.
2. Working sample-data application (recommended): reviewable, reproducible, and suitable for a guided client demonstration.
3. Live integrations and live LLM execution: stronger production validation, but require account access, consent, API configuration, and actual business rules. Reserve for a later agreed scope.

## Demo journey

1. Open **Overview** to see active jobs, inquiries awaiting review, draft quote value, and upcoming assignments. Metrics are calculated from stored records.
2. Open **Inbox** and select a fictional customer inquiry. Run **Prepare job brief** to view sample-extracted customer, site, requested dates, service category, and missing information. Review or edit these fields, then create a draft job. Repeating creation from the same inquiry opens the existing job.
3. Open the job's **Quote** workspace. Adjust illustrative service line items, quantities, and rates. Totals are calculated on the server using decimal money arithmetic. No real-world rates or technical blasting calculations are implied. Taxes are excluded and clearly labeled in this demo.
4. Review and approve the quote internally. Approval freezes that revision. Editing an approved quote produces a new draft revision. Internal approval is not represented as customer acceptance or a sent message.
5. Schedule the approved job by choosing a date, a crew, and equipment. Save the assignment only when both resources are available. Overlaps produce a specific conflict explanation; rescheduling excludes the job's current assignment from conflict checks.
6. Move the job through **Scheduled → In progress → Completed**. Add an operational note. An activity timeline records quote approval, schedule changes, status changes, and communication drafts.
7. Generate a sample customer update from the job's actual stored facts. Edit and save the draft, then copy it. The application does not send email.
8. Open **Integrations** to see how the job and quote map to QuickBooks, email/calendar, and CRM records. Preview an example payload. Every connector is labeled **Demo / Not connected**. An optional dry-run creates a local preview event and never calls an external service.

## Pages and visual direction

- **Overview:** calm construction-operations dashboard, concise KPI cards, daily schedule, attention queue, and recent activity.
- **Inbox:** inquiry list and editable job brief with explicit sample-generation labeling.
- **Jobs:** searchable/filterable list with status and a focused job workspace for details, quotes, schedule, updates, and history.
- **Schedule:** week-based resource assignments with an accessible list view on smaller screens.
- **Integrations:** connection status, field mapping, payload previews, and local dry-run history.

Use an English interface, warm light background, charcoal navigation, restrained amber accents, clear typography, and compact operational tables. Support desktop and mobile. Include loading, empty, validation, and recoverable error states. A persistent **Sample data · No live integrations** indicator explains the execution mode. Use SVG/CSS icons; generated marketing imagery is unnecessary.

## Application architecture

- Python FastAPI backend serving HTML templates and plain JavaScript/CSS. A single application process keeps setup and deployment simple.
- SQLAlchemy persistence, SQLite for local operation. Keep database configuration environment-based and schema creation/migrations explicit so a later hosted version can use PostgreSQL.
- Small service modules for job workflow, quote revisions/calculations, resource scheduling, and sample assistant output. API handlers validate requests and delegate these operations.
- A sample assistant provider implements structured job briefs and customer drafts from known example inquiries and stored records. It returns an execution mode and provenance. Unknown free-text requests are handled honestly by asking for manual details; no simulated open-ended AI understanding.
- No live LLM dependency or credential is required. A future live provider can implement the same structured interface, but it is not an MVP acceptance claim. Do not add an agent framework merely to match keywords in the listing.
- All changes and activity events persist together in transactions. Workflow state validation is enforced on the backend.

## Records and business constraints

Core records: demo workspace, customer, inquiry, job, quote revision, quote line, crew, equipment, assignment, communication draft, activity event, and integration preview.

- The server establishes an opaque visitor workspace through an HTTP-only cookie. Records and metrics are scoped to that workspace. IDs alone never grant access to another visitor's records.
- Seed a small varied dataset once per workspace: inquiries, draft/approved quotes, available crews/equipment, scheduled jobs, and completed work. Dates are relative to the current Toronto business date so the initial schedule remains useful.
- A demo reset affects only the current visitor's sample workspace and requires an in-app confirmation. No client or real business data is connected.
- Quote line quantities and amounts must be finite, nonnegative, and bounded. Money is stored/calculated in a precise decimal representation, then serialized consistently.
- Scheduled work uses whole-day, inclusive Toronto date ranges. Crew and equipment reservations must both be conflict-free. This deliberately excludes hour-level dispatch optimization.
- The job progression is Draft → Quoted → Scheduled → In progress → Completed. Quote approval moves Draft to Quoted; scheduling requires a current approved quote. Invalid transitions are rejected.
- Revising an approved quote is allowed before scheduling. Once scheduled, quote changes are outside the MVP workflow. Completed jobs retain read-only scheduling and quotes.
- Sample assistant output is draft-only and cannot silently approve quotes, assign resources, or send messages.
- Operational scope is business administration. The demo does not generate blast plans, explosive specifications, or engineering recommendations.

## Security and deployment boundaries

Use same-origin browser requests, validate mutation origins, escape rendered content, bound request lengths, and keep credentials out of frontend code. External integrations remain disabled. If publicly hosted later, require a durable database, secure cookies, visitor limits, and workspace retention/cleanup before release.

This initial scope includes a locally runnable app and deployment instructions. Creating public hosting resources or claiming verified production integrations is not part of the current implementation approval.

## Acceptance criteria

1. A reviewer completes inquiry → job → quote approval → assignment → progress update → completed job without editing code or supplying API credentials.
2. Refreshing the browser retains changes; dashboard counts and schedule reflect those changes.
3. Invalid quote values, unapproved scheduling, overlapping resources, and invalid job transitions are rejected with useful messages.
4. Repeated inquiry conversion does not create duplicate jobs. A stale quote revision cannot be approved accidentally.
5. Communication drafts use the saved job facts, remain editable, and are never shown as sent.
6. Integration previews consistently show their demo status and make no external requests.
7. Two browser workspaces cannot read or mutate each other's records, including by requesting known IDs.
8. The full journey works in the browser at desktop and narrow mobile sizes without horizontal page overflow.
9. Targeted automated tests cover money, quote approval/revision rules, resource conflicts, transition rules, visitor isolation, and persistence. Browser verification covers the complete demonstration journey and visible errors.
10. README documents setup and execution; DEMO documents a short client walkthrough; validation notes distinguish automated tests, browser observations, and unimplemented live capabilities.

## Deferred

Live QuickBooks/Google/Microsoft/CRM OAuth, autonomous communications, live model calls, real customer data, customer-facing quote acceptance, billing/payments, production multi-user roles, engineering features, and advanced scheduling optimization.

## Environment findings

The project directory was empty at inspection. Git currently resolves to the parent `C:/Users/ponyh/source/repos`, which includes unrelated projects. Keep all work in `Frank-DB-Agent`; do not stage or modify sibling files. Establish a project-local repository during implementation if appropriate.

The requested PowerShell executable is installed as 7.6.6. The user explicitly approved using this version for the current task through RTK.
