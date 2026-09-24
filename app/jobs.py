from sqlalchemy import select, func
from .models import Job, Inquiry, Customer, ActivityEvent
from .errors import DomainError


def require_record(session, model, workspace_id, record_id):
    value = session.scalar(select(model).where(model.id == record_id, model.workspace_id == workspace_id))
    if value is None:
        raise DomainError(404, "Record not found in your workspace.")
    return value


def require_job(session, workspace_id, job_id):
    return require_record(session, Job, workspace_id, job_id)


def check_version(job, expected_version):
    if job.version != expected_version:
        raise DomainError(409, "This job changed in another action. Reload the latest version before saving.")


def event(session, job, kind, text):
    session.add(ActivityEvent(workspace_id=job.workspace_id, job_id=job.id, kind=kind, text=text))
    job.version += 1
    session.flush()


def convert_inquiry(session, workspace_id, inquiry_id, brief):
    require_record(session, Inquiry, workspace_id, inquiry_id)
    existing = session.scalar(select(Job).where(Job.workspace_id == workspace_id, Job.source_inquiry_id == inquiry_id))
    if existing:
        return existing, False
    require_record(session, Customer, workspace_id, brief.customer_id)
    count = session.scalar(select(func.count()).select_from(Job).where(Job.workspace_id == workspace_id))
    job = Job(workspace_id=workspace_id, source_inquiry_id=inquiry_id, number=f"FD-{1041 + count}",
              **brief.model_dump(), status="draft", version=1)
    session.add(job)
    session.flush()
    event(session, job, "intake", "Reviewed inquiry converted to a draft job.")
    return job, True
