# Implementation record

Delivered locally on September 23, 2026 (America/Toronto), on branch codex/frank-operations-demo.

The approved seven-task plan was implemented continuously in the current session. A separate fresh reviewer inspected the complete project, with verdict **With fixes**: zero Critical, two Important, zero Minor findings. Both Important findings were reproduced and fixed in one pass; no second review was requested.

## Final regression evidence

- Unsaved cross-form edits: browser RED (quote quantity 999 silently reverted after saving a note); four frontend regression cases RED before implementation, then GREEN. Explicit Keep editing preserves fields/version; explicit discard proceeds; customer-message protection also verified in Chrome.
- Inaccessible old notes: browser RED after eight newer events; recent/full-history regression cases RED before implementation, then GREEN. Expand/collapse restores access to all saved activity.
- Final complete suites: 47 Python tests passed in 23.44 seconds; 6 Node frontend tests passed. Python compileall, four JavaScript syntax checks and Git whitespace checks passed.
- One pinned Starlette TestClient deprecation warning remains. No tested browser console errors/warnings. No deferred Minor findings.
- Browser test workspace reset to fresh examples; overview left open. The local server remains available at http://127.0.0.1:8000.

## Rulings made during implementation

In execution order:

1. A project-local Git repository on codex/frank-operations-demo was created instead of a worktree of the unrelated parent repository. This avoids tracking sibling projects. Cost if wrong: relocate repository metadata.
2. PowerShell-native ledger and verification commands replaced Bash bookkeeping scripts, respecting the required exact Windows shell dispatch and approved PowerShell 7.6.6. Cost if wrong: manually reconcile ledger and commits.
3. Tasks 1 and 2 share the first implementation commit after sandbox/ownership resolution. Git ownership was handled with exact-path command-scoped safe.directory, never global configuration. Cost: less granular rollback for those initial tasks.
4. A shared scoped session context selects read/write transactions by route instead of separate read_session/write_session helpers. This avoids duplicate dependency logic. Cost if wrong: split the context later.
5. Some source-file payloads were written as base64 bytes through PowerShell to avoid Windows nested quoting corruption. No runtime dependency was added. Cost if wrong: rewrite an affected source file and rerun validation.
6. Completed assignments remain historical reservations but are excluded from upcoming-work metrics. Cost if the intended business rule differs: adjust the KPI and add the agreed reservation-release behavior.

## Final review boundaries and decisions

- Live model quality, vendor schemas, OAuth and actual message delivery remain outside this sample-only demonstration. Cost of changing scope: authorized credentials, provider-specific implementation and acceptance tests.
- Public hosting, PostgreSQL, multiple workers, abuse controls, retention and production identity remain deferred as approved. Cost of going public: implement those controls and rerun hosted verification before exposure.
- Seven-day workspace expiry currently means normal browser cookie expiry. No server-side replay expiry or revocation is claimed. The review focus on expired browser cookies is interpreted within that local-demo scope; the limitation is explicitly documented in README and VALIDATION. Cost if stronger expiry is required: store/enforce token expiration, test replay rejection and implement cleanup.
- Early completion does not automatically release the inclusive historical reservation. The real customer's resource-release rule is unspecified. Cost if early reuse is required: add an explicit, tested release rule without erasing history.
- Historical quote revisions and lines are persisted; the UI lists revision totals and approval state. A historical line-by-line viewer is deferred. Cost if required: add a read-only revision detail view.
- The final UI fix uses an explicit keep/discard decision rather than automatically rebasing edits onto a newly saved job version. Cost: users save one form at a time. Browser navigation/reload is not an autosave feature; users should save before leaving.

## Commit sequence

- 074f56d: persisted workspaces and reviewed inquiry intake (foundation and intake).
- 1b70d2b: exact quote revisions and approval.
- 5dc7292: resource conflicts and job progression.
- 430d726: sample communications and local integration previews.
- b08a131: responsive operations interface.
- c122ffb: persistence, reset and complete demo journey.
- Final follow-up commit: unsaved-edit protection, full activity access, regression tests and finalized delivery records.

See README.md for setup, DEMO.md for the English client walkthrough, and VALIDATION.md for detailed evidence and limits.
