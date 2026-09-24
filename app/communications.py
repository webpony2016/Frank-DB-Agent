from .models import CommunicationDraft
from .jobs import require_job, require_record, check_version, event
from .assistant import customer_update
from .errors import DomainError


def add_note(session, workspace_id, job_id, expected_version, text):
    job = require_job(session, workspace_id, job_id)
    check_version(job, expected_version)
    event(session, job, "note", text)
    return job


def create_draft(session, workspace_id, job_id, expected_version):
    job = require_job(session, workspace_id, job_id)
    check_version(job, expected_version)
    subject, body = customer_update(session, workspace_id, job)
    session.add(CommunicationDraft(workspace_id=workspace_id, job_id=job_id, subject=subject, body=body))
    event(session, job, "draft", "Sample customer update prepared for review. Nothing was sent.")
    return job


def update_draft(session, workspace_id, job_id, draft_id, payload):
    job = require_job(session, workspace_id, job_id)
    draft = require_record(session, CommunicationDraft, workspace_id, draft_id)
    if draft.job_id != job_id:
        raise DomainError(404, "Draft not found for this job.")
    check_version(job, payload.expected_version)
    draft.subject, draft.body = payload.subject, payload.body
    event(session, job, "draft", "Customer update draft edited and saved. Nothing was sent.")
    return job
